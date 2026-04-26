from django.views.generic import ListView, DetailView
from ..models import Aluno, Turma, Boletim, AlunoTurma, AreaDoConhecimento
from django.db.models import Q
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

class AlunoListView(LoginRequiredMixin, ListView):
    model = Aluno
    template_name = 'dashboard/aluno_list.html'
    context_object_name = 'alunos'  # Plural para a lista
    
    def get_queryset(self):
        queryset = Aluno.objects.all().order_by('nome')
        query = self.request.GET.get('q')
        turma_id = self.request.GET.get('turma')

        if query:
            queryset = queryset.filter(
                Q(nome__icontains=query) | 
                Q(matricula__icontains=query)
            )

        if turma_id:
            queryset = queryset.filter(alunoturma__turma_id=turma_id).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['todas_turmas'] = Turma.objects.all().select_related('curso').order_by('-ano', 'descricao')
        context['busca_atual'] = self.request.GET.get('q', '')
        
        turma_selecionada_id = self.request.GET.get('turma')
        context['filtro_turma_id'] = turma_selecionada_id
        
        if turma_selecionada_id:
            context['turma_selecionada_obj'] = Turma.objects.filter(id=turma_selecionada_id).first()
            
        context["total"] = self.get_queryset().count()
        return context

class AlunoDetailView(LoginRequiredMixin, DetailView):
    model = Aluno
    template_name = 'dashboard/aluno_detail.html'
    context_object_name = 'aluno'
    
    # --- CONFIGURAÇÃO PARA BUSCAR POR MATRÍCULA ---
    slug_field = 'matricula'       
    slug_url_kwarg = 'matricula'   
    # ----------------------------------------------

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aluno = self.object
        context['aluno'] = aluno
        
        # 1. LÓGICA DA MÁQUINA DO TEMPO
        anos_disponiveis = Boletim.objects.filter(aluno_matricula=aluno).values_list('turma_ano', flat=True).distinct().order_by('-turma_ano')
        ano_selecionado = self.request.GET.get('ano')
        
        if not ano_selecionado and anos_disponiveis:
            ano_selecionado = anos_disponiveis[0]
        
        if ano_selecionado:
            ano_selecionado = int(ano_selecionado)

        turma_obj = None
        curso = None
        boletim_atual = []

        aluno_turma_registro = AlunoTurma.objects.filter(aluno_matricula=aluno, turma_ano=ano_selecionado).first()
        
        if aluno_turma_registro:
            turma_obj = Turma.objects.filter(id=aluno_turma_registro.turma_id).first()
        else:
            bol_temp = Boletim.objects.filter(aluno_matricula=aluno, turma_ano=ano_selecionado).first()
            if bol_temp:
                turma_obj = Turma.objects.filter(id=bol_temp.turma_id).first()

        if turma_obj:
            curso = turma_obj.curso
            boletim_atual = Boletim.objects.filter(
                aluno_matricula=aluno,
                turma_ano=ano_selecionado
            ).select_related('disciplina', 'disciplina__area_do_conhecimento').order_by('disciplina__descricao')

        # 2. CÁLCULOS
        comp_labels, comp_aluno, comp_turma = [], [], [] 
        global_bims = {'b1': [], 'b2': [], 'b3': [], 'b4': []}
        todas_areas = AreaDoConhecimento.objects.all().order_by('descricao')
        stats_areas = {area.descricao: {'atual': [], 'geral': [], 'turma': []} for area in todas_areas}

        def get_nota_real(boletim_item):
            def gv(v): return float(v) if v is not None else None
            b1, b2, r1 = gv(boletim_item.bimestre1), gv(boletim_item.bimestre2), gv(boletim_item.recusem1)
            b3, b4, r2 = gv(boletim_item.bimestre3), gv(boletim_item.bimestre4), gv(boletim_item.recusem2)
            
            ns1 = [n for n in [b1, b2] if n is not None and n > 0]
            m1 = (sum(ns1)/len(ns1)) if ns1 else None
            if m1 and r1 and r1 > m1: m1 = r1
            
            ns2 = [n for n in [b3, b4] if n is not None and n > 0]
            m2 = (sum(ns2)/len(ns2)) if ns2 else None
            if m2 and r2 and r2 > m2: m2 = r2
            
            if m1 is not None and m2 is not None: return (m1 + m2) / 2
            elif m1 is not None: return m1
            elif m2 is not None: return m2
            return 0.0

        for b in boletim_atual:
            nota = get_nota_real(b)
            if b.bimestre1: global_bims['b1'].append(float(b.bimestre1))
            if b.bimestre2: global_bims['b2'].append(float(b.bimestre2))
            if b.bimestre3: global_bims['b3'].append(float(b.bimestre3))
            if b.bimestre4: global_bims['b4'].append(float(b.bimestre4))

            if nota > 0:
                comp_labels.append(b.disciplina.descricao)
                comp_aluno.append(round(nota, 1))
                media_t = 0
                if turma_obj:
                    colegas = Boletim.objects.filter(
                        disciplina=b.disciplina, 
                        turma_id=turma_obj.id, 
                        turma_ano=ano_selecionado
                    ).only('bimestre1', 'bimestre2', 'recusem1', 'bimestre3', 'bimestre4', 'recusem2')
                    notas_colegas = [get_nota_real(c) for c in colegas]
                    notas_validas = [n for n in notas_colegas if n > 0]
                    if notas_validas: 
                        media_t = sum(notas_validas) / len(notas_validas)
                comp_turma.append(round(media_t, 1))
                if b.disciplina.area_do_conhecimento:
                    area = b.disciplina.area_do_conhecimento.descricao
                    if area in stats_areas:
                        stats_areas[area]['atual'].append(nota)
                        if media_t > 0: 
                            stats_areas[area]['turma'].append(media_t)

        historico_completo = Boletim.objects.filter(aluno_matricula=aluno).select_related('disciplina__area_do_conhecimento')
        for b in historico_completo:
            nota = get_nota_real(b)
            if nota > 0 and b.disciplina.area_do_conhecimento:
                area_desc = b.disciplina.area_do_conhecimento.descricao
                if area_desc in stats_areas:
                    stats_areas[area_desc]['geral'].append(nota)

        global_curve_data = [
            round(sum(global_bims[k])/len(global_bims[k]), 1) if global_bims[k] else 0 
            for k in ['b1', 'b2', 'b3', 'b4']
        ]

        radar_labels, radar_atual, radar_geral, radar_turma = [], [], [], []
        area_vencedora = "Sem dados"
        maior_media = -1
        
        for area, dados in stats_areas.items():
            if dados['atual'] or dados['geral'] or dados['turma']:
                radar_labels.append(area)
                media_atual = round(sum(dados['atual'])/len(dados['atual']), 1) if dados['atual'] else 0
                radar_atual.append(media_atual)
                media_historica = sum(dados['geral'])/len(dados['geral']) if dados['geral'] else 0
                radar_geral.append(round(media_historica, 1))
                media_da_turma = round(sum(dados['turma'])/len(dados['turma']), 1) if dados['turma'] else 0
                radar_turma.append(media_da_turma)
                if media_historica > maior_media:
                    maior_media = media_historica
                    area_vencedora = area
        
        icone_area = "bi-mortarboard-fill"
        cor_area = "#0d6619"
        area_lower = area_vencedora.lower()
        if 'téc' in area_lower or 'prof' in area_lower: icone_area, cor_area = "bi-cpu-fill", "#218c74"
        elif 'matem' in area_lower or 'exata' in area_lower: icone_area, cor_area = "bi-calculator-fill", "#0984e3"
        elif 'human' in area_lower or 'socia' in area_lower: icone_area, cor_area = "bi-people-fill", "#e1b12c"
        elif 'natur' in area_lower or 'bio' in area_lower: icone_area, cor_area = "bi-flower1", "#00b894"
        elif 'ling' in area_lower: icone_area, cor_area = "bi-translate", "#6c5ce7"

        context['turma'] = turma_obj
        context['curso'] = curso
        context['boletim'] = boletim_atual
        context['anos_disponiveis'] = anos_disponiveis
        context['ano_selecionado'] = ano_selecionado
        context['area_destaque'] = area_vencedora
        context['media_destaque'] = round(maior_media, 1)
        context['icone_destaque'] = icone_area
        context['cor_destaque'] = cor_area

        context['comp_labels'] = json.dumps(comp_labels)
        context['comp_aluno'] = json.dumps(comp_aluno)
        context['comp_turma'] = json.dumps(comp_turma)
        context['global_curve_data'] = json.dumps(global_curve_data)
        context['radar_labels'] = json.dumps(radar_labels)
        context['radar_atual'] = json.dumps(radar_atual)
        context['radar_geral'] = json.dumps(radar_geral)
        context['radar_turma'] = json.dumps(radar_turma)

        return context
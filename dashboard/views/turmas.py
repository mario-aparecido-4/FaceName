from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from ..models import Turma, Curso, Turno, Serie, AlunoTurma, Boletim, AreaDoConhecimento
from django.db.models import Q
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

class TurmaListView(LoginRequiredMixin, ListView):
    model = Turma
    template_name = 'dashboard/turma_list.html'
    context_object_name = 'turmas'
    
    def get_queryset(self):
        queryset = Turma.objects.all().select_related('curso', 'turno', 'serie').order_by('-ano', 'descricao')
        q = self.request.GET.get('q')
        curso_id = self.request.GET.get('curso')
        ano = self.request.GET.get('ano')
        turno_id = self.request.GET.get('turno')
        serie_id = self.request.GET.get('serie')

        if q:
            queryset = queryset.filter(Q(descricao__icontains=q) | Q(curso__descricao__icontains=q))
        if curso_id: queryset = queryset.filter(curso_id=curso_id)
        if ano: queryset = queryset.filter(ano=ano)
        if turno_id: queryset = queryset.filter(turno_id=turno_id)
        if serie_id: queryset = queryset.filter(serie_id=serie_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cursos'] = Curso.objects.all().order_by('descricao')
        context['turnos'] = Turno.objects.all().order_by('descricao')
        context['series'] = Serie.objects.all().order_by('descricao')
        context['anos'] = Turma.objects.values_list('ano', flat=True).distinct().order_by('-ano')
        
        context['q_atual'] = self.request.GET.get('q', '')
        context['curso_atual'] = self.request.GET.get('curso', '')
        context['ano_atual'] = self.request.GET.get('ano', '')
        context['turno_atual'] = self.request.GET.get('turno', '')
        context['serie_atual'] = self.request.GET.get('serie', '')
        context['total'] = self.get_queryset().count()
        return context

class TurmaDetailView(LoginRequiredMixin, DetailView):
    model = Turma
    template_name = 'dashboard/turma_detail.html'
    context_object_name = 'turma'

    def get_object(self):
        id = self.kwargs.get('id')
        ano = self.kwargs.get('ano')
        return get_object_or_404(Turma, id=id, ano=ano)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        turma = self.object

        alunos_qs = AlunoTurma.objects.filter(turma_id=turma.id, turma_ano=turma.ano).select_related('aluno_matricula')
        boletins = Boletim.objects.filter(turma_id=turma.id, turma_ano=turma.ano).select_related('disciplina', 'disciplina__area_do_conhecimento', 'aluno_matricula')
        
        def get_nota_real(bol):
            def gv(v): return float(v) if v is not None else None
            b1, b2, r1 = gv(bol.bimestre1), gv(bol.bimestre2), gv(bol.recusem1)
            b3, b4, r2 = gv(bol.bimestre3), gv(bol.bimestre4), gv(bol.recusem2)
            
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

        todas_areas = AreaDoConhecimento.objects.all().order_by('descricao')
        stats_areas = {area.descricao: [] for area in todas_areas}
        stats_disciplinas = {} 
        alunos_performance = {}
        evolucao_turma = {'b1': [], 'b2': [], 'b3': [], 'b4': []}

        for b in boletins:
            nota = get_nota_real(b)
            if b.bimestre1: evolucao_turma['b1'].append(float(b.bimestre1))
            if b.bimestre2: evolucao_turma['b2'].append(float(b.bimestre2))
            if b.bimestre3: evolucao_turma['b3'].append(float(b.bimestre3))
            if b.bimestre4: evolucao_turma['b4'].append(float(b.bimestre4))

            if nota > 0:
                if b.disciplina.area_do_conhecimento:
                    area = b.disciplina.area_do_conhecimento.descricao
                    if area in stats_areas: stats_areas[area].append(nota)
                
                disc = b.disciplina.descricao
                if disc not in stats_disciplinas: stats_disciplinas[disc] = []
                stats_disciplinas[disc].append(nota)

                matr = b.aluno_matricula.matricula
                if matr not in alunos_performance:
                    alunos_performance[matr] = [] 
                alunos_performance[matr].append(nota)

        radar_labels, radar_data = [], []
        maior_media_area = -1
        area_vencedora = "Analisando..."
        
        for area, notas in stats_areas.items():
            if notas:
                media = sum(notas)/len(notas)
                radar_labels.append(area)
                radar_data.append(round(media, 1))
                if media > maior_media_area:
                    maior_media_area = media
                    area_vencedora = area
        
        icone_area, cor_area = "bi-mortarboard-fill", "#6c5ce7"
        al = area_vencedora.lower()
        if 'téc' in al: icone_area, cor_area = "bi-cpu-fill", "#e17055"
        elif 'matem' in al or 'exata' in al: icone_area, cor_area = "bi-calculator-fill", "#0984e3"
        elif 'human' in al or 'socia' in al: icone_area, cor_area = "bi-people-fill", "#fdcb6e"
        elif 'natur' in al or 'bio' in al: icone_area, cor_area = "bi-flower1", "#00b894"
        elif 'ling' in al: icone_area, cor_area = "bi-translate", "#e84393"

        bar_list = []
        pior_materia, menor_media_disc = "Nenhuma", 11
        for disc, notas in stats_disciplinas.items():
            media = sum(notas)/len(notas)
            bar_list.append({'label': disc, 'y': round(media, 1)})
            if media < menor_media_disc: menor_media_disc, pior_materia = media, disc
        
        bar_list.sort(key=lambda x: x['y'], reverse=True)
        if menor_media_disc == 11: menor_media_disc = 0

        melhor_materia = bar_list[0]['label'] if bar_list else "Nenhuma"
        media_melhor = bar_list[0]['y'] if bar_list else 0.0
        distribuicao = [0, 0, 0, 0]
        alunos_risco_list = []
        lista_medias_finais = []
        lista_alunos_completa = []

        for item in alunos_qs:
            matr = item.aluno_matricula.matricula
            nome = item.aluno_matricula.nome
            pk = item.aluno_matricula.pk
            foto = item.aluno_matricula.foto
            media_aluno = 0
            if matr in alunos_performance and alunos_performance[matr]:
                media_aluno = sum(alunos_performance[matr]) / len(alunos_performance[matr])
            
            if media_aluno > 0:
                lista_medias_finais.append(media_aluno)
                if media_aluno < 4: distribuicao[0] += 1
                elif media_aluno < 6: distribuicao[1] += 1
                elif media_aluno < 8: distribuicao[2] += 1
                else: distribuicao[3] += 1
                
                if media_aluno < 6:
                    alunos_risco_list.append({'nome': nome, 'media': media_aluno, 'id': pk})

            lista_alunos_completa.append({
                'matricula': matr, 'nome': nome, 'pk': pk,
                'foto': foto,
                'media': round(media_aluno, 1) if media_aluno > 0 else None
            })

        lista_alunos_completa.sort(key=lambda x: x['nome'])
        top_alunos_temp = [x for x in lista_alunos_completa if x['media'] is not None]
        top_alunos_temp.sort(key=lambda x: x['media'], reverse=True)
        top_3 = top_alunos_temp[:3]
        alunos_risco_list.sort(key=lambda x: x['media'])
        alunos_risco = alunos_risco_list[:5]

        evolucao_data = [round(sum(evolucao_turma[k])/len(evolucao_turma[k]), 1) if evolucao_turma[k] else 0 for k in ['b1', 'b2', 'b3', 'b4']]

        context['lista_alunos_completa'] = lista_alunos_completa
        context['total_alunos'] = alunos_qs.count()
        context['media_geral_turma'] = round(sum(lista_medias_finais)/len(lista_medias_finais), 1) if lista_medias_finais else 0
        context['top_3'] = top_3
        context['alunos_risco'] = alunos_risco
        context['qtd_risco'] = len(alunos_risco_list)
        context['melhor_materia'] = melhor_materia
        context['media_melhor'] = media_melhor
        context['media_destaque'] = round(maior_media_area, 1)
        context['icone_destaque'] = icone_area
        context['cor_destaque'] = cor_area
        context['pior_materia'] = pior_materia
        context['media_pior'] = round(menor_media_disc, 1)

        context['radar_labels'] = json.dumps(radar_labels)
        context['radar_data'] = json.dumps(radar_data)
        context['bar_labels'] = json.dumps([x['label'] for x in bar_list])
        context['bar_data'] = json.dumps([x['y'] for x in bar_list])
        context['distribuicao_data'] = json.dumps(distribuicao)
        context['evolucao_data'] = json.dumps(evolucao_data)

        return context
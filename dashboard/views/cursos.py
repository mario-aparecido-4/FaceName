from django.views.generic import DetailView, ListView
from ..models import Curso, Turma, Boletim, AlunoTurma
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

# --- NOVA VIEW PARA SELEÇÃO DE CURSOS (TIPO MENU) ---
class CursoSelectionView(LoginRequiredMixin, ListView):
    model = Curso
    template_name = 'dashboard/cursos.html'
    context_object_name = 'cursos'
    
    def get_queryset(self):
        return Curso.objects.all().order_by('descricao')

# --- VIEW DE DETALHES ---
class CursoDetailView(LoginRequiredMixin, DetailView):
    model = Curso
    template_name = 'dashboard/curso_detail.html'
    context_object_name = 'curso'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curso = self.object

        # 1. Busca turmas deste curso
        turmas_qs = Turma.objects.filter(curso=curso).select_related('serie').order_by('-ano', 'serie__descricao', 'descricao')
        turma_map = {(t.id, t.ano): t for t in turmas_qs}

        # 2. Busca boletins APENAS do curso
        boletins_curso = Boletim.objects.filter(
            turma_id__in=turmas_qs.values_list('id', flat=True)
        ).select_related('disciplina', 'disciplina__area_do_conhecimento', 'aluno_matricula')

        # --- FUNÇÃO DE CÁLCULO ---
        def get_nota_real(bol):
            def gv(v): return float(v) if v is not None else None
            b1, b2, r1 = gv(bol.bimestre1), gv(bol.bimestre2), gv(bol.recusem1)
            b3, b4, r2 = gv(bol.bimestre3), gv(bol.bimestre4), gv(bol.recusem2)
            
            # Se tiver Nota Final fechada, usa ela
            nf = gv(bol.final)
            if nf and nf > 0:
                return nf

            # Senão, calcula parcial
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

        # --- ESTATÍSTICAS DO CURSO ---
        stats_series = {}      
        stats_turmas = {}      
        stats_disciplinas = {}
        lista_medias_gerais = []
        
        ids_alunos_do_curso = set()

        for b in boletins_curso:
            ids_alunos_do_curso.add(b.aluno_matricula_id)
            
            nota = get_nota_real(b)
            turma_obj = turma_map.get((b.turma_id, b.turma_ano))

            if nota > 0 and turma_obj:
                lista_medias_gerais.append(nota)
                
                # Stats Série
                serie_nome = turma_obj.serie.descricao
                if serie_nome not in stats_series: stats_series[serie_nome] = []
                stats_series[serie_nome].append(nota)

                # Stats Turma
                turma_nome = f"{turma_obj.descricao} ({turma_obj.ano})"
                if turma_nome not in stats_turmas: stats_turmas[turma_nome] = []
                stats_turmas[turma_nome].append(nota)

                # Stats Disciplina
                disc = b.disciplina.descricao
                if disc not in stats_disciplinas: stats_disciplinas[disc] = []
                stats_disciplinas[disc].append(nota)

        # --- RANKING DE ALUNOS (HISTÓRICO COMPLETO 3 ANOS) ---
        
        # 1. Busca histórico completo desses alunos
        boletins_historico = Boletim.objects.filter(
            aluno_matricula__in=list(ids_alunos_do_curso)
        ).select_related('aluno_matricula')

        # 2. Descobre a Turma Mais Recente de cada aluno (AQUI ESTAVA O ERRO)
        # Usamos 'turma_ano' diretamente, sem underline duplo, e removemos select_related('turma')
        matriculas_recentes = AlunoTurma.objects.filter(
            aluno_matricula__in=list(ids_alunos_do_curso)
        ).order_by('aluno_matricula', '-turma_ano') 

        # Mapa auxiliar para pegar os nomes das turmas (já que não temos FK)
        ids_turmas_encontradas = set([m.turma_id for m in matriculas_recentes])
        objs_turmas = Turma.objects.filter(id__in=ids_turmas_encontradas)
        mapa_nomes_turmas = {t.id: f"{t.descricao} ({t.ano})" for t in objs_turmas}

        mapa_turma_recente = {}
        for m in matriculas_recentes:
            aid = m.aluno_matricula_id
            # O primeiro registro é o mais recente devido ao order_by '-turma_ano'
            if aid not in mapa_turma_recente:
                nome_formatado = mapa_nomes_turmas.get(m.turma_id, "Turma Desconhecida")
                mapa_turma_recente[aid] = nome_formatado

        # 3. Calcula Média Geral
        notas_por_aluno_hist = {}
        nomes_alunos = {}

        for b in boletins_historico:
            nota = get_nota_real(b)
            if nota > 0:
                matr = b.aluno_matricula.matricula
                if matr not in notas_por_aluno_hist:
                    notas_por_aluno_hist[matr] = []
                    nomes_alunos[matr] = b.aluno_matricula.nome
                notas_por_aluno_hist[matr].append(nota)

        rank_alunos = []
        for matr, notas in notas_por_aluno_hist.items():
            media = sum(notas) / len(notas)
            
            # Recupera o PK do aluno para buscar no mapa de turmas
            pk_aluno = None
            # Forma rápida de achar o pk sem query extra
            for b in boletins_historico:
                if b.aluno_matricula.matricula == matr:
                    pk_aluno = b.aluno_matricula.pk
                    break
            
            turma_display = mapa_turma_recente.get(pk_aluno, "Ex-Aluno")
            
            rank_alunos.append({
                'nome': nomes_alunos[matr],
                'turma': turma_display,
                'media': round(media, 1)
            })
            
        rank_alunos.sort(key=lambda x: x['media'], reverse=True)
        top_5_alunos = rank_alunos[:5]

        # --- CONSOLIDAÇÃO ---
        total_alunos = len(ids_alunos_do_curso)
        media_curso = round(sum(lista_medias_gerais)/len(lista_medias_gerais), 1) if lista_medias_gerais else 0
        
        # Melhor Turma
        melhor_turma_nome = "Analisando..."
        maior_media_turma = -1
        bar_turmas_labels, bar_turmas_data = [], []
        
        temp_turmas = []
        for t, notas in stats_turmas.items():
            m = sum(notas)/len(notas)
            temp_turmas.append({'label': t, 'y': round(m, 1)})
            if m > maior_media_turma:
                maior_media_turma = m
                melhor_turma_nome = t
        
        temp_turmas.sort(key=lambda x: x['y'], reverse=True)
        for item in temp_turmas[:10]:
            bar_turmas_labels.append(item['label'])
            bar_turmas_data.append(item['y'])

        # Melhor e Pior Matéria
        pior_materia = "Nenhuma"
        melhor_materia = "Nenhuma"
        menor_media_disc = 11
        maior_media_disc = -1
        
        for disc, notas in stats_disciplinas.items():
            m = sum(notas)/len(notas)
            if m < menor_media_disc:
                menor_media_disc = m
                pior_materia = disc
            if m > maior_media_disc:
                maior_media_disc = m
                melhor_materia = disc
                
        if menor_media_disc == 11: menor_media_disc = 0
        if maior_media_disc == -1: maior_media_disc = 0

        # Gráficos Extras
        series_sorted = sorted(stats_series.keys())
        line_series_labels, line_series_data = [], []
        for s in series_sorted:
            notas = stats_series[s]
            m = sum(notas)/len(notas)
            line_series_labels.append(s)
            line_series_data.append(round(m, 1))

        distribuicao = [0, 0, 0, 0]
        for nota in lista_medias_gerais:
            if nota < 4: distribuicao[0] += 1
            elif nota < 6: distribuicao[1] += 1
            elif nota < 8: distribuicao[2] += 1
            else: distribuicao[3] += 1

        context.update({
            'turmas_list': turmas_qs,
            'total_turmas': turmas_qs.count(),
            'total_alunos': total_alunos,
            'media_curso': media_curso,
            'melhor_turma': melhor_turma_nome,
            'media_melhor_turma': round(maior_media_turma, 1),
            'pior_materia': pior_materia,
            'media_pior': round(menor_media_disc, 1),
            'melhor_materia': melhor_materia,           
            'media_melhor_materia': round(maior_media_disc, 1), 
            'top_5_alunos': top_5_alunos,
            'bar_turmas_labels': json.dumps(bar_turmas_labels),
            'bar_turmas_data': json.dumps(bar_turmas_data),
            'line_series_labels': json.dumps(line_series_labels),
            'line_series_data': json.dumps(line_series_data),
            'distribuicao_data': json.dumps(distribuicao)
        })

        return context
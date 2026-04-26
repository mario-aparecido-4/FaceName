from django.views.generic import TemplateView
from ..models import Aluno, Turma, Boletim
import json
import datetime
from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

class Inicio(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/inicio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Contagens Básicas
        total_alunos = Aluno.objects.count()
        total_turmas = Turma.objects.count()
        
        # 2. Mapeamento
        all_turmas = Turma.objects.select_related('curso', 'serie').all()
        turma_map = {(t.id, t.ano): t for t in all_turmas}

        # 3. Busca Boletins
        all_boletins = Boletim.objects.select_related(
            'disciplina', 'aluno_matricula'
        ).only(
            'bimestre1', 'bimestre2', 'recusem1', 'bimestre3', 'bimestre4', 'recusem2',
            'disciplina__descricao', 'aluno_matricula__nome', 'aluno_matricula__matricula',
            'turma_id', 'turma_ano'
        )

        # 4. Estruturas de Agrupamento
        notas_por_aluno = {} 
        info_alunos = {}     
        stats_cursos = {}      
        stats_turmas = {}      
        stats_disciplinas = {} 
        notas_por_materia_widget = {} 

        def calc_media(b):
            def gv(v): return float(v) if v else None
            n1, n2, r1 = gv(b.bimestre1), gv(b.bimestre2), gv(b.recusem1)
            n3, n4, r2 = gv(b.bimestre3), gv(b.bimestre4), gv(b.recusem2)
            
            ns1 = [x for x in [n1, n2] if x is not None]
            m1 = (sum(ns1)/len(ns1)) if ns1 else None
            if m1 and r1 and r1 > m1: m1 = r1
            
            ns2 = [x for x in [n3, n4] if x is not None]
            m2 = (sum(ns2)/len(ns2)) if ns2 else None
            if m2 and r2 and r2 > m2: m2 = r2
            
            if m1 is not None and m2 is not None: return (m1 + m2)/2
            elif m1 is not None: return m1
            elif m2 is not None: return m2
            return None

        # --- PROCESSAMENTO ---
        for b in all_boletins:
            nota = calc_media(b)
            turma_obj = turma_map.get((b.turma_id, b.turma_ano))
            
            if nota is not None and turma_obj:
                matr = b.aluno_matricula.matricula
                if matr not in notas_por_aluno:
                    notas_por_aluno[matr] = []
                    info_alunos[matr] = {
                        'nome': b.aluno_matricula.nome,
                        'turma': turma_obj.descricao,
                        'pk': b.aluno_matricula.pk
                    }
                notas_por_aluno[matr].append(nota)

                d_nome = b.disciplina.descricao
                if d_nome not in notas_por_materia_widget:
                    notas_por_materia_widget[d_nome] = []
                
                notas_por_materia_widget[d_nome].append({
                    'nome': b.aluno_matricula.nome,
                    'media': round(nota, 1),
                    'turma': turma_obj.descricao
                })

                c_nome = turma_obj.curso.descricao
                if c_nome not in stats_cursos: stats_cursos[c_nome] = []
                stats_cursos[c_nome].append(nota)
                
                t_nome = f"{turma_obj.descricao} ({turma_obj.ano})"
                if t_nome not in stats_turmas: stats_turmas[t_nome] = []
                stats_turmas[t_nome].append(nota)
                
                if d_nome not in stats_disciplinas: stats_disciplinas[d_nome] = []
                stats_disciplinas[d_nome].append(nota)

        # --- CÁLCULOS FINAIS ---
        medias_finais_alunos = []
        rank_alunos = []

        for matr, notas in notas_por_aluno.items():
            if notas:
                media_unica_aluno = sum(notas) / len(notas)
                medias_finais_alunos.append(media_unica_aluno)
                dados = info_alunos[matr]
                rank_alunos.append({
                    'nome': dados['nome'], 
                    'turma': dados['turma'], 
                    'media': round(media_unica_aluno, 1), 
                    'pk': dados['pk']
                })

        distribuicao = [0, 0, 0, 0, 0]
        qtd_vermelha = 0
        for n in medias_finais_alunos:
            if n < 2: distribuicao[0] += 1; qtd_vermelha += 1
            elif n < 4: distribuicao[1] += 1; qtd_vermelha += 1
            elif n < 6: distribuicao[2] += 1; qtd_vermelha += 1
            elif n < 8: distribuicao[3] += 1
            else: distribuicao[4] += 1
            
        media_escola = round(sum(medias_finais_alunos)/len(medias_finais_alunos), 1) if medias_finais_alunos else 0
        percent_sucesso = round(((len(medias_finais_alunos) - qtd_vermelha) / len(medias_finais_alunos) * 100), 1) if medias_finais_alunos else 0

        rank_turmas = []
        for t, notas in stats_turmas.items():
            rank_turmas.append({'nome': t, 'media': round(sum(notas)/len(notas), 1)})
        rank_turmas.sort(key=lambda x: x['media'], reverse=True)
        top_turmas = rank_turmas[:5]
        piores_turmas = rank_turmas[-5:]; piores_turmas.reverse()

        rank_disc = []
        for d, notas in stats_disciplinas.items():
            rank_disc.append({'nome': d, 'media': round(sum(notas)/len(notas), 1)})
        rank_disc.sort(key=lambda x: x['media'])
        gargalos_disciplinas = rank_disc[:5]

        rank_alunos.sort(key=lambda x: x['media'], reverse=True)
        top_alunos_geral = rank_alunos[:5]

        curso_labels, curso_data = [], []
        for c, notas in stats_cursos.items():
            curso_labels.append(c)
            curso_data.append(round(sum(notas)/len(notas), 1))

        widget_top3_materia = []
        for materia in sorted(notas_por_materia_widget.keys()):
            lista = notas_por_materia_widget[materia]
            lista.sort(key=lambda x: x['media'], reverse=True)
            if lista:
                widget_top3_materia.append({'materia': materia, 'alunos': lista[:3]})

        h = datetime.datetime.now().hour
        saudacao = "Bom dia" if 5<=h<12 else "Boa tarde" if 12<=h<18 else "Boa noite"

        context.update({
            'total_alunos': total_alunos, 'total_turmas': total_turmas,
            'media_escola': media_escola, 'percent_sucesso': percent_sucesso,
            'saudacao': saudacao,
            'top_turmas': top_turmas, 'piores_turmas': piores_turmas,
            'gargalos_disciplinas': gargalos_disciplinas, 'top_alunos_geral': top_alunos_geral,
            'widget_top3_materia': widget_top3_materia,
            'dist_data': json.dumps(distribuicao),
            'curso_labels': json.dumps(curso_labels),
            'curso_data': json.dumps(curso_data),
        })
        
        return context
from django.views.generic import TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from ..models import Aluno, Boletim, AreaDoConhecimento, Turma, AlunoTurma
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

# --- FUNÇÃO UTILITÁRIA ---
def safe_float(valor):
    """Converte notas para float seguro."""
    if valor is None or valor == '': return 0.0
    try:
        if isinstance(valor, (int, float)): return float(valor)
        return float(str(valor).replace(',', '.').strip())
    except:
        return 0.0

# --- LÓGICA CENTRAL DE CÁLCULO (HÍBRIDA) ---
def calcular_nota_hibrida(b):
    """
    1. Prioridade: Nota Final fechada.
    2. Fallback: Cálculo parcial considerando bimestres e recuperações.
    """
    # 1. Tenta Nota Final
    nf = safe_float(b.final)
    if nf > 0: return nf

    # 2. Calcula Parciais
    def gv(v): return safe_float(v)
    
    b1, b2, r1 = gv(b.bimestre1), gv(b.bimestre2), gv(b.recusem1)
    b3, b4, r2 = gv(b.bimestre3), gv(b.bimestre4), gv(b.recusem2)

    # Semestre 1
    ns1 = [n for n in [b1, b2] if n > 0]
    m1 = (sum(ns1)/len(ns1)) if ns1 else None
    if m1 and r1 and r1 > m1: m1 = r1 # Aplica Recuperação 1

    # Semestre 2
    ns2 = [n for n in [b3, b4] if n > 0]
    m2 = (sum(ns2)/len(ns2)) if ns2 else None
    if m2 and r2 and r2 > m2: m2 = r2 # Aplica Recuperação 2

    # Média Final Projetada
    if m1 is not None and m2 is not None: return (m1 + m2) / 2
    elif m1 is not None: return m1
    elif m2 is not None: return m2
    
    return 0.0

# 1. TELA INICIAL
class CompararIndexView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/comparar_index.html'

# 2. REDIRECIONAMENTOS
@login_required
def selecionar_alunos(request):
    return redirect('/alunos/?modo_comparacao=true')

@login_required
def selecionar_turmas(request):
    return redirect('/turmas/?modo_comparacao=true')

# 3. COMPARAR ALUNOS (REFATORADO)
def comparar_alunos_resultado(request):
    id1 = request.GET.get('id1')
    id2 = request.GET.get('id2')
    
    if not id1 or not id2: return redirect('comparar_index')

    aluno1 = get_object_or_404(Aluno, pk=id1)
    aluno2 = get_object_or_404(Aluno, pk=id2)

    def get_dados_aluno(aluno_obj):
        boletins = Boletim.objects.filter(aluno_matricula=aluno_obj).select_related('disciplina', 'disciplina__area_do_conhecimento')
        
        soma, qtd = 0, 0
        melhor = {'nome': '-', 'nota': 0}
        pior = {'nome': '-', 'nota': 11}
        notas_disc = {} 

        for b in boletins:
            # AQUI ESTÁ A MUDANÇA: Usa a lógica híbrida
            nota_final = calcular_nota_hibrida(b)
            
            if nota_final > 0:
                # Arredonda para 1 casa decimal para bater com os outros painéis
                nota_final = round(nota_final, 1)
                
                soma += nota_final
                qtd += 1
                notas_disc[b.disciplina.descricao] = nota_final
                
                if nota_final > melhor['nota']: melhor = {'nome': b.disciplina.descricao, 'nota': nota_final}
                if nota_final < pior['nota']: pior = {'nome': b.disciplina.descricao, 'nota': nota_final}
        
        media_geral = round(soma / qtd, 1) if qtd > 0 else 0
        if pior['nota'] == 11: pior = {'nome': '-', 'nota': '-'}

        # Radar (Áreas) com Lógica Híbrida
        areas = AreaDoConhecimento.objects.all().order_by('descricao')
        r_labels, r_values = [], []
        for area in areas:
            r_labels.append(area.descricao)
            bs = [b for b in boletins if b.disciplina.area_do_conhecimento_id == area.id]
            
            notas_area = []
            for b in bs:
                n = calcular_nota_hibrida(b)
                if n > 0: notas_area.append(n)
            
            r_values.append(round(sum(notas_area)/len(notas_area), 1) if notas_area else 0)

        return {'obj': aluno_obj, 'media_geral': media_geral, 'melhor': melhor, 'pior': pior, 
                'radar_labels': r_labels, 'radar_data': r_values, 'notas_disc': notas_disc}

    d1 = get_dados_aluno(aluno1)
    d2 = get_dados_aluno(aluno2)

    all_discs = sorted(list(set(list(d1['notas_disc'].keys()) + list(d2['notas_disc'].keys()))))
    
    context = {
        'aluno1': d1, 'aluno2': d2,
        'bar_labels': json.dumps(all_discs),
        'bar_data1': json.dumps([d1['notas_disc'].get(d, 0) for d in all_discs]),
        'bar_data2': json.dumps([d2['notas_disc'].get(d, 0) for d in all_discs]),
        'radar_labels': json.dumps(d1['radar_labels']),
        'radar_data1': json.dumps(d1['radar_data']),
        'radar_data2': json.dumps(d2['radar_data']),
    }
    return render(request, 'dashboard/comparar_resultado.html', context)


# 4. COMPARAR TURMAS (REFATORADO E PADRONIZADO)
def comparar_turmas_resultado(request):
    id1 = request.GET.get('id1')
    id2 = request.GET.get('id2')

    if not id1 or not id2:
        return redirect('comparar_index')

    turma1 = get_object_or_404(Turma, pk=id1)
    turma2 = get_object_or_404(Turma, pk=id2)

    def get_dados_turma(turma_obj):
        qtd_alunos = AlunoTurma.objects.filter(turma_id=turma_obj.id).count()
        boletins = Boletim.objects.filter(turma_id=turma_obj.id).select_related(
            'disciplina', 'disciplina__area_do_conhecimento'
        )

        bims = {'b1': [], 'b2': [], 'b3': [], 'b4': []}
        medias_finais_calculadas = [] 

        for b in boletins:
            # Coleta dados para o gráfico de linha (bimestral)
            n1, n2 = safe_float(b.bimestre1), safe_float(b.bimestre2)
            n3, n4 = safe_float(b.bimestre3), safe_float(b.bimestre4)

            if n1: bims['b1'].append(n1)
            if n2: bims['b2'].append(n2)
            if n3: bims['b3'].append(n3)
            if n4: bims['b4'].append(n4)
            
            # AQUI A MUDANÇA: Usa a mesma função robusta do aluno
            nota_computada = calcular_nota_hibrida(b)
            
            if nota_computada > 0:
                medias_finais_calculadas.append(nota_computada)
                # Salva no objeto para usar no Radar logo abaixo
                b.nota_computada = nota_computada 
            else:
                b.nota_computada = 0

        # Médias Bimestrais (Gráfico de Linha)
        medias_bim = [
            round(sum(bims['b1'])/len(bims['b1']), 1) if bims['b1'] else 0,
            round(sum(bims['b2'])/len(bims['b2']), 1) if bims['b2'] else 0,
            round(sum(bims['b3'])/len(bims['b3']), 1) if bims['b3'] else 0,
            round(sum(bims['b4'])/len(bims['b4']), 1) if bims['b4'] else 0
        ]

        # Média Geral da Turma (Baseada na lógica Híbrida)
        media_geral = round(sum(medias_finais_calculadas)/len(medias_finais_calculadas), 1) if medias_finais_calculadas else 0
        
        # Radar Inteligente (Usa a nota_computada calculada acima)
        areas = AreaDoConhecimento.objects.all().order_by('descricao')
        r_labels, r_values = [], []

        # Tenta por Área
        tem_dados_area = False
        if areas.exists():
            for area in areas:
                bs_area = [b for b in boletins if b.disciplina.area_do_conhecimento_id == area.id]
                notas = [b.nota_computada for b in bs_area if b.nota_computada > 0]
                
                val = round(sum(notas)/len(notas), 1) if notas else 0
                r_labels.append(area.descricao)
                r_values.append(val)
                if val > 0: tem_dados_area = True
        
        # Se não tiver dados de área, faz por disciplina (Top 7)
        if not tem_dados_area:
            r_labels, r_values = [], []
            nomes_discs = sorted(list(set([b.disciplina.descricao for b in boletins])))[:7]
            for nome in nomes_discs:
                bs_disc = [b for b in boletins if b.disciplina.descricao == nome]
                notas = [b.nota_computada for b in bs_disc if b.nota_computada > 0]
                
                val = round(sum(notas)/len(notas), 1) if notas else 0
                r_labels.append(nome)
                r_values.append(val)

        return {
            'obj': turma_obj, 'qtd_alunos': qtd_alunos, 'media_geral': media_geral,
            'medias_bimestrais': medias_bim, 'radar_labels': r_labels, 'radar_data': r_values
        }

    d1 = get_dados_turma(turma1)
    d2 = get_dados_turma(turma2)

    radar_labels_final = d1['radar_labels'] if len(d1['radar_labels']) >= len(d2['radar_labels']) else d2['radar_labels']

    context = {
        'turma1': d1, 'turma2': d2,
        'line_labels': json.dumps(['1º Bim', '2º Bim', '3º Bim', '4º Bim']),
        'line_data1': json.dumps(d1['medias_bimestrais']),
        'line_data2': json.dumps(d2['medias_bimestrais']),
        'radar_labels': json.dumps(radar_labels_final),
        'radar_data1': json.dumps(d1['radar_data']),
        'radar_data2': json.dumps(d2['radar_data']),
    }

    return render(request, 'dashboard/comparar_turmas_resultado.html', context)
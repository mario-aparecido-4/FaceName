from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from ..models import Turma, Boletim, Disciplina, AlunoTurma
from django.db.models import Max
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

# --- Função Auxiliar de Conversão ---
def safe_float(val):
    try:
        if val is None or val == '': return None
        if isinstance(val, (int, float)): return float(val)
        return float(str(val).replace(',', '.'))
    except:
        return None

# --- Função de Cálculo de Nota ---
def calcular_nota_real_boletim(b):
    nf = safe_float(b.final)
    if nf is not None and nf > 0: return nf
    
    b1, b2 = safe_float(b.bimestre1), safe_float(b.bimestre2)
    rec1 = safe_float(b.recusem1)
    b3, b4 = safe_float(b.bimestre3), safe_float(b.bimestre4)
    rec2 = safe_float(b.recusem2)

    notas_s1 = [n for n in [b1, b2] if n is not None]
    media1 = sum(notas_s1)/len(notas_s1) if notas_s1 else None
    if media1 is not None and rec1 is not None and rec1 > media1: media1 = rec1

    notas_s2 = [n for n in [b3, b4] if n is not None]
    media2 = sum(notas_s2)/len(notas_s2) if notas_s2 else None
    if media2 is not None and rec2 is not None and rec2 > media2: media2 = rec2

    if media1 is not None and media2 is not None: return (media1 + media2) / 2
    elif media1 is not None: return media1
    elif media2 is not None: return media2
    return 0.0

# ==========================================
# VIEW 1: ÍNDICE GERAL (MOSTRA TUDO)
# ==========================================
class DisciplinasIndexView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/disciplinas_index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Busca os dados DE TODA A HISTÓRIA DO BANCO
        # Removemos o filtro de ano. Queremos saber quais matérias existem em cada série,
        # independente se foi em 2023, 2024 ou 2025.
        dados_boletins = Boletim.objects.all().values(
            'disciplina__id', 
            'disciplina__descricao', 
            'turma_id'
        ).distinct()

        # 2. Mapeia Turmas para descobrir a Série
        ids_turmas = set([d['turma_id'] for d in dados_boletins if d['turma_id']])
        turmas_db = Turma.objects.filter(id__in=ids_turmas).select_related('serie')
        turma_map = {t.id: t for t in turmas_db}

        # 3. Agrupamento (Série -> Disciplinas)
        mapa_series = {}
        disciplinas_vistas = set() # Evita duplicatas (Ex: Mat 1º Ano 2022 e Mat 1º Ano 2023 aparecem só uma vez)

        for item in dados_boletins:
            t_obj = turma_map.get(item['turma_id'])
            
            # Pega o nome da série (ou "Sem Série")
            if t_obj and t_obj.serie:
                serie_nome = t_obj.serie.descricao
                serie_id = t_obj.serie.id
            else:
                serie_nome = "Série Não Definida"
                serie_id = 0

            disc_id = item['disciplina__id']
            disc_nome = item['disciplina__descricao']
            
            # Chave composta para garantir unicidade visual
            chave_unica = (serie_nome, disc_id)

            if chave_unica not in disciplinas_vistas:
                disciplinas_vistas.add(chave_unica)
                
                if serie_nome not in mapa_series:
                    mapa_series[serie_nome] = []
                
                mapa_series[serie_nome].append({
                    'id': disc_id,
                    'nome': disc_nome,
                    'serie_id': serie_id 
                })

        # 4. Ordenação
        lista_ordenada = []
        for serie in sorted(mapa_series.keys()):
            discs = sorted(mapa_series[serie], key=lambda x: x['nome'])
            lista_ordenada.append({'serie': serie, 'disciplinas': discs})

        context['organizacao'] = lista_ordenada
        return context

# ==========================================
# VIEW 2: DETALHES (FILTRO DINÂMICO DE ANO)
# ==========================================
class DisciplinaDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/disciplina_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        disc_id = self.kwargs.get('pk')
        serie_id = self.request.GET.get('serie_id') 
        disciplina = get_object_or_404(Disciplina, pk=disc_id)
        
        # --- LÓGICA DE ANO DINÂMICO ---
        # Se temos uma série selecionada (ex: 1º Ano), descobrimos qual é o 
        # ano MAIS RECENTE registrado para essa série específica.
        # 1º Ano -> vai achar 2023
        # 3º Ano -> vai achar 2025
        ano_alvo = None
        
        if serie_id and serie_id != '0':
            target_serie_id = int(serie_id)
            # Busca o maior ano onde existe turma dessa série
            ano_alvo = Turma.objects.filter(serie_id=target_serie_id).aggregate(Max('ano'))['ano__max']
        
        # Se não achou ano específico (ou não tem série), usa o maior ano global do banco
        if not ano_alvo:
            ano_alvo = Turma.objects.aggregate(Max('ano'))['ano__max']

        # --- BUSCA DOS DADOS ---
        # Agora buscamos os boletins usando esse ano "inteligente"
        filtros = {
            'disciplina_id': disc_id, 
            'turma_ano': ano_alvo # Aqui está a mágica: 2023 para uns, 2025 para outros
        }

        # Busca Boletins
        boletins = Boletim.objects.filter(**filtros).select_related('aluno_matricula')

        # Busca Turmas para os nomes
        ids_turmas_boletins = set([b.turma_id for b in boletins])
        turmas_db = Turma.objects.filter(id__in=ids_turmas_boletins).select_related('serie')
        turma_map = {t.id: t for t in turmas_db}

        notas_alunos = []
        medias_por_turma = {}
        soma_geral = 0
        qtd_geral = 0

        target_serie_id = int(serie_id) if serie_id and serie_id != '0' else None

        for b in boletins:
            t_obj = turma_map.get(b.turma_id)
            
            # Filtro extra de segurança: garante que é a série certa
            if target_serie_id:
                if not t_obj or not t_obj.serie or t_obj.serie.id != target_serie_id:
                    continue
            
            if not t_obj: continue

            nota = calcular_nota_real_boletim(b)
            if nota > 0:
                nota_arredondada = round(nota, 1)
                
                notas_alunos.append({
                    'nome': b.aluno_matricula.nome,
                    'turma': t_obj.descricao,
                    'media': nota_arredondada,
                    'foto': getattr(b.aluno_matricula, 'foto', None)
                })

                nome_turma = t_obj.descricao
                if nome_turma not in medias_por_turma:
                    medias_por_turma[nome_turma] = []
                medias_por_turma[nome_turma].append(nota_arredondada)

                soma_geral += nota_arredondada
                qtd_geral += 1

        # Estatísticas finais
        media_geral = round(soma_geral / qtd_geral, 1) if qtd_geral > 0 else 0

        notas_alunos.sort(key=lambda x: x['media'], reverse=True)
        top_5 = notas_alunos[:5]
        bottom_5 = sorted(notas_alunos, key=lambda x: x['media'])[:5]

        labels_grafico = []
        data_grafico = []
        for turma in sorted(medias_por_turma.keys()):
            notas = medias_por_turma[turma]
            media_t = sum(notas) / len(notas)
            labels_grafico.append(turma)
            data_grafico.append(round(media_t, 1))

        context.update({
            'disciplina': disciplina,
            'media_geral': media_geral,
            'top_5': top_5,
            'bottom_5': bottom_5,
            'chart_labels': json.dumps(labels_grafico),
            'chart_data': json.dumps(data_grafico),
            'ano_exibido': ano_alvo # Debug visual útil
        })

        return context
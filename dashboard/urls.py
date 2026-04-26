from django.urls import path
from django.contrib.auth import views as auth_views
from .views import home, alunos, turmas, cursos, importacao, impfotos, comparacao, disciplinas

urlpatterns = [
    # =============================================================
    # 🏠 PÁGINAS INICIAIS
    # =============================================================

    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('', home.Inicio.as_view(), name='inicio'),
    path('disciplinas/', disciplinas.DisciplinasIndexView.as_view(), name='disciplinas_index'),
    path('disciplinas/<int:pk>/', disciplinas.DisciplinaDetailView.as_view(), name='disciplina_detail'),

    # =============================================================
    # 🎓 GESTÃO DE ALUNOS
    # =============================================================
    path('alunos/', alunos.AlunoListView.as_view(), name='aluno_list'),
    path('alunos/<str:matricula>/', alunos.AlunoDetailView.as_view(), name='aluno_detail'),

    # =============================================================
    # 🏫 GESTÃO DE TURMAS
    # =============================================================
    path('turmas/', turmas.TurmaListView.as_view(), name='turma_list'),
    path('turmas/<str:id>/<int:ano>/', turmas.TurmaDetailView.as_view(), name='turma_detail'),
    
    # Rota de compatibilidade (para menus que chamam {% url 'cursos' %})
    path('turmas-lista/', turmas.TurmaListView.as_view(), name='cursos'), 

    # =============================================================
    # 📚 CURSOS (VISÃO GERAL)
    # =============================================================
    path('cursos-selecao/', cursos.CursoSelectionView.as_view(), name='curso_selection'),
    path('curso-detalhe/<int:pk>/', cursos.CursoDetailView.as_view(), name='curso_detail'),

    # =============================================================
    # ⚖️ MÓDULO DE COMPARAÇÃO
    # =============================================================
    # Index da Comparação
    path('comparar/', comparacao.CompararIndexView.as_view(), name='comparar_index'),
    
    # Comparativo: Aluno vs Aluno
    path('comparar/selecionar-alunos/', comparacao.selecionar_alunos, name='comparar_selecao_alunos'),
    path('comparar/resultado/', comparacao.comparar_alunos_resultado, name='comparar_resultado'),

    # Comparativo: Turma vs Turma
    path('comparar/selecionar-turmas/', comparacao.selecionar_turmas, name='comparar_selecao_turmas'),
    path('comparar/turmas-resultado/', comparacao.comparar_turmas_resultado, name='comparar_turmas_resultado'),

    # =============================================================
    # 🛠️ FERRAMENTAS E IMPORTAÇÃO
    # =============================================================
    path('importar-turma/', importacao.importar_turma, name='importar_turma'), 
    path('importar-fotos/', impfotos.importar_fotos, name='importar_fotos'), 
]
from django import forms
from .models import Curso, Serie, Turno, Turma

# Definindo as opções para o novo campo de seleção
PERIODO_CHOICES = [
    ('COMPLETO', 'Completo (todas as notas)'),
    ('B1', '1º Bimestre'),
    ('B2', '2º Bimestre'),
    ('R1', '1ª Recuperação'),
    ('B3', '3º Bimestre'),
    ('B4', '4º Bimestre'),
    ('R2', '2ª Recuperação'),
    ('RF', 'Recuperação Final'),
]

class TurmaCompletaImportForm(forms.Form):
    # Campos que o usuário vai preencher
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.all(),
        label="Curso"
    )
    serie = forms.ModelChoiceField(
        queryset=Serie.objects.all(), 
        label="Série"
    )
    turno = forms.ModelChoiceField(
        queryset=Turno.objects.all(), 
        label="Turno"
    )
    ano = forms.IntegerField(
        label="Ano vigente da turma",
        help_text="Ex: 2025"
    )
    turma_anterior = forms.ModelChoiceField(
        queryset=Turma.objects.all().order_by('-ano', 'id'),
        required=False,
        label="Turma Anterior (Opcional)"
    )
    
    periodo_importacao = forms.ChoiceField(
        choices=PERIODO_CHOICES,
        label="Importar notas até qual período?",
        help_text="Selecione para evitar que notas futuras sejam zeradas."
    )

    planilha = forms.FileField(label="Anexar Planilha de Notas (.xlsx ou xls)")

class FotoAlunoImportForm(forms.Form):
    fotos = forms.FileField(
        label="Selecionar Fotos dos Alunos",
        help_text="Selecione múltiplas fotos (JPG, PNG, GIF). O nome de cada arquivo DEVE ser a matrícula do aluno (ex: 12345678.jpg)."
    )
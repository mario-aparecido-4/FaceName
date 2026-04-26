import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from ..forms import FotoAlunoImportForm
from ..models import Aluno
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

# Não precisa do @transaction.atomic aqui, pois cada foto é salva individualmente.
@login_required
def importar_fotos(request):
    if request.method == 'POST':
        form = FotoAlunoImportForm(request.POST, request.FILES)
        if form.is_valid():
            # request.FILES.getlist pega todos os arquivos enviados no campo 'fotos'
            arquivos_fotos = request.FILES.getlist('fotos')
            
            fotos_importadas = 0
            alunos_nao_encontrados = 0
            erros_inesperados = 0
            nomes_nao_encontrados = []

            for uploaded_file in arquivos_fotos:
                try:
                    # Pega o nome do arquivo (ex: '12345678.jpg')
                    nome_arquivo = uploaded_file.name
                    # Extrai a matrícula (ex: '12345678')
                    matricula_aluno = os.path.splitext(nome_arquivo)[0]

                    # Tenta encontrar o aluno
                    aluno = Aluno.objects.get(matricula=matricula_aluno)
                    
                    # Se encontrou, atribui a foto diretamente ao ImageField
                    # O Django cuida de salvar no local correto (MEDIA_ROOT)
                    aluno.foto = uploaded_file
                    aluno.save()
                    
                    fotos_importadas += 1

                except Aluno.DoesNotExist:
                    alunos_nao_encontrados += 1
                    nomes_nao_encontrados.append(nome_arquivo)
                except Exception as e:
                    # Captura outros erros (permissão de escrita, arquivo corrompido, etc.)
                    erros_inesperados += 1
                    messages.error(request, f"Erro ao processar o arquivo '{nome_arquivo}': {e}")

            # Monta as mensagens de feedback para o usuário
            if fotos_importadas > 0:
                messages.success(request, f"{fotos_importadas} foto(s) importada(s) com sucesso!")
            if alunos_nao_encontrados > 0:
                messages.warning(request, f"{alunos_nao_encontrados} foto(s) ignorada(s): Aluno não encontrado para os arquivos: {', '.join(nomes_nao_encontrados)}")
            if erros_inesperados > 0:
                 messages.error(request, f"Ocorreram {erros_inesperados} erro(s) inesperado(s) durante o processamento. Verifique as mensagens acima.")

            # Limpa o formulário após o processamento
            form = FotoAlunoImportForm()

    else: # Se for GET
        form = FotoAlunoImportForm()

    return render(request, 'importacao/importar_fotos.html', {'form': form})

import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from faker import Faker

from dashboard_app.models import (
    AreaDoConhecimento, Curso, Serie, Turno, Disciplina,
    Turma, Aluno, AlunoTurma, Boletim, DisciplinaCursoSerie
)

class Command(BaseCommand):
    help = 'Popula o banco com um currículo canônico (disciplinas pertencem a um único curso fonte).'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando o povoamento com currículo canônico...'))
        
        fake = Faker('pt_BR')

        with connection.cursor() as cursor:
            self.stdout.write('Desativando a checagem de chaves estrangeiras...')
            cursor.execute("SET FOREIGN_KEY_CHECKS=0;")

        self.stdout.write('Limpando dados antigos...')
        Boletim.objects.all().delete()
        AlunoTurma.objects.all().delete()
        Aluno.objects.all().delete()
        DisciplinaCursoSerie.objects.all().delete()
        Turma.objects.all().delete()
        Disciplina.objects.all().delete()
        AreaDoConhecimento.objects.all().delete()
        Curso.objects.all().delete()
        Serie.objects.all().delete()
        Turno.objects.all().delete()

        with connection.cursor() as cursor:
            self.stdout.write('Reativando a checagem de chaves estrangeiras...')
            cursor.execute("SET FOREIGN_KEY_CHECKS=1;")

        self.stdout.write(self.style.SUCCESS('Banco de dados limpo com sucesso!'))
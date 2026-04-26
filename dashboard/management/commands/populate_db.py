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

        self.stdout.write('Criando dados básicos (Cursos, Séries, etc)...')
        areas = {desc: AreaDoConhecimento.objects.create(id=i+1, descricao=desc) for i, desc in enumerate(['Técnica', 'Humanas', 'Matemática', 'Linguagem', 'Natureza'])}
        cursos = {desc: Curso.objects.create(id=i+1, descricao=desc) for i, desc in enumerate(['Técnico em Informática', 'Técnico em Eletrotécnica', 'Técnico em Segurança do Trabalho', 'Técnico em Edificações', 'Ensino Médio'])}
        series = {f'{i}º Ano': Serie.objects.create(id=i, descricao=f'{i}º Ano') for i in range(1, 4)}
        turnos = {desc: Turno.objects.create(id=i+1, descricao=desc) for i, desc in enumerate(['Matutino', 'Vespertino'])}

        # =====================================================================================
        # SEÇÃO 2: DEFINIÇÃO DO CURRÍCULO E CRIAÇÃO DAS DISCIPLINAS
        # =====================================================================================
        self.stdout.write('Criando disciplinas e o currículo canônico...')
        
        disciplinas_base_comum = [
            {'sigla': 'LIPO', 'desc': 'Língua Portuguesa', 'area': areas['Linguagem'], 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'LIIN', 'desc': 'Língua Inglesa', 'area': areas['Linguagem'], 'series': [series['1º Ano'], series['2º Ano']]},
            {'sigla': 'LIES', 'desc': 'Língua Espanhola', 'area': areas['Linguagem'], 'series': [series['3º Ano']]},
            {'sigla': 'MATE', 'desc': 'Matemática', 'area': areas['Matemática'], 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'HIST', 'desc': 'História', 'area': areas['Humanas'], 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'GEOG', 'desc': 'Geografia', 'area': areas['Humanas'], 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'FISI', 'desc': 'Física', 'area': areas['Natureza'], 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'QUIM', 'desc': 'Química', 'area': areas['Natureza'], 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'FILO', 'desc': 'Filosofia', 'area': areas['Humanas'], 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'SOCI', 'desc': 'Sociologia', 'area': areas['Humanas'], 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'BIOL', 'desc': 'Biologia', 'area': areas['Natureza'], 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'ARTE', 'desc': 'Artes', 'area': areas['Linguagem'], 'series': [series['1º Ano']]},
            {'sigla': 'EDFI', 'desc': 'Educação Física', 'area': areas['Natureza'], 'series': [series['1º Ano'], series['2º Ano']]}
        ]

        disciplinas_tecnicas = [
            #INFORMÁTICA
            #1
            {'sigla': 'INPR', 'desc': 'Introdução a Programação', 'area': areas['Técnica'], 'curso': cursos['Técnico em Informática'], 'serie': series['1º Ano']},
            {'sigla': 'FDIN', 'desc': 'Fundamentos da Informática', 'area': areas['Técnica'], 'curso': cursos['Técnico em Informática'], 'serie': series['1º Ano']},
            {'sigla': 'MMCO', 'desc': 'Montagem e Manutenção de Computadores', 'area': areas['Técnica'], 'curso': cursos['Técnico em Informática'], 'serie': series['1º Ano']},
            {'sigla': 'SEGT', 'desc': 'Seg. do Trabalho', 'area': areas['Técnica'], 'curso': cursos['Técnico em Informática'], 'serie': series['1º Ano']},

            #2
            {'sigla': 'BADA', 'desc': 'Banco de Dados', 'area': areas['Técnica'], 'curso': cursos['Técnico em Informática'], 'serie': series['2º Ano']},
            {'sigla': 'INRC', 'desc': 'Introdução a Redes de Computadores', 'area': areas['Técnica'], 'curso': cursos['Técnico em Informática'], 'serie': series['2º Ano']},
            {'sigla': 'PROO', 'desc': 'Programação Orientada a Objetos', 'area': areas['Técnica'], 'curso': cursos['Técnico em Informática'], 'serie': series['2º Ano']},
            {'sigla': 'ENSO', 'desc': 'Engenharia de Software', 'area': areas['Técnica'], 'curso': cursos['Técnico em Informática'], 'serie': series['2º Ano']},

            #3
            {'sigla': 'PRWE', 'desc': 'Programação Web', 'area': areas['Técnica'], 'curso': cursos['Técnico em Informática'], 'serie': series['3º Ano']},
            {'sigla': 'PRMO', 'desc': 'Programação Móvel', 'area': areas['Técnica'], 'curso': cursos['Técnico em Informática'], 'serie': series['3º Ano']},
            {'sigla': 'EMDI', 'desc': 'Emprendedorismo Digital', 'area': areas['Técnica'], 'curso': cursos['Técnico em Informática'], 'serie': series['3º Ano']},
            {'sigla': 'ISRC', 'desc': 'Infraestrutura e Serviços de Redes de Computadores', 'area': areas['Técnica'], 'curso': cursos['Técnico em Informática'], 'serie': series['3º Ano']},

            #ELETROTÉCNICA
            #1
            {'sigla': 'DTEC', 'desc': 'Desenho Técnico I', 'area': areas['Técnica'], 'curso': cursos['Técnico em Eletrotécnica'], 'serie': series['1º Ano']},
            {'sigla': 'IAPL', 'desc': 'Informática Aplicada', 'area': areas['Técnica'], 'curso': cursos['Técnico em Eletrotécnica'], 'serie': series['1º Ano']},
            {'sigla': 'LABE', 'desc': 'Laboratório de Eletrecidade', 'area': areas['Técnica'], 'curso': cursos['Técnico em Eletrotécnica'], 'serie': series['1º Ano']},
            {'sigla': 'INST', 'desc': 'Instalações Elétricas', 'area': areas['Técnica'], 'curso': cursos['Técnico em Eletrotécnica'], 'serie': series['1º Ano']},
            
            #2
            {'sigla': 'GOST', 'desc': 'Gestão Organizacional e Segurança do Trabalho', 'area': areas['Técnica'], 'curso': cursos['Técnico em Eletrotécnica'], 'serie': series['2º Ano']},
            {'sigla': 'AELE', 'desc': 'Acionamentos Elétricos', 'area': areas['Técnica'], 'curso': cursos['Técnico em Eletrotécnica'], 'serie': series['2º Ano']},
            {'sigla': 'DEEL', 'desc': 'Distribuição de Energia Elétrica', 'area': areas['Técnica'], 'curso': cursos['Técnico em Eletrotécnica'], 'serie': series['2º Ano']},
            {'sigla': 'ELET', 'desc': 'Eletricidade', 'area': areas['Técnica'], 'curso': cursos['Técnico em Eletrotécnica'], 'serie': series['2º Ano']},
            {'sigla': 'PREP', 'desc': 'Projetos Elétricos Prediais', 'area': areas['Técnica'], 'curso': cursos['Técnico em Eletrotécnica'], 'serie': series['2º Ano']},
            
            #3
            {'sigla': 'AUIN', 'desc': 'Automação Industrial', 'area': areas['Técnica'], 'curso': cursos['Técnico em Eletrotécnica'], 'serie': series['3º Ano']},
            {'sigla': 'EBIN', 'desc': 'Eletrônica Básica e Industrial', 'area': areas['Técnica'], 'curso': cursos['Técnico em Eletrotécnica'], 'serie': series['3º Ano']},
            {'sigla': 'GEFE', 'desc': 'Geração e Eficiência Energética', 'area': areas['Técnica'], 'curso': cursos['Técnico em Eletrotécnica'], 'serie': series['3º Ano']},
            {'sigla': 'MANE', 'desc': 'Manutenção Elétrica', 'area': areas['Técnica'], 'curso': cursos['Técnico em Eletrotécnica'], 'serie': series['3º Ano']},
            {'sigla': 'MAEL', 'desc': 'Máquinas Elétricas', 'area': areas['Técnica'], 'curso': cursos['Técnico em Eletrotécnica'], 'serie': series['3º Ano']},
            {'sigla': 'PEIN', 'desc': 'Projetos Elétricos Industriais', 'area': areas['Técnica'], 'curso': cursos['Técnico em Eletrotécnica'], 'serie': series['3º Ano']},

            #EDIFICAÇÕES
            #1
            {'sigla': 'MATC', 'desc': 'Materiais de Construção', 'area': areas['Técnica'], 'curso': cursos['Técnico em Edificações'], 'serie': series['1º Ano']},
            {'sigla': 'INFO', 'desc': 'Informática', 'area': areas['Técnica'], 'curso': cursos['Técnico em Edificações'], 'serie': series['1º Ano']},
            {'sigla': 'DARI', 'desc': 'Desenho Arquitetônico I', 'area': areas['Técnica'], 'curso': cursos['Técnico em Edificações'], 'serie': series['1º Ano']},
            {'sigla': 'DEAC', 'desc': 'Desenho Assistido por Computador', 'area': areas['Técnica'], 'curso': cursos['Técnico em Edificações'], 'serie': series['1º Ano']},
            
            #2
            {'sigla': 'GEOS', 'desc': 'Gest. Organizacional e Segurança do Trabalho', 'area': areas['Técnica'], 'curso': cursos['Técnico em Edificações'], 'serie': series['2º Ano']},
            {'sigla': 'DAII', 'desc': 'Desenho Arquitetônico II', 'area': areas['Técnica'], 'curso': cursos['Técnico em Edificações'], 'serie': series['2º Ano']},
            {'sigla': 'TOPO', 'desc': 'Topografia', 'area': areas['Técnica'], 'curso': cursos['Técnico em Edificações'], 'serie': series['2º Ano']},
            {'sigla': 'ESCO', 'desc': 'Estabilidade das Construções', 'area': areas['Técnica'], 'curso': cursos['Técnico em Edificações'], 'serie': series['2º Ano']},
            {'sigla': 'SICO', 'desc': 'Sistemas Construtivos', 'area': areas['Técnica'], 'curso': cursos['Técnico em Edificações'], 'serie': series['2º Ano']},
            {'sigla': 'MESO', 'desc': 'Mecânica dos Solos', 'area': areas['Técnica'], 'curso': cursos['Técnico em Edificações'], 'serie': series['2º Ano']},
            
            #3
            {'sigla': 'PRAR', 'desc': 'Projeto Arquitetônico', 'area': areas['Técnica'], 'curso': cursos['Técnico em Edificações'], 'serie': series['3º Ano']},
            {'sigla': 'ELES', 'desc': 'Elementos Estruturais', 'area': areas['Técnica'], 'curso': cursos['Técnico em Edificações'], 'serie': series['3º Ano']},
            {'sigla': 'PIEP', 'desc': 'Projeto de Instalações Elétricas Prediais', 'area': areas['Técnica'], 'curso': cursos['Técnico em Edificações'], 'serie': series['3º Ano']},
            {'sigla': 'INHI', 'desc': 'Instalações Hidrossanitárias', 'area': areas['Técnica'], 'curso': cursos['Técnico em Edificações'], 'serie': series['3º Ano']},
            {'sigla': 'PLOB', 'desc': 'Planejamento de Obras', 'area': areas['Técnica'], 'curso': cursos['Técnico em Edificações'], 'serie': series['3º Ano']},
        
            #SEGURANÇA DO TRABALHO
            #1
            {'sigla': 'DETE', 'desc': 'Desenho Técnico', 'area': areas['Técnica'], 'curso': cursos['Técnico em Segurança do Trabalho'], 'serie': series['1º Ano']},
            {'sigla': 'LEST', 'desc': 'Legislação em Segurança do Trabalho', 'area': areas['Técnica'], 'curso': cursos['Técnico em Segurança do Trabalho'], 'serie': series['1º Ano']},
            {'sigla': 'MTPS', 'desc': 'Métodos e Técnicas de Primeiros Socorros', 'area': areas['Técnica'], 'curso': cursos['Técnico em Segurança do Trabalho'], 'serie': series['1º Ano']},

            #2
            {'sigla': 'ELTI', 'desc': 'Elaboração do Trabalho Intelectual', 'area': areas['Técnica'], 'curso': cursos['Técnico em Segurança do Trabalho'], 'serie': series['2º Ano']},
            {'sigla': 'SETR', 'desc': 'Segurança do Trabalho', 'area': areas['Técnica'], 'curso': cursos['Técnico em Segurança do Trabalho'], 'serie': series['2º Ano']},
            {'sigla': 'HITR', 'desc': 'Higiene do Trabalho', 'area': areas['Técnica'], 'curso': cursos['Técnico em Segurança do Trabalho'], 'serie': series['2º Ano']},
            {'sigla': 'SAOC', 'desc': 'Saúde Ocupacional', 'area': areas['Técnica'], 'curso': cursos['Técnico em Segurança do Trabalho'], 'serie': series['2º Ano']},
            {'sigla': 'ERGO', 'desc': 'Ergonomia', 'area': areas['Técnica'], 'curso': cursos['Técnico em Segurança do Trabalho'], 'serie': series['2º Ano']},
            {'sigla': 'ESAP', 'desc': 'Estatística Aplicada', 'area': areas['Técnica'], 'curso': cursos['Técnico em Segurança do Trabalho'], 'serie': series['2º Ano']},

            #3
            {'sigla': 'PPCI', 'desc': 'Projetos de Prevenção e Combate a Incêndio e Pânico', 'area': areas['Técnica'], 'curso': cursos['Técnico em Segurança do Trabalho'], 'serie': series['3º Ano']},
            {'sigla': 'PSST', 'desc': 'Programas de Saúde e Segurança do trabalho', 'area': areas['Técnica'], 'curso': cursos['Técnico em Segurança do Trabalho'], 'serie': series['3º Ano']},
            {'sigla': 'GERI', 'desc': 'Gerência de Riscos', 'area': areas['Técnica'], 'curso': cursos['Técnico em Segurança do Trabalho'], 'serie': series['3º Ano']},
            {'sigla': 'SIGE', 'desc': 'Sistemas Integrados de Gestão', 'area': areas['Técnica'], 'curso': cursos['Técnico em Segurança do Trabalho'], 'serie': series['3º Ano']},
            {'sigla': 'TEPI', 'desc': 'Tecnologias e Processos Industriais', 'area': areas['Técnica'], 'curso': cursos['Técnico em Segurança do Trabalho'], 'serie': series['3º Ano']},
        ]

        disciplinas_criadas = {}
        disciplina_id_counter = 1

        todas_as_disciplinas_data = disciplinas_base_comum + disciplinas_tecnicas
        for d in todas_as_disciplinas_data:
            if d['sigla'] not in disciplinas_criadas:
                disciplina_obj = Disciplina.objects.create(id=disciplina_id_counter, sigla=d['sigla'], descricao=d['desc'], area_do_conhecimento=d['area'])
                disciplinas_criadas[d['sigla']] = disciplina_obj
                disciplina_id_counter += 1

        disciplina_curso_serie_a_criar = []
        
        # --- LÓGICA ATUALIZADA ---
        # 1. Atribui a base comum APENAS ao curso "Ensino Médio"
        curso_ensino_medio = cursos['Ensino Médio']
        for d in disciplinas_base_comum:
            disciplina_obj = disciplinas_criadas[d['sigla']]
            for serie_obj in d['series']:
                disciplina_curso_serie_a_criar.append(DisciplinaCursoSerie(disciplina=disciplina_obj, curso=curso_ensino_medio, serie=serie_obj))
        
        # 2. Atribui as disciplinas técnicas aos seus respectivos cursos
        for d in disciplinas_tecnicas:
            disciplina_obj = disciplinas_criadas[d['sigla']]
            disciplina_curso_serie_a_criar.append(DisciplinaCursoSerie(disciplina=disciplina_obj, curso=d['curso'], serie=d['serie']))

        DisciplinaCursoSerie.objects.bulk_create(disciplina_curso_serie_a_criar)

        # Mapeia disciplinas por grade para fácil acesso
        disciplinas_por_grade = {}
        for dcs in DisciplinaCursoSerie.objects.all().select_related('disciplina', 'curso', 'serie'):
            chave = (dcs.curso_id, dcs.serie_id)
            if chave not in disciplinas_por_grade:
                disciplinas_por_grade[chave] = []
            disciplinas_por_grade[chave].append(dcs.disciplina)

        self.stdout.write('Gerando Turmas, Alunos e Boletins...')
        
        codigos_curso = {curso_obj.id: sigla for curso_obj, sigla in zip(cursos.values(), ['5', '4', 'S', '2', 'M'])}
        aluno_matricula_counter = 2025000001
        
        turmas_a_criar = []
        alunos_a_criar = []
        alunoturma_a_criar = []
        boletins_a_criar = []

        for curso_obj in [c for c in cursos.values() if c.descricao != 'Ensino Médio']:
            for serie_obj in series.values():
                for turno_obj in turnos.values():
                    codigo_turma = f"{codigos_curso[curso_obj.id]}{turno_obj.id}{serie_obj.id}"
                    
                    turma_obj = Turma(
                        id=codigo_turma, ano=2025, descricao=codigo_turma,
                        curso=curso_obj, serie=serie_obj, turno=turno_obj,
                        turma_id=0, turma_ano=0
                    )
                    turmas_a_criar.append(turma_obj)

                    # --- LÓGICA ATUALIZADA ---
                    # Busca as disciplinas da base comum (do Ensino Médio) E as disciplinas técnicas do curso atual
                    disciplinas_base = disciplinas_por_grade.get((curso_ensino_medio.id, serie_obj.id), [])
                    disciplinas_tecnicas = disciplinas_por_grade.get((curso_obj.id, serie_obj.id), [])
                    disciplinas_da_turma = disciplinas_base + disciplinas_tecnicas

                    for _ in range(10):
                        aluno_obj = Aluno(
                            matricula=str(aluno_matricula_counter),
                            nome=fake.name()
                        )
                        alunos_a_criar.append(aluno_obj)
                        
                        alunoturma_a_criar.append(AlunoTurma(
                            aluno_matricula=aluno_obj,
                            turma_id=turma_obj.id,
                            turma_ano=turma_obj.ano
                        ))

                        for disciplina_obj in disciplinas_da_turma:
                            boletins_a_criar.append(Boletim(
                                aluno_matricula=aluno_obj,
                                disciplina=disciplina_obj,
                                turma_id=turma_obj.id,
                                turma_ano=turma_obj.ano,
                                bimestre1=Decimal(random.uniform(5.0, 10.0)).quantize(Decimal('0.1')),
                                bimestre2=Decimal(random.uniform(5.0, 10.0)).quantize(Decimal('0.1')),
                                bimestre3=Decimal(random.uniform(5.0, 10.0)).quantize(Decimal('0.1'))
                            ))
                        
                        aluno_matricula_counter += 1

        self.stdout.write('Inserindo dados em massa no banco...')
        Turma.objects.bulk_create(turmas_a_criar)
        Aluno.objects.bulk_create(alunos_a_criar)
        AlunoTurma.objects.bulk_create(alunoturma_a_criar)
        Boletim.objects.bulk_create(boletins_a_criar)

        with connection.cursor() as cursor:
            self.stdout.write('Reativando a checagem de chaves estrangeiras...')
            cursor.execute("SET FOREIGN_KEY_CHECKS=1;")

        self.stdout.write(self.style.SUCCESS('Banco de dados populado com sucesso!'))
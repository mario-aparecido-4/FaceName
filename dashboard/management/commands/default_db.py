from django.core.management.base import BaseCommand
from django.db import transaction, connection
from dashboard_app.models import (
    AreaDoConhecimento, Curso, Serie, Turno, Disciplina, DisciplinaCursoSerie, Boletim, AlunoTurma, Aluno, Turma
)

class Command(BaseCommand):
    help = 'Popula o banco de dados com a estrutura curricular oficial da instituição.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando a população da base de dados curricular...'))
        
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

        self.stdout.write('Criando dados básicos (Áreas, Cursos, Séries, Turnos)...')
        areas = {desc: AreaDoConhecimento.objects.create(id=i+1, descricao=desc) for i, desc in enumerate(['Técnica', 'Humanas', 'Matemática', 'Linguagem', 'Natureza'])}
        cursos_data = ['Técnico em Informática', 'Técnico em Eletrotécnica', 'Técnico em Segurança do Trabalho', 'Técnico em Edificações']
        cursos = {desc: Curso.objects.create(id=i+1, descricao=desc) for i, desc in enumerate(cursos_data)}
        series = {f'{i}º Ano': Serie.objects.create(id=i, descricao=f'{i}º Ano') for i in range(1, 4)}
        turnos = {desc: Turno.objects.create(id=i+1, descricao=desc) for i, desc in enumerate(['Matutino', 'Vespertino'])}

        self.stdout.write('Definindo o currículo oficial...')
        
        cursos_tecnicos = list(cursos.values())

        curriculo_completo = [
            # Formação Geral
            {'sigla': 'LIPO', 'desc': 'LÍNGUA PORTUGUESA', 'area': areas['Linguagem'], 'cursos': cursos_tecnicos, 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'LIIN', 'desc': 'LÍNGUA INGLESA', 'area': areas['Linguagem'], 'cursos': cursos_tecnicos, 'series': [series['1º Ano'], series['2º Ano']]},
            {'sigla': 'LIES', 'desc': 'LÍNGUA ESPANHOLA', 'area': areas['Linguagem'], 'cursos': cursos_tecnicos, 'series': [series['3º Ano']]},
            {'sigla': 'ARTE', 'desc': 'ARTES', 'area': areas['Linguagem'], 'cursos': cursos_tecnicos, 'series': [series['1º Ano']]},
            {'sigla': 'HIST', 'desc': 'HISTÓRIA', 'area': areas['Humanas'], 'cursos': cursos_tecnicos, 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'GEOG', 'desc': 'GEOGRAFIA', 'area': areas['Humanas'], 'cursos': cursos_tecnicos, 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'FILO', 'desc': 'FILOSOFIA', 'area': areas['Humanas'], 'cursos': cursos_tecnicos, 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'SOCI', 'desc': 'SOCIOLOGIA', 'area': areas['Humanas'], 'cursos': cursos_tecnicos, 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'MATE', 'desc': 'MATEMÁTICA', 'area': areas['Matemática'], 'cursos': cursos_tecnicos, 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'FISI', 'desc': 'FÍSICA', 'area': areas['Natureza'], 'cursos': cursos_tecnicos, 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'QUIM', 'desc': 'QUÍMICA', 'area': areas['Natureza'], 'cursos': cursos_tecnicos, 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'BIOL', 'desc': 'BIOLOGIA', 'area': areas['Natureza'], 'cursos': cursos_tecnicos, 'series': [series['1º Ano'], series['2º Ano'], series['3º Ano']]},
            {'sigla': 'EDFI', 'desc': 'EDUCAÇÃO FÍSICA', 'area': areas['Natureza'], 'cursos': cursos_tecnicos, 'series': [series['1º Ano'], series['2º Ano']]},

            # Disciplinas Técnicas
            # Informática
            {'sigla': 'FINF', 'desc': 'FUNDAMENTOS DA INFORMÁTICA', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Informática']], 'series': [series['1º Ano']]},
            {'sigla': 'IPRG', 'desc': 'INTRODUÇÃO A PROGRAMAÇÃO', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Informática']], 'series': [series['1º Ano']]},
            {'sigla': 'MOMC', 'desc': 'MONTAGEM E MANUTENÇÃO DE COMPUTADORES', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Informática']], 'series': [series['1º Ano']]},
            {'sigla': 'BADA', 'desc': 'BANCO DE DADOS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Informática']], 'series': [series['2º Ano']]},
            {'sigla': 'SIOP', 'desc': 'SISTEMAS OPERACIONAIS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Informática']], 'series': [series['2º Ano']]},
            {'sigla': 'IRDC', 'desc': 'INTRODUÇÃO À REDE DE COMPUTADORES', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Informática']], 'series': [series['2º Ano']]},
            {'sigla': 'PROO', 'desc': 'PROGRAMAÇÃO ORIENTADA A OBJETOS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Informática']], 'series': [series['2º Ano']]},
            {'sigla': 'ENSO', 'desc': 'ENGENHARIA DE SOFTWARE', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Informática']], 'series': [series['2º Ano']]},
            {'sigla': 'PRWE', 'desc': 'PROGRAMAÇÃO WEB', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Informática']], 'series': [series['3º Ano']]},
            {'sigla': 'PRMO', 'desc': 'PROGRAMAÇÃO MÓVEL', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Informática']], 'series': [series['3º Ano']]},
            {'sigla': 'EMPD', 'desc': 'EMPREENDEDORISMO DIGITAL', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Informática']], 'series': [series['3º Ano']]},
            {'sigla': 'ISRD', 'desc': 'INFRAESTRUTURA E SERVIÇOS DE REDES', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Informática']], 'series': [series['3º Ano']]},

            # Eletrotécnica
            {'sigla': 'DET1', 'desc': 'DESENHO TÉCNICO', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Eletrotécnica']], 'series': [series['1º Ano']]},
            {'sigla': 'INAP', 'desc': 'INFORMÁTICA APLICADA', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Eletrotécnica']], 'series': [series['1º Ano']]},
            {'sigla': 'ISEL', 'desc': 'INSTALAÇÕES ELÉTRICAS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Eletrotécnica'], cursos['Técnico em Segurança do Trabalho']], 'series': [series['1º Ano']]},
            {'sigla': 'LABE', 'desc': 'LABORATÓRIO DE ELETRICIDADE', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Eletrotécnica']], 'series': [series['1º Ano']]},
            {'sigla': 'AELE', 'desc': 'ACIONAMENTOS ELÉTRICOS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Eletrotécnica']], 'series': [series['2º Ano']]},
            {'sigla': 'DDEE', 'desc': 'DISTRIBUIÇÃO DE ENERGIA ELÉTRICA', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Eletrotécnica']], 'series': [series['2º Ano']]},
            {'sigla': 'ELE2', 'desc': 'ELETRICIDADE', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Eletrotécnica']], 'series': [series['2º Ano']]},
            {'sigla': 'GOST', 'desc': 'GESTÃO ORGANIZACIONAL E SEGURANÇA DO TRABALHO', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Eletrotécnica'], cursos['Técnico em Edificações']], 'series': [series['2º Ano']]},
            {'sigla': 'PREP', 'desc': 'PROJETOS ELÉTRICOS PREDIAIS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Eletrotécnica']], 'series': [series['2º Ano']]},
            {'sigla': 'AUIN', 'desc': 'AUTOMAÇÃO INDUSTRIAL', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Eletrotécnica']], 'series': [series['3º Ano']]},
            {'sigla': 'ELBI', 'desc': 'ELETRÔNICA BÁSICA E INDUSTRIAL', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Eletrotécnica']], 'series': [series['3º Ano']]},
            {'sigla': 'GEEE', 'desc': 'GERAÇÃO E EFICIÊNCIA ENERGÉTICA', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Eletrotécnica']], 'series': [series['3º Ano']]},
            {'sigla': 'MANE', 'desc': 'MANUTENÇÃO ELÉTRICA', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Eletrotécnica']], 'series': [series['3º Ano']]},
            {'sigla': 'MAQ2', 'desc': 'MÁQUINAS ELÉTRICAS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Eletrotécnica']], 'series': [series['3º Ano']]},
            {'sigla': 'PREI', 'desc': 'PROJETOS ELÉTRICOS INDUSTRIAIS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Eletrotécnica']], 'series': [series['3º Ano']]},

            # Segurança do Trabalho
            {'sigla': 'DTAT', 'desc': 'DESENHO TÉCNICO APLICADO E SUAS TECNOLOGIAS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Segurança do Trabalho']], 'series': [series['1º Ano']]},
            {'sigla': 'LEST', 'desc': 'LEGISLAÇÃO EM SEGURANÇA DO TRABALHO', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Segurança do Trabalho']], 'series': [series['1º Ano']]},
            {'sigla': 'MTPS', 'desc': 'MÉTODOS E TÉCNICAS DE PRIMEIROS SOCORROS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Segurança do Trabalho']], 'series': [series['1º Ano']]},
            {'sigla': 'ELTI', 'desc': 'ELABORAÇÃO DO TRABALHO INTELECTUAL', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Segurança do Trabalho']], 'series': [series['2º Ano']]},
            {'sigla': 'EFCO', 'desc': 'ERGONOMIA FÍSICA, COGNITIVA E ORGANIZACIONAL', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Segurança do Trabalho']], 'series': [series['2º Ano']]},
            {'sigla': 'ESTA', 'desc': 'ESTATÍSTICA APLICADA', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Segurança do Trabalho']], 'series': [series['2º Ano']]},
            {'sigla': 'HIGT', 'desc': 'HIGIENE DO TRABALHO', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Segurança do Trabalho']], 'series': [series['2º Ano']]},
            {'sigla': 'SAOC', 'desc': 'SAÚDE OCUPACIONAL', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Segurança do Trabalho']], 'series': [series['2º Ano']]},
            {'sigla': 'GERI', 'desc': 'GERÊNCIA DE RISCOS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Segurança do Trabalho']], 'series': [series['3º Ano']]},
            {'sigla': 'PSST', 'desc': 'PROGRAMAS DE SAÚDE E SEGURANÇA DO TRABALHO', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Segurança do Trabalho']], 'series': [series['3º Ano']]},
            {'sigla': 'PCIP', 'desc': 'PROJETOS DE PREVENÇÃO E COMBATE A INCÊNDIO E PÂNICO', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Segurança do Trabalho']], 'series': [series['3º Ano']]},
            {'sigla': 'SIIG', 'desc': 'SISTEMAS INTEGRADOS DE GESTÃO', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Segurança do Trabalho']], 'series': [series['3º Ano']]},
            {'sigla': 'TEPI', 'desc': 'TECNOLOGIAS E PROCESSOS INDUSTRIAIS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Segurança do Trabalho']], 'series': [series['3º Ano']]},
            
            # Edificações
            {'sigla': 'DEA1', 'desc': 'DESENHO ARQUITETÔNICO I', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Edificações']], 'series': [series['1º Ano']]},
            {'sigla': 'DEAC', 'desc': 'DESENHO ASSISTIDO POR COMPUTADOR', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Edificações']], 'series': [series['1º Ano']]},
            {'sigla': 'INFO', 'desc': 'INFORMÁTICA', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Edificações']], 'series': [series['1º Ano']]},
            {'sigla': 'MATC', 'desc': 'MATERIAIS DE CONSTRUÇÃO', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Edificações']], 'series': [series['1º Ano']]},
            {'sigla': 'DEA2', 'desc': 'DESENHO ARQUITETÔNICO II', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Edificações']], 'series': [series['2º Ano']]},
            {'sigla': 'ESTC', 'desc': 'ESTABILIDADE DAS CONSTRUÇÕES', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Edificações']], 'series': [series['2º Ano']]},
            {'sigla': 'MSOL', 'desc': 'MECÂNICA DOS SOLOS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Edificações']], 'series': [series['2º Ano']]},
            {'sigla': 'SCON', 'desc': 'SISTEMAS CONSTRUTIVOS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Edificações']], 'series': [series['2º Ano']]},
            {'sigla': 'TOPO', 'desc': 'TOPOGRAFIA', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Edificações']], 'series': [series['2º Ano']]},
            {'sigla': 'EEST', 'desc': 'ELEMENTOS ESTRUTURAIS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Edificações']], 'series': [series['3º Ano']]},
            {'sigla': 'IHID', 'desc': 'INSTALAÇÕES HIDROSSANITÁRIAS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Edificações']], 'series': [series['3º Ano']]},
            {'sigla': 'POBR', 'desc': 'PLANEJAMENTO DE OBRAS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Edificações']], 'series': [series['3º Ano']]},
            {'sigla': 'PARQ', 'desc': 'PROJETO ARQUITETÔNICO', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Edificações']], 'series': [series['3º Ano']]},
            {'sigla': 'PIEP', 'desc': 'PROJETO DE INSTALAÇÕES ELÉTRICAS PREDIAIS', 'area': areas['Técnica'], 'cursos': [cursos['Técnico em Edificações']], 'series': [series['3º Ano']]},

            # Disciplina comum
            {'sigla': 'SETR', 'desc': 'SEGURANÇA DO TRABALHO', 'area': areas['Técnica'], 'cursos': cursos_tecnicos, 'series': [series['1º Ano'], series['2º Ano']]}
        ]

        self.stdout.write('Criando Disciplinas e associando ao currículo...')
        disciplinas_criadas = {}
        dcs_a_criar = []
        
        # 1. Cria todas as disciplinas primeiro, garantindo que não há duplicatas
        disciplina_id_counter = 1
        for d_info in curriculo_completo:
            if d_info['sigla'] not in disciplinas_criadas:
                disciplina_obj = Disciplina.objects.create(
                    id=disciplina_id_counter, 
                    sigla=d_info['sigla'], 
                    descricao=d_info['desc'], 
                    area_do_conhecimento=d_info['area']
                )
                disciplinas_criadas[d_info['sigla']] = disciplina_obj
                disciplina_id_counter += 1

        # 2. Cria as associações na tabela DisciplinaCursoSerie
        for d_info in curriculo_completo:
            disciplina_obj = disciplinas_criadas[d_info['sigla']]
            for curso_obj in d_info['cursos']:
                for serie_obj in d_info['series']:
                    dcs_a_criar.append(
                        DisciplinaCursoSerie(disciplina=disciplina_obj, curso=curso_obj, serie=serie_obj)
                    )

        DisciplinaCursoSerie.objects.bulk_create(dcs_a_criar)

        with connection.cursor() as cursor:
            self.stdout.write('Reativando a checagem de chaves estrangeiras...')
            cursor.execute("SET FOREIGN_KEY_CHECKS=1;")

        self.stdout.write(self.style.SUCCESS(f'Base de dados curricular populada com {len(disciplinas_criadas)} disciplinas e {len(dcs_a_criar)} vínculos curriculares.'))


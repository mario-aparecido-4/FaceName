from django.db import models

# =================================================================
# Função para definir o caminho de upload da foto
# =================================================================
def foto_aluno_path(instance, filename):
    """
    Cria um caminho de arquivo dinâmico para a foto do aluno.
    Exemplo de resultado: 'fotos_alunos/2023/2023001.jpg'
    """
    # Extrai o ano da matrícula (ex: '2023' de '2023001')
    ano_matricula = instance.matricula[:4]
    # Extrai a extensão do arquivo original
    ext = filename.split('.')[-1]
    # Monta o novo nome do arquivo para ser único, usando a matrícula
    novo_nome = f'{instance.matricula}.{ext}'
    # Retorna o caminho completo
    return f'fotos_alunos/{ano_matricula}/{novo_nome}'


# =================================================================
# Modelos do Banco de Dados
# =================================================================

class Aluno(models.Model):
    matricula = models.CharField(primary_key=True, max_length=20)
    nome = models.CharField(max_length=45)
    # ALTERADO: De BinaryField para ImageField, que armazena o caminho do arquivo
    foto = models.ImageField(upload_to=foto_aluno_path, blank=True, null=True)

    def __str__(self):
        return f"{self.nome} ({self.matricula})"

    class Meta:
        managed = False
        db_table = 'aluno'


class AreaDoConhecimento(models.Model):
    id = models.IntegerField(primary_key=True)
    descricao = models.CharField(unique=True, max_length=45)
    def __str__(self): return self.descricao
    class Meta:
        managed = False
        db_table = 'area_do_conhecimento'
        verbose_name = 'Área do Conhecimento'
        verbose_name_plural = 'Áreas do Conhecimento'


class Curso(models.Model):
    id = models.IntegerField(primary_key=True)
    descricao = models.CharField(unique=True, max_length=45)
    def __str__(self): return self.descricao
    class Meta:
        managed = False
        db_table = 'curso'


class Disciplina(models.Model):
    id = models.IntegerField(primary_key=True)
    sigla = models.CharField(unique=True, max_length=15)
    descricao = models.CharField(unique=True, max_length=60)
    horas = models.IntegerField(blank=True, null=True)
    area_do_conhecimento = models.ForeignKey(AreaDoConhecimento, models.DO_NOTHING)

    def __str__(self): return f"{self.descricao} ({self.sigla})"
    class Meta:
        managed = False
        db_table = 'disciplina'


class Serie(models.Model):
    id = models.IntegerField(primary_key=True)
    descricao = models.CharField(unique=True, max_length=45)
    def __str__(self): return self.descricao
    class Meta:
        managed = False
        db_table = 'serie'


class Turno(models.Model):
    id = models.IntegerField(primary_key=True)
    descricao = models.CharField(unique=True, max_length=45)
    def __str__(self): return self.descricao
    class Meta:
        managed = False
        db_table = 'turno'


class Turma(models.Model):
    id = models.CharField(primary_key=True, max_length=3)
    ano = models.IntegerField()
    descricao = models.CharField(max_length=45)
    curso = models.ForeignKey(Curso, models.DO_NOTHING)
    serie = models.ForeignKey(Serie, models.DO_NOTHING)
    turno = models.ForeignKey(Turno, models.DO_NOTHING)
    turma_id = models.CharField(blank=True, null=True, max_length=3)
    turma_ano = models.IntegerField(blank=True, null=True)
    def __str__(self): return f"{self.descricao} - {self.ano}"
    class Meta:
        managed = False
        db_table = 'turma'
        unique_together = (('id', 'ano'),)


class AlunoTurma(models.Model):
    aluno_matricula = models.OneToOneField(Aluno, models.DO_NOTHING, db_column='aluno_matricula', primary_key=True)
    turma_id = models.CharField(max_length=3)
    turma_ano = models.IntegerField()
    def __str__(self): return f"Aluno {self.aluno_matricula} na Turma {self.turma_id}/{self.turma_ano}"
    class Meta:
        managed = False
        db_table = 'aluno_turma'
        unique_together = (('aluno_matricula', 'turma_id', 'turma_ano'),)


class Boletim(models.Model):
    aluno_matricula = models.OneToOneField('Aluno', models.DO_NOTHING, db_column='aluno_matricula', primary_key=True)
    disciplina = models.ForeignKey('Disciplina', models.DO_NOTHING)
    turma_id = models.CharField(max_length=3)
    turma_ano = models.IntegerField()
    bimestre1 = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    bimestre2 = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    recusem1 = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    bimestre3 = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    bimestre4 = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    recusem2 = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    recfinal = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    final = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    faltas = models.IntegerField(blank=True, null=True)
    faltaspercent = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'boletim'
        unique_together = (('aluno_matricula', 'disciplina', 'turma_id', 'turma_ano'),)


class DisciplinaCursoSerie(models.Model):
    disciplina = models.OneToOneField(Disciplina, models.DO_NOTHING, primary_key=True)
    curso = models.ForeignKey(Curso, models.DO_NOTHING)
    serie = models.ForeignKey(Serie, models.DO_NOTHING)
    class Meta:
        managed = False
        db_table = 'disciplina_curso_serie'
        unique_together = (('disciplina', 'curso', 'serie'),)

# Modelo Proxy para gerenciar fotos separadamente
class AlunoFoto(Aluno):
    class Meta:
        proxy = True
        verbose_name = 'Foto de Aluno'
        verbose_name_plural = 'Fotos de Alunos'
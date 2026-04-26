from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django import forms
from django.http import HttpResponseRedirect
from django.db.models import Value, CharField
from django.db.models.functions import Concat
from .models import (
    Aluno, AreaDoConhecimento, Boletim, Curso, Disciplina,
    DisciplinaCursoSerie, Serie, Turma, AlunoTurma, Turno
)

# =================================================================
# Formulário customizado para permitir o upload da foto no AlunoAdmin
# =================================================================

class AlunoAdminForm(forms.ModelForm):
    """Adiciona um campo de upload de imagem ao formulário do Aluno."""
    foto_upload = forms.ImageField(label='Enviar/Alterar Foto', required=False)

    class Meta:
        model = Aluno
        fields = '__all__'

# =================================================================
# Configurações principais do Admin
# =================================================================

@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    """Gerencia Alunos, permitindo edição de nome e foto, e exibe boletins."""
    form = AlunoAdminForm
    list_display = ('matricula', 'nome', 'edit_link')
    search_fields = ('matricula', 'nome')
    list_display_links = None

    fieldsets = (
        ('Dados Pessoais', {'fields': ('matricula', 'nome')}),
        ('Foto', {'fields': ('image_tag', 'foto_upload')}),
        ('Boletins (Consulta)', {'fields': ('display_boletins',)}),
    )
    readonly_fields = ('image_tag', 'display_boletins')

    class Media:
        css = {'all': ('admin/css/custom_admin.css',)}
    
    def image_tag(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="max-height: 150px; max-width: 150px; border-radius: 8px;" />', obj.foto.url)
        return "Nenhuma foto enviada."
    image_tag.short_description = 'Pré-visualização'

    def edit_link(self, obj):
        # CORRIGIDO: dashboard_app -> dashboard
        url = reverse('admin:dashboard_aluno_change', args=[obj.pk])
        return format_html('<a href="{}">Editar</a>', url)
    edit_link.short_description = "Ações"

    def save_model(self, request, obj, form, change):
        """Processa a imagem enviada antes de salvar."""
        if 'foto_upload' in form.cleaned_data and form.cleaned_data['foto_upload']:
            obj.foto = form.cleaned_data['foto_upload']
        super().save_model(request, obj, form, change)

    def display_boletins(self, obj):
        """
        Renderiza uma tabela HTML pura com os boletins do aluno,
        evitando o uso de formsets que causam o erro ao salvar.
        """
        if not obj.pk:
            return "Salve o aluno para ver os boletins."

        boletins = Boletim.objects.filter(aluno_matricula=obj).order_by('-turma_ano', 'disciplina__descricao')
        if not boletins.exists():
            return "Nenhum boletim encontrado."

        html = ""
        current_year = None
        for b in boletins:
            if b.turma_ano != current_year:
                if current_year is not None:
                    html += '</tbody></table>'
                current_year = b.turma_ano
                html += f'<h3>Boletins de {current_year}</h3>'
                html += '<table style="width: 100%; border-collapse: collapse;">'
                html += '<thead style="background-color: #f2f2f2;"><tr>'
                headers = ['Disciplina', 'Turma', 'B1', 'B2', 'R1', 'B3', 'B4', 'R2', 'RF', 'Final', 'Faltas', '%', 'Status', 'Ações']
                for header in headers:
                    html += f'<th style="padding: 8px; border: 1px solid #ddd; text-align: left;">{header}</th>'
                html += '</tr></thead><tbody>'

            composite_pk = f"{b.aluno_matricula_id}-{b.disciplina_id}-{b.turma_id}-{b.turma_ano}"
            # CORRIGIDO: dashboard_app -> dashboard
            edit_url = reverse('admin:dashboard_boletim_change', args=[composite_pk])
            
            html += '<tr>'
            fields = [
                b.disciplina, b.turma_id, b.bimestre1, b.bimestre2, b.recusem1, b.bimestre3, b.bimestre4, b.recusem2, b.recfinal, b.final, b.faltas, b.faltaspercent, b.status
            ]
            for field in fields:
                html += f'<td style="padding: 8px; border: 1px solid #ddd;">{field if field is not None else ""}</td>'
            
            html += f'<td style="padding: 8px; border: 1px solid #ddd;"><a href="{edit_url}" target="_blank">Editar Notas</a></td>'
            html += '</tr>'

        html += '</tbody></table>'
        return format_html(html)
    display_boletins.short_description = ""


@admin.register(Boletim)
class BoletimAdmin(admin.ModelAdmin):
    """Gerencia a edição de notas, mas fica oculto do menu principal."""
    list_display = ('aluno_matricula', 'disciplina', 'turma_ano', 'turma_id', 'final', 'status')
    
    fieldsets = (
        ('Identificação (não editável)', {'fields': ('aluno_matricula', 'disciplina', 'turma_id', 'turma_ano')}),
        ('Notas, Faltas e Status (editável)', {'fields': (('bimestre1', 'bimestre2', 'recusem1'), ('bimestre3', 'bimestre4', 'recusem2'), ('recfinal', 'final'), ('faltas', 'faltaspercent', 'status'))}),
    )
    readonly_fields = ('aluno_matricula', 'disciplina', 'turma_id', 'turma_ano')

    def save_model(self, request, obj, form, change):
        cleaned_data = form.cleaned_data
        Boletim.objects.filter(
            aluno_matricula=obj.aluno_matricula,
            disciplina=obj.disciplina,
            turma_id=obj.turma_id,
            turma_ano=obj.turma_ano
        ).update(
            bimestre1=cleaned_data.get('bimestre1'),
            bimestre2=cleaned_data.get('bimestre2'),
            recusem1=cleaned_data.get('recusem1'),
            bimestre3=cleaned_data.get('bimestre3'),
            bimestre4=cleaned_data.get('bimestre4'),
            recusem2=cleaned_data.get('recusem2'),
            recfinal=cleaned_data.get('recfinal'),
            final=cleaned_data.get('final'),
            faltas=cleaned_data.get('faltas'),
            faltaspercent=cleaned_data.get('faltaspercent'),
            status=cleaned_data.get('status')
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(composite_pk=Concat('aluno_matricula_id', Value('-'), 'disciplina_id', Value('-'), 'turma_id', Value('-'), 'turma_ano', output_field=CharField()))
        return qs

    def get_object(self, request, object_id, from_field=None):
        try:
            matricula, disciplina_id, turma_id, turma_ano = object_id.split('-')
            return self.get_queryset(request).get(aluno_matricula_id=matricula, disciplina_id=disciplina_id, turma_id=turma_id, turma_ano=turma_ano)
        except (ValueError, self.model.DoesNotExist):
            return None

    # CORRIGIDO: dashboard_app -> dashboard
    def response_change(self, request, obj):
        aluno_url = reverse('admin:dashboard_aluno_change', args=[obj.aluno_matricula.pk])
        return HttpResponseRedirect(aluno_url)

    # CORRIGIDO: dashboard_app -> dashboard
    def response_add(self, request, obj, post_url_continue=None):
        aluno_url = reverse('admin:dashboard_aluno_change', args=[obj.aluno_matricula.pk])
        return HttpResponseRedirect(aluno_url)

    def get_model_perms(self, request):
        return {}


class TurmaAdminForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = '__all__'

    def validate_unique(self):
        exclude = self._get_validation_exclusions()
        if 'id' not in exclude:
            exclude.add('id')

        try:
            self.instance.validate_unique(exclude=exclude)
        except forms.ValidationError as e:
            self._update_errors(e)


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    """Gerencia Turmas."""
    form = TurmaAdminForm
    list_display = ('descricao_completa', 'curso', 'serie', 'turno', 'edit_link')
    search_fields = ('descricao', 'id')
    list_filter = ('ano', 'curso', 'serie', 'turno')
    list_display_links = None

    fieldsets = (
        ('Identificação da Turma', {'fields': ('id', 'ano', 'descricao')}),
        ('Estrutura', {'fields': ('curso', 'serie', 'turno')}),
        ('Progressão (Referência à turma do ano anterior)', {'fields': ('turma_id', 'turma_ano')}),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            Turma.objects.create(
                id=form.cleaned_data.get('id'),
                ano=form.cleaned_data.get('ano'),
                descricao=form.cleaned_data.get('descricao'),
                curso=form.cleaned_data.get('curso'),
                serie=form.cleaned_data.get('serie'),
                turno=form.cleaned_data.get('turno'),
                turma_id=form.cleaned_data.get('turma_id'),
                turma_ano=form.cleaned_data.get('turma_ano')
            )
        else:
            Turma.objects.filter(id=obj.id, ano=obj.ano).update(
                descricao=form.cleaned_data.get('descricao'),
                curso=form.cleaned_data.get('curso'),
                serie=form.cleaned_data.get('serie'),
                turno=form.cleaned_data.get('turno'),
                turma_id=form.cleaned_data.get('turma_id'),
                turma_ano=form.cleaned_data.get('turma_ano')
            )

    def descricao_completa(self, obj):
        return f"{obj.descricao} ({obj.ano})"
    descricao_completa.short_description = 'Turma (Ano)'
    
    def get_readonly_fields(self, request, obj=None):
        if obj: return ['id', 'ano']
        return []
        
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(composite_pk=Concat('id', Value('-'), 'ano', output_field=CharField()))
        return qs

    def get_object(self, request, object_id, from_field=None):
        try:
            id, ano = object_id.split('-')
            return self.get_queryset(request).get(id=id, ano=ano)
        except (ValueError, self.model.DoesNotExist):
            return None

    def edit_link(self, obj):
        # CORRIGIDO: dashboard_app -> dashboard
        url = reverse('admin:dashboard_turma_change', args=[obj.composite_pk])
        return format_html('<a href="{}">Editar</a>', url)
    edit_link.short_description = "Ações"


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('id', 'descricao', 'edit_link')
    search_fields = ('descricao',)
    list_display_links = None

    def edit_link(self, obj):
        # CORRIGIDO: dashboard_app -> dashboard
        url = reverse('admin:dashboard_curso_change', args=[obj.pk])
        return format_html('<a href="{}">Editar</a>', url)
    edit_link.short_description = "Ações"

@admin.register(Serie)
class SerieAdmin(admin.ModelAdmin):
    list_display = ('id', 'descricao', 'edit_link')
    search_fields = ('descricao',)
    list_display_links = None

    def edit_link(self, obj):
        # CORRIGIDO: dashboard_app -> dashboard
        url = reverse('admin:dashboard_serie_change', args=[obj.pk])
        return format_html('<a href="{}">Editar</a>', url)
    edit_link.short_description = "Ações"

@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ('id', 'sigla', 'descricao', 'area_do_conhecimento', 'edit_link')
    search_fields = ('sigla', 'descricao')
    list_filter = ('area_do_conhecimento',)
    list_select_related = ('area_do_conhecimento',)
    list_display_links = None

    def edit_link(self, obj):
        # CORRIGIDO: dashboard_app -> dashboard
        url = reverse('admin:dashboard_disciplina_change', args=[obj.pk])
        return format_html('<a href="{}">Editar</a>', url)
    edit_link.short_description = "Ações"

@admin.register(AlunoTurma)
class AlunoTurmaAdmin(admin.ModelAdmin):
    """Gerencia a associação de Alunos com Turmas."""
    list_display = ('aluno_matricula', 'turma_id', 'turma_ano', 'edit_link')
    list_filter = ('turma_ano', 'turma_id')
    search_fields = ('aluno_matricula__nome', 'aluno_matricula__matricula')
    list_display_links = None
    
    fieldsets = (('Associação', {'fields': ('aluno_matricula', 'turma_id', 'turma_ano')}),)

    def save_model(self, request, obj, form, change):
        if change:
            new_aluno_matricula = form.cleaned_data.get('aluno_matricula')
            new_turma_id = form.cleaned_data.get('turma_id')
            new_turma_ano = form.cleaned_data.get('turma_ano')
            
            original_aluno_matricula_pk = form.initial.get('aluno_matricula')
            original_turma_id = form.initial.get('turma_id')
            original_turma_ano = form.initial.get('turma_ano')
            
            AlunoTurma.objects.filter(
                aluno_matricula_id=original_aluno_matricula_pk,
                turma_id=original_turma_id,
                turma_ano=original_turma_ano
            ).update(
                aluno_matricula=new_aluno_matricula,
                turma_id=new_turma_id,
                turma_ano=new_turma_ano
            )
        else:
            super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(composite_pk=Concat('aluno_matricula_id', Value('-'), 'turma_id', Value('-'), 'turma_ano', output_field=CharField()))
        return qs

    def get_object(self, request, object_id, from_field=None):
        try:
            matricula, turma_id, turma_ano = object_id.split('-')
            return self.get_queryset(request).get(aluno_matricula_id=matricula, turma_id=turma_id, turma_ano=turma_ano)
        except (ValueError, self.model.DoesNotExist):
            return None

    def edit_link(self, obj):
        # CORRIGIDO: dashboard_app -> dashboard
        url = reverse('admin:dashboard_alunoturma_change', args=[obj.composite_pk])
        return format_html('<a href="{}">Editar</a>', url)
    edit_link.short_description = "Ações"

@admin.register(DisciplinaCursoSerie)
class DisciplinaCursoSerieAdmin(admin.ModelAdmin):
    """Gerencia a matriz curricular."""
    list_display = ('disciplina', 'curso', 'serie', 'edit_link')
    list_filter = ('curso', 'serie')
    search_fields = ('disciplina__descricao', 'disciplina__sigla')
    list_display_links = None

    fieldsets = (('Matriz Curricular', {'fields': ('disciplina', 'curso', 'serie')}),)
    
    def save_model(self, request, obj, form, change):
        if change:
            new_disciplina = form.cleaned_data.get('disciplina')
            new_curso = form.cleaned_data.get('curso')
            new_serie = form.cleaned_data.get('serie')
            
            original_disciplina_pk = form.initial.get('disciplina')
            original_curso_pk = form.initial.get('curso')
            original_serie_pk = form.initial.get('serie')
            
            DisciplinaCursoSerie.objects.filter(
                disciplina_id=original_disciplina_pk,
                curso_id=original_curso_pk,
                serie_id=original_serie_pk
            ).update(
                disciplina=new_disciplina,
                curso=new_curso,
                serie=new_serie
            )
        else:
            super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(composite_pk=Concat('disciplina_id', Value('-'), 'curso_id', Value('-'), 'serie_id', output_field=CharField()))
        return qs

    def get_object(self, request, object_id, from_field=None):
        try:
            disciplina_id, curso_id, serie_id = object_id.split('-')
            return self.get_queryset(request).get(disciplina_id=disciplina_id, curso_id=curso_id, serie_id=serie_id)
        except (ValueError, self.model.DoesNotExist):
            return None

    def edit_link(self, obj):
        # CORRIGIDO: dashboard_app -> dashboard
        url = reverse('admin:dashboard_disciplinacursoserie_change', args=[obj.composite_pk])
        return format_html('<a href="{}">Editar</a>', url)
    edit_link.short_description = "Ações"

@admin.register(AreaDoConhecimento)
class AreaDoConhecimentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'descricao', 'edit_link')
    search_fields = ('descricao',)
    list_display_links = None

    def edit_link(self, obj):
        # CORRIGIDO: dashboard_app -> dashboard
        url = reverse('admin:dashboard_areadoconhecimento_change', args=[obj.pk])
        return format_html('<a href="{}">Editar</a>', url)
    edit_link.short_description = "Ações"

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('id', 'descricao', 'edit_link')
    search_fields = ('descricao',)
    list_display_links = None

    def edit_link(self, obj):
        # CORRIGIDO: dashboard_app -> dashboard
        url = reverse('admin:dashboard_turno_change', args=[obj.pk])
        return format_html('<a href="{}">Editar</a>', url)
    edit_link.short_description = "Ações"
from django.contrib import admin

from .models import Project, ProjectLink, ProjectDate, ProjectBulletPoint

class ProjectBulletPointInlineAdmin(admin.TabularInline):
    model = ProjectBulletPoint
    extra = 1

    def formfield_for_dbfield(self, db_field, **kwargs):
        # More usable height in admin form fields for captions
        field = super(ProjectBulletPointInlineAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'description':
            field.widget.attrs['style'] = 'height: 5em;'
        return field

class ProjectDateInlineAdmin(admin.TabularInline):
    model = ProjectDate
    extra = 1

class ProjectLinkInlineAdmin(admin.TabularInline):
    model = ProjectLink
    extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    readonly_fields=('created','updated',)
    list_display=('name','created','updated',)
    inlines = [
        ProjectBulletPointInlineAdmin,
        ProjectDateInlineAdmin,
        ProjectLinkInlineAdmin,
    ]
    
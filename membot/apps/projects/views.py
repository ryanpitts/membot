from django.views.generic import TemplateView

from .models import Project

class ProjectListView(TemplateView):
    template_name = 'projects/project_list.html'

    def get_context_data(self, *args, **kwargs):
        page_context = {
            'projects': Project.objects.filter(is_active=True)
        }

        return page_context

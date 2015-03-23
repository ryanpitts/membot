from restless.dj import DjangoResource
from restless.preparers import FieldsPreparer

from .models import Project, ProjectDate


class ProjectDateResource(DjangoResource):
    preparer = FieldsPreparer(fields={
        'id': 'id',
        'name': 'name',
        'itemdate': 'itemdate',
        'itemtime': 'itemtime',
    })

    # GET /api/project-dates/
    # add ?project=<project_id> to filter for specific project
    def list(self):
        project = self.request.GET.get('project', None)
        if project:
            return ProjectDate.objects.filter(project=project)
        return ProjectDate.objects.all()
    
    # GET /api/project-dates/<pk>/
    def detail(self, pk):
        return ProjectDate.objects.get(pk=pk)


class ProjectResource(DjangoResource):
    projectdate = ProjectDateResource()
    
    preparer = FieldsPreparer(fields={
        'id': 'id',
        'created': 'created',
        'updated': 'updated',
        'name': 'name',
        'description': 'description',
        'is_active': 'is_active',
    })

    # GET /api/projects/
    def list(self):
        show_active_projects = 'hidden' not in self.request.GET
        return Project.objects.filter(is_active=show_active_projects)

    # GET /api/projects/<pk>/
    def detail(self, pk):
        return Project.objects.get(id=pk)

    def prepare(self, data):
        prepared = super(ProjectResource, self).prepare(data)
        prepared['next_itemdate'] = self.projectdate.prepare(data.next_itemdate())
        return prepared
        
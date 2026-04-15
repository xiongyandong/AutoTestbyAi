from django.shortcuts import render
from ..models import Project, Module, Config


def dashboard(request):
    project_count = Project.objects.count()
    module_count = Module.objects.count()
    config_count = Config.objects.count()
    recent_projects = Project.objects.order_by('-updated_at')[:5]

    return render(request, 'dashboard.html', {
        'project_count': project_count,
        'module_count': module_count,
        'config_count': config_count,
        'recent_projects': recent_projects,
        'nav_dashboard': 'active',
    })

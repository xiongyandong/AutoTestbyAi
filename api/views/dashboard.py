from django.shortcuts import render
from ..models import Project, Module, Config, TestCase, DDTSource


def dashboard(request):
    project_count = Project.objects.count()
    module_count = Module.objects.count()
    config_count = Config.objects.count()
    testcase_count = TestCase.objects.count()
    ddt_count = DDTSource.objects.count()
    recent_projects = Project.objects.order_by('-updated_at')[:5]
    recent_testcases = TestCase.objects.select_related('module', 'module__project').order_by('-updated_at')[:5]

    return render(request, 'dashboard.html', {
        'project_count': project_count,
        'module_count': module_count,
        'config_count': config_count,
        'testcase_count': testcase_count,
        'ddt_count': ddt_count,
        'recent_projects': recent_projects,
        'recent_testcases': recent_testcases,
        'nav_dashboard': 'active',
    })

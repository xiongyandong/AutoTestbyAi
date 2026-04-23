from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import Project, ProjectConfig, ScriptAsset


def project_list(request):
    """项目列表"""
    search = request.GET.get('search', '')
    projects = Project.objects.all()
    if search:
        projects = projects.filter(name__icontains=search)
    projects = projects.prefetch_related('modules')
    paginator = Paginator(projects, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'project/list.html', {
        'page_obj': page_obj,
        'search': search,
        'nav_project': 'active',
    })


def project_create(request):
    """创建项目"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        created_by = request.POST.get('created_by', '').strip()

        if not name:
            messages.error(request, '项目名称不能为空')
            return render(request, 'project/form.html', {
                'nav_project': 'active',
                'form_data': request.POST,
            })

        if Project.objects.filter(name=name).exists():
            messages.error(request, f'项目 "{name}" 已存在')
            return render(request, 'project/form.html', {
                'nav_project': 'active',
                'form_data': request.POST,
            })

        project = Project.objects.create(name=name, description=description, created_by=created_by)
        ScriptAsset.objects.get_or_create(
            scope_type=ScriptAsset.SCOPE_PROJECT,
            project=project,
            defaults={
                'name': f'{project.name}脚本配置',
                'language': 'python',
                'content': '',
                'function_index': [],
            },
        )
        messages.success(request, f'项目 "{name}" 创建成功')
        return redirect('project_list')

    return render(request, 'project/form.html', {'nav_project': 'active'})


def project_update(request, pk):
    """编辑项目"""
    project = get_object_or_404(Project, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        created_by = request.POST.get('created_by', '').strip()

        if not name:
            messages.error(request, '项目名称不能为空')
            return render(request, 'project/form.html', {
                'project': project,
                'nav_project': 'active',
                'form_data': request.POST,
            })

        if Project.objects.filter(name=name).exclude(pk=pk).exists():
            messages.error(request, f'项目 "{name}" 已存在')
            return render(request, 'project/form.html', {
                'project': project,
                'nav_project': 'active',
                'form_data': request.POST,
            })

        project.name = name
        project.description = description
        project.created_by = created_by
        project.save()
        messages.success(request, f'项目 "{name}" 更新成功')
        return redirect('project_list')

    return render(request, 'project/form.html', {
        'project': project,
        'nav_project': 'active',
    })


def project_delete(request, pk):
    """删除项目"""
    project = get_object_or_404(Project, pk=pk)

    if request.method == 'POST':
        name = project.name
        project.delete()
        messages.success(request, f'项目 "{name}" 已删除')
        return redirect('project_list')

    return render(request, 'project/list.html', {'nav_project': 'active'})


def project_config_list(request, pk):
    """项目配置管理列表"""
    project = get_object_or_404(Project, pk=pk)
    configs = ProjectConfig.objects.filter(project=project)
    return render(request, 'project/config.html', {
        'project': project,
        'configs': configs,
        'nav_project': 'active',
    })


def project_config_create(request, pk):
    """新增项目配置变量"""
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        key = request.POST.get('key', '').strip()
        value = request.POST.get('value', '').strip()
        description = request.POST.get('description', '').strip()
        if not key:
            messages.error(request, '变量名不能为空')
            return redirect('project_config_list', pk=pk)
        if ProjectConfig.objects.filter(project=project, key=key).exists():
            messages.error(request, f'变量名 "{key}" 已存在')
            return redirect('project_config_list', pk=pk)
        ProjectConfig.objects.create(
            project=project, key=key, value=value, description=description
        )
        messages.success(request, f'变量 "{key}" 创建成功')
    return redirect('project_config_list', pk=pk)


def project_config_update(request, pk, cid):
    """修改项目配置变量"""
    project = get_object_or_404(Project, pk=pk)
    config = get_object_or_404(ProjectConfig, pk=cid, project=project)
    if request.method == 'POST':
        key = request.POST.get('key', '').strip()
        value = request.POST.get('value', '').strip()
        description = request.POST.get('description', '').strip()
        if not key:
            messages.error(request, '变量名不能为空')
            return redirect('project_config_list', pk=pk)
        if ProjectConfig.objects.filter(project=project, key=key).exclude(pk=cid).exists():
            messages.error(request, f'变量名 "{key}" 已存在')
            return redirect('project_config_list', pk=pk)
        config.key = key
        config.value = value
        config.description = description
        config.save()
        messages.success(request, f'变量 "{key}" 更新成功')
    return redirect('project_config_list', pk=pk)


def project_config_delete(request, pk, cid):
    """删除项目配置变量"""
    project = get_object_or_404(Project, pk=pk)
    config = get_object_or_404(ProjectConfig, pk=cid, project=project)
    if request.method == 'POST':
        key = config.key
        config.delete()
        messages.success(request, f'变量 "{key}" 已删除')
    return redirect('project_config_list', pk=pk)

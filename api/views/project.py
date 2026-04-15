from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models import Project


def project_list(request):
    """项目列表"""
    search = request.GET.get('search', '')
    projects = Project.objects.all()
    if search:
        projects = projects.filter(name__icontains=search)
    projects = projects.prefetch_related('modules')
    return render(request, 'project/list.html', {
        'projects': projects,
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

        Project.objects.create(name=name, description=description, created_by=created_by)
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

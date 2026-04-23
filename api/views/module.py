from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import Module, Project


def module_list(request):
    project_id = request.GET.get('project', '')
    search = request.GET.get('search', '')
    modules = Module.objects.select_related('project').all()
    if project_id:
        modules = modules.filter(project_id=project_id)
    if search:
        modules = modules.filter(name__icontains=search)
    projects = Project.objects.all()
    paginator = Paginator(modules, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'module/list.html', {
        'page_obj': page_obj,
        'projects': projects,
        'current_project': project_id,
        'search': search,
        'nav_module': 'active',
    })


def module_create(request):
    projects = Project.objects.all()
    if request.method == 'POST':
        project_id = request.POST.get('project', '')
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if not project_id or not name:
            messages.error(request, '项目和模块名称不能为空')
            return render(request, 'module/form.html', {
                'projects': projects,
                'nav_module': 'active',
                'form_data': request.POST,
            })
        project = get_object_or_404(Project, pk=project_id)
        if Module.objects.filter(project=project, name=name).exists():
            messages.error(request, f'模块 "{name}" 在该项目下已存在')
            return render(request, 'module/form.html', {
                'projects': projects,
                'nav_module': 'active',
                'form_data': request.POST,
            })
        Module.objects.create(project=project, name=name, description=description)
        messages.success(request, f'模块 "{name}" 创建成功')
        return redirect('module_list')
    return render(request, 'module/form.html', {
        'projects': projects,
        'nav_module': 'active',
    })


def module_update(request, pk):
    module = get_object_or_404(Module, pk=pk)
    projects = Project.objects.all()
    if request.method == 'POST':
        project_id = request.POST.get('project', '')
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if not project_id or not name:
            messages.error(request, '项目和模块名称不能为空')
            return render(request, 'module/form.html', {
                'module': module,
                'projects': projects,
                'nav_module': 'active',
                'form_data': request.POST,
            })
        project = get_object_or_404(Project, pk=project_id)
        if Module.objects.filter(project=project, name=name).exclude(pk=pk).exists():
            messages.error(request, f'模块 "{name}" 在该项目下已存在')
            return render(request, 'module/form.html', {
                'module': module,
                'projects': projects,
                'nav_module': 'active',
                'form_data': request.POST,
            })
        module.project = project
        module.name = name
        module.description = description
        module.save()
        messages.success(request, f'模块 "{name}" 更新成功')
        return redirect('module_list')
    return render(request, 'module/form.html', {
        'module': module,
        'projects': projects,
        'nav_module': 'active',
    })


def module_delete(request, pk):
    module = get_object_or_404(Module, pk=pk)
    if request.method == 'POST':
        name = module.name
        module.delete()
        messages.success(request, f'模块 "{name}" 已删除')
        return redirect('module_list')
    return redirect('module_list')

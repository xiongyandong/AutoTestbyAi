import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from ..models import Config, Module, Project
from ..script_engine import normalize_hook_list


def _hook_json_for_form(raw_value):
    return json.dumps(normalize_hook_list(raw_value), ensure_ascii=False)


def config_list(request):
    module_id = request.GET.get('module', '')
    project_id = request.GET.get('project', '')
    search = request.GET.get('search', '')
    configs = Config.objects.select_related('module', 'module__project').all()
    if module_id:
        configs = configs.filter(module_id=module_id)
    if project_id:
        configs = configs.filter(module__project_id=project_id)
    if search:
        configs = configs.filter(name__icontains=search)
    projects = Project.objects.all()
    modules = Module.objects.all()
    if project_id:
        modules = modules.filter(project_id=project_id)
    paginator = Paginator(configs, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'config/list.html', {
        'page_obj': page_obj,
        'projects': projects,
        'modules': modules,
        'current_project': project_id,
        'current_module': module_id,
        'search': search,
        'nav_config': 'active',
    })


def config_create(request):
    projects = Project.objects.all()
    modules = Module.objects.select_related('project').all()
    if request.method == 'POST':
        module_id = request.POST.get('module', '')
        name = request.POST.get('name', '').strip()
        base_url = request.POST.get('base_url', '').strip()
        env_type = request.POST.get('env_type', 'DEV')
        created_by = request.POST.get('created_by', '').strip()
        variables = request.POST.get('variables', '{}')
        parameters = request.POST.get('parameters', '{}')
        request_hooks = request.POST.get('request_hooks', '[]')
        response_hooks = request.POST.get('response_hooks', '[]')
        if not module_id or not name:
            messages.error(request, '模块和环境名称不能为空')
            return render(request, 'config/form.html', {
                'projects': projects, 'modules': modules,
                'nav_config': 'active', 'form_data': request.POST,
            })
        module = get_object_or_404(Module, pk=module_id)
        try:
            variables_json = json.loads(variables) if variables else {}
            parameters_json = json.loads(parameters) if parameters else {}
            request_hooks_json = normalize_hook_list(json.loads(request_hooks) if request_hooks else [])
            response_hooks_json = normalize_hook_list(json.loads(response_hooks) if response_hooks else [])
        except json.JSONDecodeError as e:
            messages.error(request, f'JSON 格式错误: {e}')
            return render(request, 'config/form.html', {
                'projects': projects, 'modules': modules,
                'nav_config': 'active', 'form_data': request.POST,
            })
        Config.objects.create(
            module=module, name=name, base_url=base_url,
            env_type=env_type, created_by=created_by,
            variables=variables_json, parameters=parameters_json,
            request_hooks=request_hooks_json, response_hooks=response_hooks_json,
        )
        messages.success(request, f'环境 "{name}" 创建成功')
        return redirect('config_list')
    return render(request, 'config/form.html', {
        'projects': projects, 'modules': modules, 'nav_config': 'active',
        'config_request_hooks_json': '[]',
        'config_response_hooks_json': '[]',
    })


def config_update(request, pk):
    config = get_object_or_404(Config, pk=pk)
    projects = Project.objects.all()
    modules = Module.objects.select_related('project').all()
    if request.method == 'POST':
        module_id = request.POST.get('module', '')
        name = request.POST.get('name', '').strip()
        base_url = request.POST.get('base_url', '').strip()
        env_type = request.POST.get('env_type', 'DEV')
        created_by = request.POST.get('created_by', '').strip()
        variables = request.POST.get('variables', '{}')
        parameters = request.POST.get('parameters', '{}')
        request_hooks = request.POST.get('request_hooks', '[]')
        response_hooks = request.POST.get('response_hooks', '[]')
        if not module_id or not name:
            messages.error(request, '模块和环境名称不能为空')
            return render(request, 'config/form.html', {
                'config': config, 'projects': projects, 'modules': modules,
                'nav_config': 'active', 'form_data': request.POST,
            })
        module = get_object_or_404(Module, pk=module_id)
        try:
            variables_json = json.loads(variables) if variables else {}
            parameters_json = json.loads(parameters) if parameters else {}
            request_hooks_json = normalize_hook_list(json.loads(request_hooks) if request_hooks else [])
            response_hooks_json = normalize_hook_list(json.loads(response_hooks) if response_hooks else [])
        except json.JSONDecodeError as e:
            messages.error(request, f'JSON 格式错误: {e}')
            return render(request, 'config/form.html', {
                'config': config, 'projects': projects, 'modules': modules,
                'nav_config': 'active', 'form_data': request.POST,
            })
        config.module = module
        config.name = name
        config.base_url = base_url
        config.env_type = env_type
        config.created_by = created_by
        config.variables = variables_json
        config.parameters = parameters_json
        config.request_hooks = request_hooks_json
        config.response_hooks = response_hooks_json
        config.save()
        messages.success(request, f'环境 "{name}" 更新成功')
        return redirect('config_list')
    return render(request, 'config/form.html', {
        'config': config, 'projects': projects, 'modules': modules, 'nav_config': 'active',
        'config_request_hooks_json': _hook_json_for_form(config.request_hooks),
        'config_response_hooks_json': _hook_json_for_form(config.response_hooks),
    })


def config_delete(request, pk):
    config = get_object_or_404(Config, pk=pk)
    if request.method == 'POST':
        name = config.name
        config.delete()
        messages.success(request, f'环境 "{name}" 已删除')
        return redirect('config_list')
    return redirect('config_list')


def load_modules(request):
    project_id = request.GET.get('project_id', '')
    modules = Module.objects.filter(project_id=project_id).values('id', 'name') if project_id else []
    return JsonResponse(list(modules), safe=False)

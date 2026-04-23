from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Project, ScriptAsset
from ..script_engine import parse_function_signature, validate_python_script


def _ensure_assets():
    ScriptAsset.ensure_defaults()


def script_list(request):
    _ensure_assets()
    project_filter = request.GET.get('project', '')
    page_number = request.GET.get('page', 1)

    public_script = ScriptAsset.objects.filter(scope_type=ScriptAsset.SCOPE_PUBLIC).first()
    project_scripts = ScriptAsset.objects.select_related('project').filter(
        scope_type=ScriptAsset.SCOPE_PROJECT
    ).order_by('project__name')

    if project_filter == ScriptAsset.SCOPE_PUBLIC:
        queryset = ScriptAsset.objects.filter(pk=public_script.pk) if public_script else ScriptAsset.objects.none()
        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)
    elif project_filter:
        paginator = Paginator(project_scripts.filter(project_id=project_filter), 10)
        page_obj = paginator.get_page(page_number)
    else:
        paginator = Paginator(project_scripts, 9)
        page_obj = paginator.get_page(page_number)
        if page_obj.number == 1 and public_script:
            page_obj.object_list = [public_script, *list(page_obj.object_list)]

    return render(request, 'script/list.html', {
        'page_obj': page_obj,
        'projects': Project.objects.order_by('name'),
        'current_project': project_filter,
        'nav_script': 'active',
    })


def script_update(request, pk):
    _ensure_assets()
    script = get_object_or_404(ScriptAsset.objects.select_related('project'), pk=pk)

    if request.method == 'POST':
        content = request.POST.get('content', '')
        validation = validate_python_script(content)
        if not validation['ok']:
            messages.error(request, f'脚本语法错误：第 {validation["line"]} 行 {validation["message"]}')
            return render(request, 'script/form.html', {
                'script': script,
                'editor_content': content,
                'nav_script': 'active',
            })
        script.content = content
        script.function_index = validation['functions']
        script.save(update_fields=['content', 'function_index', 'updated_at'])
        messages.success(request, '脚本保存成功')
        return redirect('script_update', pk=script.pk)

    return render(request, 'script/form.html', {
        'script': script,
        'editor_content': script.content,
        'nav_script': 'active',
    })


def script_validate(request, pk):
    _ensure_assets()
    get_object_or_404(ScriptAsset, pk=pk)
    validation = validate_python_script(request.POST.get('content', ''))
    status = 200 if validation['ok'] else 400
    return JsonResponse(validation, status=status)


def hook_function_options(request):
    _ensure_assets()
    project_id = request.GET.get('project_id', '')
    project = Project.objects.filter(pk=project_id).first() if project_id else None
    payload = []

    public_script = ScriptAsset.objects.filter(scope_type=ScriptAsset.SCOPE_PUBLIC).first()
    if public_script:
        for signature in public_script.function_index:
            parsed = parse_function_signature(signature)
            if parsed:
                payload.append({
                    'name': parsed['name'],
                    'signature': parsed['signature'],
                    'args': parsed['args'],
                    'scope': ScriptAsset.SCOPE_PUBLIC,
                    'scope_label': '公共脚本',
                })

    if project is not None:
        project_script = ScriptAsset.objects.filter(
            scope_type=ScriptAsset.SCOPE_PROJECT,
            project=project,
        ).first()
        if project_script:
            for signature in project_script.function_index:
                parsed = parse_function_signature(signature)
                if parsed:
                    payload.append({
                        'name': parsed['name'],
                        'signature': parsed['signature'],
                        'args': parsed['args'],
                        'scope': ScriptAsset.SCOPE_PROJECT,
                        'scope_label': project.name,
                    })

    return JsonResponse(payload, safe=False)

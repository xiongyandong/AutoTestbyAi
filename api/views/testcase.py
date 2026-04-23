import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from ..models import TestCase, Module, Project, DDTSource


def _get_filter_context(request):
    """获取筛选用的项目和模块列表"""
    project_id = request.GET.get('project', '')
    module_id = request.GET.get('module', '')
    method = request.GET.get('method', '')
    search = request.GET.get('search', '')
    projects = Project.objects.all()
    modules = Module.objects.all()
    if project_id:
        modules = modules.filter(project_id=project_id)
    return {
        'projects': projects,
        'modules': modules,
        'current_project': project_id,
        'current_module': module_id,
        'current_method': method,
        'search': search,
    }


def testcase_list(request):
    """用例列表"""
    ctx = _get_filter_context(request)
    testcases = TestCase.objects.select_related('module', 'module__project').all()

    if ctx['current_project']:
        testcases = testcases.filter(module__project_id=ctx['current_project'])
    if ctx['current_module']:
        testcases = testcases.filter(module_id=ctx['current_module'])
    if ctx['current_method']:
        testcases = testcases.filter(method=ctx['current_method'])
    if ctx['search']:
        testcases = testcases.filter(name__icontains=ctx['search'])

    paginator = Paginator(testcases, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    ctx.update({
        'page_obj': page_obj,
        'nav_testcase': 'active',
    })
    return render(request, 'testcase/list.html', ctx)


def _validate_and_save(testcase, request, is_create=False):
    """验证表单数据并保存用例，返回 (success, form_data)"""
    module_id = request.POST.get('module', '')
    name = request.POST.get('name', '').strip()
    method = request.POST.get('method', 'GET')
    url = request.POST.get('url', '').strip()
    created_by = request.POST.get('created_by', '').strip()
    is_parameterized = request.POST.get('is_parameterized') == 'on'

    body_type = request.POST.get('body_type', 'json')

    # JSON fields
    headers = request.POST.get('headers', '{}')
    params = request.POST.get('params', '{}')
    if body_type == 'binary':
        uploaded = request.FILES.get('body_file')
        body = json.dumps({'__binary__': uploaded.name}) if uploaded else '{}'
    elif body_type == 'none':
        body = '{}'
    else:
        body = request.POST.get('body', '{}')
    extractors = request.POST.get('extractors', '{}')
    assertions = request.POST.get('assertions', '[]')
    setup_hooks = request.POST.get('setup_hooks', '[]')
    teardown_hooks = request.POST.get('teardown_hooks', '[]')

    ddt_source_id = request.POST.get('ddt_source', '')

    form_data = request.POST.copy()
    form_data['is_parameterized'] = is_parameterized
    form_data['body_type'] = body_type
    form_data['body_json_raw'] = request.POST.get('body', '{}')

    if not module_id or not name:
        messages.error(request, '模块和用例名称不能为空')
        return False, form_data

    if not url:
        messages.error(request, '请求URL不能为空')
        return False, form_data

    module = get_object_or_404(Module, pk=module_id)

    # Validate JSON fields
    json_fields = {
        'headers': (headers, {}),
        'params': (params, {}),
        'body': (body, {}),
        'extractors': (extractors, {}),
        'assertions': (assertions, []),
        'setup_hooks': (setup_hooks, []),
        'teardown_hooks': (teardown_hooks, []),
    }
    parsed = {}
    for field_name, (field_value, default) in json_fields.items():
        try:
            parsed[field_name] = json.loads(field_value) if field_value.strip() else default
        except json.JSONDecodeError as e:
            messages.error(request, f'{field_name} JSON 格式错误: {e}')
            return False, form_data

    testcase.module = module
    testcase.name = name
    testcase.method = method
    testcase.url = url
    testcase.body_type = body_type
    testcase.created_by = created_by
    testcase.is_parameterized = is_parameterized
    testcase.ddt_source_id = ddt_source_id if ddt_source_id else None
    testcase.headers = parsed['headers']
    testcase.params = parsed['params']
    testcase.body = parsed['body']
    testcase.extractors = parsed['extractors']
    testcase.assertions = parsed['assertions']
    testcase.setup_hooks = parsed['setup_hooks']
    testcase.teardown_hooks = parsed['teardown_hooks']
    testcase.save()
    return True, form_data


METHOD_CHOICES = TestCase.METHOD_CHOICES


def testcase_create(request):
    """创建用例"""
    projects = Project.objects.all()
    modules = Module.objects.select_related('project').all()
    ddt_sources = DDTSource.objects.all()
    ctx = {'projects': projects, 'modules': modules, 'method_choices': METHOD_CHOICES, 'ddt_sources': ddt_sources, 'nav_testcase': 'active'}

    if request.method == 'POST':
        tc = TestCase()
        success, form_data = _validate_and_save(tc, request, is_create=True)
        if success:
            messages.success(request, f'用例 "{tc.name}" 创建成功')
            return redirect('testcase_list')
        ctx['form_data'] = form_data
        return render(request, 'testcase/form.html', ctx)

    return render(request, 'testcase/form.html', ctx)


def testcase_update(request, pk):
    """编辑用例"""
    testcase = get_object_or_404(TestCase, pk=pk)
    projects = Project.objects.all()
    modules = Module.objects.select_related('project').all()
    ddt_sources = DDTSource.objects.all()
    ctx = {'testcase': testcase, 'projects': projects, 'modules': modules, 'method_choices': METHOD_CHOICES, 'ddt_sources': ddt_sources, 'nav_testcase': 'active'}

    if request.method == 'POST':
        success, form_data = _validate_and_save(testcase, request)
        if success:
            messages.success(request, f'用例 "{testcase.name}" 更新成功')
            return redirect('testcase_list')
        ctx['form_data'] = form_data
        return render(request, 'testcase/form.html', ctx)

    return render(request, 'testcase/form.html', ctx)


def testcase_delete(request, pk):
    """删除用例"""
    testcase = get_object_or_404(TestCase, pk=pk)
    if request.method == 'POST':
        name = testcase.name
        testcase.delete()
        messages.success(request, f'用例 "{name}" 已删除')
        return redirect('testcase_list')
    return redirect('testcase_list')

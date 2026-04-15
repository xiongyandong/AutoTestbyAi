import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from ..models import Scene, SceneCase, TestCase, Project


def scene_list(request):
    """场景列表"""
    project_id = request.GET.get('project', '')
    search = request.GET.get('search', '')
    scenes = Scene.objects.select_related('project').prefetch_related('scene_cases').all()
    if project_id:
        scenes = scenes.filter(project_id=project_id)
    if search:
        scenes = scenes.filter(name__icontains=search)
    projects = Project.objects.all()
    return render(request, 'scene/list.html', {
        'scenes': scenes,
        'projects': projects,
        'current_project': project_id,
        'search': search,
        'nav_scene': 'active',
    })


def scene_create(request):
    """创建场景"""
    projects = Project.objects.all()
    if request.method == 'POST':
        project_id = request.POST.get('project', '')
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        created_by = request.POST.get('created_by', '').strip()
        if not project_id or not name:
            messages.error(request, '项目和场景名称不能为空')
            return render(request, 'scene/form.html', {
                'projects': projects, 'nav_scene': 'active', 'form_data': request.POST,
            })
        project = get_object_or_404(Project, pk=project_id)
        Scene.objects.create(project=project, name=name, description=description, created_by=created_by)
        messages.success(request, f'场景 "{name}" 创建成功')
        return redirect('scene_list')
    return render(request, 'scene/form.html', {'projects': projects, 'nav_scene': 'active'})


def scene_update(request, pk):
    """编辑场景基本信息"""
    scene = get_object_or_404(Scene, pk=pk)
    projects = Project.objects.all()
    if request.method == 'POST':
        project_id = request.POST.get('project', '')
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        created_by = request.POST.get('created_by', '').strip()
        if not project_id or not name:
            messages.error(request, '项目和场景名称不能为空')
            return render(request, 'scene/form.html', {
                'scene': scene, 'projects': projects, 'nav_scene': 'active', 'form_data': request.POST,
            })
        project = get_object_or_404(Project, pk=project_id)
        scene.project = project
        scene.name = name
        scene.description = description
        scene.created_by = created_by
        scene.save()
        messages.success(request, f'场景 "{name}" 更新成功')
        return redirect('scene_list')
    return render(request, 'scene/form.html', {'scene': scene, 'projects': projects, 'nav_scene': 'active'})


def scene_delete(request, pk):
    """删除场景"""
    scene = get_object_or_404(Scene, pk=pk)
    if request.method == 'POST':
        name = scene.name
        scene.delete()
        messages.success(request, f'场景 "{name}" 已删除')
        return redirect('scene_list')
    return redirect('scene_list')


def scene_orchestrate(request, pk):
    """场景编排页 - 添加/移除用例、排序"""
    scene = get_object_or_404(Scene, pk=pk)
    scene_cases = scene.scene_cases.select_related('testcase', 'testcase__module', 'testcase__module__project').order_by('order_index')
    # 获取可添加的用例（排除已在场景中的）
    existing_ids = scene.scene_cases.values_list('testcase_id', flat=True)
    available_testcases = TestCase.objects.select_related('module', 'module__project').exclude(pk__in=existing_ids)
    projects = Project.objects.all()
    return render(request, 'scene/orchestrate.html', {
        'scene': scene,
        'scene_cases': scene_cases,
        'available_testcases': available_testcases,
        'projects': projects,
        'nav_scene': 'active',
    })


@require_POST
def scene_add_case(request, pk):
    """向场景添加用例"""
    scene = get_object_or_404(Scene, pk=pk)
    testcase_id = request.POST.get('testcase_id', '')
    if not testcase_id:
        return JsonResponse({'error': '未选择用例'}, status=400)
    testcase = get_object_or_404(TestCase, pk=testcase_id)
    # 获取当前最大 order_index
    max_order = scene.scene_cases.order_by('-order_index').values_list('order_index', flat=True).first() or 0
    SceneCase.objects.create(scene=scene, testcase=testcase, order_index=max_order + 1)
    return JsonResponse({'ok': True, 'testcase_name': testcase.name})


@require_POST
def scene_remove_case(request, pk, case_pk):
    """从场景移除用例"""
    scene_case = get_object_or_404(SceneCase, pk=case_pk, scene_id=pk)
    scene_case.delete()
    return JsonResponse({'ok': True})


@require_POST
def scene_reorder(request, pk):
    """重新排序场景中的用例"""
    scene = get_object_or_404(Scene, pk=pk)
    order_data = json.loads(request.POST.get('order', '[]'))
    for item in order_data:
        SceneCase.objects.filter(pk=item['id'], scene=scene).update(order_index=item['order'])
    return JsonResponse({'ok': True})


def scene_testcases_api(request):
    """AJAX: 按项目筛选获取可用用例列表"""
    project_id = request.GET.get('project_id', '')
    scene_id = request.GET.get('scene_id', '')
    testcases = TestCase.objects.select_related('module', 'module__project').all()
    if project_id:
        testcases = testcases.filter(module__project_id=project_id)
    if scene_id:
        existing_ids = SceneCase.objects.filter(scene_id=scene_id).values_list('testcase_id', flat=True)
        testcases = testcases.exclude(pk__in=existing_ids)
    data = list(testcases.values('id', 'name', 'method', 'module__name', 'module__project__name'))
    return JsonResponse(data, safe=False)

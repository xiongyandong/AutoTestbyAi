import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from ..models import Task, TaskResult, TestCase, Module, Project, Scene, Config
from ..pytest_runner import PytestRunner


def task_list(request):
    """任务列表"""
    status_filter = request.GET.get('status', '')
    tasks = Task.objects.select_related('project', 'module', 'testcase', 'scene').prefetch_related('results').all()
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    return render(request, 'task/list.html', {
        'tasks': tasks,
        'current_status': status_filter,
        'nav_task': 'active',
    })


def task_create(request):
    """创建任务"""
    projects = Project.objects.all()
    scenes = Scene.objects.select_related('project').all()

    if request.method == 'POST':
        task_name = request.POST.get('task_name', '').strip()
        scope = request.POST.get('scope', 'TESTCASE')
        execute_env = request.POST.get('execute_env', 'DEV')
        created_by = request.POST.get('created_by', '').strip()
        report_name = request.POST.get('report_name', '').strip()

        if not task_name:
            messages.error(request, '任务名称不能为空')
            return render(request, 'task/form.html', {
                'projects': projects, 'scenes': scenes,
                'nav_task': 'active', 'form_data': request.POST,
            })

        task = Task.objects.create(
            task_name=task_name,
            task_type='SYNC',
            status='PENDING',
            scope=scope,
            execute_env=execute_env,
            created_by=created_by,
            report_name=report_name or task_name,
        )

        # 关联范围
        if scope == 'TESTCASE':
            testcase_id = request.POST.get('testcase', '')
            if testcase_id:
                task.testcase_id = testcase_id
                tc = TestCase.objects.get(pk=testcase_id)
                task.project = tc.module.project
                task.module = tc.module
        elif scope == 'MODULE':
            module_id = request.POST.get('module', '')
            if module_id:
                task.module_id = module_id
                task.project_id = Module.objects.get(pk=module_id).project_id
        elif scope == 'PROJECT':
            project_id = request.POST.get('project', '')
            if project_id:
                task.project_id = project_id
        elif scope == 'SCENE':
            scene_id = request.POST.get('scene', '')
            if scene_id:
                task.scene_id = scene_id
                task.project = Scene.objects.get(pk=scene_id).project

        task.save()
        messages.success(request, f'任务 "{task_name}" 创建成功')
        return redirect('task_list')

    return render(request, 'task/form.html', {
        'projects': projects, 'scenes': scenes,
        'nav_task': 'active',
    })


def task_delete(request, pk):
    """删除任务"""
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        name = task.task_name
        task.delete()
        messages.success(request, f'任务 "{name}" 已删除')
        return redirect('task_list')
    return redirect('task_list')


def task_execute(request, pk):
    """执行任务"""
    task = get_object_or_404(Task, pk=pk)

    if task.status == 'RUNNING':
        messages.warning(request, '任务正在执行中')
        return redirect('task_list')

    # 收集要执行的用例
    testcases = []
    if task.scope == 'TESTCASE' and task.testcase:
        testcases = [task.testcase]
    elif task.scope == 'MODULE' and task.module:
        testcases = list(task.module.testcases.all())
    elif task.scope == 'PROJECT' and task.project:
        testcases = list(TestCase.objects.filter(module__project=task.project))
    elif task.scope == 'SCENE' and task.scene:
        testcases = [sc.testcase for sc in task.scene.scene_cases.select_related('testcase').order_by('order_index')]

    if not testcases:
        messages.error(request, '未找到可执行的用例')
        return redirect('task_list')

    # 加载环境配置
    env_config = None
    if task.project:
        config = Config.objects.filter(module__project=task.project, env_type=task.execute_env).first()
        if config:
            env_config = {
                'variables': config.variables or {},
                'parameters': config.parameters or {},
            }

    # 更新状态为执行中
    task.status = 'RUNNING'
    task.save(update_fields=['status', 'updated_at'])

    try:
        total, passed, failed, error, skipped, duration, report_path, log = PytestRunner.run_testcases(
            testcases, env_config
        )
        task.status = 'COMPLETED'
    except Exception as e:
        total, passed, failed, error, skipped, duration, report_path, log = 0, 0, 0, 0, 0, 0, '', str(e)
        task.status = 'FAILED'

    task.save(update_fields=['status', 'updated_at'])

    # 保存结果
    TaskResult.objects.create(
        task=task,
        total_cases=total,
        passed=passed,
        failed=failed,
        error=error,
        skipped=skipped,
        duration=duration,
        report_path=report_path,
        log=log,
    )

    if task.status == 'COMPLETED':
        messages.success(request, f'任务执行完成: {passed}/{total} 通过')
    else:
        messages.error(request, f'任务执行失败: {str(e)[:100]}')

    return redirect('task_list')


def task_result(request, pk):
    """查看任务结果"""
    task = get_object_or_404(Task, pk=pk)
    result = task.results.first()
    return render(request, 'task/result.html', {
        'task': task,
        'result': result,
        'nav_task': 'active',
    })


def testcase_quick_run(request, pk):
    """用例快捷运行（从用例列表页触发）"""
    testcase = get_object_or_404(TestCase, pk=pk)
    execute_env = request.GET.get('env', 'DEV')

    task = Task.objects.create(
        task_name=f'快捷运行: {testcase.name}',
        task_type='SYNC',
        status='RUNNING',
        scope='TESTCASE',
        testcase=testcase,
        project=testcase.module.project,
        module=testcase.module,
        execute_env=execute_env,
        created_by=testcase.created_by,
        report_name=testcase.name,
    )

    env_config = None
    config = Config.objects.filter(module__project=testcase.module.project, env_type=execute_env).first()
    if config:
        env_config = {'variables': config.variables or {}, 'parameters': config.parameters or {}}

    try:
        total, passed, failed, error, skipped, duration, report_path, log = PytestRunner.run_single_testcase(
            testcase, env_config
        )
        task.status = 'COMPLETED'
    except Exception as e:
        total, passed, failed, error, skipped, duration, report_path, log = 1, 0, 1, 0, 0, 0, '', str(e)
        task.status = 'FAILED'

    task.save(update_fields=['status', 'updated_at'])

    TaskResult.objects.create(
        task=task,
        total_cases=total, passed=passed, failed=failed,
        error=error, skipped=skipped, duration=duration,
        report_path=report_path, log=log,
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': task.status,
            'total': total, 'passed': passed, 'failed': failed,
            'duration': duration,
        })

    messages.success(request, f'用例 "{testcase.name}" 执行完成: {passed}/{total} 通过')
    return redirect('task_result', pk=task.pk)

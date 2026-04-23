import os
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from ..models import Task, TaskResult, TestCase, Module, Project, Scene, Config
from ..pytest_runner import PytestRunner
from ..tasks import run_test_task
from ..utils import collect_testcases, collect_scene_cases, load_env_config

logger = logging.getLogger(__name__)


def task_list(request):
    """任务列表"""
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('task_type', '')
    tasks = Task.objects.select_related('project', 'module', 'testcase', 'scene').prefetch_related('results').all()
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if type_filter:
        tasks = tasks.filter(task_type=type_filter)
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'task/list.html', {
        'page_obj': page_obj,
        'current_status': status_filter,
        'current_type': type_filter,
        'nav_task': 'active',
    })


def task_create(request):
    """创建任务"""
    projects = Project.objects.all()
    scenes = Scene.objects.select_related('project').all()

    if request.method == 'POST':
        task_name = request.POST.get('task_name', '').strip()
        scope = request.POST.get('scope', 'TESTCASE')
        task_type = request.POST.get('task_type', 'SYNC')
        execute_env = request.POST.get('execute_env', 'DEV')
        created_by = request.POST.get('created_by', '').strip()
        report_name = request.POST.get('report_name', '').strip()
        cron_expression = request.POST.get('cron_expression', '').strip()
        email_notify = request.POST.get('email_notify') == 'on'

        if not task_name:
            messages.error(request, '任务名称不能为空')
            return render(request, 'task/form.html', {
                'projects': projects, 'scenes': scenes,
                'nav_task': 'active', 'form_data': request.POST,
            })

        # 定时任务必须提供 cron 表达式
        if task_type == 'SCHEDULE' and not cron_expression:
            messages.error(request, '定时任务必须提供 Cron 表达式')
            return render(request, 'task/form.html', {
                'projects': projects, 'scenes': scenes,
                'nav_task': 'active', 'form_data': request.POST,
            })

        task = Task.objects.create(
            task_name=task_name,
            task_type=task_type,
            status='PENDING',
            scope=scope,
            execute_env=execute_env,
            created_by=created_by,
            report_name=report_name or task_name,
            cron_expression=cron_expression,
            email_notify=email_notify,
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

        # 如果是定时任务，注册到 django-celery-beat
        if task_type == 'SCHEDULE':
            _register_periodic_task(task)

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
        # 如果是定时任务，移除对应的 PeriodicTask
        if task.task_type == 'SCHEDULE':
            _unregister_periodic_task(task)
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

    # 根据 task_type 决定执行方式
    if task.task_type == 'ASYNC' or task.task_type == 'SCHEDULE':
        # 异步执行：提交到 Celery
        task.status = 'PENDING'
        task.save(update_fields=['status', 'updated_at'])
        try:
            run_test_task.delay(task.pk)
            task.status = 'RUNNING'
            task.save(update_fields=['status', 'updated_at'])
            messages.info(request, f'任务 "{task.task_name}" 已提交异步执行')
        except Exception as e:
            logger.exception(f'Failed to dispatch async task {task.pk}')
            task.status = 'FAILED'
            task.save(update_fields=['status', 'updated_at'])
            messages.error(request, f'异步执行提交失败: {str(e)[:100]}')
    else:
        # 同步执行：直接在当前进程执行
        env_config = load_env_config(task)

        # 场景执行使用 run_scene 以支持变量传递
        scene_cases = collect_scene_cases(task)

        if scene_cases is None:
            testcases = collect_testcases(task)
            if not testcases:
                messages.error(request, '未找到可执行的用例')
                return redirect('task_list')
        elif not scene_cases:
            messages.error(request, '场景中无可用例')
            return redirect('task_list')

        task.status = 'RUNNING'
        task.save(update_fields=['status', 'updated_at'])

        try:
            if scene_cases is not None:
                total, passed, failed, error, skipped, duration, report_path, log = \
                    PytestRunner.run_scene(scene_cases, env_config)
            else:
                total, passed, failed, error, skipped, duration, report_path, log = \
                    PytestRunner.run_testcases(testcases, env_config)
            task.status = 'COMPLETED'
        except Exception as e:
            total, passed, failed, error, skipped, duration, report_path, log = \
                0, 0, 0, 0, 0, 0, '', str(e)
            task.status = 'FAILED'

        task.save(update_fields=['status', 'updated_at'])

        TaskResult.objects.create(
            task=task,
            total_cases=total, passed=passed, failed=failed,
            error=error, skipped=skipped, duration=duration,
            report_path=report_path, log=log,
        )

        if task.status == 'COMPLETED':
            messages.success(request, f'任务执行完成: {passed}/{total} 通过')
        else:
            messages.error(request, f'任务执行失败')

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


def task_status(request, pk):
    """任务状态查询 API（AJAX 轮询）"""
    task = get_object_or_404(Task, pk=pk)
    result = task.results.first()
    data = {
        'status': task.status,
        'status_display': task.get_status_display(),
        'task_type': task.task_type,
    }
    if result:
        data.update({
            'total': result.total_cases,
            'passed': result.passed,
            'failed': result.failed,
            'error': result.error,
            'skipped': result.skipped,
            'duration': result.duration,
            'pass_rate': round(result.passed / result.total_cases * 100, 1) if result.total_cases > 0 else 0,
        })
    return JsonResponse(data)


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

    env_config = load_env_config(task)

    try:
        total, passed, failed, error, skipped, duration, report_path, log = \
            PytestRunner.run_single_testcase(testcase, env_config)
        task.status = 'COMPLETED'
    except Exception as e:
        total, passed, failed, error, skipped, duration, report_path, log = \
            1, 0, 1, 0, 0, 0, '', str(e)
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


# ---- Helper functions ----


def _register_periodic_task(task):
    """将定时任务注册到 django-celery-beat"""
    try:
        from django_celery_beat.models import PeriodicTask, CrontabSchedule

        # 解析 cron 表达式: 分 时 日 月 周
        parts = task.cron_expression.split()
        if len(parts) != 5:
            logger.error(f'Invalid cron expression: {task.cron_expression}')
            return

        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=parts[0],
            hour=parts[1],
            day_of_month=parts[2],
            month_of_year=parts[3],
            day_of_week=parts[4],
        )

        PeriodicTask.objects.create(
            name=f'task_{task.pk}_{task.task_name}',
            task='api.tasks.run_test_task',
            args=f'[{task.pk}]',
            crontab=schedule,
            enabled=True,
        )
        logger.info(f'Registered periodic task for Task {task.pk}')
    except Exception as e:
        logger.exception(f'Failed to register periodic task: {e}')


def _unregister_periodic_task(task):
    """从 django-celery-beat 移除定时任务"""
    try:
        from django_celery_beat.models import PeriodicTask
        PeriodicTask.objects.filter(name=f'task_{task.pk}_{task.task_name}').delete()
        logger.info(f'Unregistered periodic task for Task {task.pk}')
    except Exception as e:
        logger.exception(f'Failed to unregister periodic task: {e}')

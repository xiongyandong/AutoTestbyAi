import logging
from celery import shared_task
from .models import Task, TaskResult
from .pytest_runner import PytestRunner
from .utils import collect_testcases, collect_scene_cases, load_env_config

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=1)
def run_test_task(self, task_id):
    """
    异步执行测试任务
    由 Celery Worker 调用，从数据库加载 Task 配置并执行
    """
    try:
        task = Task.objects.select_related(
            'project', 'module', 'testcase', 'scene'
        ).get(pk=task_id)
    except Task.DoesNotExist:
        logger.error(f'Task {task_id} not found')
        return

    # 检查状态
    if task.status == 'COMPLETED':
        logger.info(f'Task {task_id} already completed, skipping')
        return

    # 加载环境配置
    env_config = load_env_config(task)

    # 收集要执行的用例
    scene_cases = collect_scene_cases(task)

    if scene_cases is None:
        testcases = collect_testcases(task)
        if not testcases:
            task.status = 'FAILED'
            task.save(update_fields=['status', 'updated_at'])
            TaskResult.objects.create(
                task=task, total_cases=0, log='未找到可执行的用例'
            )
            return
    elif not scene_cases:
        task.status = 'FAILED'
        task.save(update_fields=['status', 'updated_at'])
        TaskResult.objects.create(
            task=task, total_cases=0, log='场景中无可用例'
        )
        return

    # 更新状态为执行中
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
        logger.exception(f'Task {task_id} execution failed')
        total, passed, failed, error, skipped, duration, report_path, log = \
            0, 0, 0, 0, 0, 0, '', str(e)
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

    logger.info(
        f'Task {task_id} finished: status={task.status}, '
        f'{passed}/{total} passed, duration={duration}s'
    )

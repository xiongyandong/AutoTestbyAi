"""Task helper utilities shared between views and Celery tasks."""
import json
from .models import TestCase, Config


def _ensure_dict(value):
    """确保 JSONField 值为 dict，处理双重编码的情况"""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def collect_testcases(task):
    """根据 task.scope 收集要执行的用例（不含场景编排信息）"""
    if task.scope == 'TESTCASE' and task.testcase:
        return [task.testcase]
    elif task.scope == 'MODULE' and task.module:
        return list(task.module.testcases.all())
    elif task.scope == 'PROJECT' and task.project:
        return list(TestCase.objects.filter(module__project=task.project))
    elif task.scope == 'SCENE' and task.scene:
        return [
            sc.testcase for sc in
            task.scene.scene_cases.select_related('testcase').order_by('order_index')
        ]
    return []


def collect_scene_cases(task):
    """收集场景编排用例（带排序信息），仅 scope=SCENE 时有效"""
    if task.scope == 'SCENE' and task.scene:
        return list(
            task.scene.scene_cases.select_related('testcase').order_by('order_index')
        )
    return None


def load_env_config(task):
    """加载环境配置"""
    if not task.project:
        return None
    config = Config.objects.filter(
        module__project=task.project, env_type=task.execute_env
    ).first()
    if config:
        return {
            'variables': _ensure_dict(config.variables),
            'parameters': _ensure_dict(config.parameters),
            'base_url': config.base_url or '',
        }
    return None

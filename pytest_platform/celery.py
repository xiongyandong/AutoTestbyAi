import os
from celery import Celery

# 设置 Django settings 模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pytest_platform.settings')

app = Celery('pytest_platform')

# 使用 Django settings 中的 CELERY_ 前缀配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现各 app 中的 tasks.py
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Celery Beat 启动后的回调，可在此注册定时任务"""
    pass

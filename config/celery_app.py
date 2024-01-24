import logging
import os

from celery import Celery
from utils.log import InterceptTimedRotatingFileHandler
from celery.signals import setup_logging
from django.conf import settings
# 设置环境变量
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("AfanChatServer")

# namespace='CELERY'作用是允许你在Django配置文件中对Celery进行配置
# 但所有Celery配置项必须以CELERY开头，防止冲突
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动从Django的已注册app中发现任务
app.autodiscover_tasks()


# 一个测试任务
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')





@setup_logging.connect
def setup_logging(*args, **kwargs):
    log_path = settings.LOG_ROOT / 'celery.log'
    logging.basicConfig(handlers=[InterceptTimedRotatingFileHandler(
        log_path, when="W", interval=1, backupCount=7, encoding='utf-8'
    )], level=logging.INFO)

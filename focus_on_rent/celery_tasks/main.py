# Celery的入口文件
from celery import Celery


# 在创建celery实例之前，把Django的配置模块加载到运行环境中
import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'focus_on_rent.settings.dev'


# 创建Celery实例
# Celery('别名')
celery_app = Celery('ihome')

# 加载配置
# celery_app.config_from_object('配置文件')
celery_app.config_from_object('celery_tasks.config')

# 注册异步任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email', 'celery_tasks.pictures'])

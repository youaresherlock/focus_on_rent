# 定义上传图片的异步任务
import json
from celery_tasks.main import celery_app
from focus_on_rent.utils.qiniu import storage


@celery_app.task(name='upload_pictures')
def upload_pictures(data):
    """上传图片到七牛云"""
    data = json.loads(data)
    image_url = storage(data)
    print(image_url)


    return image_url

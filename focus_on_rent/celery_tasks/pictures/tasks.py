# 定义上传图片的异步任务
from celery_tasks.main import celery_app
from celery_tasks.pictures.qiniu.upload import qiniu_upload_file


@celery_app.task(name='upload_pictures')
def upload_pictures(data, filename):
    """上传图片到七牛云"""
    image_url = qiniu_upload_file(data, filename)

    return image_url

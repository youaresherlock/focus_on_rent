from qiniu import Auth, put_data
from django.conf import settings

access_key = settings.QINIU_ACCESS_KEY

secret_key = settings.QINIU_SECRET_KEY

# 空间名
bucket_name = settings.QINIU_BUCKET_NAME

base_url = settings.QINIU_BASE_URL


def qiniu_upload_file(data, filename):
    """
    上传文件
    :param data: 要上传的bytes类型数据
    :param filename: 上传的指定文件名
    :return:
    """
    # 创建鉴权对象
    q = Auth(access_key=access_key, secret_key=secret_key)

    # 生产token, 上传凭证
    token = q.upload_token(bucket=bucket_name)

    # 上传文件，None是文件名，指定None的话七牛云会自动生成一个文件名，也可以自己指定，但自己指定文件名时不能上传重复的文件
    # ret, res = put_data(token, None, data=data)
    ret, res = put_data(token, filename, data=data)

    if res.status_code != 200:
        raise Exception("upload failed")
    file_url = base_url + ret.get('key')

    return file_url

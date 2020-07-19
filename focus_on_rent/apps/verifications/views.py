import json
import re, random, logging
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.shortcuts import render
from django_redis import get_redis_connection
from apps.verifications.libs.captcha.captcha import captcha
from apps.verifications.libs.yuntongxun.ccp_sms import CCP
from celery_tasks.sms.tasks import ccp_send_sms_code

# Create your views here.

# 创建日志输出器
logger = logging.getLogger('django')


class ImageCodeView(View):
    """图片验证码"""

    def get(self, request):
        cur = request.GET.get('cur')
        # 生成图形验证码
        text, image = captcha.generate_captcha()
        print(text)
        # 保存图形验证码
        redis_conn = get_redis_connection('verify_code')
        redis_conn.setex('img_%s' % cur, 300, text)

        # 响应图形验证码
        return HttpResponse(image, content_type='image/jpg')


class SMSCodeView(View):
    """短信验证码"""

    def post(self, request):

        # 判断手机号是否频繁发送短信验证码
        # 接收参数
        json_dict = json.loads(request.body.decode())
        mobile = json_dict.get('mobile')
        id = json_dict.get('id')
        text = json_dict.get('text')

        redis_conn = get_redis_connection('verify_code')
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            return HttpResponse({'errno': 400, 'errmsg': '频繁发送短信验证码'})


        # 校验参数
        if not all([text, id, mobile]):
            return JsonResponse({'errno': 400, 'errmsg': '缺少必传参数'})
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'errno': 400, 'errmsg': '参数mobile有误'})
        image_code_server = redis_conn.get("img_%s" % id)
        if not image_code_server:
            return JsonResponse({'errno': 400, 'errmsg': '图形验证码失效'})

        # 删除图形验证码
        redis_conn.delete('img_%s' % id)

        image_code_server = image_code_server.decode()
        if image_code_server.lower() != text.lower():
            return JsonResponse({'errno': 400, 'errmsg': '图形验证码有误'})

        # 生成短信验证码
        random_num = random.randint(0, 999999)
        sms_code = '%06d' % random_num
        logger.info(sms_code)
        print(sms_code)
        redis_conn = get_redis_connection('verify_code')

        pl = redis_conn.pipeline()
        pl.setex('sms_%s' % mobile, 300, sms_code)
        # 发短信时，给该手机号码添加有效期为60秒的标记
        pl.setex('send_flag_%s' % mobile, 60, 1)
        # 执行管道：千万不要掉了
        pl.execute()

        # ccp_send_sms_code.delay(mobile, sms_code)

        return JsonResponse({'errno': 0, 'errmsg': '发送短信验证码成功'})

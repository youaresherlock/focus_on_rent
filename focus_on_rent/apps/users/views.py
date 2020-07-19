import re

from django.shortcuts import render
from django.views import View
# Create your views here.
from django.http import response
from django import http
import logging,json
from django.contrib.auth import login,authenticate,logout
from django_redis import get_redis_connection
from apps.users.models import User

class RegisterView(View):
    def post(self, request):
        json_dict = json.loads(request.body.decode())
        mobile = json_dict.get('mobile')
        password = json_dict.get('password')
        password2 = json_dict.get('password2')
        sms_code_client = json_dict.get('phonecode')


        if not all([mobile,password,password2]):
            return http.JsonResponse({'errno':400,'errmsg':'缺少必传参数'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'errno':400, 'errmsg':'手机号不对'})

        if not re.match(r'^[a-zA-Z0-9]{8,20}$',password):
            return http.JsonResponse({'errno':400, 'errmsg':'参数password错误'})
        if password != password2:
            return http.JsonResponse({'errno': 400,'errmsg': '两次输入不对'})
        # 6.mobile检验
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        if not sms_code_server:
            return http.JsonResponse({'errno':400, 'errmsg':'短信验证码过期'})
        if sms_code_server.decode() != sms_code_client:
            return http.JsonResponse({'errno':400, 'errmsg': '验证码有误'})
        try:
            user = User.objects.create_user(mobile=mobile,
                                            password=password)
        except Exception as e:
            return http.JsonResponse({'errno':400, 'errmsg':'保存数据库错误'})
        login(request, user)
        response = http.JsonResponse({'errno': 0, 'errmsg': 'ok'})
        response.set_cookie('username', user.mobile, max_age=14*24*3600)
        return response

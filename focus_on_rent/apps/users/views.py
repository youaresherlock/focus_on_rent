import re
import json
from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate

# Create your views here.


class LoginView(View):
    """用户登录
    POST /api/v1.0/session/
    """
    def post(self, request):
        """登录"""
        json_dict = json.loads(request.body.decode())
        mobile = json_dict.get('mobile')
        password = json_dict.get('password')

        if not all([mobile, password]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400, 'errmsg': 'mobile格式错误'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return JsonResponse({'code': 400, 'errmsg': 'password格式错误'})

        user = authenticate(request=request, username=mobile, password=password)
        if user is None:
            return JsonResponse({'code': 400, 'errmsg': '手机号或密码错误'})

        login(request, user)
        
        return JsonResponse({'code': 0, 'errmsg': 'ok'})


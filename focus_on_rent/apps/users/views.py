import re
import json
from django.views import View
from apps.users.models import User
from django.shortcuts import render
from django.http import JsonResponse
from django_redis import get_redis_connection
from django.contrib.auth import login, logout, authenticate





class RegisterView(View):
    def post(self, request):
        json_dict = json.loads(request.body.decode())
        mobile = json_dict.get('mobile')
        password = json_dict.get('password')
        sms_code_client = json_dict.get('phonecode')


        if not all([mobile,password]):
            return JsonResponse({'errno':400,'errmsg':'缺少必传参数'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'errno':400, 'errmsg':'手机号不对'})

        if not re.match(r'^[a-zA-Z0-9]{8,20}$',password):
            return JsonResponse({'errno':400, 'errmsg':'参数password错误'})
        # if password != password2:
        #     return JsonResponse({'errno': 400,'errmsg': '两次输入不对'})
        # 6.mobile检验
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        if not sms_code_server:
            return JsonResponse({'errno':400, 'errmsg':'短信验证码过期'})
        if sms_code_server.decode() != sms_code_client:
            return JsonResponse({'errno':400, 'errmsg': '验证码有误'})
        try:
            user = User.objects.create_user(username=mobile,
                                            password=password)
        except Exception as e:
            return JsonResponse({'errno':400, 'errmsg':'保存数据库错误'})
        login(request, user)
        response = JsonResponse({'errno': 0, 'errmsg': 'ok'})
        response.set_cookie('username', user.mobile, max_age=14*24*3600)
        return response


class LoginView(View):
    """用户登录
    /api/v1.0/session/
    """
    def get(self, request):
        """判断用户是否登录"""
        if request.user.is_authenticated:
            user = request.user
            return JsonResponse({
                "errno": "0",
                "errmsg": "已登录",
                "data": {
                    "name": user.username
                }
            })
        else:
            return JsonResponse({
                "errno": "4101",
                "errmsg": "未登录"
            })

    def post(self, request):
        """登录"""
        json_dict = json.loads(request.body.decode())
        mobile = json_dict.get('mobile')
        password = json_dict.get('password')

        if not all([mobile, password]):
            return JsonResponse({'errno': 400, 'errmsg': '缺少必传参数'})
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'errno': 400, 'errmsg': 'mobile格式错误'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return JsonResponse({'errno': 400, 'errmsg': 'password格式错误'})

        user = authenticate(request=request, username=mobile, password=password)
        if user is None:
            return JsonResponse({'errno': 400, 'errmsg': '手机号或密码错误'})

        login(request, user)
        
        response = JsonResponse({'errno': 0, 'errmsg': '登录成功'})
        # 状态保持的时间周期为两周
        request.session.set_expiry(None)
        response.set_cookie('username', user.mobile, max_age=14 * 24 * 3600)

        return response

    def delete(self, request):
        """退出登录"""
        # 清理登录状态
        logout(request)
        # 清理cookie
        response = JsonResponse({'errno': 0, 'errmsg': '已登出'})
        response.delete_cookie('username')
        return response





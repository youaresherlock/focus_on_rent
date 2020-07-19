from django import http
from django.contrib.auth import logout
from django.shortcuts import render

# Create your views here.
from django.views import View


class LogoutView(View):
    '''退出登录
    '''
    def delete(self,request):
        # 清理登录状态
        logout(request)
        # 清理cookie
        response = http.JsonResponse({'code':0,'errmsg':'已登出'})
        response.delete_cookie('username')
        return response

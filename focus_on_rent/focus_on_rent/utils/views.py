from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse


class LoginRequiredJSONMixin(LoginRequiredMixin):
    """自定义LoginRequiredJSONMixin类,用户未登录,响应JSON,状态码400"""
    def handle_no_permission(self):
        return JsonResponse({'errno': 400, 'errmsg': '用户未登录'})
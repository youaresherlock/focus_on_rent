import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from focus_on_rent.utils.views import LoginRequiredJSONMixin


# Create your views here.

class ReceiveAndRefuseView(LoginRequiredJSONMixin, View):
    '''接单和拒单'''

    def put(self, request, order_id):
        # 接收数据
        json_dict = json.loads(request.body.decode())
        action = json_dict.get('action')
        reason = json_dict.get('reason')
        # 效验参数
        if action == 'accept':
            pass
        elif action == 'reject':
            pass
        else:
            return JsonResponse({'errno': 0, 'errmsg': 'action数据错误'})
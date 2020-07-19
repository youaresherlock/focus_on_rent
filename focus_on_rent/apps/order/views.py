import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from apps.order.models import Order
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
            try:
                Order.objects.filter(id=order_id).update(status=Order.ORDER_STATUS_ENUM["WAIT_PAYMENT"])
            except Exception as e:
                return JsonResponse({'errno': 400, 'errmsg': '数据保存失败'})
            return JsonResponse({'errno': 0, 'errmsg': '操作成功'})
        elif action == 'reject':
            if not reason:
                return JsonResponse({'errno': 400, 'errmsg': '缺少reason参数'})
            try:
                Order.objects.filter(id=order_id).update(
                    status=Order.ORDER_STATUS_ENUM["REJECTED"],
                    comment=reason,
                )
            except Exception as e:
                return JsonResponse({'errno': 400, 'errmsg': '数据保存失败'})
            return JsonResponse({'errno': 0, 'errmsg': '操作成功'})
        else:
            return JsonResponse({'errno': 400, 'errmsg': 'action数据错误'})

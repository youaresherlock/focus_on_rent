import json

from django.shortcuts import render

# Create your views here.
from django.views import View
from django.http import JsonResponse
from focus_on_rent.utils.views import LoginRequiredJSONMixin
from apps.order.models import Order


class GetOrderList(LoginRequiredJSONMixin,View):
    """获取订单列表"""

    def get(self, request):
        # 获取角色类型参数
        role = request.GET.get('role')
        user = request.user
        if not user:
            return JsonResponse({'errno': 400, 'errmsg': '缺少必要参数', })
        if not role:
            return JsonResponse({'errno': 400, 'errmsg': '缺少必要参数', })
        if role == 'custom':
            # 如果是房客,则查询自己的订单
            orders = user.orders.order_by('-create_time')
        if role == 'landlord':
            # 如果是房东,则查询自己的房屋订单
            houses = user.houses
            orders = houses.order_set.order_by(Order.ORDER_STATUS_ENUM.keys())
        order_list = []
        for order in orders:
            order_dict = {
                "amount": order.days * order.house_price,
                "comment": order.comment,
                "ctime": order.create_time,
                "days": order.days,
                "end_date": order.end_date,
                "img_url": order.house.index_image_url,
                "order_id": order.id,
                "start_date": order.begin_date,
                "status": order.status,
                "title": order.house.title
            }
            order_list.append(order_dict)
        return JsonResponse({
            "errmsg": "OK",
            "errno": "0",
            "data": order_list
        })


class CommentOrder(LoginRequiredJSONMixin,View):
    """评价订单"""

    def put(self, request, order_id):
        data_dict = json.loads(request.body.decode())
        comment = data_dict.get('comment')
        if not comment:
            return JsonResponse({"errno": 400, "errmsg": "请填写评论内容"})
        try:
            order = Order.objects.get(id=order_id, status=Order.ORDER_STATUS['WAIT_COMMENT'])
        except Exception:
            return JsonResponse({'errno': 400, 'errmsg': '订单信息查询失败'})
        try:
            order.comment = comment
            order.house.order_count += 1
            order.status = Order.ORDER_STATUS['COMPLETE']
            order.save()
        except Exception:
            return JsonResponse({'errno': 0, 'errmsg': '评价成功'})

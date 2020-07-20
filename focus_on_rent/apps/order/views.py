import json
import datetime

from django.views import View
from apps.order.models import Order
from apps.houses.models import House
from django.http import JsonResponse
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


class GetOrderList(LoginRequiredJSONMixin, View):
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
            houses = user.houses.all()
            houses_id = [house.id for house in houses]
            orders = Order.objects.filter(house_id__in=houses_id).order_by('status')
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


class CommentOrder(LoginRequiredJSONMixin, View):
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

class Addlist(View, LoginRequiredJSONMixin):

    def post(self,request):
        data_dict = json.loads(request.body.decode())
        house_id = data_dict.get('house_id')
        start_date = data_dict.get('start_date')
        end_date = data_dict.get('end_date')
        user = request.user

        if not all([house_id,start_date,end_date]):
            return JsonResponse({'errno': '400', 'errmsg': '缺少必传参数'})
        try:
            house = House.objects.get(id=house_id)
        except Exception as e:
            return JsonResponse({"errno": '400', "errmsg": "房屋不存在"})

        if user == house.user:
            return JsonResponse({"errno": '400', "errmsg": "是房主无法预定"})



        try:
            d1 = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            d2 = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            delta = d2 - d1
            days = delta.days
            if days < 0:
                Exception('日期错误')

        except Exception as e:
            return JsonResponse({'errno': '400', 'errmsg': '参数有误'})

        if days < house.min_days:
            return JsonResponse({'errno': '400', 'errmsg': '住的时间太短'})

        if days > house.max_days:
            return JsonResponse({'errno': '400', 'errmsg': '住的时间太长'})

        try:
            contents = Order.objects.filter(house=house_id, status=Order.ORDER_STATUS['PAID'])

            for content in contents:
                if d1 == content.begin_date:
                    return JsonResponse({'errno': '400', 'errmsg': '日期重复'})

                if (d2 - content.begin_date).days > 0:
                    return JsonResponse({'errno': '400', 'errmsg': '日期冲突'})
        except Exception as e:
                JsonResponse({'errno': '400', 'errmsg': '参数有误'})

        else:
                price = house.price
                amount = price * days

                try:
                     order = Order.objects.create(user = user,
                                                house_id = house,
                                                begin_date = d1,
                                                end_date = d2,
                                                days = days,
                                                amount = amount,
                                                status = Order.ORDER_STATUS['PAID'],
                                                price = price,
                                                )

                except Exception as e:
                    return JsonResponse({'errno': 400, 'errmsg': '保存到数据库错误'})

        return JsonResponse({'errno': '0', 'errmsg': '添加订单成功',  "data": {
                "order_id": order.pk}
                                     })













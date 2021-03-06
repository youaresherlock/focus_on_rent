import json
import datetime

from django.views import View
from django.db import transaction
from apps.order.models import Order
from apps.houses.models import House
from django.http import JsonResponse
from focus_on_rent.utils.views import LoginRequiredJSONMixin


# Create your views here.

class ReceiveAndRefuseView(LoginRequiredJSONMixin, View):
    '''接单和拒单'''

    def put(self, request, order_id):
        # 接收数据
        # print(order_id)
        json_dict = json.loads(request.body.decode())
        action = json_dict.get('action')
        reason = json_dict.get('reason')
        # 效验参数
        if action == 'accept':
            try:
                # Order.objects.get(id=order_id).update(status=Order.ORDER_STATUS["WAIT_COMMENT"])
                order = Order.objects.get(id=order_id)
                order.status=Order.ORDER_STATUS["WAIT_COMMENT"]
                order.save()
            except Exception as e:
                return JsonResponse({'errno': 400, 'errmsg': '数据保存失败'})
            return JsonResponse({'errno': 0, 'errmsg': '操作成功'})
        elif action == 'reject':
            if not reason:
                return JsonResponse({'errno': 400, 'errmsg': '缺少reason参数'})
            try:
                # Order.objects.filter(id=order_id).update(
                #     status=Order.ORDER_STATUS_ENUM["REJECTED"],
                #     comment=reason,
                # )
                order = Order.objects.get(id=order_id)
                order.status = Order.ORDER_STATUS["REJECTED"]
                # order.comment = reason
                order.save()
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
            return JsonResponse({'errno': 400, 'errmsg': '评价失败'})
        return JsonResponse({'errno': 0, 'errmsg': '评价成功'})

class Addlist(View, LoginRequiredJSONMixin):

    def post(self,request):

        data_dict = json.loads(request.body.decode())
        house_id = data_dict.get('house_id')
        start_date = data_dict.get('start_date')
        end_date = data_dict.get('end_date')
        user = request.user

        #判断完整
        if not all([house_id,start_date,end_date]):
            return JsonResponse({'errno': 400, 'errmsg': '缺少必传参数'})
        #是否存在
        try:
            house = House.objects.get(id=house_id)
        except Exception as e:
            return JsonResponse({"errno": 400, "errmsg": "房屋不存在"})
        #是否房主
        if user.id == house.user.id:
            return JsonResponse({"errno": 400, "errmsg": "是房主无法预定"})

        #跳转页面

        #判断是否传入错误数据
        try:
            d1 = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            d2 = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            assert d1 < d2, Exception('开始日期大于结束日期')
            days = (d2 - d1).days
            if days < 0:
                return JsonResponse({'errno': 400, 'errmsg': '日期有误'})
        except Exception as e:
            return JsonResponse({'errno': 400, 'errmsg': '参数有误'})

        #开启事务
        # with transaction.atomic():
        #
        #      save_id = transaction.savepoint()

         # try:
        amount = days * house.price

        if days < house.min_days:
            return JsonResponse({'errno': 400, 'errmsg': '住的时间太短'})

        if days > house.max_days:
            return JsonResponse({'errno': 400, 'errmsg': '住的时间太长'})
        order = Order()
        order.user_id = user.id
        order.house_id = house.id
        order.begin_date = d1
        order.end_date = d2
        order.days = days
        order.amount = amount
        order.house_price = house.price
        order.status = Order.ORDER_STATUS['WAIT_ACCEPT']

        order.save()

        # order = Order.objects.create(user_id=user.id,
        #                              house_id=house_id,
        #                              begin_date=d1,
        #                              end_date=d2,
        #                              days=days,
        #                              amount=amount,
        #                              # # status=Order.ORDER_STATUS['PAID'],
        #                              price=house.price,
        #                              )
        # 判断用户下单的时间段是否有别的订单

        count = Order.objects.filter(house_id=house_id,
                                         begin_date__lte=end_date,
                                         end_date__gte=start_date).count()
        if count > 0:
            # 说明房子被别人预定
            # transaction.savepoint_rollback(save_id)
            return JsonResponse({'errno': 400, 'errmsg': '房子已被预定'})

             # except Exception as e:
             #     transaction.savepoint_rollback(save_id)
             #     return JsonResponse({'errno': 400, 'errmsg': '下单失败'})

            #提交事务

             # transaction.savepoint_commit(save_id)
        return JsonResponse({'errno': 0, 'errmsg': '添加订单成功',  "data": {"order_id": order.pk}})

    def get(self, request):
        user = request.user
        role = request.GET.get('role')

        if not role:
            return JsonResponse({"errno": 400, "errmsg": "参数错误"})

        if role not in ["landlord", "custom"]:
            return JsonResponse({"errno": 400, "errmsg": "参数错误"})

        if role == "custom":
            # 查询当前自己下了哪些订单
            orders = Order.objects.filter(user=user).order_by("-create_time")
        else:
            # 查询自己房屋都有哪些订单
            houses = House.objects.filter(user=user)
            house_ids = [house.id for house in houses]
            orders = Order.objects.filter(house_id__in=house_ids).order_by("-create_time")


        orders_list = []
        for order in orders:
            order_dict = {
                "amount":order.amount,
                "comment":order.comment,
                "ctime":order.create_time,
                "days":order.days,
                "end_date":order.end_date,
                "img_url":order.house.index_image_url,
                "order_id":order.id,
                "start_date":order.begin_date,
                "status":order.ORDER_STATUS_ENUM[order.status],
                "title":order.house.title
            }
            orders_list.append(order_dict)

        return JsonResponse({"errno": 0, "errmsg": "发布成功", "data": {"orders": orders_list}})













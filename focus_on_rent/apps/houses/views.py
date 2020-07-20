# Create your views here.
import json
from django.views import View
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from apps.houses.models import House, Facility, Area
from focus_on_rent.utils.views import LoginRequiredJSONMixin


class DetailView(View):
    '''商品详情页'''

    def get(self, request, house_id):
        # 判断用户是否是匿名用户
        if not request.user.is_authenticated:
            user_id = -1
        else:
            user_id = request.user.id
        # 查数据
        try:
            house = House.objects.get(id=house_id)
            orders = house.order_set()
            comment_list = []
            for order in orders:
                comment_list.append({
                    "comment": order.comment,
                    "ctime": order.begin_date,
                    "user_name": order.user.real_name,
                })
            decilities = house.facility
            facility_list = []
            for dec in decilities:
                facility_list.append(dec.id)

            img_urls = []
            for image in house.house:
                img_urls.append(settings.QINIU_ADDRESS + image.url)
            house_date = {
                "acreage": house.acreage,
                "address": house.address,
                "beds": house.beds,
                "capacity": house.capacity,
                "comments": comment_list,
                "deposit": house.deposit,
                "facilities": facility_list,
                "hid": house.id,
                "img_urls": img_urls,
                "max_days": house.max_days,
                "min_days": house.min_days,
                "price": house.price,
                "room_count": house.room_count,
                "title": house.title,
                "unit": house.unit,
                "user_avatar": settings.QINIU_ADDRESS + house.user.avatar,
                "user_id": house.user.id,
                "user_name": house.user.name,
            }
        except Exception as e:
            return JsonResponse({'errno': 400, 'errmsg': '数据请求失败'})

        dict = {"house": house_date, "user_id": user_id}

        return JsonResponse({'errno': 0, 'errmsg': 'OK', 'user_id': user_id, 'dict': dict})


class HousesView(LoginRequiredJSONMixin, View):
    def get(self, request):
        """房屋搜索"""
        area = request.GET.get('aid')
        start_day = request.GET.get('sd')
        end_day = request.GET.get('ed')
        sort_key = request.GET.get('sk')  # 排序方式
        page = request.GET.get('p', '1')  # 查询页数  没有默认为 1
        # 处理页数
        page = int(page)
        # 判断城区
        if not area:
            return ({'errno': 400, 'errmsg': '请选择城区城区'})
        # 判断时间
        if not start_day or not end_day:
            return ({'errno': 400, 'errmsg': '请输入准确的时间'})


    def post(self, request):
        """发布房源"""

        # 接收参数
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        price = json_dict.get('price')
        acreage = json_dict.get('acreage')
        area_id = json_dict.get('area_id')
        address = json_dict.get('address')
        room_count = json_dict.get('room_count')
        unit = json_dict.get('unit')
        capacity = json_dict.get('capacity')
        beds = json_dict.get('beds')
        deposit = json_dict.get('deposit')
        min_days = json_dict.get('min_days')
        max_days = json_dict.get('max_days')

        if not all([title, price, area_id, address, room_count, unit, capacity,
                    beds, deposit, min_days, max_days, acreage,]):
            return JsonResponse({'errno': 400, 'errmsg': '缺少必传参数'})

        try:
            area = Area.objects.get(id=area_id)
        except BaseException as e:
            return JsonResponse({'errno': 400, 'errmsg': '地址不存在'})

        # 设置数据到模型
        house = House()
        house.user = request.user
        house.title= title,
        house.price = price,
        house.area = area,
        house.address = address,
        house.acreage = acreage,
        house.room_count = room_count,
        house.unit = unit,
        house.capacity = capacity,
        house.beds = beds,
        house.deposit = deposit,
        house.min_days = min_days,
        house.max_days = max_days,

        # 同步至数据库
        try:
            house.save()
        except BaseException as e:
            return JsonResponse({'errno': 400, 'errmsg': '保存房源信息失败'})

        # 设置设施信息
        try:
            facility_ids = json_dict.get('facility')
            if facility_ids:
                facilities = Facility.objects.filter(id__in=facility_ids)
                for facility in facilities:
                    house.facility.add(facility)
        except BaseException as e:
            return JsonResponse({'errno': 400, 'errmsg': '保存设施信息失败'})

        return JsonResponse({'errno': '0', 'errmsg': '发布成功', "data": {"house_id": house.pk}})
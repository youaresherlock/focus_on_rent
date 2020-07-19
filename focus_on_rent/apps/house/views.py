import json
from django.views import View
from django.shortcuts import render
from apps.house.models import House
from django.http import JsonResponse
from apps.house.models import Area
from focus_on_rent.utils.views import LoginRequiredJSONMixin

# Create your views here.


class UploadHousesImages(LoginRequiredJSONMixin, View):
    """上传房源图片
    /api/v1.0/houses/[int:house_id]/images
    """
    def post(self, request):
        """上传房源图片"""
        json_dict = json.loads(request.body.decode())
        house_image = json_dict.get('house_image')


class HousesView(LoginRequiredJSONMixin, View):
    """发布房源"""

    def post(self, request):

        # 接收参数
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        price = json_dict.get('price')
        area_id = json_dict.get('area_id')
        address = json_dict.get('address')
        room_count = json_dict.get('room_count')
        unit = json_dict.get('unit')
        capacity = json_dict.get('capacity')
        beds = json_dict.get('beds')
        deposit = json_dict.get('deposit')
        min_days = json_dict.get('min_days')
        max_days = json_dict.get('max_days')
        facility = json_dict.get('facility')

        if not all([title, price, area_id, address, room_count, unit, capacity,
                    beds, deposit, min_days, max_days, facility,]):
            return JsonResponse({'errno': 400, 'errmsg': '缺少必传参数'})

        try:
            area = Area.objects.get(id=area_id)
        except BaseException as e:
            return JsonResponse({'errno': 400, 'errmsg': '地址不存在'})


        try:
            House.objects.filter(house_id=area_id).update(
            title= title,
            price = price,
            area_id = area_id,
            address = address,
            room_count = room_count,
            unit = unit,
            capacity = capacity,
            beds = beds,
            deposit = deposit,
            min_days = min_days,
            max_days = max_days,
            facility = facility,
            )
        except:
            return JsonResponse({'errno': 400, 'errmsg': '更新房屋信息失败'})

        # 房屋ID
        house_id = request.house_set.filter('area_id086y')

        return JsonResponse({'errno': '0', 'errmsg': '发布成功', "data": {"house_id": house_id}})

























































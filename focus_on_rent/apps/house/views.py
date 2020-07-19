import json
import logging
from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from apps.house.models import House, HouseImage
from celery_tasks.pictures.tasks import upload_pictures
from focus_on_rent.utils.views import LoginRequiredJSONMixin

# Create your views here.


# 日志输出器
logger = logging.getLogger('django')


class HousesView(LoginRequiredJSONMixin, View):
    """
    /api/v1.0/user/houses
    """
    def get(self, request):
        """我的房屋列表"""
        houses_model_list = request.user.houses.all()
        houses_list = []
        for house in houses_model_list:
            houses_list.append({
                'address': house.address,
                'area_name': house.area.name,
                'ctime': house.create_time,
                'house_id': house.id,
                'img_url': house.index_image_url,
                'order_count': house.order_count,
                'price': house.price,
                'room_count': house.room_count,
                'title': house.title,
                'user_avator': request.user.avatar.url,
            })

        return JsonResponse({'data': {'houses': houses_list}, 'errmsg': 'ok', 'errno': 0})


class UploadHousesImages(LoginRequiredJSONMixin, View):
    """上传房源图片
    /api/v1.0/houses/<int:house_id>/images
    """
    def post(self, request, house_id):
        """上传房源图片"""
        json_dict = json.loads(request.body.decode())
        house_image = json_dict.get('house_image')

        if not house_image:
            return JsonResponse({'errno': 400, 'errmsg': '缺少必传参数'})
        try:
            house = House.objects.get(id=house_id)
        except House.DoesNotExist:
            return JsonResponse({'errno': 400, 'errmsg': 'house_id不存在'})

        result = upload_pictures.delay(house_image, None)
        url = result.get()

        # 设置房屋图片
        try:
            HouseImage.objects.create(house=house, url=url)
            # 设置房屋主图片
            if not house.index_image_url:
                house.index_image_url = url
                house.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'errno': 400, 'errmsg': '新增图片失败'})

        return JsonResponse({'data': {'url': url}, 'errno': 0, 'errmsg': '图片上传成功'})




























































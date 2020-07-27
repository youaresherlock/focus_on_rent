# Create your views here.
import json
import base64
import logging
import datetime
from django.views import View
from django.conf import settings
from django.core.cache import cache
from apps.order.models import Order
from django.http import JsonResponse
from apps.houses.models import HouseImage
from django.core.paginator import Paginator
from django.db import DatabaseError, transaction
from focus_on_rent.utils.image_check import image_file
from apps.houses.models import House, Facility, Area
from celery_tasks.pictures.tasks import upload_pictures
from celery_tasks.pictures.qiniu.upload import qiniu_upload_file
from focus_on_rent.utils.views import LoginRequiredJSONMixin
from focus_on_rent.utils.recommand import similarity, recommand_list


logger = logging.getLogger('django')


class UploadHousePictureView(View):
    """上传房源图片
    /api/v1.0/houses/[int:house_id]/images
    """
    def post(self, request, house_id):
        house_image = request.FILES.get('house_image')

        if not house_image:
            return JsonResponse({'errno': 400, 'errmsg': '房屋图片为空'})
        if not image_file(house_image):
            return JsonResponse({'errno': 400, 'errmsg': '上传的不是图片'})

        try:
            house = House.objects.get(id=house_id)
        except House.DoesNotExist:
            return JsonResponse({'errno': 400, 'errmsg': '房屋不存在'})
        if house.user_id != request.user.id:
            return JsonResponse({'errno': 400, 'errmsg': '只有房主才能修改房屋图片'})

        image_content = house_image.read()
        # image_content = base64.b64encode(image_content).decode()
        # image_name = upload_pictures.delay(image_content)
        # image_url = settings.QINIU_ADDRESS + image_name.get()

        image_url = qiniu_upload_file(image_content, None)
        image_url = settings.QINIU_ADDRESS + image_url
        print(image_url)

        try:
            HouseImage.objects.create(house=house, url=image_url)
            if not house.index_image_url:
                house.index_image_url = image_url
                house.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'errno': 400, 'errmsg': '保存图片错误'})

        return JsonResponse({'data': {'url': image_url}, 'errno': 0, 'errmsg': '图片上传成功'})


class HousesCommandView(View):
    """首页房屋推荐"""
    def get(self, request):
        now = datetime.date.today()
        house_models_list = House.objects.exclude(user=request.user)
        houses_ids = [house.id for house in house_models_list]
        status_list = [Order.ORDER_STATUS.get("WAIT_ACCEPT"), Order.ORDER_STATUS.get("WAIT_PAYMENT"),
                       Order.ORDER_STATUS.get("PAID"), Order.ORDER_STATUS.get("WAIT_COMMENT")]
        for house in house_models_list:
            count = house.order_set.filter(status__in=status_list, begin_date__gt=now, end_date__lt=now).count()
            if count > 0:
                houses_ids.remove(house.id)

        recommands = houses_ids[5::-1]
        # houses_model_list = House.objects.filter(user=request.user)
        # houses_ids = [house.id for house in houses_model_list]
        #
        # status = [Order.ORDER_STATUS['PAID'], Order.ORDER_STATUS['WAIT_COMMENT'], Order.ORDER_STATUS['COMPLETE']]
        # orders_model_list = Order.objects.filter(status__in=status)
        # data_set = {}
        # for order in orders_model_list:
        #     user, score, item = str(order.user.id), '1', str(order.house.id)
        #     data_set.setdefault(user, {})
        #     data_set[user][item] = score
        # item_similarity_matrix = similarity(data_set)
        # recommands = recommand_list(data_set, item_similarity_matrix, str(request.user.id), 10, 5, houses_ids)

        data_list = []
        for house_id in recommands:
            house = House.objects.get(id=house_id)
            data_list.append({
                'house_id': house.id,
                'img_url': house.index_image_url,
                'title': house.title
            })

        return JsonResponse({'data': data_list, 'errmsg': 'ok', 'errno': 0})


class DetailView(View):
    """商品详情页"""

    def get(self, request, house_id):
        # 判断用户是否是匿名用户
        if not request.user.is_authenticated:
            user_id = -1
        else:
            user_id = request.user.id
        # 查数据
        try:
            house = House.objects.get(id=house_id)
            # 只有已完成的订单有评价
            orders = house.order_set.filter(status=Order.ORDER_STATUS['COMPLETE'])
            comment_list = []
            for order in orders:
                comment_list.append({
                    "comment": order.comment,
                    "ctime": order.begin_date.strftime("%Y-%m-%d"),
                    "user_name": order.user.real_name,
                })
            decilities = house.facility.all()
            facility_list = []
            for dec in decilities:
                facility_list.append(dec.id)

            img_urls = []
            for image in house.houseimage_set.all():
                img_urls.append(image.url)
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
                "user_avatar": settings.QINIU_ADDRESS + str(house.user.avatar),
                "user_id": house.user.id,
                "user_name": house.user.username,
            }
        except Exception as e:
            return JsonResponse({'errno': 400, 'errmsg': '数据请求失败'})

        data = {"house": house_date, "user_id": user_id}

        return JsonResponse({'errno': 0, 'errmsg': 'OK', 'user_id': user_id, 'data': data})


class HousesView(View):
    def get(self, request):
        """房屋搜索"""
        area = request.GET.get('aid')
        start_day = request.GET.get('sd')
        end_day = request.GET.get('ed')
        sort_key = request.GET.get('sk')  # 排序方式
        page = request.GET.get('p', '1')  # 查询页数  没有默认为 1
        # 处理页数
        page = int(page)

        if not area:
            houses1 = House.objects.all()
        else:
            houses1 = House.objects.filter(area_id=area)

        houses1_list = [houses.id for houses in houses1]

        # 都是非必传参数,所以不检验数据完整性
        # 开始时间格式的转换
        if start_day:
            start_date = datetime.datetime.strptime(start_day, '%Y-%m-%d')
        # 结束时间格式的转换
        if end_day:
            end_date = datetime.datetime.strptime(end_day, '%Y-%m-%d')

        if start_day:
            orderes = Order.objects.filter(end_date__gt=start_date)
            house_ids1 = [orders.house_id for orders in orderes]
            if len(house_ids1) == 0:
                house_ids = house_ids1
            else:

                for house in house_ids1:
                    house = House.objects.get(id=house)
                    min_day = house.min_days
                    delta = datetime.timedelta(days=min_day)
                    start_date = start_date + delta
                    orderes2 = Order.objects.filter(begin_date__lt=start_date)
                    house_ids2 = [orders.house_id for orders in orderes2]
                    house_ids = house_ids1 + house_ids2
        elif end_day:
            orderes = Order.objects.filter(begin_date__lt=end_date)
            house_ids1 = [orders.house_id for orders in orderes]
            if len(house_ids1) == 0:
                house_ids = house_ids1
            else:
                for house in house_ids1:
                    min_day = house.min_days
                    delta = datetime.timedelta(days=min_day)
                    end_date = start_date - delta
                    orderes2 = Order.objects.filter(end_date__lt=end_date)
                    house_ids2 = [orders.house_id for orders in orderes2]
                    house_ids = house_ids1 + house_ids2

        elif start_day and end_day:
            days = end_day - start_day
            house1 = House.objects.filter(min_days__gt=days)
            house_ids1 = [house.id for house in house1]
            house2 = House.objects.filter(max_days_lt=days)
            house_ids2 = [house.id for house in house2]
            orderes = Order.objects.filter(begin_date__lt=end_day, end_date__gt=start_day)
            house_ids3 = [orders.house_id for orders in orderes]
            house_ids = house_ids1 + house_ids2 + house_ids3

        else:
            house_ids = []

        for house_id in house_ids:
            if house_id in houses1_list:
                houses1_list.remove(house_id)

        houses2 = House.objects.filter(id__in=houses1_list)

        if sort_key == 'booking':
            # 按照订单量查询
            house_qs = houses2.order_by('-order_count')
        elif sort_key == 'price-inc':
            # 按照价格从低到高
            house_qs = houses2.order_by('price')
        elif sort_key == 'price-des':
            # 按照价格从高到低
            house_qs = houses2.order_by('-price')
        else:
            house_qs = houses2.order_by('-create_time')
        # 分页
        paginator = Paginator(house_qs, 3)
        # 获取每页对象
        page_house = paginator.page(page)
        # 获取总页数
        page_total = paginator.num_pages

        data = {}
        house_data = []

        for house in page_house:
            house_dict = {
                "address": house.address,
                "area_name": house.area.name,
                "ctime": house.create_time,
                "house_id": house.id,
                "img_url": house.index_image_url,
                "order_count": house.order_count,
                "price": house.price,
                "room_count": house.room_count,
                "title": house.title,
                "user_avatar": settings.QINIU_ADDRESS + str(house.user.avatar)
            }
            house_data.append(house_dict)

        data['houses']= house_data
        data['total_page'] = page_total
        return JsonResponse({
            "errmsg": "请求成功",
            "errno": "0",
            "data":data
        })

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
        # 判断参数是否完整
        if not all([title, price, area_id, address, room_count, unit, capacity,
                    beds, deposit, min_days, max_days, acreage]):
            return JsonResponse({'errno': 400, 'errmsg': '缺少必传参数'})
        # 对参数的合理性进行校验
        if int(price) < 0:
            return JsonResponse({'errno': 400, 'errmsg': '价格不能为负'})
        try:
            area = Area.objects.get(id=area_id)
        except Area.DoesNotExist:
            return JsonResponse({'errno': 400, 'errmsg': 'area_id不存在'})
        if int(room_count) < 0:
            return JsonResponse({'errno': 400, 'errmsg': '房间数不能为负'})
        if int(acreage) < 0:
            return JsonResponse({'errno': 400, 'errmsg': '房间面积不能为负'})
        if int(capacity) < 0:
            return JsonResponse({'errno': 400, 'errmsg': '房间容纳的人数不能为负'})
        if int(deposit) < 0:
            return JsonResponse({'errno': 400, 'errmsg': '押金不能为负'})
        if int(max_days) < 0 or int(min_days) < 0:
            return JsonResponse({'errno': 400, 'errmsg': '可入住天数不能为负'})
        if int(max_days) != 0 and int(max_days) < int(min_days):
            return JsonResponse({'errno': 400, 'errmsg': '最大入住天数不能小于最小入住天数'})

        try:
            price = int(float(price) * 100)
            deposit = int(float(deposit) * 100)
        except Exception as e:
            return JsonResponse({'errno': 400, 'errmsg': '金额参数错误'})

        while True:
            # 开启事务,保证数据库操作的正确性,一致性
            with transaction.atomic():
                save_point = transaction.savepoint()

                # 设置数据到模型
                try:
                    house = House.objects.create(
                        user=request.user,
                        title=title,
                        price=price,
                        area_id=area_id,
                        address=address,
                        acreage=acreage,
                        room_count=room_count,
                        unit=unit,
                        capacity=capacity,
                        beds=beds,
                        deposit=deposit,
                        min_days=min_days,
                        max_days=max_days,
                    )
                # 同步至数据库
                    facility_ids = json_dict.get('facility')
                    if facility_ids:
                        facilities = Facility.objects.filter(id__in=facility_ids)
                        for facility in facilities:
                            house.facility.add(facility)
                except DatabaseError as e:
                    transaction.savepoint_rollback(save_point)
                    return JsonResponse({'errno': 400, 'errmsg': '保存设施信息失败'})

                # 数据库操作无误
                transaction.savepoint_commit(save_point)
                break

        # 响应结果
        return JsonResponse({'errno': '0', 'errmsg': '发布成功', "data": {"house_id": house.pk}})

      
class AreasView(LoginRequiredJSONMixin, View):
    """
    /api/v1.0/areas
    """
    def get(self, request):
        """获取城区列表"""
        # 获取缓存
        areas = cache.get('area_list')

        if areas:
            return JsonResponse({'errno': 0, 'errmsg': '获取成功', 'data': areas})

        try:
            area_model_list = Area.objects.all()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'errno': 400, 'errmsg': '数据库错误'})
        areas = []
        for area in area_model_list:
            areas.append({
                'aid': area.id,
                'aname': area.name
            })
        cache.set('area_list', areas, 3600)

        return JsonResponse({'errno': 0, 'errmsg': '获取成功', 'data': areas})













       



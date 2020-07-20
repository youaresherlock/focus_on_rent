# Create your views here.
import json
import datetime
from django.views import View
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from apps.houses.models import House, Facility, Area
from focus_on_rent.utils.views import LoginRequiredJSONMixin
from apps.order.models import Order
from django.core.paginator import Paginator
from focus_on_rent.utils.recommand import similarity, recommand_list


class HousesCommandView(View):
    """首页房屋推荐"""
    def get(self, request):
        houses_model_list = House.objects.filter(user=request.user)
        houses_ids = [str(house.id) for house in houses_model_list]

        status = [Order.ORDER_STATUS['PAID'], Order.ORDER_STATUS['WAIT_COMMENT'], Order.ORDER_STATUS['COMPLETE']]
        orders_model_list = Order.objects.filter(status__in=status)
        data_set = {}
        for order in orders_model_list:
            user, score, item = str(order.user.id), '1', str(order.house.id)
            data_set.setdefault(user, {})
            data_set[user][item] = score
        item_similarity_matrix = similarity(data_set)
        recommands = recommand_list(data_set, item_similarity_matrix, str(request.user.id), 10, 5, houses_ids)

        data_list = []
        for house_id, _ in recommands:
            house = House.objects.get(id=int(house_id))
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
        #都是非必传参数,所以不检验数据完整性
        # 开始时间格式的转换
        if start_day:
            start_date = datetime.datetime.strptime(start_day, '%Y-%m-%d')
        # 结束时间格式的转换
        if end_day:
            end_date = datetime.datetime.strptime(end_day, '%Y-%m-%d')
        # 创建筛选条件
        filters = {}
        if area:
            filters['area_id'] = area
        # 查询时间看是否符合
        if start_day and end_day:
            orderes = Order.objects.filter(begin_date__gt=end_day,end_date__lte=start_day)
        elif start_day:
            orderes = Order.objects.filter(end_date__lte=start_day)
        elif end_day:
            orderes = Order.objects.filter(begin_date__gt=end_day)
        else:
            orderes = []
        # 找出时间符合的订单id
        orderes_id = [order.id for order in orderes]
        filters['id__in']=orderes_id
        # 根据筛选条件选择符合的房屋
        houses = House.objects.filter(**filters)
        # 以传递参数来进行排序
        if sort_key == 'booking':
            # 按照订单量查询
            house_qs = houses.order_by('-order_count')
        elif sort_key == 'price-inc':
            # 按照价格从低到高
            house_qs = houses.order_by('price')
        elif sort_key == 'price-des':
            # 按照价格从高到低
            house_qs = houses.order_by('-price')
        else:
            house_qs = houses.order_by('-create_time')

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
                "area_name": house.area,
                "ctime": house.create_time,
                "house_id": house.id,
                "img_url": house.index_image_url,
                "order_count": house.order_count,
                "price": house.price,
                "room_count": house.room_count,
                "title": house.title,
                "user_avatar": house.user.avatar
            }
            house_data.append(house_dict)
        data['houses'] = house_data
        data['total_page'] = page_total
        return JsonResponse({
            "errmsg": "请求成功",
            "errno": "0",
            "data": data
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

      
class Areas(View):
    def get(self,request):
        try:
            if request.user.is_authenticated:

                areas=Area.objects.all()
                data=[]
                for area in areas:
                    data.append({
                        "aid": area.id,
                        "aname": area.name,
                    })

                return JsonResponse({ "errno": '0',"errmsg": "获取成功","data":data})
            else:
                return JsonResponse({"errno": "400", "errmsg": "未登录"})
        except Exception as e:
            return JsonResponse({"errno": "400", "errmsg": "获取失败"})


       



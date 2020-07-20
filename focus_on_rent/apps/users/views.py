import re
import json
from django.views import View
from django.conf import settings
from django.shortcuts import render
from apps.users.models import User
from apps.houses.models import House
from django.http import JsonResponse
from django_redis import get_redis_connection
from focus_on_rent.utils.qiniu import storage
from focus_on_rent.utils.realname import IDauth
from django.contrib.auth import login, logout, authenticate
from focus_on_rent.utils.views import LoginRequiredJSONMixin


class HousesListView(View):
    """房屋列表
    /api/v1.0/user/houses
    """
    def get(self, request):
        houses_model_list = House.objects.filter(user=request.user)
        houses = []
        for house in houses_model_list:
            houses.append({
                'address': house.address,
                'area_name': house.area.name,
                'ctime': house.create_time,
                'house_id': house.id,
                'img_url': house.index_image_url,
                'order_count': house.order_count,
                'price': house.price,
                'room_count': house.room_count,
                'title': house.title,
                'user_avatar': settings.QINIU_ADDRESS + house.user.avatar
            })

        return JsonResponse({'data': {'houses': houses}, 'errmsg': 'ok', 'errno': 0})


class UpPersonImageView(LoginRequiredJSONMixin,View):
    '''上传个人图像'''

    def post(self, request):

        myFile = request.FILES.get("avatar").read()

        imageurl = storage(myFile)

        if not imageurl:
            return JsonResponse({'errno': 400, 'errmsg': '未上传图像'})
        else:
            try:
                User.objects.filter(id=request.user.id).update(
                    avatar=imageurl
                )
            except Exception as e:
                return JsonResponse({'errno': 400, 'errmsg': '图像保存到数据库错误'})
            avatar_url = settings.QINIU_ADDRESS + imageurl
            data = {'avatar_url': avatar_url}
            return JsonResponse({'errno': 0, "errmsg": "头像上传成功", 'data': {data}})


class RegisterView(View):
    def post(self, request):
        json_dict = json.loads(request.body.decode())
        mobile = json_dict.get('mobile')
        password = json_dict.get('password')
        sms_code_client = json_dict.get('phonecode')

        if not all([mobile, password]):
            return JsonResponse({'errno': 400, 'errmsg': '缺少必传参数'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'errno': 400, 'errmsg': '手机号不对'})

        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return JsonResponse({'errno': 400, 'errmsg': '参数password错误'})
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        if not sms_code_server:
            return JsonResponse({'errno': 400, 'errmsg': '短信验证码过期'})
        if sms_code_server.decode() != sms_code_client:
            return JsonResponse({'errno': 400, 'errmsg': '验证码有误'})
        try:
            user = User.objects.create_user(username=mobile,
                                            password=password)
        except Exception as e:
            return JsonResponse({'errno': 400, 'errmsg': '保存数据库错误'})
        login(request, user)
        response = JsonResponse({'errno': 0, 'errmsg': 'ok'})
        response.set_cookie('username', user.mobile, max_age=14 * 24 * 3600)
        return response


class LoginView(View):
    """用户登录
    /api/v1.0/session/
    """

    def get(self, request):
        """判断用户是否登录"""
        if request.user.is_authenticated:
            user = request.user
            return JsonResponse({
                "errno": "0",
                "errmsg": "已登录",
                "data": {
                    "user_id": user.id,
                    "name": user.username
                }
            })
        else:
            return JsonResponse({
                "errno": "4101",
                "errmsg": "未登录"
            })

    def post(self, request):
        """登录"""
        json_dict = json.loads(request.body.decode())
        mobile = json_dict.get('mobile')
        password = json_dict.get('password')

        if not all([mobile, password]):
            return JsonResponse({'errno': 400, 'errmsg': '缺少必传参数'})
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'errno': 400, 'errmsg': 'mobile格式错误'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return JsonResponse({'errno': 400, 'errmsg': 'password格式错误'})

        user = authenticate(request=request, username=mobile, password=password)
        if user is None:
            return JsonResponse({'errno': 400, 'errmsg': '手机号或密码错误'})

        login(request, user)

        response = JsonResponse({'errno': 0, 'errmsg': '登录成功'})
        # 状态保持的时间周期为两周
        request.session.set_expiry(None)
        response.set_cookie('username', user.mobile, max_age=14 * 24 * 3600)

        return response

    def delete(self, request):
        """退出登录"""
        # 清理登录状态
        logout(request)
        # 清理cookie
        response = JsonResponse({'errno': 0, 'errmsg': '已登出'})
        response.delete_cookie('username')
        return response


class Realname(View, LoginRequiredJSONMixin):
    def post(self, request):
        """登录"""
        json_dict = json.loads(request.body.decode())
        real_name = json_dict.get('real_name')
        id_card = json_dict.get('id_card')

        if not all([real_name, id_card]):
            return JsonResponse({'code': 400, 'errmsg': '缺少比穿参数'})
        if not re.match('^[1-9]\d{5}(18|19|([23]\d))\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$'):
            return JsonResponse({'code': 400, 'errmsg': '身份证号码有误'})
        content = IDauth(real_name, id_card)
        if content['status'] == '01':
            try:
                user = User.objects.create_user(real_name=real_name,
                                                id_card=id_card)
                user.save()
            except Exception as e:
                return JsonResponse({'errno': 400, 'errmsg': '保存到数据库错误'})
        else:
            return JsonResponse({'errno': 400, 'errmsg': '实名制失败'})
        return JsonResponse({"errno": "0", "errmsg": "认证信息保存成功"})


class UserInfoView(LoginRequiredJSONMixin, View):
    """个人中心"""

    def get(self, request):
        # 接收参数
        avatar = request.user.avatar
        create_time = request.user.create_time
        mobile = request.user.mobile
        name = request.user.real_name
        user_id = request.user.id

        # 用户信息字典
        data_dict = {
            "data": {
                "avatar": avatar,
                "create_time": create_time,
                "mobile": mobile,
                "name": name,
                "user_id": user_id,
            },
            "errmsg": 'OK',
            "errno": '0',
        }

        # 响应结果
        return JsonResponse(data_dict)


class ChangeUserNameView(View):
    """修改用户名"""

    def put(self, request, name):

        # 接收参数
        json_dict = json.loads(request.body.decode())
        new_name = json_dict.get('name')

        # 校验参数
        if new_name:
            if not re.match(r'^[a-zA-Z_0-9]{6,20}$', new_name):
                return JsonResponse({'errno': 400, 'errmsg': '用户名格式错误'})

            user = request.user
            # 修改用户名
            try:
                user.username = new_name
                user.save()
            except BaseException as e:
                return JsonResponse({'errno': 400, 'errmsg': '修改用户名失败'})

        # 响应结果
        return JsonResponse({'errno': '0', 'errmsg': '修改成功'})


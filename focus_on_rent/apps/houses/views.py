from django.shortcuts import render

# Create your views here.
from django.views import View


class HousesView(View):
    def get(self, request):
        """房屋搜索"""
        area = request.GET.get('aid')
        start_day = request.GET.get('sd')
        end_day = request.GET.get('ed')
        sort_key = request.GET.get('sk') # 排序方式
        page = request.GET.get('p', '1') # 查询页数  没有默认为 1
        # 处理页数
        page = int(page)
        # 判断城区
        if not area:
            return ({'errno': 400, 'errmsg': '请选择城区城区'})
        # 判断时间
        if not start_day or not end_day:
            return ({'errno':400,'errmsg':'请输入准确的时间'})

        


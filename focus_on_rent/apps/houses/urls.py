from django.urls import path
from . import views

urlpatterns = [
    # 房屋数据搜索
    path('houses',views.HousesView.as_view())
]
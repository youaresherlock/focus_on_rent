
from django.urls import path
from . import views

urlpatterns = [
    # 房屋数据搜索
    path('houses', views.HousesView.as_view()),
    path('/houses/<int:house_id>', views.DetailView.as_view()),
    path('/houses/index', views.HousesCommandView.as_view()),
    path('areas', views.Areas.as_view()),
]
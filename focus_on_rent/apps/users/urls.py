from django.urls import re_path, path
from . import views

urlpatterns =[
    # 退出登录
    path('api/v1.0/session/',views.LogoutView.as_view()),
]
from django.urls import re_path, path
from . import views

urlpatterns =[
    # 接单和拒单
    path('orders/<int:order_id>/status',views.ReceiveAndRefuseView.as_view()),
]
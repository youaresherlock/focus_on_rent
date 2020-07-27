
from django.urls import path
from . import views

urlpatterns = [
    # 获取订单列表
    path('user/orders', views.GetOrderListView.as_view()),
    # 评价订单
    path('orders/<int:order_id>/comment', views.CommentOrderView.as_view()),
    path('orders/<int:order_id>/status', views.ReceiveAndRefuseView.as_view()),
    path('orders', views.AddOrderView.as_view()),

]
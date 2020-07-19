from django.urls import re_path, path
from . import views

urlpatterns =[
    path('orders/[int:order_id]/status',views.ReceiveAndRefuseView.as_view()),
]
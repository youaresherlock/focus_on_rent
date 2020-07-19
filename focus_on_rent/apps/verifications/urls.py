from django.urls import path
from . import views

urlpatterns = [
    path('imagecode/', views.ImageCodeView.as_view()),
    path('sms', views.SMSCodeView.as_view()),
]
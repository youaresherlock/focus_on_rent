from django.urls import path
from . import views

urlpatterns = [
    path('user', views.ChangeUserNameView.as_view()),
]
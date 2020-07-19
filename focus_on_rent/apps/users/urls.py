from django.urls import path

from . import views

urlpatterns = [
   path('session', views.LoginView.as_view()),
   path('users',views.RegisterView.as_view()),
]


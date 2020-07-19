from . import views
from django.urls import path

urlpatterns = [
   path('session', views.LoginView.as_view()),
   path('users', views.RegisterView.as_view()),
]


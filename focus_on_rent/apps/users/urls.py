from django.urls import path
from . import views

urlpatterns = [
   path('session', views.LoginView.as_view()),
   path('users', views.RegisterView.as_view()),
   path('user/avatar',views.UpPersonImageView.as_view()),
   path('user/auth', views.Realname.as_view()),
   path('user/name', views.ChangeUserNameView.as_view()),
   path('user', views.UserInfoView.as_view()),
]


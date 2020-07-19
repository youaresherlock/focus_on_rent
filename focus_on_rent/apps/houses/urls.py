from django.urls import re_path, path
from . import views

urlpatterns =[
    path('/houses/<int:house_id>',views.DetailView.as_view()),
]
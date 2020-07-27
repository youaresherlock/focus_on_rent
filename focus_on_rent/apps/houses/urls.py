
from django.urls import path
from . import views

urlpatterns = [
    path('houses', views.HousesView.as_view()),
    path('houses/<int:house_id>', views.DetailView.as_view()),
    path('houses/<int:house_id>/images', views.UploadHousePictureView.as_view()),
    path('houses/index', views.HousesCommandView.as_view()),
    path('areas', views.AreasView.as_view()),
]
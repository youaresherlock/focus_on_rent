from . import views
from django.urls import path

urlpatterns = [
    path('houses/<int:house_id>/images', views.UploadHousesImages.as_view()),
    path('houses', views.HousesView.as_view()),
]

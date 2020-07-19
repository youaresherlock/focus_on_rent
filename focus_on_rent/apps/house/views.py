import json
from django.views import View
from django.shortcuts import render
from focus_on_rent.utils.views import LoginRequiredJSONMixin

# Create your views here.


class UploadHousesImages(LoginRequiredJSONMixin, View):
    """上传房源图片
    /api/v1.0/houses/[int:house_id]/images
    """
    def post(self, request):
        """上传房源图片"""
        json_dict = json.loads(request.body.decode())
        house_image = json_dict.get('house_image')

























































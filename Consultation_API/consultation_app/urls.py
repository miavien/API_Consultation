from django.urls import path
from .views import *

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login-api'),
    path('block_user/', BlockUserAPIView.as_view(), name='block-user'),
    path('unblock_user/', UnblockUserAPIView.as_view(), name='unblock-user'),
]
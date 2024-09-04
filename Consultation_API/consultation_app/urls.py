from django.urls import path
from .views import *

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login-api'),
    path('block_user/', BlockUserAPIView.as_view(), name='block-user'),
    path('unblock_user/', UnblockUserAPIView.as_view(), name='unblock-user'),
    path('create_slot/', CreateSlotAPIView.as_view(), name='create-slot'),
    path('specialist_slots/', SpecialistSlotListView.as_view(), name='specialist-slots'),
    path('client_slots/', ClientSlotListView.as_view(), name='client-slots'),
    path('create_consultation/', ClientConsultationAPIView.as_view(), name='create-consultation'),
    path('specialist_consultations/', SpecialistConsultationListView.as_view(), name='specialist-consultations'),
    path('update_status/', UpdateStatusConsultationAPIView.as_view(), name='update-status'),
    path('update_slot/', SlotUpdateAPIView.as_view(), name='update-slot'),
]

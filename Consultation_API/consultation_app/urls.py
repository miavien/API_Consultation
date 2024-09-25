from django.urls import path
from django.views.decorators.cache import cache_page

from .views import *

urlpatterns = [
    path('registration/', UserRegistrationAPIView.as_view(), name='registration-api'),
    path('block_user/', BlockUserAPIView.as_view(), name='block-user'),
    path('unblock_user/', UnblockUserAPIView.as_view(), name='unblock-user'),
    path('create_slot/', CreateSlotAPIView.as_view(), name='create-slot'),
    path('specialist_slots/', cache_page(60*10)(SpecialistSlotListView.as_view()), name='specialist-slots'),
    path('client_slots/', cache_page(60*10)(ClientSlotListView.as_view()), name='client-slots'),
    path('create_consultation/', ClientConsultationAPIView.as_view(), name='create-consultation'),
    path('specialist_consultations/', cache_page(60*10)(SpecialistConsultationListView.as_view()), name='specialist-consultations'),
    path('client_consultations/', cache_page(60*10)(ClientConsultationListView.as_view()), name='client-consultations'),
    path('update_status/', UpdateStatusConsultationAPIView.as_view(), name='update-status'),
    path('update_slot/', SlotUpdateAPIView.as_view(), name='update-slot'),
    path('cancel_consultation/', CancelConsultationAPIView.as_view(), name='cancel-consultation'),
]

import pytest
from datetime import time
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from consultation_app.models import *


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_client(db):
    User = get_user_model()
    user = User.objects.create_user(
        username='client_user',
        email='client@example.com',
        password='password123'
    )
    user.role = 'Client'
    user.save()
    return user


@pytest.fixture
def user_specialist(db):
    User = get_user_model()
    user = User.objects.create_user(
        username='specialist_user',
        email='specialist@example.com',
        password='password123'
    )
    user.role = 'Specialist'
    user.save()
    return user


@pytest.fixture
def authenticated_api_client(api_client, user_client):
    api_client.force_authenticate(user=user_client)
    api_client.user = user_client
    return api_client


@pytest.fixture
def authenticated_api_specialist(api_client, user_specialist):
    api_client.force_authenticate(user=user_specialist)
    api_client.user = user_specialist
    return api_client


@pytest.fixture
def valid_slot_data():
    return {
        'date': timezone.now().date() + timezone.timedelta(days=1),
        'start_time': time(13, 0),
        'end_time': time(13, 30),
        'context': 'Some context here'
    }


@pytest.mark.django_db
class TestClientConsultationAPIView:

    @pytest.fixture
    def valid_slot(self, valid_slot_data, user_specialist):
        slot_data = valid_slot_data.copy()
        slot_data['specialist'] = user_specialist
        slot_data['id'] = 1
        return slot_data

    def test_create_consultation_success(self, authenticated_api_client, valid_slot):
        slot = Slot.objects.create(**valid_slot)
        url = reverse('create-consultation')
        request_data = {'slot_id': slot.id}
        response = authenticated_api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Запрос на консультацию успешно отправлен'
        assert 'data' in response.data
        assert 'id' in response.data['data']
        assert 'specialist_username' in response.data['data']
        assert Consultation.objects.filter(slot=slot).exists()

    def test_create_consultation_slot_already_taken(self, authenticated_api_client, valid_slot):
        User = get_user_model()
        user_client_2 = User.objects.create_user(
            username='client_user_2',
            email='client2@example.com',
            password='password123'
        )
        user_client_2.role = 'Client'
        user_client_2.save()

        slot = Slot.objects.create(**valid_slot)
        Consultation.objects.create(slot=slot, client=user_client_2, status='Accepted')
        url = reverse('create-consultation')
        request_data = {'slot_id': slot.id}
        response = authenticated_api_client.post(url, request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['message'] == 'Для данного слота уже существует подтверждённая консультация'

    def test_create_consultation_already_sent(self, user_client, authenticated_api_client, valid_slot):
        slot = Slot.objects.create(**valid_slot)
        Consultation.objects.create(slot=slot, client=user_client)
        url = reverse('create-consultation')
        request_data = {'slot_id': slot.id}
        response = authenticated_api_client.post(url, request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['message'] == 'Вы уже отправили запрос на консультацию на эту дату'

    def test_create_consultation_invalid_date(self, authenticated_api_client, valid_slot):
        invalid_data = valid_slot.copy()
        invalid_data['date'] = timezone.now().date() - timezone.timedelta(days=1)
        invalid_data['start_time'] = time(12, 0)
        invalid_data['end_time'] = time(12, 30)

        slot = Slot.objects.create(**invalid_data)
        url = reverse('create-consultation')
        request_data = {'slot_id': slot.id}
        response = authenticated_api_client.post(url, request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['message'] == 'Дата и время консультации не могут быть ранее текущего времени'

    def test_create_consultation_invalid_id(self, authenticated_api_client):
        non_existent_slot_id = 9999
        url = reverse('create-consultation')
        request_data = {'slot_id': non_existent_slot_id}
        response = authenticated_api_client.post(url, request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'slot_id' in response.data
        assert response.data['slot_id'][0] == 'Слота с таким id не существует'

    def test_create_consultation_slot_not_available(self, authenticated_api_client, valid_slot):
        slot = Slot.objects.create(**valid_slot, is_available=False)
        url = reverse('create-consultation')
        request_data = {'slot_id': slot.id}
        response = authenticated_api_client.post(url, request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['message'] == 'Вы не можете занять данный слот'

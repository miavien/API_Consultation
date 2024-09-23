import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from .models import *
from dateutil.parser import parse
from django.test import TestCase

# Create your tests here.

User = get_user_model()


@pytest.fixture
def user_specialist(db):
    User = get_user_model()
    user = User.objects.create_user(
        username='specialist_user',
        email='specialist@example.com',
        password='password123'
    )
    user.is_specialist = True
    user.save()
    return user


@pytest.mark.django_db
class TestUserRegistrationAPIView:

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def valid_user_data(self):
        return {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'role': 'Client'
        }

    @pytest.fixture
    def invalid_user_data(self):
        return {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'password123',
            'password_confirm': '123',
            'role': 'Client'
        }

    def test_registration_success(self, api_client, valid_user_data):
        url = reverse('registration-api')
        response = api_client.post(url, valid_user_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Для подтверждения регистрации на указанную почту отправлено письмо'

        user = User.objects.get(username='testuser')
        assert user.username == valid_user_data['username']
        assert user.email == valid_user_data['email']
        assert user.check_password(valid_user_data['password'])
        assert user.role == valid_user_data['role']

    def test_registration_not_success(self, api_client, invalid_user_data):
        url = reverse('registration-api')
        response = api_client.post(url, invalid_user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data
        assert response.data['non_field_errors'] == ['Пароли не совпадают']

    def test_registration_missing_fields(self, api_client):
        url = reverse('registration-api')
        response = api_client.post(url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data
        assert 'email' in response.data
        assert 'password' in response.data
        assert 'password_confirm' in response.data
        assert 'role' in response.data

    def test_registration_duplicate_username(self, api_client, valid_user_data):
        url = reverse('registration-api')
        api_client.post(url, valid_user_data)
        response = api_client.post(url, valid_user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data


@pytest.mark.django_db
class TestCreateSlotAPIView:

    @pytest.fixture
    def api_client(self, db, user_specialist):
        client = APIClient()
        client.force_authenticate(user=user_specialist)
        return client

    @pytest.fixture
    def valid_slot_data(self):
        return {
            'date': timezone.now().date() + timezone.timedelta(days=1),
            'start_time': '13:00:00',
            'end_time': '13:30:00',
            'context': 'Some context here'
        }

    def test_create_slot_success(self, api_client, valid_slot_data):
        valid_slot_data.pop('context', None)
        url = reverse('create-slot')
        response = api_client.post(url, valid_slot_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Слот успешно создан'

        slot_data = response.data['data']
        slot = Slot.objects.get(id=slot_data['id'])

        # преобразовываем строки в формат datetime
        slot_date = parse(slot_data['date']).date()
        slot_start_time = parse(slot_data['start_time']).time()
        slot_end_time = parse(slot_data['end_time']).time()

        assert slot.date == slot_date
        assert slot.start_time == slot_start_time
        assert slot.end_time == slot_end_time
        assert slot.context is None

    def test_create_slot_end_time_before_start_time(self, api_client, valid_slot_data):
        invalid_slot_data = valid_slot_data.copy()
        invalid_slot_data['end_time'] = '12:30:00'
        url = reverse('create-slot')
        response = api_client.post(url, invalid_slot_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detail' in response.data
        assert response.data['detail'][0]== 'Время окончания должно быть позже времени начала'

    def test_create_slot_invalid_date(self, api_client, valid_slot_data):
        invalid_slot_data = valid_slot_data.copy()
        invalid_slot_data['date'] = timezone.now().date() - timezone.timedelta(days=1)
        url = reverse('create-slot')
        response = api_client.post(url, invalid_slot_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detail' in response.data
        assert response.data['detail'][0]== 'Дата не может быть ранее сегодняшнего дня'

    def test_create_slot_time_overlap(self, api_client, valid_slot_data):
        url = reverse('create-slot')
        response = api_client.post(url, valid_slot_data)

        overlapping_slot_data = valid_slot_data.copy()
        overlapping_slot_data['start_time'] = '13:15:00'
        overlapping_slot_data['end_time'] = '13:45:00'
        response = api_client.post(url, overlapping_slot_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detail' in response.data
        assert response.data['detail'][0] == 'Время слота пересекается с другим слотом'

    def test_create_slot_missing_fields(self, api_client):
        url = reverse('create-slot')
        response = api_client.post(url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'date' in response.data
        assert 'start_time' in response.data
        assert 'end_time' in response.data
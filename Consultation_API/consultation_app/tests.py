import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework import status
from django.test import TestCase

# Create your tests here.

User = get_user_model()


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
        assert User.objects.filter(username='testuser').exists()
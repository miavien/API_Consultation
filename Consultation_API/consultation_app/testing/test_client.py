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


@pytest.fixture
def slot(valid_slot_data, user_specialist):
    return Slot.objects.create(
        specialist=user_specialist,
        date=valid_slot_data['date'],
        start_time=valid_slot_data['start_time'],
        end_time=valid_slot_data['end_time']
    )


@pytest.fixture
def consultation(slot, user_client):
    return Consultation.objects.create(
        slot=slot,
        client=user_client,
        status='Pending'
    )


@pytest.mark.django_db(transaction=True)
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


@pytest.mark.django_db(transaction=True)
class TestClientConsultationListView:

    def test_get_consultations_success(self, authenticated_api_client, consultation, slot):
        url = reverse('client-consultations')
        response = authenticated_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['id'] == consultation.id
        assert response.data[0]['specialist_username'] == consultation.slot.specialist.username
        assert response.data[0]['status_display'] == consultation.get_status_display()

    def test_get_consultations_empty(self, authenticated_api_client):
        url = reverse('client-consultations')
        response = authenticated_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_get_slots_non_client(self, authenticated_api_specialist):
        url = reverse('client-consultations')
        response = authenticated_api_specialist.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_consultations_with_multiple_entries(self, authenticated_api_client, consultation, slot):
        url = reverse('client-consultations')
        Consultation.objects.create(slot=slot, client=consultation.client, status='Pending')
        Consultation.objects.create(slot=slot, client=consultation.client, status='Completed')
        response = authenticated_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 1


@pytest.mark.django_db
class TestCancelConsultationAPIView:

    def test_cancel_consultation_success(self, authenticated_api_client, consultation):
        url = reverse('cancel-consultation')
        data = {
            'consultation_id': consultation.id,
            'cancel_comment': 'Some reason',
            'cancel_reason': 'Personal'
        }
        response = authenticated_api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Вы отменили консультацию'
        consultation.refresh_from_db()
        assert consultation.is_canceled is True
        assert consultation.cancel_comment == 'Some reason'
        assert consultation.cancel_reason_choice == 'Personal'

    def test_cancel_consultation_invalid_reason(self, authenticated_api_client, consultation):
        url = reverse('cancel-consultation')
        data = {
            'consultation_id': consultation.id,
            'cancel_comment': 'Some reason',
            'cancel_reason': 'Invalid status'
        }
        response = authenticated_api_client.patch(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'cancel_reason' in response.data

    def test_cancel_consultation_invalid_data(self, authenticated_api_client, consultation):
        url = reverse('cancel-consultation')
        data = {
            'consultation_id': consultation.id
        }
        response = authenticated_api_client.patch(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data
        assert response.data['non_field_errors'][
                   0] == 'Необходимо указать либо причину отмены, либо оставить комментарий'

    def test_cancel_consultation_invalid_id(self, authenticated_api_client):
        url = reverse('cancel-consultation')
        data = {
            'consultation_id': 9999,
            'cancel_comment': 'Some reason',
            'cancel_reason': 'Personal'
        }

        response = authenticated_api_client.patch(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'consultation_id' in response.data
        assert response.data['consultation_id'][
                   0] == 'Консультации с таким id не существует'

    def test_cancel_consultation_invalid_client(self, authenticated_api_client, api_client, consultation):
        User = get_user_model()
        another_user_client = User.objects.create_user(
            username='another_client_user',
            email='another_client@example.com',
            password='password123'
        )
        another_user_client.role = 'Client'
        another_user_client.save()
        api_client.force_authenticate(user=another_user_client)
        url = reverse('cancel-consultation')
        data = {
            'consultation_id': consultation.id,
            'cancel_reason': 'Personal',
        }

        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['message'] == 'Вы не можете отменить эту консультацию, так как вы не являетесь её клиентом'

    def test_cancel_consultation_not_client(self, authenticated_api_specialist, consultation):
        url = reverse('cancel-consultation')
        data = {
            'consultation_id': consultation.id,
            'cancel_comment': 'Some reason',
            'cancel_reason': 'Personal'
        }
        response = authenticated_api_specialist.patch(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cancel_consultation_already_canceled(self, authenticated_api_client, consultation):
        consultation.is_canceled = True
        consultation.save()

        url = reverse('cancel-consultation')
        data = {
            'consultation_id': consultation.id,
            'cancel_comment': 'Some reason',
            'cancel_reason': 'Personal'
        }
        response = authenticated_api_client.patch(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['message'] == 'Вы уже отменили консультацию'

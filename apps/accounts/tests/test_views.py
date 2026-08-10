import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_login_with_valid_credentials_redirects_to_dashboard(client, user):
    response = client.post(
        reverse("accounts:login"),
        {"username": "secretaria", "password": "senha-forte-123"},
    )
    assert response.status_code == 302
    assert response.url == reverse("dashboard:home")


def test_login_with_invalid_credentials_shows_error(client, user):
    response = client.post(
        reverse("accounts:login"),
        {"username": "secretaria", "password": "senha-errada"},
    )
    assert response.status_code == 200
    assert not response.wsgi_request.user.is_authenticated


def test_dashboard_requires_login(client):
    response = client.get(reverse("dashboard:home"))
    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


def test_authenticated_user_can_access_dashboard(auth_client):
    response = auth_client.get(reverse("dashboard:home"))
    assert response.status_code == 200


def test_logout_ends_session(auth_client):
    response = auth_client.post(reverse("accounts:logout"))
    assert response.status_code == 302
    response = auth_client.get(reverse("dashboard:home"))
    assert response.status_code == 302

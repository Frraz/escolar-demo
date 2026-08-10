from datetime import timedelta

import pytest
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.google_drive.exceptions import GoogleAuthExpiredError
from apps.google_drive.models import GoogleCredential
from apps.google_drive.views import OAUTH_STATE_SESSION_KEY

pytestmark = pytest.mark.django_db


def test_status_shows_disconnected_when_no_credential(auth_client):
    response = auth_client.get(reverse("google_drive:status"))
    assert response.status_code == 200
    assert response.context["is_connected"] is False


def test_status_shows_connected_with_account_email(auth_client):
    GoogleCredential.objects.create(
        account_email="escola@example.com",
        access_token="a",
        refresh_token="b",
        token_expiry=timezone.now() + timedelta(hours=1),
        scopes="",
    )
    response = auth_client.get(reverse("google_drive:status"))
    assert response.context["is_connected"] is True
    assert "escola@example.com" in response.content.decode()


@override_settings(GOOGLE_CLIENT_ID="client-id", GOOGLE_CLIENT_SECRET="client-secret")
def test_connect_redirects_to_google_and_stores_state(auth_client, mocker):
    mocker.patch(
        "apps.google_drive.views.GoogleAuthService.get_authorization_url",
        return_value=("https://accounts.google.com/o/oauth2/auth?fake=1", "state-value"),
    )
    response = auth_client.get(reverse("google_drive:connect"))
    assert response.status_code == 302
    assert response.url.startswith("https://accounts.google.com")
    assert auth_client.session[OAUTH_STATE_SESSION_KEY] == "state-value"


@override_settings(GOOGLE_CLIENT_ID="", GOOGLE_CLIENT_SECRET="")
def test_connect_without_credentials_configured_shows_error(auth_client):
    response = auth_client.get(reverse("google_drive:connect"), follow=True)
    assert "ainda não foram" in response.content.decode()


def test_callback_with_provider_error_redirects_with_message(auth_client):
    response = auth_client.get(reverse("google_drive:oauth2callback"), {"error": "access_denied"}, follow=True)
    assert "cancelada ou negada" in response.content.decode()


def test_callback_with_mismatched_state_shows_error(auth_client):
    session = auth_client.session
    session[OAUTH_STATE_SESSION_KEY] = "expected-state"
    session.save()
    response = auth_client.get(
        reverse("google_drive:oauth2callback"), {"code": "abc", "state": "wrong-state"}, follow=True
    )
    assert "Não foi possível validar" in response.content.decode()


def test_callback_success_saves_credential(auth_client, mocker):
    session = auth_client.session
    session[OAUTH_STATE_SESSION_KEY] = "matching-state"
    session.save()
    mocker.patch("apps.google_drive.views.GoogleAuthService.handle_callback")

    response = auth_client.get(
        reverse("google_drive:oauth2callback"), {"code": "abc", "state": "matching-state"}, follow=True
    )
    assert "conectado com sucesso" in response.content.decode()


def test_callback_translates_google_service_errors(auth_client, mocker):
    session = auth_client.session
    session[OAUTH_STATE_SESSION_KEY] = "matching-state"
    session.save()
    mocker.patch(
        "apps.google_drive.views.GoogleAuthService.handle_callback", side_effect=GoogleAuthExpiredError()
    )

    response = auth_client.get(
        reverse("google_drive:oauth2callback"), {"code": "abc", "state": "matching-state"}, follow=True
    )
    assert "reconecte" in response.content.decode().lower()


def test_disconnect_removes_stored_credential(auth_client):
    GoogleCredential.objects.create(
        account_email="escola@example.com",
        access_token="a",
        refresh_token="b",
        token_expiry=timezone.now() + timedelta(hours=1),
        scopes="",
    )
    response = auth_client.post(reverse("google_drive:disconnect"), follow=True)
    assert GoogleCredential.get_solo() is None
    assert "desconectado" in response.content.decode()

from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from django.utils import timezone

from apps.google_drive.exceptions import GoogleAuthExpiredError, GoogleAuthNotConfiguredError
from apps.google_drive.models import GoogleCredential
from apps.google_drive.services.auth_service import GoogleAuthService

pytestmark = pytest.mark.django_db


def _create_credential(expiry):
    return GoogleCredential.objects.create(
        account_email="escola@example.com",
        access_token="access-token-value",
        refresh_token="refresh-token-value",
        token_expiry=expiry,
        scopes="https://www.googleapis.com/auth/drive.file",
    )


def test_is_connected_false_when_no_credential_saved():
    service = GoogleAuthService()
    assert service.is_connected() is False


def test_is_connected_true_when_credential_saved():
    _create_credential(timezone.now() + timedelta(hours=1))
    service = GoogleAuthService()
    assert service.is_connected() is True


def test_get_authorized_credentials_raises_when_not_configured():
    service = GoogleAuthService()
    with pytest.raises(GoogleAuthNotConfiguredError):
        service.get_authorized_credentials()


def test_get_authorized_credentials_returns_token_without_refresh_when_valid(mocker):
    _create_credential(timezone.now() + timedelta(hours=1))
    mock_refresh = mocker.patch("google.oauth2.credentials.Credentials.refresh")

    service = GoogleAuthService()
    credentials = service.get_authorized_credentials()

    assert credentials.token == "access-token-value"
    mock_refresh.assert_not_called()


def test_get_authorized_credentials_refreshes_when_close_to_expiry(mocker):
    stored = _create_credential(timezone.now() + timedelta(seconds=30))

    def fake_refresh(self, request):
        self.token = "refreshed-access-token"
        self.expiry = timezone.now() + timedelta(hours=1)

    mocker.patch("google.oauth2.credentials.Credentials.refresh", new=fake_refresh)

    service = GoogleAuthService()
    credentials = service.get_authorized_credentials()

    assert credentials.token == "refreshed-access-token"
    stored.refresh_from_db()
    assert stored.access_token == "refreshed-access-token"


def test_get_authorized_credentials_raises_auth_expired_when_refresh_fails(mocker):
    from google.auth.exceptions import RefreshError

    _create_credential(timezone.now() - timedelta(seconds=10))
    mocker.patch("google.oauth2.credentials.Credentials.refresh", side_effect=RefreshError("invalid_grant"))

    service = GoogleAuthService()
    with pytest.raises(GoogleAuthExpiredError):
        service.get_authorized_credentials()


def test_disconnect_removes_stored_credential():
    _create_credential(timezone.now() + timedelta(hours=1))
    service = GoogleAuthService()
    service.disconnect()
    assert GoogleCredential.get_solo() is None


def test_save_credentials_persists_tokens():
    fake_credentials = MagicMock()
    fake_credentials.token = "tok"
    fake_credentials.refresh_token = "refresh"
    fake_credentials.expiry = timezone.now() + timedelta(hours=1)
    fake_credentials.scopes = ["https://www.googleapis.com/auth/drive.file"]
    fake_credentials.id_token = {"email": "cliente@escola.com"}

    service = GoogleAuthService()
    stored = service.save_credentials(fake_credentials)

    assert stored.account_email == "cliente@escola.com"
    assert stored.access_token == "tok"
    assert GoogleCredential.objects.count() == 1

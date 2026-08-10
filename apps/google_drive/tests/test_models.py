from datetime import timedelta

import pytest
from django.db import connection
from django.utils import timezone

from apps.google_drive.models import GoogleCredential

pytestmark = pytest.mark.django_db


def test_credential_tokens_are_encrypted_at_rest():
    credential = GoogleCredential.objects.create(
        account_email="escola@example.com",
        access_token="super-secret-access-token",
        refresh_token="super-secret-refresh-token",
        token_expiry=timezone.now() + timedelta(hours=1),
        scopes="drive.file",
    )

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT access_token, refresh_token FROM google_drive_googlecredential WHERE id = %s",
            [credential.pk],
        )
        raw_access_token, raw_refresh_token = cursor.fetchone()

    assert raw_access_token != "super-secret-access-token"
    assert raw_refresh_token != "super-secret-refresh-token"

    credential.refresh_from_db()
    assert credential.access_token == "super-secret-access-token"
    assert credential.refresh_token == "super-secret-refresh-token"


def test_credential_is_singleton():
    # A forma correta de gravar a credencial é sempre via update_or_create(pk=1, ...),
    # como faz GoogleAuthService.save_credentials — reconectar substitui a linha única.
    GoogleCredential.objects.update_or_create(
        pk=1,
        defaults={
            "account_email": "a@example.com",
            "access_token": "a",
            "refresh_token": "a",
            "token_expiry": timezone.now(),
            "scopes": "",
        },
    )
    GoogleCredential.objects.update_or_create(
        pk=1,
        defaults={
            "account_email": "b@example.com",
            "access_token": "b",
            "refresh_token": "b",
            "token_expiry": timezone.now(),
            "scopes": "",
        },
    )
    assert GoogleCredential.objects.count() == 1
    assert GoogleCredential.get_solo().account_email == "b@example.com"


def test_credential_is_expired_property():
    expired = GoogleCredential.objects.create(
        account_email="a@example.com",
        access_token="a",
        refresh_token="a",
        token_expiry=timezone.now() - timedelta(minutes=1),
        scopes="",
    )
    assert expired.is_expired is True

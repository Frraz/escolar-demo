from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.classes.tests.factories import ClassFactory
from apps.documents.tests.factories import DocumentFactory
from apps.google_drive.models import GoogleCredential, GoogleSheet
from apps.students.tests.factories import StudentFactory

pytestmark = pytest.mark.django_db


def test_dashboard_requires_login(client):
    response = client.get(reverse("dashboard:home"))
    assert response.status_code == 302


def test_dashboard_renders_with_empty_database(auth_client):
    response = auth_client.get(reverse("dashboard:home"))
    assert response.status_code == 200
    assert response.context["students_count"] == 0
    assert response.context["documents_count"] == 0
    assert "Nenhum arquivo enviado ainda" in response.content.decode()


def test_dashboard_counts_match_fixtures(auth_client):
    students = StudentFactory.create_batch(3)
    ClassFactory.create_batch(2)
    [DocumentFactory(student=students[0], size=1024 * 1024) for _ in range(4)]

    response = auth_client.get(reverse("dashboard:home"))

    assert response.context["students_count"] == 3
    assert response.context["classes_count"] == 2
    assert response.context["documents_count"] == 4
    assert response.context["total_size_display"] == "4.0 MB"


def test_dashboard_shows_drive_disconnected_by_default(auth_client):
    response = auth_client.get(reverse("dashboard:home"))
    assert response.context["is_drive_connected"] is False
    assert "Desconectado" in response.content.decode()


def test_dashboard_shows_drive_connected(auth_client):
    GoogleCredential.objects.create(
        account_email="escola@example.com",
        access_token="a",
        refresh_token="b",
        token_expiry=timezone.now() + timedelta(hours=1),
        scopes="",
    )
    response = auth_client.get(reverse("dashboard:home"))
    assert response.context["is_drive_connected"] is True
    assert "Conectado" in response.content.decode()


def test_dashboard_counts_sheets(auth_client):
    school_class = ClassFactory()
    GoogleSheet.objects.create(
        school_class=school_class,
        google_sheet_id="sheet-1",
        google_drive_url="https://docs.google.com/spreadsheets/d/sheet-1",
        google_drive_folder_id="folder-1",
    )
    response = auth_client.get(reverse("dashboard:home"))
    assert response.context["sheets_count"] == 1


def test_dashboard_shows_recent_documents(auth_client):
    document = DocumentFactory(name="rg.pdf")
    response = auth_client.get(reverse("dashboard:home"))
    assert "rg.pdf" in response.content.decode()
    assert document in response.context["recent_documents"]

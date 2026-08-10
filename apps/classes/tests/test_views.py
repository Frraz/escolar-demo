import pytest
from django.urls import reverse

from apps.classes.models import Class
from apps.classes.tests.factories import ClassFactory

pytestmark = pytest.mark.django_db


def test_class_list_requires_login(client):
    response = client.get(reverse("classes:list"))
    assert response.status_code == 302


def test_class_list_shows_existing_classes(auth_client):
    ClassFactory(name="1º Ano A")
    response = auth_client.get(reverse("classes:list"))
    assert response.status_code == 200
    assert "1º Ano A" in response.content.decode()


def test_create_class(auth_client):
    response = auth_client.post(
        reverse("classes:create"),
        {"name": "2º Ano B", "school_year": 2026, "shift": "afternoon", "is_active": "on"},
    )
    assert response.status_code == 302
    assert Class.objects.filter(name="2º Ano B", school_year=2026).exists()


def test_create_class_with_duplicate_name_and_year_shows_error(auth_client):
    ClassFactory(name="3º Ano C", school_year=2026)
    response = auth_client.post(
        reverse("classes:create"),
        {"name": "3º Ano C", "school_year": 2026, "shift": "morning", "is_active": "on"},
    )
    assert response.status_code == 200
    assert Class.objects.filter(name="3º Ano C", school_year=2026).count() == 1


def test_update_class(auth_client):
    school_class = ClassFactory(name="4º Ano D")
    response = auth_client.post(
        reverse("classes:update", args=[school_class.pk]),
        {"name": "4º Ano D+", "school_year": school_class.school_year, "shift": school_class.shift, "is_active": "on"},
    )
    assert response.status_code == 302
    school_class.refresh_from_db()
    assert school_class.name == "4º Ano D+"


def test_delete_class(auth_client):
    school_class = ClassFactory()
    response = auth_client.post(reverse("classes:delete", args=[school_class.pk]))
    assert response.status_code == 302
    assert not Class.objects.filter(pk=school_class.pk).exists()

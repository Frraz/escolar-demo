import pytest
from django.urls import reverse

from apps.classes.tests.factories import ClassFactory
from apps.students.models import Student
from apps.students.tests.factories import StudentFactory

pytestmark = pytest.mark.django_db


def test_student_list_requires_login(client):
    response = client.get(reverse("students:list"))
    assert response.status_code == 302


def test_student_list_shows_existing_students(auth_client):
    StudentFactory(full_name="João Silva")
    response = auth_client.get(reverse("students:list"))
    assert response.status_code == 200
    assert "João Silva" in response.content.decode()


def test_student_list_search_filters_by_name(auth_client):
    StudentFactory(full_name="João Silva")
    StudentFactory(full_name="Maria Souza")
    response = auth_client.get(reverse("students:list"), {"q": "João"})
    content = response.content.decode()
    assert "João Silva" in content
    assert "Maria Souza" not in content


def test_create_student_sets_created_by(auth_client, user):
    school_class = ClassFactory()
    response = auth_client.post(
        reverse("students:create"),
        {
            "full_name": "Pedro Santos",
            "registration_number": "010",
            "email": "",
            "phone": "",
            "school_class": school_class.pk,
            "is_active": "on",
        },
    )
    assert response.status_code == 302
    student = Student.objects.get(registration_number="010")
    assert student.created_by == user
    assert student.school_class == school_class


def test_create_student_with_duplicate_registration_number_shows_error(auth_client):
    StudentFactory(registration_number="010")
    response = auth_client.post(
        reverse("students:create"),
        {"full_name": "Outro Aluno", "registration_number": "010", "email": "", "phone": "", "is_active": "on"},
    )
    assert response.status_code == 200
    assert Student.objects.filter(registration_number="010").count() == 1


def test_student_detail_page(auth_client):
    student = StudentFactory(full_name="Ana Lima")
    response = auth_client.get(reverse("students:detail", args=[student.pk]))
    assert response.status_code == 200
    assert "Ana Lima" in response.content.decode()


def test_delete_student(auth_client):
    student = StudentFactory()
    response = auth_client.post(reverse("students:delete", args=[student.pk]))
    assert response.status_code == 302
    assert not Student.objects.filter(pk=student.pk).exists()

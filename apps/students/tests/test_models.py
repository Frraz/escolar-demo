import pytest
from django.db import IntegrityError

from apps.students.tests.factories import StudentFactory

pytestmark = pytest.mark.django_db


def test_student_str_includes_name_and_registration():
    student = StudentFactory(full_name="João Silva", registration_number="001")
    assert str(student) == "João Silva - 001"


def test_registration_number_must_be_unique():
    StudentFactory(registration_number="001")
    with pytest.raises(IntegrityError):
        StudentFactory(registration_number="001")


def test_drive_folder_name_combines_name_and_registration():
    student = StudentFactory(full_name="Maria Silva", registration_number="002")
    assert student.drive_folder_name == "Maria Silva - 002"

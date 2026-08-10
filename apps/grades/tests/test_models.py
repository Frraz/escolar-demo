import pytest
from django.db import IntegrityError

from apps.grades.tests.factories import GradeFactory, SubjectFactory

pytestmark = pytest.mark.django_db


def test_grade_unique_per_student_subject_class_term():
    grade = GradeFactory()
    with pytest.raises(IntegrityError):
        GradeFactory(
            student=grade.student, subject=grade.subject, school_class=grade.school_class, term=grade.term
        )


def test_subject_str_is_name():
    subject = SubjectFactory(name="Educação Física")
    assert str(subject) == "Educação Física"

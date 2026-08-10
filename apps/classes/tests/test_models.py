import pytest
from django.db import IntegrityError

from apps.classes.tests.factories import ClassFactory

pytestmark = pytest.mark.django_db


def test_class_str_includes_name_and_year():
    school_class = ClassFactory(name="1º Ano A", school_year=2026)
    assert str(school_class) == "1º Ano A (2026)"


def test_class_name_and_year_must_be_unique_together():
    ClassFactory(name="1º Ano A", school_year=2026)
    with pytest.raises(IntegrityError):
        ClassFactory(name="1º Ano A", school_year=2026)

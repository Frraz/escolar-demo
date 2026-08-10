import factory

from apps.classes.tests.factories import ClassFactory
from apps.grades.models import Grade, Subject
from apps.students.tests.factories import StudentFactory


class SubjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subject
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Matéria {n}")


class GradeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Grade

    student = factory.SubFactory(StudentFactory)
    subject = factory.SubFactory(SubjectFactory)
    school_class = factory.SubFactory(ClassFactory)
    term = "1"
    value = 8.5

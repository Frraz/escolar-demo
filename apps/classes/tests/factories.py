import factory

from apps.classes.models import Class, Shift


class ClassFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Class

    name = factory.Sequence(lambda n: f"Turma {n}")
    school_year = 2026
    shift = Shift.MORNING
    is_active = True

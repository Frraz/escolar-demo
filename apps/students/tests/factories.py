import factory

from apps.students.models import Student


class StudentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Student

    full_name = factory.Sequence(lambda n: f"Aluno de Teste {n}")
    registration_number = factory.Sequence(lambda n: f"{n:04d}")
    email = factory.LazyAttribute(lambda o: f"{o.full_name.lower().replace(' ', '.')}@escola.test")
    is_active = True

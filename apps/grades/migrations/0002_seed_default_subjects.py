from django.db import migrations

DEFAULT_SUBJECTS = ["Matemática", "Português", "História", "Geografia", "Ciências"]


def create_default_subjects(apps, schema_editor):
    Subject = apps.get_model("grades", "Subject")
    for name in DEFAULT_SUBJECTS:
        Subject.objects.get_or_create(name=name)


def remove_default_subjects(apps, schema_editor):
    Subject = apps.get_model("grades", "Subject")
    Subject.objects.filter(name__in=DEFAULT_SUBJECTS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("grades", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_subjects, remove_default_subjects),
    ]

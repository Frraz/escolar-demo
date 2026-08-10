from django.apps import AppConfig


class StudentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.students"
    verbose_name = "Alunos"

    def ready(self):
        from apps.students import signals  # noqa: F401

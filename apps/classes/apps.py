from django.apps import AppConfig


class ClassesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.classes"
    verbose_name = "Turmas"

    def ready(self):
        from apps.classes import signals  # noqa: F401

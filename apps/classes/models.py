from django.db import models


class Shift(models.TextChoices):
    MORNING = "morning", "Manhã"
    AFTERNOON = "afternoon", "Tarde"
    EVENING = "evening", "Noite"


class Class(models.Model):
    name = models.CharField("Nome da turma", max_length=100)
    school_year = models.PositiveIntegerField("Ano letivo")
    shift = models.CharField("Turno", max_length=20, choices=Shift.choices, default=Shift.MORNING)
    is_active = models.BooleanField("Ativa", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Turma"
        verbose_name_plural = "Turmas"
        ordering = ["-school_year", "name"]
        constraints = [
            models.UniqueConstraint(fields=["name", "school_year"], name="uniq_class_name_year"),
        ]

    def __str__(self):
        return f"{self.name} ({self.school_year})"

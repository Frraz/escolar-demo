from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Subject(models.Model):
    name = models.CharField("Matéria", max_length=100, unique=True)

    class Meta:
        verbose_name = "Matéria"
        verbose_name_plural = "Matérias"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Grade(models.Model):
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="grades")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="grades")
    school_class = models.ForeignKey("classes.Class", on_delete=models.CASCADE, related_name="grades")
    term = models.CharField("Bimestre", max_length=20, default="1")
    value = models.DecimalField(
        "Nota", max_digits=4, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("10.0"))],
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Notas"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "subject", "school_class", "term"], name="uniq_grade_per_student_subject_term"
            ),
        ]

    def __str__(self):
        return f"{self.student} - {self.subject}: {self.value}"

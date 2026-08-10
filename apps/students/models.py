from django.conf import settings
from django.db import models


class Student(models.Model):
    full_name = models.CharField("Nome completo", max_length=200)
    birth_date = models.DateField("Data de nascimento", null=True, blank=True)
    registration_number = models.CharField("Matrícula", max_length=30, unique=True)
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Telefone", max_length=20, blank=True)
    school_class = models.ForeignKey(
        "classes.Class",
        verbose_name="Turma",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )
    is_active = models.BooleanField("Ativo", default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField("Data de cadastro", auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} - {self.registration_number}"

    @property
    def drive_folder_name(self):
        return f"{self.full_name} - {self.registration_number}"

from django.conf import settings
from django.db import models
from django.utils import timezone

from .fields import EncryptedTextField


class FolderKind(models.TextChoices):
    STUDENTS_ROOT = "students_root", "Alunos"
    STUDENT = "student", "Pasta do Aluno"
    STUDENT_DOCUMENTOS = "student_documentos", "Documentos do Aluno"
    STUDENT_FOTOS = "student_fotos", "Fotos do Aluno"
    STUDENT_OUTROS = "student_outros", "Outros do Aluno"
    CLASSES_ROOT = "classes_root", "Turmas"
    CLASS = "class", "Pasta da Turma"
    REPORTS = "reports", "Relatórios"


class GoogleDriveFolder(models.Model):
    """Cache/índice de idempotência: mapeia uma pasta lógica do sistema para o
    folder_id correspondente no Google Drive, evitando recriar pastas."""

    kind = models.CharField("Tipo", max_length=30, choices=FolderKind.choices)
    name = models.CharField("Nome no Drive", max_length=255)
    google_drive_folder_id = models.CharField(max_length=128, unique=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE, null=True, blank=True, related_name="drive_folders"
    )
    school_class = models.ForeignKey(
        "classes.Class", on_delete=models.CASCADE, null=True, blank=True, related_name="drive_folders"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pasta do Google Drive"
        verbose_name_plural = "Pastas do Google Drive"
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "student"],
                name="uniq_student_folder_kind",
                condition=models.Q(student__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["kind", "school_class"],
                name="uniq_class_folder_kind",
                condition=models.Q(school_class__isnull=False),
            ),
        ]

    def __str__(self):
        return f"{self.get_kind_display()}: {self.name}"

    @property
    def drive_url(self):
        return f"https://drive.google.com/drive/folders/{self.google_drive_folder_id}"


class GoogleSheet(models.Model):
    school_class = models.OneToOneField(
        "classes.Class", on_delete=models.CASCADE, related_name="grade_sheet"
    )
    google_sheet_id = models.CharField(max_length=128, unique=True)
    google_drive_url = models.URLField(max_length=500)
    google_drive_folder_id = models.CharField(max_length=128)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Planilha de notas"
        verbose_name_plural = "Planilhas de notas"

    def __str__(self):
        return f"Notas - {self.school_class}"

    def mark_synced(self):
        self.last_synced_at = timezone.now()
        self.save(update_fields=["last_synced_at"])


class GoogleCredential(models.Model):
    """Credencial OAuth da conta Google do cliente. Singleton lógico: o MVP
    assume uma única conta Google Drive conectada por instalação."""

    account_email = models.EmailField()
    access_token = EncryptedTextField()
    refresh_token = EncryptedTextField()
    token_expiry = models.DateTimeField()
    scopes = models.TextField(help_text="Lista de scopes concedidos, separados por espaço")
    connected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    connected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Credencial do Google"
        verbose_name_plural = "Credenciais do Google"
        constraints = [
            models.CheckConstraint(condition=models.Q(pk=1), name="single_google_credential_row"),
        ]

    def __str__(self):
        return f"Google Drive conectado como {self.account_email}"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        return cls.objects.filter(pk=1).first()

    @property
    def is_expired(self):
        return timezone.now() >= self.token_expiry

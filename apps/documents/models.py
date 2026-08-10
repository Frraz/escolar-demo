from django.conf import settings
from django.db import models


class DocumentCategory(models.TextChoices):
    DOCUMENTOS = "documentos", "Documentos"
    FOTOS = "fotos", "Fotos"
    OUTROS = "outros", "Outros"


class Document(models.Model):
    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE, related_name="documents"
    )
    name = models.CharField("Nome", max_length=255)
    category = models.CharField(
        "Categoria", max_length=20, choices=DocumentCategory.choices, default=DocumentCategory.OUTROS
    )
    mime_type = models.CharField(max_length=127)
    size = models.PositiveBigIntegerField(help_text="Tamanho em bytes")

    # A identidade real do arquivo é o Google Drive — o nome nunca é usado como
    # identificador, apenas como rótulo de exibição.
    google_drive_file_id = models.CharField(max_length=128, unique=True)
    google_drive_folder_id = models.CharField(max_length=128)
    google_drive_url = models.URLField(max_length=500)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_documents"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["student", "category"])]

    def __str__(self):
        return self.name

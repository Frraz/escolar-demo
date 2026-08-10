import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.google_drive.exceptions import GoogleServiceError
from apps.google_drive.services.folder_service import FolderStructureService

from .models import Student

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Student)
def create_drive_folders_for_student(sender, instance, created, **kwargs):
    if not created:
        return

    def _create_folders():
        try:
            FolderStructureService().ensure_student_folders(instance)
        except GoogleServiceError:
            logger.error(
                "Não foi possível criar a estrutura de pastas do aluno no Google Drive",
                exc_info=True, extra={"student_id": instance.id},
            )

    transaction.on_commit(_create_folders)

import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.google_drive.exceptions import GoogleServiceError
from apps.google_drive.services.folder_service import FolderStructureService

from .models import Class

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Class)
def create_drive_folder_for_class(sender, instance, created, **kwargs):
    if not created:
        return

    def _create_folder():
        try:
            FolderStructureService().ensure_class_folder(instance)
        except GoogleServiceError:
            logger.error(
                "Não foi possível criar a pasta da turma no Google Drive",
                exc_info=True, extra={"class_id": instance.id},
            )

    transaction.on_commit(_create_folder)

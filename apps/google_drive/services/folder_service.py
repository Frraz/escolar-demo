from django.conf import settings

from apps.google_drive.models import FolderKind, GoogleDriveFolder
from apps.google_drive.services.drive_service import GoogleDriveService


class FolderStructureService:
    """Garante a estrutura de pastas do sistema dentro do Google Drive,
    de forma idempotente: usa GoogleDriveFolder como cache local e, na
    ausência de cache, delega a busca/criação ao GoogleDriveService."""

    def __init__(self, drive_service: GoogleDriveService | None = None):
        self.drive = drive_service or GoogleDriveService()

    def _get_or_create(self, *, name, parent_id, kind, student=None, school_class=None) -> str:
        lookup = {"kind": kind, "student": student, "school_class": school_class}
        cached = GoogleDriveFolder.objects.filter(**lookup).first()
        if cached:
            return cached.google_drive_folder_id

        folder_id = self.drive.get_or_create_folder(name=name, parent_id=parent_id)
        GoogleDriveFolder.objects.create(
            kind=kind, name=name, google_drive_folder_id=folder_id, student=student, school_class=school_class
        )
        return folder_id

    def ensure_students_root(self) -> str:
        return self._get_or_create(
            name=settings.GOOGLE_DRIVE_STUDENTS_FOLDER_NAME,
            parent_id=settings.GOOGLE_DRIVE_ROOT_FOLDER_ID,
            kind=FolderKind.STUDENTS_ROOT,
        )

    def ensure_classes_root(self) -> str:
        return self._get_or_create(
            name=settings.GOOGLE_DRIVE_CLASSES_FOLDER_NAME,
            parent_id=settings.GOOGLE_DRIVE_ROOT_FOLDER_ID,
            kind=FolderKind.CLASSES_ROOT,
        )

    def ensure_reports_folder(self) -> str:
        return self._get_or_create(
            name=settings.GOOGLE_DRIVE_REPORTS_FOLDER_NAME,
            parent_id=settings.GOOGLE_DRIVE_ROOT_FOLDER_ID,
            kind=FolderKind.REPORTS,
        )

    def ensure_student_folders(self, student) -> dict[str, str]:
        students_root = self.ensure_students_root()
        student_folder = self._get_or_create(
            name=student.drive_folder_name, parent_id=students_root, kind=FolderKind.STUDENT, student=student
        )
        return {
            "documentos": self._get_or_create(
                name="Documentos", parent_id=student_folder, kind=FolderKind.STUDENT_DOCUMENTOS, student=student
            ),
            "fotos": self._get_or_create(
                name="Fotos", parent_id=student_folder, kind=FolderKind.STUDENT_FOTOS, student=student
            ),
            "outros": self._get_or_create(
                name="Outros", parent_id=student_folder, kind=FolderKind.STUDENT_OUTROS, student=student
            ),
        }

    def ensure_class_folder(self, school_class) -> str:
        classes_root = self.ensure_classes_root()
        return self._get_or_create(
            name=school_class.name, parent_id=classes_root, kind=FolderKind.CLASS, school_class=school_class
        )

from unittest.mock import MagicMock

import pytest

from apps.google_drive.models import GoogleDriveFolder
from apps.google_drive.services.drive_service import GoogleDriveService
from apps.google_drive.services.folder_service import FolderStructureService
from apps.students.tests.factories import StudentFactory
from apps.classes.tests.factories import ClassFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_drive():
    mock = MagicMock(spec=GoogleDriveService)
    mock.get_or_create_folder.side_effect = lambda name, parent_id: f"id-for-{name}-under-{parent_id}"
    return mock


def test_ensure_student_folders_creates_four_folders(mock_drive):
    student = StudentFactory(full_name="João Silva", registration_number="001")
    service = FolderStructureService(drive_service=mock_drive)

    folders = service.ensure_student_folders(student)

    assert set(folders.keys()) == {"documentos", "fotos", "outros"}
    assert GoogleDriveFolder.objects.filter(student=student).count() == 4  # pasta do aluno + 3 subpastas


def test_ensure_student_folders_is_idempotent(mock_drive):
    student = StudentFactory()
    service = FolderStructureService(drive_service=mock_drive)

    service.ensure_student_folders(student)
    call_count_after_first = mock_drive.get_or_create_folder.call_count
    service.ensure_student_folders(student)
    call_count_after_second = mock_drive.get_or_create_folder.call_count

    assert call_count_after_second == call_count_after_first
    assert GoogleDriveFolder.objects.filter(student=student).count() == 4


def test_ensure_class_folder_creates_folder_under_classes_root(mock_drive):
    school_class = ClassFactory(name="1º Ano A")
    service = FolderStructureService(drive_service=mock_drive)

    folder_id = service.ensure_class_folder(school_class)

    assert folder_id
    assert GoogleDriveFolder.objects.filter(school_class=school_class).exists()


def test_ensure_class_folder_does_not_duplicate_on_second_call(mock_drive):
    school_class = ClassFactory()
    service = FolderStructureService(drive_service=mock_drive)

    service.ensure_class_folder(school_class)
    service.ensure_class_folder(school_class)

    assert GoogleDriveFolder.objects.filter(school_class=school_class).count() == 1

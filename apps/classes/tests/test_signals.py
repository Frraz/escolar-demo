import pytest

from apps.classes.tests.factories import ClassFactory
from apps.google_drive.exceptions import GoogleServiceUnavailableError

pytestmark = pytest.mark.django_db


def test_creating_class_triggers_drive_folder_creation(mocker, django_capture_on_commit_callbacks):
    mock_ensure = mocker.patch(
        "apps.classes.signals.FolderStructureService.ensure_class_folder", return_value="folder-1"
    )

    with django_capture_on_commit_callbacks(execute=True):
        school_class = ClassFactory()

    mock_ensure.assert_called_once_with(school_class)


def test_drive_failure_during_class_creation_does_not_raise(mocker, django_capture_on_commit_callbacks):
    mocker.patch(
        "apps.classes.signals.FolderStructureService.ensure_class_folder",
        side_effect=GoogleServiceUnavailableError(),
    )

    with django_capture_on_commit_callbacks(execute=True):
        school_class = ClassFactory()

    assert school_class.pk is not None

import pytest

from apps.google_drive.exceptions import GoogleServiceUnavailableError
from apps.students.tests.factories import StudentFactory

pytestmark = pytest.mark.django_db


def test_creating_student_triggers_drive_folder_creation(mocker, django_capture_on_commit_callbacks):
    mock_ensure = mocker.patch(
        "apps.students.signals.FolderStructureService.ensure_student_folders",
        return_value={"documentos": "d", "fotos": "f", "outros": "o"},
    )

    with django_capture_on_commit_callbacks(execute=True):
        student = StudentFactory()

    mock_ensure.assert_called_once_with(student)


def test_drive_failure_during_student_creation_does_not_raise(mocker, django_capture_on_commit_callbacks):
    mocker.patch(
        "apps.students.signals.FolderStructureService.ensure_student_folders",
        side_effect=GoogleServiceUnavailableError(),
    )

    with django_capture_on_commit_callbacks(execute=True):
        student = StudentFactory()

    assert student.pk is not None


def test_unexpected_error_during_student_creation_does_not_raise(mocker, django_capture_on_commit_callbacks):
    # Regressão: um bug do tipo "TypeError: can't compare offset-naive and
    # offset-aware datetimes" já escapou do except GoogleServiceError em
    # produção e derrubou o cadastro do aluno com 500. Qualquer exceção
    # inesperada aqui não pode impedir o aluno de ser salvo.
    mocker.patch(
        "apps.students.signals.FolderStructureService.ensure_student_folders",
        side_effect=TypeError("can't compare offset-naive and offset-aware datetimes"),
    )

    with django_capture_on_commit_callbacks(execute=True):
        student = StudentFactory()

    assert student.pk is not None


def test_updating_student_does_not_trigger_folder_creation_again(mocker, django_capture_on_commit_callbacks):
    mock_ensure = mocker.patch(
        "apps.students.signals.FolderStructureService.ensure_student_folders",
        return_value={"documentos": "d", "fotos": "f", "outros": "o"},
    )

    with django_capture_on_commit_callbacks(execute=True):
        student = StudentFactory()
    mock_ensure.reset_mock()

    with django_capture_on_commit_callbacks(execute=True):
        student.full_name = "Nome Atualizado"
        student.save()

    mock_ensure.assert_not_called()

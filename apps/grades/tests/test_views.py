import pytest
from django.urls import reverse

from apps.classes.tests.factories import ClassFactory
from apps.google_drive.exceptions import GoogleServiceUnavailableError
from apps.google_drive.models import GoogleSheet
from apps.grades.models import Grade
from apps.grades.tests.factories import GradeFactory, SubjectFactory
from apps.students.tests.factories import StudentFactory

pytestmark = pytest.mark.django_db


def test_class_grades_matrix_shows_students_and_subjects(auth_client):
    school_class = ClassFactory()
    student = StudentFactory(full_name="João Silva", school_class=school_class)
    subject = SubjectFactory(name="Matemática")
    GradeFactory(student=student, subject=subject, school_class=school_class, value=8.5)

    response = auth_client.get(reverse("grades:class_grades", args=[school_class.pk]))

    content = response.content.decode()
    assert response.status_code == 200
    assert "João Silva" in content
    assert "Matemática" in content
    # Django formata Decimal com vírgula decimal para o locale pt-br.
    assert "8,5" in content


def test_update_grade_creates_new_grade(auth_client, user):
    school_class = ClassFactory()
    student = StudentFactory(school_class=school_class)
    subject = SubjectFactory()

    response = auth_client.post(
        reverse("grades:update_grade", args=[school_class.pk]),
        {"student_id": student.pk, "subject_id": subject.pk, "value": "9.5"},
    )

    assert response.status_code == 200
    grade = Grade.objects.get(student=student, subject=subject, school_class=school_class)
    assert grade.value == 9.5
    assert grade.updated_by == user


def test_update_grade_updates_existing_grade(auth_client):
    grade = GradeFactory(value=6.0)

    auth_client.post(
        reverse("grades:update_grade", args=[grade.school_class.pk]),
        {"student_id": grade.student.pk, "subject_id": grade.subject.pk, "value": "7.0"},
    )

    grade.refresh_from_db()
    assert grade.value == 7.0


def test_update_grade_rejects_out_of_range_value(auth_client):
    school_class = ClassFactory()
    student = StudentFactory(school_class=school_class)
    subject = SubjectFactory()

    response = auth_client.post(
        reverse("grades:update_grade", args=[school_class.pk]),
        {"student_id": student.pk, "subject_id": subject.pk, "value": "15"},
    )

    assert response.status_code == 200
    assert "inválida" in response.content.decode()
    assert not Grade.objects.filter(student=student, subject=subject).exists()


def test_update_grade_clears_value_when_empty(auth_client):
    grade = GradeFactory(value=6.0)

    auth_client.post(
        reverse("grades:update_grade", args=[grade.school_class.pk]),
        {"student_id": grade.student.pk, "subject_id": grade.subject.pk, "value": ""},
    )

    grade.refresh_from_db()
    assert grade.value is None


def test_sync_creates_sheet_and_moves_it_to_class_folder(auth_client, mocker):
    school_class = ClassFactory(name="1º Ano A")
    StudentFactory(school_class=school_class)
    mocker.patch(
        "apps.grades.views.FolderStructureService.ensure_class_folder", return_value="class-folder-id"
    )
    mocker.patch(
        "apps.grades.views.GoogleSheetsService.create_spreadsheet",
        return_value={"spreadsheetId": "sheet-1", "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/sheet-1"},
    )
    mock_move = mocker.patch("apps.grades.views.GoogleDriveService.move_file")
    mock_update = mocker.patch("apps.grades.views.GoogleSheetsService.update_values")

    response = auth_client.post(reverse("grades:sync_sheet", args=[school_class.pk]), follow=True)

    assert response.status_code == 200
    sheet = GoogleSheet.objects.get(school_class=school_class)
    assert sheet.google_sheet_id == "sheet-1"
    mock_move.assert_called_once_with("sheet-1", new_parent_id="class-folder-id")
    mock_update.assert_called_once()
    assert "sincronizadas" in response.content.decode()


def test_sync_reuses_existing_sheet_without_creating_duplicate(auth_client, mocker):
    school_class = ClassFactory()
    GoogleSheet.objects.create(
        school_class=school_class,
        google_sheet_id="existing-sheet",
        google_drive_url="https://docs.google.com/spreadsheets/d/existing-sheet",
        google_drive_folder_id="class-folder-id",
    )
    mocker.patch("apps.grades.views.FolderStructureService.ensure_class_folder", return_value="class-folder-id")
    mock_create = mocker.patch("apps.grades.views.GoogleSheetsService.create_spreadsheet")
    mock_update = mocker.patch("apps.grades.views.GoogleSheetsService.update_values")

    auth_client.post(reverse("grades:sync_sheet", args=[school_class.pk]))

    mock_create.assert_not_called()
    mock_update.assert_called_once()
    assert GoogleSheet.objects.filter(school_class=school_class).count() == 1


def test_sync_shows_friendly_error_on_drive_failure(auth_client, mocker):
    school_class = ClassFactory()
    mocker.patch(
        "apps.grades.views.FolderStructureService.ensure_class_folder",
        side_effect=GoogleServiceUnavailableError(),
    )

    response = auth_client.post(reverse("grades:sync_sheet", args=[school_class.pk]), follow=True)

    assert "indisponível" in response.content.decode().lower()
    assert not GoogleSheet.objects.filter(school_class=school_class).exists()

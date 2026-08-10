import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.documents.models import Document
from apps.documents.tests.factories import DocumentFactory
from apps.google_drive.exceptions import GoogleUploadFailedError
from apps.students.tests.factories import StudentFactory

pytestmark = pytest.mark.django_db

PDF_BYTES = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n"


def _pdf_upload(name="documento.pdf"):
    return SimpleUploadedFile(name, PDF_BYTES, content_type="application/pdf")


def test_upload_requires_login(client):
    student = StudentFactory()
    response = client.post(reverse("documents:upload", args=[student.pk]), {"file": _pdf_upload()})
    assert response.status_code == 302


def test_upload_success_creates_document(auth_client, mocker):
    student = StudentFactory()
    mocker.patch(
        "apps.documents.views.FolderStructureService.ensure_student_folders",
        return_value={"documentos": "folder-docs", "fotos": "folder-fotos", "outros": "folder-outros"},
    )
    mocker.patch(
        "apps.documents.views.GoogleDriveService.upload_file",
        return_value={"id": "drive-file-1", "webViewLink": "https://drive.google.com/file/d/drive-file-1/view"},
    )

    response = auth_client.post(
        reverse("documents:upload", args=[student.pk]),
        {"file": _pdf_upload(), "category": "documentos"},
    )

    assert response.status_code == 200
    document = Document.objects.get(student=student)
    assert document.google_drive_file_id == "drive-file-1"
    assert document.google_drive_folder_id == "folder-docs"
    assert "documento.pdf" in response.content.decode()


def test_upload_fails_when_drive_raises_error_and_creates_no_document(auth_client, mocker):
    student = StudentFactory()
    mocker.patch(
        "apps.documents.views.FolderStructureService.ensure_student_folders",
        return_value={"documentos": "folder-docs", "fotos": "folder-fotos", "outros": "folder-outros"},
    )
    mocker.patch(
        "apps.documents.views.GoogleDriveService.upload_file",
        side_effect=GoogleUploadFailedError(),
    )

    response = auth_client.post(
        reverse("documents:upload", args=[student.pk]),
        {"file": _pdf_upload(), "category": "documentos"},
    )

    assert response.status_code == 200
    assert not Document.objects.filter(student=student).exists()
    assert "Não foi possível enviar o arquivo" in response.content.decode()


def test_upload_with_invalid_extension_shows_form_error_without_calling_drive(auth_client, mocker):
    student = StudentFactory()
    mock_upload = mocker.patch("apps.documents.views.GoogleDriveService.upload_file")

    response = auth_client.post(
        reverse("documents:upload", args=[student.pk]),
        {"file": SimpleUploadedFile("virus.exe", b"MZ\x90\x00"), "category": "documentos"},
    )

    assert response.status_code == 200
    mock_upload.assert_not_called()
    assert not Document.objects.filter(student=student).exists()


def test_upload_cleans_up_orphan_file_when_database_save_fails(auth_client, mocker):
    student = StudentFactory()
    mocker.patch(
        "apps.documents.views.FolderStructureService.ensure_student_folders",
        return_value={"documentos": "folder-docs", "fotos": "folder-fotos", "outros": "folder-outros"},
    )
    mocker.patch(
        "apps.documents.views.GoogleDriveService.upload_file",
        return_value={"id": "drive-file-orphan", "webViewLink": "https://drive.google.com/file/d/drive-file-orphan/view"},
    )
    mock_delete = mocker.patch("apps.documents.views.GoogleDriveService.delete_file")
    mocker.patch("apps.documents.views.Document.objects.create", side_effect=Exception("db down"))

    response = auth_client.post(
        reverse("documents:upload", args=[student.pk]),
        {"file": _pdf_upload(), "category": "documentos"},
    )

    assert response.status_code == 200
    mock_delete.assert_called_once_with("drive-file-orphan")
    assert not Document.objects.filter(student=student).exists()


def test_download_redirects_to_drive_url(auth_client):
    document = DocumentFactory(google_drive_url="https://drive.google.com/file/d/abc/view")
    response = auth_client.get(reverse("documents:download", args=[document.pk]))
    assert response.status_code == 302
    assert response.url == "https://drive.google.com/file/d/abc/view"


def test_delete_removes_document_when_drive_succeeds(auth_client, mocker):
    document = DocumentFactory()
    mock_delete = mocker.patch("apps.documents.views.GoogleDriveService.delete_file")

    response = auth_client.post(reverse("documents:delete", args=[document.pk]))

    assert response.status_code == 200
    mock_delete.assert_called_once_with(document.google_drive_file_id)
    assert not Document.objects.filter(pk=document.pk).exists()


def test_delete_keeps_document_when_drive_fails(auth_client, mocker):
    document = DocumentFactory()
    mocker.patch("apps.documents.views.GoogleDriveService.delete_file", side_effect=GoogleUploadFailedError())

    response = auth_client.post(reverse("documents:delete", args=[document.pk]))

    assert response.status_code == 200
    assert Document.objects.filter(pk=document.pk).exists()


def test_document_global_list_shows_documents(auth_client):
    DocumentFactory(name="rg.pdf")
    response = auth_client.get(reverse("documents:list"))
    assert response.status_code == 200
    assert "rg.pdf" in response.content.decode()

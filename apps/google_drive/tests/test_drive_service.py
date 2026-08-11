import io
import socket

import httplib2
import pytest
from googleapiclient.errors import HttpError

from apps.google_drive.exceptions import (
    GooglePermissionDeniedError,
    GoogleRateLimitError,
    GoogleResourceNotFoundError,
    GoogleServiceUnavailableError,
    GoogleTimeoutError,
    GoogleUploadFailedError,
)

pytestmark = pytest.mark.django_db


def _http_error(status):
    response = httplib2.Response({"status": status, "reason": "error"})
    return HttpError(response, b"error body")


def test_find_folder_returns_id_when_found(drive_service):
    service, client = drive_service
    client.files.return_value.list.return_value.execute.return_value = {
        "files": [{"id": "folder-123", "name": "Documentos"}]
    }
    assert service.find_folder("Documentos", parent_id="root-id") == "folder-123"


def test_find_folder_returns_none_when_not_found(drive_service):
    service, client = drive_service
    client.files.return_value.list.return_value.execute.return_value = {"files": []}
    assert service.find_folder("Documentos", parent_id="root-id") is None


def test_get_or_create_folder_reuses_existing_folder(drive_service):
    service, client = drive_service
    client.files.return_value.list.return_value.execute.return_value = {
        "files": [{"id": "existing-folder", "name": "Fotos"}]
    }
    folder_id = service.get_or_create_folder("Fotos", parent_id="root-id")
    assert folder_id == "existing-folder"
    client.files.return_value.create.assert_not_called()


def test_get_or_create_folder_creates_when_missing(drive_service):
    service, client = drive_service
    client.files.return_value.list.return_value.execute.return_value = {"files": []}
    client.files.return_value.create.return_value.execute.return_value = {"id": "new-folder"}
    folder_id = service.get_or_create_folder("Outros", parent_id="root-id")
    assert folder_id == "new-folder"
    client.files.return_value.create.assert_called_once()


def test_upload_file_returns_created_file_metadata(drive_service):
    service, client = drive_service
    client.files.return_value.create.return_value.execute.return_value = {
        "id": "file-1", "name": "rg.pdf", "webViewLink": "https://drive.google.com/file/d/file-1/view",
    }
    result = service.upload_file(
        io.BytesIO(b"conteudo"), filename="rg.pdf", mime_type="application/pdf", parent_folder_id="folder-1"
    )
    assert result["id"] == "file-1"
    assert result["webViewLink"].startswith("https://drive.google.com")


def test_upload_file_translates_http_error_to_upload_failed(drive_service):
    service, client = drive_service
    client.files.return_value.create.return_value.execute.side_effect = _http_error(500)
    with pytest.raises(GoogleUploadFailedError):
        service.upload_file(io.BytesIO(b"x"), filename="a.pdf", mime_type="application/pdf", parent_folder_id="f1")


def test_delete_file_success(drive_service):
    service, client = drive_service
    client.files.return_value.delete.return_value.execute.return_value = None
    service.delete_file("file-1")
    client.files.return_value.delete.assert_called_once_with(fileId="file-1")


@pytest.mark.parametrize(
    "status,expected_exception",
    [
        (401, GooglePermissionDeniedError),
        (403, GooglePermissionDeniedError),
        (404, GoogleResourceNotFoundError),
        (429, GoogleRateLimitError),
        (500, GoogleServiceUnavailableError),
        (503, GoogleServiceUnavailableError),
    ],
)
def test_http_errors_are_translated_to_domain_exceptions(drive_service, status, expected_exception):
    service, client = drive_service
    client.files.return_value.get.return_value.execute.side_effect = _http_error(status)
    with pytest.raises(expected_exception):
        service.get_file_metadata("file-1")


def test_socket_timeout_is_translated_to_timeout_error(drive_service):
    service, client = drive_service
    client.files.return_value.get.return_value.execute.side_effect = socket.timeout()
    with pytest.raises(GoogleTimeoutError):
        service.get_file_metadata("file-1")


def test_list_files_returns_files_list(drive_service):
    service, client = drive_service
    client.files.return_value.list.return_value.execute.return_value = {
        "files": [{"id": "1", "name": "a.pdf"}, {"id": "2", "name": "b.jpg"}]
    }
    files = service.list_files("folder-1")
    assert len(files) == 2


def test_move_file_uses_current_parents_when_not_provided(drive_service):
    service, client = drive_service
    client.files.return_value.get.return_value.execute.return_value = {"parents": ["old-parent"]}
    client.files.return_value.update.return_value.execute.return_value = {"id": "file-1", "parents": ["new-parent"]}
    result = service.move_file("file-1", new_parent_id="new-parent")
    assert result["parents"] == ["new-parent"]
    client.files.return_value.update.assert_called_once_with(
        fileId="file-1", addParents="new-parent", removeParents="old-parent", fields="id,parents"
    )

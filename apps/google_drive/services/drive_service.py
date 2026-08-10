import io
import logging
import socket
from contextlib import contextmanager

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from apps.google_drive.exceptions import (
    GooglePermissionDeniedError,
    GoogleRateLimitError,
    GoogleResourceNotFoundError,
    GoogleServiceUnavailableError,
    GoogleTimeoutError,
    GoogleUploadFailedError,
)
from apps.google_drive.services.auth_service import GoogleAuthService

logger = logging.getLogger(__name__)

FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"

STATUS_TO_EXCEPTION = {
    401: GooglePermissionDeniedError,
    403: GooglePermissionDeniedError,
    404: GoogleResourceNotFoundError,
    429: GoogleRateLimitError,
}


@contextmanager
def translate_google_errors(default_exception=GoogleServiceUnavailableError):
    try:
        yield
    except HttpError as exc:
        status = getattr(exc.resp, "status", None)
        exception_cls = STATUS_TO_EXCEPTION.get(status)
        if exception_cls is None:
            exception_cls = default_exception if (status is None or status >= 500) else GoogleServiceUnavailableError
        logger.error("Erro da API do Google Drive (status=%s)", status, exc_info=True)
        raise exception_cls() from exc
    except (socket.timeout, TimeoutError) as exc:
        logger.error("Timeout ao comunicar com o Google Drive", exc_info=True)
        raise GoogleTimeoutError() from exc


class GoogleDriveService:
    def __init__(self, auth_service: GoogleAuthService | None = None):
        self.auth_service = auth_service or GoogleAuthService()
        self._client = None

    @property
    def client(self):
        if self._client is None:
            credentials = self.auth_service.get_authorized_credentials()
            self._client = build("drive", "v3", credentials=credentials, cache_discovery=False)
        return self._client

    def create_folder(self, name: str, parent_id: str) -> str:
        with translate_google_errors():
            metadata = {"name": name, "mimeType": FOLDER_MIME_TYPE, "parents": [parent_id]}
            folder = self.client.files().create(body=metadata, fields="id").execute()
            return folder["id"]

    def find_folder(self, name: str, parent_id: str) -> str | None:
        with translate_google_errors():
            escaped_name = name.replace("'", "\\'")
            query = (
                f"name = '{escaped_name}' and '{parent_id}' in parents "
                f"and mimeType = '{FOLDER_MIME_TYPE}' and trashed = false"
            )
            response = self.client.files().list(q=query, fields="files(id, name)", pageSize=1).execute()
            files = response.get("files", [])
            return files[0]["id"] if files else None

    def get_or_create_folder(self, name: str, parent_id: str) -> str:
        existing = self.find_folder(name, parent_id)
        if existing:
            return existing
        return self.create_folder(name, parent_id)

    def upload_file(self, file_obj, *, filename: str, mime_type: str, parent_folder_id: str) -> dict:
        with translate_google_errors(default_exception=GoogleUploadFailedError):
            metadata = {"name": filename, "parents": [parent_folder_id]}
            media = MediaIoBaseUpload(file_obj, mimetype=mime_type, resumable=False)
            created = (
                self.client.files()
                .create(body=metadata, media_body=media, fields="id, name, webViewLink, mimeType, size")
                .execute()
            )
            return created

    def download_file(self, file_id: str) -> bytes:
        with translate_google_errors():
            request = self.client.files().get_media(fileId=file_id)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return buffer.getvalue()

    def delete_file(self, file_id: str) -> None:
        with translate_google_errors():
            self.client.files().delete(fileId=file_id).execute()

    def move_file(self, file_id: str, *, new_parent_id: str, old_parent_id: str | None = None) -> dict:
        with translate_google_errors():
            if old_parent_id is None:
                current = self.client.files().get(fileId=file_id, fields="parents").execute()
                old_parent_id = ",".join(current.get("parents", []))
            return (
                self.client.files()
                .update(fileId=file_id, addParents=new_parent_id, removeParents=old_parent_id, fields="id, parents")
                .execute()
            )

    def list_files(self, parent_id: str) -> list[dict]:
        with translate_google_errors():
            query = f"'{parent_id}' in parents and trashed = false"
            response = (
                self.client.files()
                .list(q=query, fields="files(id, name, mimeType, size, webViewLink)")
                .execute()
            )
            return response.get("files", [])

    def get_file_metadata(self, file_id: str) -> dict:
        with translate_google_errors():
            return (
                self.client.files()
                .get(fileId=file_id, fields="id, name, mimeType, size, webViewLink, parents")
                .execute()
            )

    def get_file(self, file_id: str) -> dict:
        return self.get_file_metadata(file_id)

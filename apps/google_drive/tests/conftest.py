from unittest.mock import MagicMock

import pytest

from apps.google_drive.services.auth_service import GoogleAuthService
from apps.google_drive.services.drive_service import GoogleDriveService
from apps.google_drive.services.sheets_service import GoogleSheetsService


@pytest.fixture
def fake_auth_service():
    service = MagicMock(spec=GoogleAuthService)
    service.get_authorized_credentials.return_value = MagicMock()
    return service


@pytest.fixture
def drive_service(fake_auth_service, mocker):
    mock_build = mocker.patch("apps.google_drive.services.drive_service.build")
    service = GoogleDriveService(auth_service=fake_auth_service)
    return service, mock_build.return_value


@pytest.fixture
def sheets_service(fake_auth_service, mocker):
    mock_build = mocker.patch("apps.google_drive.services.sheets_service.build")
    service = GoogleSheetsService(auth_service=fake_auth_service)
    return service, mock_build.return_value

import logging

from googleapiclient.discovery import build

from apps.google_drive.services.auth_service import GoogleAuthService
from apps.google_drive.services.drive_service import translate_google_errors

logger = logging.getLogger(__name__)

DEFAULT_RANGE = "A1"


class GoogleSheetsService:
    def __init__(self, auth_service: GoogleAuthService | None = None):
        self.auth_service = auth_service or GoogleAuthService()
        self._client = None

    @property
    def client(self):
        if self._client is None:
            credentials = self.auth_service.get_authorized_credentials()
            self._client = build("sheets", "v4", credentials=credentials, cache_discovery=False)
        return self._client

    def create_spreadsheet(self, title: str) -> dict:
        with translate_google_errors():
            spreadsheet = (
                self.client.spreadsheets()
                .create(body={"properties": {"title": title}}, fields="spreadsheetId, spreadsheetUrl")
                .execute()
            )
            return spreadsheet

    def update_values(self, spreadsheet_id: str, *, values: list[list], range_name: str = DEFAULT_RANGE) -> dict:
        with translate_google_errors():
            body = {"values": values}
            return (
                self.client.spreadsheets()
                .values()
                .update(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption="USER_ENTERED", body=body)
                .execute()
            )

    def get_values(self, spreadsheet_id: str, *, range_name: str = DEFAULT_RANGE) -> list[list]:
        with translate_google_errors():
            result = (
                self.client.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )
            return result.get("values", [])

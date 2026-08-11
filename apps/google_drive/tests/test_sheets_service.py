import pytest

pytestmark = pytest.mark.django_db


def test_create_spreadsheet_returns_id_and_url(sheets_service):
    service, client = sheets_service
    client.spreadsheets.return_value.create.return_value.execute.return_value = {
        "spreadsheetId": "sheet-1",
        "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/sheet-1",
    }
    result = service.create_spreadsheet("Notas - 1º Ano A")
    assert result["spreadsheetId"] == "sheet-1"
    client.spreadsheets.return_value.create.assert_called_once()

    # Regressão: a API do Sheets (diferente da API do Drive) rejeita espaço
    # após a vírgula no parâmetro "fields" com HTTP 400 "invalid argument".
    _, kwargs = client.spreadsheets.return_value.create.call_args
    assert " " not in kwargs["fields"]


def test_update_values_sends_matrix_to_sheets_api(sheets_service):
    service, client = sheets_service
    client.spreadsheets.return_value.values.return_value.update.return_value.execute.return_value = {
        "updatedCells": 6
    }
    values = [["Aluno", "Matemática"], ["João Silva", "8.5"]]
    result = service.update_values("sheet-1", values=values)
    assert result["updatedCells"] == 6
    _, kwargs = client.spreadsheets.return_value.values.return_value.update.call_args
    assert kwargs["body"]["values"] == values


def test_get_values_returns_matrix(sheets_service):
    service, client = sheets_service
    client.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {
        "values": [["Aluno", "Matemática"], ["João Silva", "8.5"]]
    }
    values = service.get_values("sheet-1")
    assert values[0] == ["Aluno", "Matemática"]

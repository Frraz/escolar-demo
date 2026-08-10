from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _get_fernet():
    key = settings.FIELD_ENCRYPTION_KEY
    if not key:
        raise RuntimeError(
            "FIELD_ENCRYPTION_KEY não está configurada. Defina-a no .env antes de "
            "armazenar credenciais do Google."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


class EncryptedTextField(models.TextField):
    """Campo de texto cifrado em repouso com Fernet.

    O valor Python é sempre o texto plano; a cifra acontece apenas na
    escrita/leitura do banco, então o restante da aplicação usa o campo
    como um TextField comum.
    """

    def get_prep_value(self, value):
        if value is None or value == "":
            return value
        token = _get_fernet().encrypt(value.encode()).decode()
        return super().get_prep_value(token)

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return value
        try:
            return _get_fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            return ""

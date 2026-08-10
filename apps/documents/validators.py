import os
import re
import unicodedata

import magic
from django.conf import settings
from django.core.exceptions import ValidationError

# Para cada extensão permitida, os mimetypes reais aceitos ao inspecionar o
# conteúdo binário do arquivo (nunca confiar apenas no Content-Type enviado
# pelo navegador). Formatos baseados em ZIP (docx/xlsx) podem ser detectados
# como application/zip por algumas versões da libmagic — por isso aceitamos
# ambos os valores.
ALLOWED_MIME_TYPES_BY_EXTENSION = {
    ".pdf": {"application/pdf"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".doc": {"application/msword"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
    },
    ".xls": {"application/vnd.ms-excel"},
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
    },
    ".txt": {"text/plain"},
    ".csv": {"text/plain", "text/csv"},
}


def sanitize_filename(filename: str) -> str:
    """Remove caracteres perigosos e sequências de path traversal, mantendo o
    nome legível para exibição. Nunca é usado como caminho de arquivo real —
    o arquivo é enviado diretamente ao Google Drive, sem tocar o filesystem."""
    filename = os.path.basename(filename)
    filename = unicodedata.normalize("NFKC", filename)
    filename = filename.replace("/", "").replace("\\", "")
    filename = re.sub(r"[\x00-\x1f]", "", filename)
    filename = filename.strip(" .")
    return filename or "arquivo"


def validate_upload(uploaded_file):
    """Valida extensão, tamanho e mimetype real de um arquivo enviado.
    Levanta ValidationError com mensagem amigável em caso de falha."""
    extension = os.path.splitext(uploaded_file.name)[1].lower()

    if extension not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)
        raise ValidationError(f"Tipo de arquivo não permitido. Formatos aceitos: {allowed}.")

    if uploaded_file.size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError(f"O arquivo excede o tamanho máximo de {settings.MAX_UPLOAD_SIZE_MB} MB.")

    header = uploaded_file.read(2048)
    uploaded_file.seek(0)
    detected_mime = magic.from_buffer(header, mime=True)

    allowed_mimes = ALLOWED_MIME_TYPES_BY_EXTENSION.get(extension, set())
    if allowed_mimes and detected_mime not in allowed_mimes:
        raise ValidationError(
            "O conteúdo do arquivo não corresponde à extensão informada. Verifique o arquivo e tente novamente."
        )

    return detected_mime

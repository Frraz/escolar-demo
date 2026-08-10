import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from apps.documents.validators import sanitize_filename, validate_upload

PDF_BYTES = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n"
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_sanitize_filename_strips_path_traversal():
    assert sanitize_filename("../../etc/passwd") == "passwd"


def test_sanitize_filename_strips_control_characters():
    assert sanitize_filename("relatorio\x00.pdf") == "relatorio.pdf"


def test_sanitize_filename_falls_back_when_empty():
    assert sanitize_filename("...") == "arquivo"


def test_validate_upload_accepts_real_pdf():
    upload = SimpleUploadedFile("documento.pdf", PDF_BYTES, content_type="application/pdf")
    detected_mime = validate_upload(upload)
    assert detected_mime == "application/pdf"


def test_validate_upload_accepts_real_png():
    upload = SimpleUploadedFile("foto.png", PNG_BYTES, content_type="image/png")
    detected_mime = validate_upload(upload)
    assert detected_mime == "image/png"


def test_validate_upload_rejects_disallowed_extension():
    upload = SimpleUploadedFile("virus.exe", b"MZ\x90\x00", content_type="application/octet-stream")
    with pytest.raises(ValidationError):
        validate_upload(upload)


def test_validate_upload_rejects_content_that_does_not_match_extension():
    # Extensão .pdf mas conteúdo é texto puro — o "magic number" não bate.
    upload = SimpleUploadedFile("fake.pdf", b"isto nao e um pdf de verdade", content_type="application/pdf")
    with pytest.raises(ValidationError):
        validate_upload(upload)


@override_settings(MAX_UPLOAD_SIZE_BYTES=10, MAX_UPLOAD_SIZE_MB=1)
def test_validate_upload_rejects_file_too_large():
    upload = SimpleUploadedFile("documento.pdf", PDF_BYTES, content_type="application/pdf")
    with pytest.raises(ValidationError):
        validate_upload(upload)

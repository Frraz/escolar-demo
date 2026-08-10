import factory

from apps.documents.models import Document, DocumentCategory
from apps.students.tests.factories import StudentFactory


class DocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Document

    student = factory.SubFactory(StudentFactory)
    name = factory.Sequence(lambda n: f"documento-{n}.pdf")
    category = DocumentCategory.DOCUMENTOS
    mime_type = "application/pdf"
    size = 1024
    google_drive_file_id = factory.Sequence(lambda n: f"drive-file-{n}")
    google_drive_folder_id = "drive-folder-1"
    google_drive_url = factory.LazyAttribute(
        lambda o: f"https://drive.google.com/file/d/{o.google_drive_file_id}/view"
    )

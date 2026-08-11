import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DeleteView, ListView, View

from apps.google_drive.exceptions import GoogleServiceError
from apps.google_drive.services.drive_service import GoogleDriveService
from apps.google_drive.services.folder_service import FolderStructureService
from apps.students.models import Student

from .forms import DocumentUploadForm
from .models import Document
from .validators import sanitize_filename

logger = logging.getLogger(__name__)


class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = "documents/list.html"
    context_object_name = "documents"
    paginate_by = 30

    def get_queryset(self):
        return super().get_queryset().select_related("student")


def _documents_section_context(student):
    return {
        "student": student,
        "documents": student.documents.all(),
        "upload_form": DocumentUploadForm(),
    }


class DocumentUploadView(LoginRequiredMixin, View):
    def post(self, request, student_id):
        student = get_object_or_404(Student, pk=student_id)
        form = DocumentUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            context = _documents_section_context(student)
            context["upload_form"] = form
            return render(request, "students/_documents_section.html", context)

        uploaded_file = form.cleaned_data["file"]
        category = form.cleaned_data["category"]
        detected_mime = form.detected_mime_type
        clean_name = sanitize_filename(uploaded_file.name)

        try:
            folders = FolderStructureService().ensure_student_folders(student)
            target_folder_id = folders[category]
            drive_file = GoogleDriveService().upload_file(
                uploaded_file,
                filename=clean_name,
                mime_type=detected_mime,
                parent_folder_id=target_folder_id,
            )
        except GoogleServiceError as exc:
            logger.error(
                "Falha ao enviar documento para o Google Drive", exc_info=True,
                extra={"student_id": student.id, "user_id": request.user.id},
            )
            context = _documents_section_context(student)
            context["upload_error"] = exc.user_message
            return render(request, "students/_documents_section.html", context)
        except Exception:
            logger.exception(
                "Erro inesperado ao enviar documento para o Google Drive",
                extra={"student_id": student.id, "user_id": request.user.id},
            )
            context = _documents_section_context(student)
            context["upload_error"] = "Não foi possível enviar o arquivo. Tente novamente."
            return render(request, "students/_documents_section.html", context)

        try:
            with transaction.atomic():
                Document.objects.create(
                    student=student,
                    name=clean_name,
                    category=category,
                    mime_type=detected_mime,
                    size=uploaded_file.size,
                    google_drive_file_id=drive_file["id"],
                    google_drive_folder_id=target_folder_id,
                    google_drive_url=drive_file.get("webViewLink", ""),
                    uploaded_by=request.user,
                )
        except Exception:
            logger.error(
                "Documento enviado ao Drive mas falhou ao salvar no banco. Tentando cleanup.",
                exc_info=True, extra={"student_id": student.id, "drive_file_id": drive_file["id"]},
            )
            try:
                GoogleDriveService().delete_file(drive_file["id"])
                logger.info("Arquivo órfão removido do Drive: %s", drive_file["id"])
            except Exception:
                logger.critical(
                    "ARQUIVO ÓRFÃO NO DRIVE precisa de limpeza manual: file_id=%s, folder_id=%s",
                    drive_file["id"], target_folder_id, exc_info=True,
                )
            context = _documents_section_context(student)
            context["upload_error"] = "Não foi possível concluir o envio. Tente novamente."
            return render(request, "students/_documents_section.html", context)

        return render(request, "students/_documents_section.html", _documents_section_context(student))


class DocumentDownloadView(LoginRequiredMixin, View):
    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        return redirect(document.google_drive_url)


class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    model = Document

    def post(self, request, *args, **kwargs):
        document = self.get_object()
        student = document.student
        try:
            GoogleDriveService().delete_file(document.google_drive_file_id)
        except GoogleServiceError as exc:
            logger.error(
                "Falha ao excluir documento no Google Drive", exc_info=True,
                extra={"document_id": document.id, "user_id": request.user.id},
            )
            context = _documents_section_context(student)
            context["upload_error"] = exc.user_message
            return render(request, "students/_documents_section.html", context)
        except Exception:
            logger.exception(
                "Erro inesperado ao excluir documento no Google Drive",
                extra={"document_id": document.id, "user_id": request.user.id},
            )
            context = _documents_section_context(student)
            context["upload_error"] = "Não foi possível excluir o arquivo. Tente novamente."
            return render(request, "students/_documents_section.html", context)

        document.delete()
        return render(request, "students/_documents_section.html", _documents_section_context(student))

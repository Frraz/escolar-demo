from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.views.generic import TemplateView

from apps.classes.models import Class
from apps.documents.models import Document
from apps.google_drive.models import GoogleCredential, GoogleSheet
from apps.students.models import Student

from .utils import format_bytes


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_size = Document.objects.aggregate(total=Sum("size"))["total"] or 0

        context["students_count"] = Student.objects.count()
        context["classes_count"] = Class.objects.count()
        context["documents_count"] = Document.objects.count()
        context["sheets_count"] = GoogleSheet.objects.count()
        context["total_size_display"] = format_bytes(total_size)
        context["recent_documents"] = Document.objects.select_related("student").order_by("-created_at")[:8]
        context["is_drive_connected"] = GoogleCredential.get_solo() is not None
        return context

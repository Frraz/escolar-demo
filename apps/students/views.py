from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.documents.forms import DocumentUploadForm
from apps.google_drive.models import FolderKind

from .forms import StudentForm
from .models import Student


class StudentListView(LoginRequiredMixin, ListView):
    model = Student
    template_name = "students/list.html"
    context_object_name = "students"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related("school_class")
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(full_name__icontains=search)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("q", "")
        return context


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = "students/detail.html"
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documents"] = self.object.documents.all()
        context["upload_form"] = DocumentUploadForm()
        context["drive_folder"] = self.object.drive_folders.filter(kind=FolderKind.STUDENT).first()
        return context


class StudentCreateView(LoginRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = "students/form.html"
    success_url = reverse_lazy("students:list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Aluno \"{self.object.full_name}\" cadastrado com sucesso.")
        return response


class StudentUpdateView(LoginRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = "students/form.html"
    success_url = reverse_lazy("students:list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Aluno \"{self.object.full_name}\" atualizado com sucesso.")
        return response


class StudentDeleteView(LoginRequiredMixin, DeleteView):
    model = Student
    template_name = "students/confirm_delete.html"
    success_url = reverse_lazy("students:list")

    def form_valid(self, form):
        messages.success(self.request, "Aluno removido com sucesso.")
        return super().form_valid(form)

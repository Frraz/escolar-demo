from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.google_drive.models import FolderKind

from .forms import ClassForm
from .models import Class


class ClassListView(LoginRequiredMixin, ListView):
    model = Class
    template_name = "classes/list.html"
    context_object_name = "classes"
    paginate_by = 20


class ClassDetailView(LoginRequiredMixin, DetailView):
    model = Class
    template_name = "classes/detail.html"
    context_object_name = "school_class"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["students"] = self.object.students.all()
        context["drive_folder"] = self.object.drive_folders.filter(kind=FolderKind.CLASS).first()
        context["grade_sheet"] = getattr(self.object, "grade_sheet", None)
        return context


class ClassCreateView(LoginRequiredMixin, CreateView):
    model = Class
    form_class = ClassForm
    template_name = "classes/form.html"
    success_url = reverse_lazy("classes:list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Turma \"{self.object}\" criada com sucesso.")
        return response


class ClassUpdateView(LoginRequiredMixin, UpdateView):
    model = Class
    form_class = ClassForm
    template_name = "classes/form.html"
    success_url = reverse_lazy("classes:list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Turma \"{self.object}\" atualizada com sucesso.")
        return response


class ClassDeleteView(LoginRequiredMixin, DeleteView):
    model = Class
    template_name = "classes/confirm_delete.html"
    success_url = reverse_lazy("classes:list")

    def form_valid(self, form):
        messages.success(self.request, "Turma removida com sucesso.")
        return super().form_valid(form)

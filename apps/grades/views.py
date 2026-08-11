import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.classes.models import Class
from apps.google_drive.exceptions import GoogleServiceError
from apps.google_drive.models import GoogleSheet
from apps.google_drive.services.drive_service import GoogleDriveService
from apps.google_drive.services.folder_service import FolderStructureService
from apps.google_drive.services.sheets_service import GoogleSheetsService

from .models import Grade, Subject

logger = logging.getLogger(__name__)

DEFAULT_TERM = "1"


class GradesIndexView(LoginRequiredMixin, ListView):
    model = Class
    template_name = "grades/index.html"
    context_object_name = "classes"


def _build_grade_matrix(school_class):
    students = list(school_class.students.all())
    subjects = list(Subject.objects.all())
    grades = {
        (grade.student_id, grade.subject_id): grade
        for grade in Grade.objects.filter(school_class=school_class, term=DEFAULT_TERM)
    }
    rows = []
    for student in students:
        cells = [grades.get((student.id, subject.id)) for subject in subjects]
        rows.append({"student": student, "cells": list(zip(subjects, cells))})
    return subjects, rows


class ClassGradesView(LoginRequiredMixin, TemplateView):
    template_name = "grades/class_grades.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school_class = get_object_or_404(Class, pk=kwargs["class_id"])
        subjects, rows = _build_grade_matrix(school_class)
        context["school_class"] = school_class
        context["subjects"] = subjects
        context["rows"] = rows
        context["grade_sheet"] = GoogleSheet.objects.filter(school_class=school_class).first()
        return context


class UpdateGradeView(LoginRequiredMixin, View):
    def post(self, request, class_id):
        school_class = get_object_or_404(Class, pk=class_id)
        student_id = request.POST.get("student_id")
        subject_id = request.POST.get("subject_id")
        raw_value = request.POST.get("value", "").strip().replace(",", ".")

        value = raw_value or None
        error = None
        if value is not None:
            try:
                value = float(value)
                if not 0 <= value <= 10:
                    raise ValueError
            except ValueError:
                error = "Nota inválida. Use um valor entre 0 e 10."

        if error is None:
            Grade.objects.update_or_create(
                student_id=student_id, subject_id=subject_id, school_class=school_class, term=DEFAULT_TERM,
                defaults={"value": value, "updated_by": request.user},
            )

        subjects, rows = _build_grade_matrix(school_class)
        return render(request, "grades/_matrix.html", {
            "school_class": school_class, "subjects": subjects, "rows": rows, "error": error,
        })


class SyncGradeSheetView(LoginRequiredMixin, View):
    def post(self, request, class_id):
        school_class = get_object_or_404(Class, pk=class_id)
        subjects, rows = _build_grade_matrix(school_class)

        matrix = [["Aluno"] + [subject.name for subject in subjects]]
        for row in rows:
            line = [row["student"].full_name]
            for _subject, grade in row["cells"]:
                line.append(str(grade.value) if grade and grade.value is not None else "")
            matrix.append(line)

        try:
            class_folder_id = FolderStructureService().ensure_class_folder(school_class)
            sheet = GoogleSheet.objects.filter(school_class=school_class).first()
            sheets_service = GoogleSheetsService()

            if sheet is None:
                created = sheets_service.create_spreadsheet(f"Notas - {school_class.name}")
                GoogleDriveService().move_file(created["spreadsheetId"], new_parent_id=class_folder_id)
                sheet = GoogleSheet.objects.create(
                    school_class=school_class,
                    google_sheet_id=created["spreadsheetId"],
                    google_drive_url=created["spreadsheetUrl"],
                    google_drive_folder_id=class_folder_id,
                )

            sheets_service.update_values(sheet.google_sheet_id, values=matrix)
            sheet.last_synced_at = timezone.now()
            sheet.save(update_fields=["last_synced_at"])
        except GoogleServiceError as exc:
            logger.error(
                "Falha ao sincronizar notas com o Google Sheets", exc_info=True,
                extra={"class_id": school_class.id, "user_id": request.user.id},
            )
            messages.error(request, exc.user_message)
            return redirect("grades:class_grades", class_id=school_class.id)
        except Exception:
            logger.exception(
                "Erro inesperado ao sincronizar notas com o Google Sheets",
                extra={"class_id": school_class.id, "user_id": request.user.id},
            )
            messages.error(request, "Não foi possível sincronizar as notas com o Google Sheets. Tente novamente.")
            return redirect("grades:class_grades", class_id=school_class.id)

        messages.success(request, "Notas sincronizadas com o Google Sheets.")
        return redirect("grades:class_grades", class_id=school_class.id)

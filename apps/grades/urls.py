from django.urls import path

from . import views

app_name = "grades"

urlpatterns = [
    path("", views.GradesIndexView.as_view(), name="index"),
    path("turma/<int:class_id>/", views.ClassGradesView.as_view(), name="class_grades"),
    path("turma/<int:class_id>/nota/", views.UpdateGradeView.as_view(), name="update_grade"),
    path("turma/<int:class_id>/sincronizar/", views.SyncGradeSheetView.as_view(), name="sync_sheet"),
]

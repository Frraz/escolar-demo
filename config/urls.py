from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls")),
    path("contas/", include("apps.accounts.urls")),
    path("alunos/", include("apps.students.urls")),
    path("turmas/", include("apps.classes.urls")),
    path("documentos/", include("apps.documents.urls")),
    path("notas/", include("apps.grades.urls")),
    path("google-drive/", include("apps.google_drive.urls")),
]

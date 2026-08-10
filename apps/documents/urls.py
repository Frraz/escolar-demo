from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("", views.DocumentListView.as_view(), name="list"),
    path("alunos/<int:student_id>/enviar/", views.DocumentUploadView.as_view(), name="upload"),
    path("<int:pk>/baixar/", views.DocumentDownloadView.as_view(), name="download"),
    path("<int:pk>/excluir/", views.DocumentDeleteView.as_view(), name="delete"),
]

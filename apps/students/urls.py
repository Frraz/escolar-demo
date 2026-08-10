from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    path("", views.StudentListView.as_view(), name="list"),
    path("novo/", views.StudentCreateView.as_view(), name="create"),
    path("<int:pk>/", views.StudentDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.StudentUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.StudentDeleteView.as_view(), name="delete"),
]

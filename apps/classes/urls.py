from django.urls import path

from . import views

app_name = "classes"

urlpatterns = [
    path("", views.ClassListView.as_view(), name="list"),
    path("nova/", views.ClassCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ClassDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.ClassUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.ClassDeleteView.as_view(), name="delete"),
]

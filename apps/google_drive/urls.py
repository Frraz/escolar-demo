from django.urls import path

from . import views

app_name = "google_drive"

urlpatterns = [
    path("", views.DriveStatusView.as_view(), name="status"),
    path("connect/", views.DriveConnectView.as_view(), name="connect"),
    path("oauth2callback/", views.DriveOAuthCallbackView.as_view(), name="oauth2callback"),
    path("disconnect/", views.DriveDisconnectView.as_view(), name="disconnect"),
]

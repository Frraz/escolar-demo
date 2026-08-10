import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from .exceptions import GoogleServiceError
from .models import GoogleCredential
from .services.auth_service import GoogleAuthService

logger = logging.getLogger(__name__)

OAUTH_STATE_SESSION_KEY = "google_oauth_state"


class DriveStatusView(LoginRequiredMixin, TemplateView):
    template_name = "google_drive/status.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        credential = GoogleCredential.get_solo()
        context["credential"] = credential
        context["is_connected"] = credential is not None
        context["root_folder_configured"] = bool(settings.GOOGLE_DRIVE_ROOT_FOLDER_ID)
        if settings.GOOGLE_DRIVE_ROOT_FOLDER_ID:
            context["root_folder_url"] = (
                f"https://drive.google.com/drive/folders/{settings.GOOGLE_DRIVE_ROOT_FOLDER_ID}"
            )
        return context


class DriveConnectView(LoginRequiredMixin, View):
    def get(self, request):
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            messages.error(
                request,
                "As credenciais do Google (GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET) ainda não foram "
                "configuradas no .env. Consulte o README para o passo a passo.",
            )
            return redirect("google_drive:status")

        auth_url, state = GoogleAuthService().get_authorization_url()
        request.session[OAUTH_STATE_SESSION_KEY] = state
        return redirect(auth_url)


class DriveOAuthCallbackView(LoginRequiredMixin, View):
    def get(self, request):
        error = request.GET.get("error")
        if error:
            messages.error(request, "Conexão com o Google Drive cancelada ou negada.")
            return redirect("google_drive:status")

        code = request.GET.get("code")
        state = request.GET.get("state")
        expected_state = request.session.pop(OAUTH_STATE_SESSION_KEY, None)

        if not code or not state or state != expected_state:
            messages.error(request, "Não foi possível validar a resposta do Google. Tente conectar novamente.")
            return redirect("google_drive:status")

        try:
            GoogleAuthService().handle_callback(code=code, state=state, user=request.user)
        except GoogleServiceError as exc:
            logger.error("Falha ao concluir a conexão com o Google Drive", exc_info=True)
            messages.error(request, exc.user_message)
            return redirect("google_drive:status")
        except Exception:
            logger.error("Erro inesperado ao concluir OAuth do Google Drive", exc_info=True)
            messages.error(request, "Não foi possível concluir a conexão com o Google Drive. Tente novamente.")
            return redirect("google_drive:status")

        messages.success(request, "Google Drive conectado com sucesso.")
        return redirect("google_drive:status")


class DriveDisconnectView(LoginRequiredMixin, View):
    def post(self, request):
        GoogleAuthService().disconnect()
        messages.success(request, "Google Drive desconectado.")
        return redirect("google_drive:status")

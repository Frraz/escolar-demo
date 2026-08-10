import logging

from django.conf import settings
from django.utils import timezone
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from apps.google_drive.exceptions import GoogleAuthExpiredError, GoogleAuthNotConfiguredError
from apps.google_drive.models import GoogleCredential

logger = logging.getLogger(__name__)

# Margem de segurança para renovar o token antes de ele expirar de fato.
TOKEN_EXPIRY_MARGIN_SECONDS = 300


class GoogleAuthService:
    """Gerencia o ciclo de vida da credencial OAuth da conta Google do cliente."""

    def _client_config(self):
        return {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        }

    def build_flow(self, state=None):
        return Flow.from_client_config(
            self._client_config(),
            scopes=settings.GOOGLE_OAUTH_SCOPES,
            state=state,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )

    def get_authorization_url(self):
        flow = self.build_flow()
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return auth_url, state

    def handle_callback(self, *, code, state, user=None):
        flow = self.build_flow(state=state)
        flow.fetch_token(code=code)
        credentials = flow.credentials
        return self.save_credentials(credentials, user=user)

    def save_credentials(self, credentials: Credentials, user=None):
        account_email = self._resolve_account_email(credentials)
        google_credential, _ = GoogleCredential.objects.update_or_create(
            pk=1,
            defaults={
                "account_email": account_email,
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_expiry": credentials.expiry or timezone.now(),
                "scopes": " ".join(credentials.scopes or []),
                "connected_by": user,
            },
        )
        return google_credential

    def _resolve_account_email(self, credentials):
        id_token = getattr(credentials, "id_token", None)
        if isinstance(id_token, dict):
            return id_token.get("email", "")
        return ""

    def is_connected(self):
        return GoogleCredential.get_solo() is not None

    def get_authorized_credentials(self) -> Credentials:
        stored = GoogleCredential.get_solo()
        if stored is None:
            raise GoogleAuthNotConfiguredError()

        credentials = Credentials(
            token=stored.access_token,
            refresh_token=stored.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=stored.scopes.split() if stored.scopes else None,
        )
        credentials.expiry = stored.token_expiry

        seconds_to_expiry = (stored.token_expiry - timezone.now()).total_seconds()
        if seconds_to_expiry <= TOKEN_EXPIRY_MARGIN_SECONDS:
            try:
                credentials.refresh(Request())
            except RefreshError as exc:
                logger.error("Falha ao renovar token do Google Drive", exc_info=True)
                raise GoogleAuthExpiredError() from exc
            stored.access_token = credentials.token
            stored.token_expiry = credentials.expiry
            stored.save(update_fields=["access_token", "token_expiry", "updated_at"])

        return credentials

    def disconnect(self):
        GoogleCredential.objects.filter(pk=1).delete()

class GoogleServiceError(Exception):
    """Base para todos os erros da integração com o Google Drive/Sheets."""

    user_message = "Ocorreu um erro ao comunicar com o Google Drive. Tente novamente."


class GoogleAuthNotConfiguredError(GoogleServiceError):
    user_message = "O Google Drive ainda não foi conectado. Acesse Configurações para conectar."


class GoogleAuthExpiredError(GoogleServiceError):
    user_message = "A conexão com o Google Drive expirou. Reconecte em Configurações."


class GooglePermissionDeniedError(GoogleServiceError):
    user_message = "Sem permissão para acessar este recurso no Google Drive."


class GoogleResourceNotFoundError(GoogleServiceError):
    user_message = "Arquivo ou pasta não encontrado no Google Drive."


class GoogleRateLimitError(GoogleServiceError):
    user_message = "O Google Drive está temporariamente sobrecarregado. Tente novamente em instantes."


class GoogleServiceUnavailableError(GoogleServiceError):
    user_message = "O Google Drive está indisponível no momento. Tente novamente mais tarde."


class GoogleTimeoutError(GoogleServiceError):
    user_message = "A operação demorou demais para responder. Tente novamente."


class GoogleUploadFailedError(GoogleServiceError):
    user_message = "Não foi possível enviar o arquivo ao Google Drive."


class GoogleFileTooLargeError(GoogleServiceError):
    user_message = "O arquivo é muito grande para ser enviado."

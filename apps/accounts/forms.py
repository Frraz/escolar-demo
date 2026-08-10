from django.contrib.auth.forms import AuthenticationForm

INPUT_CLASSES = "field-input"


class StyledAuthenticationForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Usuário ou senha inválidos. Tente novamente.",
        "inactive": "Esta conta está desativada.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": INPUT_CLASSES, "autofocus": True})
        self.fields["password"].widget.attrs.update({"class": INPUT_CLASSES})

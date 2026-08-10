from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView

from .forms import StyledAuthenticationForm


class LoginView(DjangoLoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True
    authentication_form = StyledAuthenticationForm


class LogoutView(DjangoLogoutView):
    pass

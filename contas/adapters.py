from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


def dominio_email_permitido(email):
    if "@" not in email:
        return False

    dominio = email.rsplit("@", 1)[-1].strip().lower()
    permitidos = getattr(settings, "ALLOWED_EMAIL_DOMAINS", [])
    if isinstance(permitidos, str):
        permitidos = permitidos.split(",")
    permitidos = {
        dominio_permitido.strip().lower()
        for dominio_permitido in permitidos
        if dominio_permitido and dominio_permitido.strip()
    }
    return bool(dominio) and dominio in permitidos


class ContasSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Valida o domínio institucional antes de concluir o login social."""

    def pre_social_login(self, request, sociallogin):
        email, email_verificado = self._obter_email(sociallogin)

        if not email:
            self._rejeitar(
                request,
                "Não foi possível obter um email da conta Google.",
            )

        if not email_verificado:
            self._rejeitar(
                request,
                "O email da conta Google não está verificado.",
            )

        if not dominio_email_permitido(email):
            dominio = email.rsplit("@", 1)[-1]
            self._rejeitar(
                request,
                f"O domínio «{dominio}» não está autorizado. "
                "Utilize uma conta institucional da UCM.",
            )

        # Liga a conta social a um utilizador local que já tenha este email,
        # em vez de criar um utilizador duplicado. Se a conta social já existe,
        # o allauth já a associou ao respetivo utilizador.
        if not sociallogin.account.pk:
            utilizador = (
                get_user_model()
                .objects.filter(email__iexact=email)
                .first()
            )
            if utilizador is not None:
                sociallogin.user = utilizador
                sociallogin.account.user = utilizador
                sociallogin.save(request, connect=True)

    @staticmethod
    def _obter_email(sociallogin):
        email = ""
        verificado = False

        enderecos = list(getattr(sociallogin, "email_addresses", None) or [])
        if enderecos:
            principal = next(
                (endereco for endereco in enderecos if endereco.primary),
                enderecos[0],
            )
            email = (principal.email or "").strip().lower()
            verificado = bool(principal.verified)

        extra_data = getattr(sociallogin.account, "extra_data", None) or {}
        if isinstance(extra_data, dict):
            if not email:
                email = (extra_data.get("email") or "").strip().lower()
            if "email_verified" in extra_data:
                verificado = bool(extra_data["email_verified"])
            elif "verified_email" in extra_data:
                verificado = bool(extra_data["verified_email"])

        if not email and sociallogin.user is not None:
            email = (getattr(sociallogin.user, "email", "") or "").strip().lower()

        return email, verificado

    @staticmethod
    def _rejeitar(request, mensagem):
        messages.error(request, mensagem)
        raise ImmediateHttpResponse(redirect(settings.LOGIN_URL))

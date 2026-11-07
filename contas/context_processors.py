from django.conf import settings


def google_oauth(request):
    """Só mostra o botão Google quando as credenciais estão configuradas."""
    return {
        "google_oauth_enabled": bool(
            getattr(settings, "GOOGLE_CLIENT_ID", "")
            and getattr(settings, "GOOGLE_CLIENT_SECRET", "")
        )
    }

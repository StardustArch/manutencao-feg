from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_redirect(request):
    # Redireciona com base no papel do utilizador (preparação para o futuro)
    perfil = request.perfil if hasattr(request, 'perfil') else None
    return render(request, 'contas/home.html', {'perfil': perfil})

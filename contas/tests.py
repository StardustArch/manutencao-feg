import tempfile
from io import StringIO
from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialAccount, SocialLogin

from .adapters import ContasSocialAccountAdapter
from .models import Perfil


class LoginSocialGoogleTests(TestCase):
    """Simula o fluxo social sem chamar a API do Google."""

    def setUp(self):
        self.factory = RequestFactory()
        self.adapter = ContasSocialAccountAdapter()

    def _pedido(self):
        pedido = self.factory.get("/accounts/google/login/callback/")
        pedido.session = {}
        pedido._messages = FallbackStorage(pedido)
        return pedido

    def _social_login(self, email, *, verificado=True, uid="google-uid", extra=None):
        return SocialLogin(
            user=User(username="utilizador_google", email=email),
            account=SocialAccount(
                provider="google",
                uid=uid,
                extra_data=extra or {},
            ),
            email_addresses=[
                EmailAddress(email=email, verified=verificado, primary=True)
            ],
        )

    def test_dominio_permitido_aceita_login_e_cria_perfil_utilizador(self):
        sociallogin = self._social_login("aluno@estudante.ucm.ac.mz")
        pedido = self._pedido()

        self.adapter.pre_social_login(pedido, sociallogin)
        self.adapter.save_user(pedido, sociallogin)

        utilizador = User.objects.get(email="aluno@estudante.ucm.ac.mz")
        self.assertEqual(utilizador.perfil.papel, "utilizador")
        self.assertEqual(utilizador.perfil.get_papel_display(), "Utilizador / Docente / Estudante")
        self.assertEqual(
            SocialAccount.objects.get(provider="google", uid="google-uid").user,
            utilizador,
        )

    def test_dominio_nao_permitido_e_rejeitado(self):
        dominios_invalidos = (
            "gmail.com",
            "evil-ucm.ac.mz",
            "ucm.ac.mz.evil.com",
        )

        for indice, dominio in enumerate(dominios_invalidos):
            with self.subTest(dominio=dominio):
                email = f"aluno@{dominio}"
                sociallogin = self._social_login(
                    email,
                    uid=f"google-invalido-{indice}",
                )

                with self.assertRaises(ImmediateHttpResponse) as contexto:
                    self.adapter.pre_social_login(self._pedido(), sociallogin)

                resposta = contexto.exception.response
                self.assertEqual(resposta.status_code, 302)
                self.assertEqual(resposta["Location"], settings.LOGIN_URL)
                self.assertFalse(
                    User.objects.filter(email__iexact=email).exists()
                )
                self.assertFalse(
                    SocialAccount.objects.filter(
                        uid=f"google-invalido-{indice}"
                    ).exists()
                )

    def test_email_verified_falso_e_rejeitado(self):
        sociallogin = self._social_login(
            "aluno@ucm.ac.mz",
            verificado=False,
            extra={"email_verified": False},
        )

        with self.assertRaises(ImmediateHttpResponse) as contexto:
            self.adapter.pre_social_login(self._pedido(), sociallogin)

        self.assertEqual(contexto.exception.response.status_code, 302)
        self.assertFalse(
            User.objects.filter(email__iexact="aluno@ucm.ac.mz").exists()
        )
        self.assertEqual(SocialAccount.objects.count(), 0)

    def test_conta_local_com_mesmo_email_e_ligada_sem_duplicar(self):
        local = User.objects.create_user(
            username="maria",
            email="maria@ucm.ac.mz",
            password="segredo123",
        )
        sociallogin = self._social_login(
            "maria@ucm.ac.mz",
            uid="google-maria",
        )

        self.adapter.pre_social_login(self._pedido(), sociallogin)

        self.assertEqual(
            User.objects.filter(email__iexact="maria@ucm.ac.mz").count(),
            1,
        )
        self.assertEqual(sociallogin.user, local)
        conta = SocialAccount.objects.get(provider="google", uid="google-maria")
        self.assertEqual(conta.user, local)
        self.assertEqual(local.perfil.papel, "utilizador")

    def test_importar_utilizadores_e_idempotente(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        caminho = Path(pasta.name) / "utilizadores.csv"
        caminho.write_text(
            "nome,email,papel\n"
            "Maria Silva,maria@ucm.ac.mz,tecnico\n"
            "João Costa,joao@estudante.ucm.ac.mz,utilizador\n",
            encoding="utf-8",
        )

        call_command("importar_utilizadores", str(caminho), stdout=StringIO())
        maria = User.objects.get(email="maria@ucm.ac.mz")
        password_inicial = maria.password
        contagens_iniciais = (
            User.objects.count(),
            Perfil.objects.count(),
            SocialAccount.objects.count(),
        )

        call_command("importar_utilizadores", str(caminho), stdout=StringIO())

        self.assertEqual(
            (
                User.objects.count(),
                Perfil.objects.count(),
                SocialAccount.objects.count(),
            ),
            contagens_iniciais,
        )
        maria.refresh_from_db()
        self.assertEqual(maria.password, password_inicial)
        self.assertEqual(maria.perfil.papel, "tecnico")
        self.assertEqual(
            User.objects.get(email="joao@estudante.ucm.ac.mz").perfil.papel,
            "utilizador",
        )

    def test_importar_utilizadores_com_sem_password(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        caminho = Path(pasta.name) / "utilizadores.csv"
        caminho.write_text(
            "nome,email,papel\n"
            "Ana Silva,ana@ucm.ac.mz,admin\n",
            encoding="utf-8",
        )

        call_command(
            "importar_utilizadores",
            str(caminho),
            "--sem-password",
            stdout=StringIO(),
        )

        ana = User.objects.get(email="ana@ucm.ac.mz")
        self.assertFalse(ana.has_usable_password())
        self.assertEqual(ana.perfil.papel, "admin")


class LoginPageGoogleTests(TestCase):
    """Verifica o botão Google e a preservação do parâmetro next."""

    def test_botao_google_aparece_e_preserva_o_next(self):
        next_url = reverse(
            "equipamentos:reportar_avaria_equipamento",
            kwargs={"pk": 42},
        )

        with override_settings(
            GOOGLE_CLIENT_ID="cliente-teste",
            GOOGLE_CLIENT_SECRET="segredo-teste",
        ):
            resposta = self.client.get(
                reverse("contas:login"),
                {"next": next_url},
            )

        self.assertContains(resposta, "Entrar com Google")
        self.assertContains(resposta, "bi-google")
        self.assertContains(
            resposta,
            "Acesso de técnicos e administradores",
        )
        self.assertContains(resposta, urlencode({"next": next_url}))

    def test_botao_google_fica_escondido_sem_credenciais(self):
        with override_settings(
            GOOGLE_CLIENT_ID="",
            GOOGLE_CLIENT_SECRET="",
        ):
            resposta = self.client.get(reverse("contas:login"))

        self.assertNotContains(resposta, "Entrar com Google")
        self.assertContains(
            resposta,
            "Acesso de técnicos e administradores",
        )

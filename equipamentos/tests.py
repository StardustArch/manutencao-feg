from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Avaria, Equipamento


class Passo7QRCodeRelatoriosTests(TestCase):
    """Testes das funcionalidades do Passo 7: QR codes e relatórios PDF."""

    def setUp(self):
        self.utilizador = User.objects.create_user(
            username="tecnico_teste",
            password="segredo123",
        )
        self.utilizador.perfil.papel = "tecnico"
        self.utilizador.perfil.save()

        self.equipamento = Equipamento.objects.create(
            codigo="UCM-FEG-PC-99",
            tipo="computador",
            marca_modelo="Dell OptiPlex 7010",
            estado="avariado",
        )
        self.avaria = Avaria.objects.create(
            equipamento=self.equipamento,
            reportado_por=self.utilizador,
            descricao="O computador não liga e o LED da fonte pisca.",
            prioridade="alta",
            estado="pendente",
        )
        self.client.force_login(self.utilizador)

    def test_get_absolute_url_aponta_para_a_ficha(self):
        self.assertEqual(
            self.equipamento.get_absolute_url(),
            reverse(
                "equipamentos:equipamento_detalhe",
                kwargs={"pk": self.equipamento.pk},
            ),
        )

    def test_lista_de_equipamentos(self):
        resposta = self.client.get(reverse("equipamentos:equipamentos_lista"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "UCM-FEG-PC-99")
        self.assertContains(resposta, "Inventário de Equipamentos")

    def test_ficha_do_equipamento_mostra_dados_e_historico(self):
        resposta = self.client.get(self.equipamento.get_absolute_url())

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Dell OptiPlex 7010")
        self.assertContains(resposta, "O computador não liga")
        self.assertContains(resposta, "QR code")

    def test_qrcode_devolve_um_png(self):
        resposta = self.client.get(
            reverse(
                "equipamentos:equipamento_qrcode",
                kwargs={"pk": self.equipamento.pk},
            )
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta["Content-Type"], "image/png")
        self.assertTrue(resposta.content.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertIn("qrcode-ucm-feg-pc-99.png", resposta["Content-Disposition"])

    def test_qrcode_exige_autenticacao(self):
        self.client.logout()
        resposta = self.client.get(
            reverse(
                "equipamentos:equipamento_qrcode",
                kwargs={"pk": self.equipamento.pk},
            )
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("contas:login"), resposta["Location"])

    def test_relatorio_pdf_de_inventario(self):
        resposta = self.client.get(
            reverse("equipamentos:relatorio_pdf"),
            {"tipo": "inventario"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta["Content-Type"], "application/pdf")
        self.assertTrue(resposta.content.startswith(b"%PDF-"))
        self.assertIn("relatorio_inventario.pdf", resposta["Content-Disposition"])

    def test_relatorio_pdf_de_avarias(self):
        resposta = self.client.get(
            reverse("equipamentos:relatorio_pdf"),
            {"tipo": "avarias"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta["Content-Type"], "application/pdf")
        self.assertTrue(resposta.content.startswith(b"%PDF-"))
        self.assertIn("relatorio_avarias.pdf", resposta["Content-Disposition"])

    def test_relatorio_pdf_rejeita_utilizador_sem_perfil_tecnico(self):
        utilizador_comum = User.objects.create_user(
            username="estudante_teste",
            password="segredo123",
        )
        self.client.force_login(utilizador_comum)

        resposta = self.client.get(reverse("equipamentos:relatorio_pdf"))

        self.assertEqual(resposta.status_code, 403)

    def test_dashboard_e_avarias_mostram_atalhos_pdf(self):
        for nome_url in ("equipamentos:dashboard", "equipamentos:avarias_lista"):
            with self.subTest(nome_url=nome_url):
                resposta = self.client.get(reverse(nome_url))
                self.assertEqual(resposta.status_code, 200)
                self.assertContains(resposta, "PDF")

    def test_login_devolve_o_utilizador_a_ficha_do_qrcode(self):
        self.client.logout()
        url_ficha = self.equipamento.get_absolute_url()

        resposta_sem_sessao = self.client.get(url_ficha)
        self.assertEqual(resposta_sem_sessao.status_code, 302)
        self.assertIn(f"next={url_ficha}", resposta_sem_sessao["Location"])

        resposta_formulario = self.client.get(
            reverse("contas:login"),
            {"next": url_ficha},
        )
        self.assertContains(
            resposta_formulario,
            f'name="next" value="{url_ficha}"',
        )

        resposta_login = self.client.post(
            reverse("contas:login"),
            {
                "username": "tecnico_teste",
                "password": "segredo123",
                "next": url_ficha,
            },
        )
        self.assertRedirects(
            resposta_login,
            url_ficha,
            fetch_redirect_response=False,
        )

    def test_utilizador_comum_pode_abrir_ficha_e_lista(self):
        utilizador_comum = User.objects.create_user(
            username="estudante_teste",
            password="segredo123",
        )
        self.client.force_login(utilizador_comum)

        resposta_ficha = self.client.get(self.equipamento.get_absolute_url())
        resposta_lista = self.client.get(
            reverse("equipamentos:equipamentos_lista")
        )

        self.assertEqual(resposta_ficha.status_code, 200)
        self.assertEqual(resposta_lista.status_code, 200)

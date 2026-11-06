from unittest import mock

import qrcode
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import (
    Avaria,
    Equipamento,
    HistoricoEstadoEquipamento,
    Intervencao,
    recalcular_estado_equipamento,
)


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

    def test_qrcode_contem_o_url_de_reporte_de_avaria(self):
        dados_capturados = {}
        adicionar_url_original = qrcode.QRCode.add_data

        def capturar_url(instancia, data, *args, **kwargs):
            dados_capturados["url"] = data
            return adicionar_url_original(
                instancia, data, *args, **kwargs
            )

        with mock.patch.object(
            qrcode.QRCode, "add_data", capturar_url
        ):
            resposta = self.client.get(
                reverse(
                    "equipamentos:equipamento_qrcode",
                    kwargs={"pk": self.equipamento.pk},
                )
            )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            dados_capturados["url"],
            "http://testserver"
            + reverse(
                "equipamentos:reportar_avaria_equipamento",
                kwargs={"pk": self.equipamento.pk},
            ),
        )

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


class SincronizacaoEstadoEquipamentoTests(TestCase):
    """Testes da sincronização entre avarias e estado do equipamento."""

    def setUp(self):
        self.utilizador = User.objects.create_user(
            username="utilizador_sincronizacao",
            password="segredo123",
        )
        self.equipamento = Equipamento.objects.create(
            codigo="UCM-FEG-SINC-01",
            tipo="computador",
            marca_modelo="HP EliteDesk",
            estado="operacional",
        )

    def _criar_avaria(self, estado="pendente", **kwargs):
        return Avaria.objects.create(
            equipamento=self.equipamento,
            reportado_por=self.utilizador,
            descricao="Descrição de teste",
            prioridade="media",
            estado=estado,
            **kwargs,
        )

    def test_criar_avaria_pendente_marca_equipamento_avariado(self):
        self._criar_avaria()

        self.equipamento.refresh_from_db()
        self.assertEqual(self.equipamento.estado, "avariado")

        historico = self.equipamento.historico_estados.get()
        self.assertEqual(historico.estado_anterior, "operacional")
        self.assertEqual(historico.estado_novo, "avariado")
        self.assertEqual(historico.origem, "fluxo")
        self.assertIsNone(historico.alterado_por)

    def test_criar_avaria_em_reparacao_marca_equipamento_em_manutencao(self):
        self._criar_avaria(estado="em_reparacao")

        self.equipamento.refresh_from_db()
        self.assertEqual(self.equipamento.estado, "manutencao")

    def test_recalcular_prioriza_em_reparacao_sobre_pendente(self):
        self._criar_avaria(estado="pendente")
        self._criar_avaria(estado="em_reparacao")

        recalcular_estado_equipamento(self.equipamento)

        self.equipamento.refresh_from_db()
        self.assertEqual(self.equipamento.estado, "manutencao")

    def test_sem_avarias_abertas_equipamento_volta_a_operacional(self):
        avaria = self._criar_avaria()
        avaria.estado = "resolvido"
        avaria.save()

        recalcular_estado_equipamento(self.equipamento)

        self.equipamento.refresh_from_db()
        self.assertEqual(self.equipamento.estado, "operacional")
        self.assertEqual(
            self.equipamento.historico_estados.first().estado_novo,
            "operacional",
        )

    def test_fluxo_automatico_nunca_altera_equipamento_abatido(self):
        self.equipamento.estado = "abatido"
        self.equipamento.save(update_fields=["estado"])

        self._criar_avaria()

        self.equipamento.refresh_from_db()
        self.assertEqual(self.equipamento.estado, "abatido")
        self.assertEqual(self.equipamento.historico_estados.count(), 0)

    def test_correcao_manual_pode_retirar_equipamento_de_abatido(self):
        self.equipamento.estado = "abatido"
        self.equipamento.save(update_fields=["estado"])

        recalcular_estado_equipamento(
            self.equipamento,
            actor=self.utilizador,
            origem="manual",
            motivo="Equipamento recuperado",
        )

        self.equipamento.refresh_from_db()
        self.assertEqual(self.equipamento.estado, "operacional")

        historico = self.equipamento.historico_estados.get()
        self.assertEqual(historico.origem, "manual")
        self.assertEqual(historico.motivo, "Equipamento recuperado")
        self.assertEqual(historico.alterado_por, self.utilizador)

    def test_estado_igual_nao_cria_historico(self):
        recalcular_estado_equipamento(self.equipamento)

        self.assertEqual(self.equipamento.historico_estados.count(), 0)


class FluxoReporteAvariasTests(TestCase):
    """Testes do novo fluxo de reporte, intervenções e correção de estado."""

    def setUp(self):
        self.utilizador = User.objects.create_user(
            username="utilizador_comum",
            password="segredo123",
        )
        self.tecnico = User.objects.create_user(
            username="tecnico_fluxo",
            password="segredo123",
        )
        self.tecnico.perfil.papel = "tecnico"
        self.tecnico.perfil.save()

        self.admin = User.objects.create_user(
            username="admin_fluxo",
            password="segredo123",
        )
        self.admin.perfil.papel = "admin"
        self.admin.perfil.save()

        self.equipamento = Equipamento.objects.create(
            codigo="UCM-FEG-FLUXO-01",
            tipo="laptop",
            marca_modelo="Lenovo ThinkPad",
            estado="operacional",
        )
        self.outro_equipamento = Equipamento.objects.create(
            codigo="UCM-FEG-FLUXO-02",
            tipo="projetor",
            marca_modelo="Epson",
            estado="operacional",
        )
        self.client.force_login(self.utilizador)

    def _criar_avaria(self, estado="pendente", tecnico=None, reportado_por=None):
        return Avaria.objects.create(
            equipamento=self.equipamento,
            reportado_por=reportado_por or self.utilizador,
            tecnico_atribuido=tecnico,
            descricao="Descrição da avaria de teste",
            prioridade="alta",
            estado=estado,
        )

    def test_reportar_avaria_exige_autenticacao(self):
        self.client.logout()

        resposta = self.client.get(reverse("equipamentos:reportar_avaria"))

        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("contas:login"), resposta["Location"])

    def test_reportar_avaria_geral_cria_avaria_pendente(self):
        resposta = self.client.post(
            reverse("equipamentos:reportar_avaria"),
            {
                "equipamento": self.equipamento.pk,
                "descricao": "O ecrã não acende.",
                "prioridade": "urgente",
            },
        )

        self.assertRedirects(
            resposta, reverse("equipamentos:minhas_avarias")
        )

        avaria = Avaria.objects.get()
        self.assertEqual(avaria.equipamento, self.equipamento)
        self.assertEqual(avaria.reportado_por, self.utilizador)
        self.assertEqual(avaria.estado, "pendente")
        self.assertEqual(avaria.descricao, "O ecrã não acende.")
        self.assertEqual(avaria.prioridade, "urgente")

        self.equipamento.refresh_from_db()
        self.assertEqual(self.equipamento.estado, "avariado")

    def test_reportar_avaria_de_equipamento_cria_avaria_pendente(self):
        resposta = self.client.post(
            reverse(
                "equipamentos:reportar_avaria_equipamento",
                kwargs={"pk": self.equipamento.pk},
            ),
            {
                "equipamento": self.equipamento.pk,
                "descricao": "Teclado sem resposta.",
                "prioridade": "media",
            },
        )

        self.assertRedirects(
            resposta, reverse("equipamentos:minhas_avarias")
        )

        avaria = Avaria.objects.get()
        self.assertEqual(avaria.equipamento, self.equipamento)
        self.assertEqual(avaria.reportado_por, self.utilizador)
        self.assertEqual(avaria.estado, "pendente")

    def test_reportar_avaria_de_equipamento_usa_o_pk_do_url(self):
        resposta = self.client.post(
            reverse(
                "equipamentos:reportar_avaria_equipamento",
                kwargs={"pk": self.equipamento.pk},
            ),
            {
                "descricao": "Falha intermitente de rede.",
                "prioridade": "baixa",
            },
        )

        self.assertRedirects(
            resposta, reverse("equipamentos:minhas_avarias")
        )
        self.assertEqual(
            Avaria.objects.get().equipamento,
            self.equipamento,
        )

    def test_reportar_avaria_de_equipamento_rejeita_abatido(self):
        self.equipamento.estado = "abatido"
        self.equipamento.save(update_fields=["estado"])

        resposta = self.client.post(
            reverse(
                "equipamentos:reportar_avaria_equipamento",
                kwargs={"pk": self.equipamento.pk},
            ),
            {
                "equipamento": self.equipamento.pk,
                "descricao": "Não deve ser criada.",
                "prioridade": "baixa",
            },
            follow=True,
        )

        self.assertRedirects(
            resposta,
            reverse(
                "equipamentos:equipamento_detalhe",
                kwargs={"pk": self.equipamento.pk},
            ),
        )
        self.assertContains(resposta, "equipamento abatido")
        self.assertEqual(Avaria.objects.count(), 0)

    def test_reportar_avaria_rejeita_equipamento_diferente_do_url(self):
        resposta = self.client.post(
            reverse(
                "equipamentos:reportar_avaria_equipamento",
                kwargs={"pk": self.equipamento.pk},
            ),
            {
                "equipamento": self.outro_equipamento.pk,
                "descricao": "Tentativa com outro equipamento.",
                "prioridade": "media",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "não correspondem ao pedido")
        self.assertEqual(Avaria.objects.count(), 0)

    def test_minhas_avarias_mostra_apenas_as_do_utilizador(self):
        minha = self._criar_avaria()
        alheia = self._criar_avaria(reportado_por=self.tecnico)
        alheia.descricao = "Avaria reportada por outra pessoa"
        alheia.save(update_fields=["descricao"])

        resposta = self.client.get(reverse("equipamentos:minhas_avarias"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, f"#{minha.pk}")
        self.assertNotContains(resposta, "Avaria reportada por outra pessoa")

    def test_avaria_detalhe_mostra_formulario_ao_tecnico_atribuido(self):
        avaria = self._criar_avaria(tecnico=self.tecnico)
        self.client.force_login(self.tecnico)

        resposta = self.client.get(
            reverse(
                "equipamentos:avaria_detalhe",
                kwargs={"pk": avaria.pk},
            )
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Registar intervenção")
        self.assertContains(resposta, 'name="detalhes_reparacao"')

    def test_avaria_detalhe_nao_mostra_formulario_a_outro_utilizador(self):
        avaria = self._criar_avaria(tecnico=self.tecnico)

        resposta = self.client.get(
            reverse(
                "equipamentos:avaria_detalhe",
                kwargs={"pk": avaria.pk},
            )
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(resposta, "Registar intervenção")

    def test_registar_intervencao_guarda_tecnico_autenticado(self):
        avaria = self._criar_avaria(tecnico=self.tecnico)
        self.client.force_login(self.tecnico)

        resposta = self.client.post(
            reverse(
                "equipamentos:registar_intervencao",
                kwargs={"pk": avaria.pk},
            ),
            {
                "detalhes_reparacao": "Substituída a memória RAM.",
                "pecas_substituidas": "RAM 8GB",
            },
        )

        self.assertRedirects(
            resposta,
            reverse(
                "equipamentos:avaria_detalhe",
                kwargs={"pk": avaria.pk},
            ),
        )

        intervencao = Intervencao.objects.get(avaria=avaria)
        self.assertEqual(intervencao.tecnico, self.tecnico)
        self.assertEqual(
            intervencao.detalhes_reparacao, "Substituída a memória RAM."
        )
        self.assertEqual(intervencao.pecas_substituidas, "RAM 8GB")

    def test_registar_intervencao_rejeita_utilizador_comum(self):
        avaria = self._criar_avaria(tecnico=self.tecnico)

        resposta = self.client.post(
            reverse(
                "equipamentos:registar_intervencao",
                kwargs={"pk": avaria.pk},
            ),
            {"detalhes_reparacao": "Tentativa sem permissões."},
        )

        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(Intervencao.objects.count(), 0)

    def test_assumir_avaria_inicia_reparacao_e_atualiza_equipamento(self):
        avaria = self._criar_avaria()
        self.client.force_login(self.tecnico)

        resposta = self.client.post(
            reverse(
                "equipamentos:avaria_assumir",
                kwargs={"pk": avaria.pk},
            )
        )

        self.assertEqual(resposta.status_code, 302)

        avaria.refresh_from_db()
        self.equipamento.refresh_from_db()
        self.assertEqual(avaria.tecnico_atribuido, self.tecnico)
        self.assertEqual(avaria.estado, "em_reparacao")
        self.assertEqual(self.equipamento.estado, "manutencao")

        historico = self.equipamento.historico_estados.first()
        self.assertEqual(historico.estado_novo, "manutencao")
        self.assertEqual(historico.alterado_por, self.tecnico)

    def test_corrigir_estado_admin_regista_historico_manual(self):
        self.equipamento.estado = "abatido"
        self.equipamento.save(update_fields=["estado"])
        self.client.force_login(self.admin)

        resposta = self.client.post(
            reverse(
                "equipamentos:corrigir_estado",
                kwargs={"pk": self.equipamento.pk},
            ),
            {
                "estado": "operacional",
                "motivo": "Equipamento reparado e devolvido ao serviço.",
            },
        )

        self.assertRedirects(
            resposta,
            reverse(
                "equipamentos:equipamento_detalhe",
                kwargs={"pk": self.equipamento.pk},
            ),
        )

        self.equipamento.refresh_from_db()
        self.assertEqual(self.equipamento.estado, "operacional")

        historico = HistoricoEstadoEquipamento.objects.get(
            equipamento=self.equipamento
        )
        self.assertEqual(historico.origem, "manual")
        self.assertEqual(historico.alterado_por, self.admin)
        self.assertEqual(
            historico.motivo,
            "Equipamento reparado e devolvido ao serviço.",
        )

    def test_corrigir_estado_exige_motivo(self):
        self.equipamento.estado = "abatido"
        self.equipamento.save(update_fields=["estado"])
        self.client.force_login(self.admin)

        resposta = self.client.post(
            reverse(
                "equipamentos:corrigir_estado",
                kwargs={"pk": self.equipamento.pk},
            ),
            {"estado": "operacional", "motivo": ""},
        )

        self.assertRedirects(
            resposta,
            reverse(
                "equipamentos:equipamento_detalhe",
                kwargs={"pk": self.equipamento.pk},
            ),
        )

        self.equipamento.refresh_from_db()
        self.assertEqual(self.equipamento.estado, "abatido")
        self.assertEqual(
            HistoricoEstadoEquipamento.objects.filter(
                equipamento=self.equipamento
            ).count(),
            0,
        )

    def test_corrigir_estado_rejeita_tecnico(self):
        self.client.force_login(self.tecnico)

        resposta = self.client.post(
            reverse(
                "equipamentos:corrigir_estado",
                kwargs={"pk": self.equipamento.pk},
            ),
            {"estado": "operacional", "motivo": "Sem autorização."},
        )

        self.assertEqual(resposta.status_code, 403)

import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from contas.models import Perfil
from equipamentos.models import (
    Avaria,
    Equipamento,
    Intervencao,
    recalcular_estado_equipamento,
)

PASSWORD_DEMO = os.environ.get("DEMO_PASSWORD", "demo123")

UTILIZADORES_DEMO = (
    {
        "username": "admin",
        "papel": "admin",
        "telefone": "840000001",
        "superuser": True,
    },
    {
        "username": "tecnico1",
        "papel": "tecnico",
        "telefone": "840000002",
        "superuser": False,
    },
    {
        "username": "utilizador1",
        "papel": "utilizador",
        "telefone": "840000003",
        "superuser": False,
    },
)

EQUIPAMENTOS_DEMO = (
    ("UCM-FEG-PC-01", "computador", "Dell OptiPlex 7090", "Laboratório de Informática 1"),
    ("UCM-FEG-PC-02", "computador", "HP EliteDesk 800 G6", "Laboratório de Informática 1"),
    ("UCM-FEG-PC-03", "computador", "Lenovo ThinkCentre M720", "Laboratório de Informática 2"),
    ("UCM-FEG-LT-01", "laptop", "Lenovo ThinkPad T14", "Sala 12"),
    ("UCM-FEG-LT-02", "laptop", "HP ProBook 450 G8", "Sala 12"),
    ("UCM-FEG-LT-03", "laptop", "Dell Latitude 5420", "Biblioteca"),
    ("UCM-FEG-PR-01", "projetor", "Epson EB-X51", "Sala 3"),
    ("UCM-FEG-PR-02", "projetor", "BenQ MX560", "Sala 7"),
    ("UCM-FEG-PR-03", "projetor", "Sony VPL-EX455", "Auditório"),
    ("UCM-FEG-IM-01", "impressora", "HP LaserJet Pro M404dn", "Secretaria"),
    ("UCM-FEG-IM-02", "impressora", "Canon i-SENSYS MF421dw", "Secretaria"),
    ("UCM-FEG-IM-03", "impressora", "Brother HL-L2350DW", "Reprografia"),
    ("UCM-FEG-OU-01", "outro", "Router Cisco RV340", "Sala Técnica"),
    ("UCM-FEG-OU-02", "outro", "Switch TP-Link TL-SG1024", "Sala Técnica"),
    ("UCM-FEG-OU-03", "outro", "Webcam Logitech C920", "Laboratório de Informática 2"),
)

AVARIAS_DEMO = (
    {
        "codigo": "UCM-FEG-PC-01",
        "descricao": "O computador não liga; o LED da fonte pisca.",
        "prioridade": "alta",
        "estado": "pendente",
        "reportado_por": "utilizador1",
        "tecnico_atribuido": None,
    },
    {
        "codigo": "UCM-FEG-PC-02",
        "descricao": "Rato e teclado deixam de responder após alguns minutos.",
        "prioridade": "media",
        "estado": "pendente",
        "reportado_por": "utilizador1",
        "tecnico_atribuido": None,
    },
    {
        "codigo": "UCM-FEG-PC-03",
        "descricao": "Disco com setores defeituosos; o sistema reinicia sozinho.",
        "prioridade": "urgente",
        "estado": "em_reparacao",
        "reportado_por": "admin",
        "tecnico_atribuido": "tecnico1",
    },
    {
        "codigo": "UCM-FEG-LT-01",
        "descricao": "Bateria não carrega e o portátil desliga sem aviso.",
        "prioridade": "alta",
        "estado": "em_reparacao",
        "reportado_por": "utilizador1",
        "tecnico_atribuido": "tecnico1",
    },
    {
        "codigo": "UCM-FEG-LT-02",
        "descricao": "Teclado com teclas presas; substituído o teclado.",
        "prioridade": "media",
        "estado": "resolvido",
        "reportado_por": "utilizador1",
        "tecnico_atribuido": "tecnico1",
        "intervencao": {
            "detalhes": "Teclado substituído e testado com o sistema operativo.",
            "pecas": "Teclado HP ProBook 450 G8",
        },
    },
    {
        "codigo": "UCM-FEG-LT-03",
        "descricao": "Ventoinha ruidosa; limpeza e lubrificação.",
        "prioridade": "baixa",
        "estado": "resolvido",
        "reportado_por": "utilizador1",
        "tecnico_atribuido": "tecnico1",
        "intervencao": {
            "detalhes": "Limpeza interna e lubrificação da ventoinha.",
            "pecas": "",
        },
    },
    {
        "codigo": "UCM-FEG-PR-01",
        "descricao": "Lâmpada do projetor fundida; substituída.",
        "prioridade": "alta",
        "estado": "resolvido",
        "reportado_por": "admin",
        "tecnico_atribuido": "tecnico1",
        "intervencao": {
            "detalhes": "Substituída a lâmpada do projetor e ajustado o foco.",
            "pecas": "Lâmpada Epson ELPLP96",
        },
    },
    {
        "codigo": "UCM-FEG-PR-02",
        "descricao": "Pedido duplicado para o mesmo problema.",
        "prioridade": "baixa",
        "estado": "cancelado",
        "reportado_por": "utilizador1",
        "tecnico_atribuido": None,
    },
    {
        "codigo": "UCM-FEG-PR-03",
        "descricao": "Equipamento deixou de apresentar a falha durante o diagnóstico.",
        "prioridade": "media",
        "estado": "cancelado",
        "reportado_por": "tecnico1",
        "tecnico_atribuido": None,
    },
    {
        "codigo": "UCM-FEG-IM-01",
        "descricao": "Impressora puxa várias folhas ao mesmo tempo.",
        "prioridade": "baixa",
        "estado": "pendente",
        "reportado_por": "utilizador1",
        "tecnico_atribuido": None,
    },
)


class Command(BaseCommand):
    help = "Cria utilizadores, equipamentos, avarias e intervenções de demonstração."

    def handle(self, *args, **options):
        utilizadores = {}
        criados = {"utilizadores": 0, "equipamentos": 0, "avarias": 0, "intervencoes": 0}
        existentes = dict.fromkeys(criados, 0)

        for dados in UTILIZADORES_DEMO:
            utilizador, foi_criado = self._garantir_utilizador(
                username=dados["username"],
                papel=dados["papel"],
                telefone=dados["telefone"],
                superuser=dados["superuser"],
            )
            utilizadores[dados["username"]] = utilizador
            self._contabilizar(criados, existentes, "utilizadores", foi_criado)

        equipamentos = {}
        for codigo, tipo, marca_modelo, localizacao in EQUIPAMENTOS_DEMO:
            equipamento, foi_criado = Equipamento.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "tipo": tipo,
                    "marca_modelo": marca_modelo,
                    "localizacao": localizacao,
                    "estado": "operacional",
                },
            )
            equipamentos[codigo] = equipamento
            self._contabilizar(criados, existentes, "equipamentos", foi_criado)

        for dados in AVARIAS_DEMO:
            equipamento = equipamentos[dados["codigo"]]
            avaria, foi_criada = Avaria.objects.get_or_create(
                equipamento=equipamento,
                descricao=dados["descricao"],
                defaults={
                    "reportado_por": utilizadores[dados["reportado_por"]],
                    "tecnico_atribuido": (
                        utilizadores[dados["tecnico_atribuido"]]
                        if dados["tecnico_atribuido"]
                        else None
                    ),
                    "prioridade": dados["prioridade"],
                    "estado": dados["estado"],
                },
            )
            self._contabilizar(criados, existentes, "avarias", foi_criada)

            if dados.get("intervencao"):
                intervencao_dados = dados["intervencao"]
                _, intervencao_criada = Intervencao.objects.get_or_create(
                    avaria=avaria,
                    tecnico=utilizadores["tecnico1"],
                    detalhes_reparacao=intervencao_dados["detalhes"],
                    defaults={"pecas_substituidas": intervencao_dados["pecas"]},
                )
                self._contabilizar(
                    criados,
                    existentes,
                    "intervencoes",
                    intervencao_criada,
                )

        corrigidos = self._verificar_estados(equipamentos.values())

        self.stdout.write(self.style.SUCCESS("Dados de demonstração prontos."))
        self.stdout.write(
            "Utilizadores: {criados} criados, {existentes} já existiam".format(
                criados=criados["utilizadores"],
                existentes=existentes["utilizadores"],
            )
        )
        self.stdout.write(
            "Equipamentos: {criados} criados, {existentes} já existiam".format(
                criados=criados["equipamentos"],
                existentes=existentes["equipamentos"],
            )
        )
        self.stdout.write(
            "Avarias: {criados} criadas, {existentes} já existiam".format(
                criados=criados["avarias"],
                existentes=existentes["avarias"],
            )
        )
        self.stdout.write(
            "Intervenções: {criados} criadas, {existentes} já existiam".format(
                criados=criados["intervencoes"],
                existentes=existentes["intervencoes"],
            )
        )
        self.stdout.write(
            "Estados dos equipamentos verificados; correções aplicadas: "
            f"{corrigidos}."
        )

        if PASSWORD_DEMO == "demo123":
            self.stdout.write(
                self.style.WARNING(
                    "AVISO: a palavra-passe de demonstração está a usar o valor "
                    "por defeito (demo123). Defina a variável de ambiente "
                    "DEMO_PASSWORD em produção."
                )
            )

    def _garantir_utilizador(self, username, papel, telefone, superuser):
        utilizador, foi_criado = User.objects.get_or_create(
            username=username,
            defaults={
                "email": f"{username}@demo.ucm.ac.mz",
                "is_staff": superuser,
                "is_superuser": superuser,
            },
        )

        alterado = False
        if foi_criado:
            utilizador.set_password(PASSWORD_DEMO)
            alterado = True

        if superuser and (not utilizador.is_staff or not utilizador.is_superuser):
            utilizador.is_staff = True
            utilizador.is_superuser = True
            alterado = True

        if alterado:
            utilizador.save()

        perfil, perfil_criado = Perfil.objects.get_or_create(
            user=utilizador,
            defaults={"papel": papel, "telefone": telefone},
        )
        alterado = False
        if not perfil_criado and perfil.papel != papel:
            perfil.papel = papel
            alterado = True
        if not perfil.telefone and telefone:
            perfil.telefone = telefone
            alterado = True
        if alterado:
            perfil.save()

        return utilizador, foi_criado

    def _contabilizar(self, criados, existentes, chave, foi_criado):
        if foi_criado:
            criados[chave] += 1
        else:
            existentes[chave] += 1

    def _verificar_estados(self, equipamentos):
        """Confirma que cada equipamento reflete as avarias ainda abertas."""
        corrigidos = 0
        for equipamento in equipamentos:
            equipamento.refresh_from_db()
            if equipamento.estado == "abatido":
                continue

            if equipamento.avarias.filter(estado="em_reparacao").exists():
                esperado = "manutencao"
            elif equipamento.avarias.filter(estado="pendente").exists():
                esperado = "avariado"
            else:
                esperado = "operacional"

            if equipamento.estado != esperado:
                recalcular_estado_equipamento(equipamento)
                corrigidos += 1

        return corrigidos

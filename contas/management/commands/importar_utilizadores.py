import csv
import re
from pathlib import Path

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.utils.crypto import get_random_string

from contas.adapters import dominio_email_permitido
from contas.models import Perfil


class Command(BaseCommand):
    help = (
        "Cria ou actualiza utilizadores a partir de um CSV com as colunas "
        "nome, email e papel."
    )

    def add_arguments(self, parser):
        parser.add_argument("ficheiro", help="Caminho para o ficheiro CSV.")
        parser.add_argument(
            "--sem-password",
            action="store_true",
            help=(
                "Define uma palavra-passe inutilizável para os utilizadores "
                "importados (adequado a quem entra apenas por Google)."
            ),
        )

    def handle(self, *args, **options):
        caminho = Path(options["ficheiro"])
        if not caminho.is_file():
            raise CommandError(f"Ficheiro não encontrado: {caminho}")

        linhas = self._ler_e_validar(caminho)
        criados = 0
        actualizados = 0
        passwords = []

        for linha in linhas:
            email = linha["email"]
            utilizador = User.objects.filter(email__iexact=email).first()
            criado = utilizador is None

            if criado:
                utilizador = User(
                    username=self._username_disponivel(email),
                    email=email,
                )
                if options["sem_password"]:
                    utilizador.set_unusable_password()
                else:
                    password = get_random_string(16)
                    utilizador.set_password(password)
                    passwords.append((email, password))
                criados += 1
            else:
                if options["sem_password"]:
                    utilizador.set_unusable_password()
                actualizados += 1

            utilizador.email = email
            utilizador.first_name = linha["first_name"]
            utilizador.last_name = linha["last_name"]
            utilizador.save()

            perfil, _ = Perfil.objects.get_or_create(user=utilizador)
            if perfil.papel != linha["papel"]:
                perfil.papel = linha["papel"]
                perfil.save(update_fields=["papel"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Importação concluída: {criados} criado(s), "
                f"{actualizados} actualizado(s)."
            )
        )

        if options["sem_password"]:
            self.stdout.write(
                "Os utilizadores importados têm palavra-passe inutilizável "
                "(entrada apenas por Google)."
            )
        elif passwords:
            self.stdout.write("Palavras-passe geradas:")
            for email, password in passwords:
                self.stdout.write(f"  {email}: {password}")

    def _ler_e_validar(self, caminho):
        papeis_validos = {papel for papel, _ in Perfil.PAPEL_CHOICES}
        linhas = []

        with caminho.open(encoding="utf-8-sig", newline="") as ficheiro:
            leitor = csv.DictReader(ficheiro)
            colunas = {
                (coluna or "").strip().lower()
                for coluna in (leitor.fieldnames or [])
            }
            em_falta = {"nome", "email", "papel"} - colunas
            if em_falta:
                raise CommandError(
                    "O CSV tem de conter as colunas: "
                    + ", ".join(sorted(em_falta))
                )

            for numero, registo in enumerate(leitor, start=2):
                registo = {
                    (chave or "").strip().lower(): (valor or "").strip()
                    for chave, valor in registo.items()
                }
                nome = registo.get("nome", "")
                email = registo.get("email", "").lower()
                papel = registo.get("papel", "").lower()

                if not nome:
                    raise CommandError(f"Linha {numero}: o nome está vazio.")

                try:
                    validate_email(email)
                except ValidationError:
                    raise CommandError(
                        f"Linha {numero}: email inválido ({email!r})."
                    ) from None

                if not dominio_email_permitido(email):
                    raise CommandError(
                        f"Linha {numero}: o domínio de {email!r} não está "
                        "autorizado."
                    )

                if papel not in papeis_validos:
                    raise CommandError(
                        f"Linha {numero}: papel inválido ({papel!r}). "
                        "Use um de: " + ", ".join(sorted(papeis_validos))
                    )

                partes_nome = nome.split()
                linhas.append(
                    {
                        "email": email,
                        "papel": papel,
                        "first_name": partes_nome[0],
                        "last_name": " ".join(partes_nome[1:]),
                    }
                )

        if not linhas:
            raise CommandError("O CSV não tem linhas de dados.")

        return linhas

    @staticmethod
    def _username_disponivel(email):
        local = email.split("@", 1)[0]
        base = re.sub(r"[^a-zA-Z0-9.@+_-]", "", local)[:140]
        base = base or "utilizador"
        username = base
        contador = 2

        while User.objects.filter(username__iexact=username).exists():
            sufixo = f"_{contador}"
            username = f"{base[:150 - len(sufixo)]}{sufixo}"
            contador += 1

        return username

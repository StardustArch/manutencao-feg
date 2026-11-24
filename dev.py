#!/usr/bin/env python3
"""
dev.py — Arranque rápido do projecto (Linux e Windows).

Faz, automaticamente:
  1. Cria o .venv se não existir
  2. Instala as dependências do requirements.txt (só quando o venv é criado,
     ou forçado com --install) — poupa dados móveis!
  3. (opcional) migrações e seed
  4. Sobe o runserver

Uso:
  python dev.py                      # cria venv (se falta) + deps (1ª vez) + runserver
  python dev.py --install            # reinstala as dependências
  python dev.py --migrate --seed     # corre migrações e o seed antes de subir
  python dev.py --host 0.0.0.0       # acessível pela rede (ex.: hotspot do telemóvel)
  python dev.py --port 8080
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
VENV_DIR = PROJECT_DIR / ".venv"
REQUIREMENTS = PROJECT_DIR / "requirements.txt"
MANAGE = PROJECT_DIR / "manage.py"

ENV_FILES = [PROJECT_DIR / ".env", PROJECT_DIR / ".env.dev"]


def load_env() -> None:
    """Carrega variáveis de ambiente de ficheiros .env (sem sobrescrever
    o ambiente do sistema operativo / shell existente)."""
    for env_file in ENV_FILES:
        if not env_file.exists():
            continue
        print(f">> A carregar variáveis de ambiente de {env_file.name}")
        for linha in env_file.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, _, valor = linha.partition("=")
            chave = chave.strip()
            valor = valor.strip().strip('"').strip("'")
            if chave and chave not in os.environ:
                os.environ[chave] = valor
        break  # carrega apenas o primeiro ficheiro que encontrar (.env tem prioridade)


def venv_python() -> Path:
    """Caminho do Python dentro do venv, conforme o sistema operativo."""
    if os.name == "nt":  # Windows
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def run(cmd: list[str], **kwargs) -> None:
    print(f"$ {' '.join(str(c) for c in cmd)}\n", flush=True)
    subprocess.run([str(c) for c in cmd], cwd=PROJECT_DIR, check=True, **kwargs)


def create_venv() -> None:
    print(">> A criar o virtual environment (.venv)...")
    run([sys.executable, "-m", "venv", str(VENV_DIR)])


def install_deps() -> None:
    if not REQUIREMENTS.exists():
        sys.exit(f"Erro: não encontrei {REQUIREMENTS}")
    py = venv_python()
    run([py, "-m", "pip", "install", "--upgrade", "pip"])
    run([py, "-m", "pip", "install", "-r", str(REQUIREMENTS)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Arranque rápido do projecto Django.")
    parser.add_argument("--install", action="store_true",
                        help="Força a reinstalação das dependências")
    parser.add_argument("--migrate", action="store_true",
                        help="Corre 'migrate' antes de subir o servidor")
    parser.add_argument("--seed", action="store_true",
                        help="Corre o comando de seed antes de subir o servidor")
    parser.add_argument("--seed-cmd", default="seed_demo",
                        help="Nome do comando de seed (default: seed_demo)")
    parser.add_argument("--host", default="127.0.0.1", help="Host do runserver")
    parser.add_argument("--port", default="8000", help="Porta do runserver")
    args = parser.parse_args()

    py = venv_python()

    # 0. Injeta variáveis de ambiente do .env / .env.dev (antes de tudo)
    load_env()

    # 1. Criar o venv se não existir
    if not py.exists():
        create_venv()
        install_deps()          # só instala deps na 1ª criação (poupa dados móveis)
    elif args.install:
        install_deps()

    # 2. Opcionais: migrações / seed
    if args.migrate:
        run([py, MANAGE, "migrate"])
    if args.seed:
        run([py, MANAGE, args.seed_cmd])

    # 3. Subir o servidor
    print(f"\n>> Servidor em http://{args.host}:{args.port} — Ctrl+C para parar.\n")
    try:
        run([py, MANAGE, "runserver", f"{args.host}:{args.port}"])
    except KeyboardInterrupt:
        print("\n>> Servidor parado.")


if __name__ == "__main__":
    main()
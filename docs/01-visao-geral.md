# 01. Visão geral do sistema

> **Regra de elaboração:** este documento contém apenas factos extraídos do código-fonte do projecto. Quando algo não existe no código, escreve-se "NÃO EXISTE". Nenhum ficheiro de código foi alterado.

## 1. Objectivo do sistema

O **Sistema de Manutenção de Equipamentos — UCM-FEG** é uma aplicação web (Django) para inventariar equipamentos e gerir o respetivo ciclo de manutenção no Laboratório de Informática da Faculdade de Engenharia (FEG) da Universidade Católica de Moçambique (UCM).

Funcionalidades centrais, extraídas do código (`equipamentos/views.py`, `equipamentos/models.py`, `README.md`):

- Inventariar equipamentos com código de património, tipo, marca/modelo, localização e estado.
- Reportar avarias, com descrição e prioridade, por formulário geral ou pelo QR code de um equipamento.
- Atribuir técnicos, assumir avarias e alterar estados dentro de um fluxo permitido (pendente → em reparação → resolvido).
- Registar intervenções técnicas (detalhes da reparação e peças substituídas).
- Sincronizar automaticamente o estado do equipamento com as avarias ainda abertas (via `recalcular_estado_equipamento`).
- Corrigir manualmente o estado de um equipamento (apenas administrador), com motivo obrigatório e registo de histórico.
- Consultar avarias reportadas pelo próprio utilizador ("minhas avarias").
- Consultar dashboard com métricas e gráficos (estado dos equipamentos e estado das avarias).
- Exportar relatórios PDF (inventário e avarias) via ReportLab.
- Gerar e imprimir etiquetas A4 com QR codes (3 colunas × 8 linhas = 24 etiquetas por folha).
- Autenticação por palavra-passe e login social Google restrito a domínios institucionais (`allauth`).

## 2. Perfis de utilizador

Definidos em `contas/models.py` (modelo `Perfil`, campo `papel`):

| Papel (valor BD) | Rótulo no código | Descrição |
|---|---|---|
| `utilizador` | Utilizador / Docente / Estudante | Perfil padrão, criado por sinal quando um `User` é criado. |
| `tecnico` | Técnico de Manutenção | Pode gerir avarias, assumi-las, registar intervenções, ver dashboard e etiquetas. |
| `admin` | Administrador | Pode corrigir manualmente estados de equipamento e gerir qualquer avaria. |

Contas de demonstração criadas pelo comando `seed_demo` (`equipamentos/management/commands/seed_demo.py`, `README.md`):

| Utilizador | Password | Perfil | `is_superuser` |
|---|---|---|---|
| `admin` | `demo123` | admin | Sim |
| `tecnico1` | `demo123` | tecnico | Não |
| `utilizador1` | `demo123` | utilizador | Não |

O sinal `contas.signals.criar_ou_atualizar_perfil_utilizador` (`post_save` sobre `User`) cria automaticamente um `Perfil` para cada utilizador novo.

## 3. Stack e versões (extraídas de `requirements.txt`)

| Componente | Versão (requirements.txt) | Versão instalada (verificada com pip) |
|---|---|---|
| Python | 3.12+ (indicado no README e pyrightconfig) | 3.12.3 |
| Django | 6.1.2 | 6.1.2 |
| django-allauth[socialaccount] | 65.21.1 | 65.21.1 |
| sqlparse | 0.6.1 | 0.6.1 |
| tzdata | 2026.6 | 2026.6 |
| qrcode[pil] | 8.2 | 8.2 |
| Pillow | 13.0.0 | 13.0.0 |
| reportlab | 5.1.0 | 5.1.0 |
| asgiref | 3.13.0 | 3.13.0 |

Bibliotecas locais (vendored em `static/vendor/`), não listadas no `requirements.txt`:
- Bootstrap CSS/JS (local)
- Bootstrap Icons (local)
- HTMX (local)
- Chart.js (local)

Base de dados: **SQLite** (`db.sqlite3`), configurado em `config/settings.py` (`ENGINE: django.db.backends.sqlite3`, `NAME: BASE_DIR / 'db.sqlite3'`). O README indica que é a base de dados de desenvolvimento.

Fuso horário e idioma (`config/settings.py`): `LANGUAGE_CODE = 'pt-pt'`, `TIME_ZONE = 'Africa/Maputo'`, `USE_TZ = True`.

Nota sobre inconsistência documental: o README menciona "Pico CSS (interface)", mas os templates carregam efetivamente **Bootstrap local** (`static/vendor/bootstrap/css/bootstrap.min.css`) mais `static/css/ucm-theme.css`. Não existe ficheiro Pico CSS no projeto.

## 4. Estrutura de pastas (comentada)

```
manutencao/                     # Raiz do projeto Django
├── config/                     # Pacote de configuração do projeto (settings, URLs, WSGI/ASGI)
│   ├── settings.py             # Configurações Django (BD SQLite, apps, middleware, allauth, SITE_URL, ALLOWED_HOSTS)
│   ├── urls.py                 # URLs raiz: admin/, accounts/ (allauth), contas/, equipamentos/, home
│   ├── asgi.py / wsgi.py       # Ponto de entrada ASGI/WSGI
│   └── __init__.py
├── contas/                     # App de autenticação e perfis
│   ├── models.py               # Perfil (user 1:1, papel, telefone)
│   ├── signals.py              # Sinal post_save User -> cria Perfil automaticamente
│   ├── adapters.py             # ContasSocialAccountAdapter (valida domínio/email verificado no login Google)
│   ├── views.py                # dashboard_redirect, login/logout (auth_views)
│   ├── urls.py                 # contas/login/, contas/logout/
│   ├── context_processors.py   # google_oauth (mostra botão Google só se credenciais configuradas)
│   ├── admin.py                # PerfilAdmin (papel editável na listagem)
│   ├── management/commands/importar_utilizadores.py  # Importação em massa de utilizadores por CSV
│   ├── migrations/             # 0001_initial, 0002_site_inicial
│   └── tests.py                # Testes do login Google e importação
├── equipamentos/               # App principal do inventário e manutenção
│   ├── models.py               # Equipamento, Avaria, Intervencao, HistoricoEstadoEquipamento + recalcular_estado_equipamento
│   ├── views.py                # Todas as views de negócio + decorators de permissão
│   ├── urls.py                 # Rotas do app (namespace equipamentos)
│   ├── forms.py                # AvariaForm, IntervencaoForm, CorrigirEstadoForm
│   ├── admin.py                # Admin de Equipamento, Avaria, HistoricoEstadoEquipamento, Intervencao
│   ├── relatorios.py           # Geração de relatórios PDF (ReportLab)
│   ├── management/commands/seed_demo.py  # Dados de demonstração idempotentes
│   ├── migrations/             # 0001_initial, 0002_historicoestadoequipamento
│   └── tests.py                # 56 testes da aplicação
├── static/                     # Ficheiros estáticos locais (sem CDN)
│   ├── css/ucm-theme.css       # Tema UCM (cores primárias, botões, navbar, cards)
│   ├── img/logo-ucm.png        # Logótipo UCM
│   └── vendor/                 # Bibliotecas frontend locais: bootstrap, bootstrap-icons, chartjs, htmx
├── templates/                  # Templates Django
│   ├── base.html               # Template base (Navbar UCM, topbar, mensagens)
│   ├── contas/                 # home.html, login.html
│   └── equipamentos/           # Listas, fichas, dashboard, etiquetas, reporte, partials
├── db.sqlite3                  # Base de dados de desenvolvimento (ignorada pelo git via .gitignore)
├── manage.py                   # CLI do Django
├── requirements.txt            # Dependências Python
├── pyrightconfig.json          # Configuração Pyright (venv .venv, Python 3.12)
├── .gitignore                  # Ignora .venv, __pycache__, db.sqlite3, staticfiles, media, etc.
└── README.md                   # Documentação de utilizador do projeto
```

## 5. Como instalar e correr

Passos extraídos do `README.md` e verificados no código:

1. Clonar o repositório e entrar na pasta:
   ```bash
   git clone <URL_DO_REPOSITORIO> manutencao && cd manutencao
   ```

2. Criar e ativar o ambiente virtual (Python 3.12):
   ```bash
   python -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

3. Aplicar migrações:
   ```bash
   .venv/bin/python manage.py migrate
   ```

4. (Opcional) Carregar dados de demonstração (idempotente):
   ```bash
   .venv/bin/python manage.py seed_demo
   ```

5. Executar o servidor de desenvolvimento:
   ```bash
   .venv/bin/python manage.py runserver
   ```

   A aplicação fica disponível em `http://127.0.0.1:8000/`.

6. Para o QR code funcionar na rede local, o servidor deve escutar em todas as interfaces e o `SITE_URL` deve apontar para o IP público da máquina (extraído do `README.md`):
   ```bash
   SITE_URL=http://192.168.1.10:8000 .venv/bin/python manage.py runserver 0.0.0.0:8000
   ```
   Se o Django rejeitar o host (`DisallowedHost`), acrescente o IP a `ALLOWED_HOSTS` em `config/settings.py` ou defina a variável `DJANGO_ALLOWED_HOSTS`.

7. Verificar a instalação sem executar testes:
   ```bash
   .venv/bin/python manage.py check
   ```

8. Executar os testes:
   ```bash
   .venv/bin/python manage.py test
   ```

9. (Opcional) Login com Google: configurar `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` no Google Cloud Console e exportá-las como variáveis de ambiente antes de correr o servidor (detalhe completo no `README.md`). Sem estas credenciais, o botão "Entrar com Google" não é mostrado (`contas/context_processors.py`, `templates/contas/login.html`).

## 6. Ficheiros de entrada

- Ponto de entrada WSGI/ASGI: `config/wsgi.py`, `config/asgi.py`.
- Gestão: `manage.py` (define `DJANGO_SETTINGS_MODULE=config.settings`).
- Dependências: `requirements.txt`.

NÃO EXISTE: ficheiro `Dockerfile`, `docker-compose.yml`, ficheiro de `media/`, ficheiro de requisitos de produção separado, ficheiro de configuração de webserver (nginx/Apache), ficheiro `.env` de exemplo.

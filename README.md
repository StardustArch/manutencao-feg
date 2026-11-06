# Sistema de Manutenção de Equipamentos — UCM-FEG

Aplicação web para inventariar equipamentos e gerir o respetivo ciclo de manutenção.
Permite reportar avarias por QR code, atribuir técnicos, registar intervenções e acompanhar estados.
Inclui relatórios PDF, etiquetas A4 imprimíveis e um painel de métricas para a equipa técnica.

## Stack

- **Python 3.12+**
- **Django 6.1**
- **SQLite** (base de dados de desenvolvimento)
- **qrcode + Pillow** (geração dos QR codes)
- **ReportLab** (relatórios PDF)
- **Pico CSS** (interface)

## Instalação

```bash
git clone <URL_DO_REPOSITORIO> manutencao && cd manutencao
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

A aplicação fica disponível em <http://127.0.0.1:8000/>.

## Dados de demonstração

O comando `seed_demo` cria utilizadores, equipamentos, avarias e intervenções de exemplo.
É idempotente: pode ser executado várias vezes sem duplicar registos.

```bash
.venv/bin/python manage.py seed_demo
```

| Utilizador     | Password  | Perfil                        |
|----------------|-----------|-------------------------------|
| `admin`        | `demo123` | Administrador / superutilizador |
| `tecnico1`     | `demo123` | Técnico de manutenção         |
| `utilizador1`  | `demo123` | Utilizador / docente / estudante |

## QR code na rede local

Para que o telemóvel consiga abrir o URL gravado no QR code, o servidor deve escutar
em todas as interfaces e o projeto deve conhecer o endereço IP da máquina:

```bash
SITE_URL=http://192.168.1.10:8000 .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Substitua `192.168.1.10` pelo IP local do computador onde o Django está a correr.
Sem `SITE_URL`, o QR usa o host do pedido que gerou a imagem (comportamento anterior).

Se o Django responder com `DisallowedHost` ao abrir pelo IP da rede, acrescente esse IP
à lista `ALLOWED_HOSTS` em `config/settings.py`.

## Etiquetas A4

Técnicos e administradores podem abrir **Inventário → Etiquetas** para gerar uma folha A4
com 3 colunas × 8 linhas. Cada etiqueta inclui o QR code, o código do equipamento, a
marca/modelo e a localização, com bordas tracejadas para recortar.

A página carrega as imagens dos QR codes a partir do servidor, pelo que é necessária rede
no momento de abrir e imprimir a folha. Depois de impressas, as etiquetas continuam a
apontar para o servidor: o QR só funciona enquanto esse servidor estiver acessível.

## Estrutura do projeto

```text
manutencao/
├── config/                 # Configuração Django (settings, URLs, WSGI/ASGI)
├── contas/                 # Autenticação, perfis e respetivo admin
├── equipamentos/
│   ├── management/commands/
│   │   └── seed_demo.py    # Dados de demonstração idempotentes
│   ├── admin.py            # Gestão de equipamentos, avarias e histórico
│   ├── models.py           # Equipamento, Avaria, Intervenção e Histórico
│   ├── relatorios.py       # Geração dos relatórios PDF
│   ├── tests.py            # Testes da aplicação
│   ├── urls.py             # Rotas do inventário, avarias, QR e etiquetas
│   └── views.py            # Views, permissões e helper de URL absoluto
├── templates/
│   ├── base.html
│   ├── contas/
│   └── equipamentos/       # Listas, fichas, dashboard, etiquetas e PDF
├── manage.py
└── requirements.txt
```

## Funcionalidades por perfil

### Utilizador / Docente / Estudante

- Iniciar sessão e consultar o inventário de equipamentos.
- Abrir a ficha de um equipamento a partir do inventário ou de um QR code.
- Reportar avarias, com descrição e prioridade.
- Consultar as avarias que reportou.
- Acompanhar o estado das avarias e as intervenções realizadas.

### Técnico

- Tudo o que o perfil de utilizador pode fazer.
- Ver a lista de avarias com filtros por estado e prioridade.
- Assumir avarias e alterar o estado dentro do fluxo permitido.
- Registar intervenções nas avarias que lhe estão atribuídas.
- Consultar o dashboard de métricas e exportar relatórios PDF.
- Imprimir a folha de etiquetas A4 com QR codes.

### Administrador

- Tudo o que o perfil de técnico pode fazer.
- Corrigir manualmente o estado de um equipamento, com motivo e histórico.
- Gerir avarias, incluindo a reatribuição de técnicos diretamente na listagem do admin.
- Gerir perfis de utilizador, alterando o papel diretamente na listagem do admin.

## Testes

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py test
```

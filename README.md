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
à lista `ALLOWED_HOSTS` em `config/settings.py` (ou defina `DJANGO_ALLOWED_HOSTS`).

## Login com Google (domínios institucionais)

O login por palavra-passe continua disponível para técnicos e administradores. O botão
**Entrar com Google** aparece por cima desse formulário e só é mostrado quando as
credenciais Google estão configuradas.

### Criar as credenciais no Google Cloud Console

1. Em <https://console.cloud.google.com/>, crie (ou selecione) um projeto.
2. Em **APIs & Services → OAuth consent screen**, escolha o tipo **Externo** e mantenha
   a aplicação em **modo de teste** enquanto não for publicada. Preencha os dados da
   aplicação e adicione os scopes `profile` e `email`. Em **Test users**, acrescente as
   contas Google que vão testar o login.
3. Em **APIs & Services → Credentials → Create credentials → OAuth client ID**, escolha
   **Web application**.
4. Em **Authorized redirect URIs**, acrescente exatamente:
   - `http://localhost:8000/accounts/google/login/callback/`
   - `https://<dominio-de-producao>/accounts/google/login/callback/`
5. Copie o **Client ID** e o **Client secret** para as variáveis de ambiente.

Exemplo de arranque local:

```bash
GOOGLE_CLIENT_ID="....apps.googleusercontent.com" \
GOOGLE_CLIENT_SECRET="...." \
.venv/bin/python manage.py runserver
```

Variáveis disponíveis:

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `GOOGLE_CLIENT_ID` | Sim, para login Google | Client ID da aplicação OAuth. |
| `GOOGLE_CLIENT_SECRET` | Sim, para login Google | Client secret da aplicação OAuth. |
| `ALLOWED_EMAIL_DOMAINS` | Não | Lista de domínios separados por vírgulas. Por omissão: `ucm.ac.mz,estudante.ucm.ac.mz`. |
| `SITE_DOMAIN` | Não | Domínio usado para criar o `Site` inicial (por omissão `localhost:8000`). Pode ser alterado no admin. |
| `DJANGO_ALLOWED_HOSTS` | Não | Lista de hosts adicionais separados por vírgulas. |
| `SITE_URL` | Não | URL público usado nos QR codes. |

A restrição feita pelo parâmetro `hd` do Google é apenas uma sugestão no ecrã de escolha
de conta. A autorização efetiva é validada no servidor: o email tem de estar verificado e
o domínio (texto depois do `@`, comparado de forma exata e sem distinguir maiúsculas) tem
de constar em `ALLOWED_EMAIL_DOMAINS`. Um domínio como `evil-ucm.ac.mz` é rejeitado.

Depois de configurar as credenciais, execute `python manage.py migrate` para criar os
modelos do `allauth` e o registo inicial de `Site`. Em produção, confirme no admin
(**Sites**) que o domínio do site corresponde ao domínio público.

### Limitação do IP da rede local

O Google só aceita como redirect URI, sem HTTPS, endereços de loopback como
`localhost`. Um endereço privado do tipo `http://192.168.1.10:8000/...` não deve ser
usado como redirect URI: além de poder ser recusado pelo Google, o callback abriria no
telemóvel o `localhost` do próprio telemóvel. Para testar a partir de outro dispositivo,
use um domínio público (produção) ou um túnel HTTPS; para testes no próprio computador,
use `http://localhost:8000/`.

## Importação de utilizadores em massa

O comando `importar_utilizadores` lê um CSV com as colunas `nome`, `email` e `papel`
(`utilizador`, `tecnico` ou `admin`). É idempotente e valida o domínio de cada email
contra `ALLOWED_EMAIL_DOMAINS`.

```bash
.venv/bin/python manage.py importar_utilizadores utilizadores.csv
```

Para contas que entram apenas por Google, use `--sem-password` para lhes atribuir uma
palavra-passe inutilizável. Sem essa opção, é gerada uma palavra-passe aleatória para
cada utilizador novo e apresentada no final do comando.

```bash
.venv/bin/python manage.py importar_utilizadores utilizadores.csv --sem-password
```

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

## Demonstração (capturas de ecrã)

As capturas de ecrã abaixo ilustram o sistema na monografia. Os ficheiros estão
na pasta `static/img/`; o nome de cada ficheiro identifica a tela e o perfil a que
se destina. As imagens referenciadas com `![]` já existem no repositório.

| Tela / perfil | Captura |
|---------------|---------|
| Reportar avaria | ![Reportar avaria](static/img/equipamentos_avarias_nova_(Nest%20Hub%20Max).png) |
| Etiquetas A4 (Técnico/Admin) | ![Etiquetas A4](static/img/etiquetas_(Nest%20Hub%20Max).png) |
| Ficha do equipamento | ![Ficha do equipamento](static/img/ficha_equipamentos_1_(Nest%20Hub%20Max).png) |
| Dashboard (Técnico/Admin) | ![Dashboard](static/img/indicadores_equipamentos_dashboard_(Nest%20Hub%20Max).png) |
| Gestão de avarias (Técnico/Admin) | ![Lista de avarias](static/img/lista_equipamentos_avarias_(Nest%20Hub%20Max).png) |

## Testes

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py test
```

## Publicação no PythonAnywhere

O projeto está preparado para ser executado em produção através de variáveis
de ambiente. Em desenvolvimento, todas as variáveis têm valores seguros por
omissão; em produção, defina-as no painel do PythonAnywhere (Web → Security /
Environment variables) ou no ficheiro de ativar do virtualenv.

### Variáveis de ambiente

| Variável | Obrigatória | Descrição | Default |
|----------|-------------|-----------|---------|
| `DJANGO_SECRET_KEY` | Sim, em produção | Chave secreta do Django. Nunca use o valor de default em produção. | valor de desenvolvimento |
| `DJANGO_DEBUG` | Não | `"True"` para modo depuração, `"False"` em produção. | `"True"` |
| `DJANGO_ALLOWED_HOSTS` | Não | Hosts adicionais separados por vírgula. | — |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Não | Origens confiáveis para CSRF, separadas por vírgula (ex: `https://seudominio.pythonanywhere.com`). | — |
| `SITE_URL` | Não | URL público usado nos QR codes (ex: `https://seudominio.pythonanywhere.com`). | vazio (usa o host do pedido) |
| `GOOGLE_CLIENT_ID` | Não, para login Google | Client ID da aplicação OAuth Google. | vazio |
| `GOOGLE_CLIENT_SECRET` | Não, para login Google | Client secret da aplicação OAuth Google. | vazio |
| `ALLOWED_EMAIL_DOMAINS` | Não | Domínios de email permitidos no login Google, separados por vírgula. | `ucm.ac.mz,estudante.ucm.ac.mz` |
| `SITE_DOMAIN` | Não | Domínio inicial do registo `Site`. | `localhost:8000` |
| `DEMO_PASSWORD` | Não | Palavra-passe das contas de demonstração do `seed_demo`. | `demo123` |

Quando `DJANGO_DEBUG=False`, são ativadas automaticamente:
- `SESSION_COOKIE_SECURE` e `CSRF_COOKIE_SECURE` (cookies apenas sobre HTTPS);
- `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` (necessário atrás do proxy do PythonAnywhere);
- `SECURE_SSL_REDIRECT` (força HTTPS).

### Passos no PythonAnywhere

1. Crie um web app do tipo "WSGI" com a versão do Python desejada (3.12).
2. Crie um virtualenv e instale as dependências:
   ```bash
   python -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```
3. Faça upload/clonagem do repositório (sem a pasta `.venv` nem `db.sqlite3`, que não estão no Git).
4. Aplique as migrações e carregue dados de demonstração (opcional):
   ```bash
   .venv/bin/python manage.py migrate
   .venv/bin/python manage.py seed_demo
   ```
5. Recolha os ficheiros estáticos (o Bootstrap, HTMX, Chart.js etc. já estão no repositório em `static/vendor/`):
   ```bash
   .venv/bin/python manage.py collectstatic --noinput
   ```
6. No painel do PythonAnywhere (Web):
   - Defina o ficheiro WSGI para apontar a `config/wsgi.py`.
   - Defina a URL estática (`/static/`) para a pasta `staticfiles/` gerada pelo `collectstatic`.
   - Acrescente as variáveis de ambiente acima, incluindo o domínio da aplicação em `DJANGO_ALLOWED_HOSTS` e `DJANGO_CSRF_TRUSTED_ORIGINS`.
   - Defina `DJANGO_DEBUG=False` e `DJANGO_SECRET_KEY` com um valor seguro.

### Login Google em produção

Configure as credenciais OAuth no Google Cloud Console com o redirect URI:
`https://<seudominio>.pythonanywhere.com/accounts/google/login/callback/`
e defina `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` como variáveis de ambiente.


# 02. Requisitos

> **Regra de elaboração:** requisitos deduzidos exclusivamente do código-fonte. Não existem documentos de requisitos formais no repositório. Quando algo não existe no código, escreve-se "NÃO EXISTE".

## 1. Requisitos funcionais (RF)

Os requisitos abaixo são deduzidos das views, modelos, templates e testes em `equipamentos/`, `contas/` e `config/`. Cada RF indica o perfil a que se destina e a view/URL que o implementa (namespace `equipamentos`, exceto login/logout em `contas` e `accounts` do allauth).

### Perfil: Utilizador / Docente / Estudante (`papel = utilizador`)

| ID | Requisito | View / URL | Evidência no código |
|----|-----------|------------|---------------------|
| RF01 | Iniciar sessão (palavra-passe) | `auth_views.LoginView` — `contas/login/` | `contas/urls.py` linha 8, `templates/contas/login.html` |
| RF02 | Iniciar sessão com Google (domínio institucional) | `allauth.urls` — `accounts/google/login/` | `config/settings.py` `SOCIALACCOUNT_PROVIDERS.google`, `contas/adapters.py` |
| RF03 | Consultar inventário de equipamentos | `equipamentos_lista` — `/equipamentos/` | `equipamentos/views.py` linha 578, `equipamentos/urls.py` linha 8 |
| RF04 | Abrir ficha de um equipamento (dados, QR code, histórico) | `equipamento_detalhe` — `/equipamentos/<pk>/` | `equipamentos/views.py` linha 647 |
| RF05 | Reportar avaria por formulário geral (descrição + prioridade) | `reportar_avaria` — `/equipamentos/avarias/nova/` | `equipamentos/views.py` linha 313 |
| RF06 | Reportar avaria a partir de um equipamento específico (ex: lendo QR) | `reportar_avaria_equipamento` — `/equipamentos/<pk>/reportar/` | `equipamentos/views.py` linha 360 |
| RF07 | Não é possível reportar avaria em equipamento "abatido" | `reportar_avaria` / `reportar_avaria_equipamento` | `equipamentos/views.py` linhas 327-331 e 364-369 |
| RF08 | Consultar as avarias que reportou ("minhas avarias") | `minhas_avarias` — `/equipamentos/avarias/minhas/` | `equipamentos/views.py` linha 408 |
| RF09 | Acompanhar estado e intervenções de uma avaria | `avaria_detalhe` — `/equipamentos/avarias/<pk>/` | `equipamentos/views.py` linha 423 |
| RF10 | Encerrar sessão | `auth_views.LogoutView` — `contas/logout/` | `contas/urls.py` linha 9 |

### Perfil: Técnico de Manutenção (`papel = tecnico`) — inclui tudo do utilizador

| ID | Requisito | View / URL | Evidência no código |
|----|-----------|------------|---------------------|
| RF11 | Listar avarias com filtros por estado e prioridade | `avarias_lista` — `/equipamentos/avarias/` | `equipamentos/views.py` linha 187 |
| RF12 | Atualizar lista de avarias via HTMX (sem recarregar página) | `avarias_lista` (cabecalho `HX-Request`) | `equipamentos/views.py` linhas 192-197, `templates/equipamentos/avarias_lista.html` |
| RF13 | Assumir uma avaria (atribuir a si próprio e iniciar reparação) | `assumir_avaria` — `/equipamentos/avarias/<pk>/assumir/` | `equipamentos/views.py` linha 204 |
| RF14 | Alterar estado de uma avaria atribuída (respeitando transições) | `alterar_estado_avaria` — `/equipamentos/avarias/<pk>/estado/` | `equipamentos/views.py` linha 247 |
| RF15 | Registar intervenção numa avaria (detalhes + peças) | `registar_intervencao` — `/equipamentos/avarias/<pk>/intervencao/` | `equipamentos/views.py` linha 456 |
| RF16 | Ver dashboard de métricas e gráficos | `dashboard_metricas` — `/equipamentos/dashboard/` | `equipamentos/views.py` linha 515 |
| RF17 | Exportar relatório PDF do inventário ou das avarias | `relatorio_pdf` — `/equipamentos/relatorio/pdf/` | `equipamentos/views.py` linha 717 |
| RF18 | Gerar/imprimir folha A4 de etiquetas QR | `etiquetas` — `/equipamentos/etiquetas/` | `equipamentos/views.py` linha 616 |
| RF19 | Gerar imagem PNG do QR code de um equipamento | `equipamento_qrcode` — `/equipamentos/<pk>/qrcode.png` | `equipamentos/views.py` linha 674 |

### Perfil: Administrador (`papel = admin` / superutilizador) — inclui tudo do técnico

| ID | Requisito | View / URL | Evidência no código |
|----|-----------|------------|---------------------|
| RF20 | Corrigir manualmente o estado de um equipamento (com motivo) | `corrigir_estado` — `/equipamentos/<pk>/corrigir-estado/` | `equipamentos/views.py` linha 482 |
| RF21 | Reativar equipamento "abatido" (apenas via correção manual) | `corrigir_estado` com `origem="manual"` | `equipamentos/models.py` `recalcular_estado_equipamento` linha 70 |
| RF22 | Gerir utilizadores/perfis no admin (papel editável na listagem) | `contas.admin.PerfilAdmin` — `/admin/contas/perfil/` | `contas/admin.py` linhas 7-9 (`list_editable = ["papel"]`) |
| RF23 | Gerir avarias no admin (técnico atribuído editável na listagem) | `equipamentos.admin.AvariaAdmin` — `/admin/equipamentos/avaria/` | `equipamentos/admin.py` linhas 11-21 (`list_editable = ["tecnico_atribuido"]`) |
| RF24 | Aceder ao histórico de estados (somente leitura no admin) | `equipamentos.admin.HistoricoEstadoEquipamentoAdmin` | `equipamentos/admin.py` linhas 24-50 (`has_add/change/delete_permission` devolvem False) |

NÃO EXISTE: requisito de notificações por email ou push, requisito de anexos/ficheiros em avarias, requisito de manutenção preventiva, requisito de paginação nas listagens, requisito de API REST, requisito de exportação para Excel/CSV.

## 2. Requisitos não funcionais (RNF)

| ID | Requisito | Evidência no código |
|----|-----------|---------------------|
| RNF01 | Portabilidade: frontend sem dependência de CDN (funciona offline quanto a ativos estáticos) | Todos os CSS/JS carregam de `static/vendor/` local: `base.html` linhas 9-11, 134; `dashboard.html` linha 160; `avarias_lista.html` linha 91. |
| RNF02 | Segurança: CSRF ativado | `'django.middleware.csrf.CsrfViewMiddleware'` em `config/settings.py` linha 58; `{% csrf_token %}` em todos os formulários POST (`reportar_avaria.html`, `avaria_detalhe.html`, `_avarias_conteudo.html`, etc.). |
| RNF03 | Segurança: ALLOWED_HOSTS restrito | `config/settings.py` linhas 29-31: `["127.0.0.1", "localhost"]` + hosts da env `DJANGO_ALLOWED_HOSTS`. |
| RNF04 | Segurança: sessão obrigatória para todas as views de negócio | Decorators `@login_required`, `@tecnico_ou_admin_required`, `@admin_required` em `equipamentos/views.py` (linhas 31-78). |
| RNF05 | Segurança: controlo de acesso por perfil (decorators personalizados) | `tecnico_ou_admin_required` (linha 39) e `admin_required` (linha 65) usam `PermissionDenied` (HTTP 403). |
| RNF06 | Segurança: validação de parâmetros de filtro (ignora valores manipulados no URL) | `_contexto_lista_avarias` linhas 100-107 e `equipamentos_lista` linhas 583-585 validam estado/prioridade contra `ESTADO_*_CHOICES`. |
| RNF07 | Segurança: login Google só aceita email verificado e domínio institucional | `contas/adapters.py` `pre_social_login` (verificado + `dominio_email_permitido`), domínios por omissão `ucm.ac.mz,estudante.ucm.ac.mz` (`settings.py` linhas 142-148). |
| RNF08 | Segurança: URL absoluto dos QR codes controlável via `SITE_URL` | `url_absoluta` (`views.py` linha 86) usa `settings.SITE_URL` se definido, senão `request.build_absolute_uri`. |
| RNF09 | Usabilidade responsiva | Templates usam classes Bootstrap responsivas (`col-md-`, `col-lg-`, `col-xl-`, `navbar-toggler`, `table-responsive`, `d-flex flex-wrap`) — ver `base.html`, `dashboard.html`, `equipamentos_lista.html`, `avarias_lista.html`. Meta viewport em `base.html` linha 6. |
| RNF10 | Internacionalização/localização | `LANGUAGE_CODE = 'pt-pt'`, `TIME_ZONE = 'Africa/Maputo'`, `USE_I18N = True` (`settings.py` linhas 124-132). |
| RNF11 | Idempotência da carga de demonstração | `seed_demo` usa `get_or_create` e não duplica registos (`seed_demo.py`, `SeedDemoTests`). |
| RNF12 | Relatórios sem pasta de media | `relatorios.py` gera PDFs em memória (`io.BytesIO`), sem `MEDIA_ROOT` (comentário nas linhas 1-7). |
| RNF13 | QR code não guarda ficheiro no disco | `equipamento_qrcode` gera PNG em memória e devolve `HttpResponse` com `Content-Type: image/png` (`views.py` linhas 674-713). |
| RNF14 | Histórico imutável de estados do equipamento | `HistoricoEstadoEquipamentoAdmin` desativa add/change/delete (`admin.py` linhas 43-50). |

NÃO EXISTE: requisito de HTTPS/TLS forçado, requisito de rate limiting, requisito de auditoria de login, requisito de backup automático, requisito de acessibilidade WCAG, requisito de testes de desempenho.

## 3. Matriz resumida RF → perfil

| Perfil | RFs |
|--------|-----|
| Utilizador | RF01-RF10 |
| Técnico | RF01-RF10, RF11-RF19 |
| Administrador | RF01-RF10, RF11-RF19, RF20-RF24 |

# 08. Interface

> **Regra de elaboração:** descrição extraída dos templates em `templates/` e do ficheiro `static/css/ucm-theme.css`. Quando algo não existe, escreve-se "NÃO EXISTE".

## 1. Componentes gerais (todos os templates)

- **Base:** `templates/base.html` (estendido por todos os templates).
- **CSS local (sem CDN):**
  - `static/vendor/bootstrap/css/bootstrap.min.css` (referenciado em `base.html` linha 9).
  - `static/vendor/bootstrap-icons/bootstrap-icons.min.css` (linha 10).
  - `static/css/ucm-theme.css` (linha 11): tema UCM com cores `--ucm-primary: #2d2a8c`, `--ucm-action: #3b8de0`, barra de topo `.ucm-topbar`, navegação `.ucm-nav`, faixa de título `.ucm-page-header`, cartões `.card` sem sombra e com raio 0.
- **JS local (sem CDN):**
  - `static/vendor/bootstrap/js/bootstrap.bundle.min.js` (`base.html` linha 134).
  - `static/vendor/htmx/htmx.min.js` (`avarias_lista.html` linha 91).
  - `static/vendor/chartjs/chart.umd.min.js` (`dashboard.html` linha 160).
- **Imagem:** `static/img/logo-ucm.png` (logótipo UCM na topbar, `base.html` linha 19).
- **Idioma/fuso:** `pt-pt` e `Africa/Maputo` (`settings.py`), meta viewport responsivo (`base.html` linha 6).
- **Mensagens:** flashes de sucesso/erro/info renderizados em `base.html` linhas 121-129, com mapeamento `error → danger`, `debug → secondary`.
- **Navbar:** condicionada à autenticação (`base.html` linha 56). Mostra "Avarias" e "Dashboard" apenas se `is_superuser` ou papel `tecnico`/`admin` (`base.html` linhas 82-93).

### Badges (partials reutilizáveis)

| Partial | Ficheiro | Cores (classes Bootstrap) |
|---------|----------|---------------------------|
| Estado da avaria | `_badge_avaria.html` | pendente=warning, em_reparacao=primary, resolvido=success, cancelado=secondary |
| Estado do equipamento | `_badge_equipamento.html` | operacional=success, avariado=danger, manutencao=primary, abatido=secondary |
| Prioridade | `_badge_prioridade.html` | baixa=secondary, media=info, alta=warning, urgente=danger |

## 2. Telas por perfil

### Perfil: Utilizador / Docente / Estudante

| Template | URL | O que mostra |
|----------|-----|--------------|
| `contas/login.html` | `/contas/login/` | Formulário username/password + botão "Entrar com Google" (só se `GOOGLE_CLIENT_ID`/`SECRET` configurados) + campo `next`. |
| `contas/home.html` | `/` (home) | Cartões: Reportar avaria, Minhas avarias, Inventário; se técnico/admin: Gestão de avarias, Dashboard, Etiquetas QR. |
| `equipamentos/equipamentos_lista.html` | `/equipamentos/` | Pesquisa e filtro por estado; tabela com código, tipo, localização, estado (badge), avarias abertas, thumbnail do QR code, botões "Abrir ficha"/"Descarregar QR". |
| `equipamentos/equipamento_detalhe.html` | `/equipamentos/<pk>/` | Dados do equipamento, QR code (imagem + URL + download), botão "Reportar avaria", botão "Imprimir etiqueta" (`window.print`), histórico de avarias, histórico de estados. Sem formulário de corrigir estado (não é admin). |
| `equipamentos/reportar_avaria.html` | `/equipamentos/avarias/nova/` | Seleção de equipamento (exclui abatidos), descrição, prioridade (botões rádio estilo botão), botão "Registar avaria". |
| `equipamentos/reportar_avaria_equipamento.html` | (usa o mesmo template `reportar_avaria.html`) | `/equipamentos/<pk>/reportar/` | Mesmo formulário, equipamento pré-selecionado via URL (fluxo QR). |
| `equipamentos/minhas_avarias.html` | `/equipamentos/avarias/minhas/` | Lista das avarias reportadas pelo utilizador com estado, prioridade, registo e link "Ver detalhe". |
| `equipamentos/avaria_detalhe.html` | `/equipamentos/avarias/<pk>/` | Dados da avaria, lista de intervenções e, se o utilizador é admin ou técnico atribuído, formulário "Registar intervenção". |

### Perfil: Técnico de Manutenção (tudo do utilizador +)

| Template | URL | O que mostra |
|----------|-----|--------------|
| `equipamentos/avarias_lista.html` + partial `_avarias_conteudo.html` | `/equipamentos/avarias/` | Resumo de contagens (pendentes, em reparação, resolvidas, urgentes abertas); tabela de avarias com filtros HTMX por estado/prioridade; ações: "Assumir avaria" e select "Alterar estado…" (apenas transições permitidas, se atribuído a si ou admin). |
| `equipamentos/dashboard.html` | `/equipamentos/dashboard/` | Cartões de métricas (total equipamentos, operacionais, total avarias, avarias abertas); dois gráficos Chart.js (rosca estado dos equipamentos, barras estado das avarias); botões para relatórios PDF. |
| `equipamentos/etiquetas.html` | `/equipamentos/etiquetas/` | Folha A4 (3 colunas × 8 linhas = 24 etiquetas) com QR code, código, marca/modelo e localização; botão "Imprimir"; filtro por estado. |

### Perfil: Administrador (tudo do técnico +)

| Template | URL | O que mostra |
|----------|-----|--------------|
| `equipamentos/equipamento_detalhe.html` | `/equipamentos/<pk>/` | Mesmo que técnico/utilizador + formulário "Corrigir estado" (estado + motivo obrigatório), visível apenas se `e_admin`. |
| `equipamentos/avarias_lista.html` | `/equipamentos/avarias/` | Mesmo que técnico + pode mudar estado de qualquer avaria no select de transições. |
| Admin Django | `/admin/contas/perfil/`, `/admin/equipamentos/...` | Gestão de perfis (papel editável na listagem) e avarias (técnico atribuído editável na listagem). Histórico somente leitura. |

## 3. Decisões de design (tema UCM)

- Cores primárias do tema UCM definidas em `static/css/ucm-theme.css`: `--ucm-primary: #2d2a8c` (azul escuro UCM), `--ucm-action: #3b8de0` (ação). Sobrepostas às variáveis do Bootstrap (`--bs-primary`, `--bs-link-color`).
- Barra de topo `.ucm-topbar` com fundo `--ucm-primary` e logótipo UCM; título "Manutenção de Equipamentos · UCM-FEG".
- Faixa de título `.ucm-page-header` com fundo primário e tira escura `--ucm-nav` por baixo.
- Navbar escura `.ucm-nav`, links em branco, texto transformado em maiúsculas.
- Botões primários personalizados (`--bs-btn-bg: var(--ucm-action)`).
- Cartões sem sombra e com raio de borda 0 (`ucm-theme.css` linha 45).
- Impressão: `@media print` em `equipamento_detalhe.html` (oculta topbar/nav, remove margens, etiqueta com borda sólida) e em `etiquetas.html` (oculta elementos no-print, ajusta folha A4).
- Gráficos: Chart.js com dados injetados via `json_script` (evita concatenação manual/XSS), cores fixas por estado (`dashboard.html` linhas 175-186).
- Tabela de avarias usa HTMX para atualização parcial sem recarregar a página (`hx-get`, `hx-post`, `hx-target`).

NÃO EXISTE: modo escuro, internacionalização de textos via `.po/.mo` (os textos estão em português direto nos templates), framework de componentes (React/Vue), sistema de design além do `ucm-theme.css`, animações, ícones além do Bootstrap Icons.

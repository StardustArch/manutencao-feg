# 11. Limitações e trabalho futuro

> **Regra de elaboração:** limitações extraídas do código real. Melhorias futuras são sugestões plausíveis, não funcionalidades já implementadas. Quando algo não existe no código, escreve-se "NÃO EXISTE".

## 1. Limitações reais encontradas no código

| # | Limitação | Evidência no código |
|---|-----------|---------------------|
| L1 | **Sem notificações** | Não existe envio de email/notificação quando uma avaria é reportada, assumida, resolvida ou quando o estado do equipamento muda. `MAILERS` usa backend de console (`settings.py` linhas 182-185); não há chamadas a `send_mail` nem a `EmailMessage` nas views (`grep` confirmou ausência). |
| L2 | **Sem anexos/ficheiros** | Os modelos `Avaria` e `Intervencao` não têm `FileField`/`ImageField`; não há `MEDIA_ROOT` nem `MEDIA_URL` em `settings.py`; `relatorios.py` comenta explicitamente que não é necessário configurar `MEDIA_ROOT`. |
| L3 | **Sem manutenção preventiva** | Não existe modelo, view ou comando para manutenção preventiva, calibração ou inspeções agendadas. Apenas o ciclo corretivo (avarias → intervenções). |
| L4 | **Base de dados SQLite em desenvolvimento** | `settings.py` linhas 94-99: `ENGINE: django.db.backends.sqlite3`, `NAME: BASE_DIR / 'db.sqlite3'`. O README confirma: "SQLite (base de dados de desenvolvimento)". |
| L5 | **Servidor de desenvolvimento (`runserver`)** | O projeto não tem `Dockerfile`, nem configuração de servidor de produção (gunicorn/uWSGI + nginx). O `README.md` ensina a correr com `manage.py runserver`. |
| L6 | **`DEBUG = True` e `SECRET_KEY` hardcoded** | `settings.py` linhas 24 e 27: `SECRET_KEY` fixa no código e `DEBUG = True`. Não adequado a produção. |
| L7 | **Paginação inexistente** | As listagens (`equipamentos_lista`, `avarias_lista`, `minhas_avarias`, `etiquetas`) carregam todos os registos (`Equipamento.objects...`, `Avaria.objects...`) sem `Paginator`. A etiquetas divide em páginas de 24 apenas para impressão A4 (`views.py` linhas 628-634), não para navegação web. |
| L8 | **Sem API REST** | Não existem views de API (`@api_view`, ViewSets, `urls` de API). Todas as interações são via templates HTML + HTMX. |
| L9 | **QR code depende da acessibilidade do servidor** | O QR grava um URL absoluto (`SITE_URL` ou host do pedido). O README avisa: "o QR só funciona enquanto esse servidor estiver acessível". Sem `SITE_URL`, o QR usa `testserver`-like host do pedido, que pode não servir noutro dispositivo. |
| L10 | **`ALLOWED_HOSTS` restrito por omissão** | Apenas `127.0.0.1` e `localhost`; para usar na rede local é necessário adicionar o IP via `DJANGO_ALLOWED_HOSTS` ou `ALLOWED_HOSTS` (`settings.py` linhas 29-31). |
| L11 | **Login Google restrito a domínios e sem HTTPS em redirect privado** | O adapter valida domínio institucional (`contas/adapters.py`); o README alerta que o Google não aceita redirect URI em IP privado sem HTTPS (`http://192.168.1.10` não deve ser usado como redirect URI). |
| L12 | **Sem testes de UI/navegador** | Os testes são unitários/integração Django (`TestCase`), sem Selenium/Playwright. |
| L13 | **Sem exportação para Excel/CSV** | Exportação disponível apenas como PDF via ReportLab (`relatorio_pdf`, `relatorios.py`). |
| L14 | **Histórico de avarias não é editável** | `HistoricoEstadoEquipamentoAdmin` desativa add/change/delete (somente leitura). |
| L15 | **Não existe campo de categoria além de `tipo`** | `Equipamento.tipo` tem 5 valores fixos (`computador`, `laptop`, `projetor`, `impressora`, `outro`). Não há modelo de categoria separado. |

## 2. Melhorias futuras plausíveis (sugestões, não implementadas)

| # | Melhoria | Base plausível no código existente |
|---|----------|------------------------------------|
| M1 | Notificações por email (avaria reportada/resolvida, mudança de estado) | Aproveitar `MAILERS`/`django.core.mail` já configurado e os sinais/views onde o estado muda (`recalcular_estado_equipamento`, `alterar_estado_avaria`). |
| M2 | Anexo de fotos/ficheiros na avaria e intervenção | Adicionar `FileField`/`ImageField` aos modelos `Avaria`/`Intervencao`, configurar `MEDIA_ROOT`/`MEDIA_URL` (atualmente inexistentes). |
| M3 | Manutenção preventiva / inspeções agendadas | Novo modelo `PlanoManutencao` ou `Inspecao` ligado a `Equipamento`, com view de listagem e calendarização. |
| M4 | Produção: PostgreSQL + gunicorn/uWSGI + nginx + variáveis de ambiente | Substituir SQLite por PostgreSQL em `settings.py`; ler `SECRET_KEY` e `DEBUG` de variáveis de ambiente; remover `SECRET_KEY` hardcoded. |
| M5 | Paginação nas listagens web | Adicionar `django.core.paginator.Paginator` a `equipamentos_lista`, `avarias_lista`, `minhas_avarias`. |
| M6 | API REST (ex: Django REST Framework) para integração com app móvel | Criar `serializers.py` e `views.py` de API; o QR code já aponta para um URL web, mas uma API permitiria leitura/escrita por telemóvel. |
| M7 | Exportação para Excel/CSV | Acrescentar views de exportação CSV/Excel ao lado do `relatorio_pdf`. |
| M8 | Testes de UI (Selenium/Playwright) | Acrescentar testes de navegador para cobrir os fluxos HTMX e o reporte por QR. |
| M9 | Autenticação de dois fatores e recuperação de password | Estender o fluxo `contas/` (atualmente só login/logout via `auth_views` e Google). |
| M10 | Histórico de auditoria de acessos (login/logout) | Sinais `user_logged_in`/`user_logged_out` gravando num modelo de auditoria. |

NÃO EXISTE: planeamento de sprint, roadmap oficial, estimativa de esforço, priorização MoSCoW, ou documento de arquitetura de destino no repositório. Estas melhorias são proposições para a monografia, não funcionalidades do código.

## 3. Ficheiros criados (este dossier)

A seguir, a lista dos 11 ficheiros Markdown criados na pasta `docs/` e o respetivo número de linhas (contagem obtida com `wc -l`).

| # | Ficheiro | Linhas |
|---|----------|--------|
| 1 | `docs/01-visao-geral.md` | 171 |
| 2 | `docs/02-requisitos.md` | 77 |
| 3 | `docs/03-casos-de-uso.md` | 153 |
| 4 | `docs/04-modelo-de-dados.md` | 239 |
| 5 | `docs/05-regras-de-negocio.md` | 167 |
| 6 | `docs/06-arquitectura.md` | 156 |
| 7 | `docs/07-permissoes.md` | 45 |
| 8 | `docs/08-interface.md` | 72 |
| 9 | `docs/09-testes.md` | 160 |
| 10 | `docs/10-evidencias.md` | 68 |
| 11 | `docs/11-limitacoes-e-trabalho-futuro.md` | 40 |
| | **Total** | **1348** |

Nenhum ficheiro de código-fonte do projeto foi alterado ou criado; todos os factos acima foram extraídos do código existente em `config/`, `contas/`, `equipamentos/`, `templates/`, `static/`, `requirements.txt` e `README.md`.

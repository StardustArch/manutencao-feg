# 10. Evidências (checklist de capturas e roteiro do vídeo)

> **Regra de elaboração:** roteiro baseado nos URLs, templates e utilizadores demo reais do código. As capturas ainda não foram tiradas (este é um plano de evidências para a monografia). Quando algo não existe no código, escreve-se "NÃO EXISTE".

## 1. Utilizadores demo (do `seed_demo`, `README.md`)

| Utilizador | Password | Perfil | Uso nas evidências |
|------------|----------|--------|--------------------|
| `admin` | `demo123` | Administrador / superutilizador | Corrigir estado, admin, relatórios, etiquetas, qualquer avaria. |
| `tecnico1` | `demo123` | Técnico de Manutenção | Assumir avaria, mudar estado, registar intervenção, dashboard, etiquetas. |
| `utilizador1` | `demo123` | Utilizador / Docente / Estudante | Reportar avaria, minhas avarias, inventário, ficha. |

## 2. Checklist de capturas de ecrã (uma por tela e perfil)

Cada item indica: template, URL, perfil/utilizador demo a usar e o que deve aparecer.

| # | Template | URL | Utilizador demo | O que deve aparecer na captura |
|---|----------|-----|-----------------|--------------------------------|
| E1 | `contas/login.html` | `/contas/login/` | (não autenticado) | Formulário username/password; botão "Entrar com Google" (apenas se credenciais configuradas); link de logout não visível. |
| E2 | `contas/home.html` | `/` | `utilizador1` | Cartões Reportar avaria / Minhas avarias / Inventário (sem área técnica). |
| E3 | `contas/home.html` | `/` | `tecnico1` | Mesmo que E2 + área técnica (Gestão de avarias, Dashboard, Etiquetas QR). |
| E4 | `equipamentos_lista.html` | `/equipamentos/` | `utilizador1` | Tabela de equipamentos com código, tipo, localização, estado (badge) e thumbnail do QR code. |
| E5 | `equipamento_detalhe.html` | `/equipamentos/<pk>/` | `utilizador1` | Dados do equipamento, QR code, histórico de avarias, histórico de estados (sem formulário Corrigir estado). |
| E6 | `equipamento_detalhe.html` | `/equipamentos/<pk>/` | `admin` | Mesmo que E5 + formulário "Corrigir estado" (estado + motivo). |
| E7 | `reportar_avaria.html` | `/equipamentos/avarias/nova/` | `utilizador1` | Seleção de equipamento (sem abatidos), descrição, prioridade, botão Registar avaria. |
| E8 | `reportar_avaria.html` (equipamento pré-selecionado) | `/equipamentos/<pk>/reportar/` | `utilizador1` | Equipamento já selecionado (fluxo QR), descrição, prioridade. |
| E9 | `minhas_avarias.html` | `/equipamentos/avarias/minhas/` | `utilizador1` | Lista das avarias reportadas por si, com estado, prioridade, registo e link Ver detalhe. |
| E10 | `avaria_detalhe.html` | `/equipamentos/avarias/<pk>/` | `utilizador1` | Dados da avaria e intervenções (sem formulário Registar intervenção). |
| E11 | `avaria_detalhe.html` | `/equipamentos/avarias/<pk>/` | `tecnico1` | Mesmo que E10 + formulário Registar intervenção (se for o técnico atribuído). |
| E12 | `avarias_lista.html` + partial `_avarias_conteudo.html` | `/equipamentos/avarias/` | `tecnico1` | Resumo de contagens, tabela de avarias, filtros estado/prioridade, botão Assumir avaria / select Alterar estado. |
| E13 | `dashboard.html` | `/equipamentos/dashboard/` | `tecnico1` | Cartões de métricas e dois gráficos Chart.js (rosca equipamentos, barras avarias). |
| E14 | `relatorio_pdf` (PDF gerado) | `/equipamentos/relatorio/pdf/?tipo=inventario` e `?tipo=avarias` | `tecnico1` | Documento PDF com resumo e tabela (capturar o PDF aberto/impresso). |
| E15 | `etiquetas.html` | `/equipamentos/etiquetas/` | `tecnico1` | Folha A4 (3×8) com QR codes, códigos, marca/modelo, localização; botão Imprimir. |
| E16 | Admin `Perfil` | `/admin/contas/perfil/` | `admin` | Listagem de perfis com papel editável na linha. |
| E17 | Admin `Avaria` | `/admin/equipamentos/avaria/` | `admin` | Listagem de avarias com técnico atribuído editável na linha. |
| E18 | Admin `HistoricoEstadoEquipamento` | `/admin/equipamentos/historicoestadoequipamento/` | `admin` | Listagem somente leitura do histórico de estados. |

**Perfis a usar por ecrã:**
- Telas E1: sem sessão (visitante).
- Telas de consulta/reporte (E2-E9, E11): `utilizador1` (e `tecnico1` onde haja diferença, ex: E5 vs E6, E10 vs E11).
- Telas técnicas (E12-E15, E16-E18): `tecnico1` ou `admin` conforme a coluna "Utilizador demo".

## 3. Roteiro do vídeo do QR (passos numerados)

Objetivo do vídeo: demonstrar o reporte de avaria por leitura do QR code (CU05), conforme implementado em `equipamento_qrcode` e `reportar_avaria_equipamento`.

Passos sugeridos:

1. Iniciar sessão com `utilizador1` / `demo123`.
2. Abrir o inventário (`/equipamentos/`) e escolher um equipamento (ex: `UCM-FEG-PC-01`).
3. Abrir a ficha do equipamento (`/equipamentos/<pk>/`).
4. Mostrar o QR code exibido na fiche (imagem gerada por `equipamento_qrcode`, URL `/equipamentos/<pk>/qrcode.png`).
5. Explicar (áudio/texto) que o QR contém o URL de reporte de avaria desse equipamento (`/equipamentos/<pk>/reportar/`), não o da fiche (conforme `views.py` linhas 683-689 e teste `test_9_qrcode_contem_url_de_reporte_e_nao_da_ficha`).
6. Usar a câmara do telemóvel (ou um leitor de QR no computador) para ler o QR code.
7. O browser abre o URL de reporte (`/equipamentos/<pk>/reportar/`).
8. Confirmar que o equipamento está pré-selecionado no formulário (campo oculto com o `pk` do URL).
9. Preencher descrição e prioridade.
10. Submeter o formulário ("Registar avaria").
11. Confirmar o redirec para "Minhas avarias" (`/equipamentos/avarias/minhas/`) com a nova avaria listada.
12. (Opcional) Abrir a fiche do equipamento e confirmar que o estado passou para "avariado" e que existe registo no histórico de estados (fluxo automático, `recalcular_estado_equipamento` origem `fluxo`).

## 4. Evidências que NÃO existem no projeto

- Não existem capturas de ecrã prévias no repositório.
- Não existem gravações de vídeo no repositório.
- Não existem ficheiros de evidência (`.png`, `.mp4`) a incluir na pasta `docs/`.

NÃO EXISTE: ambiente de staging, utilizadores de produção, capturas automáticas geradas por testes, screenshots de CI/CD.

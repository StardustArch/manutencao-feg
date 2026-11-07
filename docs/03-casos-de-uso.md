# 03. Casos de uso

> **Regra de elaboração:** casos de uso deduzidos do código real (views, modelos, templates e testes). Quando algo não existe no código, escreve-se "NÃO EXISTE".

## 1. Actores

| Actor | Perfil no código | Descrição |
|-------|------------------|-----------|
| Utilizador | `utilizador` (docente/estudante) | Utilizador autenticado com perfil padrão. |
| Técnico | `tecnico` | Membro da equipa técnica de manutenção. |
| Administrador | `admin` ou `is_superuser` | Gestor com privilégios totais (inclui corrigir estados manualmente). |
| Visitante | não autenticado | Pode apenas ver a página de login; não acede a nenhuma view de negócio (todas exigem `@login_required`). |

## 2. Tabela de actores x casos de uso

| Caso de uso | Utilizador | Técnico | Administrador |
|-------------|------------|---------|---------------|
| CU01 Iniciar sessão | ✓ | ✓ | ✓ |
| CU02 Consultar inventário | ✓ | ✓ | ✓ |
| CU03 Ver ficha do equipamento | ✓ | ✓ | ✓ |
| CU04 Reportar avaria (formulário) | ✓ | ✓ | ✓ |
| CU05 Reportar avaria por QR | ✓ | ✓ | ✓ |
| CU06 Consultar minhas avarias | ✓ | ✓ | ✓ |
| CU07 Listar e filtrar avarias | — | ✓ | ✓ |
| CU08 Assumir avaria | — | ✓ | ✓ |
| CU09 Mudar estado da avaria | — | ✓ (própria) | ✓ (qualquer) |
| CU10 Registar intervenção | — | ✓ (atribuída) | ✓ |
| CU11 Ver dashboard | — | ✓ | ✓ |
| CU12 Gerar relatório PDF | — | ✓ | ✓ |
| CU13 Gerar etiquetas A4 | — | ✓ | ✓ |
| CU14 Corrigir estado do equipamento (manual) | — | — | ✓ |
| CU15 Gerir perfis no admin | — | — | ✓ |

## 3. Descrição detalhada de cada caso de uso

### CU04 — Reportar avaria (por lista de equipamentos)

- **Actor:** Utilizador, Técnico, Administrador
- **Pré-condição:** Utilizador autenticado; existe pelo menos um equipamento com estado diferente de "abatido".
- **Fluxo principal:**
  1. O actor acede a `/equipamentos/avarias/nova/` (`reportar_avaria`, `views.py` linha 313).
  2. Seleciona um equipamento da lista (excluídos os abatidos, `views.py` linha 352).
  3. Preenche descrição e prioridade (`AvariaForm`, `forms.py` linhas 6-21).
  4. Submete o formulário (POST com CSRF).
  5. A view cria a `Avaria` com `estado="pendente"` e `reportado_por=request.user` (`views.py` linhas 334-338).
  6. O `save()` do modelo `Avaria` chama `recalcular_estado_equipamento`, que deriva o estado do equipamento ("avariado" se houver avaria pendente) e grava histórico se houver mudança (`models.py` linhas 152-163, 53-97).
  7. Redireciona para "minhas avarias" com mensagem de sucesso.
- **Fluxos alternativos:**
  - A1: Equipamento não selecionado ou inválido → erro "Selecione um equipamento válido." (`views.py` linhas 324-325).
  - A2: Equipamento está "abatido" → erro "Não é possível reportar avarias para um equipamento abatido." e nada é criado (`views.py` linhas 327-331).
  - A3: Utilizador não autenticado → redireciona para login com `next` (`views.py` linha 312 `@login_required`, teste `test_reportar_exige_autenticacao`).
- **Pós-condição:** Existe uma nova `Avaria` em estado "pendente"; o estado do equipamento é atualizado e registado no histórico se houver mudança.

### CU05 — Reportar avaria por QR (leitura do QR code do equipamento)

- **Actor:** Utilizador, Técnico, Administrador
- **Pré-condição:** Utilizador autenticado; telemóvel leu o QR code, que aponta para o URL de reporte do equipamento (`/equipamentos/<pk>/reportar/`). O QR é gerado por `equipamento_qrcode` (`views.py` linha 674) e contém o URL absoluto de `reportar_avaria_equipamento` (testes `test_qrcode_contem_o_url_de_reporte_de_avaria` e `test_9_qrcode_contem_url_de_reporte_e_nao_da_ficha`).
- **Fluxo principal:**
  1. O actor abre o URL gravado no QR code (`reportar_avaria_equipamento`, `views.py` linha 360).
  2. O equipamento é carregado pelo `pk` do URL (`get_object_or_404`).
  3. Se o equipamento estiver "abatido", a view rejeita com erro e redireciona para a ficha (`views.py` linhas 364-372).
  4. O actor preenche descrição e prioridade e submete.
  5. A view verifica que o `equipamento` enviado no POST corresponde ao `pk` do URL (senão erro "Os dados do equipamento não correspondem ao pedido", `views.py` linhas 378-382).
  6. Cria a `Avaria` em "pendente" e recalcula o estado do equipamento.
  7. Redireciona para "minhas avarias".
- **Fluxos alternativos:**
  - A1: Equipamento abatido → rejeitado (sem criar avaria).
  - A2: `pk` do POST diferente do `pk` do URL → erro e não cria avaria (`views.py` linhas 378-382, teste `test_reportar_avaria_rejeita_equipamento_diferente_do_url`).
  - A3: Não autenticado → redireciona para login.
- **Pós-condição:** Mesma de CU04.

### CU08 — Assumir avaria

- **Actor:** Técnico, Administrador
- **Pré-condição:** Existe uma avaria em estado "pendente" ou "em_reparação" não fechada; actor autenticado com perfil tecnico/admin.
- **Fluxo principal:**
  1. O actor submete POST para `/equipamentos/avarias/<pk>/assumir/` (`assumir_avaria`, `views.py` linha 204, decorator `@tecnico_ou_admin_required` e `@require_POST`).
  2. Se a avaria estiver "resolvido" ou "cancelado" → erro "já está fechada" (`views.py` linhas 211-213).
  3. Se já atribuída a outro técnico → erro (`views.py` linhas 214-218).
  4. Senão, define `tecnico_atribuido = request.user`; se o estado era "pendente", passa para "em_reparacao" (`views.py` linhas 224-231).
  5. Chama `recalcular_estado_equipamento(equipamento, actor=request.user)` (`views.py` linhas 232-235).
  6. Responde com partial HTMX (se `HX-Request`) ou redireciona (`views.py` linha 242).
- **Fluxos alternativos:**
  - A1: Avaria já atribuída ao próprio técnico → mensagem informativa ("já está atribuída a ti").
  - A2: Avaria fechada → erro, nenhuma alteração.
- **Pós-condição:** Avaria atribuída ao técnico; se era pendente, agora está "em_reparacao"; estado do equipamento derivado ("manutencao") e histórico gravado.

### CU09 — Mudar estado da avaria

- **Actor:** Técnico (apenas avarias atribuídas a si) / Administrador (qualquer avaria)
- **Pré-condição:** Avaria existente; transição respeita `Avaria.TRANSICOES_ESTADO` (`models.py` linhas 117-122): `pendente → em_reparacao → resolvido`; `cancelado` sem saídas.
- **Fluxo principal:**
  1. POST para `/equipamentos/avarias/<pk>/estado/` (`alterar_estado_avaria`, `views.py` linha 247).
  2. Valida que o novo estado existe e é uma transição permitida a partir do estado atual (`views.py` linhas 257-270).
  3. Se não-admin: verifica que a avaria está atribuída ao actor (`views.py` linhas 274-283).
  4. Se novo estado == "resolvido" e não há técnico atribuído → erro ("Atribui primeiro a avaria a um técnico", `views.py` linhas 285-290).
  5. Se novo estado == "em_reparacao" e sem técnico → atribui ao actor automaticamente (`views.py` linhas 295-296).
  6. Guarda a avaria e chama `recalcular_estado_equipamento` (`views.py` linhas 294-303).
  7. Responde partial HTMX ou redireciona.
- **Fluxos alternativos:**
  - A1: Estado inválido ou transição não permitida → erro e nenhuma alteração.
  - A2: Técnico tenta alterar avaria de outro técnico → erro 403/mensagem.
  - A3: Tentativa de resolver sem técnico atribuído → erro.
- **Pós-condição:** Estado da avaria alterado; estado do equipamento recalculado; histórico do equipamento atualizado se houver mudança.

### CU10 — Registar intervenção

- **Actor:** Técnico (avaria atribuída) / Administrador
- **Pré-condição:** Avaria existente; o actor é admin ou `tecnico_atribuido == request.user` (condição de exibição do formulário em `avaria_detalhe`, `views.py` linhas 437-442; a view `registar_intervencao` é protegida por `@tecnico_ou_admin_required`, `views.py` linha 454).
- **Fluxo principal:**
  1. Na fiche da avaria (`avaria_detalhe`), o actor preenche "Detalhes da reparação" e opcionalmente "Peças substituídas" (`IntervencaoForm`, `forms.py` linhas 24-41).
  2. Submete POST para `/equipamentos/avarias/<pk>/intervencao/` (`registar_intervencao`, `views.py` linha 456).
  3. A view cria `Intervencao` com `tecnico = request.user` (`views.py` linhas 462-465).
  4. Redireciona para o detalhe da avaria com mensagem de sucesso.
- **Fluxos alternativos:**
  - A1: Formulário inválido → erro "Não foi possível registar a intervenção." (`views.py` linhas 471-475).
  - A2: Utilizador comum (não tecnico/admin) → HTTP 403 (teste `test_registar_intervencao_rejeita_utilizador_comum`).
  - A3: O formulário só é exibido no template se o actor pode registar (`pode_registar_intervencao`, `avaria_detalhe.html` linha 114).
- **Pós-condição:** Existe uma nova `Intervencao` ligada à avaria e ao técnico.

### CU14 — Corrigir estado do equipamento manualmente

- **Actor:** Administrador
- **Pré-condição:** Equipamento existente; actor autenticado como admin/superutilizador.
- **Fluxo principal:**
  1. Na fiche do equipamento (`equipamento_detalhe`), o admin vê o formulário "Corrigir estado" (apenas se `e_admin`, `views.py` linhas 654-669).
  2. Submete POST para `/equipamentos/<pk>/corrigir-estado/` (`corrigir_estado`, `views.py` linha 482, decorator `@admin_required` e `@require_POST`).
  3. O formulário `CorrigirEstadoForm` exige `estado` e `motivo` (`forms.py` linhas 44-55).
  4. Chama `recalcular_estado_equipamento(equipamento, actor=request.user, origem="manual", motivo=..., estado_manual=...)` (`views.py` linhas 489-495).
  5. Como `origem="manual"`, a regra do "abatido" não bloqueia (`models.py` linha 70); o estado definido pelo admin é aplicado diretamente.
  6. Se o motivo estiver vazio, o formulário é inválido e nada muda (teste `test_corrigir_estado_exige_motivo`).
  7. Redireciona para a fiche do equipamento.
- **Fluxos alternativos:**
  - A1: Técnico ou utilizador comum tenta aceder → HTTP 403 (teste `test_corrigir_estado_rejeita_tecnico` e `test_8_corrigir_estado_so_admin`).
  - A2: Motivo em branco → validação falha, estado não alterado, nenhum histórico criado.
- **Pós-condição:** Estado do equipamento alterado para o valor manual; registo em `HistoricoEstadoEquipamento` com `origem="manual"`, `motivo` e `alterado_por`.

### CU13 — Gerar etiquetas (folha A4 com QR codes)

- **Actor:** Técnico, Administrador
- **Pré-condição:** Existem equipamentos no inventário.
- **Fluxo principal:**
  1. O actor acede a `/equipamentos/etiquetas/` (`etiquetas`, `views.py` linha 616, decorator `@tecnico_ou_admin_required`).
  2. A view busca equipamentos ordenados por código, opcionalmente filtrados por estado.
  3. Divide em páginas de 24 equipamentos (3 colunas × 8 linhas = 24 etiquetas por folha A4, `views.py` linhas 628-634).
  4. O template `etiquetas.html` renderiza uma grade A4 (`@page { size: A4; }`) com imagem do QR (`equipamento_qrcode`), código, marca/modelo e localização (`etiquetas.html` linhas 33-49, 156-168).
  5. O actor imprime (botão "Imprimir" chama `window.print()`).
- **Fluxos alternativos:**
  - A1: Utilizador comum tenta aceder → HTTP 403 (teste `test_utilizador_comum_nao_acede_as_etiquetas`).
  - A2: Sem equipamentos → mensagem "Nenhum equipamento encontrado.".
- **Pós-condição:** Folha A4 renderizada pronta a imprimir; não é gerado ficheiro PDF neste fluxo (o PDF é gerado por `relatorio_pdf`, caso de uso CU12).

NÃO EXISTE: caso de uso de "receber notificação de avaria", caso de uso de "anexar foto/ficheiro à avaria", caso de uso de "manutenção preventiva agendada", caso de uso de "exportar para Excel".

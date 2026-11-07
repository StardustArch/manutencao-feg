# 05. Regras de negócio

> **Regra de elaboração:** todas as regras abaixo são extraídas do código real (`equipamentos/models.py`, `equipamentos/views.py`, `equipamentos/forms.py`). Não se inventa regras que não estejam no código. Quando algo não existe, escreve-se "NÃO EXISTE".

## 1. Transições de estado da avaria

Definidas no modelo `Avaria` (`equipamentos/models.py`, linhas 117-122):

```python
TRANSICOES_ESTADO = {
    "pendente": ("em_reparacao",),
    "em_reparacao": ("resolvido",),
    "resolvido": (),
    "cancelado": (),
}
```

Interpretação direta do código:

| Estado atual | Próximos estados permitidos | Estados terminais |
|--------------|-----------------------------|-------------------|
| `pendente` | `em_reparacao` | — |
| `em_reparacao` | `resolvido` | — |
| `resolvido` | (nenhum) | Sim |
| `cancelado` | (nenhum) | Sim |

A validação da transição é feita na view `alterar_estado_avaria` (`equipamentos/views.py`, linhas 257-270):

```python
if novo_estado not in Avaria.TRANSICOES_ESTADO.get(avaria.estado, ()):
    messages.error(request, "Transição inválida: ...")
    return _responder_acao(request)
```

A propriedade `Avaria.proximos_estados` (`models.py` linhas 165-176) devolve as transições válidas já com rótulos, usada no template para não renderizar opções inválidas.

Não existe transição automática para `cancelado` via view (não há view que mude para cancelado; o estado aparece apenas nos dados de demonstração e nas choices).

## 2. Derivação do estado do equipamento — `recalcular_estado_equipamento`

Função definida em `equipamentos/models.py`, linhas 53-97. Texto relevante do código:

```python
def recalcular_estado_equipamento(
    equipamento, actor=None, origem="fluxo", motivo="", estado_manual=None
):
    """Sincroniza o estado do equipamento com as avarias ainda abertas.

    O estado alvo é sempre derivado do trabalho pendente:
      * existe alguma avaria em reparação -> "manutencao";
      * caso contrário, existe alguma avaria pendente -> "avariado";
      * caso contrário -> "operacional".

    Numa correção manual, ``estado_manual`` permite ao administrador escolher
    diretamente o estado pretendido, mantendo o registo de histórico.

    REGRA DE OURO: um equipamento abatido só pode sair desse estado através de
    uma correção manual (``origem="manual"``). O fluxo automático nunca o
    reativa. Quando o estado não muda, nada é gravado.
    """
    if equipamento.estado == "abatido" and origem != "manual":
        return equipamento.estado

    if estado_manual is not None:
        novo_estado = estado_manual
    elif equipamento.avarias.filter(estado="em_reparacao").exists():
        novo_estado = "manutencao"
    elif equipamento.avarias.filter(estado="pendente").exists():
        novo_estado = "avariado"
    else:
        novo_estado = "operacional"

    if novo_estado == equipamento.estado:
        return equipamento.estado

    estado_anterior = equipamento.estado
    equipamento.estado = novo_estado
    equipamento.save(update_fields=["estado"])

    HistoricoEstadoEquipamento.objects.create(
        equipamento=equipamento,
        estado_anterior=estado_anterior,
        estado_novo=novo_estado,
        alterado_por=actor,
        origem=origem,
        motivo=motivo or "",
    )
    return novo_estado
```

Lógica resumida (ordem de prioridade):

1. **Bloqueio do abatido:** se o equipamento estiver `"abatido"` e a origem não for `"manual"`, a função retorna o estado atual sem alterar nada e sem criar histórico. O fluxo automático nunca reativa um equipamento abatido.
2. **Correção manual:** se `estado_manual` for fornecido, esse é o novo estado (apenas administrador, via `corrigir_estado` com `origem="manual"`).
3. **Fluxo automático (ordem de prioridade):**
   - existe alguma avaria do equipamento com `estado="em_reparacao"` → novo estado `"manutencao"`;
   - senão, existe alguma avaria com `estado="pendente"` → novo estado `"avariado"`;
   - senão → novo estado `"operacional"`.
4. **Sem mudança, sem escrita:** se o novo estado for igual ao atual, a função retorna sem gravar e sem criar registo em `HistoricoEstadoEquipamento`.
5. **Se houver mudança:** guarda `Equipamento.estado` (`update_fields=["estado"]`) e cria um registo `HistoricoEstadoEquipamento` com `estado_anterior`, `estado_novo`, `alterado_por`, `origem` e `motivo`.

## 3. Onde `recalcular_estado_equipamento` é invocada

| Local | Linha (views.py) | Contexto | `origem` | `actor` |
|-------|------------------|----------|----------|---------|
| `Avaria.save()` | models.py linha 163 | Criação de qualquer avaria (admin, shell, ORM) | `"fluxo"` (default) | None |
| `assumir_avaria` | views.py linha 232 | Técnico assume avaria | `"fluxo"` (default) | `request.user` |
| `alterar_estado_avaria` | views.py linha 300 | Mudança de estado da avaria | `"fluxo"` (default) | `request.user` |
| `corrigir_estado` | views.py linha 489 | Correção manual do equipamento | `"manual"` | `request.user` |
| `seed_demo._verificar_estados` | seed_demo.py linha 307 | Carga de demonstração | `"fluxo"` (default) | None |

## 4. Protecção do estado "abatido"

- `recalcular_estado_equipamento` bloqueia qualquer alteração automática quando `equipamento.estado == "abatido"` e `origem != "manual"` (models.py linha 70). Retorna o estado sem gravar nem criar histórico.
- Apenas a correção manual do administrador (`corrigir_estado`, `origem="manual"`, `estado_manual`) pode tirar um equipamento do estado "abatido" (teste `test_correcao_manual_pode_retirar_equipamento_de_abatido`).
- Não é possível reportar uma avaria para um equipamento abatido (`reportar_avaria` views.py linhas 327-331; `reportar_avaria_equipamento` views.py linhas 364-369).
- O teste `test_6_resolver_ultima_avaria_nao_altera_equipamento_abatido` confirma que resolver a última avaria de um equipamento abatido mantém o estado "abatido".

## 5. Histórico de estados

- Cada mudança real do estado de `Equipamento` gera um registo em `HistoricoEstadoEquipamento` (`models.py` linhas 89-96).
- Campos gravados: `estado_anterior`, `estado_novo`, `alterado_por`, `origem` (`"fluxo"` ou `"manual"`), `motivo`, `data_hora` (auto_now_add).
- Ordenação: mais recente primeiro (`Meta.ordering = ["-data_hora"]`, linha 230).
- No admin, o histórico é somente leitura (`has_add_permission`, `has_change_permission`, `has_delete_permission` devolvem `False`, `equipamentos/admin.py` linhas 43-50).
- Se o estado não muda, nenhum registo é criado (`recalcular_estado_equipamento` retorna cedo, linha 82-83).

## 6. Permissões por perfil

Funções de auxílio em `equipamentos/views.py` (linhas 31-78):

```python
def _e_tecnico_ou_admin(user):
    return user.is_superuser or (
        user.perfil.papel in {"tecnico", "admin"}
    )

def _e_admin(user):
    return user.is_superuser or (user.perfil.papel == "admin")
```

Decorators:

| Decorator | Linha | Exige | Efeito se não autorizado |
|-----------|-------|-------|--------------------------|
| `@login_required` | usada em todos | Sessão iniciada | Redireciona para `contas/login/` |
| `@tecnico_ou_admin_required` | 39 | `is_superuser` ou perfil `tecnico`/`admin` | `PermissionDenied` → HTTP 403 |
| `@admin_required` | 65 | `is_superuser` ou perfil `admin` | `PermissionDenied` → HTTP 403 |

Regras específicas por ação:

| Ação | View | Quem pode | Restrição adicional no código |
|------|------|-----------|-------------------------------|
| Reportar avaria | `reportar_avaria` / `reportar_avaria_equipamento` | Qualquer autenticado | Não em equipamento abatido |
| Listar/filtrar avarias | `avarias_lista` | Técnico/Admin | — |
| Assumir avaria | `assumir_avaria` | Técnico/Admin | Não se fechada; não se atribuída a outro |
| Mudar estado da avaria | `alterar_estado_avaria` | Técnico (própria) / Admin (qualquer) | Técnico não-admin não pode resolver sem técnico atribuído; não pode mexer em avaria de outro |
| Registar intervenção | `registar_intervencao` | Técnico/Admin | Template só mostra form se admin ou `tecnico_atribuido == user` (view é tecnico_ou_admin_required) |
| Corrigir estado equipamento | `corrigir_estado` | Apenas Admin | Motivo obrigatório (`CorrigirEstadoForm`) |
| Dashboard / PDF / Etiquetas / QR | `dashboard_metricas` / `relatorio_pdf` / `etiquetas` / `equipamento_qrcode` | Técnico/Admin (etiquetas/pdf); qualquer autenticado (QR) | — |

NÃO EXISTE: grupo de permissões Django (`auth.Group`) usado no projeto; regras de permissão baseadas em `django-guardian`; middleware de autorização próprio além dos decorators; regra de "apenas o reportador pode editar a sua avaria".

## 7. Regras de validação de formulário

- `AvariaForm` (`forms.py` linhas 6-21): campos `descricao` (textarea) e `prioridade` (RadioSelect). Nenhuma validação de equipamento no formulário; o equipamento é definido na view.
- `IntervencaoForm` (`forms.py` linhas 24-41): campos `detalhes_reparacao` e `pecas_substituidas` (opcional).
- `CorrigirEstadoForm` (`forms.py` linhas 44-55): `estado` (ChoiceField com `ESTADO_EQUIPAMENTO_CHOICES`) e `motivo` (Textarea, obrigatório). A validação do motivo ocorre no formulário; se vazio, `form.is_valid()` é `False` e nada é alterado (`views.py` linhas 502-506, teste `test_corrigir_estado_exige_motivo`).

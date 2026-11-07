# 04. Modelo de dados

> **Regra de elaboração:** modelo extraído exclusivamente de `contas/models.py` e `equipamentos/models.py` (e respetivas migrações). Quando algo não existe no código, escreve-se "NÃO EXISTE".

## 1. Modelos e campos

### Utilizador (`django.contrib.auth.models.User`)

Modelo padrão do Django (não definido no projeto, usado via `settings.AUTH_USER_MODEL`). Campos relevantes usados no projeto: `username`, `email`, `password`, `is_superuser`, `is_staff`.

### Perfil (`contas/models.py`, linhas 4-20)

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `id` | `BigAutoField` | PK | Identificador. |
| `user` | `OneToOneField(User)` | `on_delete=CASCADE`, `related_name="perfil"`, único | Ligação ao utilizador Django. |
| `papel` | `CharField` | `max_length=20`, `choices=PAPEL_CHOICES`, default `"utilizador"` | Papel do utilizador. |
| `telefone` | `CharField` | `max_length=20`, `blank=True`, `null=True` | Telefone opcional. |

`PAPEL_CHOICES`:
- `("utilizador", "Utilizador / Docente / Estudante")`
- `("tecnico", "Técnico de Manutenção")`
- `("admin", "Administrador")`

Sinal: `post_save` sobre `User` cria `Perfil` automaticamente (`contas/signals.py`, linhas 7-13).

### Equipamento (`equipamentos/models.py`, linhas 6-50)

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `id` | `BigAutoField` | PK | Identificador (migração 0001). |
| `codigo` | `CharField` | `max_length=50`, `unique=True` | Código de património/etiqueta (ex: UCM-FEG-PC-01). |
| `tipo` | `CharField` | `max_length=20`, `choices=TIPO_CHOICES` | Tipo do equipamento. |
| `marca_modelo` | `CharField` | `max_length=100` | Marca e modelo. |
| `localizacao` | `CharField` | `max_length=100`, default `"Laboratório de Informática UCM-FEG"` | Localização. |
| `estado` | `CharField` | `max_length=20`, `choices=ESTADO_EQUIPAMENTO_CHOICES`, default `"operacional"` | Estado atual. |
| `data_aquisicao` | `DateField` | `blank=True`, `null=True` | Data de aquisição opcional. |
| `observacoes` | `TextField` | `blank=True`, `null=True` | Observações opcionais. |

`TIPO_CHOICES`:
- `computador` — Computador / Desktop
- `laptop` — Portátil
- `projetor` — Projetor
- `impressora` — Impressora
- `outro` — Outro Periférico

`ESTADO_EQUIPAMENTO_CHOICES`:
- `operacional` — Operacional
- `avariado` — Avariado
- `manutencao` — Em Manutenção
- `abatido` — Abatido

Métodos:
- `get_absolute_url()` → `reverse("equipamentos:equipamento_detalhe", kwargs={"pk": self.pk})` (linhas 41-50). É o URL gravado na página pública; o QR code contudo aponta para o reporte de avaria (não para a fiche), conforme `equipamento_qrcode` (`views.py` linhas 683-689) e teste `test_9_qrcode_contem_url_de_reporte_e_nao_da_ficha`.

### Avaria (`equipamentos/models.py`, linhas 100-176)

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `id` | `BigAutoField` | PK | Identificador. |
| `equipamento` | `ForeignKey(Equipamento)` | `on_delete=CASCADE`, `related_name="avarias"` | Equipamento avariado. |
| `reportado_por` | `ForeignKey(User)` | `on_delete=SET_NULL`, `null=True`, `related_name="avarias_reportadas"` | Quem reportou. |
| `tecnico_atribuido` | `ForeignKey(User)` | `on_delete=SET_NULL`, `null=True`, `blank=True`, `related_name="avarias_atribuidas"` | Técnico responsável. |
| `descricao` | `TextField` | `help_text="Descreva o problema detalhadamente"` | Descrição do problema. |
| `prioridade` | `CharField` | `max_length=20`, `choices=PRIORIDADE_CHOICES`, default `"media"` | Prioridade. |
| `estado` | `CharField` | `max_length=20`, `choices=ESTADO_AVARIA_CHOICES`, default `"pendente"` | Estado da avaria. |
| `data_registo` | `DateTimeField` | `auto_now_add=True` | Data de criação. |
| `data_atualizacao` | `DateTimeField` | `auto_now=True` | Última atualização. |

`PRIORIDADE_CHOICES`:
- `baixa` — Baixa
- `media` — Média
- `alta` — Alta
- `urgente` — Urgente

`ESTADO_AVARIA_CHOICES`:
- `pendente` — Pendente
- `em_reparacao` — Em Reparação
- `resolvido` — Resolvido
- `cancelado` — Cancelado

`TRANSICOES_ESTADO` (variável de classe, linhas 117-122):
```python
TRANSICOES_ESTADO = {
    "pendente": ("em_reparacao",),
    "em_reparacao": ("resolvido",),
    "resolvido": (),
    "cancelado": (),
}
```
Fluxo permitido: Pendente → Em Reparação → Resolvido. `resolvido` e `cancelado` são estados terminais (sem saídas).

Propriedade `proximos_estados` (linhas 165-176): devolve lista de `(estado, rótulo)` das transições válidas a partir do estado atual. Usada no template para não mostrar transições inválidas.

Método `save()` (linhas 152-163): na criação (`_state.adding`), chama `recalcular_estado_equipamento(self.equipamento)` para sincronizar o estado do equipamento.

### Intervencao (`equipamentos/models.py`, linhas 179-196)

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `id` | `BigAutoField` | PK | Identificador. |
| `avaria` | `ForeignKey(Avaria)` | `on_delete=CASCADE`, `related_name="intervencoes"` | Avaria a que diz respeito. |
| `tecnico` | `ForeignKey(User)` | `on_delete=SET_NULL`, `null=True` | Técnico que executou. |
| `detalhes_reparacao` | `TextField` | `help_text="O que foi feito para resolver o problema"` | Detalhes da intervenção. |
| `pecas_substituidas` | `TextField` | `blank=True`, `null=True` | Peças usadas (opcional). |
| `data_intervencao` | `DateTimeField` | `auto_now_add=True` | Data/hora da intervenção. |

### HistoricoEstadoEquipamento (`equipamentos/models.py`, linhas 199-236)

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `id` | `BigAutoField` | PK | Identificador. |
| `equipamento` | `ForeignKey(Equipamento)` | `on_delete=CASCADE`, `related_name="historico_estados"` | Equipamento afetado. |
| `estado_anterior` | `CharField` | `max_length=20`, `choices=ESTADO_EQUIPAMENTO_CHOICES` | Estado antes da alteração. |
| `estado_novo` | `CharField` | `max_length=20`, `choices=ESTADO_EQUIPAMENTO_CHOICES` | Estado após a alteração. |
| `alterado_por` | `ForeignKey(User)` | `on_delete=SET_NULL`, `null=True`, `blank=True` | Quem alterou (pode ser None no fluxo automático). |
| `origem` | `CharField` | `max_length=20`, `choices=ORIGEM_CHOICES`, default `"fluxo"` | Origem da alteração. |
| `motivo` | `TextField` | `blank=True`, `default=""` | Motivo (obrigatório em correção manual). |
| `data_hora` | `DateTimeField` | `auto_now_add=True` | Data/hora da alteração. |

`Meta.ordering = ["-data_hora"]` (mais recente primeiro).

`ORIGEM_CHOICES`:
- `fluxo` — Fluxo automático
- `manual` — Correção manual

No admin, `HistoricoEstadoEquipamentoAdmin` desativa add/change/delete (`equipamentos/admin.py` linhas 43-50).

## 2. Regras e relações

- `Equipamento.avarias` → related_name `"avarias"` (1:N, um equipamento tem muitas avarias).
- `Avaria.equipamento` → `on_delete=CASCADE` (apagar equipamento apaga avarias).
- `Avaria.reportado_por` / `tecnico_atribuido` → `on_delete=SET_NULL` (mantém avaria se utilizador for apagado).
- `Intervencao.avaria` → `on_delete=CASCADE`; `Intervencao.tecnico` → `on_delete=SET_NULL`.
- `HistoricoEstadoEquipamento.equipamento` → `on_delete=CASCADE`; `alterado_por` → `SET_NULL`.
- `Perfil.user` → `OneToOneField`, `on_delete=CASCADE`.

Regra de negócio central (`recalcular_estado_equipamento`, `models.py` linhas 53-97) — detalhada na secção 05.

## 3. Diagrama ER (Mermaid)

```mermaid
erDiagram
    User ||--o{ Perfil : "1:1 (sinal post_save)"
    User ||--o{ Avaria : reportado_por (SET_NULL)
    User ||--o{ Avaria : tecnico_atribuido (SET_NULL)
    User ||--o{ Intervencao : tecnico (SET_NULL)
    User ||--o{ HistoricoEstadoEquipamento : alterado_por (SET_NULL)
    Equipamento ||--o{ Avaria : "tem muitas avarias (CASCADE)"
    Equipamento ||--o{ HistoricoEstadoEquipamento : "histórico de estados (CASCADE)"
    Avaria ||--o{ Intervencao : "tem muitas intervenções (CASCADE)"

    Perfil {
        int id PK
        string papel "utilizador/tecnico/admin"
        string telefone
    }
    Equipamento {
        int id PK
        string codigo UK
        string tipo "computador/laptop/projetor/impressora/outro"
        string marca_modelo
        string localizacao
        string estado "operacional/avariado/manutencao/abatido"
        date data_aquisicao
        text observacoes
    }
    Avaria {
        int id PK
        int equipamento_id FK
        int reportado_por_id FK
        int tecnico_atribuido_id FK
        text descricao
        string prioridade "baixa/media/alta/urgente"
        string estado "pendente/em_reparacao/resolvido/cancelado"
        datetime data_registo
        datetime data_atualizacao
    }
    Intervencao {
        int id PK
        int avaria_id FK
        int tecnico_id FK
        text detalhes_reparacao
        text pecas_substituidas
        datetime data_intervencao
    }
    HistoricoEstadoEquipamento {
        int id PK
        int equipamento_id FK
        string estado_anterior
        string estado_novo
        int alterado_por_id FK
        string origem "fluxo/manual"
        text motivo
        datetime data_hora
    }
```

## 4. Dicionário de dados (tabela)

| Tabela | Campo | Tipo | Nulo? | Chave | Choices / default | Observação |
|--------|-------|------|-------|-------|-------------------|------------|
| contas_perfil | id | BigAutoField | Não | PK | — | |
| contas_perfil | user_id | BigIntegerField | Não | FK → auth_user | unique (1:1) | related_name "perfil" |
| contas_perfil | papel | VARCHAR(20) | Não | — | utilizador/tecnico/admin, default utilizador | |
| contas_perfil | telefone | VARCHAR(20) | Sim | — | — | |
| equipamentos_equipamento | id | BigAutoField | Não | PK | — | |
| equipamentos_equipamento | codigo | VARCHAR(50) | Não | UK | — | Código de património |
| equipamentos_equipamento | tipo | VARCHAR(20) | Não | — | computador/laptop/projetor/impressora/outro | |
| equipamentos_equipamento | marca_modelo | VARCHAR(100) | Não | — | — | |
| equipamentos_equipamento | localizacao | VARCHAR(100) | Não | — | default "Laboratório de Informática UCM-FEG" | |
| equipamentos_equipamento | estado | VARCHAR(20) | Não | — | operacional/avariado/manutencao/abatido, default operacional | |
| equipamentos_equipamento | data_aquisicao | Date | Sim | — | — | |
| equipamentos_equipamento | observacoes | Text | Sim | — | — | |
| equipamentos_avaria | id | BigAutoField | Não | PK | — | |
| equipamentos_avaria | equipamento_id | BigIntegerField | Não | FK → equipamentos_equipamento | CASCADE | related_name "avarias" |
| equipamentos_avaria | reportado_por_id | BigIntegerField | Sim | FK → auth_user | SET_NULL | related_name "avarias_reportadas" |
| equipamentos_avaria | tecnico_atribuido_id | BigIntegerField | Sim | FK → auth_user | SET_NULL | related_name "avarias_atribuidas" |
| equipamentos_avaria | descricao | Text | Não | — | — | |
| equipamentos_avaria | prioridade | VARCHAR(20) | Não | — | baixa/media/alta/urgente, default media | |
| equipamentos_avaria | estado | VARCHAR(20) | Não | — | pendente/em_reparacao/resolvido/cancelado, default pendente | |
| equipamentos_avaria | data_registo | DateTime | Não | — | auto_now_add | |
| equipamentos_avaria | data_atualizacao | DateTime | Não | — | auto_now | |
| equipamentos_intervencao | id | BigAutoField | Não | PK | — | |
| equipamentos_intervencao | avaria_id | BigIntegerField | Não | FK → equipamentos_avaria | CASCADE | related_name "intervencoes" |
| equipamentos_intervencao | tecnico_id | BigIntegerField | Sim | FK → auth_user | SET_NULL | |
| equipamentos_intervencao | detalhes_reparacao | Text | Não | — | — | |
| equipamentos_intervencao | pecas_substituidas | Text | Sim | — | — | |
| equipamentos_intervencao | data_intervencao | DateTime | Não | — | auto_now_add | |
| equipamentos_historicoestadoequipamento | id | BigAutoField | Não | PK | — | |
| ... | equipamento_id | BigIntegerField | Não | FK → equipamentos_equipamento | CASCADE | related_name "historico_estados" |
| ... | estado_anterior | VARCHAR(20) | Não | — | operacional/avariado/manutencao/abatido | |
| ... | estado_novo | VARCHAR(20) | Não | — | operacional/avariado/manutencao/abatido | |
| ... | alterado_por_id | BigIntegerField | Sim | FK → auth_user | SET_NULL | |
| ... | origem | VARCHAR(20) | Não | — | fluxo/manual, default fluxo | |
| ... | motivo | Text | Não | — | default "" | |
| ... | data_hora | DateTime | Não | — | auto_now_add, ordering -data_hora | |

NÃO EXISTE: modelo de anexo/ficheiro, modelo de notificação, modelo de manutenção preventiva, modelo de etiqueta (as etiquetas são geradas na view/template a partir de `Equipamento`), modelo de categoria de equipamento além de `tipo`.

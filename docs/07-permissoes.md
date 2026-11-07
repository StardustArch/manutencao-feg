# 07. Permissões por view

> **Regra de elaboração:** tabela extraída dos decorators e lógica de autorização em `equipamentos/views.py`, `contas/views.py`, `contas/urls.py` e `equipamentos/urls.py`. Quando algo não existe, escreve-se "NÃO EXISTE".

Mecanismos de autorização utilizados:
- `@login_required`: obriga sessão iniciada (redireciona para `contas/login/`).
- `tecnico_ou_admin_required` (`equipamentos/views.py` linha 39): `@login_required` + verificação `_e_tecnico_ou_admin(user)` → `is_superuser` ou perfil `tecnico`/`admin`; senão `PermissionDenied` (HTTP 403).
- `admin_required` (`equipamentos/views.py` linha 65): `@login_required` + verificação `_e_admin(user)` → `is_superuser` ou perfil `admin`; senão `PermissionDenied` (HTTP 403).
- `@require_POST`: restringe o método HTTP a POST (não é um mecanismo de perfil, mas de método).
- Regras adicionais dentro das views (não são decorators): verificação de `tecnico_atribuido` para não-admin em `alterar_estado_avaria`; verificação de `e_admin` para exibir formulário de corrigir estado e `pode_registar_intervencao` para exibir formulário de intervenção.

## Tabela view | URL | perfis permitidos | mecanismo

| View | URL (nome) | Perfis permitidos | Mecanismo |
|------|------------|-------------------|-----------|
| `dashboard_redirect` | `contas:` raiz `/` (view_name `home`) | Qualquer autenticado | `@login_required` (contas/views.py linha 5) |
| `login` | `contas:login` → `/contas/login/` | Qualquer (não autenticado também) | `auth_views.LoginView` (sem decorator de perfil) |
| `logout` | `contas:logout` → `/contas/logout/` | Qualquer autenticado | `auth_views.LogoutView` |
| `equipamentos_lista` | `equipamentos:equipamentos_lista` → `/equipamentos/` | Qualquer autenticado | `@login_required` |
| `equipamento_detalhe` | `equipamentos:equipamento_detalhe` → `/equipamentos/<pk>/` | Qualquer autenticado | `@login_required` |
| `equipamento_qrcode` | `equipamentos:equipamento_qrcode` → `/equipamentos/<pk>/qrcode.png` | Qualquer autenticado | `@login_required` |
| `reportar_avaria` | `equipamentos:reportar_avaria` → `/equipamentos/avarias/nova/` | Qualquer autenticado | `@login_required` |
| `reportar_avaria_equipamento` | `equipamentos:reportar_avaria_equipamento` → `/equipamentos/<pk>/reportar/` | Qualquer autenticado | `@login_required` |
| `minhas_avarias` | `equipamentos:minhas_avarias` → `/equipamentos/avarias/minhas/` | Qualquer autenticado | `@login_required` |
| `avaria_detalhe` | `equipamentos:avaria_detalhe` → `/equipamentos/avarias/<pk>/` | Qualquer autenticado | `@login_required` |
| `avarias_lista` | `equipamentos:avarias_lista` → `/equipamentos/avarias/` | Técnico / Admin / Superutilizador | `@tecnico_ou_admin_required` |
| `assumir_avaria` | `equipamentos:avaria_assumir` → `/equipamentos/avarias/<pk>/assumir/` | Técnico / Admin / Superutilizador | `@tecnico_ou_admin_required` + `@require_POST` |
| `alterar_estado_avaria` | `equipamentos:avaria_alterar_estado` → `/equipamentos/avarias/<pk>/estado/` | Técnico / Admin / Superutilizador | `@tecnico_ou_admin_required` + `@require_POST` |
| `registar_intervencao` | `equipamentos:registar_intervencao` → `/equipamentos/avarias/<pk>/intervencao/` | Técnico / Admin / Superutilizador | `@tecnico_ou_admin_required` + `@require_POST` |
| `dashboard_metricas` | `equipamentos:dashboard` → `/equipamentos/dashboard/` | Técnico / Admin / Superutilizador | `@tecnico_ou_admin_required` |
| `relatorio_pdf` | `equipamentos:relatorio_pdf` → `/equipamentos/relatorio/pdf/` | Técnico / Admin / Superutilizador | `@tecnico_ou_admin_required` |
| `etiquetas` | `equipamentos:etiquetas` → `/equipamentos/etiquetas/` | Técnico / Admin / Superutilizador | `@tecnico_ou_admin_required` |
| `corrigir_estado` | `equipamentos:corrigir_estado` → `/equipamentos/<pk>/corrigir-estado/` | Apenas Admin / Superutilizador | `@admin_required` + `@require_POST` |
| Admin Django (`/admin/`) | `admin.site.urls` | Staff / Superutilizador | Django admin (is_staff) |
| `PerfilAdmin` | `/admin/contas/perfil/` | Staff / Superutilizador | Django admin (`contas/admin.py`, `list_editable=["papel"]`) |
| `AvariaAdmin` | `/admin/equipamentos/avaria/` | Staff / Superutilizador | Django admin (`equipamentos/admin.py`, `list_editable=["tecnico_atribuido"]`) |

### Observações sobre granularidade dentro de perfil

- Técnico não-admin pode alterar estado de uma avaria apenas se for o `tecnico_atribuido` (ou se a avaria não tiver técnico e o novo estado for `em_reparacao`, caso em que é atribuído automaticamente). Não pode resolver uma avaria sem técnico atribuído (`views.py` linhas 285-290). Não pode alterar avaria atribuída a outro técnico (`views.py` linhas 274-283).
- Técnico não-admin **não** pode aceder a `corrigir_estado` (HTTP 403, teste `test_corrigir_estado_rejeita_tecnico`).
- Administrador pode gerir qualquer avaria, incluindo reatribuição de técnico diretamente no admin Django (`AvariaAdmin.list_editable = ["tecnico_atribuido"]`).
- O histórico de estados é somente leitura para todos no admin (`HistoricoEstadoEquipamentoAdmin` desativa add/change/delete).

NÃO EXISTE: uso de `UserPassesTestMixin`, `PermissionRequiredMixin`, `django-guardian`, grupos de permissão (`auth.Group`), middleware de autorização customizado além dos decorators, decorators de "apenas o próprio utilizador" para `minhas_avarias` (a view filera por `reportado_por=request.user` na consulta, não por decorator).

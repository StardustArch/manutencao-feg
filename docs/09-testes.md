# 09. Testes

> **Regra de elaboração:** lista extraída dos ficheiros `equipamentos/tests.py` e `contas/tests.py`. Resultado obtido com execução real de `python manage.py test`. Quando algo não existe, escreve-se "NÃO EXISTE".

## 1. Execução real

Comando executado:
```
.venv/bin/python manage.py test
```

Ambiente: Python 3.12.3, Django 6.1.2, base de dados de teste em SQLite in-memory.

Resultado:
```
Ran 56 tests in 40.503s

OK
Destroying test database for alias 'default' ...
System check identified no issues (0 silenced).
```

- **56 testes executados, 56 aprovados, 0 falhas, 0 erros.**
- `python manage.py check`: "System check identified no issues (0 silenced)."

## 2. Lista de todos os testes (classe, método, o que verifica)

### App `contas` — `contas/tests.py`

**Classe `LoginSocialGoogleTests`** (simula fluxo social sem chamar a API do Google)

| Método | O que verifica |
|--------|----------------|
| `test_dominio_permitido_aceita_login_e_cria_perfil_utilizador` | Email `@estudante.ucm.ac.mz` verificado é aceito, cria utilizador com perfil `utilizador`, associa SocialAccount. |
| `test_dominio_nao_permitido_e_rejeitado` | Domínios `gmail.com`, `evil-ucm.ac.mz`, `ucm.ac.mz.evil.com` são rejeitados (ImmediateHttpResponse → login), sem criar utilizador nem SocialAccount. |
| `test_email_verified_falso_e_rejeitado` | Email não verificado é rejeitado. |
| `test_conta_local_com_mesmo_email_e_ligada_sem_duplicar` | Conta local com mesmo email é ligada sem duplicar utilizador nem SocialAccount; perfil fica `utilizador`. |
| `test_importar_utilizadores_e_idempotente` | Importação CSV é idempotente (contagens iguais na 2ª execução), papel aplicado, password não alterada. |
| `test_importar_utilizadores_com_sem_password` | Com `--sem-password`, utilizador fica com palavra-passe inutilizável e papel `admin`. |

**Classe `LoginPageGoogleTests`**

| Método | O que verifica |
|--------|----------------|
| `test_botao_google_aparece_e_preserva_o_next` | Com credenciais Google configuradas, login mostra "Entrar com Google", ícone `bi-google`, texto "Acesso de técnicos e administradores" e parâmetro `next`. |
| `test_botao_google_fica_escondido_sem_credenciais` | Sem credenciais, o botão Google não aparece (mas o texto de acesso de técnicos/administradores sim). |

### App `equipamentos` — `equipamentos/tests.py`

**Classe `Passo7QRCodeRelatoriosTests`**

| Método | O que verifica |
|--------|----------------|
| `test_get_absolute_url_aponta_para_a_ficha` | `get_absolute_url()` aponta para `equipamento_detalhe`. |
| `test_lista_de_equipamentos` | Lista de equipamentos retorna 200 e mostra código e título "Inventário de Equipamentos". |
| `test_ficha_do_equipamento_mostra_dados_e_historico` | Ficha mostra marca/modelo, descrição da avaria e "QR code". |
| `test_qrcode_devolve_um_png` | QR code retorna 200, Content-Type `image/png`, começa com assinatura PNG, filename `qrcode-ucm-feg-pc-99.png`. |
| `test_qrcode_contem_o_url_de_reporte_de_avaria` | QR contém URL de `reportar_avaria_equipamento` (não o da fiche). |
| `test_qrcode_exige_autenticacao` | Sem sessão, QR retorna 302 para login. |
| `test_relatorio_pdf_de_inventario` | Relatório PDF inventário: 200, `application/pdf`, começa com `%PDF-`, filename `relatorio_inventario.pdf`. |
| `test_relatorio_pdf_de_avarias` | Relatório PDF avarias: 200, `application/pdf`, filename `relatorio_avarias.pdf`. |
| `test_relatorio_pdf_rejeita_utilizador_sem_perfil_tecnico` | Utilizador comum recebe 403 no relatório PDF. |
| `test_dashboard_e_avarias_mostram_atalhos_pdf` | Dashboard e lista de avarias mostram link "PDF". |
| `test_login_devolve_o_utilizador_a_ficha_do_qrcode` | Login com `next` devolve à ficha do equipamento. |
| `test_utilizador_comum_pode_abrir_ficha_e_lista` | Utilizador comum acede a ficha e lista (200). |

**Classe `SincronizacaoEstadoEquipamentoTests`**

| Método | O que verifica |
|--------|----------------|
| `test_criar_avaria_pendente_marca_equipamento_avariado` | Criar avaria pendente marca equipamento como `avariado` e cria histórico (origem `fluxo`). |
| `test_criar_avaria_em_reparacao_marca_equipamento_em_manutencao` | Criar avaria `em_reparacao` marca equipamento como `manutencao`. |
| `test_recalcular_prioriza_em_reparacao_sobre_pendente` | Com avarias pendente + em_reparacao, equipamento fica `manutencao`. |
| `test_sem_avarias_abertas_equipamento_volta_a_operacional` | Resolver a avaria faz equipamento voltar a `operacional`. |
| `test_fluxo_automatico_nunca_altera_equipamento_abatido` | Equipamento `abatido` não muda com fluxo automático, sem histórico. |
| `test_correcao_manual_pode_retirar_equipamento_de_abatido` | Correção manual retira do `abatido`, regista origem `manual`, motivo e actor. |
| `test_estado_igual_nao_cria_historico` | Estado igual não cria registo de histórico. |

**Classe `FluxoReporteAvariasTests`**

| Método | O que verifica |
|--------|----------------|
| `test_reportar_avaria_exige_autenticacao` | Reportar exige login (302 para login). |
| `test_reportar_avaria_geral_cria_avaria_pendente` | Cria avaria pendente, equipamento fica `avariado`. |
| `test_reportar_avaria_de_equipamento_cria_avaria_pendente` | Reportar por equipamento cria avaria pendente. |
| `test_reportar_avaria_de_equipamento_usa_o_pk_do_url` | Usa o pk do URL, não o do POST. |
| `test_reportar_avaria_de_equipamento_rejeita_abatido` | Equipamento abatido é rejeitado, nenhuma avaria criada. |
| `test_reportar_avaria_rejeita_equipamento_diferente_do_url` | POST com equipamento diferente do URL é rejeitado. |
| `test_minhas_avarias_mostra_apenas_as_do_utilizador` | Lista apenas avarias do próprio utilizador. |
| `test_avaria_detalhe_mostra_formulario_ao_tecnico_atribuido` | Técnico atribuído vê formulário de intervenção. |
| `test_avaria_detalhe_nao_mostra_formulario_a_outro_utilizador` | Outro utilizador não vê o formulário. |
| `test_registar_intervencao_guarda_tecnico_autenticado` | Guarda intervenção com técnico autenticado, detalhes e peças. |
| `test_registar_intervencao_rejeita_utilizador_comum` | Utilizador comum recebe 403. |
| `test_assumir_avaria_inicia_reparacao_e_atualiza_equipamento` | Assumir avaria pendente → `em_reparacao`, técnico atribuído, equipamento `manutencao`, histórico com actor. |
| `test_corrigir_estado_admin_regista_historico_manual` | Admin corrige estado, regista histórico origem `manual`, motivo e actor. |
| `test_corrigir_estado_exige_motivo` | Motivo vazio não altera estado nem cria histórico. |
| `test_corrigir_estado_rejeita_tecnico` | Técnico recebe 403 ao tentar corrigir estado. |

**Classe `Fase1RequisitosTests`** (testes explícitos dos requisitos da fase 1, `test_1` a `test_9`)

| Método | O que verifica |
|--------|----------------|
| `test_1_reportar_avaria_cria_avaria_e_equipamento_avariado` | Reporte cria avaria e equipamento `avariado`. |
| `test_2_reportar_avaria_em_equipamento_abatido_e_rejeitado` | Equipamento abatido é rejeitado. |
| `test_3_reportar_exige_autenticacao` | Reportar exige login. |
| `test_4_fluxo_criar_assumir_resolver` | Fluxo criar → assumir → resolver (estados e equipamento atualizados). |
| `test_5_resolver_uma_de_duas_avarias_mantem_equipamento_avariado` | Resolver uma de duas avarias mantém equipamento `avariado`. |
| `test_6_resolver_ultima_avaria_nao_altera_equipamento_abatido` | Equipamento `abatido` permanece `abatido`. |
| `test_7_historico_regista_transicoes_corretas` | Histórico regista transições corretas (operacional→avariado→manutencao→operacional). |
| `test_8_corrigir_estado_so_admin_e_regista_origem_manual` | Corrigir estado só admin, origem `manual`, motivo e actor. |
| `test_9_qrcode_contem_url_de_reporte_e_nao_da_ficha` | QR contém URL de reporte, não o da fiche. |

**Classe `EtiquetasTests`**

| Método | O que verifica |
|--------|----------------|
| `test_tecnico_acede_as_etiquetas` | Técnico acede a etiquetas (200), mostra código, "Imprimir" e URL do QR. |
| `test_utilizador_comum_nao_acede_as_etiquetas` | Utilizador comum recebe 403. |

**Classe `SeedDemoTests`**

| Método | O que verifica |
|--------|----------------|
| `test_seed_demo_e_idempotente` | `seed_demo` é idempotente e cria equipamentos, avarias e intervenções. |

**Classe `QRCodeSiteURLTests`**

| Método | O que verifica |
|--------|----------------|
| `test_qrcode_usa_site_url_quando_definido` | Com `SITE_URL` definido, QR usa esse URL base. |
| `test_qrcode_sem_site_url_usa_o_host_do_pedido` | Sem `SITE_URL`, QR usa o host do pedido (`testserver`). |

## 3. Matriz requisito x teste

| RF | Testes que cobrem |
|----|-------------------|
| RF01 (login palavra-passe) | `LoginPageGoogleTests`, `FluxoReporteAvariasTests.test_reportar_avaria_exige_autenticacao`, `test_login_devolve_o_utilizador_a_ficha_do_qrcode` |
| RF02 (login Google) | `LoginSocialGoogleTests.*`, `LoginPageGoogleTests.*` |
| RF03 (consultar inventário) | `Passo7QRCodeRelatoriosTests.test_lista_de_equipamentos`, `test_utilizador_comum_pode_abrir_ficha_e_lista` |
| RF04 (ficha do equipamento) | `test_ficha_do_equipamento_mostra_dados_e_historico`, `test_utilizador_comum_pode_abrir_ficha_e_lista` |
| RF05 (reportar avaria formulário) | `Fase1RequisitosTests.test_1...`, `FluxoReporteAvariasTests.test_reportar_avaria_geral_cria_avaria_pendente` |
| RF06 (reportar por QR/equipamento) | `test_reportar_avaria_de_equipamento_cria_avaria_pendente`, `test_reportar_avaria_de_equipamento_usa_o_pk_do_url` |
| RF07 (não reportar abatido) | `test_reportar_avaria_de_equipamento_rejeita_abatido`, `Fase1RequisitosTests.test_2...` |
| RF08 (minhas avarias) | `test_minhas_avarias_mostra_apenas_as_do_utilizador` |
| RF09 (acompanhar avaria) | `test_avaria_detalhe_mostra_formulario_ao_tecnico_atribuido`, `test_avaria_detalhe_nao_mostra_formulario_a_outro_utilizador` |
| RF11 (listar/filtrar avarias) | `Passo7QRCodeRelatoriosTests.test_dashboard_e_avarias_mostram_atalhos_pdf` (lista) |
| RF13 (assumir avaria) | `test_assumir_avaria_inicia_reparacao_e_atualiza_equipamento` |
| RF14 (mudar estado) | `Fase1RequisitosTests.test_4...`, `test_5...` |
| RF10 / RF15 (intervenção) | `test_registar_intervencao_guarda_tecnico_autenticado`, `test_registar_intervencao_rejeita_utilizador_comum` |
| RF14/RF20 (corrigir estado) | `test_corrigir_estado_admin_regista_historico_manual`, `test_corrigir_estado_exige_motivo`, `test_corrigir_estado_rejeita_tecnico`, `Fase1RequisitosTests.test_8...` |
| Regras de estado (abatido, histórico) | `SincronizacaoEstadoEquipamentoTests.*` |
| RF13/etiquetas | `EtiquetasTests.*` |
| QR code | `Passo7QRCodeRelatoriosTests.test_qrcode_*`, `QRCodeSiteURLTests.*`, `Fase1RequisitosTests.test_9...` |
| PDF | `Passo7QRCodeRelatoriosTests.test_relatorio_pdf_*` |
| Seed | `SeedDemoTests.test_seed_demo_e_idempotente` |
| Importação utilizadores | `LoginSocialGoogleTests.test_importar_utilizadores_*` |

Não há testes de integração com navegador (Selenium/Playwright), testes de performance, testes de acessibilidade ou testes de API REST.

NÃO EXISTE: ficheiro `conftest.py`, configuração `pytest`, testes de UI automatizados, testes de carga.

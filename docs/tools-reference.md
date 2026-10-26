# Catálogo Completo de Referência das 100 Ferramentas do Splunk MCP

O servidor MCP do Splunk disponibiliza **100 ferramentas especializadas** distribuídas em 10 domínios operacionais.

Todas as ferramentas retornam uma resposta estruturada padronizada no formato `ToolResult`:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "warnings": [],
  "request_id": "uuid-ou-sid",
  "metadata": {
    "duration_ms": 14.2,
    "truncated": false,
    "total_count": null,
    "next_offset": null,
    "server_version": "10.6.1.1",
    "read_only": false
  }
}
```

---

## Domínio A: Buscas SPL e Execução (1 - 10)

| # | Ferramenta | Permissão | Descrição e Parâmetros |
|---|---|:---:|---|
| **001** | `splunk_search` | Leitura | Executa uma busca SPL síncrona com bloqueio em uma janela temporal explícita (`spl`, `earliest_time`, `latest_time`, `count`, `offset`). |
| **002** | `splunk_search_stream` | Leitura | Transmite em streaming os resultados de busca progressivamente via endpoint de exportação. |
| **003** | `splunk_search_async` | Leitura | Inicia um job de busca assíncrono em segundo plano e retorna imediatamente o Search Job ID (`sid`). |
| **004** | `splunk_search_status` | Leitura | Consulta o estado de execução, progresso de varredura e total de eventos processados por `sid`. |
| **005** | `splunk_search_results` | Leitura | Recupera os resultados paginados e transformados de um job concluído (`sid`, `count`, `offset`). |
| **006** | `splunk_search_events` | Leitura | Recupera os eventos brutos (`_raw`) protegidos contra ataques de injeção de prompt (`sid`, `count`). |
| **007** | `splunk_search_preview` | Leitura | Recupera resultados parciais em tempo real de uma busca ainda em processamento. |
| **008** | `splunk_search_cancel` | Escrita + Confirmação | Cancela e expurga um Search Job em execução (`sid`, `confirm=True`). |
| **009** | `splunk_search_explain` | Leitura | Analisa sintaticamente o pipeline SPL, avalia riscos, estima custo computacional e sugere melhorias. |
| **010** | `splunk_search_history` | Leitura | Consulta o histórico dos últimos jobs e buscas disparados pelo usuário autenticado. |

---

## Domínio B: Índices, Eventos & Descoberta de Dados (11 - 20)

| # | Ferramenta | Permissão | Descrição e Parâmetros |
|---|---|:---:|---|
| **011** | `splunk_list_indexes` | Leitura | Lista todos os índices acessíveis com total de eventos, tamanho em disco (MB) e retenção. |
| **012** | `splunk_get_index` | Leitura | Obtém detalhes avançados de configuração, caminhos de buckets e retenção de um índice (`index_name`). |
| **013** | `splunk_index_stats` | Leitura | Calcula métricas consolidadas de volumetria, total de eventos e espaço ocupado em disco por todos os índices. |
| **014** | `splunk_list_sourcetypes`| Leitura | Descobre os tipos de fontes de dados (*sourcetypes*) observados e seu último registro visto. |
| **015** | `splunk_list_sources` | Leitura | Lista os caminhos e origens de arquivos ou portas de entrada registrados no ambiente. |
| **016** | `splunk_list_hosts` | Leitura | Inventaria todos os servidores, computadores e endpoints que transmitem dados ao Splunk. |
| **017** | `splunk_get_field_summary`| Leitura | Gera resumo estatístico de campos extraídos, valores numéricos, valores distintos e médias (`index`, `sourcetype`). |
| **018** | `splunk_get_data_freshness`| Leitura | Avalia a latência de dados, timestamp do evento mais recente e atraso de ingestão de um índice. |
| **019** | `splunk_search_data_gaps` | Leitura | Detecta intervalos temporais e quedas inesperadas de fluxo de dados onde a taxa de ingestão caiu a zero. |
| **020** | `splunk_sample_events` | Leitura | Coleta uma amostra rápida e representativa de eventos sem realizar varredura completa nas tabelas. |

---

## Domínio C: Buscas Salvas, Relatórios & Alertas (21 - 30)

| # | Ferramenta | Permissão | Descrição e Parâmetros |
|---|---|:---:|---|
| **021** | `splunk_list_saved_searches` | Leitura | Lista todas as buscas salvas e relatórios agendados configurados no ambiente. |
| **022** | `splunk_get_saved_search` | Leitura | Inspeciona os detalhes de query SPL, agendamento cron e ações de alerta de uma busca salva (`name`). |
| **023** | `splunk_create_saved_search` | Escrita | Cria programaticamente uma nova busca salva ou alerta com agendamento e limites (`name`, `spl`, `cron_schedule`). |
| **024** | `splunk_update_saved_search` | Escrita | Atualiza propriedades, query SPL ou periodicidade de execução de uma busca existente. |
| **025** | `splunk_delete_saved_search` | Escrita + Confirmação | Exclui definitivamente uma busca salva do catálogo (`name`, `confirm=True`). |
| **026** | `splunk_dispatch_saved_search`| Leitura | Dispara manualmente e de imediato a execução de uma busca salva gerando um novo SID. |
| **027** | `splunk_list_alerts` | Leitura | Lista alertas configurados e registros de alertas acionados recentemente (*fired alerts*). |
| **028** | `splunk_get_alert_history` | Leitura | Recupera o histórico cronológico de disparo de alertas de segurança em uma janela temporal definida. |
| **029** | `splunk_acknowledge_alert` | Escrita | Reconhece e anota o status operacional de um incidente de segurança por um analista de SOC (`alert_id`, `comment`). |
| **030** | `splunk_manage_alert_suppression` | Escrita | Ativa ou desativa temporariamente a supressão de disparos para conter ruído operacional. |

---

## Domínio D: Dashboards & Objetos de Conhecimento (31 - 40)

| # | Ferramenta | Permissão | Descrição e Parâmetros |
|---|---|:---:|---|
| **031** | `splunk_list_dashboards` | Leitura | Enumera todos os dashboards Simple XML e Dashboard Studio existentes no Splunk. |
| **032** | `splunk_get_dashboard` | Leitura | Extrai a definição Simple XML e metadados de layout de um dashboard (`name`, `app`). |
| **033** | `splunk_create_dashboard` | Escrita | Cria um novo dashboard analítico Simple XML diretamente na interface do Splunk Web (`name`, `xml_data`, `app`). |
| **034** | `splunk_update_dashboard` | Escrita | Atualiza dinamicamente o código Simple XML, painéis ou título de um dashboard existente. |
| **035** | `splunk_delete_dashboard` | Escrita + Confirmação | Remove definitivamente um dashboard da plataforma com barreira de confirmação (`name`, `confirm=True`). |
| **036** | `splunk_list_reports` | Leitura | Lista relatórios formatados salvos no Splunk com seus critérios de visualização. |
| **037** | `splunk_run_report` | Leitura | Executa um relatório de negócio e coleta seus resultados consolidados (`name`). |
| **038** | `splunk_list_eventtypes` | Leitura | Lista os tipos de eventos (*eventtypes*) taxonômicos cadastrados e suas tags associadas. |
| **039** | `splunk_list_tags` | Leitura | Consulta o catálogo de tags de normalização CIM (Common Information Model). |
| **040** | `splunk_list_macros` | Leitura | Lista todas as macros SPL disponíveis no catálogo de conhecimento. |

---

## Domínio E: Administração & Controle de Acesso (41 - 50)

| # | Ferramenta | Permissão | Descrição e Parâmetros |
|---|---|:---:|---|
| **041** | `splunk_get_server_info` | Leitura | Identifica versão do Splunk, build, licença, papel do servidor e sistema operacional. |
| **042** | `splunk_get_server_health` | Leitura | Retorna o status de integridade de todos os componentes e subsistemas internos. |
| **043** | `splunk_list_apps` | Leitura | Inventaria aplicativos e add-ons tecnológicos instalados com suas versões e estados. |
| **044** | `splunk_get_app_details` | Leitura | Consulta informações aprofundadas, autor e visibilidade de um aplicativo (`app_name`). |
| **045** | `splunk_list_users` | Leitura | Lista as contas de usuários locais e integradas (LDAP/SAML) cadastradas. |
| **046** | `splunk_get_user` | Leitura | Exibe detalhes cadastrais, e-mail e papéis RBAC atribuídos a um usuário (`username`). |
| **047** | `splunk_list_roles` | Leitura | Consulta o catálogo de perfis e funções de segurança do Splunk (`admin`, `power`, `user`). |
| **048** | `splunk_get_role_capabilities` | Leitura | Inspeciona a lista detalhada de permissões granulares (*capabilities*) de um papel (`role_name`). |
| **049** | `splunk_list_configurations` | Leitura | Lista os arquivos de configuração `.conf` gerenciados pelo Splunk. |
| **050** | `splunk_get_configuration` | Leitura | Lê as stanzas e diretivas ativas de um arquivo de configuração `.conf` (`conf_name`). |

---

## Domínio F: Monitoramento de Ingestão & Forwarders (51 - 60)

| # | Ferramenta | Permissão | Descrição e Parâmetros |
|---|---|:---:|---|
| **051** | `splunk_list_inputs` | Leitura | Lista todos os canais de entrada configurados (monitores de arquivo, portas TCP/UDP, HEC). |
| **052** | `splunk_get_input` | Leitura | Consulta as propriedades e filtros de uma entrada de dados específica (`input_type`, `name`). |
| **053** | `splunk_list_forwarders` | Leitura | Descobre Universal Forwarders e Heavy Forwarders conectados com taxa de tráfego e SO. |
| **054** | `splunk_get_forwarder_status` | Leitura | Identifica o status ativo ou silencioso de um agente forwarder específico (`hostname`). |
| **055** | `splunk_check_forwarder_connectivity` | Leitura | Detecta agentes forwarders que deixaram de transmitir dados além de um limite em minutos (`threshold_minutes`). |
| **056** | `splunk_get_ingestion_metrics` | Leitura | Mensura a taxa de transferência de dados (KB/s) e vazão de eventos por segundo (EPS). |
| **057** | `splunk_get_ingestion_lag` | Leitura | Calcula a defasagem temporal entre a geração original do evento e a efetiva indexação. |
| **058** | `splunk_get_parsing_errors` | Leitura | Realiza varredura de erros de timestamp e quebra de linhas no pipeline de parsing. |
| **059** | `splunk_check_source_coverage` | Leitura | Valida se todas as fontes esperadas estão ativamente alimentando os respectivos índices. |
| **060** | `splunk_diagnose_ingestion` | Leitura | Executa um diagnóstico completo dos gargalos em pipelines de parsing e indexação. |

---

## Domínio G: Segurança, SIEM & Caça a Ameaças (61 - 70)

| # | Ferramenta | Permissão | Descrição e Parâmetros |
|---|---|:---:|---|
| **061** | `splunk_detect_failed_logins` | Leitura | Detecta e consolida falhas de autenticação em logs de auditoria do Splunk, Windows e Linux. |
| **062** | `splunk_detect_brute_force` | Leitura | Identifica padrões e picos característicos de ataques de força bruta ou credential stuffing. |
| **063** | `splunk_investigate_ip` | Leitura | Realiza investigação forense 360° em todas as atividades originadas ou destinadas a um endereço IP. |
| **064** | `splunk_investigate_user` | Leitura | Audita o comportamento, acessos e alterações realizadas por uma conta de usuário específica. |
| **065** | `splunk_investigate_host` | Leitura | Analisa eventos de segurança, conexões de rede e processos de um computador/servidor específico. |
| **066** | `splunk_search_ioc` | Leitura | Busca abrangente por Indicadores de Comprometimento (hashes MD5/SHA256, IPs, domínios maliciosos). |
| **067** | `splunk_correlate_events` | Leitura | Correlaciona eventos temporais de múltiplas fontes em torno de um pivô suspeito. |
| **068** | `splunk_detect_anomalies` | Leitura | Detecta anomalias estatísticas e desvios de linha de base no tráfego de dados. |
| **069** | `splunk_get_security_alerts` | Leitura | Recupera alertas pendentes de triagem nas categorias de segurança da informação. |
| **070** | `splunk_build_incident_timeline` | Leitura | Reconstrói cronologicamente todos os eventos antes, durante e após um incidente de segurança. |

---

## Domínio H: Performance & Capacidade do Cluster (71 - 80)

| # | Ferramenta | Permissão | Descrição e Parâmetros |
|---|---|:---:|---|
| **071** | `splunk_get_search_performance` | Leitura | Monitora o desempenho do motor de busca, tempos de resposta e uso de recursos do Search Head. |
| **072** | `splunk_detect_slow_searches` | Leitura | Identifica queries SPL ineficientes, lentas ou com alto consumo de memória. |
| **073** | `splunk_get_search_concurrency` | Leitura | Verifica limites de concorrência e quantidade de buscas simultâneas em execução. |
| **074** | `splunk_get_scheduler_health` | Leitura | Audita a taxa de sucesso e atrasos na fila do agendador de buscas automáticas. |
| **075** | `splunk_get_internal_errors` | Leitura | Coleta e sumariza mensagens de erro e exceções críticas registradas no log `_internal`. |
| **076** | `splunk_get_license_usage` | Leitura | Consulta o consumo diário de cota de licença do Splunk e alertas de excesso de volume. |
| **077** | `splunk_get_storage_usage` | Leitura | Audita a ocupação de espaço em disco nas partições do sistema e diretórios `$SPLUNK_DB`. |
| **078** | `splunk_get_cluster_health` | Leitura | Avalia a conectividade e estado operacional de Search Head Clusters ou Indexer Clusters. |
| **079** | `splunk_get_replication_status` | Leitura | Checa o status dos Fatores de Replicação (RF) e Fatores de Busca (SF) dos buckets de dados. |
| **080** | `splunk_diagnose_performance` | Leitura | Realiza diagnóstico automatizado integrando CPU, memória, I/O de disco e filas do Splunk. |

---

## Domínio I: Ações Operacionais & Gestão (81 - 90)

| # | Ferramenta | Permissão | Descrição e Parâmetros |
|---|---|:---:|---|
| **081** | `splunk_create_index` | Escrita | Cria programaticamente um novo índice de armazenamento de dados no Splunk (`name`, `max_data_size_mb`). |
| **082** | `splunk_update_index_settings` | Escrita | Ajusta parâmetros de retenção, congelamento e tamanho máximo de buckets de um índice. |
| **083** | `splunk_manage_input` | Escrita | Habilita ou desabilita operacionalmente uma entrada de dados (`input_type`, `name`, `action`). |
| **084** | `splunk_manage_user` | Escrita + Confirmação | Gerencia contas de usuários (criação, edição e exclusão de credenciais com confirmação). |
| **085** | `splunk_manage_role` | Escrita + Confirmação | Cria e ajusta papéis de segurança e permissões RBAC no Splunk. |
| **086** | `splunk_manage_app` | Escrita + Confirmação | Habilita, desabilita ou atualiza aplicativos e add-ons tecnológicos instalados. |
| **087** | `splunk_validate_configuration` | Leitura | Executa validação de sintaxe e resolução de stanzas de arquivos `.conf` utilizando o utilitário `btool`. |
| **088** | `splunk_export_search_results` | Leitura | Exporta datasets completos de resultados de busca nos formatos JSON ou CSV. |
| **089** | `splunk_submit_event` | Escrita | Envia diretamente eventos individuais ou sintéticos para um índice via REST ou token HEC. |
| **090** | `splunk_replay_saved_search` | Leitura | Reexecuta uma busca salva em uma janela histórica para auditoria e conferência. |

---

## Domínio J: Inteligência, Análise & Automação de Workflows (91 - 100)

| # | Ferramenta | Permissão | Descrição e Parâmetros |
|---|---|:---:|---|
| **091** | `splunk_natural_language_to_spl` | Leitura | Traduz intenções analíticas em linguagem natural humana para queries SPL otimizadas. |
| **092** | `splunk_optimize_spl` | Leitura | Analisa um comando SPL e reescreve a query para máxima eficiência de processamento. |
| **093** | `splunk_explain_search_results` | Leitura | Interpreta datasets de busca, resume descobertas e responde a perguntas analíticas do operador. |
| **094** | `splunk_compare_time_periods` | Leitura | Compara a volumetria ou métricas entre dois períodos distintos de tempo (`period1` vs `period2`). |
| **095** | `splunk_detect_data_quality_issues`| Leitura | Analisa anomalias de formatação, valores nulos e inconsistências de schema em um índice. |
| **096** | `splunk_generate_operational_report`| Leitura | Gera automaticamente um relatório executivo em Markdown sobre a integridade geral do Splunk. |
| **097** | `splunk_execute_workflow` | Leitura / Escrita | Orquestra pipelines sequenciais de resposta a incidentes (ex: `incident_triage`, `ingestion_audit`). |
| **098** | `splunk_preview_change` | Leitura | Simula o impacto e riscos de uma alteração administrativa antes de executá-la em produção. |
| **099** | `splunk_audit_tool_activity` | Leitura | Consulta a trilha de auditoria em memória das ferramentas executadas pelo servidor MCP. |
| **100** | `splunk_test_connection` | Leitura | Testa ponta a ponta a comunicação, latência, TLS, autenticação e versão do Splunk. |

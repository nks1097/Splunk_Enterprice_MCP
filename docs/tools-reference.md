# Catálogo de Referência das 100 Ferramentas do Splunk MCP

Este documento é o **manual definitivo de referência técnica** das 100 ferramentas disponíveis no Servidor MCP para Splunk Enterprise. Para cada ferramenta, são especificados o **objetivo operacional**, **casos de uso práticos**, **parâmetros de entrada** e **níveis de permissão de segurança**.

Todas as ferramentas devolvem o envelope padrão padronizado:
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "warnings": [],
  "request_id": "uuid-ou-sid",
  "metadata": {
    "duration_ms": 25.4,
    "truncated": false,
    "total_count": null,
    "next_offset": null,
    "server_version": "10.6.1.1",
    "read_only": false
  }
}
```

---

## Índice dos Domínios

1. [Domínio A: Buscas SPL & Execução (001 - 010)](#domínio-a-buscas-spl--execução-001---010)
2. [Domínio B: Índices, Eventos & Descoberta de Dados (011 - 020)](#domínio-b-índices-eventos--descoberta-de-dados-011---020)
3. [Domínio C: Buscas Salvas, Relatórios & Alertas (021 - 030)](#domínio-c-buscas-salvas-relatórios--alertas-021---030)
4. [Domínio D: Dashboards & Objetos de Conhecimento (031 - 040)](#domínio-d-dashboards--objetos-de-conhecimento-031---040)
5. [Domínio E: Administração & Controle de Acesso (041 - 050)](#domínio-e-administração--controle-de-acesso-041---050)
6. [Domínio F: Monitoramento de Ingestão & Forwarders (051 - 060)](#domínio-f-monitoramento-de-ingestão--forwarders-051---060)
7. [Domínio G: Segurança, SIEM & Caça a Ameaças (061 - 070)](#domínio-g-segurança-siem--caça-a-ameaças-061---070)
8. [Domínio H: Performance & Capacidade do Cluster (071 - 080)](#domínio-h-performance--capacidade-do-cluster-071---080)
9. [Domínio I: Ações Operacionais & Gestão (081 - 090)](#domínio-i-ações-operacionais--gestão-081---090)
10. [Domínio J: Inteligência, Análise & Automação de Workflows (091 - 100)](#domínio-j-inteligência-análise--automação-de-workflows-091---100)

---

## Domínio A: Buscas SPL & Execução (001 - 010)

### 001. `splunk_search`
- **Permissão:** Somente Leitura
- **Para que serve:** Executa uma consulta SPL síncrona com bloqueio e aguarda a conclusão da busca antes de devolver os registros estruturados.
- **Quando usar:** Ideal para consultas rápidas onde o agente precisa dos dados imediatos para tomar uma decisão analítica (ex: verificar status de um host ou contar erros recentes).
- **Parâmetros:**
  - `spl` *(obrigatório)*: Comando de busca SPL.
  - `earliest_time` *(opcional)*: Limite inferior da janela temporal (ex: `-1h`, `-24h@h`).
  - `latest_time` *(opcional)*: Limite superior da janela temporal (padrão: `now`).
  - `count` *(opcional)*: Quantidade máxima de registros retornados (padrão: 100).
  - `offset` *(opcional)*: Deslocamento para paginação (padrão: 0).

### 002. `splunk_search_stream`
- **Permissão:** Somente Leitura
- **Para que serve:** Transmite em fluxo contínuo (*streaming*) resultados de busca progressivamente através do endpoint de exportação do Splunk.
- **Quando usar:** Quando for necessário recuperar grandes volumes de registros sem sobrecarregar a memória do servidor ou estourar limites de timeout de API.
- **Parâmetros:**
  - `spl` *(obrigatório)*: Consulta SPL a ser executada em stream.
  - `earliest_time`, `latest_time`, `count`.

### 003. `splunk_search_async`
- **Permissão:** Somente Leitura
- **Para que serve:** Dispara um Search Job assíncrono em segundo plano no Splunk e retorna imediatamente o identificador único do job (`sid`).
- **Quando usar:** Para consultas complexas ou varreduras históricas pesadas em índices de grande volume que levam vários minutos para concluir.
- **Parâmetros:**
  - `spl` *(obrigatório)*: Query SPL complexa.
  - `earliest_time`, `latest_time`, `max_count`.

### 004. `splunk_search_status`
- **Permissão:** Somente Leitura
- **Para que serve:** Consulta o estado de execução, percentual de progresso (`done_progress`), quantidade de eventos processados e status de conclusão de um Search Job pelo `sid`.
- **Quando usar:** Para acompanhar periodicamente o avanço de um job assíncrono antes de solicitar os resultados finais.
- **Parâmetros:**
  - `sid` *(obrigatório)*: Search Job ID retornado por `splunk_search_async`.

### 005. `splunk_search_results`
- **Permissão:** Somente Leitura
- **Para que serve:** Recupera os resultados tabulares finais e transformados (processados por comandos como `stats`, `table`, `chart`) de um job concluído.
- **Quando usar:** Para coletar tabelas consolidadas, contagens, agregações e métricas finais calculadas por uma busca SPL.
- **Parâmetros:**
  - `sid` *(obrigatório)*: Search Job ID.
  - `count`, `offset`: Para navegação paginada em relatórios extensos.

### 006. `splunk_search_events`
- **Permissão:** Somente Leitura
- **Para que serve:** Recupera os eventos brutos originais (`_raw`) de um job, protegendo a saída com delimitadores de segurança contra injeção de prompt.
- **Quando usar:** Em investigações forenses profundas de SOC, onde o analista precisa inspecionar payloads brutos de pacotes, mensagens originais do syslog ou XML de eventos do Windows.
- **Parâmetros:**
  - `sid` *(obrigatório)*: Search Job ID.
  - `count`, `offset`.

### 007. `splunk_search_preview`
- **Permissão:** Somente Leitura
- **Para que serve:** Obtém uma pré-visualização em tempo real de resultados parciais de uma busca enquanto ela ainda está sendo processada.
- **Quando usar:** Em buscas de longa duração onde o usuário quer visualizar uma amostra inicial imediata sem ter que aguardar a conclusão de 100% da varredura.
- **Parâmetros:**
  - `sid` *(obrigatório)*: Search Job ID em execução.

### 008. `splunk_search_cancel`
- **Permissão:** Escrita + Confirmação Humana (`confirm=True`)
- **Para que serve:** Cancela a execução de um Search Job ativo e libera os recursos computacionais (CPU/memória) consumidos no Search Head e nos Indexers.
- **Quando usar:** Para abortar queries acidentais mal otimizadas que estejam consumindo recursos excessivos do cluster.
- **Parâmetros:**
  - `sid` *(obrigatório)*: Search Job ID a ser abortado.
  - `confirm` *(obrigatório)*: Deve ser `true` para confirmar a destruição do job.

### 009. `splunk_search_explain`
- **Permissão:** Somente Leitura
- **Para que serve:** Faz a auditoria sintática e decomposição AST da consulta SPL, verifica conformidade com as políticas de segurança e aponta comandos proibidos ou ineficientes.
- **Quando usar:** Antes de executar uma query complexa, para garantir que ela não contenha anti-patterns nem comandos mutantes indesejados.
- **Parâmetros:**
  - `spl` *(obrigatório)*: Query SPL a ser analisada.

### 010. `splunk_search_history`
- **Permissão:** Somente Leitura
- **Para que serve:** Consulta o histórico das buscas mais recentes despachadas no Splunk pelo usuário autenticado, com status e horários.
- **Quando usar:** Para auditar quais consultas foram executadas recentemente, resgatar SIDs de jobs passados ou identificar comandos executados por outros analistas.
- **Parâmetros:**
  - `count` *(opcional)*: Quantidade de buscas a listar do histórico (padrão: 50).

---

## Domínio B: Índices, Eventos & Descoberta de Dados (011 - 020)

### 011. `splunk_list_indexes`
- **Permissão:** Somente Leitura
- **Para que serve:** Lista todos os índices configurados no Splunk com contagem total de eventos, tamanho em disco (MB), status (ativo/desabilitado) e tempos de retenção.
- **Quando usar:** Para inventariar as bases de dados existentes no Splunk e verificar onde os dados de determinado sistema estão sendo guardados.
- **Parâmetros:**
  - `count`, `offset`.

### 012. `splunk_get_index`
- **Permissão:** Somente Leitura
- **Para que serve:** Consulta detalhada das propriedades de um índice específico, incluindo caminhos de armazenamento de buckets (`home_path`, `cold_path`, `thawed_path`) e política de descarte.
- **Quando usar:** Durante auditorias de armazenamento ou para verificar a configuração de retenção máxima de um índice crítico de conformidade.
- **Parâmetros:**
  - `index_name` *(obrigatório)*: Nome do índice desejado.

### 013. `splunk_index_stats`
- **Permissão:** Somente Leitura
- **Para que serve:** Calcula estatísticas consolidadas agregadas sobre todos os índices: espaço total em disco (MB/GB) e volume consolidado de eventos.
- **Quando usar:** Em relatórios executivos de capacidade para avaliar o crescimento global da base do Splunk.

### 014. `splunk_list_sourcetypes`
- **Permissão:** Somente Leitura
- **Para que serve:** Descobre e cataloga todos os tipos de fontes de dados (*sourcetypes*) observados na base, com contagem de eventos e data da última ocorrência.
- **Quando usar:** Para identificar quais formatos de log estão ativos (ex: `WinEventLog`, `cisco:asa`, `nginx:access`, `json_telemetry`).
- **Parâmetros:**
  - `index` *(opcional)*: Filtrar por índice específico.
  - `count`.

### 015. `splunk_list_sources`
- **Permissão:** Somente Leitura
- **Para que serve:** Lista os caminhos de arquivos de origem, portas de escuta ou canais de onde os dados estão sendo lidos.
- **Quando usar:** Para verificar se um arquivo de log específico (ex: `/var/log/audit/audit.log`) está sendo indexado.
- **Parâmetros:**
  - `index` *(opcional)*, `count`.

### 016. `splunk_list_hosts`
- **Permissão:** Somente Leitura
- **Para que serve:** Descobre e lista todos os servidores, computadores e dispositivos que estão gerando e enviando logs para o Splunk.
- **Quando usar:** Em auditorias de inventário de ativos de TI para checar quais computadores da empresa estão emitindo telemetria.
- **Parâmetros:**
  - `index` *(opcional)*, `count`.

### 017. `splunk_get_field_summary`
- **Permissão:** Somente Leitura
- **Para que serve:** Gera um resumo estatístico profundo sobre os campos extraídos de um índice/sourcetype, mostrando valores distintos, média, desvio padrão e top valores.
- **Quando usar:** Para entender a estrutura e conteúdo de novos logs desconhecidos sem precisar abrir eventos um por um.
- **Parâmetros:**
  - `index` *(obrigatório)*: Índice a amostrar.
  - `sourcetype` *(opcional)*: Tipo de fonte específico.
  - `sample_count`: Quantidade de eventos para a amostra estatística (padrão: 500).

### 018. `splunk_get_data_freshness`
- **Permissão:** Somente Leitura
- **Para que serve:** Avalia o frescor dos dados de um índice, calculando o atraso em segundos/minutos entre o momento atual e o evento mais recente gravado.
- **Quando usar:** Para verificar se os logs de firewalls, sistemas de pagamento ou servidores estão chegando em tempo real ou se há represamento na rede.
- **Parâmetros:**
  - `index` *(obrigatório)*.

### 019. `splunk_search_data_gaps`
- **Permissão:** Somente Leitura
- **Para que serve:** Analisa a série temporal de ingestão e identifica "buracos" (gaps) onde a taxa de eventos caiu a zero em horários onde deveria haver atividade.
- **Quando usar:** Para diagnosticar quedas de conectividade de rede, servidores que foram reiniciados ou falhas em agentes de coleta.
- **Parâmetros:**
  - `index` *(obrigatório)*, `earliest_time`, `latest_time`.

### 020. `splunk_sample_events`
- **Permissão:** Somente Leitura
- **Para que serve:** Coleta uma amostra rápida e equilibrada de eventos de um índice sem disparar varreduras completas em tabelas inteiras.
- **Quando usar:** Para visualizar rapidamente o layout dos registros e exemplos reais de linhas de log antes de elaborar buscas mais avançadas.
- **Parâmetros:**
  - `index` *(obrigatório)*, `count` (padrão: 10).

---

## Domínio C: Buscas Salvas, Relatórios & Alertas (021 - 030)

### 021. `splunk_list_saved_searches`
- **Permissão:** Somente Leitura
- **Para que serve:** Lista todas as buscas salvas, relatórios agendados e regras de alerta cadastradas na plataforma.
- **Quando usar:** Para auditar quais buscas automáticas estão programadas no sistema e checar quais relatórios estão disponíveis.
- **Parâmetros:**
  - `app` *(opcional)*: Filtrar por aplicativo (ex: `search`).
  - `count`.

### 022. `splunk_get_saved_search`
- **Permissão:** Somente Leitura
- **Para que serve:** Obtém a definição completa de uma busca salva específica: query SPL, periodicidade cron, limites de disparo e ações configuradas (e-mail, webhook, script).
- **Quando usar:** Para auditar a lógica de detecção de um alerta de segurança existente.
- **Parâmetros:**
  - `name` *(obrigatório)*: Nome da busca salva.

### 023. `splunk_create_saved_search`
- **Permissão:** Escrita
- **Para que serve:** Cria programaticamente uma nova busca salva ou regra de alerta no Splunk com agendamento cron e ações integradas.
- **Quando usar:** Para automatizar o provisionamento de novos casos de uso de detecção de ameaças do SOC ou agendar novos relatórios gerenciais periódicos.
- **Parâmetros:**
  - `name` *(obrigatório)*: Identificador único da busca salva.
  - `spl` *(obrigatório)*: Query SPL que será executada automaticamente.
  - `cron_schedule` *(opcional)*: Expressão cron (ex: `*/15 * * * *`).
  - `description`, `is_scheduled`.

### 024. `splunk_update_saved_search`
- **Permissão:** Escrita
- **Para que serve:** Altera propriedades, query SPL ou periodicidade cron de uma busca salva ou alerta já existente.
- **Quando usar:** Para refinar thresholds de alertas falsos positivos ou atualizar filtros de consulta em regras de segurança.
- **Parâmetros:**
  - `name` *(obrigatório)*: Nome da busca salva a modificar.
  - `spl`, `cron_schedule`, `description`.

### 025. `splunk_delete_saved_search`
- **Permissão:** Escrita + Confirmação Humana (`confirm=True`)
- **Para que serve:** Exclui definitivamente uma busca salva ou regra de alerta do catálogo do Splunk.
- **Quando usar:** Para desativar e expurgar relatórios obsoletos ou regras de detecção descontinuadas.
- **Parâmetros:**
  - `name` *(obrigatório)*: Nome da busca salva a remover.
  - `confirm` *(obrigatório)*: `true` para confirmar a exclusão.

### 026. `splunk_dispatch_saved_search`
- **Permissão:** Somente Leitura
- **Para que serve:** Dispara manualmente a execução imediata de uma busca salva fora do seu agendamento cron e retorna o SID correspondente.
- **Quando usar:** Para forçar a atualização imediata dos dados de um relatório ou testar se uma regra de alerta está funcionando corretamente no momento.
- **Parâmetros:**
  - `name` *(obrigatório)*: Nome da busca salva a despachar.

### 027. `splunk_list_alerts`
- **Permissão:** Somente Leitura
- **Para que serve:** Lista os alertas cadastrados e o histórico recente de alertas acionados (*fired alerts*).
- **Quando usar:** Para verificar quais alertas de monitoramento dispararam nas últimas horas na central de operações.
- **Parâmetros:**
  - `count` *(opcional)*.

### 028. `splunk_get_alert_history`
- **Permissão:** Somente Leitura
- **Para que serve:** Consulta cronologicamente no log de auditoria interno (`_audit`) quando e quantas vezes determinado alerta disparou em uma janela temporal definida.
- **Quando usar:** Para identificar padrões de recorrência ou picos de disparos anormais de alertas de segurança.
- **Parâmetros:**
  - `alert_name` *(opcional)*: Nome do alerta a auditar.
  - `earliest_time` (padrão: `-7d@d`), `count`.

### 029. `splunk_acknowledge_alert`
- **Permissão:** Escrita
- **Para que serve:** Permite que o operador ou analista de SOC reconheça (*acknowledge*) um alerta disparado e registre notas operacionais de triagem.
- **Quando usar:** No fluxo de triagem de incidentes, para marcar que um evento já está sendo investigado por um operador e evitar retrabalho na equipe.
- **Parâmetros:**
  - `alert_id` *(obrigatório)*: Identificador do alerta.
  - `comment` *(opcional)*: Nota ou parecer técnico do analista.

### 030. `splunk_manage_alert_suppression`
- **Permissão:** Escrita
- **Para que serve:** Ativa ou desativa temporariamente a supressão de novos disparos de um alerta para evitar tempestade de notificações (*alert fatigue*).
- **Quando usar:** Durante janelas de manutenção de servidores ou incidentes massivos onde múltiplos disparos repetitivos causariam sobrecarga.
- **Parâmetros:**
  - `alert_name` *(obrigatório)*: Nome do alerta a suprimir.
  - `suppress` *(obrigatório)*: `true` para silenciar, `false` para reativar.

---

## Domínio D: Dashboards & Objetos de Conhecimento (031 - 040)

### 031. `splunk_list_dashboards`
- **Permissão:** Somente Leitura
- **Para que serve:** Lista todos os dashboards Simple XML e Dashboard Studio disponíveis na instância do Splunk com título, aplicativo e dono.
- **Quando usar:** Para mapear os painéis visuais ativos e localizar a URL de acesso de painéis operacionais do SOC.
- **Parâmetros:**
  - `app` *(opcional)*: Filtrar por aplicativo (ex: `search`).
  - `count`.

### 032. `splunk_get_dashboard`
- **Permissão:** Somente Leitura
- **Para que serve:** Extrai o código-fonte XML completo (`Simple XML`) e a árvore de painéis de um dashboard específico.
- **Quando usar:** Para auditar as consultas SPL embutidas nos gráficos de um dashboard ou fazer backup do layout antes de uma alteração.
- **Parâmetros:**
  - `name` *(obrigatório)*: ID do dashboard.
  - `app` *(opcional)*: Nome do app associado.

### 033. `splunk_create_dashboard`
- **Permissão:** Escrita
- **Para que serve:** Cria um novo dashboard analítico Simple XML diretamente no Splunk Web com suporte a tabelas, gráficos, indicadores e mapas geográficos.
- **Quando usar:** Para gerar dashboards completos de SOC, painéis de monitoramento de servidores ou centros de comando visual para os clientes e times de resposta.
- **Parâmetros:**
  - `name` *(obrigatório)*: Identificador único na URL (slug).
  - `xml_data` *(obrigatório)*: Código XML válido da tag raiz `<dashboard>` ou `<form>`.
  - `app` *(opcional)*: Aplicativo de destino (padrão: `search`).

### 034. `splunk_update_dashboard`
- **Permissão:** Escrita
- **Para que serve:** Atualiza o código Simple XML, modifica painéis existentes ou altera o título visível de um dashboard.
- **Quando usar:** Para incluir novas métricas, ajustar o layout visual ou alterar a lógica de filtros de um dashboard corporativo.
- **Parâmetros:**
  - `name` *(obrigatório)*, `xml_data`, `label`, `app`.

### 035. `splunk_delete_dashboard`
- **Permissão:** Escrita + Confirmação Humana (`confirm=True`)
- **Para que serve:** Exclui definitivamente um dashboard e seus painéis do Splunk Web.
- **Quando usar:** Para desativar e limpar painéis temporários ou projetos visuais descontinuados.
- **Parâmetros:**
  - `name` *(obrigatório)*: ID do dashboard a excluir.
  - `confirm` *(obrigatório)*: `true` para confirmar a exclusão.

### 036. `splunk_list_reports`
- **Permissão:** Somente Leitura
- **Para que serve:** Lista os relatórios de negócio salvos e formatados no sistema, mostrando suas queries e agendamentos.
- **Quando usar:** Para auditar quais relatórios analíticos estão disponíveis para os gestores e analistas.
- **Parâmetros:**
  - `app` *(opcional)*, `count`.

### 037. `splunk_run_report`
- **Permissão:** Somente Leitura
- **Para que serve:** Executa um relatório salvo e devolve diretamente a tabela de dados final consolidada.
- **Quando usar:** Para extrair métricas de relatórios consolidados oficiais sem ter que reescrever a query SPL manualmente.
- **Parâmetros:**
  - `name` *(obrigatório)*: Nome do relatório a executar.

### 038. `splunk_list_eventtypes`
- **Permissão:** Somente Leitura
- **Para que serve:** Lista os tipos de eventos (*eventtypes*) configurados no Splunk, suas prioridades e expressões de busca correspondentes.
- **Quando usar:** Para entender a taxonomia de classificação de logs adotada na empresa (ex: categorizar eventos de falha de login, auditoria de arquivos ou tráfego VPN).
- **Parâmetros:**
  - `count`.

### 039. `splunk_list_tags`
- **Permissão:** Somente Leitura
- **Para que serve:** Consulta o catálogo de tags de normalização CIM (Common Information Model) ativas no ambiente.
- **Quando usar:** Em ambientes com Splunk Enterprise Security (ES) para verificar se os dados de firewall, autenticação e antivírus estão devidamente mapeados para o modelo padrão da indústria.
- **Parâmetros:**
  - `count`.

### 040. `splunk_list_macros`
- **Permissão:** Somente Leitura
- **Para que serve:** Lista as macros SPL cadastradas no Splunk com suas definições e argumentos de substituição.
- **Quando usar:** Para identificar funções reutilizáveis de busca (ex: `` `drop_dm_object_name()` ``) e entender sua expansão sintática.
- **Parâmetros:**
  - `count`.

---

## Domínio E: Administração & Controle de Acesso (041 - 050)

### 041. `splunk_get_server_info`
- **Permissão:** Somente Leitura
- **Para que serve:** Retorna informações fundamentais da instância: versão exata do Splunk (`10.6.1.1`), build, tipo de licença, sistema operacional hospedeiro e papel do nó.
- **Quando usar:** Como passo inicial de qualquer automação para checar a compatibilidade e a versão do Splunk antes de disparar rotinas complexas.

### 042. `splunk_get_server_health`
- **Permissão:** Somente Leitura
- **Para que serve:** Consulta a saúde dos subsistemas internos do Splunk (fila de indexação, agendador, disco, licença) retornando estados `GREEN`, `YELLOW` ou `RED`.
- **Quando usar:** Para verificações automáticas diárias de saúde ou antes de iniciar manutenções na infraestrutura.

### 043. `splunk_list_apps`
- **Permissão:** Somente Leitura
- **Para que serve:** Inventaria todos os aplicativos, add-ons tecnológicos (TAs) e módulos instalados, com suas respectivas versões e status de ativação.
- **Quando usar:** Para verificar se complementos importantes (como o `Splunk_TA_windows` ou `Splunk_TA_nix`) estão instalados e habilitados.
- **Parâmetros:**
  - `count`.

### 044. `splunk_get_app_details`
- **Permissão:** Somente Leitura
- **Para que serve:** Detalha as informações de autor, versão, caminho no disco e visibilidade na interface de um aplicativo específico.
- **Quando usar:** Em auditorias de conformidade de plugins e apps instalados no Splunk.
- **Parâmetros:**
  - `app_name` *(obrigatório)*: Identificador do app (ex: `search`, `Splunk_TA_windows`).

### 045. `splunk_list_users`
- **Permissão:** Somente Leitura
- **Para que serve:** Lista os usuários cadastrados no Splunk (locais ou sincronizados via Active Directory/LDAP), com e-mails e papéis atribuídos.
- **Quando usar:** Para auditar o catálogo de identidades e checar quem possui acesso à plataforma.
- **Parâmetros:**
  - `count`.

### 046. `splunk_get_user`
- **Permissão:** Somente Leitura
- **Para que serve:** Exibe detalhes aprofundados sobre uma conta de usuário específica: papéis associados, fuso horário, status de bloqueio e último login.
- **Quando usar:** Em investigações de acesso não autorizado ou para validar permissões atribuídas a um colaborador.
- **Parâmetros:**
  - `username` *(obrigatório)*: Nome de usuário a inspecionar.

### 047. `splunk_list_roles`
- **Permissão:** Somente Leitura
- **Para que serve:** Lista todos os perfis e funções RBAC (Role-Based Access Control) configurados no Splunk (ex: `admin`, `power`, `user`).
- **Quando usar:** Para mapear a estrutura de privilégios de acesso do ambiente.
- **Parâmetros:**
  - `count`.

### 048. `splunk_get_role_capabilities`
- **Permissão:** Somente Leitura
- **Para que serve:** Inspeciona detalhadamente a lista de permissões granulares (*capabilities*) concedidas a um perfil específico (ex: `schedule_search`, `admin_all_objects`, `edit_indexer_cluster`).
- **Quando usar:** Para auditar se determinada função possui privilégios excessivos ou restrições de segurança adequadas.
- **Parâmetros:**
  - `role_name` *(obrigatório)*: Nome do perfil a inspecionar.

### 049. `splunk_list_configurations`
- **Permissão:** Somente Leitura
- **Para que serve:** Lista os nomes de todos os arquivos de configuração `.conf` gerenciados pelo Splunk (`inputs.conf`, `props.conf`, `transforms.conf`, `server.conf`).
- **Quando usar:** Para identificar quais módulos de configuração possuem stanzas ativas no ambiente.
- **Parâmetros:**
  - `count`.

### 050. `splunk_get_configuration`
- **Permissão:** Somente Leitura
- **Para que serve:** Lê o conteúdo e os parâmetros ativos de stanzas dentro de um arquivo `.conf` específico.
- **Quando usar:** Para checar como uma entrada de log ou pipeline de transformação foi declarada nos bastidores dos arquivos de configuração.
- **Parâmetros:**
  - `conf_name` *(obrigatório)*: Nome do arquivo (ex: `inputs`, `props`, `server`).

---

## Domínio F: Monitoramento de Ingestão & Forwarders (051 - 060)

### 051. `splunk_list_inputs`
- **Permissão:** Somente Leitura
- **Para que serve:** Lista todas as entradas ativas de coleta de dados configuradas (monitores de arquivo, portas TCP/UDP de syslog, tokens HEC).
- **Quando usar:** Para conferir quais canais e portas estão abertos recebendo dados de rede ou arquivos locais.
- **Parâmetros:**
  - `count`.

### 052. `splunk_get_input`
- **Permissão:** Somente Leitura
- **Para que serve:** Consulta os detalhes avançados de uma entrada específica (diretório monitorado, índice de destino, sourcetype associado, lista negra de extensões).
- **Quando usar:** Para diagnosticar se um monitor de log está apontando para a pasta correta e aplicando a regex adequada de filtragem.
- **Parâmetros:**
  - `input_type` *(obrigatório)*: Tipo de entrada (ex: `monitor`, `tcp`, `udp`).
  - `name` *(obrigatório)*: Caminho do arquivo ou porta de escuta.

### 053. `splunk_list_forwarders`
- **Permissão:** Somente Leitura
- **Para que serve:** Descobre e lista todos os Universal Forwarders (UF) e Heavy Forwarders (HF) conectados, com versão do agente, sistema operacional e volume transmitido em MB.
- **Quando usar:** Para checar o parque de agentes instalados nas estações e servidores da empresa e garantir que todos estejam comunicando normalmente.
- **Parâmetros:**
  - `count`.

### 054. `splunk_get_forwarder_status`
- **Permissão:** Somente Leitura
- **Para que serve:** Verifica se um forwarder específico está ativo (*active*) ou silencioso (*inactive*) com base no seu último batimento de conexão.
- **Quando usar:** Para checar a saúde de um servidor crítico que aparenta ter parado de enviar eventos.
- **Parâmetros:**
  - `hostname` *(obrigatório)*: Nome de máquina do forwarder.

### 055. `splunk_check_forwarder_connectivity`
- **Permissão:** Somente Leitura
- **Para que serve:** Realiza uma auditoria automatizada em todos os forwarders e destaca aqueles que não transmitem dados além de um limite de tempo estabelecido em minutos.
- **Quando usar:** Em rotinas de monitoramento de infraestrutura do SOC para disparar alertas quando um endpoint ou servidor parar de enviar telemetria.
- **Parâmetros:**
  - `threshold_minutes` *(opcional)*: Limite de tolerância de inatividade (padrão: 15 minutos).

### 056. `splunk_get_ingestion_metrics`
- **Permissão:** Somente Leitura
- **Para que serve:** Mensura a taxa de transferência instantânea da ingestão de dados em Kilobytes por segundo (KB/s) e eventos por segundo (EPS).
- **Quando usar:** Para identificar sobrecargas de rede ou avaliar o impacto de novos sistemas sendo conectados ao Splunk.

### 057. `splunk_get_ingestion_lag`
- **Permissão:** Somente Leitura
- **Para que serve:** Calcula a defasagem temporal média (latência) entre o momento em que o evento ocorreu no servidor de origem e a hora em que ele foi gravado no índice.
- **Quando usar:** Para detectar gargalos de fila ou identificar forwarders operando com horários desincronizados de relógio (problemas de NTP).
- **Parâmetros:**
  - `index` *(opcional)*.

### 058. `splunk_get_parsing_errors`
- **Permissão:** Somente Leitura
- **Para que serve:** Varre os logs internos procurando falhas de parsing de timestamp, eventos truncados por estouro de tamanho de linha ou erros de quebra de eventos multilinhas.
- **Quando usar:** Durante a homologação de novas fontes de dados para garantir que os logs estejam sendo interpretados e fatiados corretamente pelo indexador.
- **Parâmetros:**
  - `earliest_time` (padrão: `-24h@h`), `count`.

### 059. `splunk_check_source_coverage`
- **Permissão:** Somente Leitura
- **Para que serve:** Compara as fontes cadastradas com as fontes que efetivamente geraram eventos no período, apontando lacunas de cobertura.
- **Quando usar:** Em auditorias periódicas de conformidade para certificar que 100% dos servidores obrigatórios estão com seus logs ativos.
- **Parâmetros:**
  - `index` *(obrigatório)*.

### 060. `splunk_diagnose_ingestion`
- **Para que serve:** Executa uma avaliação completa e automatizada do pipeline de indexação, integrando análise de filas, status de forwarders e erros de parsing.
- **Quando usar:** Como primeira ferramenta de diagnóstico quando a ingestão do Splunk apresentar lentidão ou quando eventos demorarem para aparecer nas buscas.

---

## Domínio G: Segurança, SIEM & Caça a Ameaças (061 - 070)

### 061. `splunk_detect_failed_logins`
- **Permissão:** Somente Leitura
- **Para que serve:** Varre e consolida todas as tentativas de login com falha em logs do Windows (`EventID 4625`), Linux (`sshd` / `pam`) e auditoria do Splunk.
- **Quando usar:** Em triagens diárias de segurança do SOC para detectar colaboradores errando senhas ou contas sofrendo ataques de tentativa e erro.
- **Parâmetros:**
  - `earliest_time` (padrão: `-24h@h`), `index`, `count`.

### 062. `splunk_detect_brute_force`
- **Permissão:** Somente Leitura
- **Para que serve:** Aplica algoritmos estatísticos e heurísticos para identificar padrões de ataque de força bruta ou pulverização de senhas (*password spraying*).
- **Quando usar:** Para detectar ataques automatizados contra servidores web, APIs ou controladores de domínio.
- **Parâmetros:**
  - `threshold` *(opcional)*: Quantidade mínima de falhas para caracterizar o ataque (padrão: 10).
  - `earliest_time`.

### 063. `splunk_investigate_ip`
- **Permissão:** Somente Leitura
- **Para que serve:** Realiza uma investigação forense 360° sobre um endereço IP, correlacionando conexões de rede, acessos web, tentativas de login e bloqueios em firewalls.
- **Quando usar:** Ao analisar um IP suspeito reportado pelo firewall ou por uma ferramenta de Threat Intelligence.
- **Parâmetros:**
  - `ip_address` *(obrigatório)*: Endereço IPv4 ou IPv6 a investigar.
  - `earliest_time`.

### 064. `splunk_investigate_user`
- **Permissão:** Somente Leitura
- **Para que serve:** Audita todo o histórico de atividade de um usuário específico: logins bem-sucedidos e com falha, pesquisas executadas e alterações de sistema.
- **Quando usar:** Em casos de suspeita de credencial comprometida ou investigação de ameaça interna (*insider threat*).
- **Parâmetros:**
  - `username` *(obrigatório)*: Nome de usuário alvo.
  - `earliest_time`.

### 065. `splunk_investigate_host`
- **Permissão:** Somente Leitura
- **Para que serve:** Consolida todos os eventos associados a um host ou endpoint: processos executados, alterações de registro, usuários logados e conexões de rede.
- **Quando usar:** Na resposta a incidentes quando uma estação ou servidor específico for identificado como ponto de invasão.
- **Parâmetros:**
  - `host` *(obrigatório)*: Nome do computador ou servidor.
  - `earliest_time`.

### 066. `splunk_search_ioc`
- **Permissão:** Somente Leitura
- **Para que serve:** Realiza busca profunda e abrangente por Indicadores de Comprometimento (IOC): hashes de malware (MD5, SHA256), domínios maliciosos ou IPs.
- **Quando usar:** Após a publicação de um novo relatório de inteligência de ameaças para checar se a empresa foi exposta àquele malware.
- **Parâmetros:**
  - `ioc_value` *(obrigatório)*: Hash, IP ou domínio pesquisado.
  - `earliest_time`.

### 067. `splunk_correlate_events`
- **Permissão:** Somente Leitura
- **Para que serve:** Correlaciona cronologicamente eventos de múltiplas fontes distintas (ex: VPN + Active Directory + Firewall) em torno de um mesmo alvo.
- **Quando usar:** Para rastrear a cadeia de ataque (*cyber kill chain*) e entender como o invasor se movimentou pela infraestrutura.
- **Parâmetros:**
  - `pivot_field`, `pivot_value`, `time_window_minutes`.

### 068. `splunk_detect_anomalies`
- **Permissão:** Somente Leitura
- **Para que serve:** Aplica modelos estatísticos de desvio padrão para encontrar picos anormais de tráfego, exfiltração de dados ou disparos incomuns de processos.
- **Quando usar:** Em rotinas de caça a ameaças (*threat hunting*) para descobrir anomalias silenciosas não cobertas por regras de alerta estáticas.
- **Parâmetros:**
  - `index` *(obrigatório)*, `metric_field`, `threshold_stdev`.

### 069. `splunk_get_security_alerts`
- **Permissão:** Somente Leitura
- **Para que serve:** Coleta e sumariza todos os alertas pendentes de triagem categorizados sob a disciplina de segurança da informação.
- **Quando usar:** Para preencher a fila inicial de chamados de segurança de analistas do SOC nível 1 e 2.
- **Parâmetros:**
  - `severity` *(opcional)*: Filtrar por severidade (ex: `critical`, `high`).
  - `count`.

### 070. `splunk_build_incident_timeline`
- **Permissão:** Somente Leitura
- **Para que serve:** Constrói uma linha do tempo cronológica consolidada de todos os acontecimentos antes, durante e após um incidente de segurança.
- **Quando usar:** Para montar o relatório final pós-incidente e apoiar auditorias legais e periciais com comprovação cronológica precisa.
- **Parâmetros:**
  - `entity_value` *(obrigatório)*: IP, host ou usuário pivô do incidente.
  - `incident_time` *(obrigatório)*: Timestamp central do evento.
  - `window_minutes`: Janela de análise anterior e posterior.

---

## Domínio H: Performance & Capacidade do Cluster (071 - 080)

### 071. `splunk_get_search_performance`
- **Permissão:** Somente Leitura
- **Para que serve:** Analisa o desempenho das buscas executadas no Search Head, apresentando tempos médios de resposta, buscas iniciadas e concluídas por usuário.
- **Quando usar:** Para identificar quais analistas ou integrações estão sobrecarregando o Splunk com buscas lentas.
- **Parâmetros:**
  - `earliest_time` (padrão: `-4h`).

### 072. `splunk_detect_slow_searches`
- **Permissão:** Somente Leitura
- **Para que serve:** Identifica e isola consultas SPL que excederam tempos toleráveis de execução ou que consumiram mais de 1GB de memória RAM.
- **Quando usar:** Para realizar ajustes e otimizações contínuas nas regras e painéis corporativos.
- **Parâmetros:**
  - `threshold_seconds` (padrão: 30s).

### 073. `splunk_get_search_concurrency`
- **Permissão:** Somente Leitura
- **Para que serve:** Monitora a quantidade de buscas concorrentes em execução em comparação com os limites máximos permitidos por CPU no servidor.
- **Quando usar:** Para verificar se o Splunk está enfileirando buscas por falta de capacidade simultânea de processamento.

### 074. `splunk_get_scheduler_health`
- **Permissão:** Somente Leitura
- **Para que serve:** Audita a fila do agendador automático de buscas, calculando a taxa de sucesso e apontando buscas agendadas que foram puladas (*skipped searches*).
- **Quando usar:** Para diagnosticar por que determinados relatórios ou alertas periódicos deixaram de rodar no horário programado.

### 075. `splunk_get_internal_errors`
- **Permissão:** Somente Leitura
- **Para que serve:** Varre e sumariza as mensagens de erro de nível `ERROR` e `FATAL` registradas no log interno `_internal` do Splunk.
- **Quando usar:** Em rotinas de suporte e sustentação para verificar a estabilidade interna dos processos do Splunkd.
- **Parâmetros:**
  - `earliest_time` (padrão: `-24h@h`), `count`.

### 076. `splunk_get_license_usage`
- **Permissão:** Somente Leitura
- **Para que serve:** Consulta a cota total de licença, os pools configurados e o volume consumido hoje em Megabytes e Gigabytes.
- **Quando usar:** Diariamente, para prevenir violações de licença (*license warnings*) que bloqueiam a execução de buscas após estouro de cota.

### 077. `splunk_get_storage_usage`
- **Permissão:** Somente Leitura
- **Para que serve:** Audita a ocupação de espaço em disco nas partições do sistema e nos diretórios onde o Splunk armazena os dados (`$SPLUNK_DB`).
- **Quando usar:** Para evitar paradas não planejadas causadas por esgotamento de espaço em disco no servidor.

### 078. `splunk_get_cluster_health`
- **Permissão:** Somente Leitura
- **Para que serve:** Avalia o estado e a conectividade de clusters de Search Head ou clusters de Indexadores (Search Head Clustering / Indexer Clustering).
- **Quando usar:** Em arquiteturas distribuídas com múltiplos nós para verificar se todos os membros estão sincronizados.

### 079. `splunk_get_replication_status`
- **Permissão:** Somente Leitura
- **Para que serve:** Checa se os Fatores de Replicação (RF) e Fatores de Busca (SF) dos buckets de dados do cluster de indexadores foram atendidos integralmente.
- **Quando usar:** Para garantir a redundância e a resiliência dos dados em caso de perda física de um dos servidores indexadores.

### 080. `splunk_diagnose_performance`
- **Permissão:** Somente Leitura
- **Para que serve:** Executa um diagnóstico sistêmico automatizado correlacionando consumo de hardware, concorrência de busca e uso de disco.
- **Quando usar:** Como ferramenta central de triagem quando usuários relatarem lentidão geral na plataforma Splunk.

---

## Domínio I: Ações Operacionais & Gestão (081 - 090)

### 081. `splunk_create_index`
- **Permissão:** Escrita
- **Para que serve:** Cria programaticamente um novo índice no Splunk definindo nome, caminhos de diretório e tamanho máximo em disco.
- **Quando usar:** Ao integrar novos sistemas ou projetos que exigem um índice próprio separado por motivos de governança ou retenção.
- **Parâmetros:**
  - `name` *(obrigatório)*: Nome do novo índice.
  - `max_data_size_mb` *(opcional)*: Tamanho máximo permitido em Megabytes.

### 082. `splunk_update_index_settings`
- **Permissão:** Escrita
- **Para que serve:** Ajusta as configurações de um índice existente, como período de retenção em segundos (`frozen_time_period_in_secs`) ou habilitação/desabilitação.
- **Quando usar:** Para estender a retenção histórica de um índice de auditoria ou arquivar um índice descontinuado.
- **Parâmetros:**
  - `name` *(obrigatório)*: Nome do índice.
  - `frozen_time_period_in_secs`, `max_total_data_size_mb`, `disabled`.

### 083. `splunk_manage_input`
- **Permissão:** Escrita
- **Para que serve:** Habilita (`enable`) ou desabilita (`disable`) operacionalmente uma entrada de dados (monitor de arquivos, porta TCP/UDP ou token HEC).
- **Quando usar:** Para interromper temporariamente a ingestão de um arquivo durante manutenções ou ativar novos monitores de log.
- **Parâmetros:**
  - `input_type` *(obrigatório)*: Tipo de entrada (ex: `monitor`).
  - `name` *(obrigatório)*: Caminho da entrada.
  - `action` *(obrigatório)*: `"enable"` ou `"disable"`.

### 084. `splunk_manage_user`
- **Permissão:** Escrita + Confirmação Humana para exclusão (`confirm=True`)
- **Para que serve:** Gerencia contas de usuários: cria novas credenciais, atualiza perfis e senhas ou exclui usuários definitivamente.
- **Quando usar:** Na automação de onboarding e offboarding de analistas no Splunk.
- **Parâmetros:**
  - `username` *(obrigatório)*: Nome de usuário.
  - `action` *(obrigatório)*: `"create"`, `"update"` ou `"delete"`.
  - `password`, `roles`, `email`, `confirm`.

### 085. `splunk_manage_role`
- **Permissão:** Escrita + Confirmação Humana para exclusão (`confirm=True`)
- **Para que serve:** Cria, atualiza permissões ou exclui perfis e papéis RBAC no Splunk.
- **Quando usar:** Para definir novos níveis de acesso com restrições granulares a índices específicos.
- **Parâmetros:**
  - `role_name` *(obrigatório)*, `action`, `capabilities`, `allowed_indexes`, `confirm`.

### 086. `splunk_manage_app`
- **Permissão:** Escrita + Confirmação Humana para desativação/remoção (`confirm=True`)
- **Para que serve:** Controla o ciclo de vida de aplicativos e add-ons (habilita, desabilita ou atualiza status).
- **Quando usar:** Para ativar um novo Technology Add-on após a sua instalação.
- **Parâmetros:**
  - `app_name` *(obrigatório)*, `action` (`"enable"` ou `"disable"`), `confirm`.

### 087. `splunk_validate_configuration`
- **Permissão:** Somente Leitura
- **Para que serve:** Executa a ferramenta de linha de comando `btool` do Splunk para validar a integridade sintática e verificar conflitos de precedência em arquivos `.conf`.
- **Quando usar:** Após criar ou editar arquivos `.conf` manualmente, para garantir que não há erros de digitação antes de reiniciar o serviço.
- **Parâmetros:**
  - `conf_name` *(obrigatório)*: Nome do arquivo (ex: `props`, `transforms`, `inputs`).

### 088. `splunk_export_search_results`
- **Permissão:** Somente Leitura
- **Para que serve:** Executa uma busca SPL e exporta o conjunto de dados completo nos formatos estruturados JSON ou CSV para consumo externo.
- **Quando usar:** Para alimentar bases de Data Lake externas, gerar relatórios de auditoria para reguladores ou backup de dados de incidentes.
- **Parâmetros:**
  - `spl` *(obrigatório)*, `format` (`"json"` ou `"csv"`), `count`.

### 089. `splunk_submit_event`
- **Permissão:** Escrita
- **Para que serve:** Injeta diretamente eventos sintéticos ou mensagens pontuais em um índice do Splunk via API REST ou HTTP Event Collector (HEC).
- **Quando usar:** Para testes de validação de pipeline de ingestão, simulação de ataques para homologação de alertas de SOC ou gravação de logs de sistemas legados.
- **Parâmetros:**
  - `event_data` *(obrigatório)*: Conteúdo do evento em texto ou JSON.
  - `index` *(opcional)*: Índice de destino (padrão: `main`).
  - `sourcetype`, `host`.

### 090. `splunk_replay_saved_search`
- **Permissão:** Somente Leitura
- **Para que serve:** Reexecuta uma busca salva histórica aplicando exatamente a mesma lógica em uma janela temporal retroativa do passado.
- **Quando usar:** Para auditorias retroativas e reconstituição de incidentes antigos ocorridos em períodos específicos.
- **Parâmetros:**
  - `name` *(obrigatório)*: Nome da busca salva.
  - `earliest_time`, `latest_time`.

---

## Domínio J: Inteligência, Análise & Automação de Workflows (091 - 100)

### 091. `splunk_natural_language_to_spl`
- **Permissão:** Somente Leitura
- **Para que serve:** Traduz pedidos e perguntas expressas em linguagem natural humana para comandos SPL válidos, formatados e otimizados.
- **Quando usar:** Para permitir que analistas não especializados ou agentes de IA formulem queries complexas rapidamente sem necessidade de memorizar comandos avançados de SPL.
- **Parâmetros:**
  - `prompt` *(obrigatório)*: Pergunta ou intenção em linguagem natural (ex: *"Mostre os 10 usuários com mais falhas de login nas últimas 24 horas"*).

### 092. `splunk_optimize_spl`
- **Permissão:** Somente Leitura
- **Para que serve:** Analisa um comando SPL fornecido, identifica gargalos de execução (como comandos de ordenação prematuros ou joins desnecessários) e reescreve a query com maior eficiência.
- **Quando usar:** Antes de agendar buscas periódicas pesadas, para garantir o menor impacto possível na CPU dos indexadores.
- **Parâmetros:**
  - `spl` *(obrigatório)*: Consulta SPL a ser otimizada.

### 093. `splunk_explain_search_results`
- **Permissão:** Somente Leitura
- **Para que serve:** Analisa semanticamente um conjunto de dados resultante de uma busca, resume os principais achados analíticos e responde a dúvidas pontuais do operador sobre os dados.
- **Quando usar:** Para gerar resumos executivos automáticos de relatórios complexos para gestores e lideranças de TI e Segurança.
- **Parâmetros:**
  - `results` *(obrigatório)*: Array de objetos JSON retornados por uma busca.
  - `question` *(opcional)*: Pergunta analítica a ser respondida com base nos dados.

### 094. `splunk_compare_time_periods`
- **Permissão:** Somente Leitura
- **Para que serve:** Executa a mesma métrica SPL em duas janelas temporais distintas (ex: hoje vs. ontem, ou esta semana vs. semana passada) e calcula a variação percentual e absoluta.
- **Quando usar:** Para detecção de tendências de tráfego, identificar desvios após atualizações de versão de sistemas ou medir o impacto de incidentes.
- **Parâmetros:**
  - `metric_spl` *(obrigatório)*: Métrica SPL a comparar (ex: `index=_internal | stats count`).
  - `period1_earliest`, `period1_latest`: Período atual.
  - `period2_earliest`, `period2_latest`: Período de comparação.

### 095. `splunk_detect_data_quality_issues`
- **Permissão:** Somente Leitura
- **Para que serve:** Analisa a consistência dos dados de um índice, apontando campos com alta incidência de valores nulos, discrepâncias de tipos de dados e anomalias de schema.
- **Quando usar:** Em auditorias de engenharia de dados e governança para garantir a qualidade das informações que alimentam dashboards e relatórios analíticos.
- **Parâmetros:**
  - `index` *(obrigatório)*, `sourcetype`.

### 096. `splunk_generate_operational_report`
- **Para que serve:** Compila e formata automaticamente um relatório executivo completo em Markdown sobre a saúde operacional geral do Splunk (licença, erros internos, armazenamento, status dos servidores).
- **Quando usar:** Para geração de relatórios diários de passagem de turno no SOC ou relatórios periódicos de governança para a diretoria.

### 097. `splunk_execute_workflow`
- **Permissão:** Leitura / Escrita (dependendo do fluxo)
- **Para que serve:** Orquestra pipelines sequenciais e automatizadas de investigação de incidentes ou auditorias operacionais pré-programadas (ex: `incident_triage`, `ingestion_audit`).
- **Quando usar:** Para automatizar a triagem inicial de incidentes de segurança (verificar histórico do usuário, falhas de login e anomalias correlacionadas em um único comando).
- **Parâmetros:**
  - `workflow_name` *(obrigatório)*: Nome do fluxo (ex: `"incident_triage"`, `"ingestion_audit"`).
  - `parameters` *(opcional)*: Parâmetros da investigação (ex: `{"entity": "usuario_alvo"}`).

### 098. `splunk_preview_change`
- **Permissão:** Somente Leitura
- **Para que serve:** Simula previamente (*dry-run*) o impacto e os riscos potenciais de uma ação administrativa antes de sua execução real em produção.
- **Quando usar:** Antes de realizar ações de alto impacto (como atualizar configurações de retenção de índices ou excluir objetos) para avaliar riscos e dependências.
- **Parâmetros:**
  - `operation` *(obrigatório)*: Ação pretendida (ex: `"update_index"`, `"delete_saved_search"`).
  - `target` *(obrigatório)*: Recurso alvo.
  - `proposed_settings` *(obrigatório)*: Configurações que seriam aplicadas.

### 099. `splunk_audit_tool_activity`
- **Permissão:** Somente Leitura
- **Para que serve:** Recupera o log de auditoria em memória das últimas ferramentas e requisições executadas pelo servidor MCP, com latências, horários e status.
- **Quando usar:** Para auditar as ações tomadas pelo próprio assistente de IA durante uma sessão de trabalho e garantir total transparência operacional.
- **Parâmetros:**
  - `count` *(opcional)*: Quantidade de registros de auditoria a retornar (padrão: 50).

### 100. `splunk_test_connection`
- **Permissão:** Somente Leitura
- **Para que serve:** Realiza um teste diagnóstico abrangente de ponta a ponta na conexão MCP: valida o handshake HTTP/HTTPS, TLS, autenticação, licença, latência de rede e versão do servidor Splunk.
- **Quando usar:** Sempre que inicializar o servidor MCP ou quando houver suspeita de instabilidade de rede entre o assistente de IA e o Splunk Enterprise.

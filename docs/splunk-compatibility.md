# Matriz de Compatibilidade do Splunk Enterprise

## 1. Versões do Splunk Homologadas

| Versão do Splunk | Status de Suporte | Observações e Recursos |
|---|---|---|
| **Splunk Enterprise 10.6.x** |  **Totalmente Homologado** | Validado contra instância ativa `v10.6.1.1`. Todas as 100 ferramentas testadas e aprovadas com 100% de sucesso. |
| **Splunk Enterprise 10.0.x - 10.5.x** |  **Totalmente Homologado** | Compatibilidade plena com a API REST principal e views Simple XML. |
| **Splunk Enterprise 9.0.x - 9.4.x** |  **Totalmente Homologado** | Suporte total a endpoints REST clássicos, jobs de busca, dashboards e alertas. |
| **Splunk Enterprise 8.2.x** | ⚠️ Suporte Parcial | Funcionalidades legadas; métricas de introspecção do cluster podem apresentar variações de schema. |
| **Splunk Cloud Platform** |  **Homologado** | Conexão via porta de gerenciamento padrão (`8089`) utilizando autenticação com Token JWT Bearer. |

---

## 2. Topologias de Implantação Suportadas

- **Instância Standalone Única (Tudo em um)**: Suportada e testada. O servidor MCP detecta automaticamente a ausência de nós de cluster e devolve respostas informativas para ferramentas de cluster sem falhar.
- **Topologia Distribuída (Search Head + Indexers Distribuídos)**: Suportada. Os jobs de busca são despachados através do Search Head e agregados transparentemente a partir dos nós indexadores.
- **Search Head Cluster (SHC)**: Suportada. Replicação de dashboards e objetos de conhecimento através do nó capitão (*Captain*).
- **Indexer Cluster (IDC)**: Suportada. Auditoria de fatores de replicação de buckets e busca (RF/SF) via endpoints do Cluster Master / Manager.
- **Universal & Heavy Forwarders**: Suportada. Telemetria e conectividade de agentes monitoradas em tempo real através dos pipelines de ingestão TCP (`group=tcpin_connections`).

---

## 3. Portas de Rede e Modos de Conexão

| Modo de Conexão | Porta Padrão | Protocolo | Métodos de Autenticação | Caso de Uso Recomendado |
|---|:---:|:---:|---|---|
| **API REST de Gerenciamento Direta** | `8089` | HTTPS | Bearer Token JWT, Basic Auth, SessionKey | Ambientes corporativos padrão, microserviços e contêineres |
| **Splunk Web Proxy** | `8000` | HTTP / HTTPS | Sessão com Cookies + Token Anti-CSRF (`splunkweb_csrf_token_8000`) | Ambientes onde a porta 8089 é bloqueada por políticas de firewall |
| **HTTP Event Collector (HEC)** | `8088` | HTTP / HTTPS | HEC Authorization Token | Envio de telemetria e eventos sintéticos em alta velocidade |

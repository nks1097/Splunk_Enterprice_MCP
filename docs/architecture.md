# Arquitetura do Servidor MCP para Splunk Enterprise

## 1. Visão Geral do Sistema

O **Servidor Model Context Protocol (MCP) para Splunk Enterprise** estabelece uma ponte bidirecional entre Agentes Inteligentes de Inteligência Artificial (LLMs) e instâncias do Splunk Enterprise, oferecendo interfaces seguras, tipadas, auditadas e tolerantes a falhas.

```mermaid
graph TD
    LLM["Agente de IA / Cliente LLM\n(Claude, Cursor, Antigravity IDE, LangChain)"]
    MCP_STDIO["Camada de Protocolo MCP\n(STDIO / SSE / Streamable HTTP)"]
    GOV["Motor de Política & Governança\n- Enforçamento Read-Only\n- Portão Human-in-the-Loop\n- Redator Automático de Segredos\n- Proteção contra Injeção de Prompt"]
    VAL["Validador de SPL & Custos\n- Parser de Pipeline AST\n- Validação de Janela Temporal\n- Detecção de Anti-Patterns"]
    AUDIT["Motor de Auditoria & Correlação\n- Gerador de Request ID Único\n- Telemetria Estruturada (stderr)"]
    
    subgraph "Matriz das 100 Ferramentas por Domínio"
        DA["Domínio A: Buscas SPL (1-10)"]
        DB["Domínio B: Índices & Descoberta (11-20)"]
        DC["Domínio C: Buscas Salvas & Alertas (21-30)"]
        DD["Domínio D: Dashboards & Relatórios (31-40)"]
        DE["Domínio E: Administração & Configs (41-50)"]
        DF["Domínio F: Ingestão & Forwarders (51-60)"]
        DG["Domínio G: Segurança & SOC (61-70)"]
        DH["Domínio H: Performance & Hardware (71-80)"]
        DI["Domínio I: Gestão Operacional (81-90)"]
        DJ["Domínio J: Inteligência Analítica (91-100)"]
    end

    CLIENT["SplunkClient Core"]
    DIRECT["Splunkd REST API Direta\n(TCP 8089 - HTTPS / Bearer / Basic)"]
    PROXY["Splunk Web Proxy API\n(TCP 8000 - HTTP / Sessão / Anti-CSRF)"]
    SPLUNK["Splunk Enterprise Server\n(Standalone / Distribuído / SHC / Indexer Cluster)"]

    LLM <--> MCP_STDIO
    MCP_STDIO --> GOV
    GOV --> VAL
    VAL --> AUDIT
    AUDIT --> DA & DB & DC & DD & DE & DF & DG & DH & DI & DJ
    DA & DB & DC & DD & DE & DF & DG & DH & DI & DJ --> CLIENT
    CLIENT --> DIRECT & PROXY
    DIRECT & PROXY --> SPLUNK
```

---

## 2. Camadas Arquiteturais Detalhadas

### 1. Camada de Protocolo e Transporte (`mcp.server.mcpserver`)
- **Transporte STDIO (Standard I/O)**: Ideal para integração local com IDEs de desenvolvimento de IA (Claude Desktop, Cursor, Antigravity IDE, Roo Code, Cline). Toda a comunicação JSON-RPC trafega por `sys.stdout`.
- **Isolamento Estrito de Diagnósticos**: Logs internos de depuração, advertências e telemetria são emitidos exclusivamente via `sys.stderr`, garantindo que o canal de dados JSON-RPC permaneça 100% íntegro e sem poluição.
- **Transportes de Rede (SSE & Streamable HTTP)**: Suporte para exposição como microserviço HTTP em contêineres Docker e orquestradores Kubernetes.

### 2. Camada de Governança, Política e Segurança
- **Modo Somente Leitura (`MCP_READ_ONLY=true`)**: Ativado por padrão para proteger ambientes produtivos contra modificações acidentais de índices, papéis de usuário ou dashboards.
- **Portão de Confirmação Humana (*Human-in-the-Loop*)**: Ferramentas com potencial destrutivo (como `splunk_search_cancel`, `splunk_delete_saved_search`, `splunk_delete_dashboard` e remoção de usuários) exigem explicitamente o parâmetro `confirm=True`. Sem isso, uma resposta preventiva com detalhes da ação pretendida é devolvida para validação do operador humano.
- **Defesa Ativa contra Injeção de Prompt**: Logs recuperados de sistemas externos podem conter instruções maliciosas injetadas por invasores. O servidor encapsula esses registros no container `UntrustedEventData`, acompanhado de cabeçalhos de segurança obrigatórios para o modelo de linguagem.
- **Redator Automático de Segredos**: Higieniza automaticamente tokens Bearer, senhas, chaves privadas e cookies de sessão (`splunkd_*`) antes de devolver qualquer resposta ou registrar logs de auditoria.

### 3. Validador de SPL e Otimizador de Consultas (`SPLValidator`)
- **Decomposição em AST (Árvore Sintática Abstrata)**: Processa e decompõe cada estágio do pipeline SPL (`search`, `stats`, `eval`, `dedup`, `table`, etc.).
- **Bloqueio de Comandos Perigosos**: Impede a execução de comandos capazes de apagar dados ou gravar artefatos arbitrários (`delete`, `outputcsv`, `outputlookup`, `script`).
- **Verificação de Limites Temporais**: Garante a presença de cláusulas `earliest` e `latest`, prevenindo buscas irrestritas que consumiriam memória excessiva no cluster de indexadores.
- **Detecção de Anti-Patterns**: Alerta sobre wildcards no início de strings (`*termo`) ou ausência de filtro de índice (`index=`).

### 4. Cliente Splunk Multi-Conexão (`SplunkClient`)
- **Modo Direto (Porta 8089 - HTTPS)**: Comunicação direta com a API REST do daemon `splunkd`.
- **Modo Web Proxy (Porta 8000 - HTTP/HTTPS)**: Negocia automaticamente autenticação de sessão via cookies e tokens CSRF (`splunkweb_csrf_token_8000`), viabilizando a integração mesmo em redes restritas onde a porta de gerenciamento padrão está bloqueada.

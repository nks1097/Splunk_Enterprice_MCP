# Splunk Enterprise MCP Server Architecture

## 1. System Overview

The **Splunk Enterprise Model Context Protocol (MCP) Server** bridges Large Language Model (LLM) reasoning agents with Splunk Enterprise through typed, secure, audited, and resilient interfaces.

```mermaid
graph TD
    LLM["AI Agent / LLM Client\n(Claude, Cursor, Copilot, LangChain)"]
    MCP_STDIO["MCP Transport Layer\n(STDIO / SSE / Streamable HTTP)"]
    GOV["Policy & Governance Engine\n- Read-Only Enforcer\n- Destructive Action Guard\n- Secret Redactor\n- Prompt Injection Defense"]
    VAL["SPL Validation & Cost Engine\n- AST Pipeline Parser\n- Time Bound Enforcer\n- Anti-Pattern Detector"]
    AUDIT["Audit & Correlation Engine\n- Request ID Generator\n- Telemetry Store (stderr)"]
    
    subgraph "Domain Tool Matrix (100 Tools)"
        DA["Domain A: SPL Search (1-10)"]
        DB["Domain B: Discovery (11-20)"]
        DC["Domain C: Saved Searches (21-30)"]
        DD["Domain D: Dashboards (31-40)"]
        DE["Domain E: Administration (41-50)"]
        DF["Domain F: Ingestion (51-60)"]
        DG["Domain G: Security / SIEM (61-70)"]
        DH["Domain H: Performance (71-80)"]
        DI["Domain I: Operations (81-90)"]
        DJ["Domain J: Intelligence (91-100)"]
    end

    CLIENT["SplunkClient Core"]
    DIRECT["Direct Splunkd REST API\n(TCP 8089 - HTTPS/Bearer/Basic)"]
    PROXY["Splunk Web Proxy API\n(TCP 8000 - HTTP/Session/CSRF)"]
    SPLUNK["Splunk Enterprise Server\n(Standalone / Distributed / SHC / IDX Cluster)"]

    LLM <--> MCP_STDIO
    MCP_STDIO --> GOV
    GOV --> VAL
    VAL --> AUDIT
    AUDIT --> DA & DB & DC & DD & DE & DF & DG & DH & DI & DJ
    DA & DB & DC & DD & DE & DF & DG & DH & DI & DJ --> CLIENT
    CLIENT --> DIRECT & PROXY
    DIRECT & PROXY --> SPLUNK
```

## 2. Layered Architecture

1. **Protocol & Transport Layer (`mcp.server.mcpserver`)**:
   - Supports Standard I/O (`stdio`) for local desktop IDE agents (e.g. Claude Desktop, VS Code, Antigravity IDE).
   - Supports Server-Sent Events (`sse`) and Streamable HTTP (`streamable-http`) for microservices and Kubernetes deployments.
   - Strictly redirects all operational diagnostics to `sys.stderr` so the JSON-RPC STDIO pipe on `sys.stdout` remains pristine.

2. **Policy, Governance, and Security Guard**:
   - **Read-Only Mode (`MCP_READ_ONLY=true`)**: Activated by default. Blocks mutating actions (index creation, app toggling, user removal, query deletion) unless explicitly overridden by enterprise policy.
   - **Human Confirmation Gate**: High-impact destructive tools require explicit `confirm=True`. If omitted, the server returns an explanatory confirmation warning with the target resource details.
   - **Secret Redaction**: Recursively strips passwords, Bearer tokens, Splunk session cookies (`splunkd_*`), and JWT signatures from error messages, debug logs, and tool payloads.
   - **Prompt Injection Defense**: Encapsulates raw log records in `UntrustedEventData` boundaries with strict system advisories warning LLMs not to interpret log lines as executable instructions.

3. **SPL Validation & Cost Engine (`SPLValidator`)**:
   - Parses the command pipeline (`search`, `stats`, `dedup`, `eval`, `sort`, `join`).
   - Rejects mutating commands (`delete`, `outputcsv`, `outputlookup`, `script`, `run`) during read-only operation.
   - Flags anti-patterns (leading wildcards `*term`, missing `index=` filter, expensive joins).
   - Suggests optimized query structures.

4. **Dual-Mode Splunk Connectivity Client (`SplunkClient`)**:
   - **Direct Management REST API**: Connects via HTTPS on standard port `8089` using Bearer Tokens or Basic Authentication.
   - **Splunk Web Proxy API**: Connects via HTTP/HTTPS on port `8000` (`/en-US/splunkd/__raw/services/*`) with automated cookie and CSRF token negotiation (`splunkweb_csrf_token_8000`, `splunkd_8000`), allowing operations even in environments where port 8089 is firewall-blocked.

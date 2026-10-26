# Splunk Enterprise MCP Deployment Guide

This guide covers deploying the Splunk Enterprise MCP Server across local developer environments, AI IDE agents, and enterprise production infrastructure.

---

## 1. Local IDE Integration (STDIO Transport)

### Claude Desktop / Antigravity IDE Configuration
Add the server entry to your MCP configuration file (`claude_desktop_config.json` or `mcp_config.json`):

```json
{
  "mcpServers": {
    "splunk": {
      "command": "python",
      "args": ["-m", "splunk_mcp.server", "--transport", "stdio"],
      "cwd": "C:/Users/Natanael Krindges/.gemini/antigravity/mcp/Splunk_Enterprice_MCP",
      "env": {
        "SPLUNK_HOST": "192.168.0.107",
        "SPLUNK_PORT": "8000",
        "SPLUNK_SCHEME": "http",
        "SPLUNK_USERNAME": "admin",
        "SPLUNK_PASSWORD": "your-password-here",
        "SPLUNK_TOKEN": "your-splunk-bearer-token",
        "SPLUNK_VERIFY_TLS": "false",
        "MCP_READ_ONLY": "true"
      }
    }
  }
}
```

---

## 2. Docker & Container Deployment

### Build the Image
```bash
docker build -t splunk-enterprise-mcp:latest .
```

### Run with Docker Compose
```bash
docker compose up -d
```

### Standalone Docker Run
```bash
docker run -d \
  --name splunk-mcp \
  --restart unless-stopped \
  -p 8001:8001 \
  --env-file .env \
  splunk-enterprise-mcp:latest \
  --transport sse --host 0.0.0.0 --port 8001
```

---

## 3. Remote HTTP / SSE Microservice Architecture

In distributed environments, the server can be deployed as an independent SSE endpoint:
- **Port**: `8001`
- **Endpoints**:
  - `GET /sse` — Establishes SSE stream connection
  - `POST /messages` — Dispatches JSON-RPC tool invocation requests
- **Healthcheck**:
  ```bash
  curl -I http://localhost:8001/sse
  ```

---

## 4. Production Hardening Checklist

1. **Service Accounts**: Create a dedicated least-privilege Splunk service account (`svc_mcp_agent`) with access only to designated indexes.
2. **Read-Only Mode**: Ensure `MCP_READ_ONLY=true` in production monitoring and investigation environments.
3. **TLS Validation**: Enable `SPLUNK_VERIFY_TLS=true` and mount internal corporate CA certificates with `SPLUNK_CA_BUNDLE`.
4. **Rate Limits & Caps**: Set `SPLUNK_MAX_RESULTS` (default: 1000) and `SPLUNK_MAX_CONCURRENT_SEARCHES` (default: 5) to safeguard search head performance.

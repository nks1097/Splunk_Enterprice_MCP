# Guia de Implantação e Produção do Splunk MCP

Este documento orienta a implantação do Servidor MCP para Splunk Enterprise em diferentes cenários corporativos, desde o desenvolvimento local com IDEs de IA até clusters containerizados em produção.

---

## 1. Integração com IDEs Locais (Transporte STDIO)

O transporte Standard Input/Output (`stdio`) é a forma recomendada para conectar assistentes de IA instalados na máquina do desenvolvedor ou analista de SOC.

### Preparação do Ambiente Virtual Python

**No Windows (PowerShell):**

> [!TIP]
> Caso o PowerShell bloqueie a execução de scripts (`running scripts is disabled on this system`), libere a permissão para o seu usuário antes de ativar o ambiente:

```powershell
# 1. Liberar execução de scripts para o usuário atual
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# (Pressione 'S' ou 'A' para confirmar)

# 2. Criar e ativar o ambiente virtual
python -m venv .venv
.\.venv\Scripts\activate

# 3. Instalar dependências em modo de desenvolvimento
pip install -e ".[dev]"
```

**No Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Arquivo de Configuração do Cliente MCP

Dependendo da sua ferramenta, adicione o bloco JSON no arquivo correspondente:
- **Claude Desktop:** `%APPDATA%\Claude\claude_desktop_config.json` (Windows) ou `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS/Linux)
- **Antigravity IDE:** `~/.gemini/config/mcp_config.json`
- **Cursor:** `.cursor/mcp.json` na raiz do seu projeto

```json
{
  "mcpServers": {
    "splunk": {
      "command": "python",
      "args": ["-m", "splunk_mcp.server", "--transport", "stdio"],
      "cwd": "C:/caminho/para/Splunk_Enterprice_MCP",
      "env": {
        "SPLUNK_HOST": "192.168.0.107",
        "SPLUNK_PORT": "8000",
        "SPLUNK_SCHEME": "http",
        "SPLUNK_USERNAME": "admin",
        "SPLUNK_PASSWORD": "sua_senha_aqui",
        "SPLUNK_VERIFY_TLS": "false",
        "MCP_READ_ONLY": "false"
      }
    }
  }
}
```

---

## 2. Implantação Containerizada (Docker & Docker Compose)

Para disponibilizar o servidor MCP como um serviço de rede centralizado acessível por múltiplos agentes ou sistemas de orquestração (via protocolo SSE ou Streamable HTTP):

### Construção da Imagem Docker
```bash
docker build -t splunk-enterprise-mcp:latest .
```

### Inicialização com Docker Compose
```bash
docker compose up -d
```

### Execução Direta via Docker CLI
```bash
docker run -d \
  --name splunk-mcp-server \
  --restart unless-stopped \
  -p 8001:8001 \
  --env-file .env \
  splunk-enterprise-mcp:latest \
  --transport sse --host 0.0.0.0 --port 8001
```

### Teste de Conectividade e Saúde do Container
```bash
curl -I http://localhost:8001/sse
```

---

## 3. Implantação como Serviço de Sistema no Linux (Systemd)

Para manter o servidor MCP rodando continuamente em um servidor Linux dedicado:

Crie o arquivo `/etc/systemd/system/splunk-mcp.service`:

```ini
[Unit]
Description=Splunk Enterprise MCP Server
After=network.target

[Service]
Type=simple
User=splunkmcp
WorkingDirectory=/opt/Splunk_Enterprice_MCP
ExecStart=/opt/Splunk_Enterprice_MCP/.venv/bin/python -m splunk_mcp.server --transport sse --host 0.0.0.0 --port 8001
EnvironmentFile=/opt/Splunk_Enterprice_MCP/.env
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Ative e inicie o serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable splunk-mcp
sudo systemctl start splunk-mcp
sudo systemctl status splunk-mcp
```

---

## 4. Recomendações de Segurança para Produção

1. **Utilize Credenciais de Menor Privilégio**: Crie um usuário dedicado no Splunk (ex: `svc_mcp_agent`) associado a um perfil que tenha acesso restrito apenas aos índices e permissões necessárias.
2. **Habilite TLS/HTTPS**: Em ambientes produtivos com tráfego externo, utilize certificados válidos assinados por autoridade certificadora e configure `SPLUNK_VERIFY_TLS=true`.
3. **Mantenha o Modo Read-Only Ativo Inicialmente**: Recomenda-se iniciar com `MCP_READ_ONLY=true` e habilitar `MCP_READ_ONLY=false` apenas quando houver necessidade de criação de dashboards ou manipulação programática de alertas.

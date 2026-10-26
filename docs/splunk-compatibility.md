# Splunk Compatibility Matrix

## 1. Supported Splunk Versions

| Version | Status | Notes |
|---|---|---|
| **Splunk Enterprise 10.6.x** | Fully Supported | Verified against live instance `v10.6.1.1`. All 100 tools operational. |
| **Splunk Enterprise 10.0.x - 10.5.x** | Fully Supported | Core REST API and Simple XML views compatible. |
| **Splunk Enterprise 9.0.x - 9.4.x** | Fully Supported | Standard REST endpoints, search jobs, and alerting compatible. |
| **Splunk Enterprise 8.2.x** | Partially Supported | Legacy features; some introspection metrics may vary. |
| **Splunk Cloud Platform** | Supported | Accessible via standard management port (8089) with JWT Bearer Token. |

---

## 2. Supported Deployment Topologies

- **Standalone Single-Instance**: Supported (verified). Non-clustered mode handled gracefully with informational notices for cluster tools.
- **Distributed Search Head + Indexers**: Supported. Dispatches search jobs through Search Head and aggregates across indexer peers.
- **Search Head Cluster (SHC)**: Supported. Replicates knowledge objects through SHC captain.
- **Indexer Cluster (IDC)**: Supported. Queries bucket replication and peer status via cluster master endpoints.
- **Universal & Heavy Forwarders**: Supported. Telemetry monitored via `group=tcpin_connections`.

---

## 3. Network Ports & Connection Modes

| Mode | Port | Protocol | Auth Methods | Use Case |
|---|---|---|---|---|
| **Direct Management REST** | 8089 | HTTPS | Bearer Token, Basic Auth, SessionKey | Standard enterprise deployments, microservices |
| **Splunk Web Proxy** | 8000 | HTTP / HTTPS | Cookie Session + CSRF (`splunkweb_csrf_token_8000`) | Environments where port 8089 is restricted by firewalls |
| **HTTP Event Collector (HEC)** | 8088 | HTTP / HTTPS | HEC Token | Synthetic event submission |

# Splunk Enterprise MCP - 100 Tools Reference Catalog

The server exposes **100 typed tools** grouped into 10 domains. All tools return the standard `ToolResult` envelope:
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "warnings": [],
  "request_id": "uuid-or-sid",
  "metadata": {
    "duration_ms": 14.2,
    "truncated": false,
    "next_offset": null,
    "server_version": "10.6.1.1",
    "read_only": true
  }
}
```

---

## Domain A: SPL Search and Execution (1 - 10)

| Tool | Permission | Description |
|---|---|---|
| `splunk_search` | Read | Execute synchronous blocking SPL query within an explicit time window. |
| `splunk_search_stream` | Read | Stream search results progressively via export endpoint. |
| `splunk_search_async` | Read | Initiate background search job and return Job SID immediately. |
| `splunk_search_status` | Read | Query execution status, scan progress, and event counts by SID. |
| `splunk_search_results` | Read | Fetch paginated results for a completed or running job (`offset`, `count`). |
| `splunk_search_events` | Read | Fetch raw events with prompt injection protection. |
| `splunk_search_preview` | Read | Retrieve preliminary results from in-progress search. |
| `splunk_search_cancel` | Write + Confirm | Terminate and cancel an active search job. |
| `splunk_search_explain` | Read | Parse SPL query, check risks, estimate execution cost, and suggest fixes. |
| `splunk_search_history` | Read | Query search history and recently dispatched user jobs. |

---

## Domain B: Indexes, Events & Data Discovery (11 - 20)

| Tool | Permission | Description |
|---|---|---|
| `splunk_list_indexes` | Read | List accessible indexes with event counts, disk size, and retention settings. |
| `splunk_get_index` | Read | Retrieve detailed stanza configuration and disk paths for an index. |
| `splunk_index_stats` | Read | Retrieve aggregate storage statistics and event volumes across all indexes. |
| `splunk_list_sourcetypes`| Read | Discover observed sourcetypes with event totals and latest seen timestamps. |
| `splunk_list_sources` | Read | List event sources discovered across indexes. |
| `splunk_list_hosts` | Read | Discover reporting hosts with activity metrics. |
| `splunk_get_field_summary`| Read | Calculate statistical distribution and top values for extracted fields. |
| `splunk_get_data_freshness`| Read | Evaluate data recency, latest event timestamp, and ingestion latency. |
| `splunk_search_data_gaps` | Read | Detect time gaps where event throughput dropped to 0. |
| `splunk_sample_events` | Read | Retrieve representative event samples without full table scans. |

---

## Domain C: Saved Searches, Reports & Alerts (21 - 30)

| Tool | Permission | Description |
|---|---|---|
| `splunk_list_saved_searches` | Read | List saved searches, alerts, and scheduled reports. |
| `splunk_get_saved_search` | Read | Retrieve SPL query, schedule, and actions of a saved search. |
| `splunk_create_saved_search`| Write | Create a new saved search or scheduled report. |
| `splunk_update_saved_search`| Write | Update SPL query, schedule, or description of a saved search. |
| `splunk_delete_saved_search`| Write + Confirm | Delete a saved search (guarded by human confirmation). |
| `splunk_dispatch_saved_search`| Read / Write | Dispatch saved search immediately and return new Job SID. |
| `splunk_list_alerts` | Read | List configured alerts and triggered alert records. |
| `splunk_get_alert_history` | Read | Query historical fired alerts over a time range. |
| `splunk_acknowledge_alert` | Write | Mark an alert finding as acknowledged with operational comments. |
| `splunk_manage_alert_suppression` | Write | Configure alert suppression intervals to prevent notification fatigue. |

---

## Domain D: Dashboards & Knowledge Objects (31 - 40)

| Tool | Permission | Description |
|---|---|---|
| `splunk_list_dashboards` | Read | List Simple XML and Dashboard Studio views. |
| `splunk_get_dashboard` | Read | Retrieve XML/JSON definition and panels of a dashboard. |
| `splunk_create_dashboard` | Write | Create a new dashboard with title and layout. |
| `splunk_update_dashboard` | Write | Update XML/JSON layout of an existing dashboard. |
| `splunk_delete_dashboard` | Write + Confirm | Delete a dashboard (requires human confirmation). |
| `splunk_list_reports` | Read | List interactive and scheduled reports. |
| `splunk_run_report` | Read | Execute a named report and return generated results. |
| `splunk_list_eventtypes` | Read | List configured eventtypes and search patterns. |
| `splunk_list_tags` | Read | List tags mapped across fields and knowledge objects. |
| `splunk_list_macros` | Read | List search macros, arguments, and definition strings. |

---

## Domain E: Administration & Configurations (41 - 50)

| Tool | Permission | Description |
|---|---|---|
| `splunk_get_server_info` | Read | Retrieve host name, Splunk version, OS, build, and license state. |
| `splunk_get_server_health` | Read | Retrieve system health report, status features, and warnings. |
| `splunk_list_apps` | Read | List installed Splunk apps and add-ons with versions. |
| `splunk_get_app_details` | Read | Get detailed configuration and permissions for an app. |
| `splunk_list_users` | Read | List user accounts, roles, and status (secrets redacted). |
| `splunk_get_user` | Read | Get details, email, and assigned roles of a specific user. |
| `splunk_list_roles` | Read | List configured roles and allowed search indexes. |
| `splunk_get_role_capabilities` | Read | Inspect granular capabilities assigned to a role. |
| `splunk_list_configurations` | Read | List `.conf` configuration files accessible via REST properties. |
| `splunk_get_configuration` | Read | Read configuration stanzas with passwords scrubbed. |

---

## Domain F: Ingestion & Forwarders (51 - 60)

| Tool | Permission | Description |
|---|---|---|
| `splunk_list_inputs` | Read | List active data inputs (monitor, TCP, UDP, HEC). |
| `splunk_get_input` | Read | Get configuration details of an input stanza. |
| `splunk_list_forwarders` | Read | List Universal and Heavy Forwarders observed in indexing pipeline. |
| `splunk_get_forwarder_status` | Read | Check status, latency, and throughput of a specific forwarder. |
| `splunk_check_forwarder_connectivity` | Read | Detect silent or missing forwarders exceeding inactivity threshold. |
| `splunk_get_ingestion_metrics` | Read | Retrieve hourly ingestion throughput (MB/hour) by index. |
| `splunk_get_ingestion_lag` | Read | Measure delay between event occurrence time and index time. |
| `splunk_get_parsing_errors` | Read | Query timestamp parsing, line-breaking, and regex errors. |
| `splunk_check_source_coverage` | Read | Verify that expected data sources are actively transmitting data. |
| `splunk_diagnose_ingestion` | Read | Composite assessment of pipeline health, queue fill %, and bottlenecks. |

---

## Domain G: Security, SIEM & Forensics (61 - 70)

| Tool | Permission | Description |
|---|---|---|
| `splunk_detect_failed_logins` | Read | Query and aggregate failed authentication events across telemetry. |
| `splunk_detect_brute_force` | Read | Detect password spraying or brute force patterns by threshold. |
| `splunk_investigate_ip` | Read | Forensic investigation of IP address across firewall, auth, and web logs. |
| `splunk_investigate_user` | Read | Audit user activity, login anomalies, and admin actions. |
| `splunk_investigate_host` | Read | Investigate system logs, processes, and errors for a specific host. |
| `splunk_search_ioc` | Read | Search for Indicators of Compromise (hashes, IPs, domains) across indexes. |
| `splunk_correlate_events` | Read | Correlate multi-source events occurring in a synchronized time window. |
| `splunk_detect_anomalies` | Read | Run statistical outlier detection on time series volume. |
| `splunk_get_security_alerts` | Read | Retrieve security alerts and high-severity trigger events. |
| `splunk_build_incident_timeline` | Read | Composite reconstruction of chronological incident timeline for an entity. |

---

## Domain H: Performance & Capacity (71 - 80)

| Tool | Permission | Description |
|---|---|---|
| `splunk_get_search_performance` | Read | Inspect search execution times and resource utilization by user. |
| `splunk_detect_slow_searches` | Read | Identify expensive searches exceeding duration threshold. |
| `splunk_get_search_concurrency` | Read | Inspect active concurrent searches against system limits. |
| `splunk_get_scheduler_health` | Read | Check search scheduler health, skipped searches, and delayed jobs. |
| `splunk_get_internal_errors` | Read | Query daemon errors logged in `index=_internal log_level=ERROR`. |
| `splunk_get_license_usage` | Read | Retrieve daily license quota, consumed bytes, and pool breakdown. |
| `splunk_get_storage_usage` | Read | Inspect filesystem disk space and partition utilization. |
| `splunk_get_cluster_health` | Read | Check indexer or search head cluster health status. |
| `splunk_get_replication_status` | Read | Check bucket replication status and sync health. |
| `splunk_diagnose_performance` | Read | Composite multi-dimensional performance diagnostic. |

---

## Domain I: Operational Administration (81 - 90)

| Tool | Permission | Description |
|---|---|---|
| `splunk_create_index` | Write | Create a new index with storage and retention limits. |
| `splunk_update_index_settings` | Write | Modify storage quotas or disable/enable an index. |
| `splunk_manage_input` | Write | Enable or disable a data input stanza. |
| `splunk_manage_user` | Write + Confirm | Create, modify, or delete a Splunk user account. |
| `splunk_manage_role` | Write + Confirm | Create, modify, or delete a security role. |
| `splunk_manage_app` | Write + Confirm | Enable or disable a Splunk application. |
| `splunk_validate_configuration`| Read | Audit `.conf` files for syntax errors or stanza conflicts. |
| `splunk_export_search_results` | Read | Export query results to JSON, CSV, or raw formats. |
| `splunk_submit_event` | Write | Submit a synthetic event or test log into an index. |
| `splunk_replay_saved_search` | Read / Write | Re-run a saved search over a historical time range. |

---

## Domain J: Intelligence & Governance (91 - 100)

| Tool | Permission | Description |
|---|---|---|
| `splunk_natural_language_to_spl` | Read | Convert natural language requirements into optimized, secure SPL. |
| `splunk_optimize_spl` | Read | Detect performance anti-patterns and generate optimized SPL. |
| `splunk_explain_search_results`| Read | Summarize and explain search result trends and outliers. |
| `splunk_compare_time_periods` | Read | Compare metrics between two distinct time periods (current vs. prior). |
| `splunk_detect_data_quality_issues`| Read | Audit an index for null values, clock skew, and schema drift. |
| `splunk_generate_operational_report`| Read | Generate an executive Markdown operational health report. |
| `splunk_execute_workflow` | Read | Execute multi-step orchestrated troubleshooting or triage workflows. |
| `splunk_preview_change` | Read | Simulate the impact of an administrative modification before applying it. |
| `splunk_audit_tool_activity` | Read | Retrieve local MCP audit log records of actions executed by the agent. |
| `splunk_test_connection` | Read | Verify end-to-end connectivity, TLS, version, and latency. |

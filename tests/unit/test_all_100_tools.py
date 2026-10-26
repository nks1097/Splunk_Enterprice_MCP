"""Comprehensive unit test suite verifying execution and contracts for all 100 MCP tools."""

import pytest

from splunk_mcp.config import Settings, set_settings
from splunk_mcp.tools import (
    splunk_acknowledge_alert,
    splunk_audit_tool_activity,
    splunk_build_incident_timeline,
    splunk_check_forwarder_connectivity,
    splunk_check_source_coverage,
    splunk_compare_time_periods,
    splunk_correlate_events,
    splunk_create_dashboard,
    splunk_create_index,
    splunk_create_saved_search,
    splunk_delete_dashboard,
    splunk_delete_saved_search,
    splunk_detect_anomalies,
    splunk_detect_brute_force,
    splunk_detect_data_quality_issues,
    splunk_detect_failed_logins,
    splunk_detect_slow_searches,
    splunk_diagnose_ingestion,
    splunk_diagnose_performance,
    splunk_dispatch_saved_search,
    splunk_execute_workflow,
    splunk_explain_search_results,
    splunk_export_search_results,
    splunk_generate_operational_report,
    splunk_get_alert_history,
    splunk_get_app_details,
    splunk_get_cluster_health,
    splunk_get_configuration,
    splunk_get_dashboard,
    splunk_get_data_freshness,
    splunk_get_field_summary,
    splunk_get_forwarder_status,
    splunk_get_index,
    splunk_get_ingestion_lag,
    splunk_get_ingestion_metrics,
    splunk_get_input,
    splunk_get_internal_errors,
    splunk_get_license_usage,
    splunk_get_parsing_errors,
    splunk_get_replication_status,
    splunk_get_role_capabilities,
    splunk_get_saved_search,
    splunk_get_scheduler_health,
    splunk_get_search_concurrency,
    splunk_get_search_performance,
    splunk_get_security_alerts,
    splunk_get_server_health,
    splunk_get_server_info,
    splunk_get_storage_usage,
    splunk_get_user,
    splunk_index_stats,
    splunk_investigate_host,
    splunk_investigate_ip,
    splunk_investigate_user,
    splunk_list_alerts,
    splunk_list_apps,
    splunk_list_configurations,
    splunk_list_dashboards,
    splunk_list_eventtypes,
    splunk_list_forwarders,
    splunk_list_hosts,
    splunk_list_indexes,
    splunk_list_inputs,
    splunk_list_macros,
    splunk_list_reports,
    splunk_list_roles,
    splunk_list_saved_searches,
    splunk_list_sources,
    splunk_list_sourcetypes,
    splunk_list_tags,
    splunk_list_users,
    splunk_manage_alert_suppression,
    splunk_manage_app,
    splunk_manage_input,
    splunk_manage_role,
    splunk_manage_user,
    splunk_natural_language_to_spl,
    splunk_optimize_spl,
    splunk_preview_change,
    splunk_replay_saved_search,
    splunk_run_report,
    splunk_sample_events,
    splunk_search,
    splunk_search_async,
    splunk_search_cancel,
    splunk_search_data_gaps,
    splunk_search_events,
    splunk_search_explain,
    splunk_search_history,
    splunk_search_ioc,
    splunk_search_preview,
    splunk_search_results,
    splunk_search_status,
    splunk_search_stream,
    splunk_submit_event,
    splunk_test_connection,
    splunk_update_dashboard,
    splunk_update_index_settings,
    splunk_update_saved_search,
    splunk_validate_configuration,
)


@pytest.mark.asyncio
async def test_domain_a_search_tools(mock_client):
    # 1. splunk_search
    res1 = await splunk_search(spl="index=main | head 5")
    assert res1.success is True
    assert "records" in res1.data

    # 2. splunk_search_stream
    res2 = await splunk_search_stream(spl="index=main | head 5")
    assert res2.success is True

    # 3. splunk_search_async
    res3 = await splunk_search_async(spl="index=main | stats count")
    assert res3.success is True
    assert "sid" in res3.data

    # 4. splunk_search_status
    res4 = await splunk_search_status(sid="mock_sid_1")
    assert res4.success is True
    assert res4.data["is_done"] is True

    # 5. splunk_search_results
    res5 = await splunk_search_results(sid="mock_sid_1")
    assert res5.success is True

    # 6. splunk_search_events
    res6 = await splunk_search_events(sid="mock_sid_1")
    assert res6.success is True

    # 7. splunk_search_preview
    res7 = await splunk_search_preview(sid="mock_sid_1")
    assert res7.success is True

    # 8. splunk_search_cancel (Write tool + confirm)
    set_settings(Settings(mcp_read_only=False))
    res8 = await splunk_search_cancel(sid="mock_sid_1", confirm=True)
    assert res8.success is True
    set_settings(Settings(mcp_read_only=True))

    # 9. splunk_search_explain
    res9 = await splunk_search_explain(spl="index=main | head 10")
    assert res9.success is True

    # 10. splunk_search_history
    res10 = await splunk_search_history()
    assert res10.success is True


@pytest.mark.asyncio
async def test_domain_b_data_discovery_tools(mock_client):
    # 11. splunk_list_indexes
    r11 = await splunk_list_indexes()
    assert r11.success is True
    assert len(r11.data["indexes"]) > 0

    # 12. splunk_get_index
    r12 = await splunk_get_index(name="main")
    assert r12.success is True

    # 13. splunk_index_stats
    r13 = await splunk_index_stats()
    assert r13.success is True

    # 14. splunk_list_sourcetypes
    r14 = await splunk_list_sourcetypes()
    assert r14.success is True

    # 15. splunk_list_sources
    r15 = await splunk_list_sources()
    assert r15.success is True

    # 16. splunk_list_hosts
    r16 = await splunk_list_hosts()
    assert r16.success is True

    # 17. splunk_get_field_summary
    r17 = await splunk_get_field_summary(index="main")
    assert r17.success is True

    # 18. splunk_get_data_freshness
    r18 = await splunk_get_data_freshness(index="main")
    assert r18.success is True

    # 19. splunk_search_data_gaps
    r19 = await splunk_search_data_gaps(index="main")
    assert r19.success is True

    # 20. splunk_sample_events
    r20 = await splunk_sample_events(index="main")
    assert r20.success is True


@pytest.mark.asyncio
async def test_domain_c_saved_searches_tools(mock_client):
    set_settings(Settings(mcp_read_only=False))

    # 21. splunk_list_saved_searches
    r21 = await splunk_list_saved_searches()
    assert r21.success is True

    # 22. splunk_get_saved_search
    r22 = await splunk_get_saved_search(name="Test Alert")
    assert r22.success is True

    # 23. splunk_create_saved_search
    r23 = await splunk_create_saved_search(name="New Alert", search="index=main | stats count")
    assert r23.success is True

    # 24. splunk_update_saved_search
    r24 = await splunk_update_saved_search(name="New Alert", description="Updated description")
    assert r24.success is True

    # 25. splunk_delete_saved_search (requires confirm=True)
    r25 = await splunk_delete_saved_search(name="New Alert", confirm=True)
    assert r25.success is True

    # 26. splunk_dispatch_saved_search
    r26 = await splunk_dispatch_saved_search(name="Test Alert")
    assert r26.success is True

    # 27. splunk_list_alerts
    r27 = await splunk_list_alerts()
    assert r27.success is True

    # 28. splunk_get_alert_history
    r28 = await splunk_get_alert_history()
    assert r28.success is True

    # 29. splunk_acknowledge_alert
    r29 = await splunk_acknowledge_alert(alert_id="alert_101")
    assert r29.success is True

    # 30. splunk_manage_alert_suppression
    r30 = await splunk_manage_alert_suppression(alert_name="Test Alert", suppression_period="1h")
    assert r30.success is True

    set_settings(Settings(mcp_read_only=True))


@pytest.mark.asyncio
async def test_domain_d_dashboards_tools(mock_client):
    set_settings(Settings(mcp_read_only=False))

    # 31. splunk_list_dashboards
    r31 = await splunk_list_dashboards()
    assert r31.success is True

    # 32. splunk_get_dashboard
    r32 = await splunk_get_dashboard(name="operations_overview")
    assert r32.success is True

    # 33. splunk_create_dashboard
    r33 = await splunk_create_dashboard(name="dash_1", label="Dash 1", xml_data="<dashboard/>")
    assert r33.success is True

    # 34. splunk_update_dashboard
    r34 = await splunk_update_dashboard(name="dash_1", xml_data="<dashboard><label>Updated</label></dashboard>")
    assert r34.success is True

    # 35. splunk_delete_dashboard
    r35 = await splunk_delete_dashboard(name="dash_1", confirm=True)
    assert r35.success is True

    # 36. splunk_list_reports
    r36 = await splunk_list_reports()
    assert r36.success is True

    # 37. splunk_run_report
    r37 = await splunk_run_report(name="Sample Report")
    assert r37.success is True

    # 38. splunk_list_eventtypes
    r38 = await splunk_list_eventtypes()
    assert r38.success is True

    # 39. splunk_list_tags
    r39 = await splunk_list_tags()
    assert r39.success is True

    # 40. splunk_list_macros
    r40 = await splunk_list_macros()
    assert r40.success is True

    set_settings(Settings(mcp_read_only=True))


@pytest.mark.asyncio
async def test_domain_e_administration_tools(mock_client):
    # 41. splunk_get_server_info
    r41 = await splunk_get_server_info()
    assert r41.success is True
    assert r41.data["version"] == "10.6.1.1"

    # 42. splunk_get_server_health
    r42 = await splunk_get_server_health()
    assert r42.success is True

    # 43. splunk_list_apps
    r43 = await splunk_list_apps()
    assert r43.success is True

    # 44. splunk_get_app_details
    r44 = await splunk_get_app_details(name="search")
    assert r44.success is True

    # 45. splunk_list_users
    r45 = await splunk_list_users()
    assert r45.success is True

    # 46. splunk_get_user
    r46 = await splunk_get_user(username="admin")
    assert r46.success is True

    # 47. splunk_list_roles
    r47 = await splunk_list_roles()
    assert r47.success is True

    # 48. splunk_get_role_capabilities
    r48 = await splunk_get_role_capabilities(role_name="admin")
    assert r48.success is True

    # 49. splunk_list_configurations
    r49 = await splunk_list_configurations()
    assert r49.success is True

    # 50. splunk_get_configuration
    r50 = await splunk_get_configuration(conf_file="props")
    assert r50.success is True


@pytest.mark.asyncio
async def test_domain_f_ingestion_tools(mock_client):
    # 51. splunk_list_inputs
    r51 = await splunk_list_inputs()
    assert r51.success is True

    # 52. splunk_get_input
    r52 = await splunk_get_input(input_type="tcp/raw", name="9997")
    assert r52.success is True

    # 53. splunk_list_forwarders
    r53 = await splunk_list_forwarders()
    assert r53.success is True

    # 54. splunk_get_forwarder_status
    r54 = await splunk_get_forwarder_status(hostname="fwd-01")
    assert r54.success is True

    # 55. splunk_check_forwarder_connectivity
    r55 = await splunk_check_forwarder_connectivity()
    assert r55.success is True

    # 56. splunk_get_ingestion_metrics
    r56 = await splunk_get_ingestion_metrics()
    assert r56.success is True

    # 57. splunk_get_ingestion_lag
    r57 = await splunk_get_ingestion_lag(index="main")
    assert r57.success is True

    # 58. splunk_get_parsing_errors
    r58 = await splunk_get_parsing_errors()
    assert r58.success is True

    # 59. splunk_check_source_coverage
    r59 = await splunk_check_source_coverage(expected_sources=["access.log"])
    assert r59.success is True

    # 60. splunk_diagnose_ingestion
    r60 = await splunk_diagnose_ingestion()
    assert r60.success is True


@pytest.mark.asyncio
async def test_domain_g_security_investigation_tools(mock_client):
    # 61. splunk_detect_failed_logins
    r61 = await splunk_detect_failed_logins()
    assert r61.success is True

    # 62. splunk_detect_brute_force
    r62 = await splunk_detect_brute_force()
    assert r62.success is True

    # 63. splunk_investigate_ip
    r63 = await splunk_investigate_ip(ip_address="192.168.1.50")
    assert r63.success is True

    # 64. splunk_investigate_user
    r64 = await splunk_investigate_user(username="jsmith")
    assert r64.success is True

    # 65. splunk_investigate_host
    r65 = await splunk_investigate_host(hostname="app-srv-01")
    assert r65.success is True

    # 66. splunk_search_ioc
    r66 = await splunk_search_ioc(ioc_value="bad-domain.evil")
    assert r66.success is True

    # 67. splunk_correlate_events
    r67 = await splunk_correlate_events(entity_value="10.0.0.5")
    assert r67.success is True

    # 68. splunk_detect_anomalies
    r68 = await splunk_detect_anomalies(index="main")
    assert r68.success is True

    # 69. splunk_get_security_alerts
    r69 = await splunk_get_security_alerts()
    assert r69.success is True

    # 70. splunk_build_incident_timeline
    r70 = await splunk_build_incident_timeline(entity_type="ip", entity_value="10.0.0.99")
    assert r70.success is True


@pytest.mark.asyncio
async def test_domain_h_performance_tools(mock_client):
    # 71. splunk_get_search_performance
    r71 = await splunk_get_search_performance()
    assert r71.success is True

    # 72. splunk_detect_slow_searches
    r72 = await splunk_detect_slow_searches()
    assert r72.success is True

    # 73. splunk_get_search_concurrency
    r73 = await splunk_get_search_concurrency()
    assert r73.success is True

    # 74. splunk_get_scheduler_health
    r74 = await splunk_get_scheduler_health()
    assert r74.success is True

    # 75. splunk_get_internal_errors
    r75 = await splunk_get_internal_errors()
    assert r75.success is True

    # 76. splunk_get_license_usage
    r76 = await splunk_get_license_usage()
    assert r76.success is True

    # 77. splunk_get_storage_usage
    r77 = await splunk_get_storage_usage()
    assert r77.success is True

    # 78. splunk_get_cluster_health
    r78 = await splunk_get_cluster_health()
    assert r78.success is True

    # 79. splunk_get_replication_status
    r79 = await splunk_get_replication_status()
    assert r79.success is True

    # 80. splunk_diagnose_performance
    r80 = await splunk_diagnose_performance()
    assert r80.success is True


@pytest.mark.asyncio
async def test_domain_i_operations_tools(mock_client):
    set_settings(Settings(mcp_read_only=False))

    # 81. splunk_create_index
    r81 = await splunk_create_index(name="new_test_idx")
    assert r81.success is True

    # 82. splunk_update_index_settings
    r82 = await splunk_update_index_settings(name="new_test_idx", max_size_mb=20000)
    assert r82.success is True

    # 83. splunk_manage_input
    r83 = await splunk_manage_input(input_type="tcp/raw", name="9997", action="enable")
    assert r83.success is True

    # 84. splunk_manage_user
    r84 = await splunk_manage_user(username="testuser", action="create", confirm=True)
    assert r84.success is True

    # 85. splunk_manage_role
    r85 = await splunk_manage_role(role_name="testrole", action="create", confirm=True)
    assert r85.success is True

    # 86. splunk_manage_app
    r86 = await splunk_manage_app(app_name="search", action="enable", confirm=True)
    assert r86.success is True

    # 87. splunk_validate_configuration
    r87 = await splunk_validate_configuration(conf_file="props")
    assert r87.success is True

    # 88. splunk_export_search_results
    r88 = await splunk_export_search_results(spl="index=main | head 5")
    assert r88.success is True

    # 89. splunk_submit_event
    r89 = await splunk_submit_event(event_data="2026-10-26 synthetic test log")
    assert r89.success is True

    # 90. splunk_replay_saved_search
    r90 = await splunk_replay_saved_search(name="Test Alert")
    assert r90.success is True

    set_settings(Settings(mcp_read_only=True))


@pytest.mark.asyncio
async def test_domain_j_intelligence_tools(mock_client):
    # 91. splunk_natural_language_to_spl
    r91 = await splunk_natural_language_to_spl(prompt="find top 10 failed logins by user")
    assert r91.success is True
    assert "stats count" in r91.data["generated_spl"]

    # 92. splunk_optimize_spl
    r92 = await splunk_optimize_spl(spl="search index=main | dedup user | stats count")
    assert r92.success is True
    assert "optimized_spl" in r92.data

    # 93. splunk_explain_search_results
    r93 = await splunk_explain_search_results(results=[{"user": "alice", "count": "10"}])
    assert r93.success is True

    # 94. splunk_compare_time_periods
    r94 = await splunk_compare_time_periods(metric_spl="index=main | stats count")
    assert r94.success is True

    # 95. splunk_detect_data_quality_issues
    r95 = await splunk_detect_data_quality_issues(index="main")
    assert r95.success is True

    # 96. splunk_generate_operational_report
    r96 = await splunk_generate_operational_report()
    assert r96.success is True
    assert "report_markdown" in r96.data

    # 97. splunk_execute_workflow
    r97 = await splunk_execute_workflow(workflow_name="incident_triage", parameters={"entity": "10.0.0.1"})
    assert r97.success is True

    # 98. splunk_preview_change
    r98 = await splunk_preview_change(operation="delete_index", target="old_logs", proposed_settings={})
    assert r98.success is True
    assert r98.data["risk_level"] == "HIGH"

    # 99. splunk_audit_tool_activity
    r99 = await splunk_audit_tool_activity()
    assert r99.success is True

    # 100. splunk_test_connection
    r100 = await splunk_test_connection()
    assert r100.success is True
    assert r100.data["status"] == "CONNECTED"
    assert r100.data["splunk_version"] == "10.6.1.1"

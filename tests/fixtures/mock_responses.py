"""Test fixtures and mock payloads simulating Splunk REST API responses."""

MOCK_SERVER_INFO = {
    "entry": [
        {
            "name": "server-info",
            "content": {
                "serverName": "splunk-test-host",
                "version": "10.6.1.1",
                "build": "b2ae2962645c",
                "os_name": "Linux",
                "cpu_arch": "x86_64",
                "licenseState": "OK",
                "server_roles": ["indexer", "search_head"],
                "mode": "normal",
            },
        }
    ]
}

MOCK_SERVER_HEALTH = {
    "entry": [
        {
            "name": "feature:search",
            "content": {"health": "GREEN", "reasons": []},
        },
        {
            "name": "feature:indexing",
            "content": {"health": "GREEN", "reasons": []},
        },
    ]
}

MOCK_INDEXES = {
    "entry": [
        {
            "name": "main",
            "content": {
                "totalEventCount": 154200,
                "currentDBSizeMB": 245.5,
                "maxTotalDataSizeMB": 500000,
                "homePath": "/opt/splunk/var/lib/splunk/defaultdb/db",
                "coldPath": "/opt/splunk/var/lib/splunk/defaultdb/colddb",
                "thawedPath": "/opt/splunk/var/lib/splunk/defaultdb/thaweddb",
                "disabled": False,
                "frozenTimePeriodInSecs": 188697600,
            },
            "acl": {"app": "search", "owner": "nobody"},
        },
        {
            "name": "_internal",
            "content": {
                "totalEventCount": 892010,
                "currentDBSizeMB": 1200.0,
                "maxTotalDataSizeMB": 500000,
                "homePath": "/opt/splunk/var/lib/splunk/_internaldb/db",
                "coldPath": "/opt/splunk/var/lib/splunk/_internaldb/colddb",
                "thawedPath": "/opt/splunk/var/lib/splunk/_internaldb/thaweddb",
                "disabled": False,
                "frozenTimePeriodInSecs": 2592000,
            },
            "acl": {"app": "search", "owner": "nobody"},
        },
    ]
}

MOCK_JOB_STATUS = {
    "entry": [
        {
            "name": "1710000000.123",
            "content": {
                "isDone": True,
                "isFailed": False,
                "isPaused": False,
                "dispatchState": "DONE",
                "doneProgress": 1.0,
                "eventCount": 10,
                "resultCount": 10,
                "scanCount": 50,
                "runDuration": 0.42,
            },
        }
    ],
    "messages": [],
}

MOCK_SEARCH_RESULTS = {
    "results": [
        {"_time": "2026-10-26T11:00:00.000Z", "host": "srv-01", "sourcetype": "access_combined", "status": "200"},
        {"_time": "2026-10-26T11:01:00.000Z", "host": "srv-02", "sourcetype": "access_combined", "status": "500"},
    ]
}

MOCK_SAVED_SEARCHES = {
    "entry": [
        {
            "name": "High Severity Error Alert",
            "content": {
                "search": "index=_internal log_level=ERROR | stats count by component",
                "description": "Alert on sudden spikes in daemon errors",
                "is_scheduled": True,
                "cron_schedule": "*/15 * * * *",
                "disabled": False,
                "alert_type": "number of events",
            },
            "acl": {"app": "search", "owner": "admin"},
        }
    ]
}

MOCK_APPS = {
    "entry": [
        {
            "name": "search",
            "content": {
                "label": "Search & Reporting",
                "version": "10.6.1",
                "author": "Splunk",
                "disabled": False,
                "visible": True,
            },
        }
    ]
}

MOCK_USERS = {
    "entry": [
        {
            "name": "admin",
            "content": {
                "realname": "Administrator",
                "email": "admin@example.com",
                "roles": ["admin"],
                "type": "Splunk",
                "locked-out": False,
            },
        }
    ]
}

MOCK_ROLES = {
    "entry": [
        {
            "name": "admin",
            "content": {
                "capabilities": ["admin_all_objects", "edit_roles", "search"],
                "imported_capabilities": [],
                "srchIndexesAllowed": ["*"],
                "srchIndexesDefault": ["main"],
            },
        }
    ]
}

MOCK_VIEWS = {
    "entry": [
        {
            "name": "operations_overview",
            "content": {
                "label": "Operations Overview",
                "isDashboard": True,
                "rootNode": "dashboard",
                "eai:data": "<dashboard><label>Operations Overview</label></dashboard>",
            },
            "acl": {"app": "search", "owner": "admin"},
        }
    ]
}

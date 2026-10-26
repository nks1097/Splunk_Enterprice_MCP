"""Unit tests for SPL query syntax validation and optimization."""

import pytest

from splunk_mcp.exceptions import SPLValidationError
from splunk_mcp.spl_validation import SPLValidator


def test_command_extraction():
    spl = "search index=main sourcetype=access* | stats count by status | sort - count"
    commands = SPLValidator.extract_commands(spl)
    assert commands == ["search", "stats", "sort"]


def test_mutating_command_blocking_in_read_only():
    spl = "search index=main | delete"
    with pytest.raises(SPLValidationError) as exc_info:
        SPLValidator.analyze(spl, read_only=True)
    assert "mutating command" in str(exc_info.value)


def test_mutating_command_allowed_in_read_write():
    spl = "search index=main | delete"
    result = SPLValidator.analyze(spl, read_only=False)
    assert result.has_mutating_commands is True


def test_anti_pattern_detection():
    # Leading wildcard and dedup before stats
    spl = "search *error* | dedup user | stats count"
    analysis = SPLValidator.analyze(spl, read_only=False)
    assert any("wildcard" in ap.lower() for ap in analysis.anti_patterns_found)
    assert any("dedup" in ap.lower() for ap in analysis.anti_patterns_found)
    assert analysis.estimated_cost == "HIGH"


def test_spl_optimization():
    spl = "search index=main | dedup user | stats count"
    optimized, changes = SPLValidator.optimize(spl)
    assert "dc(user)" in optimized
    assert len(changes) > 0

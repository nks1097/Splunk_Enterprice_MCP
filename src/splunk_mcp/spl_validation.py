"""SPL query syntax analysis, validation, safety policy enforcement, and optimization."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from splunk_mcp.exceptions import SPLValidationError

# Dangerous commands that alter data, execute arbitrary scripts, or write to filesystem
MUTATING_COMMANDS = {
    "delete",
    "outputcsv",
    "outputlookup",
    "collect",
    "summaryindex",
    "sendemail",
    "dump",
    "runcmd",
    "script",
    "run",
}

# Administrative inspection commands that might query privileged internal REST APIs
PRIVILEGED_COMMANDS = {
    "rest",
    "dbxquery",
    "runshellscript",
}


class SPLAnalysisResult(BaseModel):
    """Structured report produced by analyzing and validating an SPL query."""

    is_valid: bool = Field(description="Whether the query passes validation policies")
    query: str = Field(description="Sanitized SPL query string")
    commands: list[str] = Field(default_factory=list, description="Pipeline of commands in the query")
    has_mutating_commands: bool = Field(default=False, description="Whether query modifies data or filesystem")
    has_privileged_commands: bool = Field(default=False, description="Whether query uses rest or shell scripts")
    warnings: list[str] = Field(default_factory=list, description="Potential performance issues or anti-patterns")
    anti_patterns_found: list[str] = Field(default_factory=list, description="List of detected anti-patterns")
    suggestions: list[str] = Field(default_factory=list, description="Concrete optimization suggestions")
    estimated_cost: str = Field(default="LOW", description="Estimated performance impact (LOW, MEDIUM, HIGH)")


class SPLValidator:
    """Security and performance validator for Splunk Search Processing Language (SPL)."""

    @staticmethod
    def extract_commands(spl: str) -> list[str]:
        """Extract pipeline command names from SPL string."""
        clean = spl.strip()
        if clean.startswith("|"):
            clean = clean[1:].strip()

        # Split pipeline taking care not to split inside quotes
        parts = re.split(r"\|(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", clean)
        commands = []
        for p in parts:
            p_strip = p.strip()
            if not p_strip:
                continue
            first_word = p_strip.split()[0].lower()
            commands.append(first_word)
        return commands

    @classmethod
    def analyze(
        cls,
        spl: str,
        read_only: bool = True,
        earliest_time: str | None = None,
        latest_time: str | None = None,
    ) -> SPLAnalysisResult:
        """Analyze and validate an SPL query against security rules and performance best practices."""
        clean_spl = spl.strip()
        if not clean_spl:
            raise SPLValidationError("SPL query string cannot be empty.")

        commands = cls.extract_commands(clean_spl)
        has_mutating = bool(set(commands).intersection(MUTATING_COMMANDS))
        has_privileged = bool(set(commands).intersection(PRIVILEGED_COMMANDS))

        # Check mutating commands in read-only mode
        if read_only and has_mutating:
            mut_found = list(set(commands).intersection(MUTATING_COMMANDS))
            raise SPLValidationError(
                f"SPL query contains forbidden mutating command(s): {mut_found} while in read-only mode.",
                query=clean_spl,
            )

        warnings: list[str] = []
        anti_patterns: list[str] = []
        suggestions: list[str] = []
        cost_level = "LOW"

        # Check time window bounds
        if not earliest_time and "earliest=" not in clean_spl:
            warnings.append("No explicit earliest time boundary specified; defaults to server retention or -24h.")
            suggestions.append("Specify explicit earliest_time (e.g. -1h, -24h@h) to bound the search scope.")
            cost_level = "MEDIUM"

        # Anti-pattern: Leading wildcard in initial term
        if re.search(r"(?i)(?:^|[\s=])\*[a-zA-Z0-9_]+", clean_spl):
            anti_patterns.append("Leading wildcard (e.g. *term) triggers full-text scan without index acceleration.")
            suggestions.append("Avoid leading wildcards; search for specific prefix or exact term.")
            cost_level = "HIGH"

        # Anti-pattern: Missing index specification in initial search
        if not clean_spl.startswith("|") and "index=" not in clean_spl.lower():
            warnings.append("Query does not specify 'index=<name>'. It will search the default or all allowed indexes.")
            suggestions.append("Always specify 'index=<target_index>' to reduce scanned buckets and improve speed.")
            if cost_level != "HIGH":
                cost_level = "MEDIUM"

        # Anti-pattern: Using dedup before stats
        if "dedup" in commands and "stats" in commands:
            dedup_idx = commands.index("dedup")
            stats_idx = commands.index("stats")
            if dedup_idx < stats_idx:
                anti_patterns.append("Executing 'dedup' before 'stats' wastes memory. Prefer 'stats' aggregations.")
                suggestions.append("Use 'stats latest(field) by id' or 'stats values(field)' instead of 'dedup'.")

        # Anti-pattern: Excessive join or subsearches
        if "join" in commands:
            warnings.append("Using 'join' in Splunk is resource-intensive and capped at 50,000 subsearch rows.")
            suggestions.append("Prefer 'stats' or 'eventstats' over 'join' whenever correlating by common key.")
            cost_level = "HIGH"

        return SPLAnalysisResult(
            is_valid=True,
            query=clean_spl,
            commands=commands,
            has_mutating_commands=has_mutating,
            has_privileged_commands=has_privileged,
            warnings=warnings,
            anti_patterns_found=anti_patterns,
            suggestions=suggestions,
            estimated_cost=cost_level,
        )

    @classmethod
    def optimize(cls, spl: str) -> tuple[str, list[str]]:
        """Suggest an optimized rewrite of common SPL patterns."""
        changes = []
        optimized = spl.strip()

        # Replace dedup followed by stats if simple
        if re.search(r"\|\s*dedup\s+([a-zA-Z0-9_]+)\s*\|\s*stats\s+count", optimized):
            optimized = re.sub(
                r"\|\s*dedup\s+([a-zA-Z0-9_]+)\s*\|\s*stats\s+count",
                r"| stats dc(\1) as count",
                optimized,
            )
            changes.append("Replaced '| dedup field | stats count' with '| stats dc(field) as count'")

        # If missing earliest in SPL, suggest adding it
        if "earliest=" not in optimized and not optimized.startswith("|"):
            changes.append("Add 'earliest=-24h' to partition time window.")

        return optimized, changes

"""Parsing utilities for log lines."""

import re
from dataclasses import dataclass
from typing import Optional

LOG_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}(?:\.\d+)?)"
    r"\s+(TRACE|DEBUG|INFO|NOTICE|WARN(?:ING)?|ERROR|CRITICAL|FATAL|SEVERE)\s+"
    r"(.*)$",
    re.IGNORECASE,
)

LEVEL_MAP = {
    "WARN": "WARNING",
    "FATAL": "CRITICAL",
    "SEVERE": "ERROR",
}

VALID_LEVELS = {"TRACE", "DEBUG", "INFO", "NOTICE", "WARNING", "ERROR", "CRITICAL", "RAW"}


@dataclass
class LogEntry:
    timestamp: str
    level: str
    message: str


def normalize_level(raw: str) -> str:
    level = raw.upper()
    return LEVEL_MAP.get(level, level)


def parse_line(line: str) -> LogEntry:
    """Parse a single log line. Malformed lines become level RAW."""
    stripped = line.strip()
    if not stripped:
        return LogEntry(timestamp="-", level="RAW", message="")
    match = LOG_RE.match(stripped)
    if match:
        timestamp, level, message = match.groups()
        return LogEntry(
            timestamp=timestamp.strip(),
            level=normalize_level(level),
            message=message.strip(),
        )
    return LogEntry(timestamp="-", level="RAW", message=stripped)


def parse_content(content: str) -> list[LogEntry]:
    return [parse_line(line) for line in content.splitlines()]


def compute_counts(entries: list[LogEntry]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry.level] = counts.get(entry.level, 0) + 1
    return counts


def filter_entries(
    entries: list[LogEntry],
    level: Optional[str] = None,
    query: Optional[str] = None,
) -> list[LogEntry]:
    result = entries
    if level and level != "ALL":
        result = [e for e in result if e.level == level.upper()]
    if query:
        q = query.lower()
        result = [e for e in result if q in e.message.lower() or q in e.timestamp.lower()]
    return result

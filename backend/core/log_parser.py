"""
Log Parser - Ingests and normalizes logs from various formats
"""
import re
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, asdict


@dataclass
class LogEntry:
    timestamp: str
    service: str
    level: str
    message: str
    raw: str
    metadata: Dict = None

    def to_dict(self):
        return asdict(self)


class LogParser:
    """Parses logs from multiple formats into a unified structure."""

    # Regex patterns for common log formats
    PATTERNS = [
        # Standard format: 2026-01-15 02:10:00 [service] LEVEL: message
        r'(?P<timestamp>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\s+\[(?P<service>[^\]]+)\]\s+(?P<level>\w+):\s+(?P<message>.*)',
        # JSON format
        r'^\{(?P<json>.*)\}$',
        # Syslog format
        r'(?P<timestamp>\w+\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(?P<service>\S+)\s+(?P<message>.*)',
    ]

    def parse(self, raw_logs: str) -> List[LogEntry]:
        """Parse raw log text into structured LogEntry objects."""
        entries = []
        for line in raw_logs.strip().split('\n'):
            if not line.strip():
                continue
            entry = self._parse_line(line)
            if entry:
                entries.append(entry)
        return entries

    def _parse_line(self, line: str) -> LogEntry:
        """Parse a single log line."""
        # Try standard format first
        match = re.match(self.PATTERNS[0], line)
        if match:
            return LogEntry(
                timestamp=match.group('timestamp'),
                service=match.group('service').strip(),
                level=match.group('level').strip(),
                message=match.group('message').strip(),
                raw=line
            )

        # Try JSON format
        if line.strip().startswith('{'):
            try:
                import json
                data = json.loads(line)
                return LogEntry(
                    timestamp=data.get('timestamp', datetime.now().isoformat()),
                    service=data.get('service', 'unknown'),
                    level=data.get('level', 'INFO'),
                    message=data.get('message', ''),
                    raw=line,
                    metadata={k: v for k, v in data.items()
                             if k not in ['timestamp', 'service', 'level', 'message']}
                )
            except json.JSONDecodeError:
                pass

        # Fallback: treat as raw message
        return LogEntry(
            timestamp=datetime.now().isoformat(),
            service='unknown',
            level='INFO',
            message=line.strip(),
            raw=line
        )

    def filter_by_time_window(self, entries: List[LogEntry],
                               start: str = None, end: str = None) -> List[LogEntry]:
        """Filter logs within a time window."""
        if not start and not end:
            return entries
        filtered = []
        for entry in entries:
            if start and entry.timestamp < start:
                continue
            if end and entry.timestamp > end:
                continue
            filtered.append(entry)
        return filtered
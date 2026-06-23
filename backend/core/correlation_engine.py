"""
Correlation Engine - Links related events across services and time
"""
from typing import List, Dict
from datetime import datetime, timedelta
from .log_parser import LogEntry


class CorrelationEngine:
    """Correlates anomalies across services to find causal chains."""

    def __init__(self, time_window_minutes: int = 10):
        self.time_window = timedelta(minutes=time_window_minutes)

    def correlate(self, entries: List[LogEntry], anomalies: List[Dict]) -> List[Dict]:
        """
        Group related anomalies into incident chains.
        """
        if not anomalies:
            return []

        # Sort anomalies by timestamp
        sorted_anomalies = sorted(anomalies, key=lambda x: x['timestamp'])

        # Group by time window and service relationships
        chains = []
        used_indices = set()

        for i, primary in enumerate(sorted_anomalies):
            if i in used_indices:
                continue

            chain = {
                'primary': primary,
                'related': [],
                'services_involved': [primary['service']],
                'time_span': None,
                'pattern': 'unknown',
            }

            primary_time = self._parse_time(primary['timestamp'])

            # Find related events within time window
            for j, related in enumerate(sorted_anomalies):
                if j == i or j in used_indices:
                    continue

                related_time = self._parse_time(related['timestamp'])
                if primary_time and related_time:
                    time_diff = abs((related_time - primary_time).total_seconds() / 60)
                    if time_diff <= self.time_window.total_seconds() / 60:
                        chain['related'].append(related)
                        used_indices.add(j)
                        if related['service'] not in chain['services_involved']:
                            chain['services_involved'].append(related['service'])

            used_indices.add(i)

            # Determine pattern
            chain['pattern'] = self._determine_pattern(chain)
            chain['time_span'] = self._compute_time_span(chain)
            chains.append(chain)

        # Sort chains by severity
        chains.sort(key=lambda c: c['primary']['severity_score'], reverse=True)
        return chains

    def _determine_pattern(self, chain: Dict) -> str:
        """Identify the type of incident pattern."""
        services = chain['services_involved']
        messages = ' '.join([chain['primary']['message']] +
                            [r['message'] for r in chain['related']]).lower()

        if 'deploy' in messages or 'release' in messages or 'rollout' in messages:
            return 'deployment_related'
        elif 'connection pool' in messages or 'database' in messages:
            return 'database_issue'
        elif len(services) > 2:
            return 'cascading_failure'
        elif 'memory' in messages or 'oom' in messages:
            return 'resource_exhaustion'
        elif 'timeout' in messages:
            return 'network_timeout'
        elif '5xx' in messages or 'error rate' in messages:
            return 'service_degradation'
        else:
            return 'general_incident'

    def _parse_time(self, ts: str):
        """Parse timestamp string to datetime."""
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S.%f',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(ts, fmt)
            except (ValueError, TypeError):
                continue
        return None

    def _compute_time_span(self, chain: Dict) -> Dict:
        """Compute the time span of the incident chain."""
        all_events = [chain['primary']] + chain['related']
        times = [self._parse_time(e['timestamp']) for e in all_events]
        times = [t for t in times if t is not None]

        if not times:
            return {'start': None, 'end': None, 'duration_minutes': 0}

        start, end = min(times), max(times)
        return {
            'start': start.isoformat(),
            'end': end.isoformat(),
            'duration_minutes': (end - start).total_seconds() / 60
        }
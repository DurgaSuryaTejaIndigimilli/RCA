"""
Anomaly Detector - Identifies unusual patterns in logs using ML
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Dict
from .log_parser import LogEntry


class AnomalyDetector:
    """Detects anomalies in log sequences using Isolation Forest + heuristics."""

    # Critical error keywords that always indicate anomalies
    CRITICAL_PATTERNS = [
        'connection pool exhausted',
        'out of memory',
        'crash',
        'fatal',
        'panic',
        'timeout exceeded',
        'circuit breaker',
        'rate limit exceeded',
        '5xx error',
        'service unavailable',
        'connection refused',
        'disk full',
        'oom killed',
    ]

    WARNING_PATTERNS = [
        'slow response',
        'high latency',
        'retry',
        'degraded',
        'warning',
        'elevated',
        'threshold',
    ]

    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.vectorizer = TfidfVectorizer(max_features=100)

    def detect(self, entries: List[LogEntry]) -> List[Dict]:
        """
        Detect anomalies in log entries.
        Returns a list of anomalies with severity scores.
        """
        anomalies = []
        messages = [e.message for e in entries]

        # Rule-based detection (always reliable)
        for i, entry in enumerate(entries):
            anomaly = self._check_rules(entry)
            if anomaly:
                anomalies.append(anomaly)

        # ML-based detection (if we have enough data)
        if len(entries) >= 10:
            try:
                ml_anomalies = self._detect_with_ml(entries, messages)
                anomalies.extend(ml_anomalies)
            except Exception:
                # ML detection failed, rely on rules
                pass

        # Deduplicate and sort by severity
        unique = self._deduplicate(anomalies)
        unique.sort(key=lambda x: x['severity_score'], reverse=True)
        return unique

    def _check_rules(self, entry: LogEntry) -> Dict:
        """Rule-based anomaly detection."""
        message_lower = entry.message.lower()
        level = entry.level.upper()

        # Critical patterns
        for pattern in self.CRITICAL_PATTERNS:
            if pattern in message_lower:
                return {
                    'log_index': None,
                    'service': entry.service,
                    'timestamp': entry.timestamp,
                    'level': entry.level,
                    'message': entry.message,
                    'pattern_matched': pattern,
                    'severity_score': 0.95,
                    'detection_method': 'rule_based',
                    'category': 'critical_error'
                }

        # Warning patterns
        for pattern in self.WARNING_PATTERNS:
            if pattern in message_lower:
                return {
                    'log_index': None,
                    'service': entry.service,
                    'timestamp': entry.timestamp,
                    'level': entry.level,
                    'message': entry.message,
                    'pattern_matched': pattern,
                    'severity_score': 0.65,
                    'detection_method': 'rule_based',
                    'category': 'performance_warning'
                }

        # High log levels
        if level in ['ERROR', 'CRITICAL', 'FATAL']:
            return {
                'log_index': None,
                'service': entry.service,
                'timestamp': entry.timestamp,
                'level': entry.level,
                'message': entry.message,
                'pattern_matched': f'log_level_{level}',
                'severity_score': 0.7,
                'detection_method': 'rule_based',
                'category': 'error_level'
            }

        return None

    def _detect_with_ml(self, entries: List[LogEntry], messages: List[str]) -> List[Dict]:
        """ML-based anomaly detection using Isolation Forest."""
        try:
            # Vectorize messages
            X = self.vectorizer.fit_transform(messages).toarray()

            if X.shape[1] == 0:
                return []

            # Predict
            predictions = self.model.fit_predict(X)
            scores = self.model.decision_function(X)

            anomalies = []
            for i, (pred, score) in enumerate(zip(predictions, scores)):
                if pred == -1:  # Anomaly
                    anomalies.append({
                        'log_index': i,
                        'service': entries[i].service,
                        'timestamp': entries[i].timestamp,
                        'level': entries[i].level,
                        'message': entries[i].message,
                        'pattern_matched': 'statistical_outlier',
                        'severity_score': float(1 - (score + 0.5)),  # Normalize
                        'detection_method': 'isolation_forest',
                        'category': 'statistical_anomaly'
                    })
            return anomalies
        except Exception:
            return []

    def _deduplicate(self, anomalies: List[Dict]) -> List[Dict]:
        """Remove duplicate anomaly detections."""
        seen = set()
        unique = []
        for a in anomalies:
            key = (a['service'], a['timestamp'], a['message'][:50])
            if key not in seen:
                seen.add(key)
                unique.append(a)
        return unique
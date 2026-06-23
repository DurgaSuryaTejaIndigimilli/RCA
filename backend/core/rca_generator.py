"""
RCA Generator - Orchestrates the full root cause analysis pipeline
"""
from typing import List, Dict
from .log_parser import LogParser, LogEntry
from .anomaly_detector import AnomalyDetector
from .correlation_engine import CorrelationEngine
from .rag_engine import RAGEngine
from .llm_client import LLMClient


class RCAGenerator:
    """End-to-end Root Cause Analysis pipeline."""

    def __init__(self):
        self.parser = LogParser()
        self.anomaly_detector = AnomalyDetector()
        self.correlator = CorrelationEngine(time_window_minutes=10)
        self.rag = RAGEngine()
        self.llm = LLMClient()

    def analyze(self, raw_logs: str, user_query: str = None) -> Dict:
        """
        Run full RCA pipeline on raw logs.

        Args:
            raw_logs: Raw log text
            user_query: Optional user question about the logs

        Returns:
            Complete RCA report as a dictionary
        """
        # Stage 1: Parse logs
        entries = self.parser.parse(raw_logs)

        if not entries:
            return {
                'status': 'error',
                'message': 'No valid log entries found',
                'report': None
            }

        # Stage 2: Build RAG index
        self.rag.index_logs([e.message for e in entries])

        # Stage 3: Detect anomalies
        anomalies = self.anomaly_detector.detect(entries)

        # Stage 4: Correlate events
        incident_chains = self.correlator.correlate(entries, anomalies)

        # Stage 5: Get primary incident (most severe)
        primary_incident = incident_chains[0] if incident_chains else None

        # Stage 6: Retrieve relevant context
        relevant_logs = []
        if primary_incident:
            relevant_logs = self.rag.retrieve_for_incident(primary_incident)

        # Stage 7: Generate RCA with LLM
        rca_report = self._generate_rca_report(
            primary_incident, relevant_logs, entries, user_query
        )

        # Stage 8: Generate fix recommendations
        fix_recommendations = self._generate_fix_recommendations(
            primary_incident, relevant_logs
        )

        # Stage 9: Find similar historical incidents
        similar_incidents = self._find_similar_incidents(primary_incident)

        return {
            'status': 'success',
            'summary': {
                'total_logs_analyzed': len(entries),
                'anomalies_detected': len(anomalies),
                'incident_chains': len(incident_chains),
                'severity': primary_incident['primary']['severity_score'] if primary_incident else 0,
                'services_affected': list(set([e.service for e in entries])),
            },
            'primary_incident': primary_incident,
            'all_anomalies': anomalies[:20],  # Top 20
            'incident_chains': incident_chains[:5],  # Top 5
            'rca_report': rca_report,
            'fix_recommendations': fix_recommendations,
            'similar_historical_incidents': similar_incidents,
            'relevant_logs': relevant_logs,
        }

    def _generate_rca_report(self, incident: Dict, relevant_logs: List[Dict],
                              all_entries: List[LogEntry],
                              user_query: str = None) -> str:
        """Generate the RCA report using LLM."""
        if not incident:
            return "No significant incidents detected in the provided logs."

        # Build context for LLM
        context = self._build_llm_context(incident, relevant_logs, all_entries)

        system_prompt = """You are an expert Site Reliability Engineer (SRE) and 
        DevOps specialist with 15+ years of experience in incident response and 
        root cause analysis. You specialize in distributed systems, microservices, 
        and IoT infrastructure. Your analyses are:
        - Precise and data-driven
        - Clear and actionable
        - Backed by evidence from logs
        - Structured for both technical and executive audiences
        Always provide confidence scores and cite specific log evidence."""

        user_prompt = f"""Analyze the following incident and provide a detailed Root Cause Analysis:

{context}

User Question: {user_query if user_query else 'Provide a complete root cause analysis'}

Please structure your response with:
1. Incident Summary
2. Primary Root Cause
3. Timeline of Events
4. Contributing Factors
5. Confidence Score with justification
6. Why this is the most likely root cause"""

        return self.llm.generate(system_prompt, user_prompt, max_tokens=2500)

    def _generate_fix_recommendations(self, incident: Dict,
                                      relevant_logs: List[Dict]) -> str:
        """Generate fix recommendations using LLM."""
        if not incident:
            return "No remediation needed at this time."

        context = self._build_llm_context(incident, relevant_logs, [])

        system_prompt = """You are an expert SRE who specializes in rapid incident 
        remediation. You provide:
        - Prioritized, actionable steps
        - Specific commands and configurations
        - Risk assessment for each action
        - Both immediate fixes and long-term improvements
        Be precise, practical, and prioritize safety."""

        user_prompt = f"""Based on this incident analysis, provide prioritized remediation steps:

{context}

Format your response as:
1. Immediate Actions (numbered, with commands)
2. Short-term Improvements (next 24 hours)
3. Long-term Preventive Measures

For each step, include:
- Confidence score
- Estimated time to execute
- Risk level
- Expected impact"""

        return self.llm.generate(system_prompt, user_prompt, max_tokens=2500)

    def _find_similar_incidents(self, incident: Dict) -> List[Dict]:
        """Find similar historical incidents."""
        if not incident:
            return []

        pattern = incident.get('pattern', 'general_incident')

        # In production, this would query a real incident database
        # For now, return curated historical examples
        historical_db = {
            'deployment_related': [
                {
                    'incident_id': 'INC-2025-09-14-003',
                    'date': '2025-09-14',
                    'title': 'Production deployment caused 47-min outage',
                    'pattern': 'deployment_related',
                    'resolution': 'Rolled back deployment, increased pool size to 100, added canary rollout',
                    'similarity_score': 0.94,
                    'resolution_time_minutes': 47
                },
                {
                    'incident_id': 'INC-2025-06-22-001',
                    'date': '2025-06-22',
                    'title': 'Database connection pool exhaustion post-deploy',
                    'pattern': 'deployment_related',
                    'resolution': 'Reverted deploy, optimized queries, implemented staged rollout',
                    'similarity_score': 0.87,
                    'resolution_time_minutes': 32
                }
            ],
            'database_issue': [
                {
                    'incident_id': 'INC-2025-11-03-002',
                    'date': '2025-11-03',
                    'title': 'Connection pool leak caused service degradation',
                    'pattern': 'database_issue',
                    'resolution': 'Restarted services, patched connection leak, added monitoring',
                    'similarity_score': 0.89,
                    'resolution_time_minutes': 28
                }
            ],
            'cascading_failure': [
                {
                    'incident_id': 'INC-2025-08-17-004',
                    'date': '2025-08-17',
                    'title': 'Multi-service cascade from single point of failure',
                    'pattern': 'cascading_failure',
                    'resolution': 'Added circuit breakers, implemented bulkhead pattern',
                    'similarity_score': 0.82,
                    'resolution_time_minutes': 65
                }
            ],
        }

        return historical_db.get(pattern, [
            {
                'incident_id': 'INC-2025-12-01-001',
                'date': '2025-12-01',
                'title': 'Service degradation due to resource constraints',
                'pattern': 'general_incident',
                'resolution': 'Scaled resources, optimized configurations',
                'similarity_score': 0.71,
                'resolution_time_minutes': 42
            }
        ])

    def _build_llm_context(self, incident: Dict, relevant_logs: List[Dict],
                            all_entries: List[LogEntry]) -> str:
        """Build structured context for LLM."""
        parts = []

        # Primary incident
        if incident:
            parts.append("=== PRIMARY INCIDENT ===")
            parts.append(f"Pattern: {incident.get('pattern', 'unknown')}")
            parts.append(f"Services Involved: {', '.join(incident.get('services_involved', []))}")
            parts.append(f"Severity Score: {incident['primary'].get('severity_score', 0):.2f}")
            parts.append(f"Primary Event: [{incident['primary']['service']}] "
                        f"{incident['primary']['level']}: {incident['primary']['message']}")
            parts.append(f"Timestamp: {incident['primary']['timestamp']}")

            if incident.get('related'):
                parts.append("\n=== RELATED EVENTS ===")
                for rel in incident['related'][:5]:
                    parts.append(f"- [{rel['service']}] {rel['level']}: {rel['message']}")

        # Relevant logs from RAG
        if relevant_logs:
            parts.append("\n=== RELEVANT LOG CONTEXT (Top Matches) ===")
            for log in relevant_logs[:5]:
                parts.append(f"- {log['content']} (relevance: {log['relevance_score']:.2f})")

        return "\n".join(parts)

    def chat(self, user_message: str, context: Dict = None) -> str:
        """
        Interactive chat about an incident analysis.

        Args:
            user_message: User's question
            context: Previous analysis context (optional)
        """
        system_prompt = """You are an expert DevOps/SRE AI assistant specializing in 
        incident analysis. You have access to system logs, anomaly detection results, 
        and historical incident data. Provide clear, accurate, and actionable responses."""

        if context:
            user_prompt = f"""Previous analysis context:
{context.get('summary', {})}

User Question: {user_message}

Provide a helpful, specific response based on the context."""
        else:
            user_prompt = user_message

        return self.llm.generate(system_prompt, user_prompt, max_tokens=1500)
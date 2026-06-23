"""
LLM Client - Unified interface for Claude, OpenAI, or Mock LLM
"""
import os
from typing import Optional


class LLMClient:
    """Unified LLM client supporting multiple providers."""

    def __init__(self):
        self.provider = os.getenv('LLM_PROVIDER', 'mock').lower()
        self.client = None
        self._initialize()

    def _initialize(self):
        """Initialize the appropriate LLM client."""
        if self.provider == 'anthropic':
            try:
                import anthropic
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if api_key and api_key != 'your_anthropic_api_key_here':
                    self.client = anthropic.Anthropic(api_key=api_key)
                    self.provider = 'anthropic'
                else:
                    self.provider = 'mock'
            except ImportError:
                self.provider = 'mock'

        elif self.provider == 'openai':
            try:
                import openai
                api_key = os.getenv('OPENAI_API_KEY')
                if api_key and api_key != 'your_openai_api_key_here':
                    self.client = openai.OpenAI(api_key=api_key)
                    self.provider = 'openai'
                else:
                    self.provider = 'mock'
            except ImportError:
                self.provider = 'mock'

        else:
            self.provider = 'mock'

        # Allow override via env
        if os.getenv('USE_MOCK_LLM', 'true').lower() == 'true':
            self.provider = 'mock'

    def generate(self, system_prompt: str, user_prompt: str,
                 max_tokens: int = 2000) -> str:
        """Generate a response from the LLM."""
        if self.provider == 'anthropic':
            return self._call_anthropic(system_prompt, user_prompt, max_tokens)
        elif self.provider == 'openai':
            return self._call_openai(system_prompt, user_prompt, max_tokens)
        else:
            return self._mock_generate(system_prompt, user_prompt)

    def _call_anthropic(self, system_prompt: str, user_prompt: str,
                        max_tokens: int) -> str:
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return self._mock_generate(system_prompt, user_prompt, error=str(e))

    def _call_openai(self, system_prompt: str, user_prompt: str,
                     max_tokens: int) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return self._mock_generate(system_prompt, user_prompt, error=str(e))

    def _mock_generate(self, system_prompt: str, user_prompt: str,
                       error: str = None) -> str:
        """
        Mock LLM that returns high-quality structured responses
        without requiring any API key. Perfect for demos.
        """
        # Detect what kind of response is being asked for
        prompt_lower = (system_prompt + user_prompt).lower()

        if 'rca' in prompt_lower or 'root cause' in prompt_lower:
            return self._mock_rca(user_prompt)
        elif 'fix' in prompt_lower or 'remediation' in prompt_lower:
            return self._mock_fix_recommendation(user_prompt)
        else:
            return self._mock_general(user_prompt)

    def _mock_rca(self, user_prompt: str) -> str:
        """Generate a structured RCA response."""
        return """## 🔍 Root Cause Analysis Report

### Incident Summary
A **cascading service degradation** has been detected across multiple components. Analysis of correlated events reveals a deployment-triggered failure pattern.

### 🎯 Primary Root Cause
A **recent deployment** introduced increased query load that exhausted the database connection pool, causing downstream services to fail with timeout errors.

### ⏱️ Timeline of Events
1. **02:10:00** - New deployment `v2.3.1` rolled out to production
2. **02:11:30** - API gateway response times began exceeding thresholds
3. **02:12:00** - Edge device telemetry started timing out
4. **02:13:00** - Database connection pool reached maximum capacity (50/50)
5. **02:15:00** - Critical 5xx error rate spike triggered alerts

### 🔗 Contributing Factors
- Insufficient connection pool sizing for new query patterns
- Missing query timeout configuration on new endpoints
- No staged rollout validation for database-intensive changes
- Lack of automatic rollback triggers on error rate spikes

### 📊 Confidence Score: 92%
This diagnosis is based on:
- Strong temporal correlation between deployment and failure
- Identical pattern in a previous incident (3 months ago)
- Clear causal chain in service dependency graph
- Log evidence from 4 distinct services converging on the same root cause

### 💡 Why This Is The Root Cause
The deployment introduced 12 new query patterns that increased database load by approximately 240%. The connection pool, sized for previous load patterns, became the bottleneck. This is not a transient issue — it will persist until either the pool is resized or the query patterns are optimized."""

    def _mock_fix_recommendation(self, user_prompt: str) -> str:
        """Generate fix recommendations."""
        return """## 🛠️ Recommended Remediation Steps

### 🚨 Immediate Actions (Execute in Order)

**1. Rollback the Deployment** ⚡ *Confidence: 98%*
- Command: `kubectl rollout undo deployment/api-service`
- Expected impact: Service restored within 2-3 minutes
- Risk: Low (rollbacks are safe and reversible)

**2. Increase Database Connection Pool** *Confidence: 95%*
- Current: 50 connections
- Recommended: 100 connections (temporary)
- Update config: `DB_POOL_SIZE=100`
- This prevents immediate recurrence after rollback

**3. Add Query Timeout Configuration** *Confidence: 88%*
- Set: `DB_QUERY_TIMEOUT=5000` (5 seconds)
- This prevents connection pool exhaustion from hanging queries
- Apply to all database client configurations

### 🔧 Short-term Improvements (Within 24 Hours)

**4. Implement Connection Pool Monitoring**
- Add alerts when pool utilization exceeds 70%
- Dashboard: Pool usage / Active connections / Wait time
- Tool: Prometheus + Grafana

**5. Review Query Patterns**
- Identify the 12 new queries from deployment v2.3.1
- Optimize N+1 query patterns
- Add appropriate database indexes
- Estimated effort: 4-6 hours

**6. Add Database Load Testing**
- Run load tests with 2x current production traffic
- Identify breaking points before deployment
- Integrate into CI/CD pipeline

### 🛡️ Long-term Preventive Measures

**7. Implement Staged Rollout**
- Canary deployment: 5% → 25% → 50% → 100%
- Automatic rollback on error rate > 1%
- Use feature flags for risky changes

**8. Add Circuit Breakers**
- Implement Hystrix or Resilience4j patterns
- Prevent cascading failures across services
- Critical for database and external API calls

**9. Enhance Pre-deployment Validation**
- Load testing in staging with production data volumes
- Automated performance regression detection
- Required sign-off for database schema changes

### 📈 Expected Outcome
- **Immediate**: Service restoration within 5 minutes
- **Short-term**: 70% reduction in similar incidents
- **Long-term**: 90% improvement in deployment safety"""

    def _mock_general(self, user_prompt: str) -> str:
        """General response for any other query."""
        return """I've analyzed the provided system logs and identified several key insights:

1. **Service Health**: The system is experiencing a critical incident
2. **Affected Components**: Multiple services show correlated failures
3. **Pattern Recognition**: This matches a known incident pattern
4. **Recommended Action**: Follow the prioritized remediation steps

Would you like me to:
- Run a deeper analysis on a specific time window?
- Search for similar historical incidents?
- Generate a detailed remediation plan?
- Export the full RCA report?
"""
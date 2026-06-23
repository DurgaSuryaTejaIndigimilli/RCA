"""Historical incident database for pattern matching."""

HISTORICAL_INCIDENTS = [
    {
        "id": "INC-2025-09-14-003",
        "date": "2025-09-14",
        "title": "Production deployment caused 47-min outage",
        "pattern": "deployment_related",
        "root_cause": "New deployment increased DB query load by 240%",
        "resolution": "Rolled back, increased pool size, added canary rollout",
        "resolution_time_minutes": 47,
        "affected_services": ["api-gateway", "db-connection-pool", "edge-devices"]
    },
    {
        "id": "INC-2025-11-03-002",
        "date": "2025-11-03",
        "title": "Connection pool leak caused service degradation",
        "pattern": "database_issue",
        "root_cause": "Connection leak in ORM library version 4.2.1",
        "resolution": "Patched library, added connection monitoring",
        "resolution_time_minutes": 28,
        "affected_services": ["api-gateway", "db-connection-pool"]
    },
    {
        "id": "INC-2025-08-17-004",
        "date": "2025-08-17",
        "title": "Multi-service cascade from single point of failure",
        "pattern": "cascading_failure",
        "root_cause": "Auth service failure cascaded to all dependent services",
        "resolution": "Added circuit breakers, implemented bulkhead pattern",
        "resolution_time_minutes": 65,
        "affected_services": ["auth-service", "api-gateway", "user-service", "edge-devices"]
    },
]
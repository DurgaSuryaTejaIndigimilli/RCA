"""
Sample log data for demos and testing
"""

SAMPLE_DEMO_LOGS = """2026-01-15 02:10:00 [deploy-service] INFO: Starting deployment v2.3.1 to production
2026-01-15 02:10:15 [deploy-service] INFO: Deployment v2.3.1 rolled out to 100% of pods
2026-01-15 02:10:30 [api-gateway] INFO: New version v2.3.1 detected, starting warmup
2026-01-15 02:11:00 [api-gateway] INFO: Health check passed
2026-01-15 02:11:30 [api-gateway] WARN: Response time p99 = 720ms (threshold: 500ms)
2026-01-15 02:11:45 [api-gateway] WARN: Response time p99 = 1240ms
2026-01-15 02:12:00 [edge-device-7821] ERROR: Telemetry packet timeout after 5000ms
2026-01-15 02:12:15 [edge-device-7821] ERROR: Failed to upload telemetry data
2026-01-15 02:12:30 [api-gateway] WARN: Response time p99 = 1840ms
2026-01-15 02:12:45 [db-connection-pool] WARN: Active connections: 35/50
2026-01-15 02:13:00 [db-connection-pool] ERROR: Connection pool exhausted 50/50
2026-01-15 02:13:15 [db-connection-pool] ERROR: 23 requests waiting for available connection
2026-01-15 02:13:30 [api-gateway] ERROR: Database query timeout after 5000ms
2026-01-15 02:13:45 [api-gateway] ERROR: HTTP 500 - Internal server error
2026-01-15 02:14:00 [mqtt-broker] WARN: High connection latency detected
2026-01-15 02:14:15 [mqtt-broker] ERROR: Cannot establish new connections
2026-01-15 02:14:30 [edge-device-7822] ERROR: Connection lost to MQTT broker
2026-01-15 02:14:45 [edge-device-7823] ERROR: Connection lost to MQTT broker
2026-01-15 02:15:00 [api-gateway] CRITICAL: 5xx error rate = 78% (threshold: 5%)
2026-01-15 02:15:00 [alerting] CRITICAL: PagerDuty alert triggered - INC-2026-0115-001
2026-01-15 02:15:15 [api-gateway] CRITICAL: Service degradation detected
2026-01-15 02:15:30 [oncall-engineer] INFO: Alert acknowledged by John Doe
2026-01-15 02:16:00 [db-connection-pool] ERROR: Pool still exhausted, recovery in progress"""

SAMPLE_INCIDENT_LOGS = """2026-01-15 03:00:00 [mqtt-broker] INFO: Normal operation, 5423 active connections
2026-01-15 03:05:00 [mqtt-broker] WARN: Memory usage at 78%
2026-01-15 03:10:00 [mqtt-broker] WARN: Memory usage at 85%
2026-01-15 03:12:00 [mqtt-broker] ERROR: Out of memory, killing connections
2026-01-15 03:12:30 [mqtt-broker] CRITICAL: Broker shutdown - OOM killed
2026-01-15 03:13:00 [edge-device-7821] ERROR: Cannot reach MQTT broker
2026-01-15 03:13:00 [edge-device-7822] ERROR: Cannot reach MQTT broker
2026-01-15 03:13:00 [edge-device-7823] ERROR: Cannot reach MQTT broker
2026-01-15 03:13:30 [telemetry-service] ERROR: No data received from devices
2026-01-15 03:14:00 [telemetry-service] CRITICAL: Data pipeline stalled
2026-01-15 03:15:00 [alerting] CRITICAL: IoT fleet offline - 5423 devices disconnected"""
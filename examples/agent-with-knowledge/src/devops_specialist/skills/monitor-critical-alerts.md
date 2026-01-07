---
name: monitor-critical-alerts
description: How to monitor and respond to system alerts by severity
---

# Monitor Critical Alerts

Use this skill when you need to review system alerts and identify issues requiring immediate attention.

## List All Alerts

Use `api_get` tool with:
- service: "devops"
- endpoint: "/alerts"

Returns all alerts across all services and severities.

## Filter by Severity

To focus on critical issues, use `api_get` with:
- service: "devops"
- endpoint: "/alerts"
- params: {"severity": "critical"}

Available severity levels:
- **critical**: Immediate action required, service impact
- **warning**: Investigate soon, potential impact
- **info**: Informational only, no action needed

## Find Unacknowledged Alerts

Use `api_get` with:
- service: "devops"
- endpoint: "/alerts"
- params: {"acknowledged": "false"}

These alerts need review and acknowledgment.

## Alert Fields

Each alert includes:
- `id`: Unique alert identifier
- `title`: Alert description
- `severity`: Alert severity level
- `service`: Affected service name
- `acknowledged`: Whether alert has been reviewed

## Response Workflow

1. **Check for critical alerts**
   - Use severity filter: {"severity": "critical"}
   - These require immediate investigation

2. **Identify affected services**
   - Note the `service` field in each alert
   - Use check-service-health skill for affected services

3. **Review unacknowledged alerts**
   - Filter: {"acknowledged": "false"}
   - Prioritize by severity

4. **Correlate with other data**
   - Check if related pipelines have failed
   - Review recent deployments to affected services
   - Examine service health status

## Prioritization

1. Critical + Unacknowledged → Highest priority
2. Critical + Acknowledged → Monitor resolution
3. Warning + Unacknowledged → Review and triage
4. Info → Review when time permits


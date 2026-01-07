---
name: check-service-health-api-gateway
description: Detailed troubleshooting and monitoring for API Gateway (Service ID 2)
---

# API Gateway Health Check (Service ID 2)

Use this skill for deep investigation of API Gateway issues.

## Service Information

**Service ID**: 2  
**Service Name**: api-gateway  
**Technology**: Nginx with custom routing modules  
**Owner**: Platform Team (platform-team@example.com)  
**SLA**: 99.95% uptime

For full details, read the fact: `devops-services-catalog.md`

## Quick Health Check

```
api_get(service="devops", endpoint="/services/2")
```

## Key Metrics to Monitor

When checking API Gateway health, focus on these fields:

### Status Field
- `healthy`: All endpoints responding normally
- `warning`: Some endpoints slow or elevated latency
- `degraded`: Multiple endpoints failing or high error rate

### Issues Array
Common issue patterns:
- "High latency detected" → Performance degradation
- "Some requests timing out" → Backend services slow
- "Rate limiting active" → Traffic spike

### Response Time
Normal: < 100ms  
Warning: 100-500ms  
Critical: > 500ms

## Troubleshooting Steps

### Step 1: Check Current Status
```
api_get(service="devops", endpoint="/services/2")
```
Note the `status`, `response_time_ms`, and `issues` fields.

### Step 2: Check Related Alerts
```
api_get(service="devops", endpoint="/alerts")
```
Filter results for api-gateway related alerts.

### Step 3: Verify Backend Services
API Gateway depends on:
- Authentication Service (ID 3) - Token validation
- All backend services - Request routing

If API Gateway shows high latency or timeouts:
```
api_get(service="devops", endpoint="/services/3")  # Check auth service
api_get(service="devops", endpoint="/services")    # Check all services
```

### Step 4: Check Recent Deployments
```
api_get(service="devops", endpoint="/deployments")
```
Recent deployments may have introduced configuration issues.

## Common Issues and Solutions

### Issue: "High latency detected"
**Cause**: Backend services responding slowly or resource pressure  
**Impact**: Slow API responses, poor user experience  
**Action**: 
- Check response_time_ms value (threshold: > 500ms critical)
- Verify all backend services health
- Review recent deployment changes
- Check if traffic spike occurred
- Contact Platform Team if sustained > 15 minutes

### Issue: "Some requests timing out"
**Cause**: Backend services unavailable or very slow  
**Impact**: Request failures, 504 Gateway Timeout errors  
**Action**:
1. Check all services status immediately
2. Identify which backend is failing
3. Check Authentication Service (ID 3) first (most common cause)
4. Review error rates in monitoring
5. Escalate to SEV-2 if affecting > 5% of requests

### Issue: Rate limiting or traffic spike
**Cause**: Unusually high traffic volume  
**Impact**: Some requests receiving 429 responses  
**Action**:
1. Verify if legitimate traffic increase
2. Check for potential DDoS or bot traffic
3. Review API Gateway configuration
4. Contact Platform Team for capacity adjustment
5. May need temporary rate limit increase

## Health Indicators

### Good Health Signs
- Status: "healthy"
- Uptime: > 99.9%
- Response time: < 100ms
- Issues: empty array
- No critical alerts

### Warning Signs
- Status: "warning"
- Uptime: 99.0% - 99.9%
- Response time: 100-500ms
- Issues: mentions "latency"
- Warning-level alerts present

### Critical Signs
- Status: "degraded"
- Uptime: < 99.0%
- Response time: > 500ms
- Issues: mentions "timeout", "failing"
- Critical alerts present
- High error rate

## Escalation

- **Warning status**: Monitor for 15 minutes, investigate if persistent
- **Degraded status**: Immediate investigation, notify Platform Team
- **Critical alerts**: Follow incident response protocol (see fact: company-incident-response-protocol.md)
- **Response time > 1000ms**: Escalate immediately to SEV-2

## Related Skills

- `monitor-critical-alerts.md`: How to check and prioritize alerts
- `check-service-health/auth-service.md`: Check dependent authentication service
- `check-service-health.md`: General service health overview

## Related Facts

- `devops-services-catalog.md`: Complete service details and dependencies
- `deployment-environments.md`: Deployment policies and rollback procedures
- `company-incident-response-protocol.md`: Incident response procedures

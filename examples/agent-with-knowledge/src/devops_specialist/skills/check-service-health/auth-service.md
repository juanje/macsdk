---
name: check-service-health-auth-service
description: Detailed troubleshooting and monitoring for Authentication Service (Service ID 3)
---

# Authentication Service Health Check (Service ID 3)

Use this skill for deep investigation of Authentication Service issues.

## Service Information

**Service ID**: 3  
**Service Name**: auth-service  
**Technology**: Custom service with JWT token management  
**Owner**: Security Team (security-team@example.com)  
**SLA**: 99.99% uptime (CRITICAL SERVICE)

⚠️ **Note**: This is a critical service with the highest SLA requirement.

For full details, read the fact: `devops-services-catalog.md`

## Quick Health Check

```
api_get(service="devops", endpoint="/services/3")
```

## Critical Dependencies

Authentication Service depends on:
1. **Redis Cache (Service ID 5)** - Session storage
2. **Postgres Primary (Service ID 4)** - User data storage

Always check dependent services when investigating auth issues.

## Key Metrics to Monitor

### Status Field Interpretation
- `healthy`: All authentication flows working
- `warning`: Elevated error rates or performance issues
- `degraded`: Authentication failures occurring

### Issues Array
Critical patterns to watch:
- "Redis connection issues" → Session management failure
- "Token validation delays" → Performance degradation
- "Database connection" → Backend storage issues
- "High authentication request volume" → Capacity issue

## Troubleshooting Steps

### Step 1: Check Service Status
```
api_get(service="devops", endpoint="/services/3")
```

### Step 2: Verify Critical Dependencies
```
api_get(service="devops", endpoint="/services/5")  # Redis Cache
api_get(service="devops", endpoint="/services/4")  # Postgres Primary
```
If either dependency has issues, Auth Service will degrade.

### Step 3: Check for Critical Alerts
```
api_get(service="devops", endpoint="/alerts")
```
Look for auth-service or authentication-related alerts.

### Step 4: Check Recent Deployments
```
api_get(service="devops", endpoint="/deployments")
```
Look for recent auth-service deployments.

## Common Issues and Solutions

### Issue: "Redis connection issues affecting sessions"
**Severity**: CRITICAL  
**Cause**: Redis Cache (ID 5) unavailable or connection pool exhausted  
**Impact**: New logins failing, sessions lost  
**Action**:
1. Check Redis Cache health (Service ID 5) immediately
2. Verify if Redis is down or degraded
3. Escalate to Security Team AND Platform Team
4. Follow SEV-1 incident protocol if logins failing
5. May require Redis restart or failover

### Issue: "Token validation delays"
**Severity**: MODERATE to HIGH  
**Cause**: High load or database performance issues  
**Impact**: Slow API responses, poor user experience  
**Action**:
1. Check response times in service status
2. Verify Postgres Primary health (Service ID 4)
3. Check if traffic spike or sustained high volume
4. Notify Security Team if delay > 2 seconds
5. May need scaling or caching adjustments

### Issue: "High authentication request volume"
**Severity**: MODERATE (can escalate)  
**Cause**: Traffic spike or potential attack  
**Impact**: Slow authentication, possible service degradation  
**Action**:
1. Check if legitimate traffic increase
2. Review for potential brute force attack patterns
3. Check rate limiting configuration
4. Notify Security Team to assess
5. May need temporary capacity increase
6. Consider enabling additional rate limits

### Issue: "Database connection pool saturation"
**Severity**: HIGH  
**Cause**: Connection leak or too many concurrent requests  
**Impact**: New authentications failing  
**Action**:
1. Check Postgres Primary status (Service ID 4)
2. Review connection pool configuration
3. Check for connection leaks in recent deployments
4. Escalate to Security Team AND Database Team
5. May require service restart

## Health Indicators

### Good Health Signs
- Status: "healthy"
- Uptime: > 99.99%
- Issues: empty array
- Redis Cache (ID 5) healthy
- Postgres Primary (ID 4) healthy
- No alerts

### Warning Signs (Requires Attention)
- Status: "warning"
- Any mention of delays or high volume
- Token validation > 1 second
- Warning alerts present
- Uptime: 99.9% - 99.99%

### Critical Signs (Immediate Action)
- Status: "degraded"
- "Redis connection issues"
- "Database connection" issues
- Critical alerts present
- Uptime: < 99.9%
- Authentication failures occurring

## Impact Assessment

Authentication Service affects:
- **API Gateway (ID 2)**: Cannot validate tokens
- **Web Frontend (ID 1)**: Login failures
- **All API calls**: Authorization failures
- **Worker Queue (ID 6)**: Authenticated job processing fails

When Auth Service degrades, expect cascading issues across entire infrastructure.

## Escalation Path

1. **Warning status** + < 15 min duration:
   - Monitor closely
   - Inform Security Team via Slack

2. **Warning status** + > 15 min duration:
   - Escalate to Security Team on-call
   - Prepare for potential SEV-2

3. **Degraded status** or **Critical alerts** or **Login failures**:
   - Immediate SEV-1 incident
   - Notify Security Team AND SRE Team
   - Follow incident response protocol
   - Notify VP Engineering within 30 minutes

## Quick Command Reference

```bash
# Check auth service
api_get(service="devops", endpoint="/services/3")

# Check critical dependencies
api_get(service="devops", endpoint="/services/5")  # Redis
api_get(service="devops", endpoint="/services/4")  # Postgres

# Check all alerts
api_get(service="devops", endpoint="/alerts")

# Check recent deployments
api_get(service="devops", endpoint="/deployments")
```

## Related Skills

- `check-service-health/redis-cache.md`: Redis troubleshooting
- `check-service-health/postgres-primary.md`: Database troubleshooting
- `monitor-critical-alerts.md`: Alert prioritization
- `check-service-health.md`: General overview

## Related Facts

- `devops-services-catalog.md`: Service dependencies and SLAs
- `company-incident-response-protocol.md`: SEV-1 incident procedures

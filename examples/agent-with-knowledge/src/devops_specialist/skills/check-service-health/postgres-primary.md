---
name: check-service-health-postgres-primary
description: Detailed troubleshooting and monitoring for Postgres Primary (Service ID 4)
---

# Postgres Primary Health Check (Service ID 4)

Use this skill for deep investigation of the primary PostgreSQL database.

## Service Information

**Service ID**: 4  
**Service Name**: postgres-primary  
**Technology**: PostgreSQL 15 with streaming replication  
**Owner**: Database Team (dba-team@example.com)  
**SLA**: 99.99% uptime  
**Critical Dependencies**: None (foundational service)

⚠️ **Note**: This is a foundational service - many other services depend on it.

For full details, read the fact: `devops-services-catalog.md`

## Quick Health Check

```
api_get(service="devops", endpoint="/services/4")
```

## Dependent Services

Postgres Primary is critical for:
- **Authentication Service (ID 3)** - User data
- **Worker Queue (ID 6)** - Job state and queue management
- **All application services** - Primary data store

Database issues create widespread impact.

## Key Metrics to Monitor

### Status Field Interpretation
- `healthy`: Primary and replicas operating normally
- `warning`: Performance degradation or resource pressure
- `degraded`: Query failures or connection issues

### Issues Array
Critical patterns:
- "Connection pool exhaustion" → Too many connections
- "Slow query performance under load" → Performance issue
- "Replication lag to read replicas" → Replication problem
- "Disk space pressure" → Capacity issue

## Troubleshooting Steps

### Step 1: Check Database Status
```
api_get(service="devops", endpoint="/services/4")
```

### Step 2: Check Critical Alerts
```
api_get(service="devops", endpoint="/alerts")
```
Look for postgres-related alerts.

### Step 3: Check Dependent Services
If database has issues, check impact:
```
api_get(service="devops", endpoint="/services/3")  # Auth Service
api_get(service="devops", endpoint="/services/6")  # Worker Queue
api_get(service="devops", endpoint="/services")    # All services
```

### Step 4: Review Recent Changes
```
api_get(service="devops", endpoint="/deployments")
```
Look for recent migrations or schema changes.

## Common Issues and Solutions

### Issue: "Connection pool exhaustion"
**Severity**: CRITICAL  
**Cause**: Too many concurrent connections or connection leak  
**Impact**: New connections failing, application errors  
**Action**:
1. Identify which service(s) holding connections
2. Check recent deployments for connection leaks
3. Escalate to Database Team immediately
4. May require application restart
5. SEV-1 if affecting user-facing services

### Issue: "Slow query performance under load"
**Severity**: MODERATE to HIGH  
**Cause**: Missing indexes, inefficient queries, or resource pressure  
**Impact**: Slow API responses, degraded user experience  
**Action**:
1. Review recent code deployments
2. Check if sustained high query volume
3. Identify slow queries (Database Team has monitoring)
4. Escalate to Database Team for query optimization
5. May need index creation or query rewriting

### Issue: "Replication lag to read replicas"
**Severity**: MODERATE to HIGH  
**Cause**: Write-heavy workload or replication issues  
**Impact**: Read replicas serving stale data  
**Action**:
1. Check lag duration (< 1 minute: normal, > 5 minutes: urgent)
2. If lag > 5 minutes: Escalate to Database Team
3. If lag > 15 minutes: Consider SEV-2 incident
4. Review recent deployment for query changes
5. May need read query optimization or replica scaling

### Issue: "Disk space pressure"
**Severity**: HIGH (escalates quickly)  
**Cause**: Transaction logs or data growth  
**Impact**: Database will fail when disk full  
**Action**:
1. Check remaining disk space percentage
2. If < 10%: URGENT - Escalate immediately (SEV-1)
3. If < 20%: Escalate to Database Team
4. Database Team needs to cleanup or expand storage
5. Plan capacity expansion if growth pattern

## Health Indicators

### Good Health Signs
- Status: "healthy"
- Uptime: > 99.99%
- Issues: empty array
- Connection pool: < 70% utilized
- Replication lag: < 1 minute
- No critical alerts

### Warning Signs
- Status: "warning"
- Connection pool: 70-90% utilized
- Slow queries detected
- Replication lag: 1-5 minutes
- Warning alerts present

### Critical Signs
- Status: "degraded"
- Connection pool: > 90% or exhausted
- Query failures occurring
- Replication lag: > 5 minutes
- Disk space: < 20% free
- Critical alerts present

## Escalation Path

1. **Warning status**:
   - Monitor for 10 minutes
   - If persists: Notify Database Team via Slack

2. **Degraded status** OR **Connection pool exhaustion**:
   - Immediate escalation to Database Team on-call
   - Prepare incident documentation
   - SEV-2 if user-facing impact

3. **Critical alerts** OR **Disk space < 10%**:
   - SEV-1 incident
   - Notify Database Team AND SRE Team
   - Notify VP Engineering
   - Follow incident response protocol

## Impact on Other Services

When Postgres Primary has issues:
1. Check Authentication Service (ID 3) - Login failures likely
2. Check Worker Queue (ID 6) - Job processing will fail
3. Check all critical alerts - Expect cascading failures
4. API Gateway (ID 2) may show elevated error rates

## Quick Command Reference

```bash
# Check database health
api_get(service="devops", endpoint="/services/4")

# Check critical database alerts
api_get(service="devops", endpoint="/alerts")

# Check dependent services
api_get(service="devops", endpoint="/services/3")  # Auth
api_get(service="devops", endpoint="/services/6")  # Worker Queue
api_get(service="devops", endpoint="/services")    # All services

# Check recent deployments/migrations
api_get(service="devops", endpoint="/deployments")
```

## Related Skills

- `check-service-health/auth-service.md`: Check dependent auth service
- `check-service-health/worker-queue.md`: Check dependent worker service
- `monitor-critical-alerts.md`: Alert handling
- `check-service-health.md`: General overview

## Related Facts

- `devops-services-catalog.md`: Service dependencies map
- `company-incident-response-protocol.md`: Incident procedures

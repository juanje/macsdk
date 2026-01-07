---
name: check-service-health
description: How to check the health status of infrastructure services (general guidance)
---

# Check Service Health

Use this skill when you need to assess the operational status of infrastructure services.

## Quick Overview

### List All Services
Use `api_get` tool with:
- service: "devops"
- endpoint: "/services"

This returns all monitored services with their current status.

### Get Specific Service Details
Use `api_get` tool with:
- service: "devops"
- endpoint: "/services/{id}"
- Replace {id} with service ID (1-6)

## Available Services

The infrastructure monitors these services:
1. **web-frontend** - Customer-facing web application
2. **api-gateway** - Backend API entry point
3. **auth-service** - Authentication and authorization
4. **postgres-primary** - Primary database
5. **redis-cache** - Caching layer
6. **worker-queue** - Background job processing

## Service Status Interpretation

Services can have these statuses:
- **healthy**: Operating normally, no action needed
- **warning**: Minor issues detected, monitor closely
- **degraded**: Significant issues, immediate attention required

## Response Fields

Each service includes:
- `id`: Unique service identifier (1-6)
- `name`: Service name
- `status`: Current operational status
- `uptime_percent`: Service uptime percentage
- `last_check`: Timestamp of last health check
- `response_time_ms`: Response time in milliseconds (if applicable)
- `issues`: Array of current issues (if any)

## General Workflow

1. Start with `/services` to get overview
2. If issues found, get specific service details with `/services/{id}`
3. Check the `issues` field for detailed problem descriptions
4. Cross-reference with alerts using service name
5. For deeper investigation, use service-specific skills (see below)

## Service-Specific Skills

For detailed troubleshooting and monitoring of specific services, use these specialized skills:

- **check-service-health/api-gateway.md** (Service ID 2): Deep dive into API Gateway health, latency issues, timeout problems
- **check-service-health/auth-service.md** (Service ID 3): Authentication service health, token management, dependency issues
- **check-service-health/postgres-primary.md** (Service ID 4): Database health, connection pools, query performance

These service-specific skills provide:
- Service-specific metrics to check
- Common failure patterns
- Troubleshooting steps
- Related alerts and dependencies to examine
- Escalation procedures

## When to Use Service-Specific Skills

- Use this general skill for **overview and initial assessment**
- Use service-specific skills when:
  - A specific service shows issues
  - User asks about a particular service
  - You need detailed troubleshooting steps
  - You need to understand service-specific behavior

## Example Tasks

**General Check**: "Check if all services are healthy"
→ Use this skill
→ Call `/services`
→ Report overall status

**Specific Check**: "Why is the API Gateway having issues?"
→ Use this skill to identify the issue
→ Use `check-service-health/api-gateway.md` for deep troubleshooting
→ Follow service-specific investigation steps

**Impact Assessment**: "Is the auth problem affecting other services?"
→ Use `check-service-health/auth-service.md` to understand dependencies
→ Check dependent services mentioned in the skill
→ Read `devops-services-catalog.md` fact for service interaction map

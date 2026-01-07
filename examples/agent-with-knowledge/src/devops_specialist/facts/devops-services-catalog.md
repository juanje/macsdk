---
name: devops-services-catalog
description: Detailed catalog of monitored infrastructure services and their roles
---

# DevOps Services Catalog

This document describes all services monitored in the infrastructure.

## Service ID 1: Web Frontend (web-frontend)

**Purpose**: Customer-facing web application interface

**Technology**: React SPA with Next.js framework

**Owner**: Frontend Team (frontend-team@example.com)

**Critical Dependencies**: 
- API Gateway (ID 2)
- CDN infrastructure

**SLA**: 99.95% uptime

**Typical Issues**:
- Build deployment failures
- CDN cache invalidation delays
- Static asset loading issues

## Service ID 2: API Gateway (api-gateway)

**Purpose**: Main entry point for all backend API traffic

**Technology**: Nginx with custom routing modules

**Owner**: Platform Team (platform-team@example.com)

**Critical Dependencies**: 
- Authentication Service (ID 3)
- Backend services

**SLA**: 99.95% uptime

**Typical Issues**:
- High latency under load
- Request timeout issues
- Rate limiting triggers during traffic spikes
- Upstream service connection issues

## Service ID 3: Authentication Service (auth-service)

**Purpose**: Handles user authentication and session management

**Technology**: Custom service with JWT token management

**Owner**: Security Team (security-team@example.com)

**Critical Dependencies**:
- Redis Cache (ID 5) for session storage
- Postgres Primary (ID 4) for user data

**SLA**: 99.99% uptime (critical service)

**Typical Issues**:
- Redis connection issues affecting sessions
- Token validation delays
- High authentication request volume
- Database connection pool saturation

## Service ID 4: Postgres Primary (postgres-primary)

**Purpose**: Primary PostgreSQL database for application data

**Technology**: PostgreSQL 15 with streaming replication

**Owner**: Database Team (dba-team@example.com)

**Critical Dependencies**: None (foundational service)

**SLA**: 99.99% uptime

**Typical Issues**:
- Connection pool exhaustion
- Slow query performance under load
- Replication lag to read replicas
- Disk space pressure

## Service ID 5: Redis Cache (redis-cache)

**Purpose**: Distributed caching layer for sessions and data

**Technology**: Redis Cluster

**Owner**: Platform Team (platform-team@example.com)

**Critical Dependencies**: None

**SLA**: 99.9% uptime

**Typical Issues**:
- Memory pressure from large cache entries
- Key eviction rate too high
- Connection pool exhaustion
- Network latency to cache cluster

## Service ID 6: Worker Queue (worker-queue)

**Purpose**: Asynchronous background job processing

**Technology**: Custom worker service with queue system

**Owner**: Backend Team (backend-team@example.com)

**Critical Dependencies**:
- Postgres Primary (ID 4) for job state
- Redis Cache (ID 5) for queue management

**SLA**: 99.9% uptime

**Typical Issues**:
- Queue depth growing (slow processing)
- Worker process crashes
- Job timeout failures
- Dead letter queue accumulation

## Service Interaction Map

```
Users → Web Frontend (1)
            ↓
       API Gateway (2)
            ↓
       Auth Service (3) ← Redis Cache (5)
            ↓              ↓
       Postgres Primary (4)
            ↓
       Worker Queue (6) ← Redis Cache (5)
```

## Critical Service Priority

**Tier 1 (Critical - SEV-1 if down)**:
- Service ID 3: auth-service (99.99% SLA)
- Service ID 4: postgres-primary (99.99% SLA)

**Tier 2 (Important - SEV-2 if degraded)**:
- Service ID 2: api-gateway (99.95% SLA)
- Service ID 1: web-frontend (99.95% SLA)
- Service ID 5: redis-cache (99.9% SLA)

**Tier 3 (Standard - Monitor and fix)**:
- Service ID 6: worker-queue (99.9% SLA)

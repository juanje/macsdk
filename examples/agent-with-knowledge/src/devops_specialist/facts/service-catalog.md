---
name: service-catalog
description: Information about available services and their configurations
---

# Service Catalog

This document provides contextual information about the services in our infrastructure.

## Production Services

### API Gateway (ID: 1)
- **Endpoint**: /services/1
- **Critical**: Yes
- **Deployment**: Rolling updates, 5-minute intervals
- **Health Check**: /health endpoint, 30-second timeout
- **Dependencies**: None
- **Scaling**: Auto-scales 2-10 instances

### Auth Service (ID: 2)
- **Endpoint**: /services/2
- **Critical**: Yes
- **Deployment**: Blue-green deployment required
- **Health Check**: /health endpoint, 10-second timeout
- **Dependencies**: PostgreSQL, Redis
- **Scaling**: Fixed 3 instances

### User Service (ID: 3)
- **Endpoint**: /services/3
- **Critical**: Yes
- **Deployment**: Canary deployment (10% → 50% → 100%)
- **Health Check**: /health endpoint, 15-second timeout
- **Dependencies**: PostgreSQL, Message Queue
- **Scaling**: Auto-scales 3-15 instances

### Notification Service (ID: 4)
- **Endpoint**: /services/4
- **Critical**: No
- **Deployment**: Rolling updates
- **Health Check**: /health endpoint, 20-second timeout
- **Dependencies**: Message Queue, Email Service
- **Scaling**: Auto-scales 1-5 instances

### Analytics Service (ID: 5)
- **Endpoint**: /services/5
- **Critical**: No
- **Deployment**: Direct deployment (low traffic)
- **Health Check**: /health endpoint, 30-second timeout
- **Dependencies**: Data Warehouse, Cache
- **Scaling**: Fixed 2 instances

### Reporting Service (ID: 6)
- **Endpoint**: /services/6
- **Critical**: No
- **Deployment**: Scheduled deployment (off-peak)
- **Health Check**: /health endpoint, 60-second timeout
- **Dependencies**: Data Warehouse
- **Scaling**: Fixed 1 instance

## Deployment Windows

- **Critical Services**: Monday-Thursday, 10:00-14:00 UTC
- **Non-Critical Services**: Any time, avoid peak hours (12:00-13:00, 17:00-19:00 UTC)

## Alert Severity Levels

- **Critical**: Immediate action required, service down
- **Warning**: Performance degraded, investigate soon
- **Info**: Informational, review when convenient

## Common Endpoints

- List all services: GET /services
- Get service details: GET /services/{id}
- List alerts: GET /alerts
- List deployments: GET /deployments
- List pipelines: GET /pipelines
- Get job details: GET /jobs

## SLA Targets

- Critical services: 99.9% uptime (43 minutes/month downtime max)
- Non-critical services: 99% uptime (7.2 hours/month downtime max)


---
name: deployment-environments
description: Information about deployment environments, policies, and approval workflows
---

# Deployment Environments

This document describes the deployment environments and their governance policies.

## Environment: development

**Purpose**: Active development and feature testing

**Cluster**: dev-k8s-cluster-01 (3 nodes)

**Region**: us-west-2a

**Deployment Frequency**: Continuous (on every merge to develop branch)

**Approval Required**: No

**Rollback Policy**: Automatic on health check failure

**Access**: All developers

**Special Notes**:
- Database is reset nightly at 02:00 UTC
- Feature flags enabled by default
- Debug logging at INFO level

## Environment: staging

**Purpose**: Pre-production validation and integration testing

**Cluster**: staging-k8s-cluster-01 (5 nodes)

**Region**: us-west-2b

**Deployment Frequency**: Daily (14:00 UTC)

**Approval Required**: Yes (Tech Lead approval)

**Rollback Policy**: Manual within 1 hour window

**Access**: Developers + QA Team

**Special Notes**:
- Database mirrors production schema
- Uses production-like traffic patterns (20% load)
- All monitoring alerts active
- Change freeze: 2 days before major releases

## Environment: production

**Purpose**: Live customer-facing services

**Cluster**: prod-k8s-cluster-01 through prod-k8s-cluster-04 (20 nodes total)

**Region**: Multi-region (us-west-2, us-east-1, eu-west-1)

**Deployment Frequency**: Tuesday and Thursday at 10:00 UTC

**Approval Required**: Yes (requires 2 approvals: Tech Lead + SRE)

**Rollback Policy**: 
- Automatic rollback if error rate > 1%
- Manual rollback available within 4 hours
- Full rollback beyond 4 hours requires incident review

**Access**: SRE Team + designated release engineers

**Deployment Windows**:
- Normal: Tuesday/Thursday 10:00-12:00 UTC
- Emergency: Any time with VP Engineering approval
- Blackout periods: 
  - Black Friday week (Nov 20-27)
  - End of quarter (last 3 days)
  - Major holiday weekends

**Special Notes**:
- Blue-green deployment strategy
- Canary deployment: 5% → 25% → 100% over 2 hours
- Database migrations require separate approval
- All changes must have runbook documentation
- Post-deployment monitoring: 24 hours minimum

## Deployment Approval Matrix

| Environment | Code Review | Tech Lead | SRE | VP Engineering |
|------------|-------------|-----------|-----|----------------|
| development | Required    | -         | -   | -              |
| staging     | Required    | Required  | -   | -              |
| production  | Required    | Required  | Required | Emergency only |

## Emergency Hotfix Procedure

For critical production issues:

1. Create hotfix branch from production tag
2. Implement minimal fix with tests
3. Deploy to staging for validation (30 min max)
4. Get expedited approval (Tech Lead + SRE on-call)
5. Deploy to production with enhanced monitoring
6. Post-incident review within 24 hours

**Hotfix SLA**: From issue identification to production fix in < 2 hours for critical severity.


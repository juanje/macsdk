---
name: deploy-service
description: How to safely deploy a service to production
---

# Deploy Service

This skill provides step-by-step instructions for safely deploying a service to production.

## Prerequisites

Before deploying:
1. Verify the service passes all tests in CI/CD
2. Check that staging deployment is successful
3. Ensure the deployment window is appropriate (avoid peak hours)
4. Have rollback plan ready

## Deployment Steps

### 1. Pre-Deployment Checks

```
- Verify current service health: GET /services/{service-id}
- Check for active alerts: GET /alerts?acknowledged=false
- Review recent deployments: GET /deployments?environment=production
```

### 2. Deploy Process

1. **Start deployment**:
   - Use the deployment API to initiate
   - Monitor the pipeline: GET /pipelines/{id}

2. **Monitor progress**:
   - Watch job status: GET /jobs?pipelineId={id}
   - If any job fails, fetch logs immediately
   - Use fetch_file tool to get detailed error logs

3. **Verify deployment**:
   - Check service status after deployment
   - Verify health endpoints respond correctly
   - Monitor for new alerts

### 3. Post-Deployment

- Monitor service for 15 minutes after deployment
- Check error rates and response times
- Verify no critical alerts are triggered

## Rollback Procedure

If issues are detected:

1. Stop current deployment immediately
2. Trigger rollback using deployment API
3. Verify previous version is restored
4. Check service health returns to normal
5. Document the issue for review

## Common Issues

- **Deployment stuck**: Check pipeline status and job logs
- **Service degraded**: Compare before/after metrics
- **New alerts**: Investigate root cause before proceeding

## Related

- See `service-catalog.md` (facts) for service-specific deployment notes
- Use calculate() tool for uptime percentage calculations


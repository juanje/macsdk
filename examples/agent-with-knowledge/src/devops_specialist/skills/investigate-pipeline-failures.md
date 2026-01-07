---
name: investigate-pipeline-failures
description: How to investigate and diagnose CI/CD pipeline failures
---

# Investigate Pipeline Failures

Use this skill when you need to troubleshoot failed CI/CD pipelines and identify root causes.

## Step 1: List Failed Pipelines

Use `api_get` tool with:
- service: "devops"
- endpoint: "/pipelines"
- params: {"status": "failed"}

This returns all pipelines that have failed.

## Step 2: Get Pipeline Details

For each failed pipeline, use `api_get` with:
- service: "devops"
- endpoint: "/pipelines/{id}"
- Replace {id} with the pipeline ID from step 1

Pipeline fields include:
- `name`: Pipeline name
- `status`: Current status (passed/failed/running)
- `branch`: Git branch
- `commit`: Commit hash

## Step 3: Find Failed Jobs

Use `api_get` with:
- service: "devops"
- endpoint: "/jobs"
- params: {"pipelineId": "{pipeline_id}"}

Or to see all failed jobs across pipelines:
- params: {"status": "failed"}

Job fields include:
- `name`: Job name
- `pipelineId`: Parent pipeline
- `status`: Job status
- `duration`: Execution time
- `error`: Error message (if failed)
- `log_url`: URL to full logs

## Step 4: Retrieve Log Files

If a job has a `log_url`, use `fetch_file` tool with:
- url: The log_url value from the job

This downloads the complete log file for detailed analysis.

## Analysis Guidelines

1. Start broad: List all failed pipelines
2. Focus on recent failures: Check commit and branch info
3. Identify patterns: Multiple jobs failing suggests systemic issue
4. Read logs: Always check log files for detailed error messages
5. Correlate with services: Failed deploy jobs may relate to service issues

## Common Patterns

- Build job fails → Check compilation errors in logs
- Test job fails → Check test failures in logs
- Deploy job fails → Check service status and deployment history


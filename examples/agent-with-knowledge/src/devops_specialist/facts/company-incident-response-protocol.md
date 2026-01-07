---
name: company-incident-response-protocol
description: TechCorp Inc incident response procedures and escalation policies (established 2024)
---

# TechCorp Inc Incident Response Protocol

**Document Version**: 3.2 (Effective January 15, 2024)

**Company**: TechCorp Inc (fictional company for testing)

**Last Updated**: December 15, 2024 by SRE Team

## Incident Severity Classification

### SEV-1 (Critical)
**Definition**: Complete service outage or security breach

**Response Time**: 15 minutes

**Escalation**: Immediate to VP Engineering (Alice Rodriguez, ext. 5501)

**Communication**: 
- Customer notification within 30 minutes
- Status page update every 15 minutes
- CEO (Bob Martinez) must be informed within 1 hour

**Recent SEV-1 Example**: 
- Incident #2024-09-15-001: Database cluster failure
- Duration: 47 minutes
- Root cause: Disk space exhaustion on primary node
- Resolution: Emergency capacity expansion

### SEV-2 (Major)
**Definition**: Partial service degradation affecting > 20% of users

**Response Time**: 30 minutes

**Escalation**: Engineering Manager (Carlos Johnson, ext. 5502)

**Communication**:
- Status page update every 30 minutes
- Customer support notified immediately
- Post-mortem required within 48 hours

### SEV-3 (Minor)
**Definition**: Minor issues affecting < 5% of users or non-critical features

**Response Time**: 2 hours

**Escalation**: Team Lead level

**Communication**:
- Internal Slack notification
- Status page update if customer-facing

## On-Call Schedule (Week of Dec 29, 2024)

**Primary On-Call**: Diana Patel (diana.patel@techcorp.example, +1-555-0142)

**Secondary On-Call**: Edward Kim (edward.kim@techcorp.example, +1-555-0143)

**Manager On-Call**: Fatima Okonkwo (fatima.okonkwo@techcorp.example, +1-555-0144)

**Rotation**: Weekly, Sunday to Sunday

## Incident Command Structure

For SEV-1 and SEV-2 incidents, establish incident command:

**Incident Commander (IC)**: Primary on-call engineer
- Coordinates all response activities
- Makes decisions on investigation vs. mitigation
- Approves all production changes during incident

**Technical Lead**: Most experienced engineer for affected system
- Drives technical investigation
- Implements fixes
- Reports to IC every 15 minutes

**Communications Lead**: Designated from support team
- Updates status page
- Coordinates customer communications
- Documents timeline

**Scribe**: Junior engineer or rotating role
- Documents all actions in incident log
- Tracks timeline
- Records decisions and their rationale

## TechCorp Specific Policies

### War Room Protocol
For SEV-1 incidents:
- Physical war room: Building C, Conference Room "Apollo"
- Virtual war room: Zoom link in incident channel
- Recording mandatory for post-mortem

### Blameless Post-Mortem
Required for all SEV-1 and SEV-2 incidents within 5 business days:
- Root cause analysis
- Timeline of events
- Action items with owners
- Reviewed by Director of Engineering (Grace Thompson)

### Known System Quirks (As of Q4 2024)

**The "Tuesday Slowdown"**:
- Every Tuesday 14:00-16:00 UTC, expect 10-15% performance degradation
- Root cause: Automated backup processes
- Mitigation: Scheduled optimization in Q1 2025

**Cache Warmup Issue**:
- After cache layer restart, first 5 minutes show elevated latency
- Workaround: Gradual traffic ramp-up
- Fix pending: Redis persistence configuration update

**Authentication Service "Ghost Tokens"**:
- Occasionally tokens persist 5 minutes beyond expiration
- Impact: Minimal (only affects logout timing)
- Fix scheduled: Auth service v2.4.0 (February 2025)

## Emergency Contact Tree

```
Incident Detected
       ↓
Primary On-Call (Diana)
       ↓
If no response in 15 min → Secondary On-Call (Edward)
       ↓
If no response in 15 min → Manager On-Call (Fatima)
       ↓
For SEV-1 → VP Engineering (Alice)
       ↓
For security incidents → CISO (Henry Zhang, ext. 5600)
```

## Post-Incident Actions

Within 24 hours:
- Draft post-mortem document
- Schedule post-mortem review meeting
- Update runbooks with lessons learned
- File Jira tickets for preventive actions

Within 1 week:
- Finalize and publish post-mortem
- Present findings to engineering team
- Begin work on high-priority preventive measures

## Historical Note

TechCorp Inc moved to this protocol after the "Great Outage of March 2024" which lasted 6 hours due to poor incident coordination. This protocol has reduced Mean Time To Resolution (MTTR) by 65% since implementation.


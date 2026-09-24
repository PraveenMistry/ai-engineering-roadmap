# Engineering Practices

## Code Review
Every pull request requires at least one approval before merging into the main
branch. Pull requests that touch authentication, billing, or data deletion logic
require two approvals, including one from a senior engineer.

## Branching Strategy
The team uses trunk-based development. Feature branches should be short-lived,
ideally merged within 2-3 days of being opened. Long-running feature branches
are discouraged due to merge conflict risk.

## Testing Requirements
All new features must include unit tests covering the core logic. Code coverage
for new pull requests should not drop the overall project coverage below 80%.
Critical paths (payments, auth, data pipelines) require integration tests in
addition to unit tests.

## Deployment
Deployments to production happen through the CI/CD pipeline only. Manual
deployments to production are not permitted except during a declared incident,
and must be logged in the incident channel afterward.

## On-Call
Engineers on the on-call rotation are expected to acknowledge production alerts
within 15 minutes during business hours and within 30 minutes outside business
hours. On-call rotations are weekly and are compensated with a stipend.

## Incident Response
Any production incident affecting customers must be logged with a severity level
(SEV1-SEV3) and a post-incident review must be completed within 5 business days
for SEV1 and SEV2 incidents.

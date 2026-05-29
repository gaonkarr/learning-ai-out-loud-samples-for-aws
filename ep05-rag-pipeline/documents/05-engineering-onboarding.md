# PineRidge Solutions — Engineering Team Onboarding Guide
**Document ID: PR-ENG-2026-011**
**For: New engineers joining any PineRidge engineering team**
**Maintained by: Engineering Operations**
**Last updated: March 15, 2026**

---

## Welcome to Engineering

You're joining a team of about 140 engineers across five squads. We build data infrastructure tools for mid-size logistics companies — our core product, RouteForge, handles shipment optimization, warehouse flow, and real-time fleet tracking.

This guide covers engineering-specific onboarding. For company-wide orientation, see the Employee Handbook (PR-HB-2026-042).

---

## Section 1: Engineering Organization

### 1.1 Team Structure

| Squad | Focus | Tech Lead | Team Size |
|-------|-------|-----------|-----------|
| Atlas | Core routing engine and optimization algorithms | Priya Ramachandran | 28 |
| Beacon | Real-time tracking, event streaming, telemetry | Marcus Chen | 24 |
| Cartography | Maps, geospatial services, address resolution | Aisha Okafor | 22 |
| Dockside | Warehouse management, inventory flow | Jonas Eriksson | 18 |
| Echo | Platform, infrastructure, developer experience | Sam Tremblay | 26 |
| (Staff+) | Architecture, cross-cutting concerns, tech strategy | Reports to VP Eng | 12 |

You'll be assigned to a squad before your start date. Your tech lead is your primary technical mentor for the first 90 days.

### 1.2 Reporting Structure

- Individual contributors (L1–L3) report to an Engineering Manager (EM).
- Senior ICs (L4+) report to a Senior EM or Director.
- Each squad has one EM and one Tech Lead. The EM handles people management; the Tech Lead handles technical direction. They partner closely.
- The VP of Engineering (Diane Foster) leads the overall engineering org.

### 1.3 Key Meetings

| Meeting | Frequency | Duration | Purpose |
|---------|-----------|----------|---------|
| Squad standup | Daily (async option available) | 15 min | Blockers, coordination |
| Sprint planning | Bi-weekly (Monday) | 60 min | Commit to sprint goals |
| Sprint retro | Bi-weekly (Friday) | 45 min | Process improvements |
| Tech lead sync | Weekly | 30 min | Cross-squad alignment |
| Architecture review | Monthly | 90 min | Significant design decisions |
| Eng all-hands | Monthly (first Thursday) | 45 min | Updates, demos, recognition |
| 1:1 with EM | Weekly | 30 min | Career, blockers, feedback |

---

## Section 2: Development Environment Setup

### 2.1 Day 1 Checklist

Your laptop arrives pre-configured by IT. On Day 2, complete these engineering-specific setup steps:

1. **GitHub access:** Accept the invite to the `pineridge-eng` org. Enable 2FA if not already active.
2. **Clone the monorepo:** `git clone git@github.com:pineridge-eng/routeforge.git` — this is the main codebase (~2.3M lines).
3. **Run the setup script:** `./scripts/dev-setup.sh` — installs dependencies, configures local environment, and runs the test suite.
4. **Verify local build:** `make build && make test` should pass within 15 minutes on the standard MacBook Pro.
5. **Access staging environment:** Request staging access in #eng-access (Slack). Approved within 4 hours.
6. **Install IDE extensions:** Recommended list at `docs/ide-setup.md` in the repo.
7. **Set up Harvest:** Configure time tracking with project codes from your EM.
8. **Join Slack channels:** #engineering, #eng-{your-squad}, #incidents, #deploy-notifications, #code-review.

### 2.2 Development Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend services | Go (1.22+) | Primary language for all new services since 2022 |
| Legacy backend | Python 3.11 | Older services, being migrated to Go over 2025–2027 |
| API layer | gRPC (internal), REST/OpenAPI (external) | All new external APIs are REST |
| Frontend | React 18, TypeScript 5.4 | Dashboard and admin console |
| Mobile | React Native | Driver and warehouse apps |
| Database | PostgreSQL 16 (primary), Redis (caching) | All data access through repository pattern |
| Message broker | Apache Kafka | Event-driven architecture between services |
| Search | Elasticsearch 8.x | Shipment search and analytics |
| Infrastructure | AWS (EKS, RDS, S3, SQS) | Terraform for IaC |
| CI/CD | GitHub Actions | Automated test, build, deploy pipeline |
| Observability | Datadog (metrics, traces, logs) | All services instrumented |
| Feature flags | LaunchDarkly | All new features behind flags |

### 2.3 Monorepo Structure

```
routeforge/
├── services/           # Individual backend services
│   ├── routing-engine/
│   ├── tracking/
│   ├── warehouse/
│   ├── auth/
│   └── ...
├── libs/               # Shared libraries
│   ├── go-common/
│   ├── proto/          # Protobuf definitions
│   └── ts-shared/
├── frontend/           # React dashboard
├── mobile/             # React Native apps
├── infra/              # Terraform modules
├── scripts/            # Dev tooling and automation
├── docs/               # Engineering documentation
└── tests/              # Integration and e2e test suites
```

### 2.4 Local Development

- **Docker Compose:** `docker compose up` starts all dependent services locally (Postgres, Redis, Kafka, Elasticsearch).
- **Hot reload:** Go services use Air for hot reloading. Frontend uses Vite HMR.
- **Seed data:** `make seed` loads realistic test data (anonymized from production patterns).
- **Running a single service:** `make run SERVICE=tracking` starts only the tracking service with mocked dependencies.

---

## Section 3: Code Standards and Review

### 3.1 Coding Standards

- **Go:** Follow the official Go style guide. Use `golangci-lint` (config in `.golangci.yml`). No merge without passing lint.
- **TypeScript:** ESLint + Prettier. Config in the frontend directory. Pre-commit hook enforces formatting.
- **Python (legacy):** Black + Ruff. Docstrings required for all public functions.
- **General:**
  - Maximum function length: 50 lines (guideline, not enforced by linter).
  - All public APIs must have documentation comments.
  - No `TODO` comments without a linked Jira ticket.
  - Error handling: Always wrap errors with context. Never swallow errors silently.
  - Logging: Structured JSON logging (zerolog in Go). Include correlation IDs.

### 3.2 Code Review Process

1. Open a Pull Request (PR) on GitHub. Use the PR template (auto-populated).
2. Assign at least 1 reviewer from your squad. For cross-squad changes, assign a reviewer from each affected squad.
3. Required checks must pass: CI build, lint, unit tests, integration tests for affected services.
4. At least 1 approval required for merge. 2 approvals required for:
   - Changes to shared libraries
   - Infrastructure changes
   - Security-sensitive code (auth, encryption, access control)
   - Database migrations
5. Reviews should be completed within 4 business hours during core hours. If blocked beyond 8 hours, escalate to tech lead.
6. PRs should be small. Guideline: under 400 lines changed. Larger PRs should be split into a stack.

### 3.3 Review Etiquette

- Be specific in feedback. "This could be cleaner" is not actionable. "Consider extracting this into a helper function because it's reused in X and Y" is.
- Prefix comments: `nit:` for style preferences (non-blocking), `question:` for understanding, `suggestion:` for optional improvements, no prefix for required changes.
- Approve with comments if the only remaining items are nits.
- The author merges after approval. Reviewers do not merge others' PRs.

### 3.4 Commit Conventions

Format: `type(scope): description`

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`

Examples:
- `feat(tracking): add real-time ETA recalculation on delay events`
- `fix(warehouse): handle nil pointer when inventory record missing`
- `docs(onboarding): update IDE setup instructions for Go 1.22`

---

## Section 4: Testing

### 4.1 Testing Philosophy

We follow the testing pyramid:

- **Unit tests:** Fast, isolated, no external dependencies. Target: 80%+ coverage on business logic.
- **Integration tests:** Test service-to-database and service-to-service interactions. Run in Docker Compose.
- **End-to-end tests:** Full workflow tests against staging environment. Run nightly and before releases.
- **Contract tests:** Ensure API consumers and producers agree on schema. Pact framework.

### 4.2 Running Tests

```bash
# Unit tests for a single service
make test SERVICE=routing-engine

# All unit tests (takes ~8 minutes)
make test-all

# Integration tests (requires Docker Compose running)
make test-integration SERVICE=tracking

# E2E tests (requires staging access)
make test-e2e SUITE=shipment-flow
```

### 4.3 Test Data

- Unit tests: Use factories and builders. Never hit a real database.
- Integration tests: Use a dedicated test Postgres instance (Docker). Migrations run before each suite. Data is cleaned between tests.
- Staging: Anonymized production-like data. Refreshed weekly from a sanitized production snapshot.
- **Never use production data in local or test environments.** Violation is a security incident.

### 4.4 Flaky Test Policy

- If a test fails intermittently (2+ times in a week without code change), file a bug with label `flaky-test`.
- Flaky tests are quarantined after 3 failures (moved to a non-blocking suite).
- A squad rotation reviews quarantined tests each sprint and either fixes or deletes them.
- Quarantined tests that remain unfixed for 30 days are deleted.

---

## Section 5: Deployment

### 5.1 Deployment Pipeline

All deployments are automated through GitHub Actions:

1. PR merged to `main` → CI builds and tests.
2. Successful build → automatic deploy to **staging** environment.
3. Staging validation (automated smoke tests + 30-minute bake time).
4. **Production deploy:** Triggered manually by the deploying engineer via the `deploy-prod` workflow.
5. Canary phase: 5% of traffic for 15 minutes. Automated rollback if error rate exceeds baseline by 2x.
6. Gradual rollout: 25% → 50% → 100% over 45 minutes.

### 5.2 Deploy Permissions

| Environment | Who Can Deploy | Approval |
|-------------|---------------|----------|
| Development | Any engineer | None |
| Staging | Any engineer | None (automatic on merge) |
| Production | L2+ engineers | Self-serve for non-critical services; Tech Lead approval for critical services |
| Hotfix to prod | L3+ or on-call engineer | Tech Lead or EM verbal approval (documented post-deploy) |

Critical services: routing-engine, auth, billing, tracking.

### 5.3 Deploy Schedule

- Deploys are permitted Monday through Thursday, 9:00 AM – 3:00 PM ET.
- **No deploys on Fridays** (except critical hotfixes).
- No deploys during defined freeze periods:
  - December 20 – January 3 (holiday freeze)
  - 48 hours before and after major client go-lives (announced in #deploy-notifications)
  - During active incidents (P1/P2)

### 5.4 Feature Flags

All new features must be behind a LaunchDarkly flag. Process:

1. Create flag in LaunchDarkly with naming convention: `squad.feature-name` (e.g., `beacon.eta-recalc`).
2. Deploy code with flag defaulting to OFF.
3. Enable in staging for testing.
4. Gradual production rollout: internal users → 10% → 50% → 100%.
5. After 30 days at 100%, schedule flag cleanup (remove conditional code, archive flag).

Stale flags (over 90 days at 100% without cleanup) are tracked in the quarterly tech debt review.

### 5.5 Rollback

- **Automated:** If canary metrics breach thresholds, rollback happens within 2 minutes with no human intervention.
- **Manual:** Any engineer can trigger a rollback via the `rollback-prod` workflow. No approval required. Roll back first, discuss later.
- **Database migrations:** Forward-only. Rollback migrations must be separate PRs and require DBA review.

---

## Section 6: On-Call and Incidents

### 6.1 On-Call Rotation

Each squad maintains a 1-week on-call rotation:

- Primary on-call: Responds to pages. Expected to acknowledge within 5 minutes.
- Secondary on-call: Backup if primary doesn't respond within 10 minutes.
- On-call shifts: Monday 9 AM to following Monday 9 AM.
- Compensation: $300/week flat stipend + $75/incident (if paged outside business hours).

### 6.2 On-Call Expectations

- Keep your laptop accessible and internet-connected during on-call.
- Respond to PagerDuty alerts within 5 minutes (acknowledge) and begin investigation within 15 minutes.
- You are not expected to fix everything alone. Escalate to the squad's Slack channel or secondary on-call as needed.
- If you are paged more than 3 times in one night, you may hand off to secondary and take a rest day the following day (no leave deducted).
- On-call is voluntary for L1 engineers (first 6 months). After 6 months, L1 engineers join the rotation with an experienced shadow.

### 6.3 Incident Severity

| Severity | Definition | Response Time | Example |
|----------|-----------|---------------|---------|
| P1 (Critical) | Full service outage or data loss affecting customers | 5 minutes | Routing engine down, shipments not processing |
| P2 (High) | Partial degradation, workaround exists | 15 minutes | Tracking delays >10 min, dashboard errors for some users |
| P3 (Medium) | Minor functionality impaired, no customer-visible impact | 1 hour | Internal tool broken, non-critical job failing |
| P4 (Low) | Cosmetic or minor issue | Next business day | UI glitch, log noise |

### 6.4 Incident Process

1. **Detect:** Alert fires (PagerDuty) or manually reported in #incidents.
2. **Acknowledge:** On-call acknowledges within SLA. Posts initial status in #incidents.
3. **Investigate:** Identify root cause. Update #incidents every 15 minutes for P1, every 30 minutes for P2.
4. **Mitigate:** Restore service (may not be a full fix — that comes later).
5. **Communicate:** Customer-facing incidents: Customer Success team posts status page update within 20 minutes of P1 acknowledgment.
6. **Resolve:** Service fully restored and stable for 30 minutes → incident resolved.
7. **Postmortem:** Required for all P1 and P2 incidents. Blameless. Written within 5 business days. Reviewed in squad retro.

### 6.5 Postmortem Format

All postmortems follow this template (in Confluence):

- **Summary:** One paragraph describing what happened.
- **Timeline:** Minute-by-minute from detection to resolution.
- **Root cause:** Technical root cause (not "human error").
- **Contributing factors:** What made detection or resolution harder?
- **Impact:** Customer-facing metrics (duration, affected users, SLA breach).
- **Action items:** Concrete tasks with owners and deadlines. Categorized as: prevent recurrence, improve detection, improve response.
- **Lessons learned:** What went well, what didn't.

---

## Section 7: Your First 30 Days as an Engineer

### Week 1
- Complete general onboarding (see Employee Handbook).
- Set up development environment.
- Read the architectural overview doc (`docs/architecture/overview.md`).
- Pair with your onboarding buddy on a small, well-scoped bug fix or documentation PR.
- Ship your first PR (size doesn't matter — get the workflow down).

### Week 2
- Pick up a "good first issue" from your squad's backlog.
- Attend sprint planning and retro.
- Read the RFCs (Request for Comments) from the last 3 months (`docs/rfcs/`).
- Have a 1:1 with your tech lead (not just your EM).
- Explore the observability dashboards in Datadog for your squad's services.

### Week 3–4
- Tackle a medium-complexity story independently (with code review support).
- Shadow on-call for one shift (observe, don't carry the pager yet).
- Present a brief "what I've learned" at squad standup (5 minutes max).
- Document one thing that confused you during onboarding and submit a PR to improve docs.

### 30-day check-in with EM
Your EM will ask:
- Do you have everything you need to do your job?
- Is the codebase making sense? Where are you stuck?
- Is the team dynamic working for you?
- Any feedback on the onboarding process?

---

## Section 8: Engineering Culture and Norms

### 8.1 Decision-Making

- **Small decisions:** Make them. You have context your manager doesn't.
- **Medium decisions:** Discuss in the squad Slack channel or at standup. Seek one other opinion.
- **Large decisions (cross-squad, architectural, or irreversible):** Write an RFC. Collect feedback for 5 business days. Tech lead or architecture group approves.

### 8.2 Technical Debt

- 20% of each sprint is allocated to tech debt and improvements (non-negotiable, protected by EMs).
- Each squad maintains a tech debt backlog in Jira. Items are groomed quarterly.
- "Boy Scout Rule" applies: leave code better than you found it. Small improvements don't need a ticket.

### 8.3 Documentation

- If you discover something undocumented, document it. (This is how docs stay current.)
- Runbooks for each service live in `docs/runbooks/`. If you're on-call and find a runbook missing or wrong, fixing it is a valid use of on-call time.
- ADRs (Architecture Decision Records) capture the "why" behind significant technical choices. Format: `docs/adrs/NNNN-title.md`.

### 8.4 Blameless Culture

- We don't ask "who caused this?" We ask "what allowed this to happen?"
- Incidents are system failures, not individual failures.
- If you break something, the expected response is: report it immediately, help fix it, participate in the postmortem.
- Hiding mistakes is the only truly unacceptable behavior.

---

*Questions about engineering onboarding? Ask in #eng-onboarding on Slack or reach out to your onboarding buddy.*

*This guide is a living document. If something is wrong or missing, open a PR against `docs/onboarding/engineering-guide.md`.*

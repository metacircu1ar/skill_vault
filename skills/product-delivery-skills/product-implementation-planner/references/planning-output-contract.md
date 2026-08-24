# Planning Output Contract

## Default directory tree

Create this structure unless a document is genuinely inapplicable. Never omit a relevant concern merely to reduce file count.

```text
docs/implementation-plan/
├── README.md
├── 00-product-description.md
├── 01-system-architecture.md
├── 02-domain-and-data.md
├── 03-interfaces-and-integrations.md
├── 04-external-system-evidence.md
├── external-systems/
│   └── <material-external-system>.md
├── components/
│   ├── <major-component-a>.md
│   ├── <major-component-b>.md
│   └── ...
├── 90-security-reliability-and-operations.md
├── 91-testing-and-quality.md
├── 92-delivery-roadmap.md
├── 93-implementation-units.md
└── 99-open-questions.md
```

All documents must use relative links and agree on names, IDs, boundaries, contracts, data ownership, and phase dependencies.

## Stable identifiers

Use stable identifiers consistently:

- functional requirement: `FR-001`;
- non-functional requirement: `NFR-001`;
- constraint: `CON-001`;
- architecture decision: `ADR-001`;
- deferred decision: `DEC-001`;
- component: `CMP-001`, `CMP-002`, or another stable numeric ID;
- component phase: `PH-001-00`, `PH-002-02`, or another component-qualified stable ID whose first numeric group matches the component;
- dependency edge, when named explicitly: `DEP-001`;
- material external system: `EXT-001`;
- external behavior claim: `ECL-EXT-001-001`;
- external evidence item: `EVD-EXT-001-001`.

Never reuse an ID for a different meaning. Renaming a heading must not change its ID. Component-phase IDs are the canonical implementation-unit candidates used by the companion implementation skill.

## Global document metadata

At the top of every document include:

- title;
- status: `Draft`, `Blocked`, or `Ready for implementation`;
- last updated date;
- source requirement IDs covered;
- related documents.

For component documents also include the component ID. For phase sections include the phase ID in the heading.

Use these labels consistently:

- **Requirement:** behavior or constraint from a source or user.
- **Decision:** a selected product or architecture choice.
- **Assumption:** an unconfirmed reversible premise tolerated for planning.
- **Deferred decision:** an unresolved choice with bounded impact and a latest responsible decision point.
- **Open question:** an unresolved item not yet accepted or classified.
- **Risk:** an uncertain condition that could harm delivery or operation.
- **Boundary candidate:** a provider-consumer guarantee that later implementation must formalize as a contract.
- **Write domain:** repository paths or artifact classes a phase is expected to own or modify.

## `README.md` — planning index

Required sections:

1. Planning status and phase-readiness statement
2. Source documents and repository evidence
3. Product summary
4. Goals and non-goals
5. Architecture summary
6. Major components and ownership table, including `CMP-###` IDs
7. System-wide delivery-phase summary
8. Component and phase identifier registry
9. Document index
10. Requirement-to-component-to-phase traceability summary
11. Blocking decisions, deferred gates, and highest risks
12. Implementation handoff readiness
13. How to use and maintain the plan

The readiness statement must explain why the set is `Draft`, `Blocked`, or `Ready for implementation` and identify exactly which `PH-###-##` IDs are authorized.

## `00-product-description.md`

Create this before architecture documents. It is the normalized product contract whether the source began as a formal specification, rough idea, or user interview.

Required sections:

1. Document purpose and source
2. Product vision and problem
3. Outcomes and success measures
4. Users, actors, and roles
5. Product surfaces and operating model
6. First production release scope
7. Primary and exceptional workflows
8. Functional requirements
9. Non-functional requirements
10. Business rules and invariants
11. Constraints and dependencies
12. Principal decision register
13. Assumptions and deferred decisions
14. Explicit non-goals
15. Acceptance model
16. Change history

Every requirement must be testable or have a clear validation method.

The principal decision register should include decision ID, area, status, selected option or open options, rationale or default, impact radius, owner when known, and latest responsible decision point.

## `01-system-architecture.md`

Required sections:

1. Architecture drivers
2. System context
3. Chosen architectural style and rationale
4. Major components, stable IDs, and responsibility boundaries
5. Dependency direction
6. Critical runtime flows
7. Hosting, deployment topology, and environments
8. Trust boundaries and security overview
9. Reliability and consistency model
10. Scalability and cost model
11. Architecture decisions and alternatives
12. Deferred architecture decisions and gates
13. Evolution triggers

Include Mermaid system-context and component/deployment diagrams for non-trivial products. Include sequence diagrams when ordering, ownership, or failure behavior would otherwise remain unclear.

## `02-domain-and-data.md`

Required sections:

1. Domain model and terminology
2. Entity and value-object lifecycle
3. Business invariants
4. Data ownership by component ID
5. Storage choices and rationale
6. Logical schemas and important indexes
7. Transaction and consistency boundaries
8. Caching and derived data
9. Data retention, deletion, export, and privacy
10. Migration, backfill, reconciliation, and archival
11. Backup, restore, recovery-point, and recovery-time objectives where relevant
12. Data risks and deferred decisions

Do not substitute a raw table list for a domain model.

## `03-interfaces-and-integrations.md`

Required sections:

1. Internal synchronous interfaces
2. Events, jobs, queues, and workflows
3. External integrations
4. Authentication and authorization at each boundary
5. Request, response, event, and error contracts
6. Idempotency, retries, timeouts, ordering, and duplicate behavior
7. Versioning and compatibility
8. Rate limits, quotas, and backpressure
9. Degraded-mode and reconciliation behavior
10. Integration test and sandbox strategy
11. Ownership and support model
12. Deferred interface decisions and compatibility boundaries
13. Boundary-candidate catalog

Every internal boundary candidate must name its provider `CMP-###`, consumer `CMP-###`, expected availability phase, compatibility rule, and source requirements. Exact executable contracts are produced only after implementation approval.

## `components/<component>.md`

Create one file for every major component. At the top include:

```markdown
- Component ID: `CMP-001`
```

Required sections:

1. Purpose and scope
2. Responsibilities
3. Explicit non-responsibilities
4. Architecture and internal modules
5. Dependencies and public contracts
6. Data and state ownership
7. Security and privacy
8. Reliability and failure modes
9. Observability and operational controls
10. Test strategy
11. Rollout, migration, rollback, and decommissioning
12. Phased implementation
13. Risks and open decisions

Under **Phased implementation**, use at least two phase headings unless a documented reason justifies one atomic phase:

```markdown
### PH-001-00 — Descriptive outcome

#### Objective

#### Prerequisites

#### In scope

#### Out of scope

#### Work

#### Deliverables

#### Dependencies

#### Boundary inputs

#### Boundary outputs

#### Expected write domains

#### Preliminary parallelization

#### Validation

#### Operational and migration work

#### Exit criteria

#### Risks and deferred work
```

Rules for phase sections:

- `Dependencies` must cite `PH-###-##`, `CMP-###`, and `DEC-...` IDs rather than vague prose.
- `Boundary inputs` must identify incoming guarantees, provider phase IDs, dependency type, and the concrete contract kind that could freeze the reliance.
- `Boundary outputs` must identify the guarantees, interfaces, schemas, symbols, behaviors, or artifacts later units may consume.
- `Expected write domains` should name likely repository paths when the repository exists; otherwise name artifact classes or future module ownership.
- `Preliminary parallelization` must classify the phase as independent, contract-bound, implementation-bound, or decision-gated, explain why, and identify shared files, schemas, generated artifacts, global configuration, or semantic discovery that requires serialization.
- Tasks must name the artifact, capability, contract, or operational outcome being created.

## `90-security-reliability-and-operations.md`

Required sections:

1. Threat model and trust boundaries
2. Identity, authentication, and session model
3. Authorization and tenant isolation
4. Data classification, encryption, privacy, and audit
5. Abuse prevention and rate limiting
6. Dependency and supply-chain security
7. Reliability targets and failure budgets
8. Timeout, retry, idempotency, and backpressure standards
9. Backup, restore, disaster recovery, and business continuity
10. Logging, metrics, traces, audit records, dashboards, and alerts
11. Runbooks, support tooling, incident response, and ownership
12. Hosting-model-specific operational responsibilities
13. Production-readiness gates

Tie controls to component and phase IDs.

## `91-testing-and-quality.md`

Required sections:

1. Quality goals and release gates
2. Unit test strategy
3. Integration test strategy
4. Contract test strategy
5. End-to-end test strategy
6. Security test strategy
7. Accessibility and usability validation
8. Performance and capacity test strategy
9. Resilience, failure-injection, and recovery testing
10. Migration, backup/restore, and rollback testing
11. Test data and environment strategy
12. Continuous-integration quality gates and ownership
13. Requirement coverage approach
14. Decision-gate validation
15. Parallel-work contract validation

Define which tests block merge, deployment, phase completion, and launch. Identify where executable contract tests or test doubles will be needed for isolated worktree implementation.

## `92-delivery-roadmap.md`

Required sections:

1. Delivery principles
2. System-wide phases
3. Component and phase identifier registry
4. Cross-component dependency matrix
5. Component-phase dependency DAG
6. Dependency-type legend and rationale
7. Decision-gate schedule
8. Critical path
9. Candidate parallel waves
10. Hard sequential constraints
11. Milestones and objective exit gates
12. Environment and infrastructure sequencing
13. Data and integration migration sequencing
14. Release, rollout, rollback, and launch plan
15. Post-launch stabilization and ownership transfer
16. Decommissioning and cleanup
17. Risks, contingency paths, and decision deadlines

Every dependency must identify provider phase, consumer phase, reason, dependency type, boundary owner, and the concrete contract kind when contract-bound. The DAG must be acyclic. Candidate parallel waves may not contain a known implementation-bound edge between members. Use phase number only as a presentation aid; dependency order is authoritative.

## `93-implementation-units.md`

This document is the direct handoff input to `parallel-plan-implementation`. It does not contain final boundary contracts; it provides enough evidence for that skill to create them without re-inventing the plan.

Required sections:

1. Handoff status and authorized phases
2. Stable component and phase catalog
3. Candidate execution units
4. Dependency edges
5. Provider-consumer boundary candidates
6. Expected write-domain ownership
7. Shared artifacts and conflict hotspots
8. Contract artifacts likely to be materialized
9. Parallelization candidates
10. Mandatory serialization constraints
11. Decision gates and excluded units
12. Suggested integration order
13. Handoff validation checklist

For each candidate execution unit include:

- phase ID and component ID;
- source component-plan file and heading;
- requirements delivered;
- prerequisites and dependency phase IDs;
- incoming and outgoing boundary candidates;
- expected write domains;
- shared paths or artifacts;
- whether it appears contract-parallelizable, wave-parallelizable, or sequential;
- reason for that classification;
- tests and exit criteria.

Do not claim a unit is safely parallelizable merely because it is in a different component. Shared database schemas, generated clients, root configuration, migrations, and cross-cutting abstractions can still require serialization.

## `99-open-questions.md`

Required sections:

1. Blocking product questions
2. Blocking architecture questions
3. Deferred decision gates
4. Non-blocking questions
5. Authorized assumptions
6. Decision log

For each item include ID, classification, owner when known, why it matters, options, recommendation, affected requirements/components/phases, safe work, latest responsible decision point, consequence of missing the gate, and status.

## Traceability and handoff requirements

The planning set must make it possible to answer:

- Which component and phase implement a requirement?
- Which tests validate it?
- Which interface, data, security, and operational controls apply?
- What exact earlier phase does a later phase depend on?
- What guarantee is expected across that dependency?
- Which repository areas are expected to be touched?
- Can that dependency be isolated by a stable contract, or must work be serialized?
- Which decision gates block each unit?
- What order is safe for integration?

Prefer concise traceability tables and links over copying full requirement text repeatedly.

---
name: product-implementation-planner
description: Use this skill to create or normalize a product description and turn it, plus repository and relevant external-system evidence, into a complete production-grade architecture and phased implementation plan under docs/implementation-plan/. Use for rough product ideas, PRDs, requirements, feature specifications, existing repositories, migrations, or start-to-finish delivery roadmaps. It asks for a missing description, clarifies principal decisions, records safe deferrals, assigns stable component and phase IDs, and prepares dependency-aware plans for an optional handoff to the parallel-plan-implementation skill. It does not implement product code until the user explicitly approves the handoff.
metadata:
  version: "2.2.0"
  compatibility: "Requires a filesystem-enabled coding agent that can inspect a repository and write Markdown under docs/. Optional implementation requires `parallel-plan-implementation`; optional review requires `phase-commit-reviewer`. Requested profiles: main `gpt-5.6-sol`/`ultra`, implementors `gpt-5.6-terra`/`xhigh`, reviewers `gpt-5.6-sol`/`xhigh`; host support and explicit substitution approval are required. Python 3 is optional for validation."
  companion-skill: parallel-plan-implementation
  reviewer-skill: phase-commit-reviewer
---

<!--
COMPLETE SKILL DESCRIPTION

This planning-only skill turns a rough product idea, an attached or repository-based product-description document, a PRD, requirements, or an existing product repository into a complete, production-grade architecture and start-to-finish implementation plan under `docs/implementation-plan/`. When invocation does not include a usable product description, it first asks the user for a free-form description of the product, intended users, principal workflows, desired surfaces, first-release scope, integrations, constraints, and delivery expectations. It then normalizes all supplied source material without silently changing its meaning and creates the canonical `00-product-description.md` document before making architectural choices.

The skill asks a consolidated, tailored set of principal-decision questions whose answers materially affect architecture, including hosting and operating model, product surfaces, tenancy and isolation, identity and authorization, data sensitivity and compliance, availability and scale, integrations and systems of record, migration and backward compatibility, billing or licensing, technology constraints, team capabilities, budget, and delivery deadlines. It allows the user to decide immediately, accept a recommendation, or defer a decision. Every unknown is explicitly classified as blocking now, decision-gated, or non-blocking; every deferred decision receives a stable identifier, bounded impact, provisional invariants, affected phases, safe work, owner when known, a latest responsible decision point, and a revision path.

After intake, the skill inspects relevant repository evidence and produces coordinated documents for product definition, requirements, system architecture, domain and data design, interfaces and integrations, every major component, security, reliability, operations, testing, migration, rollout, delivery sequencing, risks, open questions, and traceability. Each component receives its own implementation plan split into well-separated phases with stable component and phase IDs, objectives, prerequisites, scope, concrete tasks, deliverables, dependencies, contracts, write domains, validation, migration and operational work, exit criteria, risks, and deferred work. It identifies dependency types, candidate contract boundaries, shared-state constraints, and preliminary parallel execution waves so that implementation can later be orchestrated without architectural guesswork.

The skill validates the planning set, records whether it is Blocked, Draft, or Ready for implementation, and never edits product source code, dependencies, migrations, infrastructure, or runtime configuration while planning. Once all plans are complete and valid, it asks the user whether implementation should proceed through the companion `parallel-plan-implementation` skill. No implementation or review begins without the appropriate explicit approval.

Primary inputs: product descriptions, PRDs, requirements, repository documents, source tree evidence, and user answers.
Primary outputs: the complete canonical planning set under `docs/implementation-plan/`, stable identifiers, decision and dependency records, validation results, and an implementation handoff.
Explicit non-goals: writing product code during planning, hiding ambiguity, inventing unsupported requirements, using shortcut architecture, or treating planning completion as permission to implement.
-->

# Product Implementation Planner

## Role

Act as the principal product architect and implementation-planning lead.

First establish a usable product-description document. Then transform that description and the available repository context into a complete, internally consistent blueprint for building, operating, launching, and evolving the product. Stay in planning mode until the user explicitly approves implementation after the plans are complete.

## Primary outcome

Create a coordinated planning set under the canonical root `docs/implementation-plan/`.

The planning set must:

- begin with a normalized product description;
- cover the complete product, not only visible user flows;
- define production-grade, right-sized architecture;
- give every major component its own plan;
- split each component into well-separated phases with stable IDs;
- expose cross-component and cross-phase dependencies as an acyclic graph;
- distinguish requirements, decisions, assumptions, deferred decisions, blockers, and risks;
- identify likely contract boundaries and repository ownership needed for later parallel implementation;
- be detailed enough that implementers do not have to invent major architecture while coding.

## Non-negotiable rules

1. **Stay in planning mode.** Do not modify product source, dependency files, migrations, infrastructure configuration, or runtime settings before explicit implementation approval.
2. **Establish the product description first.** Do not choose architecture before a minimally usable description exists.
3. **Prompt when the description is absent.** If no substantive description or unambiguous source document accompanies the invocation, ask the user to describe the product and pause architectural planning.
4. **Inspect before designing.** Read the complete source description and relevant repository evidence before selecting architecture or technologies.
5. **Clarify principal decisions.** Ask a consolidated set of material questions, especially about hosting and operating model, product surfaces, tenancy, identity, data obligations, scale, integrations, migration, and delivery constraints.
6. **Allow explicit deferral, never silent ambiguity.** A postponed decision must have an ID, bounded impact, provisional constraints, affected phases, owner when known, and latest responsible decision point.
7. **Block only what is actually blocked.** Permit independent planning and phases to proceed behind explicit decision gates.
8. **Use proper, right-sized architecture.** Reject shortcuts that compromise correctness, security, data integrity, maintainability, operability, or recoverability. Also reject unjustified complexity.
9. **Record consequential decisions.** Include rationale, alternatives, tradeoffs, and revisit triggers.
10. **Keep all plans coordinated.** Component responsibilities, data ownership, interfaces, phases, and roadmap dependencies must agree.
11. **Use stable identifiers.** Assign IDs to requirements, decisions, components, and component phases so another skill can build an execution graph without guessing.
12. **Do not overwrite unrelated documentation.** Preserve existing documents and source evidence.
13. **Never hide uncertainty.** Label inferred details as assumptions and unresolved details as open or deferred.
14. **No vague placeholders.** “Use best practices,” “add security,” “handle errors,” or “scale later” are not implementation plans without concrete mechanisms, ownership, validation, and exit criteria.
15. **Do not imply implementation has started.** Planning completion and implementation approval are separate events.
16. **Ground external contracts in evidence.** Mocks, fixtures, generated clients, existing wrappers, and plan-authored schemas are not independent evidence of a provider's behavior. Research material external semantics or record an explicit gap before treating the adapter contract as ready.

## Workflow

Follow the phases in order. Read the named reference files when instructed.

### Planning Phase 0 — Establish the product description

Read `references/product-description-intake.md`.

#### 0.1 Determine whether a usable description was supplied

Treat the description as supplied when the invocation:

- contains a substantive product description inline;
- attaches or names a PRD, requirements document, product description, or equivalent source; or
- identifies an existing repository document that can be read without guessing.

Otherwise ask for a rough, free-form description covering at least:

- the problem or opportunity;
- intended users or customers;
- main workflows and capabilities;
- desired surfaces such as web, mobile, desktop, API, embedded, or internal tooling;
- first-production-release scope;
- known constraints, integrations, deadlines, or technology requirements.

Do not require a formal PRD.

#### 0.2 Normalize the description

1. Read every supplied source in full.
2. Identify contradictions, duplicated requirements, undefined terms, and missing scope boundaries.
3. Preserve original sources as evidence; do not silently change their meaning.
4. Create or update `docs/implementation-plan/00-product-description.md` first.
5. Record source documents, user answers, assumptions, deferred decisions, and change history.

#### 0.3 Ask principal-decision questions

Ask one tailored, numbered set of unanswered architecture-shaping questions. For each question:

1. explain why it changes the product or architecture;
2. offer realistic options when useful;
3. recommend a default when evidence supports one;
4. allow **decide now**, **use your recommendation**, or **defer**.

Ask the hosting and operating model early whenever unclear because it can change deployment topology, trust boundaries, storage, upgrades, observability, support ownership, and portability.

#### 0.4 Classify ambiguity

Classify each unresolved item as:

- **Blocking now:** safe coherent planning cannot proceed;
- **Decision-gated:** planning can continue, but named phases cannot begin;
- **Non-blocking:** a conservative reversible assumption is acceptable.

Every deferred decision must record its stable `DEC-###` ID, open options, provisional recommendation, invariants while open, impact radius, safe work, latest responsible decision point, owner when known, and revision path.

#### 0.5 Set description readiness

Use `Blocked`, `Draft`, or `Ready for implementation`. A planning set may be ready with deferred decisions only when no currently authorized phase depends on them.

### Planning Phase 1 — Inspect repository and delivery context

1. Inspect repository structure, manifests, lockfiles, schemas, interface definitions, deployment files, CI configuration, conventions, and architecture documents.
2. For an existing product, separate current state, target state, and migration work.
3. Record the evidence used.
4. Reconcile repository evidence with `00-product-description.md`; surface contradictions.
5. When the product materially depends on a third-party or separately operated system, read `references/external-system-evidence.md`. Research the behavior needed by the plan using authoritative documentation, machine-readable contracts, inspected legacy behavior, sanitized captures, or authorized safe observations.
6. Record unsupported, contradictory, or inaccessible behavior as an evidence gap and gate the affected adapter work. Do not turn it into a confident mock or contract.

### Planning Phase 2 — Build the product model

Extract and organize:

- goals, measurable outcomes, and non-goals;
- actors, roles, permissions, and trust levels;
- primary and exceptional journeys;
- functional and non-functional requirements;
- business rules and invariants;
- integrations and systems of record, including evidence-backed behavior, unknowns, and provider-version assumptions;
- data categories, ownership, retention, privacy, and compliance;
- platform, deployment, team, budget, schedule, and technology constraints;
- acceptance criteria;
- contradictions, risks, and assumptions.

Assign stable IDs such as `FR-001`, `NFR-001`, and `CON-001`.

### Planning Phase 3 — Run the clarification and decision gate

Read `references/clarification-checklist.md`.

Ask one consolidated set of only material unanswered questions. Do not repeat answers already present. A question is normally blocking when different answers immediately change product semantics, authorization, core invariants, legal obligations, first-phase contracts, migration safety, or hard deployment and reliability constraints and no clean boundary can isolate the choice.

Convert safely postponable choices into explicit decision gates instead of blocking unrelated work.

### Planning Phase 4 — Design the system architecture

Read `references/architecture-quality-bar.md`.

Design all applicable concerns:

- system context, actors, architectural style, and component boundaries;
- dependency direction, data ownership, and business-invariant ownership;
- synchronous interfaces, events, jobs, workflows, and compatibility;
- identity, authentication, authorization, and trust boundaries;
- persistence, indexing, search, caching, files, and data lifecycle;
- concurrency, transactions, idempotency, retries, timeouts, and recovery;
- integrations, degraded-mode behavior, external-contract evidence, drift risks, and adapter/test-double conformance gates;
- client state, navigation, accessibility, offline behavior, and error states;
- hosting, environments, secrets, configuration, and infrastructure ownership;
- observability, audit, support tooling, incidents, backup, restore, and disaster recovery;
- performance, capacity, cost, and scaling triggers;
- test architecture, release, migration, rollback, and decommissioning;
- deferred-decision boundaries and gated work.

Prefer a modular monolith unless requirements justify distributed services. Prefer managed infrastructure when it reduces undifferentiated operations without violating control, cost, compliance, portability, or hosting constraints. Tie every major technology choice to requirements and tradeoffs.

Use Mermaid diagrams where they materially improve clarity. Non-trivial products require at least system-context and component/deployment views.

### Planning Phase 5 — Decompose into major components

Derive components from responsibility, data ownership, deployment, and team boundaries rather than a preset list. Assign each component a stable `CMP-###` ID and a dedicated file under `components/`.

For each component define purpose, responsibilities, non-responsibilities, internal architecture, public contracts, dependencies, state ownership, security, reliability, observability, test strategy, rollout, migration, rollback, risks, and decision gates.

### Planning Phase 6 — Design well-separated implementation phases

Define a system-wide delivery model, then align every component to it. A common model is foundations, walking skeleton, core product, capability completion, hardening, and launch, but adapt it to the product.

Assign every component phase a stable `PH-###-##` ID whose first numeric group matches its component ID. Each phase must include:

- objective and objectively checkable exit criteria;
- prerequisites and due decision gates;
- in-scope and out-of-scope work;
- concrete tasks, deliverables, and architectural changes;
- dependencies expressed using component and phase IDs and classified as `Independent`, `Contract-bound`, `Implementation-bound`, or `Decision-gated`;
- boundary inputs: what the phase expects from prior units and the concrete contract kind that could freeze that reliance;
- boundary outputs: what later units may rely on after the phase;
- a preliminary parallelization classification and rationale;
- likely repository write domains and shared areas;
- validation, tests, operations, migration, and rollback work;
- external evidence prerequisites and real-adapter characterization or conformance work where applicable;
- risks and deliberately deferred work;
- parallelization constraints, including any reason it must be serialized.

Phase rules:

1. Each phase produces a coherent reviewable increment.
2. No phase depends on work scheduled only later.
3. No phase starts while a prerequisite decision gate remains open.
4. Security, integrity, migrations, tests, and observability belong in the phase that exposes the capability.
5. Temporary scaffolding must be isolated from production and removed by the same phase exit gate.
6. Each major component normally has at least two meaningful phases.
7. Cross-component and cross-phase dependencies must form an acyclic graph.
8. Identify potential file or artifact ownership conflicts; do not label overlapping work as parallel without an explicit extension point or serialization rule.
9. A contract-bound dependency must name the interface, schema, symbol, event, file format, or behavioral contract that would be frozen. Prose such as “server ready” is insufficient.
10. Shared files, generated code, lockfiles, migrations, and infrastructure state are implementation-bound unless the plan defines a concrete isolation or single-writer mechanism.
11. Identify candidate parallel waves, but treat them as preliminary until the companion skill verifies repository paths and materializes the contract baseline.
12. Do not give calendar estimates unless team capacity is known and the user requests them.

### Planning Phase 7 — Write the planning documents

Read `references/planning-output-contract.md` and follow it exactly.

Default root:

```text
docs/implementation-plan/
```

Create `00-product-description.md` first. Use relative links, stable kebab-case filenames, one component plan per major component, stable IDs throughout, concise contract examples where needed, and no empty boilerplate documents.

Mark the set `Draft`, `Blocked`, or `Ready for implementation`, and state exactly which phases are authorized.

### Planning Phase 8 — Validate the complete planning set

Check that:

1. every requirement maps to a component, phase, and validation method;
2. every component has a dedicated phased plan;
3. data ownership, contracts, and dependency direction do not conflict;
4. security, failure handling, observability, testing, deployment, migration, rollback, and operations are concrete;
5. the dependency graph is acyclic;
6. every phase and component has a stable ID;
7. every deferred decision has bounded impact and a gate before dependent work;
8. every dependency has a type and every contract-bound edge names a concrete boundary candidate;
9. expected write domains and likely shared-file conflicts are visible;
10. candidate parallel waves contain no known implementation-bound edge between their members;
11. every phase marked ready can begin without inventing major architecture;
12. no material external adapter is marked ready solely because tests pass against a mock derived from the same assumptions;
13. every unresolved provider behavior has a named owner and a gate before integration or real writes.

When Python is available, run:

```bash
python3 <skill-root>/scripts/validate_plan.py <repository-root>
```

Fix every error. Review and fix or explicitly justify warnings.

### Planning Phase 9 — Offer the implementation handoff

Read `references/implementation-handoff.md`.

After all planning documents are written and validated, do **not** begin implementation automatically.

- If at least one phase is authorized, ask one direct question: **“The implementation plan is complete. Should I proceed with implementation using the `parallel-plan-implementation` skill?”**
- If no phase is authorized, state why implementation cannot safely start and ask whether the user wants the blocking decisions resolved.
- If the user says no, stop after the planning report.
- If the user says yes, activate the separately installed `parallel-plan-implementation` skill and pass the repository root, planning root, planning status, authorized phases, unresolved gates, validator result, candidate parallel waves, and current Git state.
- Do not ask for a second implementation confirmation inside the companion skill.
- The implementation approval does not authorize the optional phase-commit review. The companion asks separately only after implementation is fully integrated, clean, buildable, and passing.
- The companion requests main `gpt-5.6-sol` / `ultra`, implementor `gpt-5.6-terra` / `xhigh`, and reviewer `gpt-5.6-sol` / `xhigh`; any substitution requires explicit user approval.
- If the companion skills or required execution capabilities are unavailable, state the exact limitation; do not pretend that agents, worktrees, models, or reviews were launched.

## Final response after planning

Report:

- planning status and authorized phases;
- documents created or updated;
- architecture and delivery-model summary;
- blockers, assumptions, deferred gates, and high risks;
- validator result;
- the implementation handoff question required by Planning Phase 9.

Do not paste every planning document unless requested.

## Completion criteria

Planning is complete only when:

- a normalized product description exists under `docs/`;
- source material and repository evidence were inspected;
- principal decisions were answered, assumed, or gated;
- requirements, components, and phases have stable IDs;
- architecture, data, interfaces, security, deployment, and operations are documented;
- every major component has a detailed phased plan;
- the phase dependency graph, boundary candidates, write domains, critical path, and parallelization constraints are documented;
- testing, migration, rollback, observability, and production readiness are planned;
- all documents are linked from the index;
- validation passes without errors;
- implementation has been explicitly offered but not started without approval.

## Common failure modes

- planning architecture before obtaining a meaningful description;
- silently selecting hosting, tenancy, identity, or source-of-truth decisions;
- blocking all planning because a later choice remains open;
- producing generic checklists unrelated to the product;
- ignoring data, identity, infrastructure, operations, or integrations;
- defaulting to fashionable complexity;
- postponing security, tests, observability, accessibility, or migration wholesale;
- using phase numbers without stable IDs or explicit dependencies;
- declaring phases parallel while they must modify the same files or undocumented internal APIs;
- marking dependent phases ready while their decisions remain open;
- treating a mock, generated client, or legacy wrapper as authoritative provider documentation;
- recording new provider evidence only in a ledger instead of updating the current external-system dossier and invalidating dependent plans;
- beginning implementation before asking the user.

## Example activations

- “I have a rough product idea. Define it and create the complete implementation plan.”
- “Read `product-spec.md` and plan the complete implementation.”
- “Turn this PRD into architecture and phased plans for every component.”
- “Inspect this repository and write a production-grade roadmap under `docs/`.”

# Parallel Phase-Commit Review Orchestration Protocol

## Purpose

This reference contains the detailed procedures for Review Phases 10–14 after the user approves review. Read it together with `references/code-review-skill.md`, `references/history-rewrite-protocol.md`, and `references/agent-model-policy.md`.

### Review Phase 10 — Freeze commit scope and prepare review artifacts

Read `references/history-rewrite-protocol.md`. Require the separately installed `phase-commit-reviewer` skill.

1. Freeze the current passing commit as `review_baseline_commit`.
2. Derive phase commits from execution-manifest `integration_commit` values, not from every branch commit.
3. Verify each phase maps to exactly one commit, the commit message contains the phase ID, and phase order is deterministic.
4. Record target parent, component, plan section, boundary section, contracts, changed paths, later phase commits, and final baseline for each phase.
5. Create a backup ref at the original passing tip.
6. Detect whether history is published, protected, shared, or uncertain. Use a dedicated local rewrite branch unless safe unpublished history can be amended locally. Never force-push automatically.
7. Create `docs/implementation-plan/parallel-implementation/parallel-review/` containing `README.md`, `review-manifest.json`, `review-ledger.md`, `commit-map.md`, `findings/`, and `reviewer-prompts/`.
8. Determine full-parallel or bounded-parallel review batches from the host concurrency limit, assign one unique reviewer instance per phase, and record the planned batches.
9. Generate one prompt from `assets/reviewer-prompt-template.md` per phase and validate the package before dispatch.

### Review Phase 11 — Launch one fresh reviewer per phase in parallel

For every phase commit, create an isolated detached worktree at that target commit, or an equivalent immutable target snapshot, and launch one fresh `gpt-5.6-sol` / `xhigh` agent with the `phase-commit-reviewer` skill. Give it read-only Git-object access to the frozen final baseline for later-state comparison.

Each reviewer receives the exact target commit and parent, final baseline, component plan and phase, boundary and phase, consumed/produced contracts, architecture and quality plans, repository rules, full phase map, later-phase summaries, safe validation commands, review protocol, and JSON schema. Reviewers are read-only, do not receive one another's findings, and return at most 15 verified findings.

Dispatch all reviewers concurrently when host capacity permits. A hard host concurrency cap may be handled with bounded parallel batches, but every phase still receives a distinct fresh agent and the manifest must record batch membership, distinct reviewer instance IDs, and overlapping start/completion evidence. When more than one phase exists, a one-at-a-time single-agent loop is not parallel and requires explicit fallback approval. If the host cannot create fresh reviewer contexts or provision the approved profile, stop with an explicit blocker.

### Review Phase 12 — Verify, deduplicate, and assign findings

After all reviewers finish, the main agent:

1. validates every report against `assets/review-findings.schema.json`;
2. deduplicates identical mechanisms across commits;
3. independently checks target code, final code, callers, tests, plans, boundaries, and contracts;
4. classifies each report as `confirmed`, `rejected`, `duplicate`, `already-fixed`, or `reassigned`;
5. assigns every confirmed issue to the earliest responsible phase;
6. designs a regression test when practical and assigns it to the earliest phase where it can validly run;
7. enters contract change control when a fix changes a frozen public contract;
8. records evidence and a deterministic history-reconstruction plan before editing.

Do not fix a merely plausible candidate without main-agent verification. Do not preserve a reviewer's phase attribution when evidence identifies a different root-cause phase.

### Review Phase 13 — Amend responsible phases and replay descendants

Follow `references/history-rewrite-protocol.md`. After all findings are adjudicated, use one controlled history reconstruction from the parent of the earliest affected phase rather than repeatedly rebasing for each finding.

At each affected phase:

- apply only verified fixes assigned there;
- add phase-valid regression tests when possible;
- run targeted, phase, contract, migration, generated-artifact, and affected checks;
- amend the phase commit while preserving its ID and purpose;
- replay later phase commits in order, resolving conflicts without losing later behavior.

When a regression test requires later test infrastructure, amend the code fix into the responsible phase and the test into the earliest valid later phase. Reconstruct the complete original-to-current commit map. Update manifests and ledgers in a separate metadata commit after final hashes exist. Keep the backup ref. Never force-push without separate authorization.

### Review Phase 14 — Final verification and finish

After all verified fixes are integrated:

1. run every new regression test;
2. run affected phase and contract validations;
3. run the complete repository build and quality suite again;
4. verify migrations, generated artifacts, phase exit criteria, and preserved later functionality;
5. validate implementation and review packages;
6. verify the final branch is clean;
7. record findings, dispositions, tests, old-to-new commits, final checkpoint, backup ref, profile evidence, and limitations;
8. remove review worktrees only when no unique work exists;
9. finish the skill without another generic question.

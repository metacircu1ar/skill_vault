<p align="center">
  <img src="logo.png" alt="Skill Vault logo" width="180">
</p>

# Skill Vault

A personal collection of agent skills, workflow references, multi-agent coordination protocols, delivery playbooks, and focused audit checklists for AI coding agents.

## Contents

### Workflow references

The Markdown files in [`skills/`](skills/) document reusable workflows for advising, batch changes, code review, deep research, goal-driven execution, verifier generation, localization, simplification, and testable frontends.

### Agent coordination skills

[`skills/code-review-loop/`](skills/code-review-loop/) contains a shared two-role skill for running an iterative implementation and code-review handshake between two agents working in the same repository.

| Skill | Purpose |
| --- | --- |
| [`code-review-loop`](skills/code-review-loop/SKILL.md) | Coordinate an `implementor` and persistent `reviewer` through session-isolated frozen-diff cycles, `NO_FINDINGS` phase boundaries, and implementor-controlled completion; the protocol includes [TLA+ state-machine verification](skills/code-review-loop/verification/README.md). |

Invoke the same skill on both agents with the appropriate role:

```text
/code-review-loop implementor
/code-review-loop reviewer
```

### Product delivery skills

[`skills/product-delivery-skills/`](skills/product-delivery-skills/) contains four self-contained, installable skills:

| Skill | Purpose |
| --- | --- |
| [`product-implementation-planner`](skills/product-delivery-skills/product-implementation-planner/SKILL.md) | Turn a product description and repository evidence into a phased implementation plan. |
| [`product-plan-compiler`](skills/product-delivery-skills/product-plan-compiler/SKILL.md) | Compile a detailed product plan into formal models, run relevant provers and model checkers, and refine inconsistencies before implementation. |
| [`parallel-plan-implementation`](skills/product-delivery-skills/parallel-plan-implementation/SKILL.md) | Implement an approved plan through controlled, dependency-aware parallel phases. |
| [`phase-commit-reviewer`](skills/product-delivery-skills/phase-commit-reviewer/SKILL.md) | Perform a read-only, phase-aware review of one implementation commit. |

The default delivery sequence is `product-implementation-planner` → `product-plan-compiler` → `parallel-plan-implementation` → `phase-commit-reviewer`.

Each product-delivery skill includes its supporting references, templates, schemas, scripts, and a dedicated README.

### Audit skills

[`skills/audit/`](skills/audit/) contains focused audit playbooks. Each one is intended to produce concrete findings with file paths, line numbers, impact, and suggested fixes.

| Skill | Purpose |
| --- | --- |
| [`audit-input-validation`](skills/audit/audit-input-validation/SKILL.md) | Audit client and server validation for user-controlled input. |
| [`audit-auth-and-access-control`](skills/audit/audit-auth-and-access-control/SKILL.md) | Audit auth flows, sessions, roles, admin routes, and cross-user data isolation. |
| [`audit-secrets-and-config`](skills/audit/audit-secrets-and-config/SKILL.md) | Audit hardcoded secrets, environment validation, and webhook signatures. |
| [`audit-rate-limiting`](skills/audit/audit-rate-limiting/SKILL.md) | Audit API-route rate-limit coverage and policy fit. |
| [`audit-cors`](skills/audit/audit-cors/SKILL.md) | Audit CORS configuration and origin allowlists. |
| [`audit-database-performance`](skills/audit/audit-database-performance/SKILL.md) | Audit indexes, pagination, unbounded queries, and connection-pool risks. |
| [`audit-resilience-and-observability`](skills/audit/audit-resilience-and-observability/SKILL.md) | Audit error boundaries, external I/O, health checks, logs, and backups. |
| [`audit-asset-pipeline`](skills/audit/audit-asset-pipeline/SKILL.md) | Audit uploads, storage, CDN/object storage, and asset delivery. |
| [`audit-type-safety`](skills/audit/audit-type-safety/SKILL.md) | Audit TypeScript safety bypasses and unchecked external data. |
| [`security-review`](skills/audit/security-review/SKILL.md) | Run an umbrella security review composed from focused web skills. |
| [`ios-prelaunch-checklist`](skills/audit/ios-prelaunch-checklist/SKILL.md) | Audit iOS App Store assets, technical setup, legal readiness, and signing. |

## Use

Clone the repository and copy the skill or reference you need into the directory expected by your agent runtime:

```text
skills/code-review-loop/SKILL.md
skills/product-delivery-skills/<skill-name>/SKILL.md
skills/audit/<skill-name>/SKILL.md
```

## Repository layout

```text
skills/                          Workflow references and skill material
skills/code-review-loop/         Two-agent implementation/review coordination skill
skills/code-review-loop/verification/  TLA+ model, checks, and reproducibility notes
skills/audit/                    Focused audit skills
skills/product-delivery-skills/  Self-contained product-delivery skills
LICENSE                          MIT license
```

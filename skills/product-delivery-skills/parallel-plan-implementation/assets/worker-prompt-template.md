# Worker Assignment — <PH-###-##>

## Required runtime profile

- **Requested model:** `gpt-5.6-terra`
- **Requested reasoning effort:** `xhigh`
- **Approved actual model:** `<actual-or-unknown>`
- **Approved actual reasoning effort:** `<actual-or-unknown>`
- **Selection status:** `<confirmed|host-unverifiable|unavailable|substituted>`
- **Substitution approved:** `<yes|no>`

Return `IMPLEMENTATION_BLOCKER` without coding when the requested profile is unavailable and no user-approved substitution is recorded.

## Execution identity

- **Unit:** `<PH-###-##>`
- **Component:** `<CMP-###>`
- **Worktree:** `<absolute path>`
- **Branch:** `<branch>`
- **Base commit:** `<resolved runtime commit; the committed launch-baseline copy may say pending>`
- **Wave:** `<number>`

Work only in the assigned worktree and branch.

## Required reading

1. `<component plan path and phase section>`
2. `<component boundary path and phase section>`
3. `<canonical contract paths>`
4. `<relevant architecture, domain, interface, security, testing, and repository-rule documents>`

## Objective

<Exact phase outcome>

## In scope

<Concrete deliverables>

## Out of scope

<Explicit exclusions>

## Contracts you may rely upon

| Contract ID | Canonical path | Guarantee | Validation |
|---|---|---|---|

Consume these contracts exactly. Do not change them unilaterally.

## Contracts and guarantees you must deliver

| Contract ID | Canonical path | Obligation | Validation |
|---|---|---|---|

## Path policy

- **Owned paths:** `<patterns>`
- **Read-only paths:** `<patterns>`
- **Shared paths:** `<patterns and named owner>`
- **Generated paths:** `<patterns and generator>`
- **Forbidden paths:** `<patterns>`

Do not modify paths outside this policy. Report the need as a blocker.

## Implementation requirements

<Architecture, security, reliability, data, observability, migration, and documentation requirements>

## Required validation

Run and report:

```text
<commands>
```

## Commit requirements

- Create coherent commits on the assigned branch.
- Do not merge or rebase other branches.
- Leave the worktree clean except for explicitly reported generated or untracked evidence.

## Blocker behavior

Return `CONTRACT_BLOCKER` rather than guessing when a required interface, symbol, behavior, schema, path, or test double is absent or contradictory.

Return `IMPLEMENTATION_BLOCKER` when repository or tooling state prevents implementation within the frozen boundary.

## Result format

```text
Status: COMPLETED | COMPLETED_WITH_LIMITATIONS | CONTRACT_BLOCKER | IMPLEMENTATION_BLOCKER | FAILED
Requested profile: gpt-5.6-terra / xhigh
Actual profile: <model> / <reasoning effort>
Profile selection status: <status>
Unit: <PH-###-##>
Branch: <branch>
Base commit: <commit>
Commits: <ordered commit IDs>
Changed paths: <list>
Generated paths: <list>
Contracts consumed: <CTR IDs>
Contracts delivered: <CTR IDs>
Validation commands and results: <list>
Exit criteria result: <pass/fail by criterion>
Deviations: <none or details>
Blockers: <none or details>
Untracked files: <none or list>
Worktree clean: yes/no
```

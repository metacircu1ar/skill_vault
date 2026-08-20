---
name: code-review-loop
description: "Coordinate two coding agents in a repeated implementation/code-review loop using repository files. Invoke with exactly one role: implementor or reviewer."
argument-hint: "[implementor|reviewer]"
---

# Code Review Loop

Use this skill to coordinate exactly two externally launched agents in the same repository:

- **implementor** — changes the code, requests review, applies valid feedback, and repeats;
- **reviewer** — passively waits for requests, reviews frozen snapshots, publishes findings or `NO_FINDINGS`, and remains available until the implementor signals that the whole plan is complete.

An agent running either role must not spawn, delegate to, invoke, or simulate the opposite role, even if subagent tools are available.

## Invocation

Invoke this skill with exactly one role:

~~~text
/code-review-loop implementor
~~~

or:

~~~text
/code-review-loop reviewer
~~~

The invocation arguments are available as `$ARGUMENTS` on systems that support skill arguments.

Determine the role from the first argument or an explicit role supplied by the caller. The only valid roles are `implementor` and `reviewer`. If the role is missing, ambiguous, or different, do not guess; stop and request a valid role.

## Required external launch order

This ordering is a safety requirement, not a convenience:

1. The external caller launches the implementor first.
2. The implementor completes its one-time startup cleanup and explicitly reports that all six working files are absent.
3. The external caller confirms that no reviewer from a previous loop remains active.
4. Only then does the external caller launch the passive reviewer. Do not launch both roles simultaneously.

The files deliberately carry no IDs or generation tags, so they cannot distinguish an old live reviewer from the current one. A reviewer may accept a lock that already exists when it starts; this preserves delayed launch and reviewer-restart recovery, and is safe only under the required external launch order above.

## Working state files

All six working state files live in the repository root:

- `.skill_vault_review_lock` — empty marker: a completed implementation snapshot is waiting for review.
- `.skill_vault_implementor_to_reviewer.txt` — optional implementor-authored task context, diff explanation, test evidence, or response to feedback.
- `.skill_vault_reviewer_to_implementor.txt` — reviewer-authored findings or the exact `NO_FINDINGS` signal.
- `.skill_vault_review_round_complete` — empty marker: the implementor has finished the whole plan and requests reviewer shutdown acknowledgement.
- `.skill_vault_implementor_to_reviewer.tmp` — temporary output for atomic implementor-channel publication.
- `.skill_vault_reviewer_to_implementor.tmp` — temporary output for atomic reviewer-channel publication.

The lock and completion marker are empty files. Human-readable text belongs only in the two `.txt` channels. Channel files contain only their message bodies; do not add protocol headers.

Poll every 30 seconds using a sleep/poll mechanism or equivalent; do not busy-wait.

## Ownership and publication

- Only the implementor creates the lock and completion marker.
- Only the reviewer removes the lock, after publishing its complete response.
- Only the implementor creates, refreshes, or replaces the implementor-to-reviewer channel.
- Only the reviewer creates, refreshes, or replaces the reviewer-to-implementor channel.
- The implementor removes the reviewer final only after reading and fully consuming it. The reviewer never removes the implementor final.
- The implementor may remove all six files during its one-time startup cleanup. During final cleanup it removes the other five and leaves completion-marker removal to the reviewer.
- The reviewer that participated in this loop removes the completion marker and then terminates.

To refresh an outbound channel, remove its old temp and final, then either leave both absent or write the complete new body to the temp and atomically rename it to the final `.txt` file. Never write a final incrementally and never allow a channel's temp and final to coexist.

The channels have opposite lock polarity: the implementor publishes only while the lock is absent; the reviewer publishes only while the lock exists.

## Mandatory invariants

1. The implementor does not modify implementation files or its outbound channel while the lock exists.
2. The reviewer never modifies implementation files.
3. The reviewer reads and considers the implementor final, if present, before reviewing each request.
4. The implementor reads and considers the reviewer final before editing after a review.
5. The reviewer atomically publishes findings or `NO_FINDINGS` before removing the lock.
6. The implementor does not read reviewer feedback while the lock exists.
7. Each logical request receives exactly one reviewer decision. Recreating a missing, unclaimed lock continues the same request and frozen snapshot.
8. A reviewer that cannot finish leaves the lock and does not publish a decision.
9. The implementor publishes completion only after consuming `NO_FINDINGS`, finishing every planned phase, and removing the other five files. The reviewer removes the marker; the implementor observes that acknowledgement.
10. The implementor message present when the lock is created remains unchanged until the reviewer decides.
11. The reviewer message remains unchanged after unlock until the implementor consumes it.
12. A new lock is never created while a temp file or reviewer final remains.
13. `NO_FINDINGS` means only that the submitted snapshot is clean. It does not end the loop while planned work remains.

---

# Role: implementor

Follow this section only for the `implementor` role.

## One-time startup cleanup

Before inspecting or changing the implementation, treat all existing working files as stale:

1. Remove these files if present:
   - `.skill_vault_review_lock`
   - `.skill_vault_implementor_to_reviewer.txt`
   - `.skill_vault_reviewer_to_implementor.txt`
   - `.skill_vault_implementor_to_reviewer.tmp`
   - `.skill_vault_reviewer_to_implementor.tmp`
   - `.skill_vault_review_round_complete` last
2. Verify that all six are absent.
3. Report that startup cleanup is complete, then begin implementation work. The external caller may now launch the reviewer.

Perform this cleanup exactly once. It removes stale files but cannot stop an old agent, which is why the external caller must ensure that no reviewer from a previous loop remains active.

## Implement and prepare context

1. Understand the task and existing behavior.
2. Implement the requested change.
3. Run relevant tests, linters, type checks, static analysis, or other practical checks.
4. Inspect staged, unstaged, and relevant untracked changes and make the tree coherent and reviewable.
5. Do not create the lock while still editing or testing.

Before every request, refresh the optional implementor channel while the lock is absent:

1. Remove stale implementor temp and final files.
2. If there is nothing useful to say, leave both absent.
3. Otherwise write the entire task context, explanation, evidence, response, or disagreement to `.skill_vault_implementor_to_reviewer.tmp`.
4. Atomically rename the temp to `.skill_vault_implementor_to_reviewer.txt`.
5. Verify that the temp is absent and the final is complete.

## Request review

Before creating the lock, confirm that:

- the completion marker and lock are absent;
- both temp files are absent;
- the reviewer final is absent because any previous response was consumed;
- the implementation and optional implementor final are complete.

Create `.skill_vault_review_lock` as an empty file and verify that it exists and is empty. The lock is a marker, not a message channel. Freeze the implementation and implementor channel until the reviewer decides.

## Wait for review

While the lock exists, do not modify the implementation or either channel. Wait 30 seconds and poll again.

If the lock disappears:

1. If the reviewer temp exists, do not overwrite it, recreate the lock, or modify the implementation or channels. Wait 30 seconds and re-poll up to three times. If the temp disappears, restart this procedure. If it remains after the third re-poll, stop and report a protocol failure.
2. If the implementor temp exists, stop and report a protocol failure because the submitted snapshot was not stable.
3. If no reviewer final exists, recreate the empty lock for the same frozen logical request and resume polling.
4. Otherwise read the entire reviewer final and take it into account before editing.

An empty or missing reviewer final is not a decision. A file whose trimmed entire body is exactly `NO_FINDINGS` is a clean result; text that merely mentions that token is ordinary feedback.

## Handle reviewer feedback

For every finding or nit:

1. Understand the underlying issue.
2. Apply feedback that is correct, relevant, safe, and consistent with the task.
3. Do not blindly implement incorrect, contradictory, unsafe, misunderstood, or out-of-scope feedback.
4. If a suggestion is unsuitable but identifies a real issue, fix the underlying issue appropriately.
5. Preserve intended behavior and project conventions unless the feedback establishes a reason to change them.

After addressing findings, or after `NO_FINDINGS` when another planned phase remains:

1. Complete the next phase if applicable, run relevant checks, and inspect the tree.
2. Refresh the implementor channel for the next request.
3. Remove the reviewer final only after fully consuming it. This is a separate receipt acknowledgement; never create or overwrite that file.
4. Confirm that the completion marker, lock, both temp files, and reviewer final are absent.
5. Create the next empty lock, freeze the snapshot, and resume polling.

Repeat until every planned phase is complete and the latest response is `NO_FINDINGS`.

## Finish the whole plan

Only after consuming `NO_FINDINGS` and deciding that no planned work remains:

1. Confirm that the lock and reviewer temp are absent.
2. Remove, as separate cleanup operations:
   - `.skill_vault_reviewer_to_implementor.txt`
   - `.skill_vault_implementor_to_reviewer.txt`
   - `.skill_vault_implementor_to_reviewer.tmp`
   - `.skill_vault_reviewer_to_implementor.tmp`
3. Confirm that those four files and `.skill_vault_review_lock` are absent, and that the completion marker is absent.
4. Create `.skill_vault_review_round_complete` as an empty file and verify that it exists and is empty.
5. Make no further mutation. Wait 30 seconds and re-poll at most three times.
6. If the marker disappears, verify that all six working files are absent and exit.
7. If it remains after the third poll, leave it in place and report that shutdown still awaits reviewer acknowledgement.

## Implementor must never

- Spawn, delegate to, invoke, or simulate a reviewer. Request review only through the files and lock.
- Put prose in the lock or completion marker.
- Remove an active lock except during the one-time startup cleanup.
- Create, write, truncate, or overwrite the reviewer channel.
- Publish completion before consuming `NO_FINDINGS`, while planned work remains, or before the other five files are absent.
- Read reviewer feedback, edit implementation files, or change the implementor channel while the lock exists.
- Create a lock while any temp file or unconsumed reviewer final exists.
- Interpret missing feedback, an empty message, `NO_CHANGES`, or text merely containing `NO_FINDINGS` as the clean sentinel.

---

# Role: reviewer

Follow this section only for the `reviewer` role.

## Wait for a request

Remain passive and poll for the completion marker and lock every 30 seconds. Track whether this invocation has accepted at least one lock.

1. If the completion marker exists and this invocation previously accepted a lock, remove the marker, verify that it is absent, and terminate.
2. If the completion marker exists before this invocation has accepted a lock, do not remove it. Re-poll every 30 seconds up to three times; if the same marker remains after the third poll, report that this reviewer cannot acknowledge it and terminate without mutation.
3. If the lock is absent, do not review speculatively or modify working state; wait and poll again.
4. If the lock exists, accept exactly one review cycle and remember that this invocation has participated in the loop.

## Review a request

Treat the implementation and implementor channel as frozen while the lock exists.

1. Re-check that the lock exists. If it disappeared, abort this attempt and return to polling without touching the final files.
2. If the implementor temp exists, leave every coordination file unchanged and report an invalid snapshot.
3. If the implementor final exists, read it completely and take its context, constraints, evidence, or response into account. Evaluate it against the code and requirements; do not assume it is correct.
4. Re-check that the lock exists, then remove any stale reviewer temp and final left by an interrupted reviewer publication.
5. Inspect repository status, staged and unstaged changes relative to the appropriate base, relevant untracked implementation files, and enough surrounding code and tests to understand the effect.
6. Never modify implementation files.

Review until the frozen snapshot has no comment you would reasonably ask the implementor to address. Include all severities and genuine nits: correctness, regressions, edge cases, error handling, concurrency, security, compatibility, tests, conventions, maintainability, scope, naming, clarity, and consistency. Do not invent findings to keep the loop running.

## Publish reviewer feedback

Every accepted request produces exactly one response. With findings, use the complete findings as the message body. With no findings or nits, make the entire body exactly `NO_FINDINGS` with no other commentary.

1. Re-check that the lock exists. If not, abort and return to polling without publishing.
2. Ensure the reviewer temp and final are absent.
3. Write the entire response to `.skill_vault_reviewer_to_implementor.tmp`.
4. Re-check that the lock exists. If it disappeared, remove only the unpublished temp and return to polling.
5. Atomically rename the temp to `.skill_vault_reviewer_to_implementor.txt`.
6. Verify that the temp is absent and the final is complete.
7. Re-check that the lock exists. If it still exists, remove it.
8. Do not change the final afterward; the implementor removes it after consumption.
9. Return to passive polling for the next lock or completion marker.

Publishing before unlocking is mandatory for both findings and `NO_FINDINGS`. If review or publication cannot finish, leave the lock in place. Neither `NO_FINDINGS` nor unlocking terminates the reviewer.

## Reviewer must never

- Spawn, delegate to, invoke, or simulate an implementor.
- Put prose in the lock or completion marker.
- Create the lock or completion marker.
- Remove the lock before complete reviewer feedback is published.
- Modify implementation files or apply its own suggestions.
- Remove the completion marker before this invocation has accepted a review request.
- Create, write, replace, truncate, or remove the implementor channel.
- Modify the reviewer final after unlocking.
- Use `NO_CHANGES`, an empty file, or missing feedback instead of the exact `NO_FINDINGS` body.

---

# State-machine summary

~~~text
IMPLEMENTOR removes all stale working files once
IMPLEMENTOR edits/tests and optionally publishes context atomically
IMPLEMENTOR creates an empty lock and freezes
REVIEWER reads optional context and reviews
REVIEWER atomically publishes findings or NO_FINDINGS
REVIEWER removes the lock and keeps polling
IMPLEMENTOR reads and consumes the response

if work remains:
  IMPLEMENTOR implements the next phase and requests another review

if the whole plan is complete after NO_FINDINGS:
  IMPLEMENTOR removes the other five files
  IMPLEMENTOR creates the empty completion marker last
  REVIEWER removes the marker and exits
  IMPLEMENTOR observes the acknowledgement and exits
~~~

# Failure behavior

- Any files at implementor startup: remove all six, completion marker last.
- Lock disappears without reviewer temp or final: recreate it for the same frozen request.
- Lock disappears with reviewer temp: wait up to three polls for it to clear, then report failure.
- Implementor temp exists with a lock: reviewer leaves state unchanged and reports an invalid snapshot.
- Reviewer cannot finish: leave the lock and do not publish a decision.
- `NO_FINDINGS` with planned work remaining: continue the plan and request another review.
- Completion acknowledgement does not arrive within three polls: leave the marker, report pending shutdown, and stop polling.
- Reviewer sees completion before accepting any lock: leave the marker, wait at most three polls, report that it cannot acknowledge, and terminate.
- Missing or invalid role: stop and request `implementor` or `reviewer`.

# Formal verification

This protocol is modeled in the checked [TLA+ source](verification/CodeReviewLoop.tla). The model uses clean abstract file names without the skill's `.skill_vault_` prefix.

The model covers arbitrary stale-file startup cleanup, delayed external reviewer launch, optional implementor context on first and later requests, incoming-message read gates, atomic channel publication, snapshot freezing, findings-or-`NO_FINDINGS` publication before unlock, bounded lock loss and same-snapshot retry, another planned phase after `NO_FINDINGS`, implementor-owned final cleanup and completion publication, reviewer acknowledgement, and clean termination.

The model assumes both agents follow the protocol and that external orchestration does not overlap a new loop with an old reviewer. Agent noncompliance, old-agent interference, semantic understanding of messages, and documented timeout/failure branches remain outside the abstraction as detailed in the [verification README](verification/README.md).

When changing protocol states, file ownership, message lifecycle, publication order, recovery, or cleanup, update the model and run `verification/run-tlc.sh`, `verification/check-state-space.sh`, `verification/check-early-unlock.sh`, `verification/check-temp-file-unlock.sh`, and `verification/check-cleanup-order.sh`. The change is incomplete until the normal model passes, state-space statistics match, and all negative checks report their expected violations.

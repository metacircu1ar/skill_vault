---
name: code-review-loop
description: "Coordinate an implementor and a static read-only reviewer through blocking Python waiters and files in a shared working directory. Invoke with one role and an optional completion authority."
argument-hint: "[implementor|reviewer] [completion-authority=implementor|caller]"
---

# Code Review Loop

Use this skill to coordinate exactly two externally launched agents through one shared coordination directory:

- **implementor** — changes the code, requests review, applies valid feedback, and repeats;
- **reviewer** — passively waits for requests, performs a strictly static read-only review of the identified repository and context, publishes findings or `NO_FINDINGS`, and remains available until the session completion authority closes the loop.

An agent running either role must not spawn, delegate to, invoke, or simulate the opposite role, even if subagent tools are available.

## Invocation

Invoke this skill with exactly one role. Completion authority is optional:

~~~text
/code-review-loop implementor
~~~

or:

~~~text
/code-review-loop reviewer
~~~

The invocation arguments are available as `$ARGUMENTS` on systems that support skill arguments.

Determine the role and completion authority from the arguments or explicit values supplied by the caller. The only valid roles are `implementor` and `reviewer`. If completion authority is omitted, resolve it to `implementor`. The only valid explicit completion authorities are:

- `completion-authority=implementor` — the implementor decides when no work remains and closes the session itself;
- `completion-authority=caller` — the enclosing caller decides whether to continue with another work item or close the session. The implementor must not close it on its own.

Both role invocations for one session must resolve to the same completion authority. Thus, omitting it from both invocations selects `implementor`; an explicit `caller` value must be supplied to both. If the role is missing or ambiguous, or an explicit completion authority is invalid or inconsistent with the already-declared session, do not guess; stop and request valid invocation values.

For example, an epic that keeps one reviewer alive across several tasks invokes both roles with `completion-authority=caller`. Each task ends at a clean work-item boundary; only the epic decides when to close the shared review session.

Once given a valid role, start that role immediately. Do not ask whether the opposite role is running, ready, or already launched, and do not wait for the caller to confirm its status. The implementor begins cleanup and implementation; the reviewer starts its blocking waiter.

## Required external launch order

This ordering is a safety requirement, not a convenience:

1. The external caller ensures that neither role from a previous loop remains active.
2. The external caller launches the implementor.
3. The implementor completes its one-time startup cleanup and explicitly reports that all six working files are absent from the coordination directory.
4. Only then does the external caller launch the passive reviewer. Do not launch both roles simultaneously.

The files deliberately carry no IDs or generation tags, so they cannot distinguish an old live reviewer from the current one. A reviewer may accept a lock that already exists when it starts; this preserves delayed launch and reviewer-restart recovery, and is safe only under the required external launch order above.

The launch order is the external caller's responsibility. Stopping old roles before cleanup is mandatory because cleanup cannot stop an old process from recreating or republishing a protocol file afterward. Neither agent asks the caller or the opposite role to confirm that the order was followed; each starts its assigned behavior as soon as it is invoked. Completion authority controls only who decides to close the session; it does not change launch order, file ownership, or reviewer behavior.

## Working state files

At invocation, resolve the current working directory to an absolute path and keep it as the fixed **coordination directory** for the entire loop. All six working state files live directly in that directory:

- `.skill_vault_review_lock` — empty marker: a completed implementation snapshot is waiting for review.
- `.skill_vault_implementor_to_reviewer.txt` — implementor-authored review context. Its first publication is mandatory and contains the complete context handoff; later requests retain or atomically replace it with a complete current message.
- `.skill_vault_reviewer_to_implementor.txt` — reviewer-authored findings or the exact `NO_FINDINGS` signal.
- `.skill_vault_review_round_complete` — empty marker: the declared completion authority has closed the whole review session through the implementor CLI and requests reviewer shutdown acknowledgement.
- `.skill_vault_implementor_to_reviewer.tmp` — temporary output for atomic implementor-channel publication.
- `.skill_vault_reviewer_to_implementor.tmp` — temporary output for atomic reviewer-channel publication.

The coordination directory is not implicitly the repository root. It may be the repository root, a parent such as `/x` for a repository at `/x/repo1`, or an unrelated shared directory. Repository and context paths are supplied separately in the implementor message. Even if an agent changes its shell working directory to inspect the repository, every protocol-script invocation and channel publication must continue using the captured absolute coordination directory. Never search for, poll, or create protocol files in the repository, its parents, its children, or any context directory.

The lock and completion marker are empty files. Human-readable text belongs only in the two `.txt` channels. Channel files contain only their message bodies; do not add protocol headers.

## Required protocol scripts

Use Python 3.9 or newer. The examples use `python3`; use the platform's equivalent Python 3 launcher, such as `python` or `py -3`, when needed. Resolve `<skill-dir>` to the directory containing this `SKILL.md`, and pass the captured absolute coordination directory as `<coordination-dir>`. The role entrypoints are:

- `<skill-dir>/scripts/implementor_loop.py`
- `<skill-dir>/scripts/reviewer_loop.py`

The scripts own every wait and cleanup operation. Their wait commands run silently in the foreground, inspect the six protocol paths once per second, and exit only after the requested state is actionable or a protocol error is detected. They use only the Python standard library; do not install Watchdog or substitute an OS-specific filesystem watcher.

A wait command returning a live process or session identifier is still running. Continue waiting on that exact process with the execution environment's wait/resume mechanism. Silence, an execution-tool yield, or an ordinary tool-call time limit is not a protocol result. Do not send a final response, start a second waiter, or leave the role. Only a completed process that exits zero with JSON `"status": "ready"` authorizes the next step. On a nonzero exit accompanied by JSON `"status": "error"`, report the protocol error. If the environment is known to have externally terminated a waiter without either record, including exit 130, immediately run the same wait command again against the same frozen state unless the operator explicitly stops the loop. Treat any other unstructured nonzero exit as a launcher or runtime failure: report it instead of retrying indefinitely.

Do not reproduce a wait with shell loops, manual sleeps, repeated file checks, Watchdog, `inotify`, or another agent-side polling mechanism. Do not delete a protocol file manually; invoke the owning role's cleanup command below.

Cleanup and transition commands are replay-safe for their documented state. If the execution environment is known to terminate one before it emits JSON, rerun that same command rather than finishing its file operations manually. In particular, `complete` retains the clean reviewer response as a durable phase record and atomically promotes it to the empty completion marker, so interruption cannot strand an ambiguous all-files-absent pre-acknowledgement state.

## Ownership and publication

- Only the implementor creates the lock. The declared completion authority creates the completion marker only through the implementor CLI.
- Only the reviewer, through `release-review`, removes the lock after publishing its complete response.
- Only the implementor creates, refreshes, or replaces the implementor-to-reviewer channel.
- Only the reviewer creates, refreshes, or replaces the reviewer-to-implementor channel.
- The implementor removes the reviewer final only through `acknowledge-feedback` or `complete`, after reading and fully consuming it. The reviewer never removes the implementor final.
- The implementor script may remove all six files during one-time startup cleanup. During final cleanup it makes the other five paths absent, atomically promoting the clean reviewer final into the completion marker, and leaves completion-marker removal to the reviewer script.
- The reviewer that participated in this loop removes the completion marker through `acknowledge-completion` and then terminates.

To refresh an outbound channel, first invoke the owning role's preparation command. Then write the complete new body to the temp and atomically rename it to the final `.txt` file. Never write a final incrementally and never allow a channel's temp and final to coexist.

The channels have opposite lock polarity: the implementor publishes only while the lock is absent; the reviewer publishes only while the lock exists.

## Mandatory invariants

1. The implementor does not modify implementation files or its outbound channel while the lock exists.
2. Apart from publishing its response and removing protocol markers as specified here, the reviewer never modifies repository or context files and performs only static inspection.
3. Every review request carries a complete implementor final, and the reviewer reads and considers it before reviewing.
4. The implementor reads and considers the reviewer final before editing after a review.
5. The reviewer atomically publishes findings or `NO_FINDINGS` before removing the lock.
6. The implementor does not read reviewer feedback while the lock exists.
7. Each logical request receives exactly one reviewer decision. Recreating a missing, unclaimed lock continues the same request and frozen snapshot.
8. A reviewer that cannot finish leaves the lock and does not publish a decision.
9. The declared completion authority publishes completion through the implementor CLI only after consuming `NO_FINDINGS` and deciding that no session work remains. The CLI first makes the four paths other than the reviewer final and completion marker absent, then atomically promotes that final into the marker. The reviewer removes the marker; the completion authority observes that acknowledgement.
10. The implementor message present when the lock is created remains unchanged until the reviewer decides.
11. The reviewer message remains unchanged after unlock until the implementor consumes it.
12. A new lock is never created while a temp file or reviewer final remains.
13. `NO_FINDINGS` means only that the submitted snapshot is clean. It does not end the loop while planned work remains.
14. The first implementor message identifies the fixed coordination directory, repository, and every needed context directory by absolute path, and supplies the full task text unless an identified context source already contains it.
15. Neither role asks for confirmation of the opposite role's status; a valid invocation starts its assigned behavior immediately.
16. Agents never perform their own polling or cleanup. A role remains active while its blocking wait process is running and advances only after the script emits a ready result.
17. Completing a reviewed work item does not close a caller-owned session. Only the declared completion authority decides between acknowledging the clean response to continue and publishing session completion.

---

# Role: implementor

Follow this section only for the `implementor` role.

## One-time startup cleanup

Before inspecting or changing the implementation, treat all existing working files as stale and run:

~~~text
python3 "<skill-dir>/scripts/implementor_loop.py" startup-cleanup --coordination-dir "<coordination-dir>"
~~~

The command removes only the six protocol paths, removes the completion marker last, verifies that all six are absent, and emits `startup_cleanup_complete`. Report that startup cleanup in the captured coordination directory is complete, then begin implementation work. Do not ask whether the reviewer is running or wait for confirmation about it.

Perform this cleanup exactly once. It removes stale files but cannot stop an old agent, which is why the external caller must ensure that no reviewer from a previous loop remains active.

## Implement and prepare context

1. Understand the task and existing behavior.
2. Implement the requested change.
3. Run relevant tests, linters, type checks, static analysis, or other practical checks.
4. Inspect staged, unstaged, and relevant untracked changes and make the tree coherent and reviewable.
5. Do not create the lock while still editing or testing.

### Publish the initial context handoff

Before the first review request, publish a mandatory, self-contained implementor message while the lock is absent. Its body must include:

- **Coordination directory:** the resolved absolute path captured from the implementor's initial current working directory. State explicitly that all six protocol files are read and written only there.
- **Repository:** the resolved absolute path to the repository being reviewed. Do not use `~`, environment-variable shorthand, or a relative path.
- **Context directories:** the resolved absolute path of every directory the reviewer needs beyond the repository, with a short statement of what it contains. Include relevant evidence, log, crash-dump, reproduction, task-bundle, fixture, or other data directories. Write `None` when no additional directory is needed.
- **Task:** either the full task text or the resolved absolute path to the exact context file or files that contain the full task. A directory path alone is not a task source; identify the file and where the operative task can be found. Include the full text directly when it exists only in conversation or was not supplied through a context directory.
- **Review target and evidence:** what implementation or snapshot is being submitted, the relevant base or comparison when known, checks already run, and the evidence most useful for judging it.
- **Implementor notes:** constraints, preserved behavior, known limitations, uncertain assumptions, responses to prior discussion, or any other information the implementor considers important for this review.
- **Completion authority:** the resolved value, either `implementor` or `caller`. State that `implementor` was selected by default when the invocation omitted it, and identify the enclosing workflow represented by `caller` when that value is explicit.

Point to large logs, dumps, or evidence by absolute directory and useful filenames instead of copying their full contents into the channel. Do not omit task-relevant context merely because it is large; give the reviewer enough location and interpretation detail to inspect it.

Publish atomically:

1. Run:

   ~~~text
   python3 "<skill-dir>/scripts/implementor_loop.py" prepare-context --coordination-dir "<coordination-dir>"
   ~~~

2. Write the complete context handoff to `.skill_vault_implementor_to_reviewer.tmp`.
3. Atomically rename the temp to `.skill_vault_implementor_to_reviewer.txt`.
4. Verify that the temp is absent and the final is complete.

### Maintain context on later requests

The implementor final must remain present for every later request. If the stable context and current notes remain accurate, leave it unchanged. If anything material changes, replace it atomically while unlocked after acknowledging the prior reviewer final: run `prepare-context`, write one complete replacement to the temp, then rename it to the final. A replacement must preserve the coordination-directory path, repository path, context-directory paths, completion authority, and task source or full task text from the initial handoff while adding the current diff explanation, validation evidence, feedback response, disagreement, or other round-specific notes.

## Request review

Before creating the lock, confirm that:

- the completion marker and lock are absent;
- both temp files are absent;
- the reviewer final is absent because any previous response was consumed;
- the implementation and mandatory implementor final are complete and current.

Create `.skill_vault_review_lock` as an empty file and verify that it exists and is empty. The lock is a marker, not a message channel. Freeze the implementation and implementor channel until the reviewer decides.

## Wait for review

While the lock exists, do not modify the implementation or either channel. Run this command in the foreground and remain in the loop until it finishes:

~~~text
python3 "<skill-dir>/scripts/implementor_loop.py" wait-for-review --coordination-dir "<coordination-dir>"
~~~

The command waits once per second without returning control after each poll. It exits ready only when the lock is absent and a complete reviewer final exists. It also recreates a missing lock for the same frozen request when no reviewer publication exists, and reports invalid temp or completion states as protocol errors. After `review_result`, read the entire reviewer final and take it into account before editing.

An empty or missing reviewer final is not a decision. A file whose trimmed entire body is exactly `NO_FINDINGS` is a clean result; text that merely mentions that token is ordinary feedback.

## Handle reviewer feedback

For every finding or nit:

1. Understand the underlying issue.
2. Apply feedback that is correct, relevant, safe, and consistent with the task.
3. Do not blindly implement incorrect, contradictory, unsafe, misunderstood, or out-of-scope feedback.
4. If a suggestion is unsuitable but identifies a real issue, fix the underlying issue appropriately.
5. Preserve intended behavior and project conventions unless the feedback establishes a reason to change them.

After fully consuming findings, or after fully consuming `NO_FINDINGS` when another session work item remains, acknowledge the reviewer final through the script:

~~~text
python3 "<skill-dir>/scripts/implementor_loop.py" acknowledge-feedback --coordination-dir "<coordination-dir>"
~~~

Then:

1. Complete the next phase if applicable, run relevant checks, and inspect the tree.
2. Keep the implementor channel unchanged when its complete context remains current, or atomically replace it with a complete updated message through `prepare-context` and atomic publication.
3. Confirm that the completion marker, lock, both temp files, and reviewer final are absent.
4. Create the next empty lock, freeze the snapshot, and run `wait-for-review` again.

Repeat until the current work item is complete and the latest response is `NO_FINDINGS`. Then apply the completion-authority rule below.

## Finish or hand back the session

After reading an unlocked reviewer final whose entire body is exactly `NO_FINDINGS`, choose the next transition according to the declared completion authority:

- With `completion-authority=implementor`, decide whether session work remains. If it does, run `acknowledge-feedback` and continue. If it does not, close the session as described below.
- With `completion-authority=caller`, do not decide or close the session. Leave the unlocked `NO_FINDINGS` reviewer final and the current implementor context in place, report that the work item is clean, and return control to the caller. The caller must then make exactly one of these transitions through the implementor CLI: run `acknowledge-feedback` before starting the next work item, or run `complete` to close the whole session. Until the caller makes that choice, do not edit implementation files, change either channel, create a lock, or publish completion.

To continue a caller-owned session, the caller must run `acknowledge-feedback` and resume the same already-initialized implementor role in the same coordination directory. The resumed role continues with the next work item and must not repeat one-time startup cleanup. Do not launch a fresh implementor role into a live session; if the existing role cannot be resumed, close the session and start a new one using the required launch order.

Only the declared completion authority may close the session. After it has consumed `NO_FINDINGS` and decided that no session work remains, it runs:

~~~text
python3 "<skill-dir>/scripts/implementor_loop.py" complete --coordination-dir "<coordination-dir>"
~~~

The command requires the unlocked reviewer final to contain exactly `NO_FINDINGS` on its first run, performs final cleanup, empties that retained response, and atomically renames it to the completion marker after the other four paths are absent. A replay resumes from the retained final, an already-published marker, or an already-acknowledged all-absent state. This is why caller-owned work returns before acknowledging its final clean response: the caller must retain the choice between continuing and closing. After `complete`, make no further mutation and block for acknowledgement:

~~~text
python3 "<skill-dir>/scripts/implementor_loop.py" wait-for-completion --coordination-dir "<coordination-dir>"
~~~

Exit the session only after the command emits `completion_acknowledged` and verifies that all six protocol files are absent. In caller-owned mode, the caller performs both `complete` and `wait-for-completion`; the implementor work-item invocation has already returned without terminating the reviewer.

## Implementor must never

- Spawn, delegate to, invoke, or simulate a reviewer. Request review only through the files and lock.
- Ask whether the reviewer is running, ready, or launched, or wait for confirmation of its status.
- Put prose in the lock or completion marker.
- Remove an active lock except during the one-time startup cleanup.
- Create, write, truncate, or overwrite the reviewer channel.
- Publish completion without being the declared completion authority, before consuming `NO_FINDINGS`, while session work remains, or except through the CLI's ordered cleanup and atomic reviewer-final promotion.
- Read reviewer feedback, edit implementation files, or change the implementor channel while the lock exists.
- Create a lock while any temp file or unconsumed reviewer final exists.
- Poll protocol files, sleep between checks, or delete a protocol file directly instead of using the implementor script.
- Interpret missing feedback, an empty message, `NO_CHANGES`, or text merely containing `NO_FINDINGS` as the clean sentinel.

---

# Role: reviewer

Follow this section only for the `reviewer` role.

## Wait for a request

Start immediately without asking whether the implementor is running, ready, or finished with startup. Do not review speculatively or inspect any other directory for protocol state.

Before accepting the first request, run this foreground command:

~~~text
python3 "<skill-dir>/scripts/reviewer_loop.py" wait-for-request --coordination-dir "<coordination-dir>" --fresh
~~~

After accepting any request in this invocation, use `--participated` instead of `--fresh` for every later wait:

~~~text
python3 "<skill-dir>/scripts/reviewer_loop.py" wait-for-request --coordination-dir "<coordination-dir>" --participated
~~~

Each command remains blocked and checks once per second until it emits `review_request`, `review_ready_to_release`, or, only for a participating reviewer, `completion`. A fresh reviewer never acknowledges a completion marker from a loop it did not join; a marker that remains in that state for 90 seconds produces a protocol error.

On `review_request`, remember that this invocation has participated and review exactly one frozen snapshot. `review_ready_to_release` means a prior reviewer invocation atomically published a complete response but was interrupted before unlocking. Before releasing it, read the complete implementor final and validate its fixed coordination directory and completion authority exactly as required for a normal request. If either check fails, leave all files unchanged and report an invalid snapshot. Otherwise remember participation, do not replace or repeat the existing decision, run `release-review`, and return to `wait-for-request --participated`. On `completion`, run:

~~~text
python3 "<skill-dir>/scripts/reviewer_loop.py" acknowledge-completion --coordination-dir "<coordination-dir>" --participated
~~~

Then verify the ready result and terminate.

## Review a request

Treat the implementation and implementor channel as frozen while the lock exists.

1. Re-check that the lock exists. If it disappeared, abort this attempt and return to the blocking `wait-for-request --participated` command without touching the final files.
2. If the implementor temp exists, leave every coordination file unchanged and report an invalid snapshot.
3. Require the implementor final. If it is absent, leave every coordination file unchanged and report an invalid snapshot. Otherwise read it completely and take its coordination-directory path, repository path, context paths, task, constraints, evidence, and notes into account. Evaluate them against the code and requirements; do not assume they are correct.
4. Confirm that the message's coordination-directory path is exactly the directory captured at invocation. If it differs, leave every coordination file unchanged and report an invalid snapshot. Never switch directories or search for another set of protocol files.
5. Confirm that the message's completion authority exactly matches the reviewer's invocation value. If it differs or is absent, leave every coordination file unchanged and report an invalid snapshot.
6. Re-check that the lock exists, then run `python3 "<skill-dir>/scripts/reviewer_loop.py" prepare-response --coordination-dir "<coordination-dir>"`. This requires an active lock and complete implementor final when it starts, then removes only stale unpublished reviewer temp output. It refuses to replace an already-published final. A racing lock loss does not make successful cleanup fail; the publication-time lock checks below still decide whether the response may be published.
7. Inspect the repository identified in the message; do not assume it is the coordination directory. Read its version-control state, staged and unstaged changes relative to the appropriate base, relevant untracked implementation files, and enough surrounding code and tests as text to understand the effect. Use only non-mutating inspection. For Git, disable optional locks, pagers, fsmonitor, external diffs, and textconv helpers: use the execution environment to set `GIT_OPTIONAL_LOCKS=0`, pass `--no-pager -c core.fsmonitor=false` before the Git subcommand, and pass `--no-ext-diff --no-textconv` to diff-producing subcommands. Do not invoke a configured helper merely to inspect text.
8. Never modify repository or context files and never execute project code or a validation tool against it.

This is a completely static review. Do not run tests, builds, compilers, linkers, type-checkers, linters, formatters, code generators, package-manager commands, migrations, benchmarks, fuzzers, project scripts, project binaries, or any command intended to determine whether the implementation executes or validates successfully. Read existing test code and implementor-supplied results as evidence, but leave all compilation and dynamic validation to the implementor.

Concentrate review effort on substantive correctness: whether the implementation fundamentally satisfies the task, preserves required behavior and invariants, and handles data flow, state transitions, boundaries, failure modes, concurrency, security, and compatibility correctly. Potential syntax, type, linking, or compilation issues are **trivial** in this workflow. Classify any such note as `Trivial` and mention it briefly only when it is obvious; do not spend material time mentally compiling the source, reconstructing toolchain diagnostics, or making compilation confidence a review-completion gate.

Review until the frozen snapshot has no substantive comment or genuine static nit you would reasonably ask the implementor to address. Do not invent findings to keep the loop running.

## Publish reviewer feedback

Every accepted request produces exactly one response. With findings, use the complete findings as the message body. With no findings or nits, make the entire body exactly `NO_FINDINGS` with no other commentary.

1. Re-check that the lock exists. If not, return to `wait-for-request --participated` without publishing.
2. Ensure `prepare-response` completed and the reviewer temp and final are absent.
3. Write the entire response to `.skill_vault_reviewer_to_implementor.tmp`.
4. Re-check that the lock exists. If it disappeared, run `python3 "<skill-dir>/scripts/reviewer_loop.py" abort-response --coordination-dir "<coordination-dir>"`, then return to `wait-for-request --participated`. The abort command removes only the unpublished reviewer temp and remains safe if the implementor has already recreated the lock for the same frozen request.
5. Atomically rename the temp to `.skill_vault_reviewer_to_implementor.txt`.
6. Verify that the temp is absent and the final is complete.
7. Run `python3 "<skill-dir>/scripts/reviewer_loop.py" release-review --coordination-dir "<coordination-dir>"`. This requires the complete final and removes the lock if it is still present. It does not re-inspect the implementor-owned final after unlocking, because the implementor may consume that file immediately.
8. Do not change the final afterward; the implementor removes it after consumption.
9. Return to the blocking `wait-for-request --participated` command.

Publishing before unlocking is mandatory for both findings and `NO_FINDINGS`. If review or publication cannot finish, leave the lock in place. Neither `NO_FINDINGS` nor unlocking terminates the reviewer.

## Reviewer must never

- Spawn, delegate to, invoke, or simulate an implementor.
- Ask whether the implementor is running, ready, or launched, or wait for confirmation of its status.
- Put prose in the lock or completion marker.
- Create the lock or completion marker.
- Remove the lock before complete reviewer feedback is published.
- Modify implementation files or apply its own suggestions.
- Run tests, builds, compilation, linking, type-checking, linting, formatting, generation, package operations, project scripts or binaries, or any other dynamic validation.
- Write to the repository or any context/evidence path; reviewer writes are limited to its coordination-channel publication and the specified lock or completion-marker removals.
- Remove the completion marker before this invocation has accepted a review request.
- Create, write, replace, truncate, or remove the implementor channel.
- Modify the reviewer final after unlocking.
- Poll protocol files, sleep between checks, or delete a protocol file directly instead of using the reviewer script.
- Use `NO_CHANGES`, an empty file, or missing feedback instead of the exact `NO_FINDINGS` body.

---

# State-machine summary

~~~text
IMPLEMENTOR removes all stale working files once
IMPLEMENTOR edits/tests and publishes the complete initial context atomically
IMPLEMENTOR creates an empty lock and freezes
REVIEWER reads the mandatory context and performs a static read-only review
REVIEWER atomically publishes findings or NO_FINDINGS
REVIEWER releases the lock and starts the next blocking waiter
IMPLEMENTOR reads and consumes the response

if session work remains:
  IMPLEMENTOR implements the next phase and requests another review

if the current work item is clean and completion authority is CALLER:
  IMPLEMENTOR leaves the unlocked NO_FINDINGS response in place
  CALLER either acknowledges it and starts another work item, or closes the session

if the completion authority decides the session is complete after NO_FINDINGS:
  COMPLETION AUTHORITY invokes the implementor CLI to remove the other files
  COMPLETION AUTHORITY atomically promotes the emptied clean response to the completion marker last
  REVIEWER removes the marker and exits
  COMPLETION AUTHORITY observes the acknowledgement and exits the session
~~~

# Failure behavior

- Any files at implementor startup: `startup-cleanup` removes the exact six paths, completion marker last.
- Lock disappears without reviewer temp or final: the running `wait-for-review` process confirms the state on its next one-second poll, recreates the lock for the same frozen request, and keeps waiting.
- Lock disappears with reviewer temp: `wait-for-review` keeps polling internally for up to 90 seconds, then reports a protocol error if the temp remains.
- A participating reviewer restarts after lock loss with only its unpublished temp remaining: `wait-for-request --participated` removes that owned orphan temp and continues waiting; a fresh reviewer never claims or removes it.
- A complete reviewer final remains under the lock after reviewer interruption: `wait-for-request` emits `review_ready_to_release`; the reviewer releases that existing decision without replacing or repeating it.
- Implementor temp exists with a lock: reviewer leaves state unchanged and reports an invalid snapshot.
- Implementor final is missing with a lock: reviewer leaves state unchanged and reports an invalid snapshot.
- Implementor message names a different coordination directory: reviewer leaves state unchanged and reports an invalid snapshot.
- Implementor message omits the completion authority or names one different from the reviewer invocation: reviewer leaves state unchanged and reports an invalid snapshot.
- Reviewer cannot finish: leave the lock and do not publish a decision.
- `NO_FINDINGS` with session work remaining: the implementor authority acknowledges it and continues; a caller authority chooses whether to acknowledge it and continue or close the session.
- Completion acknowledgement has not arrived: `wait-for-completion` remains blocked; do not exit merely because time passed.
- Reviewer sees completion before accepting any lock: `wait-for-request --fresh` leaves the marker unchanged and reports a protocol error if it remains for 90 seconds.
- A wait command is still running or the execution tool yields a live session: continue that same process; this is not a reason to terminate the role.
- A wait process is known to have been externally terminated without a ready or error record: restart the same wait against the unchanged protocol state.
- A role script exits nonzero with a JSON error: stop the affected transition and report it; do not imitate the failed cleanup manually. Restart a non-JSON failure only when the execution environment confirms external waiter termination; otherwise report the launcher or runtime failure.
- Missing or invalid role: stop and request `implementor` or `reviewer`. An omitted completion authority is valid and defaults to `implementor`; reject only an invalid or inconsistent explicit authority.

# Formal verification

This protocol is modeled in the checked [TLA+ source](verification/CodeReviewLoop.tla). The model uses clean abstract file names without the skill's `.skill_vault_` prefix.

The model covers arbitrary stale-file startup cleanup, delayed external reviewer launch, mandatory implementor context on every request with a required initial publication and later reuse or atomic refresh, incoming-message read gates, snapshot freezing, findings-or-`NO_FINDINGS` publication before unlock, bounded lock loss and same-snapshot retry, another planned phase after `NO_FINDINGS`, final cleanup and completion publication through the implementor CLI, reviewer acknowledgement, and clean termination. The caller-versus-implementor decision authority is a control-plane choice outside the file-state model; both choices use the same verified completion transition. TLC verifies the common file transition after an authorized close decision, not authority selection, caller handback, or the promise that an implementor will not close a caller-owned session.

The Python role scripts are the concrete implementation of the model's wait, recovery, cleanup, unlock, and completion-acknowledgement transitions. The model abstracts the scripts' internal one-second polls because those polls do not change protocol state.

The model assumes both agents follow the protocol and that external orchestration does not overlap a new loop with an old reviewer. It treats the fixed coordination directory as one abstract file namespace and a reviewer decision as an abstract transition; absolute-path equality, static-only inspection, agent noncompliance, process termination by the execution environment, old-agent interference, semantic understanding of messages, and documented timeout/failure branches remain outside the abstraction as detailed in the [verification README](verification/README.md).

When changing protocol states, file ownership, message lifecycle, publication order, recovery, or cleanup, update the model and run `verification/run-tlc.sh`, `verification/check-state-space.sh`, `verification/check-early-unlock.sh`, `verification/check-temp-file-unlock.sh`, and `verification/check-cleanup-order.sh`. The change is incomplete until the normal model passes, state-space statistics match, and all negative checks report their expected violations.

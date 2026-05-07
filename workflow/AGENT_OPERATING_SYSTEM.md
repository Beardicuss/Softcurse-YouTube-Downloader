# ⚙️ AGENT OPERATING SYSTEM — WORKFLOW ORCHESTRATION PROTOCOL

This is your complete operating model. Read it at the start of every session.
Follow it without exception. When in doubt, refer back here.

---

## 🟢 0. SESSION INITIALIZATION (Run at Every Session Start)

Before touching any code or task, do this in order:

```
1. Read tasks/lessons.md in full — internalize every rule
2. Read tasks/todo.md — understand current task state and what's in progress
3. Confirm your understanding with a 2-sentence session brief:
   "I'm continuing [task]. Key lesson to apply today: [most relevant lesson]."
4. If no todo.md exists, ask the user for the session goal before proceeding
```

Do not skip initialization. Context from previous sessions prevents repeat mistakes.

---

## 📐 1. PLANNING PROTOCOL

### 1.1 When to enter plan mode

Enter plan mode (write to `tasks/todo.md` before acting) when the task meets
ANY of these criteria:

| Trigger | Example |
|---------|---------|
| 3 or more discrete steps | Auth system with routes, middleware, and tests |
| Touches more than 2 files | Refactor that crosses module boundaries |
| Involves architectural decisions | Choosing between two data models |
| Has external dependencies | API integration, DB schema change |
| Affects public interfaces | Changing function signatures, API contracts |
| Carries rollback risk | DB migration, file system restructure |

Simple tasks (fix a typo, rename a variable, add a log line) do not need a plan.
When uncertain, default to planning. Over-planning costs 2 minutes. Under-planning
costs hours.

### 1.2 Plan format (`tasks/todo.md`)

```markdown
## Task: <name>
**Goal:** One sentence — what success looks like.
**Approach:** 2-3 sentences — the strategy, not the steps.
**Risk:** What could go wrong and how you'll handle it.

### Steps
- [ ] Step 1 — <specific, verifiable action>
- [ ] Step 2 — <specific, verifiable action>
- [ ] Step 3 — <specific, verifiable action>

### Verification
- [ ] <how you will prove each step worked>
- [ ] Tests pass: `<exact command>`
- [ ] Build passes: `<exact command>`

### Review
<!-- Fill in after completion -->
**Result:** ✅ complete / ❌ blocked / ⚠️ partial
**What changed from the plan:** <delta>
**Lessons captured:** yes / no
```

### 1.3 When the plan breaks down

If you hit a blocker or something goes sideways mid-execution:

```
STOP. Do not keep pushing.

1. Write a BLOCKED entry in todo.md with the exact failure and what you tried
2. Assess: is this a fixable deviation or a fundamental wrong turn?
   - Fixable deviation → update the plan, continue
   - Wrong turn → revert to last known-good state, re-plan from scratch
3. If you've attempted the same fix more than twice: escalate to the user
   with a clear problem statement, what you tried, and two proposed paths forward
```

Never spiral. Three failed attempts at the same approach is a signal to stop,
not to try a fourth time.

---

## 🤖 2. SUBAGENT STRATEGY

### 2.1 When to spawn a subagent

Spawn a subagent when the task benefits from isolation. Use this decision rule:

```
Will this work pollute the main context with noise the primary task doesn't need?
  YES → subagent
  NO  → handle inline
```

Concrete triggers:
- Research / exploration (investigating an unfamiliar API, reading docs)
- Parallel workstreams that don't share state (two independent features)
- Large file analysis where only the summary matters to the main task
- Experimental spikes ("try approach A, report back findings")

### 2.2 One focused mission per subagent

Each subagent gets exactly one clearly scoped mission. Bad scope examples:
- "Research auth and also look at the DB schema and check the logs" ❌

Good scope examples:
- "Find all places where `userToken` is read or written. Return a list of
  file paths and line numbers only." ✅
- "Read the Stripe webhook docs and summarize the 3 event types we need
  for subscription management." ✅

### 2.3 Subagent output contract

Tell the subagent exactly what to return:
```
Return format: [bullet list / JSON / file path list / single paragraph]
Max length: [N lines / N tokens]
Include: [what matters]
Exclude: [what doesn't]
```

Subagents that return unstructured walls of text are wasted compute.

---

## 🔁 3. SELF-IMPROVEMENT LOOP

### 3.1 When to update lessons

Update `tasks/lessons.md` after:
- Any correction from the user (explicit or implicit)
- A mistake you catch yourself before the user does
- A plan that failed and required re-planning
- A verification step that revealed a bug in your own work

### 3.2 Lesson format

Every lesson must follow this exact structure:

```markdown
## LESSON-<NNN>: <short title>
**Triggered by:** <what caused this lesson — one sentence>
**Mistake pattern:** <what went wrong or nearly went wrong>
**Root cause:** <why it happened — be honest>
**Rule:** <the concrete preventive rule, written as an imperative>
**Verification:** <how to confirm the rule was applied>
**Date:** YYYY-MM-DD
```

Example:
```markdown
## LESSON-007: Don't mutate shared state in parallel subagents
**Triggered by:** Two subagents wrote to the same config file simultaneously
**Mistake pattern:** Assumed subagents had isolated file system views
**Root cause:** Did not check for shared state before parallelizing
**Rule:** Before spawning parallel subagents, explicitly list shared resources.
          If any resource is shared, serialize the agents or assign ownership.
**Verification:** Shared resource list reviewed before any parallel spawn
**Date:** 2025-01-14
```

### 3.3 Lessons are binding rules

Lessons are not suggestions. Once written, treat every lesson as a hard
constraint. At session start, if a task would violate a lesson, flag it before
starting, not after.

### 3.4 Lessons audit

Every 10 lessons, review the list:
- Merge lessons that cover the same root cause
- Promote the 3 most-violated lessons to the top of the file as CRITICAL
- Archive lessons that no longer apply (mark as `[ARCHIVED]`, don't delete)

---

## ✅ 4. VERIFICATION PROTOCOL

### 4.1 Verification is mandatory — no exceptions

A task is not done until you have proof it works. "It looks right" is not proof.

| Work type | Minimum verification |
|-----------|---------------------|
| Code change | Tests pass + build passes + manual smoke test |
| Bug fix | The specific bug no longer reproduces |
| Refactor | Behavior is identical before and after (diff the outputs) |
| API change | Contract tests pass; no downstream callers broken |
| DB change | Migration runs clean; rollback runs clean |
| Config change | App starts and health check passes |
| Dependency change | Full test suite passes; no new audit warnings |

### 4.2 Verification commands

Always run and capture the output — do not assume:
```bash
# Confirm tests pass
<test command>

# Confirm build is clean
<build command>

# Confirm no regressions (if baseline exists)
git stash && <test command> > /tmp/before.txt
git stash pop && <test command> > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt
```

### 4.3 The staff engineer bar

Before marking complete, ask yourself these four questions:

1. **Correctness** — Does it handle the edge cases, not just the happy path?
2. **Simplicity** — Is this the simplest solution that solves the problem correctly?
3. **Maintainability** — Will the next developer understand this without asking you?
4. **Risk** — What's the worst-case failure mode, and is it acceptable?

If you can't answer all four confidently, it's not done.

---

## 💎 5. ELEGANCE STANDARD

### 5.1 When to pause and refactor

Pause and ask "is there a more elegant solution?" when:
- You've written the same logic twice
- A function exceeds ~40 lines
- You're passing more than 4 arguments to a function
- You're adding a special case to handle a new edge case
- The fix feels like duct tape on duct tape

Skip this check for: typo fixes, log message changes, simple config updates,
straightforward additions that don't touch existing logic.

### 5.2 The elegance test

If a fix feels hacky, apply this directive before presenting it:

> "Knowing everything I know now — the root cause, the constraints, the
> edge cases — implement the cleanest solution from scratch."

The first working solution is rarely the best one. The best solution is the one
that would survive a year of maintenance without needing a comment to explain it.

### 5.3 Simplicity rules

- Add no abstraction before there are at least 2 concrete use cases for it
- Prefer explicit over clever — clever code is a future bug
- Delete more than you add when possible
- If you added a dependency to solve a 10-line problem, reconsider

---

## 🐛 6. AUTONOMOUS BUG RESOLUTION

### 6.1 Given a bug report: act, don't ask

When given a bug report, log file, error message, or failing test:

```
1. Reproduce the failure yourself — confirm you can see it
2. Form a hypothesis about the root cause
3. Verify the hypothesis with evidence (logs, tests, code trace)
4. Fix the root cause — not the symptom
5. Verify the fix resolves the original report
6. Confirm no regressions introduced
7. Report back: root cause + fix + verification result
```

Do not ask the user how to fix it. Do not ask for more context unless you've
exhausted the available signals (logs, errors, tests, code). If you genuinely
need more information, ask one specific question — not a list.

### 6.2 CI failures

If CI is failing: read the CI logs, reproduce locally, fix, push. Do not
report the failure back to the user as a problem for them to solve. CI failures
are your responsibility to resolve.

### 6.3 Root cause discipline

Never fix a symptom. If fixing the symptom requires adding a guard clause
(`if (x === null) return`) without understanding why `x` is null, you haven't
fixed the bug — you've hidden it. Always trace to the origin of the problem.

---

## 📂 7. GIT DISCIPLINE

### 7.1 Branch strategy

```bash
# New feature or non-trivial change
git checkout -b <type>/<short-description>
# Types: feat, fix, refactor, chore, docs, test

# Examples
git checkout -b feat/user-authentication
git checkout -b fix/token-expiry-race-condition
git checkout -b refactor/payment-module-split
```

Never work directly on `main` or `master` unless explicitly told to.

### 7.2 Commit hygiene

- One logical change per commit (not one file, not one session — one *change*)
- Commit message format: **Conventional Commits**
  ```
  <type>(<scope>): <short imperative description>

  <optional body: what changed and why, not how>

  <optional footer: Closes #123, Breaking Change: ...>
  ```
- Examples:
  ```
  feat(auth): add JWT refresh token rotation
  fix(payments): prevent double-charge on network retry
  refactor(users): extract profile validation into service layer
  ```
- Never commit: debug logs, commented-out code, `.env` files, build artifacts

### 7.3 Before pushing

```bash
git diff main...HEAD          # review what you're about to push
git log main...HEAD --oneline # confirm commit messages are clean
<test command>                # confirm tests pass on the final state
```

---

## 📋 8. TASK MANAGEMENT

### 8.1 `tasks/todo.md` — the single source of truth

- One active task at a time documented here
- Mark items complete with `[x]` as you go — do not batch-complete at the end
- Never mark a task complete without the verification section filled in
- When starting a new task, archive the previous one (move to `tasks/archive/`)

### 8.2 `tasks/lessons.md` — the institutional memory

- Updated after every correction, failure, or near-miss
- Never truncated or overwritten — always append
- Reviewed in full at every session start
- CRITICAL lessons (top 3 most-violated) pinned at the top of the file

### 8.3 Communication cadence

At each meaningful step:
- **Starting a step:** one line — "Starting: [step name]"
- **Completing a step:** one line — "Done: [step name] — [what was confirmed]"
- **Blocked:** escalate immediately with context (see 1.3)
- **Task complete:** structured summary (see 8.4)

Do not produce status updates mid-step. Finish the step, then report.

### 8.4 Completion summary format

```
## ✅ Task Complete: <name>

**What was done:** <2-3 sentences>
**Verification:** <what was run and the result>
**Files changed:** <list>
**Lessons captured:** <LESSON-NNN title, or "none">
**Follow-up needed:** <any outstanding items or "none">
```

---

## 🧱 9. CORE PRINCIPLES (Non-Negotiable)

| Principle | Meaning in practice |
|-----------|---------------------|
| **Simplicity first** | Smallest change that correctly solves the problem. No gold-plating. |
| **Root causes only** | No symptom patches. Trace every bug to its origin. |
| **Minimal blast radius** | Touch only what the task requires. Don't refactor adjacent code "while you're there." |
| **No laziness** | No TODOs, no placeholder implementations, no "good enough for now." |
| **Prove it works** | Verification is not optional. Untested code is broken code. |
| **Lessons are law** | Every lesson in lessons.md is a hard rule. Violating one requires a new lesson explaining why. |
| **One thing at a time** | Don't start the next step until the current one is verified complete. |
| **Escalate early** | Stuck after two attempts = immediate escalation. Don't spiral. |

# Pre-Implementation Techniques (1–5)

Run these before writing code. Each technique closes a different class of unknowns. Stop after the one that answers your blocker.

---

## Technique 1: Blindspot Pass

**Why:** Unknown-knowns are invisible until you look for them. A checklist forced to your task type surfaces the tacit conventions everyone assumes but never writes down.

**When to skip:** The task is genuinely trivial (single-line fix, mechanical rename). Otherwise, run it.

**How it works:** Use the task-type-specific checklist below. Read each item; mark it as resolved, assumed, or escalated. An assumption is only safe if written down and checkable later.

**Artifact:** `blindspot-log.md` (only if it surfaces something actionable — if all items are trivial/resolved, skip the log).

### Blindspot Pass Checklist — Bug Fix

- [ ] **Reproduction.** Can you trigger the bug consistently? What are the exact steps, environment (Python 3.8+? Node 16+?), and data needed?
- [ ] **Call paths.** Grep all callers of the function you are about to patch. Is it called from one place or ten? High-call-volume functions need defensive guards, not single-site patches.
- [ ] **Data/env/version dependencies.** Does the bug appear only under specific conditions (low-memory, high-concurrency, particular OS, specific input encoding)?
- [ ] **Regression oracle.** How will you know the patch works and didn't break something else? What is the automated check (test, log message, metric)?

### Blindspot Pass Checklist — New Feature

- [ ] **Acceptance criteria.** When is this feature done? Who are the users? What does success look like, measured?
- [ ] **API contracts.** What are the inputs (parameters, data formats)? Outputs? Error modes? Backward compat — does this break existing code?
- [ ] **Permissions & gating.** Who can call this? Role-based, feature-flagged, admin-only, or public? Are there quotas?
- [ ] **Error states & migration.** When the feature fails, what error message does the user see? If this replaces an old feature, do old clients keep working?

### Blindspot Pass Checklist — UI/UX

- [ ] **Accessibility (WCAG):** Color contrast (4.5:1 minimum for text). Keyboard navigation (Tab, Enter, Escape, Arrow keys). Screen readers: heading hierarchy, alt text, aria-labels.
- [ ] **Responsive design.** 320px (mobile), 768px (tablet), 1024px (desktop), 1440px (wide). Does layout break? Do images stay proportional? Touch targets 44px minimum?
- [ ] **State variants.** Empty state (no data). Loading state (spinner/skeleton). Error state (error message, retry button). Success state. Does each read as intentional, not accidental?
- [ ] **Internationalization & long content.** Does the UI handle long strings (German compound words, Japanese characters, RTL text)? Truncation boundaries? Overflow?

### Blindspot Pass Checklist — Backend Optimization

- [ ] **Baseline measurement.** How slow is it now? Measure: response time (p50, p95, p99), throughput (requests/sec), resource cost (CPU %, memory, DB queries). Use a profiler.
- [ ] **Real bottleneck.** Is it the database, network, CPU, or disk? Grep for N+1 queries, missing indexes, unbounded scans. Don't guess.
- [ ] **Workload shape.** Is it a 1% slowdown or a 100x? Is it common or rare? Does it matter? (Optimizing a 10ms operation that fires once a day is YAGNI.)
- [ ] **Correctness under load.** Optimizations often break under concurrency. Does the change introduce races, deadlocks, or memory leaks? Test under realistic load.
- [ ] **Rollback & observability.** What metric or alert proves the optimization regressed, and how do we disable or roll it back?

### Copy-paste prompt

```
Run a blindspot pass for a [bug fix | feature | UI/UX | backend optimization] task:
[task description]

Use the task-type-specific checklist from finding-your-unknowns/pre-implementation.md.
Mark each item as resolved / assumed / escalated.
Write an assumption only if it is checkable (testable, measurable, or reviewable by code inspection).
If all items resolve cleanly, no log needed. If you surface assumptions or escalations, produce
a blindspot-log.md in docs/unknowns/<task-slug>/ with the structure:

## Questions
[Any ambiguity in the checklist?]

## Assumptions
[Each assumption: why you need it, how you'll verify it]

## Evidence
[Measured data, code excerpts, concrete examples]

## Decisions
[Any escalations or open questions? Status: resolved | pending | escalated]
```

---

## Technique 2: Brainstorm & Prototype

**Why:** When the architecture is open or the design direction is unclear, building quick variants surfaces real constraints before committing to one implementation.

**When to skip:** Architecture is locked. Spec is explicit. This is a bug fix with a clear target. Otherwise, brainstorm.

**How it works:** Generate 2–4 implemention directions (not 10). Build a minimal prototype for each (50–200 lines, throwaway). Implement just enough to surface trade-offs. Compare on: maintainability, performance, testing ease, future extensibility. Pick the winner. Throw away the losers.

**Artifact:** Prototype code (not committed; archive if needed for evidence, then discard). Optional: `brainstorm-log.md` if the comparison surfaced something worth documenting for the reviewer.

### Copy-paste prompt

```
Brainstorm and prototype implementations for [task description].

Generate 2-4 distinct approaches:
1. Approach A: [description, trade-off focus]
2. Approach B: [description, trade-off focus]
3. Approach C: [description, trade-off focus]

For each approach:
- Write a minimal prototype (50–200 LOC, throwaway).
- Evaluate on: (a) maintainability (how easy to read/modify?), (b) performance (measurable gain?), 
  (c) testing (testable? how many edge cases?), (d) future extensibility (can we add X later?).

Compare side-by-side. Pick one. Discard the others.

If the comparison surfaced a non-obvious trade-off, document it in docs/unknowns/<task-slug>/brainstorm-log.md:

## Approaches Considered
[Approach A: description, why rejected]
[Approach B: description, why rejected]
[Chosen: Approach C: rationale]

## Key Trade-off
[What was the deciding factor? Why did one win?]
```

---

## Technique 3: Interview Me

**Why:** A direct question often closes unknowns faster than speculation. Top-5 questions ranked by "impact-if-wrong."

**When to skip:** The task is trivial or the spec is explicit. Otherwise, ask.

**How it works:** Identify the top 5 questions where getting the answer wrong would send you in the wrong direction. Rank by impact. Ask them. Write the answers. Each answer becomes a checkpoint for implementation.

**Artifact:** `interview-log.md` (Q&A pairs; only if answers change your approach).

### Copy-paste prompt

```
Interview Me: Generate top-5 questions for this task [task description].

Rank by "impact-if-wrong": if the answer is wrong, how much rework do I face?

1. Question: [biggest impact]
   Impact if wrong: [redesign, full rewrite, minor adjustment?]
2. Question: [second biggest]
   Impact if wrong: [...]
... (top 5 only)

For each answer I provide, write a checkpoint: "Once this is known, we can proceed with [next decision]."
```

### Examples by task type

**Bug fix (impact = rework needed if you patch the wrong layer):**
1. Is the bug in the application code, the library, or the data?
2. Does this bug affect other users or just this scenario?
3. Can we ship a quick guard (defensive check) or do we need a redesign?

**Feature (impact = scope grows mid-task):**
1. Who owns the success metrics for this feature?
2. Is this feature-flagged from day one or enabled for all users?
3. What happens to old clients that don't know about this feature?

**Backend optimization (impact = measuring the wrong thing):**
1. What is the user-facing latency target?
2. Are we optimizing for throughput, latency, cost, or all three?
3. Do we have a/b test infrastructure to measure the real impact in production?

---

## Technique 4: References

**Why:** The unknown-unknown often hides in a place you didn't think to look: existing code, library docs, prior art, standards.

**When to skip:** Only after a quick search (codebase + installed dependencies) confirms no prior art exists. Never declare work novel from the prompt alone.

**How it works:** Search for existing implementations, library features, prior examples in the codebase, or standards that cover this. If found, read it. Adapt or reuse, don't reinvent. If not found, document the gap (design space is clear, not just dark).

**Artifact:** None, unless you discover something unexpected; then note it in implementation-notes.md.

### Copy-paste prompt

```
Find references for [task description].

Search order:
1. Existing code in this codebase: [grep for similar patterns, existing implementations]
   - Grep [function/module/pattern names]
   - Any existing [feature/optimization/UI pattern] we can adapt?
2. Library / framework docs: [for the language/framework in use]
   - Is there an official way to [do this thing]?
   - Do we have [dependency] already that can solve this?
3. Standards or best practices: [domain-specific references]
   - CDISC IG (clinical), WCAG (accessibility), OWASP (security), RFC (protocol), etc.
   - What does the standard say about [edge case]?

If findings change your approach, append them to docs/unknowns/<task-slug>/implementation-notes.md
(no separate artifact):

## References Found
- Source: [file/doc/standard], [key insight]
- Reusable: [yes, can adapt logic / no, but teaches us X / no, we're doing it differently and here's why]

## Gap Analysis
- If nothing found: What does "no reference" mean? Is the design space clear (we understand what to build) 
  or dark (we're guessing)?
```

---

## Technique 5: Implementation Plan

**Why:** Before writing code, outline the sequence of changes. Identify which decisions are most likely to need reversal. Flag unresolved items.

**When to skip:** This is a one-line fix or a trivial patch. Otherwise, plan.

**How it works:** List the changes you will make, in order. For each change, note whether it is reversible (easy to undo if wrong) or irreversible (needs a migration). Identify the critical-path changes that, if wrong, force a redesign. List unresolved items that might force changes.

**Artifact:** `implementation-plan.md` in `docs/unknowns/<task-slug>/`.

### Copy-paste prompt

```
Create an implementation plan for [task description].

Format:
1. [Change name]: [what you'll do]
   - Reversible: [yes | no]
   - Why: [brief rationale]
   - If wrong, cost: [redesign | full rewrite | minor fix | rollback in prod?]
2. [Next change]: [...]
   ... (order by likelihood-of-reversal: the decision most likely to be reversed comes first;
   flag the top 1-2 items most likely to change)

Unresolved items (things that might change the plan):
- Item: [decision not yet made], impact: [what breaks if we guess wrong]

Critical path (changes that, if wrong, force a redesign):
- Change: [X], because: [changing it later costs Y]

Dependencies:
- Change A depends on B because [reason]
```

### Example (TS feature — Express rate limiting), ordered by likelihood-of-reversal:

```
1. Choose rate-limit storage backend (Redis vs. in-memory)   [FLAGGED: most likely to reverse]
   - Reversible: no (if chosen wrong, migration required)
   - Why: Cross-server limits need shared state; single-instance deploys don't. Pending Interview Me.
   - If wrong, cost: Full rewrite or migration

2. Define rate-limit response contract (429 status, Retry-After header, error body)   [FLAGGED: likely to change]
   - Reversible: partly (clients may already depend on the shape once shipped)
   - Why: Clients need a stable contract; changing it later breaks integrations.
   - If wrong, cost: Redesign + client coordination

3. Decide route scope (all routes vs. /api/* vs. per-endpoint limits)
   - Reversible: yes (middleware mount point is a config change)
   - Why: Blanket limits are simplest; per-endpoint quotas can come later.
   - If wrong, cost: Minor fix

4. Implement middleware + tests for boundary cases (hitting limit, reset window)
   - Reversible: yes
   - Why: Core logic; straightforward once 1-3 are settled.
   - If wrong, cost: Test-only or minor fix

Unresolved:
- Storage backend (pending Interview Me). Impact: Steps 2-4 depend on it.

Critical path:
- Step 1: Choosing the wrong backend forces a redesign.
```

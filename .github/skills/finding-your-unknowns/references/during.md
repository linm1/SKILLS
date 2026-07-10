# During Implementation: Technique 6 (Implementation Notes)

Implementation Notes are an append-only log of decisions made during coding. You write an entry each time you make a choice the spec didn't make for you — a trade-off, an edge-case call, an assumption you're betting on. Each entry is structured so a reviewer can understand why you chose A over B without asking.

## When to write an entry

Write when:
- The spec is ambiguous and you chose an interpretation.
- You discovered a constraint or edge case the pre-implementation phase didn't catch.
- You chose A over B for non-obvious reasons (performance, maintainability, compatibility).
- You wrote a workaround or a defensive guard that wasn't in the plan.
- You realized mid-task that an assumption was wrong, or a decision needs reversing.

Do **not** write for every line of code. Implementation Notes are not a code log. They are decision evidence.

## Entry format

Each entry in `docs/unknowns/<task-slug>/implementation-notes.md`:

```markdown
### [Timestamp] — [Decision name / Which part of the code]

**Decision:** [What you chose to do]

**Why the spec didn't cover it:** [Ambiguity, edge case, or missing requirement]

**Alternative considered:** [What you chose not to do, and why]

**Evidence:** [Measurement, code excerpt, test result, log snippet]

**Status:** [resolved | pending | escalated]
```

## Examples

### Bug fix

```markdown
### 14:30 — Where to patch refresh_session()

**Decision:** Added a guard at the call site (auth/session.py:42) instead of inside refresh_session().

**Why the spec didn't cover it:** Grep found 8 callers of refresh_session(). Patching inside would affect all of them, 
but the bug report described only one scenario. A defensive guard at the call site catches the specific case without 
risking side effects on other callers.

**Alternative considered:** Patching inside refresh_session() (catches all cases automatically, but risks breaking 
other call paths). Decided against: the bug is environment-specific (low-memory); patching globally could hide other issues.

**Evidence:** 
- Grep: refresh_session() called from [routes.py:1, api.py:5, scheduled.py:3, tests.py:xxx, ...]
- Reproduction: bug only under load (< 50MB available); normal operation OK. Guard checks available memory before calling.
- Test: Added test_refresh_session_low_memory() confirming guard prevents the crash.

**Status:** resolved
```

### Feature

```markdown
### 09:15 — Rate-limit storage: Redis vs. in-memory

**Decision:** Chose Redis (separate service) over in-memory map.

**Why the spec didn't cover it:** Interview Me identified storage as the critical unknown. Spec said "rate limit requests" 
but not how to track state across servers.

**Alternative considered:** In-memory map per server instance (simpler, but limits don't cross servers; users on different 
instances get independent quotas). Redis (cross-server, but adds dependency).

**Evidence:** 
- Deployment: multi-instance setup (3+ servers behind load balancer). In-memory tracking fails: User A on server 1 gets 
  10 requests, load balancer routes next request to server 2, which has no state for User A. Limit resets. User can exceed quota.
- Interview Me answer: "Cross-server rate limits are required."
- Test: test_rate_limit_multi_instance() confirms Redis enforces global limit.

**Status:** resolved
```

### Backend optimization

```markdown
### 11:45 — Query N+1: single loop vs. batch fetch

**Decision:** Refactored loop to batch-fetch all IDs before the main loop. Query count: ~1000 down to ~2.

**Why the spec didn't cover it:** Baseline measurement revealed N+1 queries (one SELECT per item). Optimization plan 
noted it as a risk but didn't prescribe the fix.

**Alternative considered:** 
1. Keep loop, add caching layer (Redis). Pro: minimal code change. Con: stale cache risk, added infrastructure cost.
2. Batch fetch all (chosen). Pro: no cache invalidation, guarantees freshness, simplest. Con: requires refactor.

**Evidence:** 
- Before: baseline = 2.3s p95 with 1000 items (1001 queries to DB)
- After: 0.12s p95 (2 queries: 1 fetch all IDs, 1 join). Measured with perf profiler (py-spy).
- Test: test_performance_batch_vs_loop() asserts query count == 2.

**Status:** resolved
```

### UI/UX

```markdown
### 16:20 — Empty state messaging

**Decision:** Showed a clear empty state with icon + "No projects yet" + call-to-action button 
instead of just an empty grid.

**Why the spec didn't cover it:** Blindspot Pass flagged empty state as mandatory but didn't specify messaging. 
User testing (informal) showed empty grid is confusing — users thought the app was broken.

**Alternative considered:** 
1. Hide the section entirely (might confuse users who expect a projects area). Con: navigation changes.
2. Show a pale placeholder grid (subtle, but looks like a loading state bug). Con: accessibility, confusion.
3. Chosen: explicit messaging. Pro: clear intent, accessible, actionable.

**Evidence:** 
- A/B test result (small cohort): users with messaging 0 clicks to support; users with empty grid 3x support questions about missing projects.
- WCAG audit: icon + text passes contrast. Alt text on icon. Button has clear focus state.

**Status:** resolved

**Pending:** Verify i18n for all supported languages (German translation of "No projects yet" in progress).
```

## Appending to the log

As implementation proceeds, append entries. Use timestamps or section numbers to maintain order. When status changes (pending → resolved, or resolved → escalated), update the entry in place. Reviewers read top-to-bottom to see the decision thread.

## Reviewing Implementation Notes

A reviewer uses these entries to:
1. Understand why you chose A over B without re-reading code.
2. Challenge assumptions: "Did you measure that?" → Evidence section shows measurement or admits you didn't.
3. Catch missed edge cases: "What about...?" → If not in the log, it wasn't considered; log it now.
4. Trace reversals: If a status is "escalated," the reviewer knows the change might need redesign.

Strong implementation notes make code review fast and thorough.

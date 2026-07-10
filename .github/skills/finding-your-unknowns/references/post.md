# Post-Implementation Techniques (7–8)

Run these before merge. They ensure the reviewer can understand what changed and why, and that you've considered the risks.

---

## Technique 7: Explainer

**Why:** A reviewer reading your code without context often misses intent. An Explainer translates the code changes into a narrative: what changed, why, what stayed, what remains uncertain.

**When to skip:** Trivial patches (typo fixes, single-line safe changes). Otherwise, write.

**How it works:** Write an explainer document as if you're briefing a colleague. Structure: what changed / why / what stayed / open risks. For bug fixes, frame as "root cause" (prove the bug was in X, not Y). For features, frame as "pitch" (here's what users can do now). Keep it tight: 200–500 words.

**Artifact:** `explainer.md` in `docs/unknowns/<task-slug>/`.

### Explainer template — Bug fix (root-cause framing)

```markdown
# [Bug title]

## What changed
[1–2 sentences: what code was modified and where]

## Root cause
[Why did the bug happen? What assumption was wrong?]
- Original code at [file:line]: [code snippet]
- Assumption: [what the code assumed]
- Reality: [what actually happened under condition X]

## Fix
[How does the new code prevent the bug?]
- New code at [file:line]: [code snippet]
- Guard: [what check was added?]
- Effect: [what prevents the bug now?]

## Testing
- Reproduction case: [how to trigger the bug; test shows it fails before patch, passes after]
- Regression guard: [what keeps this from breaking again?]
- All callers checked: [yes/no; if yes, link to grep or trace]

## What stayed the same
[What did not change? Why is this OK?]
- [behavior X still works because...]

## Open risks
[What could go wrong? What couldn't we test?]
- Risk: [description]
- Mitigation: [how we'll catch it if it surfaces in production]
```

### Explainer template — Feature (pitch framing)

```markdown
# [Feature name]

## What users can do now
[1–2 sentences: the user-facing capability]

## What changed
[Architecture/code changes required to enable it]
- New endpoint/component/system: [description]
- Modified systems: [list + brief impact]
- Data model: [if applicable; schema/migration summary]

## API / interface contract
- Inputs: [parameters/formats]
- Outputs: [success response + error responses]
- Rate limits / quotas: [if applicable]
- Backward compat: [does this break existing clients?]

## Why this design
[Key trade-off decisions + alternatives considered]
- Storage backend: chose Redis because [rationale]
- Sync vs. async: chose async because [rationale]

## Testing
- Unit: [coverage %, test count]
- Integration: [key flows tested]
- E2E: [user journey tested]
- Edge cases: [boundary conditions verified]

## What stayed the same
[Related features that still work unchanged]
- Feature X still behaves as before because [reason]

## Open risks / future work
- Migration path if storage backend changes
- Performance under [high-load scenario] untested; needs load test post-launch
- [Feature flag strategy if a rollback is needed]
```

### Explainer template — UI/UX (capability + accessibility framing)

```markdown
# [UI feature name]

## What users see
[1–2 sentences + screenshot/sketch if helpful]

## Changes
- New component: [component name, structure]
- Modified views: [list of affected pages/states]
- Styling: [token/system changes, if any]

## Accessibility & responsive
- WCAG compliance: [level AA, tested with NVDA/JAWS/screen reader]
- Keyboard support: [Tab/arrow/Enter/Escape behavior]
- Responsive: tested on [320, 768, 1024, 1440]px; all states responsive
- States: empty, loading, error, success all visually distinct and labeled

## Internationalization
- Long text handling: [truncation, wrapping]
- RTL support: [yes/no; if yes, tested]
- Character sets: [tested with German, Japanese, emoji, etc.]

## Browser support
- Tested: [Chrome, Firefox, Safari, Edge]
- Fallbacks: [for older browsers, if applicable]

## Testing
- Visual regression: [automated screenshots on key breakpoints]
- Interaction: [manual test of all states and transitions]
- Performance: [LCP, CLS impact measured]

## What stayed the same
- Other components on this page remain unchanged
- Existing user journeys not affected because [reason]

## Open risks
- Dark mode untested (manual test needed)
- [Specific browser/device where edge case might exist]
```

### Copy-paste prompt

```
Write an explainer for this work:

Task: [bug fix | new feature | UI/UX change | optimization]
[task description]

Use the template for your task type (see finding-your-unknowns/post.md).

Structure:
1. What changed (code/UI)
2. Why (root cause / design rationale / pitch)
3. What stayed (no-change impacts)
4. Open risks (things we can't guarantee)

Keep it 200–500 words. Assume the reviewer has not read your implementation notes or code yet.
Write for clarity, not completeness.

Save to docs/unknowns/<task-slug>/explainer.md.
```

---

## Technique 8: Quiz Me

**Why:** Before merge, the reviewer needs to verify they understand the change. A quiz with 3–5 questions, ranked by "if you answer wrong, the merge fails," ensures the reviewer can explain the change to someone else.

**When to skip:** Trivial patches (typo fix, one-liner safe change). Unless it touches shared code, auth, money, or concurrency — then always quiz.

**How it works:** Generate 3–5 comprehension questions about the change. Rank by "impact if the reviewer can't answer." Each question must be answerable from code + implementation notes + explainer; if a reviewer can't answer, something's missing in the artifact. The reviewer must be able to fail (give a wrong answer) and have the work sent back.

**Artifact:** None kept. The quiz is throwaway: run it inline in the conversation or PR review thread (or a scratch/temp file if you need to draft it), then discard. Never place it in `docs/unknowns/<task-slug>/` and never commit it.

### Quiz question examples

#### Bug fix
- Q: What is the root cause of the bug? (Reviewer should name the wrong assumption, not just describe symptoms.)
- Q: Which call paths are affected, and why doesn't this fix break the others?
- Q: If we didn't apply this guard, what would happen under [edge case]?
- Q: How would a regression in this fix look in production? What metric would alert us?

#### Feature
- Q: Why did you choose Redis over in-memory storage? What breaks if we switch?
- Q: What happens when the rate-limit storage is unavailable? (Should have a fallback or graceful degradation.)
- Q: A user tries to do [specific action]. Walk through the code path from request to response.
- Q: Is this feature backward-compatible? Can an old client still work?

#### UI/UX
- Q: A user on a 320px screen tries to [task]. Show me where they click and what they see.
- Q: What does the empty state look like, and why is it better than [alternative]?
- Q: Can a user navigate this using only keyboard? Walk through Tab order and interaction keys.
- Q: Does this work with a screen reader? What does a user with visual impairment hear?

#### Backend optimization
- Q: What was the bottleneck? Prove it with data (baseline measurement).
- Q: Did you measure the improvement? What changed from before to after?
- Q: What's the risk this optimization introduces? (Concurrency? Cache invalidation? Correctness edge case?)
- Q: Under what conditions might the optimization fail or regress?

### Quiz template

```markdown
# Quiz Me — [Feature/fix/UI]

Before merging, the reviewer should be able to answer these questions.
If they can't, or if they answer wrong, send the work back.

## Question 1 (Must-pass)
**Q:** [Understanding question; reviewer must nail the core insight]

**Expected answer:** [One-sentence proof of understanding]

**If wrong:** [What this error reveals about the implementation]

---

## Question 2
**Q:** [Trade-off or design choice]

**Expected answer:** [Rationale + alternative considered]

**If wrong:** [What gets missed if the reviewer doesn't understand this]

---

## Question 3
**Q:** [Boundary case or edge case]

**Expected answer:** [Specific behavior under the edge case]

**If wrong:** [What risk goes unmitigated if the reviewer misses this]

---

[Additional questions as needed]
```

### Copy-paste prompt

```
Generate a Quiz Me for this change:

Task: [description]
Core changes: [what code was modified]

Generate 3–5 questions. Rank by "impact if the reviewer answers wrong."

Use the template from finding-your-unknowns/post.md:

1. Must-pass question (core insight)
2. Trade-off question (why did you choose A over B?)
3. Edge-case question (boundary condition)
4. [Optional] Risk question (what could break?)
5. [Optional] Backward-compat question (does this break existing code?)

For each question:
- Write the question (answerable from code, explainer, and implementation notes)
- Write the expected answer (one sentence minimum)
- Write what an incorrect answer reveals (what the reviewer missed)

Present the quiz inline (conversation or PR review thread); do not save it to docs/unknowns/ or commit it. Discard after code review.
```

### Using Quiz Me in code review

1. **Before merge**, the author sends `explainer.md` and `implementation-notes.md` to the reviewer (or includes links in the PR description), and posts the quiz questions inline in the PR review thread or conversation.
2. **Reviewer answers first** from the explainer and implementation notes, then verifies those answers against the code. This is a sequencing rule, not a ban on reading code — answering from the artifacts first exposes gaps in them.
3. **If the reviewer answers all questions correctly**, they understand the change well enough to merge.
4. **If the reviewer struggles or answers wrong**, they ask the author for clarification. The question points to what's missing in the artifacts.
5. **Author revises** the artifacts or the code, and the quiz is re-attempted. (This is not punishment; it's a check that understanding is real, not accidental.)

Strong quiz makes strong reviews: reviewers who can't explain the change shouldn't merge it.

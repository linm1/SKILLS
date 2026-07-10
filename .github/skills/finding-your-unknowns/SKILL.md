---
name: finding-your-unknowns
description: Surface gaps between your specification and the real codebase before a capable model guesses confidently and derails a long task. Use when starting a bug fix (need repro + call paths + regression guard), scoping a feature (acceptance criteria + API contracts), tackling underspecified UI/UX (accessibility + responsive + state variants), tuning backend (baseline first, not blind optimizing), mid-task when "the spec didn't say what to do here" or "I realize I'm missing something", or pre/post-merge when asked to "quiz me on this change", "write an explainer", or "before merging, check my understanding". Eight techniques — pre-implementation (Blindspot Pass, Brainstorm & Prototype, Interview Me, References, Implementation Plan), during (Implementation Notes), post-merge (Explainer, Quiz Me) — stop after the first one that resolves the blocking uncertainty. Read the matching reference file for technique instructions.
---

# Finding Your Unknowns

The gap between a specification (your prompt/brief) and the real codebase (the territory) is made of unknowns. When unknowns go unspoken, a model guesses — and more capable models guess with higher confidence, burying wrong assumptions deep in the work. This skill systematically surfaces unknowns before edits, during implementation, and before merge, so guesses become decisions and decisions become traceable.

## Four unknown types

The types repeat across all domains: clinical programming, backend optimization, UI/UX, bug fixes. Each surfaces differently.

| Quadrant | What it is | How to surface it |
|---|---|---|
| Known knowns | What the spec says explicitly | State it directly |
| Known unknowns | Ambiguities you can already see | Ask explicit questions (Interview Me) |
| Unknown knowns | Tacit conventions — everyone assumes them, never write them down | Run the Blindspot Pass checklist (task-type specific) |
| Unknown unknowns | Edge cases, data surprises, things nobody considered | Profile data, test boundaries (References, Implementation Notes) |

## Before you run a technique: risk gate

Classify the task before diving in. Trivial changes skip artifacts entirely.

| Gate | Signal | Workflow |
|---|---|---|
| **Skip** | Mechanical rename, typo fix, single-line code change with no ambiguity | Just do it, no artifacts |
| **Quick pass** | One blocking unknown you can already name | Run only the technique that resolves it, skip the rest |
| **Full workflow** | Complex task, architecture open, high stakes | Use the mapping table below; stop after the first technique that resolves a blocker |

**Escalators to full workflow** (bypass the quick pass):
- Small bug fix touching shared helpers, auth, money, or concurrency → full
- "Simple performance speedup" without a measured baseline → full
- UI tweak that feels visual-only → full (a11y/responsive/states always apply)

## Task-type × technique mapping

This table shows whether each technique applies. Find your task type; read down. **High** = standard play for this type. **Situational** = use if that unknown matters for your task. **Skip** = usually not needed. Stop after the first technique that answers a blocker.

| Technique | Bug fix | New feature | UI/UX | Backend opt |
|---|---|---|---|---|
| Blindspot Pass | High | High | Situational | High |
| Brainstorm & Prototype | Skip | High if architecture open | High | Situational |
| Interview Me | Situational | High | High | Situational |
| References | High | High | High | Situational |
| Implementation Plan | Skip | High | High | High |
| Implementation Notes | High | High | Situational | High |
| Explainer | Situational | High | High | High |
| Quiz Me | Skip unless shared-code fix | High | Situational | High if critical path |

## Required probes per task type

These are non-skippable regardless of gate level. They are not techniques; they are hygiene.

| Task type | Mandatory before any edit |
|---|---|
| **Bug fix** | Reproduce the bug. Grep all callers of the function you're patching. Find the regression oracle (how to know it broke). |
| **Backend optimization** | Measure the baseline first. Prove the bottleneck exists, measure it. Then optimize. |
| **UI/UX** | Accessibility (WCAG), responsive breakpoints (320, 768, 1024, 1440), empty/loading/error state variants. Never optimize visuals alone. |
| **Feature** | Acceptance criteria (what does done look like?). API contracts (inputs, outputs, errors). Migration/compat (backwards compatibility if this is a breaking change?). |

## Stop-early rule

Once a technique resolves the blocking uncertainty, stop. Running all eight by default is this skill's own failure mode. Each technique closes unknowns; once you have an answer, move to implementation. This rule scopes to the exploratory (pre-implementation) techniques for the current blocker — for complex work, Explainer + Quiz Me still run before merge (see guardrails).

Stop per blocker, not after the first artifact. An item marked assumed, pending, or escalated is still unresolved. Route it once to the smallest matching technique: an open design or architecture choice to Brainstorm & Prototype; a stakeholder or API contract to Interview Me; missing prior art to References; a multi-step or costly-to-reverse change to Implementation Plan. Then stop as soon as implementation can proceed without a hidden bet.

For complex feature, UI/UX, or backend work, write the Implementation Plan before edits once discovery identifies more than one change or a costly-to-reverse decision. Brainstorm & Prototype compares approaches; it does not replace the plan.

## How to run a technique

Each of the eight techniques lives in a reference file. When you decide to run one:

1. Find your stage: **pre-implementation** (Blindspot Pass, Brainstorm & Prototype, Interview Me, References, Implementation Plan), **during** (Implementation Notes), **post** (Explainer, Quiz Me).
2. Open the matching reference file (`references/<stage>.md`).
3. Read the section for your technique.
4. Copy the prompt block or checklist; adapt it to your task.
5. Produce the artifact specified.

Progressive disclosure: SKILL.md points; references have the detail.

## Artifact conventions

All unknowns work lives in `docs/unknowns/<task-slug>/` where `<task-slug>` is kebab-case branch name or ticket ID. Create the directory if absent. Files inside:

- **implementation-plan.md** (standard output of the Implementation Plan technique)
- **implementation-notes.md** (append-only log, written during implementation)
- **explainer.md** (written near merge, for the reviewer)
- **blindspot-log.md**, **interview-log.md**, **brainstorm-log.md** (optional; only if they surfaced something actionable)

Throwaway artifacts — prototype variants and quiz-me transcripts — are never committed and never placed in `docs/unknowns/`; discard them after use.

Structure all multi-section notes as:
```
## Questions
- What is X?
- Can Y happen?

## Assumptions
- Assuming X means Y
- Assuming Z is backwards-compatible

## Evidence
- Measured baseline: X ms
- Grepped callers: found Y in module Z

## Decisions
- Chose A over B because C (status: resolved | pending | escalated)
```

Update status as items move: a question becomes a decision once resolved; an assumption becomes evidence once checked; a decision becomes blocked if evidence contradicts it.

## Cross-reference: clinical programming

If you are performing clinical trial QC, refer to `qc-clinical-programming` skill — it uses the same four-quadrant unknown-mapping framework and integrates with this skill's techniques. The two skills read as one family; they are not duplicates.

## Working with other skills

- **Brainstorm & Prototype** and **Writing Plans**: If you have already invoked `superpowers:brainstorming` or `superpowers:writing-plans`, defer to it; do not re-brainstorm.
- **Code review**: This skill surfaces unknowns *before* edits. After editing, use the code-reviewer agent.
- **Specific domains**: For SAS programming, refer to domain skills; for TypeScript/Python idioms, use language reviewers.

## Agent guardrails

- Do not invent requirements, acceptance criteria, API contracts, or bottlenecks. If absent, mark as unknown and ask.
- Do not skip the mandatory probes for your task type. They are not optional.
- Do not run all eight techniques by default. Stop after the first one that resolves a blocker.
- Do not treat the risk gate as a speed bump. It is the filter: trivial changes skip artifacts; medium changes use one technique; complex changes use the mapping table.
- Do not merge without the artifacts. Explainer + Quiz Me are the merge gate for complex work.

---

**Based on "A Field Guide to Fable: Finding Your Unknowns" by Thariq Shihipar (Anthropic), July 2026.**

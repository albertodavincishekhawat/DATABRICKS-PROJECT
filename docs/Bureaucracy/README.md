# Bureaucracy — Document Governance

This folder governs the full document hierarchy for this project.

Every document that gets written is registered here first — its purpose, its required sections, the rules for writing it, and how it connects to the next document. No document is created without an entry here. No code is written without the relevant document being in **Accepted** status.

---

## 1. Why This Folder Exists

Professional software is built twice — once in documents, once in code. The documents come first. They force clarity on what is being built before time is spent building it. When a decision changes, the document changes first. The code follows. This folder defines the rules for that process.

---

## 2. The Document Hierarchy

Documents are written in a strict sequence. Each document depends on the one above it being locked before it can be written. The arrow means "must be accepted before writing the next one."

```
PRD  →  ADR-000  →  SAD  →  ADR-001 to ADR-006  →  ROADMAP
```

| # | Document | File Path | Purpose | Status |
|---|----------|-----------|---------|--------|
| 1 | **PRD** — Product Requirements | `docs/PRD.md` | Defines the business problem, the user, and what success looks like. Written in plain English. Zero technology. | **Accepted** |
| 2 | **ADR-000** — System Specification | `docs/adr/ADR-000-system-specification.md` | The engineering contract. Exact rules, data requirements, output requirements. Technology-agnostic. | **Accepted** |
| 3 | **SAD** — Solution Architecture | `docs/SAD.md` | The full architecture. Technology stack, component design, data flow, infrastructure. Technology choices are made here for the first time. | **Draft** |
| 4 | **ADR-001** — Data Collection Architecture | `docs/adr/ADR-001-data-collection-architecture.md` | Decision: how data is collected — scraper notebooks in Databricks, DBFS landing zone, refresh schedule, failure handling | To be written |
| 5 | **ADR-002** — Data Storage Strategy | `docs/adr/ADR-002-data-storage-strategy.md` | Decision: DBFS + Delta Lake medallion (Bronze/Silver/Gold), schema design, partitioning strategy | To be written |
| 6 | **ADR-003** — Decision Engine Implementation | `docs/adr/ADR-003-decision-engine-implementation.md` | Decision: rule engine as a Databricks Gold notebook, output schema, historical states computation | To be written |
| 7 | **ADR-004** — Orchestration Platform | `docs/adr/ADR-004-orchestration-platform.md` | Decision: Databricks Jobs (multi-task, weekly cron), task dependencies, failure handling | To be written |
| 8 | **ADR-005** — Data Quality & Synchronisation | `docs/adr/ADR-005-data-quality-synchronisation.md` | Decision: freshness SLAs per parameter, stale data guard, handling late-published sources (CPI, FII) | To be written |
| 9 | **ADR-006** — Deployment & Environments | `docs/adr/ADR-006-deployment-environments.md` | Decision: dev/UAT/prod separation within Databricks Community Edition, GitHub branch strategy | To be written |
| 10 | **ROADMAP** — Implementation Roadmap | `docs/ROADMAP.md` | Phases of development. What gets built in each phase, in what order, and what each phase unlocks. | To be written |

---

## 3. Writing Order and Dependencies

Documents must be written in this exact sequence. Writing out of order produces documents that contradict each other.

| Step | Write | Dependency | Why you cannot skip ahead |
|------|-------|------------|--------------------------|
| 1 | PRD | None — start here | Every other document answers to the PRD. Without it, you do not know who the user is or what success means. |
| 2 | ADR-000 | PRD accepted | ADR-000 translates the business requirements from the PRD into engineering requirements. It cannot be written until the business problem is locked. |
| 3 | SAD | ADR-000 accepted | The SAD makes technology choices. Those choices must satisfy the requirements in ADR-000. If ADR-000 is still changing, the SAD will contradict it. |
| 4 | ADR-001 to ADR-006 | SAD accepted | Each ADR justifies one decision that was made in the SAD. They cannot be written before the SAD defines what decisions were made. |
| 5 | ROADMAP | All ADRs accepted | The implementation sequence only becomes clear once the full architecture is settled. A roadmap written before the architecture will be rewritten. |

---

## 4. How to Write Each Document

### PRD — Product Requirements Document

**Language**: Plain English. A non-technical stakeholder must be able to read and approve it.

**Must contain**:
- Problem statement — one paragraph, the business problem in plain language
- The user — who uses this system, what they know, what they do not want to think about
- What the system must do — a numbered list of functional requirements
- What the system must not do — explicit exclusions (scope boundary)
- Success criteria — how do we know the system is working correctly? Measurable outcomes only.
- Constraints — things that cannot be changed (e.g. free data sources only, no broker API)

**Must not contain**: Technology names, programming languages, infrastructure choices, implementation details.

**Ready when**: A business stakeholder can read it, confirm it matches their intent, and sign it without asking clarifying questions.

---

### ADR-000 — System Specification

**Language**: Precise English with tables and formulas. An engineer must be able to implement from it without asking questions.

**Must contain**:
- Problem statement (engineering version of the PRD problem)
- Actors — who and what interacts with the system (inputs and consumers of outputs)
- System boundary — hard fence: what is in scope and what is explicitly out of scope
- Business rules — the invariants (rules R1–R7 written as requirements, not pseudocode)
- Data requirements — what data flows in: field names, units, frequency, freshness SLA
- Output requirements — what the system produces: format, fields, delivery
- Success criteria — measurable definition of correct behaviour
- Quality attributes — reliability, cost, auditability, reproducibility requirements
- Assumptions — what must remain true for this spec to hold
- Constraints — non-negotiable boundaries
- Open questions — what must be resolved before implementation starts

**Must not contain**: Technology names, library names, infrastructure choices, code or pseudocode.

**Ready when**: An engineer can implement the system without asking "but what should happen when...?" for any scenario covered by the rules.

---

### SAD — Solution Architecture Document

**Language**: Technical but justified. Every technology choice must have a reason.

**Must contain**:
- Executive summary — one page: what is being built, for whom, and the full technology stack in one view
- Architecture diagram — every component, every data flow, every integration point
- Technology stack — for each layer: what technology, why that technology, what was rejected and why
- Component design — per component: what it does, its inputs, its outputs, its failure behaviour
- Data flow — how data moves through the system end to end, with format at each boundary
- Infrastructure — where each component runs, estimated cost, scaling approach
- Security — who can read and write what, how credentials are managed
- Open questions resolved — every open question from ADR-000 must be answered here

**Must not contain**: Business requirements (those are in ADR-000 and PRD). Implementation code.

**Ready when**: A developer can read it and know exactly what to build without architecture questions. A new team member can onboard from it alone.

---

### ADRs — Architectural Decision Records (ADR-001 to ADR-006)

**Language**: Direct and decisive. State the decision clearly, then justify it.

**Must contain** (use the template in Section 7):
- Context — why this decision was needed
- Decision — one paragraph stating exactly what was decided
- Rationale — why this option and not the alternatives
- Alternatives considered — what else was evaluated and why each was rejected
- Consequences — positive and negative outcomes of this decision
- Open issues — what remains unresolved after this decision

**Must not contain**: Business requirements (those are in ADR-000). Implementation code. Decisions that belong in a different ADR.

**Ready when**: A developer can read it, understand exactly why the technology was chosen, and implement accordingly. If a new option emerges in the future, the ADR provides enough context to evaluate whether switching is worth the cost.

---

### ROADMAP — Implementation Roadmap

**Language**: Clear, milestone-driven. No ambiguity about what is in each phase.

**Must contain**:
- Phase list — numbered phases with a one-line goal for each
- Per-phase deliverables — exactly what is produced at the end of each phase (runnable code, not just tasks)
- Dependencies — what each phase requires from previous phases
- Verification — how each phase is validated before the next begins
- Open issues — any outstanding decisions that will affect the roadmap

**Must not contain**: Technology decisions (those are in ADRs). Business requirements (those are in ADR-000 and PRD).

**Ready when**: A developer knows exactly what to build first, why that order, and how to verify they are done before moving on.

---

## 5. How to Use Documents to Drive Development

This project follows **spec-driven development**. The rules are:

**Rule 1: Documents before code.**
No code is written before the document that specifies it is in Accepted status. Writing code against a Draft document wastes the code when the document changes.

**Rule 2: Documents win.**
If code contradicts a document, the code is wrong. The document is the truth. Fix the code, not the document — unless the document itself has a bug, in which case raise it explicitly and update the document first, then the code.

**Rule 3: Every PR references its spec.**
Every pull request includes a reference to the section of the document it implements. This keeps code and documentation in sync and makes review faster.

**Rule 4: Decisions live in ADRs, not in commit messages.**
When a technical choice is made, it is written as an ADR. Commit messages describe what changed. ADRs describe why the approach was chosen. Both are required.

**Rule 5: Change the document before changing the code.**
When a requirement changes, update the relevant document first. Get it reviewed. Then update the code. This prevents undocumented drift between what the system does and what it is supposed to do.

**Rule 6: The ROADMAP is the only place where sequencing is decided.**
Do not decide what to build next in conversation or in a ticket. If the order needs to change, update the ROADMAP. This keeps the build sequence visible to everyone.

---

## 6. Document Status Lifecycle

Every document in this project has one of four statuses:

```
Draft  →  In Review  →  Accepted  →  Superseded
```

| Status | Meaning | What can happen next |
|--------|---------|---------------------|
| **Draft** | Being written, not yet ready for review | Author continues writing; no implementation against it |
| **In Review** | Complete enough to be reviewed; open for comments | Reviewer raises issues; author resolves them |
| **Accepted** | Reviewed, agreed upon, locked | Implementation can begin; changes require a new Draft cycle |
| **Superseded** | Replaced by a newer version or a different ADR | Kept for history; link to the document that supersedes it |

A document moves from Draft to In Review when the author believes it is complete.
A document moves from In Review to Accepted when all open questions are resolved and the owner approves it.
A document moves from Accepted to Superseded when a new decision overrides it.

---

## 7. ADR Template

Copy this template when creating any new ADR. File naming: `ADR-NNN-short-decision-title.md`.

```markdown
# ADR-NNN — [Short Decision Title]

| Field      | Value                  |
|------------|------------------------|
| Status     | Draft                  |
| Date       | YYYY-MM-DD             |
| Owner      |                        |
| Supersedes | —                      |
| Superseded by | —                   |

---

## Context

[Why is this decision needed? What is the problem or constraint that forces a choice?
Be specific. Include any relevant constraints from ADR-000 or the SAD.]

---

## Decision

[One paragraph. State exactly what was decided. Use active voice: "We will use X for Y."]

---

## Rationale

[Why this option? What properties of this choice satisfy the requirements better than alternatives?
Reference specific requirements from ADR-000 where relevant.]

---

## Alternatives Considered

### Option A — [Name]
[What it is. Why it was rejected.]

### Option B — [Name]
[What it is. Why it was rejected.]

---

## Consequences

**Positive**
- [Outcome 1]
- [Outcome 2]

**Negative / Trade-offs**
- [Trade-off 1]
- [Trade-off 2]

---

## Open Issues

| # | Issue | Resolution Target |
|---|-------|-------------------|
| 1 | [Unresolved question] | [Date or milestone] |
```

---

*This document is the governing reference for all project documentation. When in doubt about whether a document is needed, what it should contain, or what order to write it in — the answer is in this file.*

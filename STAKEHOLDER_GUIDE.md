# OpenSpec-Driven Modernization — Stakeholder Guide

**Audience:** engineering leadership, project sponsors, and stakeholders overseeing a
legacy application modernization effort.
**Purpose:** explain, in professional and non-implementation-specific language, how this
project analyzes a legacy application, plans modernization work, and delivers it
feature-by-feature with a documented, auditable trail at every step.

A companion technical reference (`OPENSPEC_GUIDE.md`) contains full command-level detail
for engineers executing this process. This document explains the *approach*, the
*controls*, and the *evidence* behind it.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Problem This Approach Solves](#2-the-problem-this-approach-solves)
3. [How the Legacy Application Is Analyzed](#3-how-the-legacy-application-is-analyzed)
4. [Project Setup — Standing Up the Modernization Environment](#4-project-setup--standing-up-the-modernization-environment)
5. [The Delivery Model: Feature-by-Feature, With Gates](#5-the-delivery-model-feature-by-feature-with-gates)
6. [Worked Example: One Feature, Start to Finish](#6-worked-example-one-feature-start-to-finish)
7. [Quality Controls and Governance](#7-quality-controls-and-governance)
8. [Roadmap to Full Migration](#8-roadmap-to-full-migration)
9. [Summary Reference Table](#9-summary-reference-table)

---

## 1. Executive Summary

This project modernizes a legacy ASP.NET Web Forms application by:

1. **Analyzing** the legacy codebase automatically to produce a complete, factual
   inventory of every page, its business purpose, its authentication requirements, and
   its technical risk factors (e.g., direct database access).
2. **Planning** the modernization as a sequence of discrete, independently deliverable
   capabilities, ordered by risk and complexity rather than arbitrary priority.
3. **Specifying** each capability before any code is written, using a structured,
   reviewable four-document format (Proposal, Design, Specification, Task Plan).
4. **Building and verifying** each capability against its specification, with an
   explicit, enforced distinction between "code has been written" and "behavior has
   been confirmed working."
5. **Recording** completed work as durable specifications that describe what the new
   system actually does — not what a plan once said it would do.

Two capabilities have been delivered and verified to date; a complete, reviewable
transcript of the entire process — every command executed and every result observed —
is maintained in `example-walkthrough/EXAMPLE_WALKTHROUGH.md` for audit purposes.

---

## 2. The Problem This Approach Solves

Legacy modernization projects commonly fail or stall for three reasons:

| Risk | How this approach addresses it |
|---|---|
| **Undocumented legacy behavior** — nobody can say with confidence what the current system actually does, only what it was originally intended to do. | An automated analysis tool reads the legacy source directly and produces a factual inventory (pages, controls, authentication model, data-access patterns) — not assumptions, not tribal knowledge. |
| **Uncontrolled AI-assisted development** — when using AI coding assistants, there is a risk of scope drift, unverifiable claims of completion, and code that diverges from any agreed plan. | Every unit of work is scoped, specified, and reviewed *before* implementation begins, and implementation is required to follow the agreed task list exactly. Nothing is marked complete without being genuinely tested. |
| **All-or-nothing delivery risk** — attempting to migrate an entire application in one release invites schedule and quality risk. | The application is decomposed into independent, incrementally deliverable capabilities. Each is planned, built, and verified on its own; the legacy system continues operating throughout. |

---

## 3. How the Legacy Application Is Analyzed

Before any modernization work is planned, the legacy application is processed by an
automated analysis tool (referred to in this project as the **aspx-analyzer skill**,
located in `skill/`). This is a factual, mechanical analysis — it reads source code, it
does not guess or infer intent.

**What it produces:**

| Output | Business value |
|---|---|
| A complete inventory of every page and reusable component in the legacy application | Establishes ground truth for scope — nothing is modernized based on incomplete knowledge of what exists |
| Classification of pages into business capability groupings (e.g., Orders, Administration, Reporting) | Enables the modernization to be planned around business function, not arbitrary technical boundaries |
| Identification of authentication and access-control requirements per page | Ensures security posture is preserved or deliberately and visibly changed — never silently dropped |
| Identification of direct database access and other technical risk factors | Surfaces the pages that carry the highest migration risk and effort *before* planning begins, not after work starts |
| A recommended build sequence, ordered from lowest to highest complexity | Provides a defensible, risk-based prioritization for planning discussions, rather than an ad hoc one |

**How it is used:** the analysis output is fed directly into the planning tool
(OpenSpec, described below) so that every subsequent planning document is automatically
informed by real facts about the legacy system — the technology stack, the
capability inventory, and known risk areas — without requiring engineers to manually
re-research and re-type this information for every piece of work.

This analysis step is also self-correcting: during this project, the analysis tool
itself was found to have a gap (it was not recognizing a category of legacy UI
controls, which understated the presence of certain page types). The gap was identified,
corrected, and the analysis was re-run — a demonstration that the process includes
verification of its own tooling, not only of the application being modernized.

---

## 4. Project Setup — Standing Up the Modernization Environment

Setting up a modernization project of this kind involves four components, each with a
distinct and separable responsibility:

| Component | Responsibility | Location in this project |
|---|---|---|
| **Legacy source** | The application being modernized, unmodified, retained as the reference for correct behavior | `legacy/` (not stored in this repository — retrieved on demand from its original source, since it is not proprietary work product) |
| **Analysis output** | The factual inventory and modernization roadmap produced by the analysis tool | `example-walkthrough/analysis-output/` |
| **Planning workspace** | The structured planning-and-specification workspace (OpenSpec), where every capability's Proposal, Design, Specification, and Task Plan is authored, reviewed, and archived once verified | `modernization/openspec/` |
| **Modern application** | The new implementation being built to replace legacy capabilities, one at a time | `modernization/` (backend service and frontend application) |

**Setup sequence, at a governance level:**

1. Establish the planning workspace in the target project.
2. Run the analysis tool against the legacy source to produce the factual inventory and
   the recommended build sequence.
3. Project that inventory into the planning workspace, so every future planning
   document is automatically informed by it.
4. Select the first capability to build, using the recommended build sequence as the
   starting point for prioritization discussion.
5. Proceed to the delivery model described in Section 5.

This sequence is fully documented at the command level in `OPENSPEC_GUIDE.md`, Parts 2–4,
for the engineering team executing it.

---

## 5. The Delivery Model: Feature-by-Feature, With Gates

Each capability — whether a single legacy page or a related group of pages — is
delivered through an identical, repeatable four-stage planning process before any
implementation begins, followed by implementation and verification.

| Stage | Document Produced | Purpose | Review Question |
|---|---|---|---|
| **1. Proposal** | `proposal.md` | States why the work is needed, what will change, and what is explicitly out of scope | Does this solve a real, well-understood problem, scoped appropriately? |
| **2. Design** | `design.md` | States the technical approach, the key decisions, and their trade-offs | Is the approach sound, and are the trade-offs acceptable? |
| **3. Specification** | `spec.md` | States the exact functional requirements as testable scenarios | Are these the right requirements, stated unambiguously? |
| **4. Task Plan** | `tasks.md` | States the ordered, checkable implementation steps | Is this plan complete and achievable? |

**Only once all four documents exist and have been reviewed does implementation begin.**
Implementation is required to follow the Task Plan exactly — this is a deliberate control
to prevent unscoped or undocumented changes, particularly relevant when AI coding
assistants are used to accelerate delivery.

**The verification gate:** a task is only marked complete once its outcome has been
genuinely observed — a feature that has been coded but not run and checked is not
"complete." This distinction is enforced throughout the project and is the single most
important quality control in this delivery model. A capability's specification is only
finalized into the permanent project record once every task has been verified this way,
not merely written.

---

## 6. Worked Example: One Feature, Start to Finish

To illustrate the delivery model concretely, this section walks through one capability
that was delivered in this project: modernizing the legacy grid-selection page into a
web API and modern user interface.

**1. Selection.** The automated analysis identified this capability as low-complexity
and low-risk (no direct database dependency, no asynchronous UI behavior) — a
deliberate choice to prove the delivery model on a well-understood, low-risk unit of
work before tackling higher-complexity capabilities.

**2. Proposal.** The proposal document stated the business rationale: the legacy page
functions correctly but cannot be reused outside the legacy runtime, cannot be
independently tested, and ties the user interface technology to a single vendor
control library. It named the exact legacy page being replaced and confirmed the
change was additive — the legacy page would remain live and unmodified throughout.

**3. Design.** The design document recorded the technical approach (a modern web
service plus a modern web front end) and, importantly, recorded what would deliberately
be verified only when a suitable technical environment became available — the
compilation and execution of the backend service required a runtime not present in the
environment used for this phase of work. This limitation was documented explicitly
rather than concealed.

**4. Specification.** The specification stated the exact required behavior as
verifiable scenarios: the data returned must match the legacy page exactly; the user
interface must reproduce the same selection behavior and paging; the feature must be
demonstrably testable in a web browser.

**5. Implementation and verification.** The backend service was built to specification.
The front-end application was built, and — critically — was **actually run** and
verified in a live browser session: real data was loaded, user interactions (selecting
rows, navigating pages) were performed, and the resulting behavior was directly observed
and confirmed correct, with no errors present. The backend service's compilation could
not be verified in this phase, for the reason recorded in the Design document, and this
was recorded as an open item rather than an assumed success.

**6. Outcome.** The capability was fully implemented and its user-facing behavior
independently verified. It has not yet been marked as formally complete ("archived") in
the planning workspace, because one verification step — compiling and running the
backend service — remains outstanding pending the availability of the required
technical environment. This is by design: the process does not permit a capability to
be recorded as complete while a known verification gap remains open.

This example demonstrates the model's core value: every claim of progress is backed by
either a direct observation or an explicitly recorded limitation — never an assumption.

---

## 7. Quality Controls and Governance

| Control | How it works |
|---|---|
| **Pre-implementation review gate** | No implementation begins until all four planning documents exist and can be reviewed — the point at which correcting a wrong assumption is cheapest. |
| **Verification discipline** | Tasks are marked complete only when their outcome has been observed, not merely coded. This is checked at every stage of every capability in this project. |
| **Traceability to legacy source** | Every proposal is required to name the exact legacy page(s) or component(s) it replaces — modernization scope is never based on invented or assumed requirements. |
| **Security continuity** | Every proposal is required to preserve existing access-control requirements unless a change to the access model is explicitly proposed and reviewed. |
| **Independent audit trail** | A complete, unedited transcript of every command executed and every result observed is maintained (`example-walkthrough/EXAMPLE_WALKTHROUGH.md`), including issues encountered and how they were resolved — not a curated summary. |
| **Multi-contributor safety** | Each capability is scoped to its own isolated unit of work, preventing two contributors from conflicting on the same piece of work; a defined review checklist governs acceptance of any contributor's work before it is merged. |

---

## 8. Roadmap to Full Migration

Two capabilities have been delivered to date, out of an inventory of legacy business
capabilities identified during analysis. Completing the modernization is a continuation
of the same model at scale, not a different process:

1. **Work the prioritized list to completion.** The analysis tool's recommended build
   sequence serves as the ongoing backlog; each remaining capability is delivered
   through the same four-stage planning and verification model described in Section 5.
2. **Close outstanding verification gaps.** Once the required backend technical
   environment is available, the deferred verification step (Section 6) is completed for
   every capability built to date, and each is formally finalized ("archived") into the
   permanent specification record.
3. **Consolidate shared infrastructure.** As common patterns emerge across capabilities
   (shared services, authentication, data access), these are deliberately proposed and
   reviewed as their own units of work, rather than allowed to develop inconsistently.
4. **Scale quality assurance.** As the delivered surface area grows, manual verification
   is supplemented with automated testing to ensure prior capabilities remain correct as
   new ones are added.
5. **Execute a deliberate cutover strategy.** Two standard approaches apply: an
   incremental cutover, where user traffic is redirected to each modernized capability
   as it is completed and verified (the legacy system shrinks progressively), or a
   coordinated single cutover once all capabilities are complete. This decision should be
   made explicitly, with stakeholder input, rather than assumed.
6. **Define "complete" in advance.** Functional parity, verified test coverage, and
   (where applicable) a stable period of live operation should be agreed as the
   completion criteria for each capability before work begins, so that project status
   can be reported unambiguously at any point in time.

---

## 9. Summary Reference Table

| Question | Answer |
|---|---|
| What produces the factual inventory of the legacy application? | The aspx-analyzer skill (`skill/`) — automated, source-level analysis |
| Where is the modernization plan recorded? | `modernization/openspec/` — one folder per capability, containing its four planning documents |
| Where is the new application being built? | `modernization/` — backend service and frontend application |
| How is progress measured? | By capability: proposal → design → specification → task plan → implementation → verified → finalized. Current status of every capability is queryable at any time. |
| What is the audit record? | `example-walkthrough/EXAMPLE_WALKTHROUGH.md` — an unedited, complete transcript of the entire process to date |
| Where is the engineering-level command reference? | `OPENSPEC_GUIDE.md` |
| Where is the current project status? | `README.md` |

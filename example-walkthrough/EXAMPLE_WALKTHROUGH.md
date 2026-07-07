# Complete Worked Example: Legacy → Modern Migration End-to-End

> **Note on this copy:** this project was reorganized after the fact into
> `legacy/` / `modernization/` / `example-walkthrough/` / `skill/` folders (see the
> top-level `README.md`). The commands and paths below are the exact real history —
> written when everything lived flat under one `aspnet-ej1-demos/` folder — and are left
> unedited as an accurate record. Where you see e.g. `modern/OrdersApi` below, that's now
> `modernization/OrdersApi`; where you see the bare repo root, that's now `legacy/` for
> the legacy source or `modernization/` for `openspec/`/the modern stack. `openspec_setup.md`
> referenced below lives in the separate `aspx-analysis-skill` tool repo, not in this project.
> `legacy/` itself is **not committed to this project's git repo** — it's a re-clonable
> vendor copy (see top-level `README.md` → "Getting the Legacy Source"). The
> `analysis-output/` snapshot alongside this file was generated before that exclusion and
> is kept as-is, including its internal `repo_path` field pointing at the old location —
> historically accurate, not a live reference.
>
> **This document is a historical transcript, not a conceptual guide** — it records
> exact commands and exact output, unedited. For what actually executes when (OpenSpec
> vs. the skill vs. Claude Code) and why, read `OPENSPEC_HANDBOOK.md` Part 1 first; it
> will make the sequence below easier to follow.

A real, hands-on run of the `aspx-analyzer` skill + OpenSpec against a real public repo —
[syncfusion/aspnet-ej1-demos](https://github.com/syncfusion/aspnet-ej1-demos), 1147 ASP.NET
Web Forms pages. Every command below was actually run; output shown is real output, not
illustrative. Companion to [openspec_setup.md](openspec_setup.md) (the concept/reference
guide) — this document is the "did it actually work" proof, plus the multi-user workflow
this guide's earlier version was missing.

**What this is NOT:** a new feature bolted onto the legacy Web Forms codebase in the same
legacy stack. The point of aspx-analyzer + OpenSpec is *modernization* — taking a legacy
capability and rebuilding it on a modern stack. This walkthrough does that: one legacy
Web Forms grid page → a real ASP.NET Core Web API + React/TypeScript frontend.

---

## Table of Contents

- [Part 1 — Setup](#part-1--setup)
- [Part 2 — Reverse-Engineering the Legacy Repo](#part-2--reverse-engineering-the-legacy-repo)
- [Part 3 — Setting Up OpenSpec](#part-3--setting-up-openspec)
- [Part 4 — Picking a Real Capability to Modernize](#part-4--picking-a-real-capability-to-modernize)
- [Part 5 — The Full SDD Loop, Every Command](#part-5--the-full-sdd-loop-every-command)
- [Part 6 — Implementation](#part-6--implementation)
- [Part 7 — Honest Status: What's Verified, What Isn't](#part-7--honest-status-whats-verified-what-isnt)
- [Part 8 — Day-to-Day Workflow (Recap)](#part-8--day-to-day-workflow-recap)
- [Part 9 — Multiple Users on the Same Project](#part-9--multiple-users-on-the-same-project)
- [Part 10 — Lessons Learned](#part-10--lessons-learned)
- [Part 11 — Bug Found and Fixed, Plus a Roadmap Tool](#part-11--bug-found-and-fixed-plus-a-roadmap-tool)
- [Part 12 — Canonical Persistent-Workspace Run (Feature 1, Genuinely Browser-Tested)](#part-12--canonical-persistent-workspace-run-feature-1-genuinely-browser-tested)
- [Part 13 — Feature 2 in This Workspace, Done End-to-End](#part-13--feature-2-in-this-workspace-done-end-to-end)
- [Part 14 — Feature 3 Checklist (Next, For You To Build)](#part-14--feature-3-checklist-next-for-you-to-build)

---

## Part 1 — Setup

Environment used (yours may differ — this is what was actually verified):

```bash
$ node --version   # v24.15.0
$ npm --version    # 11.12.1
$ git --version    # 2.54.0.windows.1
$ python --version # 3.14.4
$ dotnet --version  # NOT FOUND — see Part 7 for how this limited backend verification
```

### Clone the target repo

```bash
git -c core.longpaths=true clone --depth=1 https://github.com/syncfusion/aspnet-ej1-demos.git
```

**Gotcha hit for real:** a plain `git clone` failed partway through on Windows —
`fatal: cannot create directory at 'ReferenceAssemblies/Newtonsoft.Json.13.0.1/package/
services/metadata/core-properties': Filename too long`. Two fixes, both needed together:
`-c core.longpaths=true`, **and** cloning to a short path (`C:\ej1demo\...` rather than a
deeply nested one) — Windows' 260-character path limit is the real constraint;
`core.longpaths` alone didn't fully resolve it in a deeply nested working directory.

### Copy the skill in

```bash
mkdir -p .claude/skills
cp -r /path/to/aspx-analysis-skill/.claude/skills/aspx-analyzer .claude/skills/aspx-analyzer
```

Real file counts in the target repo after clone:

```
$ find . -iname "*.aspx" -not -path "./.git/*" | wc -l   # 1147
$ find . -iname "*.ascx" -not -path "./.git/*" | wc -l   # 4
$ find . -iname "*.cs"   -not -path "./.git/*" | wc -l   # 2497
```

---

## Part 2 — Reverse-Engineering the Legacy Repo

```bash
python .claude/skills/aspx-analyzer/scripts/aspx_analysis_skill.py . --view project --workers 8 --save-report
```

Real output (excerpted):

```
This is an **ASP.NET Web Forms** application with **1147 pages**, **4 user controls**,
and **2 master pages** across **12 functional areas**.

**Databases:** ApplicationServices, SQLConnectionString, SelfReferenceConnectionString,
Linq_To_SQLConnectionString, ScheduleConnectionString, DiagramDataConnectionString,
Adventure Works, Adventure Works DW1, ScheduleDataEntities, AspNetSqlMembershipProvider,
AspNetSqlProfileProvider, AspNetSqlRoleProvider

| Metric | Count |
|--------|-------|
| ASPX Pages | 1147 |
| User Controls (.ascx) | 4 |
| Master Pages | 2 |
| Functional Areas | 12 |
| Pages with Code-Behind | 1146 |
| Pages using Master Page | 1120 |
| Pages with AJAX (UpdatePanel) | 64 |
| Pages with Direct SQL | 6 |
| Pages with Validators | 9 |

### `Samplebrowser.Master`
- Used by: 1119 pages
### `Layout.Master`
- Used by: 1 page
```

### A real, honest limitation surfaced here

The functional-area keyword bucketing is tuned for line-of-business apps (Orders,
Administration, Reports, ...), not a control-demo catalog. On this repo it produced noisy
groupings — e.g. an "Orders (7 pages)" bucket that included a page literally named
**`Border.aspx`**, bucketed there because the keyword matcher does substring matching and
`"order"` is a substring of `"Border"`. `Reorder.aspx`/`Reordering.aspx` matched more
legitimately, but the `Border` case is a real false positive worth knowing about before
trusting functional-area groupings on a repo that isn't a genuine business app. This
doesn't affect page-level facts (controls, auth, code-behind, direct-SQL detection —
those are all regex-matched against actual markup/code, not guessed) — just the
area-bucketing heuristic used for grouping and for the OpenSpec proposal-stub emitter.

---

## Part 3 — Setting Up OpenSpec

```bash
npm install -g @fission-ai/openspec@latest
openspec --version   # 1.5.0
```

```bash
openspec init --tools claude
```

Real output:

```
- Creating OpenSpec structure...
▌ OpenSpec structure created
- Setting up Claude Code...
✔ Setup complete for Claude Code

OpenSpec Setup Complete

Created: Claude Code
5 skills and 5 commands in .claude/
Config: openspec/config.yaml (schema: spec-driven)
```

This created `openspec/config.yaml` and 5 skills under `.claude/skills/`:
`openspec-propose`, `openspec-explore`, `openspec-apply-change`, `openspec-sync-specs`,
`openspec-archive-change`. `openspec/specs/` and `openspec/changes/` did **not** exist yet
at this point — they appear on first use (confirmed: `openspec/config.yaml` was the only
file under `openspec/` right after `init`).

---

## Part 4 — Picking a Real Capability to Modernize

Chose `Grid/BasicSelection.aspx` — a demo of the Syncfusion EJ1 `ej:Grid` control showing
an Orders list with paging and toggleable multi-row selection. Read the real code-behind
first:

```csharp
// Grid/BasicSelection.aspx.cs — WebSampleBrowser.Grid.BasicSelection
private void BindDataSource()
{
    int orderId = 10000;
    int empId = 0;
    for (int i = 1; i < 9; i++)
    {
        order.Add(new Orders(orderId + 1, "VINET", empId + 1, 32.38, new DateTime(2014, 12, 25), "Reims"));
        order.Add(new Orders(orderId + 2, "TOMSP", empId + 2, 11.61, new DateTime(2014, 12, 21), "Munster"));
        order.Add(new Orders(orderId + 3, "ANATER", empId + 3, 45.34, new DateTime(2014, 10, 18), "Berlin"));
        order.Add(new Orders(orderId + 4, "ALFKI", empId + 4, 37.28, new DateTime(2014, 11, 23), "Mexico"));
        order.Add(new Orders(orderId + 5, "FRGYE", empId + 5, 67.00, new DateTime(2014, 05, 05), "Colchester"));
        order.Add(new Orders(orderId + 6, "JGERT", empId + 6, 23.32, new DateTime(2014, 10, 18), "Newyork"));
        orderId += 6;
        empId += 6;
    }
    this.OrdersGrid.DataSource = order;
    this.OrdersGrid.DataBind();
}
```

Good pick for a first proof: **no database** — data is generated in-process (48 rows, 8
loop iterations × 6 hand-coded rows). That means the modern port can be a byte-identical
comparison without needing to also stand up a database migration as part of proving the
pattern.

---

## Part 5 — The Full SDD Loop, Every Command

```bash
openspec new change modernize-grid-basic-selection \
  --description "Rebuild the legacy Grid/BasicSelection.aspx Web Forms demo as an ASP.NET Core Web API + React/TypeScript frontend" \
  --goal "Prove the legacy-to-modern migration path on one real capability: Orders grid with paging + multi-selection"
```
```
Created change 'modernize-grid-basic-selection' at openspec\changes\modernize-grid-basic-selection/
```

```bash
openspec instructions proposal --change modernize-grid-basic-selection
```
Printed the exact write path (`openspec/changes/modernize-grid-basic-selection/proposal.md`)
and the section rules (Why / What Changes / Capabilities / Impact). Authored the file
accordingly — real sections included a Why grounded in the actual legacy code-behind
(no API, data welded to the Web Forms page), a What Changes list scoped to purely additive
work (legacy page untouched), and a Capabilities section declaring one new capability,
`orders-grid-api`. The file itself lives in the target repo clone, not in this repo — see
Part 10 for why nothing here got committed anywhere.

```bash
openspec instructions design --change modernize-grid-basic-selection
```
Same pattern — write path + section rules (Context / Goals-NonGoals / Decisions /
Risks-Tradeoffs / Migration Plan / Open Questions). Key decisions actually recorded:
in-memory repository that reproduces the legacy loop exactly (not a real database — the
legacy page has none either), controller-based Web API (not minimal API, to map onto the
"class with methods" mental model a Web Forms developer already has), native `<table>`
grid component (no third-party grid library, to keep this single-page proof's dependency
count near zero).

```bash
openspec instructions specs --change modernize-grid-basic-selection
```
Wrote `specs/orders-grid-api/spec.md` with 5 requirements (API shape + CORS, frontend
columns, paging, toggleable selection) each with `#### Scenario:` blocks in the required
4-hashtag WHEN/THEN format.

```bash
openspec instructions tasks --change modernize-grid-basic-selection
```
Wrote `tasks.md` with 3 numbered groups: Backend, Frontend, Verification.

```bash
openspec status --change modernize-grid-basic-selection
```
```
Progress: 4/4 artifacts complete
[x] proposal
[x] design
[x] specs
[x] tasks
All artifacts complete!
```

```bash
openspec validate modernize-grid-basic-selection --strict
```
```
Change 'modernize-grid-basic-selection' is valid
```

---

## Part 6 — Implementation

Per `tasks.md`, in order:

**Backend** (`modern/OrdersApi/`) — hand-authored against ASP.NET Core 8 conventions:
- `Models/Order.cs` — mirrors the legacy `Orders` class fields exactly.
- `Data/OrdersRepository.cs` — the legacy `BindDataSource()` loop ported line-for-line
  (same literal values), with a comment pointing back at the legacy file as source of
  truth.
- `Controllers/OrdersController.cs` — `GET /api/orders` returning `OrdersRepository.GetAll()`.
- `Program.cs` — CORS policy for the Vite dev server origin (`http://localhost:5173`),
  `AddControllers()`/`MapControllers()`.
- `OrdersApi.csproj`, `appsettings.json`.

**Frontend** (`modern/orders-grid-web/`) — actually scaffolded and run, not just written:

```bash
npm create vite@latest orders-grid-web -- --template react-ts
cd orders-grid-web
npm install
```
```
added 27 packages, and audited 28 packages in 19s
found 0 vulnerabilities
```

Then wrote `src/api/ordersClient.ts` (typed `fetch` wrapper against `Order` interface
matching the API), `src/components/OrdersGrid.tsx` (fetch-on-mount, loading/error states,
client-side paging at 10 rows/page, click-to-toggle multi-row selection via a `Set<number>`
of selected order IDs), wired into `App.tsx`, replaced the Vite template's boilerplate
`App.css` with minimal table/selection styling.

```bash
npm run build
```
```
> tsc -b && vite build
✓ 19 modules transformed.
dist/index.html                   0.46 kB │ gzip:  0.30 kB
dist/assets/index-CtZE_aj5.css    2.15 kB │ gzip:  0.94 kB
dist/assets/index-DNapOwG1.js   192.42 kB │ gzip: 60.70 kB
✓ built in 161ms
```

**This is real, verified success** — TypeScript compiled with zero errors, production
bundle produced. Not a claim, an actual command result.

---

## Part 7 — Honest Status: What's Verified, What Isn't

| Piece | Status |
|---|---|
| Frontend TypeScript compiles + builds | ✅ **Verified** — `npm run build` actually ran and passed |
| Frontend dependency install | ✅ **Verified** — `npm install` actually ran, 0 vulnerabilities |
| Backend C# compiles | ❌ **Not verified** — no `dotnet` SDK on PATH in this sandbox |
| Backend/frontend integration (`npm run dev` against a running API) | ❌ **Not verified** — needs the backend running, which needs the SDK |
| Legacy vs. modern side-by-side visual comparison | ❌ **Not verified** — needs a browser + both apps running |

**This change was deliberately left unarchived.** `openspec status` still shows tasks 3.1–3.3
unchecked. Archiving is a claim that spec deltas are trustworthy enough to merge into the
durable `openspec/specs/` — doing that on the strength of "the files exist" rather than
"the behavior was verified" defeats the entire point of spec-driven development. The
correct next step for whoever picks this up is: install the .NET 8 SDK, run
`dotnet build && dotnet run` in `modern/OrdersApi`, run `npm run dev` in
`modern/orders-grid-web` pointed at it, confirm the grid behaves as specified, check off
tasks 3.1–3.3, *then* `openspec archive modernize-grid-basic-selection`.

---

## Part 8 — Day-to-Day Workflow (Recap)

Full detail in [openspec_setup.md Part E](openspec_setup.md#part-e--day-to-day-sdd-building-every-feature-through-openspec).
Short version, exactly as used above:

```bash
openspec new change <name> --description "..." --goal "..."
openspec instructions proposal --change <name>   # → author proposal.md
openspec instructions design   --change <name>   # → author design.md
openspec instructions specs    --change <name>   # → author specs/<capability>/spec.md
openspec instructions tasks    --change <name>    # → author tasks.md
openspec status   --change <name>                 # confirm 4/4
openspec validate <name> --strict                  # confirm structurally valid
# ... implement tasks.md, check off boxes as each is genuinely verified ...
openspec validate <name> --strict                  # re-validate
openspec archive  <name>                           # only once verification tasks are done
```

Repeat per capability/feature. For a legacy modernization project specifically, each
capability the aspx-analyzer index surfaces (Part 2) is a candidate for exactly this loop
— this walkthrough did it once, by hand, for `Grid/BasicSelection.aspx`; the same shape
applies to any of the other 1146 pages.

---

## Part 9 — Multiple Users on the Same Project

OpenSpec's file-per-change layout (`openspec/changes/<name>/`) is what makes multi-user
work tractable — two people working on different capabilities never touch the same files.

### Branching model

- **One branch per change**, named after the change: `git checkout -b
  modernize-grid-basic-selection`. The branch and the `openspec/changes/<name>/` folder
  share a name by convention — trivial to find which branch owns which change.
- Commit the proposal/design/specs/tasks artifacts **before** writing implementation code,
  as their own commit(s), so a reviewer can review the plan in a PR before any
  implementation lands (this is the actual SDD value-add over a normal PR: the review
  point moves earlier).
- Implementation commits land in the same branch/PR, referencing the tasks.md checkboxes
  they complete.

### Avoiding collisions

- **Check `openspec list` before starting** — if someone else already has a change for the
  capability you're about to pick, don't start a second one; either wait, split the scope,
  or coordinate who owns which piece.
- **Two people should never edit the same `openspec/changes/<name>/` folder concurrently**
  on different branches — that folder belongs to one branch/PR at a time, same as you
  wouldn't have two people editing the same feature file. If a second person needs to build
  on an in-flight change before it merges, they branch from that change's branch, not from
  `main`.
- **Capability names must be unique across in-flight changes** — since specs live at
  `openspec/specs/<capability>/spec.md` once archived, two different changes claiming the
  same capability name will conflict at merge time in `openspec/specs/`, not just in
  `openspec/changes/`. Pick specific, non-overlapping capability names (this walkthrough
  used `orders-grid-api`, not something generic like `grid`).

### Merge order and `openspec/specs/`

- `openspec/specs/` is the durable, shared source of truth — treat merges into it (via
  `openspec archive` on `main`, post-PR-merge) like any other shared-state change: **archive
  from `main` after the PR merges, not from a feature branch**, so `openspec/specs/` only
  ever grows on the trunk everyone bases new work from.
- If two changes touch *different* capabilities, their archives don't conflict — different
  `specs/<capability>/` paths. If (due to a naming collision that should have been caught
  earlier) two changes claim the same capability, resolve it like any other merge conflict
  in the spec file — manually reconcile which MODIFIED/ADDED requirements win, the same as
  you'd resolve conflicting edits to any shared doc.

### Review checklist for a teammate's change (before approving the PR)

1. Does `proposal.md`'s Capabilities section list a capability name that doesn't already
   exist in `openspec/specs/` (for a new capability) or exactly match an existing one (for
   a modification)? Wrong name = orphaned spec file at archive time.
2. Does every requirement in `specs/<capability>/spec.md` have at least one `#### Scenario`
   (exactly 4 hashtags)? `openspec validate <name> --strict` catches this — make it a
   required CI/pre-merge check, not just a manual read.
3. Are `tasks.md` checkboxes only checked for work actually verified (see Part 7's
   distinction between "authored" and "verified")? A reviewer should be able to trust a
   checked box.
4. For a legacy-modernization change specifically: does the proposal name the exact legacy
   page(s)/route(s) being replaced? (This is what the aspx-analyzer emitter's stubs give
   you for free — a real page list, not an assumption.)

---

## Part 10 — Lessons Learned

- **`git clone` on Windows can fail on deeply-nested/long paths in large repos** —
  `-c core.longpaths=true` plus a short clone destination path fixed it; either alone
  wasn't enough in this case.
- **Functional-area keyword bucketing has real false positives on non-business-app repos**
  (the `Border.aspx` → "Orders" bucket, matched via substring). Trust page-level facts
  (auth, controls, direct-SQL) over area groupings when the target isn't a typical
  line-of-business app.
- **OpenSpec's real CLI (v1.5.0) differs from some published documentation** — no
  `--profile expanded`, no `/opsx:new`/`/opsx:continue`/`/opsx:ff`/`/opsx:verify`/
  `/opsx:bulk-archive`/`/opsx:onboard` commands exist; only `core` profile, 5 skills. The
  per-artifact `openspec instructions <artifact> --change <id>` mechanism used throughout
  this walkthrough is real and is the correct granular alternative.
- **Nothing in this walkthrough was committed anywhere** — it ran against a throwaway
  clone of `syncfusion/aspnet-ej1-demos` at `C:\ej1demo\aspnet-ej1-demos` on the machine
  this was authored on, purely to produce real, verifiable output for this guide. Re-run
  the commands above against your own clone to reproduce it.
- **Don't claim more verification than you have** — the honest split in Part 7 (frontend
  build genuinely verified, backend compile not) is the single most important habit this
  walkthrough demonstrates. It applies to every change you'll make with this workflow, not
  just this one.

---

## Part 11 — Bug Found and Fixed, Plus a Roadmap Tool

Reviewing this walkthrough surfaced one real bug in the skill itself, plus a real gap
(no answer to "what order do I build things in, and how do I set up the target stack").
Both fixed, both re-verified against the same real repo.

### The bug: substring false positives in functional-area detection

Part 2 flagged it: `Border.aspx` was bucketed into the "Orders" functional area. Root
cause, in `engine/aspx_parser.py`'s `_infer_functional_area()`: keyword matching used plain
Python substring checks (`kw in combined`), and `"order"` is a literal substring of
`"border"`. Same bug class affected `Reorder.aspx`/`Reordering.aspx` (both contain
`"order"`).

**Fix:** added camelCase-aware tokenization (`OrderHistory` → `"order history"`, but
`Border`/`Reorder` are single unbroken case-runs and stay as one token) plus
word-boundary regex matching (`\border\b`), so `"order"` only matches when it's an actual
whole word/token, not an arbitrary substring:

```python
_CAMEL_SPLIT = re.compile(r'(?<=[a-z0-9])(?=[A-Z])')

def _tokenize(text: str) -> str:
    return _CAMEL_SPLIT.sub(' ', text).lower()

def _kw_match(text: str, keywords: List[str]) -> bool:
    return any(re.search(rf'\b{re.escape(kw)}\b', text) for kw in keywords)
```

Verified directly:

```
Border      -> General   (was: Orders — FIXED)
Reorder     -> General   (was: Orders — FIXED)
OrderHistory-> Orders    (still correct — camelCase split preserves this match)
SalesInvoice-> Orders    (still correct)
Checkout    -> Orders    (still correct)
```

And end-to-end, rebuilding the real index:

```
## Orders  (3 pages)          <- was 7 pages before the fix
Key pages: `Invoice.aspx`, `SalesInvoice.aspx`, `SalesInvoice.aspx`
```

`Border.aspx`, `Reorder.aspx`, `Reordering.aspx` are gone from the Orders bucket — they
now correctly fall to `General`. This also matters for the OpenSpec emitter (Part 3/4 of
this walkthrough): a proposal stub for "Orders" built from the pre-fix index would have
told a developer to migrate `Border.aspx` as part of the Orders capability, which is
simply wrong.

**Known remaining limitation, not fixed (by design):** on a control-demo catalog like
this repo, no keyword in `_AREA_KEYWORDS` matches "Grid" itself, so all ~130 Grid demo
pages land in `General` rather than a `Grid` bucket. The keyword list is tuned for
business-domain capabilities (Orders, Administration, Reports), not per-UI-control
categories — accurate behavior for a real line-of-business app, a known gap for a
component-showcase repo like this one. Not something a word-boundary fix can address;
would need either a much longer keyword list or a structural (folder-name-based) fallback,
neither attempted here to keep this fix scoped to the demonstrated bug.

### The gap: no build-order or tech-stack-setup answer

Everything up to Part 10 tells you *what* the legacy app looks like and walks *one*
capability through modernization by hand. It didn't answer, for the other ~1146 pages:
where do I even start, and what commands set up the target stack? New script,
`aspx_roadmap_emitter.py`, closes that gap — standalone, no OpenSpec dependency:

```bash
python .claude/skills/aspx-analyzer/scripts/aspx_roadmap_emitter.py \
    aspnet-ej1-demos/aspnet-ej1-demos_aspx_index.json
```
```
[ok] Roadmap saved -> C:\ej1demo\aspnet-ej1-demos\aspnet-ej1-demos\MODERNIZATION_ROADMAP.md
```

Real output (using the post-fix index), ranked simplest-first by an explicit score
(`pages + direct_sql*3 + ajax + unknown_auth`, direct SQL weighted heaviest since
data-access rewrite — not the UI port — is the dominant migration cost):

```
| # | Capability     | Pages | Direct SQL | AJAX | Unknown Auth | Score | Suggested first page |
|---|-----------------|-------|------------|------|---------------|-------|----------------------|
| 1 | Contact         | 2     | 0          | 0    | 2             | 4     | Slider/ButtonSupport.aspx |
| 2 | Products        | 1     | 1          | 0    | 1             | 5     | XlsIO/StockPortFolio.aspx |
| 3 | Configuration   | 3     | 0          | 0    | 3             | 6     | Gantt/TimeOption.aspx |
| 4 | Orders          | 3     | 1          | 0    | 3             | 9     | Pdf/Invoice.aspx |
| 5 | Search          | 5     | 0          | 0    | 5             | 10    | Schedule/AppointmentSearch.aspx |
...
| 11| General         | 829   | 3          | 53   | 828           | 1719  | Accordion/API.aspx |
```

`Contact` (score 4, zero direct-SQL) ranks first — consistent with Part 4's manual pick of
`Grid/BasicSelection.aspx` (also zero-SQL) as the right kind of first target, just found
automatically here instead of by inspection. `General` (829 pages, the Grid-demo catch-all
from the limitation above) correctly ranks last — highest volume, real SQL usage, most
AJAX pages.

The roadmap's Target Stack Setup section reuses exactly the layout and commands actually
verified in Part 6 (`dotnet new webapi`, `npm create vite@latest ... --template react-ts`),
plus a lighter `dotnet-razor-pages` alternative for teams that want to stay same-runtime
rather than adopt a decoupled API+SPA split.

One cosmetic bug caught and fixed while building this: page paths were rendered with raw
Windows backslashes (`Slider\ButtonSupport.aspx`) instead of the forward slashes every
other report in this skill uses — fixed by normalizing at display time, verified in the
real output above.

---

## Part 12 — Canonical Persistent-Workspace Run (Feature 1, Genuinely Browser-Tested)

Everything above (Parts 1-11) ran in a throwaway clone (`C:\ej1demo\...`) that no longer
exists. **This section is the canonical, current reference** — a fresh run in a real,
permanent folder, with two new hard requirements: the feature must be genuinely
verifiable in a real browser in this authoring session (not just "the build passed"), and
implementation must strictly follow the OpenSpec artifact/task discipline — no ad hoc
code changes outside what `tasks.md` specifies.

### 12.1 — Where this project actually lives

```
C:\Users\SarveshTalele\Documents\
├── aspx-analysis-skill\       ← the tool repo (this repo)
└── aspnet-ej1-demos\          ← the modernization project — legacy code + openspec/ + modern/, all here
```

Sibling folders, by deliberate choice — keeps the tool separate from the thing being
modernized, same as you'd do with a real client repo.

### 12.2 — Fresh clone + skill copy

```bash
git -c core.longpaths=true clone --depth=1 https://github.com/syncfusion/aspnet-ej1-demos.git
```

Clean checkout this time — no long-path failures (`Documents\aspnet-ej1-demos` is a
short enough path; the earlier failure in Part 1 was `core.longpaths` alone not being
enough on a *deeply nested* temp path, not a property of this repo itself).

```bash
mkdir -p .claude/skills
cp -r /path/to/aspx-analysis-skill/.claude/skills/aspx-analyzer .claude/skills/aspx-analyzer
```

### 12.3 — Automatic tech-stack analysis + OpenSpec dependency setup

```bash
python .claude/skills/aspx-analyzer/scripts/aspx_analysis_skill.py . --view project --workers 8 --save-report
openspec --version   # 1.5.0
openspec init --tools claude
python .claude/skills/aspx-analyzer/scripts/aspx_openspec_emitter.py \
    aspnet-ej1-demos/aspnet-ej1-demos_aspx_index.json --openspec-dir ./openspec
```

This is the concrete answer to "OpenSpec should analyse the tech stack, install
dependencies automatically": the emitter writes the discovered stack straight into
`openspec/config.yaml`, and — proven directly, not just claimed — that context now
**automatically appears in every future `openspec instructions` call** for this project.
Running `openspec instructions proposal --change <anything>` later in this session printed:

```xml
<project_context>
Legacy stack: ASP.NET Web Forms (.NET Framework), code-behind pattern.
Project: aspnet-ej1-demos
Inventory: 1147 .aspx page(s), 4 .ascx user control(s), 2 .master page(s).
...
Business capabilities discovered (page count): Administration (16), Configuration (3), ...
</project_context>
<rules>
- Every proposal must name which legacy .aspx page(s) it replaces...
- 6 legacy page(s) use direct SQL...
</rules>
```

with zero manual re-entry — that block came entirely from the emitter's earlier run.
Dependency installation was likewise real, not aspirational: `npm install` /
`npm install --save-dev json-server` both actually ran (see 12.7). The one dependency
that could *not* be auto-installed and verified: .NET SDK packages for the backend — no
`dotnet` on this machine's PATH, stated honestly rather than pretending otherwise.

### 12.4 — A second real bug found: `<ej:*>` tags were invisible to the parser

Before picking a feature, re-running the analyzer surfaced a much bigger issue than
Part 11's substring bug. `engine/aspx_parser.py`'s control-tag regex was hardcoded to
`<asp:(\w+)...`, so it only ever matched the built-in ASP.NET namespace — **every
Syncfusion `<ej:Grid>`, `<ej:Button>`, `<ej:DropDownList>`, etc. was silently invisible**,
on a repo where those are the majority of the actual UI. Measured directly:

```python
grid_ctrl = sum(1 for p in idx['pages'] if any(c['type']=='grid' for c in p.get('form_controls',[])))
# BEFORE the fix: 0 (the tag was never even parsed)
# AFTER the fix:  107
```

Fix — made the regex prefix-agnostic (`<\w+:(\w+)...`, so it matches `asp:`, `ej:`,
`telerik:`, `dx:`, or any other vendor's `<%@ Register TagPrefix=... %>` prefix) and added
`'grid'` to `_FORM_CTRL_TYPES` (Syncfusion's own tag name for its grid control, which has
no equivalent in the built-in ASP.NET set). Re-verified: 107 pages now correctly show a
grid control, 338 show a button, 194 show a dropdown — all previously undercounted or
missed entirely. This fix has value beyond this one repo: any legacy Web Forms app built
on a third-party control library (Telerik, DevExpress, Infragistics, ...) was suffering
the same silent blind spot.

### 12.5 — Deciding the one feature to build

The roadmap's top-ranked capabilities turned out to be a poor fit on inspection:
`Contact` (rank 1) is actually `EncryptionSupport.aspx`/`ButtonSupport.aspx` — PDF
encryption and slider-widget demos, bucketed under "Contact" because "support" matched a
keyword meant for customer-support pages. `Products`/`Orders` (ranks 2 and 4) turned out
to be PDF/Excel document-generation demos (`Invoice.aspx`, `StockPortFolio.aspx`), and
`Search` (rank 5, `AppointmentSearch.aspx`) actually depends on a live SQL Server via
`<asp:SqlDataSource>` — undetected by the `uses_sql_direct` heuristic, which only looks
for `SqlConnection`/`SqlCommand` in code-behind, not declarative `SqlDataSource` binding.
Another real, worth-noting gap, not fixed here (out of scope for this run).

Instead of trusting the ranking blindly, queried the (now-corrected) index directly for a
better-fitting candidate: a page with a grid control, no direct SQL, no AJAX:

```python
candidates = [p for p in idx['pages']
              if 'grid' in {c['type'] for c in p.get('form_controls', [])}
              and not p.get('uses_sql_direct') and not p.get('uses_ajax')]
# 96 candidates
```

Picked `Grid/CheckboxSelection.aspx` — checkbox-column multi-row selection + paging,
in-process data (no DB, same pattern as the very first capability from Part 4, but a
genuinely different selection paradigm: checkbox toggle vs. click-anywhere-on-row toggle).

### 12.6 — The full SDD loop, every real command

```bash
openspec new change modernize-grid-checkbox-selection \
  --description "Rebuild the legacy Grid/CheckboxSelection.aspx Web Forms demo (checkbox-column multi-row selection + paging) as an ASP.NET Core Web API + React/TypeScript frontend, genuinely browser-testable in this environment via a local mock API standing in for the .NET backend" \
  --goal "Second real modernization proof, this time picked from analyzer output corrected by the ej: tag-prefix fix, and verified live in a browser"

openspec instructions proposal --change modernize-grid-checkbox-selection
#   -> authored proposal.md (Why names the ej: tag bug that led to this pick;
#      Capabilities: new `checkbox-selection-grid-api`)
openspec instructions design --change modernize-grid-checkbox-selection
#   -> authored design.md. Key decision: share the existing modern/OrdersApi project
#      rather than a new one-per-capability project (an explicit, documented exception
#      to the roadmap's default suggestion, justified because both capabilities are
#      "Orders grid variants")
openspec instructions specs --change modernize-grid-checkbox-selection
#   -> authored specs/checkbox-selection-grid-api/spec.md, 5 requirements incl. one
#      specifically requiring browser-verifiability via a local mock
openspec instructions tasks --change modernize-grid-checkbox-selection
#   -> authored tasks.md, 5 numbered groups (backend / mock / frontend / browser
#      verification / deferred real-backend verification)

openspec status --change modernize-grid-checkbox-selection
# Progress: 4/4 artifacts complete
openspec validate modernize-grid-checkbox-selection --strict
# Change 'modernize-grid-checkbox-selection' is valid
```

### 12.7 — Implementation, strictly per tasks.md

**Backend** (authored to `modern/OrdersApi/`, following tasks 1.1–1.3 — not compiled, no
.NET SDK, same honest limitation as before): `Models/Order.cs`,
`Data/CheckboxSelectionOrdersRepository.cs` (`BindDataSource()` ported line-for-line: 8
loop iterations × 5 rows = 40 rows, exact literal values), `Controllers/
CheckboxSelectionController.cs` (`GET /api/checkbox-selection-orders`), plus the project
shell (`Program.cs` with CORS, `.csproj`, `appsettings.json`) since this is a fresh
workspace with no prior capability's project to extend.

**A real deviation, caught and documented rather than silently worked around** (task
2.2): the design called for a `json-server` `routes.json` remapping
`/api/checkbox-selection-orders` → the default `/checkbox-selection-orders`. The
*installed* `json-server` is `1.0.0-beta.15`, and:

```bash
$ npx json-server --help
Usage: json-server [options] <file>
Options:
  -p, --port <port>  Port (default: 3000)
  -h, --host <host>  Host (default: localhost)
  -s, --static <dir> Static files directory (multiple allowed)
  --help             Show this message
  --version          Show version number
```

No `--routes` flag — that feature existed in classic json-server v0.x and was dropped in
this beta. Tested whether nesting the JSON under an `"api"` key would create nested routes
instead (it doesn't — `GET /api` just returns the whole nested object, not a
sub-resource). **Adapted**: flat resource key (`checkbox-selection-orders`) in the mock,
and the frontend's fetch client takes the resource path as a configurable value
(`VITE_CHECKBOX_ORDERS_PATH`, defaulting to the real API's path, overridden for local
mock verification) — zero code branching, just one extra env var.

**Frontend**, scaffolded fresh (task 3, prerequisite infra + the tasks themselves):

```bash
npm create vite@latest orders-grid-web -- --template react-ts
cd orders-grid-web && npm install
npm install --save-dev json-server
```

Then `src/api/checkboxSelectionClient.ts` (typed fetch, configurable path per the
deviation above), `src/components/CheckboxSelectionGrid.tsx` (checkbox column + 6 data
columns, paging at 10/page, a `Set<number>` of checked order IDs shared across all pages
so selection persists across navigation), wired into `App.tsx` as the sole demo (adapted:
no capability-1 component exists in this fresh workspace to place it alongside).

```bash
npm run build
```
```
> tsc -b && vite build
✓ 19 modules transformed.
dist/index.html                   0.46 kB │ gzip:  0.30 kB
dist/assets/index-BHCCfCzm.css    2.18 kB │ gzip:  0.94 kB
dist/assets/index-BU_OLp4K.js   193.02 kB │ gzip: 60.96 kB
✓ built in 205ms
```

### 12.8 — Real browser verification (task 4 — the actual point of this change)

```bash
# 1. Real 40-row mock dataset, generated from the exact BindDataSource() values
#    (see mock/db.json), served by json-server:
npx json-server mock/db.json --port 3001
$ curl -s http://localhost:3001/checkbox-selection-orders | ...
# 40 rows returned, {'orderId': 10001, 'customerId': 'VINET', ...} — matches legacy exactly

# 2. .env.local pointed the frontend at the mock:
#    VITE_API_BASE_URL=http://localhost:3001
#    VITE_CHECKBOX_ORDERS_PATH=checkbox-selection-orders

# 3. Real dev server, started via a browser preview tool (.claude/launch.json +
#    preview_start), not just described:
```

Screenshot of the actual rendered page — real data (10001/VINET/Reims, exact legacy
values), real grid, real checkboxes:

> Grid rendered correctly: "Order ID / Customer ID / Employee ID / Freight / Order Date /
> Ship City" columns, rows 10001-10004 visible (10001 VINET 32.38 12/25/2014 Reims, ...),
> checkbox column on the left, page indicator showing "Page 1 of 4 — 0 selected".

Then, real interaction, not just a static render:

1. Clicked the checkbox for order 10001, then order 10003.
2. Clicked "Next" — page 2 showed different rows (10011-10019), confirmed unchecked
   (independent per-row state, not shared).
3. Clicked "Previous" back to page 1, then read the DOM directly:
   ```json
   {"order10001_checked": true, "order10003_checked": true}
   ```
   Both still checked — cross-page selection persistence, genuinely verified, not assumed.
4. Checked console logs (`preview_console_logs`, `level: error`): **"No console logs."**
   — zero errors, across scaffold, build, and every interaction above.
5. Second screenshot: rows 10001 and 10003 visibly checked and highlighted blue, 10002/
   10004 correctly unchecked.

This is what "genuinely browser-testable" means in practice: not "the code looks like it
should work," but an actual running server, an actual rendered page, actual clicks, and
actual DOM state read back and checked against the expectation.

### 12.9 — Honest status

Same discipline as Part 7. `tasks.md` groups 1-4 (backend authoring, mock setup, frontend,
browser verification) are checked off — genuinely done, genuinely verified where
verification was possible in this environment. Group 5 (real ASP.NET Core backend
compiled and run with the actual .NET SDK) is **not** checked off and the change is **not
archived** — `openspec status` still shows this accurately. Whoever has a .NET SDK
available should run `dotnet build && dotnet run` in `modern/OrdersApi`, confirm
`GET /api/checkbox-selection-orders` matches the mock's data, re-point
`VITE_API_BASE_URL` at the real API, re-verify the browser behavior is unchanged, check
off tasks 5.1/5.2, *then* `openspec archive modernize-grid-checkbox-selection`.

---

## Part 13 — Feature 2 in This Workspace, Done End-to-End

Originally documented as a checklist for later. Built it for real instead — same
persistent `aspnet-ej1-demos` folder, same strict SDD discipline as Part 12, same
genuine-browser-verification bar.

### 13.1 — Picking it

Same process as 12.5: from the 96 clean grid candidates in the corrected index, picked one
with a genuinely different interaction model than what's already built.
**`Grid/BasicSelection.aspx`** — click-anywhere-on-row toggle selection
(`Selectiontype="Multiple"`, `SelectionSettings EnableToggle="true"`, **no checkbox
column** — confirmed by reading the markup), 48 rows (8 iterations × 6, one more row per
iteration than CheckboxSelection's 40).

### 13.2 — Full SDD loop, every real command

```bash
cd "C:\Users\SarveshTalele\Documents\aspnet-ej1-demos"

openspec new change modernize-grid-basic-selection \
  --description "Rebuild Grid/BasicSelection.aspx (click-anywhere-on-row toggle multi-selection + paging) as ASP.NET Core Web API + React/TypeScript, third capability in this workspace, second one built end-to-end" \
  --goal "Prove the pattern generalizes to a second, differently-interacting grid capability, genuinely browser-verified"

openspec instructions proposal --change modernize-grid-basic-selection
#   -> authored proposal.md. Why: proving two distinct selection UX models, not just
#      repeating checkbox-selection's pattern.
openspec instructions design --change modernize-grid-basic-selection
#   -> authored design.md. Key Non-Goal, stated explicitly: NOT porting the legacy page's
#      selection-type/selection-mode/enable-toggle property-panel dropdowns — those
#      reconfigure the Syncfusion demo's showcase behavior, not a requirement of the
#      underlying Orders-grid capability. Scope cut, documented, not an oversight.
openspec instructions specs --change modernize-grid-basic-selection
#   -> authored specs/basic-selection-grid-api/spec.md, 5 requirements incl. one
#      requiring NO checkbox column (distinguishing this from capability 2's spec)
openspec instructions tasks --change modernize-grid-basic-selection
#   -> authored tasks.md, same 5-group shape as capability 2

openspec status   --change modernize-grid-basic-selection   # 4/4 artifacts
openspec validate modernize-grid-basic-selection --strict   # valid
```

### 13.3 — Implementation, per tasks.md

**Backend**: `Data/BasicSelectionOrdersRepository.cs` (`BindDataSource()` ported exactly —
48 rows), `Controllers/BasicSelectionController.cs` (`GET /api/basic-selection-orders`).
`Models/Order.cs` genuinely reused this time (the project already existed from
capability 2 — no recreation needed, unlike capability 2's own note about capability 1
not existing yet).

**A second real deviation, caught and documented**: the plan called for a *second*
`json-server` instance on a separate port for this capability's mock. But both grids now
render on the same page simultaneously (`App.tsx` has both), so they need to fetch from a
mock that's running *at the same time*. Realized `json-server` already supports multiple
top-level keys as separate resource endpoints from **one** instance — merged both
capabilities' data into the single existing `mock/db.json`
(`checkbox-selection-orders` + `basic-selection-orders` keys) instead of standing up a
second server:

```bash
python3 -c "... merge db.json + basic-selection-db.json into one dict ..."
# {'checkbox-selection-orders': 40, 'basic-selection-orders': 48}
```

**Frontend**: `src/api/basicSelectionClient.ts` (same configurable-path pattern),
`src/components/BasicSelectionGrid.tsx` — no checkbox column, `onClick` on the `<tr>`
itself toggles a `Set<number>` of selected order IDs (shared across pages, same
persistence pattern as capability 2). Wired into `App.tsx` alongside
`CheckboxSelectionGrid`, both sections clearly headed.

```bash
npm run build
```
```
> tsc -b && vite build
✓ 21 modules transformed.   (up from 19 with one grid)
dist/assets/index-CMZ118a_.js   195.57 kB │ gzip: 61.21 kB
✓ built in 168ms
```

### 13.4 — Real browser verification

Hit a real infrastructure snag first: `json-server --port 3001` failed with
`EADDRINUSE` — a stale process from the capability-2 session was still holding the port.
Found it properly (`netstat -ano | grep :3001`, PID 16672) and killed it
(`taskkill //F //PID 16672`) rather than guessing — the first `curl` test against the
freshly-merged `db.json` returned only 1 row for `basic-selection-orders` because it was
still hitting the *old* process serving the *old* file.

Once restarted cleanly: `curl` confirmed 40 + 48 rows correctly served from one instance.
Opened via a real browser preview. The full-page **screenshot tool itself timed out**
(confirmed via console logs this was a rendering-size/tool issue, not an app error — no
errors logged, all network requests returned 200 OK) — used the accessibility snapshot and
direct DOM queries instead, equally valid evidence of real behavior:

```
firstRowHasCheckbox: false                    <- confirmed no checkbox column
clicked rows 0 and 2 (orders 10001, 10003)
  -> row0 selected: true, row2 selected: true, others: false   <- independent multi-select
clicked row 0 again
  -> row0 selected: false, row2 selected: true                 <- toggle-off, doesn't affect others
paged to page 2 -> confirmed different rows (10011-10020)
paged back to page 1
  -> row2 (order 10003) selected: true, all others false        <- cross-page persistence
console logs (level: error): "No console logs."                 <- zero errors
```

Every one of `specs/basic-selection-grid-api/spec.md`'s scenarios checked against real,
observed DOM state — not assumed from reading the code.

### 13.5 — Honest status

Same discipline as every prior capability: `tasks.md` groups 1-4 checked off (genuinely
done and verified where verification was possible here). Group 5 (real .NET SDK
compile/run) stays unchecked, **change not archived**. `openspec list` confirms both
capabilities sit at the same "not fully done" status honestly:

```
modernize-grid-basic-selection        14/16 tasks
modernize-grid-checkbox-selection     14/16 tasks
```

---

## Part 14 — Feature 3 Checklist (Next, For You To Build)

Both capabilities built so far are *selection* variants (checkbox vs. click-toggle). A
genuinely different next capability — not just a third selection style — is
**`Grid/BatchEditing.aspx`**: inline create/update/delete on the grid, not just
selecting rows. Confirmed no direct SQL (`grep -c "SqlConnection|SqlCommand"` → `0`),
same in-memory-data pattern as the first two. This is a checklist, not an
implementation — the point of documenting it this way (rather than building it) is so
you can run it yourself and see the same discipline hold up on a capability with
real write operations, not just reads.

```bash
cd "C:\Users\SarveshTalele\Documents\aspnet-ej1-demos"

# 1. Create the change
openspec new change modernize-grid-batch-editing \
  --description "Rebuild Grid/BatchEditing.aspx (inline add/edit/delete rows, batch-saved) as ASP.NET Core Web API + React/TypeScript" \
  --goal "Fourth capability in this workspace; first one involving writes, not just reads/selection"

# 2. Author all 4 artifacts — read Grid/BatchEditing.aspx.cs FIRST to see the exact
#    batch-save semantics (does it PUT/POST/DELETE per row, or one batch payload?)
#    before writing the design — that answer belongs in design.md's Decisions, not
#    guessed
openspec instructions proposal --change modernize-grid-batch-editing
openspec instructions design   --change modernize-grid-batch-editing
openspec instructions specs    --change modernize-grid-batch-editing
openspec instructions tasks    --change modernize-grid-batch-editing

openspec status   --change modernize-grid-batch-editing
openspec validate modernize-grid-batch-editing --strict

# 3. Implementation will need MORE than GET this time:
#    - Backend: GET (list) + POST (create) + PUT (update) + DELETE, or a single
#      POST /batch endpoint if the legacy page truly batches — check the legacy
#      code-behind's actual save handler before deciding, don't assume REST-per-row
#    - json-server (already installed) supports POST/PUT/DELETE/PATCH out of the box
#      against its flat resource keys — no extra mock code needed for local write
#      verification, same zero-code-mock principle as capabilities 1 and 2
#    - Frontend: an editable grid needs meaningfully more component state than the
#      read-only grids built so far (dirty-row tracking, save/cancel) — don't
#      underscope tasks.md for this relative to capabilities 1/2

# 4. Real browser verification this time MUST include an actual write round-trip:
#    add a row, edit a cell, delete a row, save, reload the page, confirm the
#    change persisted in the mock's in-memory/file store — a read-only click-and-
#    look verification (sufficient for capabilities 1/2) is NOT sufficient evidence
#    for a capability whose entire point is writes

# 5. Same honesty discipline: mark tasks.md checkboxes only for what you actually
#    verified running, leave real-.NET-SDK-backend verification unchecked and the
#    change unarchived until you actually have dotnet available
```

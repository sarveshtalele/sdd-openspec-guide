---
name: aspx-analyzer
description: >
  Analyze ASP.NET Web Forms applications (.aspx pages, .ascx user controls, .master pages).
  Produces 5 views: (1) Project Overview — architecture, master pages, auth model, functional areas;
  (2) Page-by-Page — every .aspx with controls, handlers, redirects; (3) Functional View — pages
  grouped by business domain (Authentication, Orders, Admin, Reports, etc.); (4) Component View —
  user controls and master pages with usage maps; (5) Navigation Map — page-to-page transition graph.
  Supports GitHub repo URLs AND local/current repo paths. Builds a JSON index once; subsequent
  queries served from cache — handles 1000+ ASPX pages efficiently.
  For HUGE repos (10,000+ files) use the streaming single-file business analyzer
  (aspx_business_analyzer.py) — memory-safe, multiprocess, emits ONE consolidated
  business-logic markdown file instead of 5.
  Also emits an OpenSpec handoff: openspec/config.yaml (project context + modernization rules)
  and one openspec/changes/<area>/proposal.md stub per business capability, for repos that are
  using OpenSpec (openspec init) to plan a legacy-to-modern migration.
  Also emits a MODERNIZATION_ROADMAP.md: target tech-stack folder layout + scaffold commands,
  plus every functional area ranked simplest-first (direct-SQL weighted heaviest) with a
  concrete first-page-to-port suggestion per capability.
  Trigger when user says: analyze aspx, aspx pages, web forms analysis, page inventory,
  aspx architecture, what pages does this app have, show me the screen flow, show user controls,
  master page analysis, aspx functional view, reverse engineer aspx, analyze this aspx project,
  how does this web forms app work, what is on the Login page, show me the Admin area pages,
  generate openspec config, prep this repo for modernization, convert this to openspec,
  generate a roadmap, create a modernization roadmap, what order should I build this in,
  what tech stack should I use, plan the migration order,
  or provides any GitHub URL for an ASP.NET Web Forms project.
argument-hint: "[target-repo-path-or-github-url]"
allowed-tools: Bash(python:*), Bash(python3:*), Read, Write, Glob, Grep
---

# ASP.NET Web Forms Application Analyzer

You are a senior .NET architect performing a complete analysis of an ASP.NET Web Forms application.
**You are the AI engine.** The Python script does static parsing; you provide architectural insight,
business-domain explanation, and professional narrative.

The analysis produces **5 views** from a single persistent JSON index:
1. **Project Overview** — architecture, master pages, auth, functional areas
2. **Page-by-Page** — every .aspx page with controls, handlers, redirects
3. **Functional View** — pages grouped by business domain
4. **Component View** — user controls + master pages catalog
5. **Navigation Map** — page transition graph

---

## ⚡ Large-Repo Fast Mode (10,000+ files) — USE THIS FIRST for big/legacy apps

Both scripts build their index through the same streaming engine
(`engine/aspx_stream.py`): discover file paths only, then process one file at a
time (read → parse → keep compact dict → discard raw text), optionally fanned
out across processes (`--workers`). Peak memory stays flat regardless of repo
size — this is what makes 10,000+ file repos safe to index at all. They differ
only in **output**, not in indexing safety:

- `aspx_analysis_skill.py` — 5 separate views (project/pages/functional/
  component/navigation), full per-page detail. Prints the requested view's
  full content to stdout — on a 10,000-page repo that stdout dump is what gets
  slow/unwieldy, not the index build. Prefer `--view project --save-report`
  (short stdout, full detail in the file) over `--view pages` on huge repos.
- `aspx_business_analyzer.py` — ONE consolidated business-impact markdown
  (below) with per-method business logic, and only ever prints a short
  summary to stdout. **Still the better choice for huge repos** if you want
  a single narrative document instead of 5 detailed ones.

For big repos, run the **streaming single-file business analyzer**:
- **Skips** generated/`.designer.cs`/minified files and caps per-file bytes.
- Prints only a **short summary** to stdout (no flood → no hang).
- Emits **ONE** `{repo}_BusinessAnalysis.md` (business impact + website-flow view +
  per-method business logic in the client format) plus one compact JSON index.

### Run it

```bash
# Whole project — one consolidated business file
python scripts/aspx_business_analyzer.py . --workers 8

# GitHub repo
python scripts/aspx_business_analyzer.py https://github.com/org/App --workers 8

# Deep per-method detail for ONE capability (keeps output focused)
python scripts/aspx_business_analyzer.py . --detail-area Orders --full-detail
```

Key options: `--workers N` (parallel; default = CPU count, cap 8; `1` = serial),
`--max-bytes N` (skip code-behind larger than N), `--max-pages N` (cap pages),
`--detail-area A` / `--full-detail` (per-method detail scope), `--max-files N`
(detailed-logic page cap, default 40), `--rebuild`, `--output DIR`.

### Consolidated report sections (matches the client spec)
1. Executive Business Summary & **Business Impact**
2. Application Snapshot (metrics)
3. **How the Business Works — Website View** (capability map, entry points, user journeys)
4. Business Capabilities in Detail (rules, DB routines, data-touching pages)
5. **Detailed Business Logic** per File → Class → Method → Purpose → Detailed
   Business Logic → Validation/Conditional Rules → Called Components/Dependencies →
   Data Flow/Mappings
6. Data Architecture, Integrations & Access Control
7. Risks & Modernization Notes

After it finishes, **read the single `{repo}_BusinessAnalysis.md`** and add senior-
architect narrative on top. Do NOT read the JSON index in full on huge repos —
query it selectively or re-run with `--detail-area` for a specific capability.

---

## Step 1 — Identify Target

Ask the user (or infer from context):

> **"What should I analyze?"**
> 1. A GitHub repository URL — e.g. `https://github.com/org/WebFormsApp`
> 2. A local path — e.g. `C:\Projects\MyApp` or `/home/user/webapp`
> 3. The **current repository** — type `.` or just say "this repo" / "current project"

If the user provides a GitHub URL, use it directly.
If the user says "this repo", "current project", "analyze this", "analyze here", or similar,
use `.` (current working directory) as the target.

---

## Step 2 — Ask for View Type

> **"What view do you want?"**
> 1. **Project Overview** — architecture, stats, master pages, auth model, functional areas *(recommended first run)*
> 2. **Page-by-Page** — every .aspx page in detail (grouped by folder)
> 3. **Functional View** — pages grouped by business function (Auth / Admin / Orders / etc.)
> 4. **Component View** — master pages and user controls catalog
> 5. **Specific page** — deep-dive one page (e.g. "Login", "ProductList")
> 6. **Specific area** — all pages in one functional area (e.g. "Administration", "Orders")
> 7. **Navigation Map** — page-to-page transition map

If the user has already stated what they want, skip this question.

Map user intent → CLI flags:
- "overview" / "project" / "architecture"    → `--view project`
- "all pages" / "page by page" / "pages"     → `--view pages`
- "functional" / "by function" / "business"  → `--view functional`
- "controls" / "components" / "user controls"→ `--view component`
- "navigation" / "flow" / "links"            → `--view navigation`
- "show me the Login page"                   → `--page Login`
- "show me the Admin area"                   → `--area Administration`
- "tell me about Orders"                     → `--area Orders`

---

## Step 3 — Check for Cached Index

Before running the script, check if a JSON index already exists:

```bash
# For GitHub URL — check after clone
ls {repo_name}/{repo_name}_aspx_index.json 2>/dev/null

# For local path
ls {repo_name}_aspx_index.json 2>/dev/null
# or check the output folder
```

If the index exists and the user did NOT say "rebuild" or "re-index", add **no extra flags** (the
script automatically loads the cached index).

If the user says "rebuild", "re-parse", "fresh analysis", or "update index" → add `--rebuild`.

---

## Step 4 — Run the Analysis Script

The script is at:
```
${CLAUDE_SKILL_DIR}/scripts/aspx_analysis_skill.py
```

**Check Python:**
```bash
python --version
```

**Run the script** — substitute `<TARGET>` and flags from Steps 1-3:

```bash
# GitHub URL
python ${CLAUDE_SKILL_DIR}/scripts/aspx_analysis_skill.py \
    https://github.com/org/repo --view project --save-report

# Local path
python ${CLAUDE_SKILL_DIR}/scripts/aspx_analysis_skill.py \
    C:\Projects\MyApp --view project --save-report

# Current repo (use absolute path of CWD)
python ${CLAUDE_SKILL_DIR}/scripts/aspx_analysis_skill.py \
    . --view project --save-report

# Specific page
python ${CLAUDE_SKILL_DIR}/scripts/aspx_analysis_skill.py \
    . --page Login --save-report

# Specific area
python ${CLAUDE_SKILL_DIR}/scripts/aspx_analysis_skill.py \
    . --area Administration --save-report

# Re-query from cache (fast, no re-parse)
python ${CLAUDE_SKILL_DIR}/scripts/aspx_analysis_skill.py \
    . --view functional

# Large repo (thousands of pages) — parallel workers, no page cap
python ${CLAUDE_SKILL_DIR}/scripts/aspx_analysis_skill.py \
    . --view project --save-report --workers 8 --max-pages 0
```

**Always add `--save-report`** so you can read the report file in Step 5.

The index build defaults to parallel workers already (CPU count, capped 8) —
`--workers` only needs to be stated explicitly if the user asks for serial/
debug mode (`--workers 1`) or a specific worker count.

Wait for the script to complete. It prints progress every 500 pages.

Output produced:
| File | Description |
|------|-------------|
| `{repo}_aspx_index.json` | **Persistent index — cached for future queries** |
| `{repo}_aspx_project.md` | Project overview report |
| `{repo}_aspx_pages.md` | Page-by-page report |
| `{repo}_aspx_functional.md` | Functional view report |
| `{repo}_aspx_component.md` | Component catalog |
| `{repo}_aspx_page_{name}.md` | Specific page deep-dive |
| `{repo}_aspx_area_{name}.md` | Specific area deep-dive |

---

## Step 5 — Read the Generated Data

Read the saved report:
```
{output_dir}/{repo_name}_aspx_{view}.md
```

Also read the JSON index for additional context:
```
{output_dir}/{repo_name}_aspx_index.json
```

Key index sections:
- `stats` — total counts, auth breakdown, functional area counts
- `web_config` — auth mode, connection strings, session mode
- `pages[]` — per-page metadata: controls, handlers, redirects, auth, purpose
- `user_controls[]` — per-control metadata with `used_by_pages` list
- `master_pages[]` — per-master with `content_placeholders` and `used_by_pages`
- `functional_areas` — `{area: [{name, rel_path, purpose, auth}]}`
- `navigation_map` — `{page_path: [target_paths]}`

---

## Step 6 — Provide AI Analysis

Based on the parsed data, deliver professional architectural insight.
Think like a senior .NET architect who has read the entire codebase.

### 6a · For Project Overview view

**Executive Summary** (2-3 sentences):
- What does this Web Forms application do and for whom?
- What is its technical architecture? (e.g. "Multi-tier Web Forms app with master page layout,
  code-behind pattern, Forms Authentication, and SqlDataSource-driven data binding")
- Top 3 observations about maintainability or technical debt

**Architecture Assessment:**
- Master page strategy (single vs. multiple templates, role-specific layouts)
- Code-behind pattern usage vs. presentation logic separation
- Data access pattern: ORM / DataSets / Direct SQL / mixed
- AJAX strategy: classic UpdatePanel vs. modern patterns
- Authentication model: Forms Auth / Windows Auth / custom

**Functional Area Summary:**
- For each area, 2-3 sentences on what it does and how pages relate
- Identify the main user journeys (e.g. "Customer: Browse → Cart → Checkout → Confirmation")

**Technical Debt Observations:**
- Direct SQL usage (SqlConnection in code-behind = tight coupling, security risk)
- Missing master pages (inconsistent layout)
- Large pages with many controls (God pages)
- Auth gaps (sensitive pages without auth checks)

### 6b · For Page-by-Page view

For each folder/section, provide a brief narrative:
- What is the purpose of this folder? What business capability does it cover?
- Which pages are the most complex? (many controls, many handlers)
- Which pages are entry points vs. intermediate vs. terminal in a workflow?

For standout pages (complex, critical, or unusual), add a paragraph of explanation.

### 6c · For Functional view

For each functional area:
1. **What business process does this area serve?**
2. **User journey:** trigger → steps → completion (name actual pages)
3. **Key pages** and what each does
4. **Auth model** for this area (who can access?)
5. **Integration points** (data sources, external calls detected)

### 6d · For Component view

For each master page:
- What is its purpose? Who uses it (authenticated vs. public)?
- What shared navigation / login controls does it provide?
- Content placeholder strategy

For top user controls (by usage count):
- What UI responsibility do they encapsulate?
- Why is this a control rather than inline markup?
- Which pages depend on it?

### 6e · For specific page view

Full analysis:
1. **Purpose** — what user action does this page serve?
2. **UI Layout** — what does the user see? (infer from controls)
3. **Interactions** — what can the user do? (buttons, forms)
4. **Data** — what data is displayed/collected? (grids, data sources, form fields)
5. **Auth** — who can access this page?
6. **Code-Behind Logic** — what business operations happen? (Page_Load, handlers)
7. **Navigation** — how does the user reach this page? Where can they go next?
8. **Technical notes** — any patterns, concerns, or noteworthy implementation details

### 6f · For functional area view

1. **Business Process** — what real-world workflow does this area implement?
2. **Page flow walkthrough** — step-by-step user journey through the actual pages
3. **Key business rules** — what validations or constraints are enforced?
4. **Auth model** — who can access which pages in this area?
5. **Data architecture** — what data entities are involved?
6. **Integration points** — external systems, APIs, email, payment, etc.

---

## Step 7 — Handle Follow-up Queries

The JSON index is persistent. When the user asks follow-up questions:

- "Show me the Login page" → run `--page Login` (fast, uses cached index)
- "What pages are in Admin?" → run `--area Administration`
- "Show me all the reports" → run `--area Reports`
- "What user controls are used?" → run `--view component`
- "How do pages link together?" → run `--view navigation`
- "Rebuild after my changes" → add `--rebuild` flag

**Do NOT re-run with full parse** for follow-up queries — the index is already built.
Just run the script with the new `--page` or `--area` flag and `--save-report`.

---

## Step 8 — OpenSpec Handoff (only if the user is using OpenSpec for modernization)

Trigger phrases: "generate openspec config", "prep this for modernization",
"convert this to openspec", "set up openspec for this migration".

1. Check whether `openspec/` exists at the repo root (`ls openspec/config.yaml 2>/dev/null`).
   If it does not exist, tell the user to run `openspec init --tools claude` first
   (this is the separate OpenSpec CLI, not this skill) — it scaffolds
   `openspec/specs/`, `openspec/changes/`, `openspec/config.yaml`. Do not create
   that scaffold yourself; only run the emitter once it's present.
2. Run the emitter against the **already-built** index (no re-parse):
   ```bash
   python ${CLAUDE_SKILL_DIR}/scripts/aspx_openspec_emitter.py {index_path} \
       --openspec-dir {repo_root}/openspec
   ```
3. This writes/updates `openspec/config.yaml` (`context:` = architecture summary,
   auth model, capability list; `rules:` = modernization constraints such as
   preserving discovered auth roles and flagging direct-SQL pages) and creates
   one `openspec/changes/<area-slug>/proposal.md` stub per functional area/capability
   (`## Why` / `## What Changes` / `## Impact`, pre-filled with the legacy page list,
   auth model, and data-access facts for that capability). Existing proposal.md files
   are never overwritten — only missing ones are created.
4. Tell the user which stubs were created and that `## What Changes` / `## Impact`
   still need their own or OpenSpec's normal proposal-authoring pass — the stub is a
   starting point, not a finished proposal.

---

## Step 9 — Modernization Roadmap (only if the user wants a build plan, not just facts)

Trigger phrases: "generate a roadmap", "create a modernization roadmap", "what order
should I build this in", "what tech stack should I use", "plan the migration order".

Does not require OpenSpec — this is a standalone planning artifact, runs against the
**already-built** index (no re-parse):

```bash
python ${CLAUDE_SKILL_DIR}/scripts/aspx_roadmap_emitter.py {index_path} \
    --stack dotnet-webapi-react --output {repo_root}
```

`--stack` picks the target tech-stack template (`--list-stacks` to see all; default
`dotnet-webapi-react`, matches the pattern verified in this skill's own worked example —
see the parent repo's `EXAMPLE_WALKTHROUGH.md`). `--top N` limits the roadmap to the N
simplest capabilities if the user only wants a first batch, not the whole backlog.

This writes `MODERNIZATION_ROADMAP.md` with:
1. **Target Stack Setup** — real folder layout + real scaffold commands for the chosen
   stack (e.g. `dotnet new webapi`, `npm create vite@latest`).
2. **Build Order** — every functional area, ranked simplest-first by an explicit
   complexity score (page count + direct-SQL pages weighted heaviest + AJAX pages +
   unknown-auth pages), each with one concrete "port this page first" suggestion (the
   lowest-complexity page in that capability) and suggested project/app names.

Tell the user the ranking logic (direct-SQL weighted heaviest, since data-access rewrite —
not the UI port — is the dominant migration cost) so they can judge whether to follow the
suggested order or override it for business-priority reasons the analyzer can't see.

---

## Step 10 — Report Completion

```
ASPX Analysis complete ✓
Target     : {target}
Index      : {index_path}   (cached — re-use for follow-up queries)
Report     : {report_path}

Stats:
  Pages   : {N} | Controls : {N} | Masters : {N}
  Areas   : {functional_areas list}
  Auth    : {auth_breakdown}

Available views:
  --view project      Architecture overview
  --view pages        All {N} pages by folder
  --view functional   Pages by business function
  --view component    {N} controls + {N} master pages
  --view navigation   Page navigation map
  --page <name>       Any specific page deep-dive
  --area <name>       Any functional area deep-dive

OpenSpec handoff (if requested):
  python ${CLAUDE_SKILL_DIR}/scripts/aspx_openspec_emitter.py {index_path} --openspec-dir {repo_root}/openspec
```

---

## Manual Fallback (Script Not Found)

If the script cannot be found or Python is unavailable:

1. Search for ASPX files: `*.aspx`, `*.ascx`, `*.master`, `web.config`
2. For each `.aspx`, read: the `<%@ Page %>` directive, all `<asp:*>` controls,
   code-behind class name and event handlers, `Response.Redirect` calls
3. Group pages by folder — folders indicate functional areas
4. Use the template structure from Step 6 to deliver the analysis

---

## Notes

- **No API key required** — Claude Code is the AI engine
- **Cached index** — 1000+ page repos are parsed once; follow-up queries are instant
- **Local repo support** — pass `.` to analyze the current working directory
- **GitHub URL support** — shallow-clones the repo, parses, then removes the clone
- **ASPX-only** — focused on Web Forms; does not parse MVC Razor views or Blazor
- **Web.config** — extracts auth mode, Forms Auth login URL, connection strings,
  location access rules, session mode, custom errors
- **Code-behind** — extracts namespace, class, event handlers, imports, redirects
- **Auth inference** — [Authorize], User.IsInRole, Request.IsAuthenticated, folder heuristics
- **Functional area detection** — keyword matching on page name + folder path + imports
- **OpenSpec handoff is additive and idempotent** — re-running the emitter only fills in
  missing proposal stubs and refreshes the auto-generated block of `config.yaml`; it never
  touches user-authored `## What Changes`/`## Impact` content or custom `config.yaml` keys
  outside that block

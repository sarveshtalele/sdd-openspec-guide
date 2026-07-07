# The Complete OpenSpec Guide — Setup, Daily Use, and Legacy Migration

A standalone reference for [OpenSpec](https://github.com/Fission-AI/OpenSpec) (v1.5.0) —
install it, run it day-to-day on any project, and use it to migrate a legacy codebase
end-to-end. Every command and behavior here was actually run and verified while building
this repo — see [README.md](README.md) and
[example-walkthrough/EXAMPLE_WALKTHROUGH.md](example-walkthrough/EXAMPLE_WALKTHROUGH.md)
for the real, full transcript this guide is distilled from. For execution-model
mechanics and Claude Code integration specifically, see
[OPENSPEC_HANDBOOK.md](OPENSPEC_HANDBOOK.md) — this guide covers usage and workflow, the
Handbook covers precisely what runs, what invokes what, and when.

**One-sentence execution model**: OpenSpec is a file-based planning tool — it never
compiles or runs application code. It produces `tasks.md`; a developer (or Claude Code,
on instruction) then implements those tasks with ordinary tools (`dotnet`, `npm`).
Full breakdown: `OPENSPEC_HANDBOOK.md` Part 1.

---

## Table of Contents

- [Part 1 — What OpenSpec Is](#part-1--what-openspec-is)
- [Part 2 — Install](#part-2--install)
- [Part 3 — Initialize in a Project](#part-3--initialize-in-a-project)
- [Part 4 — Command Reference (Every Command, One Line, When to Use It)](#part-4--command-reference-every-command-one-line-when-to-use-it)
- [Part 5 — The Core SDD Loop (Any Feature, Any Project)](#part-5--the-core-sdd-loop-any-feature-any-project)
- [Part 6 — End-to-End: Migrating a Legacy Project](#part-6--end-to-end-migrating-a-legacy-project)
- [Part 7 — Every Command, As Used in This Project](#part-7--every-command-as-used-in-this-project)
- [Part 8 — How to Build Your Next Feature in This Project](#part-8--how-to-build-your-next-feature-in-this-project)
- [Part 9 — Real Gotchas (Found the Hard Way)](#part-9--real-gotchas-found-the-hard-way)
- [Part 10 — Multiple People, One Project](#part-10--multiple-people-one-project)
- [Part 11 — FAQ](#part-11--faq)

---

## Part 1 — What OpenSpec Is

A spec layer, not a project-management tool. The idea: agree on **what** to build, in
writing, before code gets written — by you, or by an AI assistant acting on your behalf.
Every unit of work ("a change") produces four artifacts, in order:

| Artifact | Answers |
|---|---|
| `proposal.md` | Why is this happening? What changes? What's the impact? |
| `specs/<capability>/spec.md` | What are the exact requirements (Given/When/Then scenarios)? |
| `design.md` | How will it be built — architecture, key decisions, trade-offs? |
| `tasks.md` | What's the ordered, checkable implementation checklist? |

Once a change is **archived**, its spec deltas merge into `openspec/specs/` — the
durable, living source of truth for what the system actually does. That's the entire
point: six months later, `openspec/specs/` tells you real current behavior, not what a
stale PR description once claimed.

---

## Part 2 — Install

Needs Node.js.

```bash
npm install -g @fission-ai/openspec@latest
openspec --version   # this guide was verified against 1.5.0
```

Upgrade later the same way (`npm install -g @fission-ai/openspec@latest` again); refresh
an already-initialized project's generated AI-tool instructions with `openspec update`.

---

## Part 3 — Initialize in a Project

Run inside whatever repo you're adding specs to (a legacy app, a greenfield project, this
guide's own repo — doesn't matter):

```bash
cd your-project
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

`--tools claude` generates Claude Code integration. Use `--tools all` for every supported
AI assistant, `--tools none` for a bare scaffold. **Only `openspec/config.yaml` is
created immediately** — `openspec/specs/` and `openspec/changes/` don't exist as folders
yet; they appear the first time you run `openspec new change`. Don't be alarmed if you
don't see them right after `init`.

This also creates 5 Claude Code skills under `.claude/skills/`:
`openspec-propose`, `openspec-explore`, `openspec-apply-change`, `openspec-sync-specs`,
`openspec-archive-change` — same discovery mechanism as any other Claude Code Agent
Skill. (The CLI's own printed hint, `Start your first change: /opsx:propose "your idea"`,
doesn't match these real skill names — a cosmetic wording quirk in v1.5.0. Invoke the
real skill by its real name, `openspec-propose`.)

If a repo already has partial/broken `openspec/` remnants, add `--force` to clean up
before re-scaffolding.

---

## Part 4 — Command Reference (Every Command, One Line, When to Use It)

Verified against the real installed CLI (`openspec --help` and every subcommand's
`--help`), not documentation that may be stale.

### Core workflow — you'll use these constantly

| Command | One line | When to use it |
|---|---|---|
| `openspec init [path]` | Scaffold `openspec/` in a project | Once, per project, before anything else |
| `openspec new change <name>` | Create a new change folder | Starting any new feature/capability |
| `openspec instructions <artifact> --change <name>` | Print the exact write-path + authoring template for one artifact | Right before writing `proposal.md`/`design.md`/`specs/*.md`/`tasks.md` — this is how you (or an AI) know exactly what to write and where |
| `openspec status --change <name>` | Show which of the 4 artifacts are done vs. blocked | Checking progress mid-change, or confirming you're ready for the next artifact |
| `openspec validate <name> --strict` | Check a change's artifacts are structurally correct | After authoring artifacts, and again after implementation, before archiving |
| `openspec archive <name>` | Merge a change's spec deltas into `openspec/specs/`, move it to history | Only once every task in `tasks.md` is genuinely verified — not just written |
| `openspec list` | List all in-flight changes (or `--specs` for durable specs) | Checking what's already being worked on before starting something new |
| `openspec show <name>` | Print one change's or spec's full content | Reviewing a change without opening every file individually |

### Supporting / reference — used less often, still real

| Command | One line | When to use it |
|---|---|---|
| `openspec update [path]` | Refresh generated AI-tool instructions after an OpenSpec upgrade | After `npm install -g @fission-ai/openspec@latest` bumps your CLI version |
| `openspec view` | Interactive dashboard of specs + changes | Browsing visually instead of via `list`/`show` |
| `openspec doctor` | Health-check the resolved OpenSpec root | Something feels broken and you're not sure why |
| `openspec context` | Print the working context that gets injected into prompts | Debugging why an AI's output doesn't reflect your `config.yaml` |
| `openspec templates --schema <name>` | Show resolved template paths for a schema's artifacts | Customizing what an artifact template actually asks for |
| `openspec schemas` | List available workflow schemas with descriptions | Checking what schemas exist before forking one (a fresh install has exactly one: `spec-driven`) |
| `openspec schema init/fork/validate/which` | Manage custom workflow schemas *(experimental)* | Only if the default proposal→specs→design→tasks shape doesn't fit your team |
| `openspec config path/list/get/set/unset/reset/edit` | View/modify global OpenSpec CLI config | Checking or changing CLI-wide settings (not per-project) |
| `openspec config profile [preset]` | Show/set the workflow profile | Checking which skills your profile grants — the non-interactive `[preset]` shortcut only accepts `core`, see the note below the tables |
| `openspec feedback <message>` | Submit feedback to the OpenSpec maintainers | Reporting a bug or suggestion |
| `openspec completion` | Manage shell completions | One-time shell setup convenience |

### Advanced / multi-repo — skip unless you need this specifically

| Command | One line | When to use it |
|---|---|---|
| `openspec store setup/register/unregister/remove/list/doctor` | Create/manage standalone OpenSpec repos registered on your machine | Centralizing specs across multiple codebases — not needed for a single project |
| `openspec workset create/list/open/remove` | Compose personal, local-only working views across stores | Same — multi-repo power-user feature |

**Profiles, precisely (re-verified against the official repo's docs and the actual
installed CLI, since the two disagree with each other in one spot):**

Official docs (`docs/commands.md`, `docs/faq.md`, quoted directly) describe two
profiles: **core** (default — `propose`, `explore`, `apply`, `sync`, `archive`) and
**expanded** (adds `new`, `continue`, `ff`, `verify`, `bulk-archive`, `onboard`), selected
via `openspec config profile` (interactive) then applied to a project with
`openspec update`.

What's directly verified against the real CLI (v1.5.0, freshly reinstalled at `@latest`):
- `openspec init --help` names the second option **"custom"**, not "expanded" —
  `--profile <profile>  Override global config profile (core or custom)`. The official
  docs and the CLI's own `--help` text disagree with each other on the name; not
  something this guide got wrong, a real inconsistency in the upstream project itself.
- The **non-interactive shortcut form fails for both names**: `openspec config profile
  expanded` and `openspec config profile custom` both error with
  `Unknown profile preset "<name>". Available presets: core`. Selecting the second
  profile appears to require a genuine interactive terminal session
  (`openspec config profile` with no argument, then choosing from a picker) — not
  scriptable via a single non-interactive command, and not something this guide could
  fully exercise in a non-TTY environment. If you're scripting/automating OpenSpec setup
  (CI, a setup script), plan for `core` only unless you've confirmed interactively that
  the second profile activates in your terminal.
- What *is* fully verified either way: the granular, step-by-step mechanism
  `openspec instructions <artifact> --change <name>` — used throughout this guide and
  the companion project regardless of profile, and not gated behind either profile.

---

## Part 5 — The Core SDD Loop (Any Feature, Any Project)

**Fast path** — small/well-understood change: ask your AI assistant to use the
`openspec-propose` skill with a description of what you want. It creates the change
directory and all 4 artifacts together in one step. Review them, then have it use
`openspec-apply-change` to implement `tasks.md`.

**Granular path** — what every real capability in this guide's companion project
actually used, and what you need whenever a change didn't start via the propose skill:

```bash
# 1. Create the shell
openspec new change <name> --description "..." --goal "..."

# 2. Author each artifact, one at a time — each command prints the exact write
#    path, section-by-section rules, and a fill-in-the-blanks template
openspec instructions proposal --change <name>   # -> write proposal.md
openspec instructions design   --change <name>   # -> write design.md
openspec instructions specs    --change <name>   # -> write specs/<capability>/spec.md
openspec instructions tasks    --change <name>    # -> write tasks.md

# 3. Confirm before implementing
openspec status   --change <name>          # expect: 4/4 artifacts complete
openspec validate <name> --strict          # expect: valid

# 4. Implement STRICTLY per tasks.md — no freehand changes outside what a task
#    line specifies. Check off boxes only for what you actually verified running,
#    not just wrote.

# 5. Re-validate, then archive — only once real verification is done
openspec validate <name> --strict
openspec archive <name>
```

Each artifact is gated on the one before it — `openspec status` shows
`[-] design (blocked by: proposal)` until the proposal exists, so you can't skip ahead
by accident.

**The single most important discipline**: don't archive a change whose verification
tasks aren't actually done. Archiving is a claim that the work is real and its spec
deltas are trustworthy going into `openspec/specs/` — treat it that way, not as a
"mark as finished" formality. Neither capability in this repo's `modernization/`
folder is archived yet, specifically because their backend-compile tasks need a real
.NET SDK that wasn't available while building them — see
[README.md](README.md)'s Status table.

---

## Part 6 — End-to-End: Migrating a Legacy Project

The generic version of what this repo actually did (see
[README.md](README.md)'s "How OpenSpec + the aspx-analyzer Skill Integrate Here" for the
concrete, tool-specific version):

```
1. Get a static-analysis tool to read the legacy codebase and produce ONE structured
   index of it — pages/modules, controls/components, auth model, data-access patterns,
   direct-SQL usage, functional groupings. (This repo used a custom Claude Code skill,
   aspx-analyzer, for an ASP.NET Web Forms app — but the pattern generalizes to any
   language/framework with an equivalent analyzer.)
        │
        ▼
2. Project that index into two things:
   a. openspec/config.yaml's context+rules — so every future `openspec instructions`
      call already knows the tech stack, without re-typing it per change.
   b. One proposal stub per functional area/capability, pre-filled with real facts
      (actual file/page names, actual auth model, actual data-access risk) — not
      invented placeholders.
        │
        ▼
3. Rank capabilities simplest-first (fewest direct-SQL touchpoints, fewest external
   dependencies) so you build momentum and prove the pattern before tackling the
   highest-risk pieces. Pick ONE to start.
        │
        ▼
4. Run the Core SDD Loop (Part 5) for that one capability — proposal names the exact
   legacy files being replaced, design documents the target architecture and explicit
   Non-Goals (don't silently expand scope), specs capture the exact requirements,
   tasks.md is the implementation checklist.
        │
        ▼
5. Implement strictly per tasks.md. Verify genuinely — if part of your stack can't be
   run in your environment (e.g. no local runtime for the target backend), say so
   explicitly in tasks.md rather than checking the box anyway.
        │
        ▼
6. Validate, archive only what's truly done. Move to the next capability in your
   ranked list. Repeat.
```

This repo is the concrete, fully-real proof of that loop: 1147 real legacy pages
analyzed, a real bug in the analyzer found and fixed *during* capability selection (an
undercounted control type that was hiding 107 real pages from the capability rankings),
two real capabilities built and genuinely browser-verified, one intentionally left as a
checklist for the next person. Read
[example-walkthrough/EXAMPLE_WALKTHROUGH.md](example-walkthrough/EXAMPLE_WALKTHROUGH.md)
for every command and every real result.

---

## Part 7 — Every Command, As Used in This Project

Part 4 is generic. This is the same commands against the real
`modernization/openspec/` in this repo — every invocation below was actually run while
building `modernize-grid-checkbox-selection` and `modernize-grid-basic-selection` (see
`example-walkthrough/EXAMPLE_WALKTHROUGH.md` Parts 12–13 for the full transcripts each
of these is pulled from).

All of these run from `modernization/` (`cd modernization` first):

| Command | Real invocation in this project | What it actually did/returned here |
|---|---|---|
| `openspec init` | `openspec init --tools claude` (run once, at project start) | Created `openspec/config.yaml` + 5 skills under `.claude/skills/` |
| `openspec new change` | `openspec new change modernize-grid-checkbox-selection --description "Rebuild the legacy Grid/CheckboxSelection.aspx Web Forms demo..." --goal "Second real modernization proof..."` | `Created change 'modernize-grid-checkbox-selection' at openspec\changes\modernize-grid-checkbox-selection/` |
| `openspec instructions proposal` | `openspec instructions proposal --change modernize-grid-checkbox-selection` | Printed the write path + template; result authored to `openspec/changes/modernize-grid-checkbox-selection/proposal.md` |
| `openspec instructions design` | `openspec instructions design --change modernize-grid-checkbox-selection` | Printed dependency info (reads `proposal.md` first) + template; result authored to `design.md` — this is where the "share the existing `OrdersApi` project instead of a new one" decision got documented |
| `openspec instructions specs` | `openspec instructions specs --change modernize-grid-checkbox-selection` | Result authored to `specs/checkbox-selection-grid-api/spec.md` — 5 requirements, each with `#### Scenario` blocks |
| `openspec instructions tasks` | `openspec instructions tasks --change modernize-grid-checkbox-selection` | Result authored to `tasks.md` — 5 numbered groups (backend / mock / frontend / browser verification / deferred real-backend verification) |
| `openspec status --change` | `openspec status --change modernize-grid-basic-selection` | `Progress: 4/4 artifacts complete` once all 4 were authored |
| `openspec validate --strict` | `openspec validate modernize-grid-checkbox-selection --strict` | `Change 'modernize-grid-checkbox-selection' is valid` — run right after authoring, and again after implementation |
| `openspec list` | `openspec list` (no args) | Real output showed 13 changes: the 2 built capabilities at `14/16 tasks` each, plus 11 unused proposal stubs (`administration`, `orders`, `search`, ... — one per functional area, seeded by `aspx_openspec_emitter.py`) with `No tasks` |
| `openspec archive` | **Not run yet, deliberately** | Both built capabilities are still `14/16` — the 2 unchecked tasks in each are real-.NET-SDK backend verification, unavailable in the authoring environment. Archiving before that would be a false claim of "done" — see Part 9's honesty-discipline gotcha |

**Not used in this project (and why):** `openspec view`/`openspec context`/`openspec doctor`
weren't needed — no runtime issues came up that needed diagnosing. `openspec schema *`
wasn't touched — the default `spec-driven` schema fit both capabilities as-is, no need to
fork it. `openspec store`/`workset` are multi-repo features and this is a single project.

---

## Part 8 — How to Build Your Next Feature in This Project

Concrete, step-by-step, using this repo's actual paths and conventions — not a generic
template. This is exactly what building `modernize-grid-batch-editing` (the checklist in
`example-walkthrough/EXAMPLE_WALKTHROUGH.md` Part 14, not yet built) looks like; swap the
capability name/legacy page for whatever you pick next.

```bash
# 0. You need the legacy source present to read the code-behind you're porting
#    (see README.md "Getting the Legacy Source" if legacy/ isn't cloned yet)
cd aspnet-ej1-demos-modernization

# 1. Read the legacy page you're porting FIRST — don't guess the data/behavior
cat legacy/Grid/BatchEditing.aspx.cs
cat legacy/Grid/BatchEditing.aspx

# 2. Create the change, from inside modernization/
cd modernization
openspec new change modernize-grid-batch-editing \
  --description "Rebuild Grid/BatchEditing.aspx (inline add/edit/delete, batch-saved) as ASP.NET Core Web API + React/TypeScript" \
  --goal "Fourth capability in this workspace; first one involving writes, not just reads"

# 3. Author all 4 artifacts, in order — read what each command prints (write path +
#    section rules + template) before writing the file
openspec instructions proposal --change modernize-grid-batch-editing
openspec instructions design   --change modernize-grid-batch-editing
openspec instructions specs    --change modernize-grid-batch-editing
openspec instructions tasks    --change modernize-grid-batch-editing

# 4. Confirm before implementing
openspec status   --change modernize-grid-batch-editing
openspec validate modernize-grid-batch-editing --strict

# 5. Implement STRICTLY per your tasks.md, reusing this project's existing pieces —
#    don't scaffold new ones:
#      - Backend goes in the EXISTING modernization/OrdersApi/ project:
#          OrdersApi/Data/BatchEditingOrdersRepository.cs  (port BindDataSource() exactly)
#          OrdersApi/Controllers/BatchEditingController.cs (this capability needs
#            GET + POST/PUT/DELETE — check the legacy save handler's actual semantics
#            before assuming REST-per-row vs. one batch payload)
#      - Frontend goes in the EXISTING modernization/orders-grid-web/:
#          src/api/batchEditingClient.ts
#          src/components/BatchEditingGrid.tsx
#          wire it into src/App.tsx alongside the existing grids, clearly labeled

# 6. Mock data for local browser verification (no .NET SDK needed) — reuse the
#    EXISTING mock server, don't start a second one. json-server supports multiple
#    top-level resource keys from one instance and already handles GET/POST/PUT/
#    DELETE/PATCH out of the box against them:
cd orders-grid-web
#    add a new top-level key to the EXISTING mock/db.json, e.g. "batch-editing-orders"
npx json-server mock/db.json --port 3001    # same one instance, now 3 resources
npm run build                                # must actually pass
npm run dev                                  # http://localhost:5173

# 7. Real browser verification — for THIS capability specifically, a read-only
#    click-and-look pass is NOT sufficient evidence (see Part 9): add a row, edit a
#    cell, delete a row, save, reload, confirm the change persisted in the mock's
#    store. Check the browser console for errors throughout.

# 8. Update tasks.md checkboxes honestly (only what you actually verified running),
#    re-validate, and leave real-.NET-SDK-backend verification unchecked + the
#    change unarchived until you actually have dotnet available:
openspec validate modernize-grid-batch-editing --strict
# openspec archive modernize-grid-batch-editing   <- only once tasks.md is truly 4/4-ish complete
```

---

## Part 9 — Real Gotchas (Found the Hard Way)

- **A project's own docs can disagree with its own `--help` output.** OpenSpec's
  official docs call the second profile "expanded"; `openspec init --help` calls it
  "custom"; neither name works as a non-interactive `openspec config profile <name>`
  shortcut (both error, only `core` is listed as available) — see Part 4 for the full,
  precise finding. Don't assume a feature works as documented until you've run it
  yourself against the version you actually have installed.
- **Long paths on Windows.** Cloning a repo with deeply-nested folders can fail with
  `Filename too long` partway through. Fix: `git -c core.longpaths=true clone ...` **and**
  a short destination path — `core.longpaths` alone wasn't sufficient on a deeply nested
  temp path in this project's own experience.
- **Mock-tooling versions drift too.** `json-server`'s 1.0.0-beta series dropped the
  classic `--routes` custom-path-remapping flag from v0.x. If a design assumes a flag
  exists, verify it against the actually-installed version (`npx <tool> --help`) before
  building on it — this project had to adapt mid-implementation when it didn't.
- **Background processes outlive your session.** A `json-server`/dev-server started in
  one working session can still be holding a port in the next one, causing confusing
  `EADDRINUSE` errors or, worse, silently serving *stale* data on a port you think is
  running fresh. Find the real PID (`netstat -ano | grep :<port>` on Windows,
  `Get-CimInstance Win32_Process` to confirm what it actually is before killing it) rather
  than guessing.
- **Don't let "authored" quietly become "verified" in your own head.** The most repeated
  discipline throughout this project: a file existing is not the same as its behavior
  being checked. Every `tasks.md` in this repo's `modernization/openspec/changes/`
  distinguishes the two explicitly, task by task.

---

## Part 10 — Multiple People, One Project

OpenSpec's file-per-change layout (`openspec/changes/<name>/`) is what makes this
tractable — two people on different capabilities never touch the same files.

- **One branch per change**, named after it (`git checkout -b modernize-<capability>`).
  Commit the 4 artifacts *before* implementation, as their own commit — lets a reviewer
  approve the plan before any code lands, which is the actual value SDD adds over a
  normal PR.
- **Check `openspec list` before starting** — don't start a second change for a
  capability someone already has in flight.
- **Capability names must be unique across in-flight changes** — they become
  `openspec/specs/<capability>/spec.md` paths at archive time; a naming collision is a
  merge conflict waiting to happen. Use specific names, not generic ones.
- **Archive from `main` after a PR merges, not from a feature branch** — so
  `openspec/specs/` only ever grows on the branch everyone else bases new work from.
- **Review checklist for a teammate's change**: does the capability name in `proposal.md`
  match an existing spec (modification) or a genuinely new one? Does every requirement in
  `specs/*.md` have at least one `#### Scenario` (exactly 4 hashtags —
  `openspec validate --strict` catches this, make it a required check)? Are `tasks.md`
  checkboxes only checked for what's actually verified, not just written?

---

## Part 11 — FAQ

**Do I need an AI assistant to use OpenSpec, or can I author artifacts by hand?**
Either. `openspec instructions <artifact> --change <name>` prints the exact template and
rules regardless of who's writing the file — a human can follow it exactly the same way
an AI does.

**What if my target repo has no existing specs yet?**
Normal — `openspec/specs/` starts empty and only grows via `openspec archive`. Every
project starts here.

**Can I use OpenSpec without any legacy-migration angle at all — just for new features?**
Yes — Part 5's loop is the whole story for greenfield work too. Part 6 is specifically
about the *legacy analysis + capability-ranking* layer on top, which only matters when
there's an existing codebase to migrate.

**How do I know which profile/skills I have?**
`openspec config list` shows your current profile and its workflow set (the `core`
default gives `propose, explore, apply, sync, archive` — confirmed directly, matching
the 5 real Claude Code skill folders `openspec init --tools claude` creates:
`openspec-propose`, `openspec-explore`, `openspec-apply-change`, `openspec-sync-specs`,
`openspec-archive-change`). To try the docs' "expanded" profile, run
`openspec config profile` with no arguments in a real interactive terminal and pick from
the prompt, then `openspec update` in your project — the shortcut form
(`openspec config profile expanded`) doesn't work non-interactively, see Part 4.

**I ran `openspec archive` too early / on the wrong change — what now?**
Same care as any git history mistake — the archived change moves to
`openspec/changes/archive/`, and its spec deltas are already merged into
`openspec/specs/`. Manually revert the spec-file changes if they were premature; there's
no built-in "un-archive" command as of v1.5.0.

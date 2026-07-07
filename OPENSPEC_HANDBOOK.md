# OpenSpec Handbook

Technical reference: execution model, Claude Code integration, complete command
surface (OpenSpec CLI + the aspx-analyzer skill), and the project lifecycle. Precise and
non-narrative by design — for the worked example and full command transcript, see
`example-walkthrough/EXAMPLE_WALKTHROUGH.md`.

---

## 1. Execution Model

Three independent layers. None of them runs continuously; each executes only when
invoked.

| Layer | What it is | What it executes | Runs when |
|---|---|---|---|
| **OpenSpec CLI** | A file-based planning/state tool | Reads and writes files under `openspec/` (`config.yaml`, `changes/*/*.md`). Does not compile, run, or test application code. | Once per command invocation (`openspec new change`, `openspec instructions`, `openspec archive`, etc.) — never in the background. |
| **aspx-analyzer skill** | A static-analysis tool (`skill/scripts/*.py`) | Reads legacy source files, writes a JSON index + markdown reports. Does not modify the legacy application. | On demand — first analysis, and any `--rebuild` after legacy source changes. Not re-run automatically. |
| **Claude Code** | An interactive AI agent with Agent Skill discovery | Neither of the above directly — it invokes the OpenSpec CLI and the skill's Python scripts as subprocesses/tool calls, on your instruction. | Only while you are actively conversing with it. |

**Key clarification:** OpenSpec does not "run the project." It produces and tracks
planning documents. The application itself — the ASP.NET Core API, the React frontend —
is built, run, and tested with its own normal toolchain (`dotnet`, `npm`), independently
of OpenSpec. OpenSpec's role ends at producing `tasks.md`; a human or Claude Code then
executes those tasks using ordinary development tools.

### Sequence, this project

| # | Action | Executed by | Command / trigger |
|---|---|---|---|
| 1 | Analyze legacy source | aspx-analyzer skill | `python skill/scripts/aspx_analysis_skill.py legacy --view project` |
| 2 | Initialize planning workspace | OpenSpec CLI | `openspec init --tools claude` (once) |
| 3 | Project analysis into planning workspace | aspx-analyzer skill | `python skill/scripts/aspx_openspec_emitter.py <index.json> --openspec-dir openspec` |
| 4 | Create + author a change's 4 artifacts | OpenSpec CLI | `openspec new change`, `openspec instructions <artifact>` (repeated per artifact) |
| 5 | Implement per `tasks.md` | Developer / Claude Code, using `dotnet`/`npm` directly | Not an OpenSpec or skill command — ordinary application tooling |
| 6 | Validate + archive | OpenSpec CLI | `openspec validate --strict`, `openspec archive` |

Steps 1 and 3 run once per legacy-analysis cycle. Steps 4 and 6 run once per capability.
Step 5 is outside OpenSpec entirely.

---

## 2. Claude Code Integration

### Discovery

Claude Code auto-discovers Agent Skills at `.claude/skills/<name>/SKILL.md`. No
registration step. Two independent skill sets exist in this project:

| Skill folder | Provided by | Purpose |
|---|---|---|
| `skill/` (copy; activate via `.claude/skills/aspx-analyzer/`) | This project | Legacy analysis, OpenSpec config/proposal emission, modernization roadmap |
| `modernization/.claude/skills/openspec-propose` | OpenSpec CLI (`openspec init --tools claude`) | Create a change + all 4 artifacts in one step |
| `modernization/.claude/skills/openspec-explore` | OpenSpec CLI | Pre-commitment exploration of an idea |
| `modernization/.claude/skills/openspec-apply-change` | OpenSpec CLI | Implement a change's `tasks.md` |
| `modernization/.claude/skills/openspec-sync-specs` | OpenSpec CLI | Merge delta specs into `openspec/specs/` ahead of archive |
| `modernization/.claude/skills/openspec-archive-change` | OpenSpec CLI | Archive a completed change |

### Invocation paths

Both of the following are equivalent — Claude Code is a convenience layer, not a
requirement:

1. **Via Claude Code**: state intent in chat ("analyze this repo", "propose a change for
   X"). Claude Code matches the phrase against installed skills' `description` fields,
   invokes the matched skill, which runs the same underlying Python script or `openspec`
   CLI command a human would type.
2. **Direct CLI**: run `python skill/scripts/aspx_analysis_skill.py ...` or
   `openspec ...` in a terminal yourself. Identical result — Claude Code adds no
   additional processing to the underlying command.

### Activating `aspx-analyzer` in a project

```bash
mkdir -p .claude/skills
cp -r skill .claude/skills/aspx-analyzer
```

Required once per target project. Not required to run the Python scripts directly
(`python skill/scripts/aspx_analysis_skill.py ...` works regardless of `.claude/skills/`
placement).

---

## 3. OpenSpec CLI — Complete Command Reference

Verified against the installed CLI (`openspec --version` → `1.5.0`).

### Core workflow

| Command | Function |
|---|---|
| `openspec init [path] [--tools <list>] [--force]` | Scaffold `openspec/config.yaml` + AI-tool skills in a project |
| `openspec new change <name> [--description] [--goal] [--schema]` | Create a change directory |
| `openspec instructions <artifact> --change <name>` | Print write-path + authoring template for `proposal`/`design`/`specs`/`tasks` |
| `openspec status --change <name>` | Show artifact completion state |
| `openspec validate <name> [--strict] [--all]` | Validate a change or spec |
| `openspec archive <name> [-y] [--skip-specs] [--no-validate]` | Merge spec deltas into `openspec/specs/`, close the change |
| `openspec list [--specs] [--sort]` | List changes (default) or durable specs |
| `openspec show <name> [--type] [--requirements]` | Print a change's or spec's content |

### Supporting

| Command | Function |
|---|---|
| `openspec update [path] [--force]` | Refresh generated AI-tool skill files after a CLI upgrade |
| `openspec view` | Interactive dashboard |
| `openspec doctor [--json]` | Health-check the resolved OpenSpec root |
| `openspec context [--json]` | Print the context injected into artifact-generation prompts |
| `openspec templates [--schema]` | Show resolved template paths for a schema |
| `openspec schemas [--json]` | List available workflow schemas (`spec-driven` by default) |
| `openspec schema init/fork/validate/which` | Manage custom schemas *(experimental)* |
| `openspec config path/list/get/set/unset/reset/edit` | Global CLI configuration |
| `openspec config profile [preset]` | Show/set workflow profile — see note below |
| `openspec feedback <message>` | Submit feedback upstream |
| `openspec completion` | Shell completion setup |

### Advanced (multi-repo)

| Command | Function |
|---|---|
| `openspec store setup/register/unregister/remove/list/doctor` | Manage standalone OpenSpec repos across projects |
| `openspec workset create/list/open/remove` | Personal, local-only cross-store views |

**Profile note:** the CLI ships a `core` preset (`propose`, `explore`, `apply`, `sync`,
`archive`). A second profile is documented (named `expanded` in `docs/commands.md`,
named `custom` in `openspec init --help` — the two disagree with each other) but is not
selectable via the non-interactive `openspec config profile <name>` shortcut (confirmed:
both names error with `Available presets: core`); it requires the interactive picker
(`openspec config profile` with no argument) followed by `openspec update`.

---

## 4. aspx-analyzer Skill — Complete Command Reference

| Script | Command | Output |
|---|---|---|
| `aspx_analysis_skill.py` | `python skill/scripts/aspx_analysis_skill.py <target> --view <project\|pages\|functional\|component\|navigation> [--page <name>] [--area <name>] [--workers N] [--rebuild] [--output DIR] [--save-report]` | JSON index (`<repo>_aspx_index.json`) + one markdown report |
| `aspx_business_analyzer.py` | `python skill/scripts/aspx_business_analyzer.py <target> [--workers N] [--detail-area A] [--full-detail]` | One consolidated business-logic markdown, for 10,000+ page repos |
| `aspx_openspec_emitter.py` | `python skill/scripts/aspx_openspec_emitter.py <index.json> --openspec-dir <path>` | Updates `openspec/config.yaml`; creates missing `openspec/changes/<area>/proposal.md` stubs |
| `aspx_roadmap_emitter.py` | `python skill/scripts/aspx_roadmap_emitter.py <index.json> [--stack dotnet-webapi-react\|dotnet-razor-pages] [--top N]` | `MODERNIZATION_ROADMAP.md` — target-stack setup + capability build order |

`<target>` accepts a GitHub URL, a local path, or `.`. All four scripts are stdlib-only
Python — no dependency installation required to run them.

---

## 5. Project Lifecycle

### One-time setup

```bash
openspec init --tools claude                                          # (2) in the sequence table
python skill/scripts/aspx_analysis_skill.py legacy --view project --save-report   # (1)
python skill/scripts/aspx_openspec_emitter.py <index.json> --openspec-dir openspec  # (3)
python skill/scripts/aspx_roadmap_emitter.py <index.json>              # optional — build-order backlog
```

### Per-capability loop (repeat for every feature)

```bash
openspec new change <name> --description "..." --goal "..."
openspec instructions proposal --change <name>   # author proposal.md
openspec instructions design   --change <name>   # author design.md
openspec instructions specs    --change <name>   # author specs/<capability>/spec.md
openspec instructions tasks    --change <name>    # author tasks.md
openspec status   --change <name>                 # confirm 4/4
openspec validate <name> --strict                  # confirm valid
# implement strictly per tasks.md, using dotnet/npm — not an OpenSpec step
openspec validate <name> --strict                  # re-validate post-implementation
openspec archive <name>                             # only once every task is verified, not just written
```

### Full migration

Repeat the per-capability loop for every entry in `MODERNIZATION_ROADMAP.md`, in ranked
order. Completion = every capability archived, `openspec/specs/` fully populated.

---

## 6. Governance Controls

| Control | Enforced by |
|---|---|
| No implementation before all 4 artifacts exist | `openspec status` gates each artifact on the prior one |
| No archiving unverified work | Process discipline — `tasks.md` checkboxes marked only against observed behavior, checked before every `openspec archive` |
| Legacy traceability | Proposal must name the exact legacy file(s)/page(s) replaced |
| Access-control continuity | Proposal must preserve existing auth requirements unless explicitly changing them |
| Structural correctness | `openspec validate --strict` — required scenario format, artifact completeness |
| Multi-contributor isolation | One branch per change; capability names unique across in-flight changes; archive only from the trunk branch |

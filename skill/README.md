# aspx-analyzer — Claude Code Agent Skill

Reverse-engineers ASP.NET Web Forms applications (`.aspx`/`.ascx`/`.master`) into a
persistent JSON index, five human-readable views, an OpenSpec modernization handoff, and
a build-order roadmap. This copy produced everything under `../legacy/`,
`../modernization/`, and `../example-walkthrough/` in this project — see
`../example-walkthrough/EXAMPLE_WALKTHROUGH.md` for the full real run.

This is a plain folder copy, not a live Claude Code skill in this location — Claude Code
only auto-discovers skills under `.claude/skills/<name>/`. To activate it (here or in
another repo):

```bash
mkdir -p .claude/skills
cp -r skill .claude/skills/aspx-analyzer   # run from this project's root
```

## Scripts

| Script | Purpose |
|---|---|
| `scripts/aspx_analysis_skill.py` | 5-view analyzer (project/pages/functional/component/navigation), builds the JSON index |
| `scripts/aspx_business_analyzer.py` | Streaming/parallel mode for 10,000+ page repos, one consolidated business report |
| `scripts/aspx_openspec_emitter.py` | Projects the JSON index into an existing OpenSpec workspace (`config.yaml` + per-capability proposal stubs) |
| `scripts/aspx_roadmap_emitter.py` | Target-stack setup + capability build-order roadmap, ranked simplest-first |
| `scripts/engine/` | Shared parser, indexer, reporter, method-extractor modules |

## Quick usage

```bash
python scripts/aspx_analysis_skill.py <target> --view project --save-report
python scripts/aspx_openspec_emitter.py <index.json> --openspec-dir <path>/openspec
python scripts/aspx_roadmap_emitter.py <index.json> --stack dotnet-webapi-react
```

`<target>` is a GitHub URL, a local path, or `.` for the current directory. Full flag
reference: `SKILL.md` in this folder, or run any script with `--help`.

No third-party dependencies — see `assets/requirements.txt`.

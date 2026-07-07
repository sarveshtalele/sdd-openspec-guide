#!/usr/bin/env python3
"""
ASPX Modernization Roadmap Emitter
===================================
Reads the JSON index already produced by aspx_analysis_skill.py (or
aspx_business_analyzer.py) and emits ONE markdown roadmap with two things a
team needs before starting a legacy-to-modern migration:

  1. Target-stack folder layout + real scaffold commands (a "how do I even
     set this up" answer), for a chosen modern stack.
  2. A build order — every functional area/capability discovered by the
     analyzer, ranked simplest-first by an explicit complexity score, so the
     team starts with the lowest-risk capability and builds confidence before
     tackling direct-SQL / high-control-count areas. Each capability also
     names one concrete "port this page first" starting point.

This does not require OpenSpec — it's a standalone planning artifact. If you
are using OpenSpec too, feed each roadmap entry into its own
`openspec new change` (see openspec_setup.md / EXAMPLE_WALKTHROUGH.md in this
skill's parent repo for the full worked pattern).

Usage:
    python aspx_roadmap_emitter.py <index.json> [--stack <name>] [--output DIR] [--top N]

Stacks available: dotnet-webapi-react (default). Run --list-stacks to see all.
"""

import sys
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any

_HELP = __doc__

# ---------------------------------------------------------------------------
# Stack templates — folder layout + real setup commands per target stack.
# Add a new stack by adding an entry here; nothing else needs to change.
# ---------------------------------------------------------------------------

_STACKS: Dict[str, dict] = {
    'dotnet-webapi-react': {
        'label': 'ASP.NET Core Web API + React/TypeScript (Vite)',
        'layout': """modern/
├── <Capability>Api/            ASP.NET Core Web API for this capability
│   ├── <Capability>Api.csproj
│   ├── Program.cs              minimal hosting + CORS policy for the frontend dev server
│   ├── Models/                 DTOs matching the legacy code-behind's data classes
│   ├── Data/                   repository/service porting the legacy data-access logic
│   └── Controllers/            one controller per legacy page being replaced
└── <capability>-web/           React + TypeScript frontend (Vite)
    ├── src/
    │   ├── api/                 typed fetch client(s) against the API above
    │   └── components/          one component per legacy page/control being replaced
    └── package.json""",
        'setup_commands': [
            '# Backend — one Web API project per capability keeps each migration slice',
            '# independently buildable/deployable; consolidate later if the target',
            '# architecture calls for a single shared API.',
            'dotnet new webapi -n <Capability>Api -o modern/<Capability>Api',
            '',
            '# Frontend',
            'npm create vite@latest <capability>-web -- --template react-ts',
            'cd modern/<capability>-web && npm install',
            '',
            '# Verify the frontend at least (Node-only, always runnable):',
            'npm run build',
        ],
        'notes': [
            'This exact stack was used and verified in this skill\'s own worked example '
            '(EXAMPLE_WALKTHROUGH.md, parent repo) — a real legacy grid page ported to a real, '
            'built ASP.NET Core Web API + React/TS app.',
            'CORS: the Web API must explicitly allow the Vite dev server origin '
            '(default http://localhost:5173) — see Program.cs pattern in EXAMPLE_WALKTHROUGH.md.',
            'No .NET SDK available to verify the backend compiles in a given environment? '
            'Say so explicitly rather than claiming it builds — the same discipline this '
            'skill\'s own walkthrough followed.',
        ],
    },
    'dotnet-razor-pages': {
        'label': 'ASP.NET Core Razor Pages (same-runtime, lighter migration)',
        'layout': """modern/
└── <Capability>/                Razor Pages app (or area within a shared one)
    ├── Pages/
    │   └── <Page>.cshtml         + <Page>.cshtml.cs (PageModel) — replaces .aspx + code-behind
    ├── Models/
    └── Services/                 porting the legacy data-access logic""",
        'setup_commands': [
            'dotnet new webapp -n <Capability> -o modern/<Capability>',
            '# Then, per legacy page: create Pages/<Page>.cshtml + <Page>.cshtml.cs,',
            '# porting the legacy .aspx markup and code-behind\'s Page_Load logic 1:1.',
        ],
        'notes': [
            'Same .NET runtime as the legacy app — smaller jump than a fully decoupled '
            'API+SPA stack, at the cost of not separating UI framework from backend long-term.',
            'Good default when the team wants to stay in C#/Razor rather than adopt a JS '
            'frontend framework.',
        ],
    },
}

_DEFAULT_STACK = 'dotnet-webapi-react'


# ---------------------------------------------------------------------------
# Complexity scoring / build ordering
# ---------------------------------------------------------------------------

def _slug(name: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9]+', '-', name.strip().lower()).strip('-')
    return s or 'capability'


def _pascal(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9]+', ' ', name).title().replace(' ', '')


def _score_capability(pages: List[dict], page_index: Dict[str, dict]) -> Dict[str, Any]:
    """Lower score = simpler = build first. Direct SQL weighted heaviest since
    that's the dominant migration-effort driver (data-access rewrite, not just
    UI rewrite); AJAX and unknown-auth pages add smaller amounts of risk."""
    full_pages = [page_index.get(p['rel_path'], {}) for p in pages]
    n = len(pages)
    sql = sum(1 for p in full_pages if p.get('uses_sql_direct'))
    ajax = sum(1 for p in full_pages if p.get('uses_ajax'))
    unknown_auth = sum(1 for p in pages if p.get('auth') == 'unknown')
    score = n + sql * 3 + ajax * 1 + unknown_auth * 1
    return {'pages': n, 'sql': sql, 'ajax': ajax, 'unknown_auth': unknown_auth, 'score': score}


def _pick_starting_page(pages: List[dict], page_index: Dict[str, dict]) -> dict:
    """Cheapest single page to port first within a capability: no direct SQL,
    fewest form controls, preferring simpler pages over complex ones — mirrors
    how this skill's own worked example picked its first real migration target."""
    def _page_cost(p):
        full = page_index.get(p['rel_path'], {})
        sql_penalty = 100 if full.get('uses_sql_direct') else 0
        ctrl_count = len(full.get('form_controls', []))
        return (sql_penalty, ctrl_count)

    return min(pages, key=_page_cost)


def build_roadmap(index: dict, stack: str, top: int = 0) -> str:
    if stack not in _STACKS:
        raise ValueError(f"Unknown stack '{stack}'. Available: {', '.join(_STACKS)}")
    tpl = _STACKS[stack]
    page_index = {p['rel_path']: p for p in index.get('pages', [])}
    areas = index.get('functional_areas', {})

    ranked = []
    for area, pages in areas.items():
        stats = _score_capability(pages, page_index)
        start_page = _pick_starting_page(pages, page_index) if pages else None
        ranked.append({'area': area, 'pages': pages, 'stats': stats, 'start_page': start_page})
    ranked.sort(key=lambda r: r['stats']['score'])
    if top:
        ranked = ranked[:top]

    lines = [
        f"# Modernization Roadmap — {index.get('project', 'project')}",
        "",
        f"Generated from the aspx-analyzer index. Target stack: **{tpl['label']}**.",
        "Build order is simplest/lowest-risk capability first — direct-SQL pages weigh",
        "heaviest in the ranking since data-access rewrite is the dominant migration cost,",
        "not the UI port itself.",
        "",
        "---",
        "",
        "## 1. Target Stack Setup",
        "",
        "```",
        tpl['layout'],
        "```",
        "",
        "```bash",
    ]
    lines += tpl['setup_commands']
    lines += ["```", ""]
    if tpl.get('notes'):
        lines.append("**Notes:**")
        for note in tpl['notes']:
            lines.append(f"- {note}")
        lines.append("")

    lines += ["---", "", "## 2. Build Order — Capabilities, Simplest First", ""]
    lines += [
        "| # | Capability | Pages | Direct SQL | AJAX | Unknown Auth | Score | Suggested first page |",
        "|---|------------|-------|------------|------|---------------|-------|----------------------|",
    ]
    for i, r in enumerate(ranked, 1):
        s = r['stats']
        start = r['start_page']
        start_label = f"`{start['rel_path'].replace(chr(92), '/')}`" if start else "—"
        lines.append(
            f"| {i} | {r['area']} | {s['pages']} | {s['sql']} | {s['ajax']} | "
            f"{s['unknown_auth']} | {s['score']} | {start_label} |"
        )

    lines += ["", "### Per-capability detail", ""]
    for i, r in enumerate(ranked, 1):
        area, s = r['area'], r['stats']
        slug = _slug(area)
        pascal = _pascal(area)
        lines.append(f"#### {i}. {area}  (score: {s['score']})")
        lines.append("")
        if s['sql'] == 0 and s['ajax'] == 0:
            lines.append(f"No direct-SQL or AJAX pages — good candidate to prove the migration "
                         f"pattern on before tackling harder capabilities.")
        elif s['sql'] > 0:
            lines.append(f"**{s['sql']} page(s) use direct SQL** in code-behind — plan a "
                         f"parametrized-query/repository migration as part of this capability's "
                         f"design, not a like-for-like port.")
        if r['start_page']:
            start_rel = r['start_page']['rel_path'].replace(chr(92), '/')
            lines.append(f"- Start with: `{start_rel}` "
                         f"({r['start_page'].get('purpose', r['start_page']['name'])})")
        lines.append(f"- Suggested scaffold names: `{pascal}Api` / `{slug}-web`")
        lines.append("")

    lines += [
        "---",
        "",
        "## Using this with OpenSpec",
        "",
        "Feed each row into its own change, in the order above:",
        "```bash",
        "openspec new change modernize-<capability-slug> --description \"...\" --goal \"...\"",
        "openspec instructions proposal --change modernize-<capability-slug>",
        "# ... proposal -> design -> specs -> tasks, same loop as EXAMPLE_WALKTHROUGH.md",
        "```",
    ]

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(_HELP)
        sys.exit(0 if args else 1)
    if '--list-stacks' in args:
        for key, tpl in _STACKS.items():
            print(f"{key} — {tpl['label']}")
        sys.exit(0)

    index_path = args[0]
    stack = _DEFAULT_STACK
    output_dir = None
    top = 0

    i = 1
    while i < len(args):
        if args[i] == '--stack' and i + 1 < len(args):
            stack = args[i + 1]; i += 2
        elif args[i] == '--output' and i + 1 < len(args):
            output_dir = args[i + 1]; i += 2
        elif args[i] == '--top' and i + 1 < len(args):
            top = int(args[i + 1]); i += 2
        else:
            i += 1

    if not os.path.isfile(index_path):
        sys.exit(f"Error: index file not found — {index_path}")

    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)

    try:
        content = build_roadmap(index, stack, top)
    except ValueError as e:
        sys.exit(f"Error: {e}")

    out_dir = output_dir or os.path.dirname(os.path.abspath(index_path))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'MODERNIZATION_ROADMAP.md')
    Path(out_path).write_text(content, encoding='utf-8')

    print(f"[ok] Roadmap saved -> {out_path}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
ASPX -> OpenSpec Emitter
========================
Reads the JSON index already produced by aspx_analysis_skill.py (or the
compact index from aspx_business_analyzer.py — both share the same
project/stats/web_config/pages/functional_areas shape) and projects it into
an existing OpenSpec workspace:

  openspec/config.yaml               context + modernization rules
                                      (written inside a marker block —
                                      re-running only refreshes that block)
  openspec/changes/<area-slug>/
      proposal.md                    one stub per functional area/capability
                                      (Why / What Changes / Impact) — created
                                      only if it does not already exist

Does NOT run `openspec init` and does NOT create openspec/specs or
openspec/changes themselves — `openspec/` must already exist (created by the
separate OpenSpec CLI). This script only fills content into that scaffold.

No third-party dependencies (stdlib only), matching the rest of this skill.

Usage:
    python aspx_openspec_emitter.py <index.json> [--openspec-dir DIR] [--project-name NAME]
"""

import sys
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any

_HELP = __doc__

_MARKER_START = "# >>> aspx-analyzer:auto-generated (regenerate via aspx_openspec_emitter.py — do not hand-edit below) >>>"
_MARKER_END   = "# <<< aspx-analyzer:auto-generated <<<"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug(name: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9]+', '-', name.strip().lower()).strip('-')
    return s or 'general'


def _yaml_literal_block(key: str, text: str, indent: int = 2) -> str:
    pad = ' ' * indent
    lines = text.splitlines() or ['']
    body = '\n'.join(f'{pad}{ln}' if ln else '' for ln in lines)
    return f'{key}: |\n{body}\n'


def _yaml_quoted(s: str) -> str:
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


# ---------------------------------------------------------------------------
# Content builders
# ---------------------------------------------------------------------------

def _build_context(index: dict) -> str:
    s  = index.get('stats', {})
    wc = index.get('web_config', {})
    areas = index.get('functional_areas', {})

    lines = [
        f"Legacy stack: ASP.NET Web Forms (.NET Framework), code-behind pattern.",
        f"Project: {index.get('project', 'unknown')}",
        f"Inventory: {s.get('total_pages', 0)} .aspx page(s), "
        f"{s.get('total_controls', 0)} .ascx user control(s), "
        f"{s.get('total_masters', 0)} .master page(s).",
    ]
    if s.get('total_methods') is not None:
        lines.append(f"Code-behind methods parsed: {s.get('total_methods', 0)}"
                      + (f", stored procedures referenced: {s.get('total_stored_procs', 0)}."
                         if s.get('total_stored_procs') else "."))
    if wc.get('auth_mode'):
        lines.append(f"Authentication mode (web.config): {wc['auth_mode']}"
                      + (f", forms login URL: {wc['forms_auth_url']}" if wc.get('forms_auth_url') else ""))
    if wc.get('connection_strings'):
        lines.append(f"Connection strings declared: {', '.join(wc['connection_strings'])}")
    if wc.get('session_mode'):
        lines.append(f"Session mode: {wc['session_mode']}")
    if s.get('pages_with_sql_direct'):
        lines.append(f"Direct SQL usage (SqlConnection/SqlCommand in code-behind) found in "
                      f"{s['pages_with_sql_direct']} page(s) — treat as tight-coupling / injection-risk debt.")
    if areas:
        area_list = ', '.join(f"{a} ({len(v)})" for a, v in sorted(areas.items()))
        lines.append(f"Business capabilities discovered (page count): {area_list}")
    lines.append("Modernization target: to be defined per capability in openspec/changes/<area>/proposal.md.")
    return '\n'.join(lines)


def _build_rules(index: dict) -> Dict[str, List[str]]:
    s = index.get('stats', {})
    auth_breakdown = s.get('auth_breakdown', {})
    roles = sorted(a.split(':', 1)[1] for a in auth_breakdown if a.startswith('role:'))

    proposal_rules = [
        "Every proposal must name which legacy .aspx page(s) it replaces (use rel_path from the aspx-analyzer index).",
        "Preserve existing authorization boundaries unless the proposal explicitly calls out an access-model change.",
    ]
    if roles:
        proposal_rules.append(
            f"Roles discovered in the legacy app ({', '.join(roles)}) must map to an equivalent role/claim "
            f"in the modernized design — do not silently drop a role."
        )
    if s.get('pages_with_sql_direct'):
        proposal_rules.append(
            f"{s['pages_with_sql_direct']} legacy page(s) use direct SQL (SqlConnection/SqlCommand) in "
            f"code-behind — proposals touching these must include a data-access migration plan "
            f"(parametrized queries / repository layer), not a like-for-like lift."
        )

    specs_rules = [
        "Reference actual legacy page names and routes from the proposal's page list — do not invent screen names.",
        "Call out any page whose auth was inferred as 'unknown' by the analyzer as a spec risk requiring manual auth verification.",
    ]

    return {'proposal': proposal_rules, 'specs': specs_rules}


def _build_proposal_stub(area: str, pages: List[dict], page_index: Dict[str, dict]) -> str:
    lines = [f"# {area} — Modernization Proposal", "", "## Why", ""]
    lines.append(f"`{area}` is a legacy capability comprising {len(pages)} ASP.NET Web Forms page(s):")
    lines.append("")
    sql_pages = []
    for p in pages:
        full = page_index.get(p['rel_path'], {})
        auth = p.get('auth', 'unknown')
        lines.append(f"- `{p['rel_path']}` — {p.get('purpose') or p['name']} (auth: {auth})")
        if full.get('uses_sql_direct'):
            sql_pages.append(p['rel_path'])
    lines.append("")
    if sql_pages:
        lines.append(f"**Data-access risk:** {len(sql_pages)} page(s) in this capability use direct SQL "
                      f"in code-behind: {', '.join(sql_pages)}. Plan a parametrized-query or repository-layer "
                      f"migration for these before cutover.")
        lines.append("")
    lines += [
        "## What Changes",
        "",
        "<!-- TODO: describe the target modern implementation for this capability -->",
        "",
        "## Impact",
        "",
        f"- Affected legacy pages: {len(pages)}",
        f"- Pages with unresolved/unknown auth: {sum(1 for p in pages if p.get('auth') == 'unknown')}",
        f"- Pages with direct SQL usage: {len(sql_pages)}",
        "<!-- TODO: list affected APIs/services/dependencies in the modernized system -->",
        "",
    ]
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# File writers
# ---------------------------------------------------------------------------

def _write_config_yaml(openspec_dir: str, context: str, rules: Dict[str, List[str]]) -> str:
    config_path = os.path.join(openspec_dir, 'config.yaml')
    existing = Path(config_path).read_text(encoding='utf-8') if os.path.exists(config_path) else ''

    block_lines = [_MARKER_START, _yaml_literal_block('context', context).rstrip('\n'), 'rules:']
    for artifact, items in rules.items():
        block_lines.append(f'  {artifact}:')
        for item in items:
            block_lines.append(f'    - {_yaml_quoted(item)}')
    block_lines.append(_MARKER_END)
    block = '\n'.join(block_lines) + '\n'

    start_i = existing.find(_MARKER_START)
    end_i   = existing.find(_MARKER_END)

    if start_i != -1 and end_i != -1:
        prefix = existing[:start_i]
        suffix = existing[end_i + len(_MARKER_END):].lstrip('\n')
        new_content = prefix + block + (('\n' + suffix) if suffix else '')
        action = 'updated'
    elif existing.strip():
        # Warn about conflicting top-level keys we're not allowed to touch.
        for key in ('context:', 'rules:'):
            if re.search(rf'^{re.escape(key)}', existing, re.MULTILINE):
                print(f"  [!] Existing config.yaml already has a top-level '{key}' outside the "
                      f"auto-generated block — leaving it as-is, appending our block separately. "
                      f"Merge manually if this is unintended.")
        new_content = existing.rstrip('\n') + '\n\n' + block
        action = 'appended to'
    else:
        new_content = 'schema: spec-driven\n\n' + block
        action = 'created'

    os.makedirs(openspec_dir, exist_ok=True)
    Path(config_path).write_text(new_content, encoding='utf-8')
    return f"{action} {config_path}"


def _write_proposal_stubs(openspec_dir: str, index: dict) -> List[str]:
    changes_dir = os.path.join(openspec_dir, 'changes')
    page_index = {p['rel_path']: p for p in index.get('pages', [])}
    results = []

    for area, pages in index.get('functional_areas', {}).items():
        area_dir = os.path.join(changes_dir, _slug(area))
        proposal_path = os.path.join(area_dir, 'proposal.md')
        if os.path.exists(proposal_path):
            results.append(f"skipped (exists): {proposal_path}")
            continue
        os.makedirs(area_dir, exist_ok=True)
        content = _build_proposal_stub(area, pages, page_index)
        Path(proposal_path).write_text(content, encoding='utf-8')
        results.append(f"created: {proposal_path}")

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(index_path: str, openspec_dir: str, project_name: str = None) -> None:
    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)
    if project_name:
        index['project'] = project_name

    if not os.path.isdir(openspec_dir):
        sys.exit(
            f"Error: '{openspec_dir}' does not exist. Run `openspec init --tools claude` "
            f"in the target repo first — this emitter only fills content into an existing "
            f"openspec/ scaffold, it does not create one."
        )

    print(f"\n{'=' * 62}")
    print("  ASPX -> OpenSpec Emitter")
    print(f"  Index        : {index_path}")
    print(f"  OpenSpec dir : {openspec_dir}")
    print(f"{'=' * 62}\n")

    context = _build_context(index)
    rules   = _build_rules(index)

    cfg_result = _write_config_yaml(openspec_dir, context, rules)
    print(f"[1/2] config.yaml {cfg_result}")

    stub_results = _write_proposal_stubs(openspec_dir, index)
    print(f"[2/2] proposal stubs:")
    for r in stub_results:
        print(f"      {r}")

    created = sum(1 for r in stub_results if r.startswith('created'))
    print(f"\nDone. {created} new proposal stub(s), "
          f"{len(stub_results) - created} already existed and were left untouched.")


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(_HELP)
        sys.exit(0 if args else 1)

    index_path = args[0]
    openspec_dir = os.path.join(os.getcwd(), 'openspec')
    project_name = None

    i = 1
    while i < len(args):
        if args[i] == '--openspec-dir' and i + 1 < len(args):
            openspec_dir = args[i + 1]; i += 2
        elif args[i] == '--project-name' and i + 1 < len(args):
            project_name = args[i + 1]; i += 2
        else:
            i += 1

    if not os.path.isfile(index_path):
        sys.exit(f"Error: index file not found — {index_path}")

    run(index_path, openspec_dir, project_name)


if __name__ == '__main__':
    main()

"""
ASPX Report Generator
=====================
Generates human-readable Markdown reports from the ASPX index JSON.

View types:
  project      — architecture overview: stats, master pages, auth, functional areas, top components
  pages        — page-by-page listing grouped by folder
  functional   — pages grouped and described by business function
  component    — master pages + user controls catalog
  page:<name>  — deep-dive single page (controls, handlers, redirects, imports)
  area:<name>  — all pages in one functional area with full detail
"""

from pathlib import Path
from typing import Dict, List, Any, Optional


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def generate_project_overview(index: dict) -> str:
    stats   = index['stats']
    project = index['project']
    wc      = index.get('web_config', {})
    areas   = index.get('functional_areas', {})
    masters = index.get('master_pages', [])
    controls= index.get('user_controls', [])

    lines = [
        f"# {project} — ASP.NET Web Forms Application Analysis",
        f"",
        f"> Generated: {index.get('generated_at', 'N/A')}",
        f"",
        f"---",
        f"",
        f"## Executive Summary",
        f"",
        f"This is an **ASP.NET Web Forms** application with **{stats['total_pages']} pages**, "
        f"**{stats['total_controls']} user controls**, and **{stats['total_masters']} master pages** "
        f"across **{stats['total_functional_areas']} functional areas**.",
        f"",
    ]

    # Auth summary
    auth_mode = wc.get('auth_mode', '')
    forms_url = wc.get('forms_auth_url', '')
    if auth_mode:
        lines.append(f"**Authentication:** {auth_mode}" +
                     (f" (login URL: `{forms_url}`)" if forms_url else ""))
    if wc.get('connection_strings'):
        lines.append(f"**Databases:** {', '.join(wc['connection_strings'])}")
    if wc.get('smtp_host'):
        lines.append(f"**Email (SMTP):** {wc['smtp_host']}")
    if wc.get('session_mode'):
        lines.append(f"**Session:** {wc['session_mode']}")

    lines += ['', '---', '', '## Codebase Metrics', '']
    lines += [
        '| Metric | Count |',
        '|--------|-------|',
        f'| ASPX Pages | {stats["total_pages"]} |',
        f'| User Controls (.ascx) | {stats["total_controls"]} |',
        f'| Master Pages | {stats["total_masters"]} |',
        f'| Functional Areas | {stats["total_functional_areas"]} |',
        f'| Pages with Code-Behind | {stats["pages_with_codebehind"]} |',
        f'| Pages using Master Page | {stats["pages_with_master"]} |',
        f'| Pages with AJAX (UpdatePanel) | {stats["pages_with_ajax"]} |',
        f'| Pages with Direct SQL | {stats["pages_with_sql_direct"]} |',
        f'| Pages with Validators | {stats.get("pages_with_validators", 0)} |',
        f'| Named Routes (RouteConfig) | {stats.get("total_named_routes", 0)} |',
    ]

    # Auth breakdown
    auth_bd = stats.get('auth_breakdown', {})
    if auth_bd:
        lines += ['', '---', '', '## Access Control Breakdown', '']
        lines += ['| Requirement | Pages |', '|-------------|-------|']
        for k, v in sorted(auth_bd.items(), key=lambda x: -x[1]):
            lines.append(f'| `{k}` | {v} |')

    # Location rules from web.config
    locs = wc.get('location_rules', [])
    if locs:
        lines += ['', '### Web.config Location Rules', '']
        lines += ['| Path | Allow | Deny |', '|------|-------|------|']
        for loc in locs[:15]:
            lines.append(f'| `{loc["path"]}` | {", ".join(loc["allow"]) or "—"} | '
                         f'{", ".join(loc["deny"]) or "—"} |')

    # Master pages
    if masters:
        lines += ['', '---', '', '## Master Pages', '']
        for m in sorted(masters, key=lambda x: -len(x['used_by_pages'])):
            phs  = ', '.join(f'`{p}`' for p in m.get('content_placeholders', []))
            navs = ', '.join(set(m.get('navigation_menus', [])))
            lines.append(f"### `{m['rel_path']}`")
            lines.append(f"- **Purpose:** {m['purpose']}")
            lines.append(f"- **Used by:** {len(m['used_by_pages'])} pages")
            if phs:
                lines.append(f"- **Content Placeholders:** {phs}")
            if navs:
                lines.append(f"- **Navigation Controls:** {navs}")
            if m.get('has_login_controls'):
                lines.append(f"- **Login Controls:** Yes")
            if m.get('uses_ajax'):
                lines.append(f"- **ScriptManager (AJAX):** Yes")
            lines.append('')

    # Functional areas overview
    if areas:
        lines += ['---', '', '## Functional Areas Overview', '']
        for area, area_pages in areas.items():
            cnt = len(area_pages)
            lines.append(f"### {area} ({cnt} {'page' if cnt == 1 else 'pages'})")
            for ap in sorted(area_pages, key=lambda p: p['name'])[:6]:
                lines.append(f"- **{ap['name']}** — {ap['purpose']}  *(auth: `{ap['auth']}`)*")
            if cnt > 6:
                lines.append(f"- _{cnt - 6} more pages…_")
            lines.append('')

    # Top user controls
    if controls:
        top = sorted(controls, key=lambda c: -len(c.get('used_by_pages', [])))[:12]
        lines += ['---', '', '## Most-Used User Controls', '']
        lines += ['| Control | Purpose | Used By |', '|---------|---------|---------|']
        for c in top:
            lines.append(f'| `{c["filename"]}` | {c["purpose"]} | {len(c["used_by_pages"])} pages |')

    return '\n'.join(lines)


def generate_pages_report(index: dict) -> str:
    """Page-by-page listing, grouped by folder."""
    pages   = index.get('pages', [])
    project = index['project']

    lines = [
        f"# {project} — Page-by-Page Analysis",
        f"",
        f"**{len(pages)} pages** total.",
        f"",
        f"---",
        f"",
    ]

    # Group by folder
    folders: Dict[str, List[dict]] = {}
    for page in pages:
        folder = page.get('folder', '') or 'Root'
        if folder in ('.', ''):
            folder = 'Root'
        folders.setdefault(folder, []).append(page)

    for folder in sorted(folders.keys()):
        folder_pages = sorted(folders[folder], key=lambda p: p['name'])
        lines.append(f"## `{folder}/`  ({len(folder_pages)} pages)")
        lines.append('')

        for page in folder_pages:
            lines += _page_card(page, full=False)
            lines.append('')

        lines += ['---', '']

    return '\n'.join(lines)


def generate_page_detail(index: dict, page_name: str) -> str:
    """Deep-dive report for a single named page."""
    pages  = index.get('pages', [])
    target = _find_page(pages, page_name)

    if not target:
        avail = '\n'.join(f'- {p["name"]} (`{p["rel_path"]}`)'
                          for p in sorted(pages, key=lambda p: p['name'])[:30])
        return (f"# Page not found: `{page_name}`\n\n"
                f"Available pages (first 30):\n{avail}")

    lines = [
        f"# Page Deep-Dive: `{target['name']}.aspx`",
        f"",
        f"**File:** `{target['rel_path']}`",
        f"**Functional Area:** {target.get('functional_area', 'General')}",
        f"**Purpose:** {target.get('purpose', '—')}",
        f"**Auth Requirement:** `{target.get('auth', 'unknown')}`",
        f"",
        f"---",
        f"",
    ]
    lines += _page_card(target, full=True)
    return '\n'.join(lines)


def generate_functional_report(index: dict) -> str:
    """Pages grouped and described by business function."""
    areas          = index.get('functional_areas', {})
    pages_by_path  = {p['rel_path']: p for p in index.get('pages', [])}
    project        = index['project']

    lines = [
        f"# {project} — Functional View",
        f"",
        f"**{len(areas)} functional areas** covering all {index['stats']['total_pages']} pages.",
        f"",
        f"---",
        f"",
    ]

    for area, area_pages in areas.items():
        lines.append(f"## {area}  ({len(area_pages)} pages)")
        lines.append('')
        lines.append(_area_workflow_summary(area, area_pages))
        lines.append('')

        for ap in sorted(area_pages, key=lambda p: p['name']):
            full = pages_by_path.get(ap['rel_path'])
            if not full:
                continue
            lines.append(f"### {full['name']}.aspx")
            lines.append(f"")
            lines.append(f"**Purpose:** {full.get('purpose', '—')}  |  **Auth:** `{full.get('auth', 'unknown')}`")

            # Controls summary
            ctrls = full.get('form_controls', [])
            if ctrls:
                types: Dict[str, int] = {}
                for c in ctrls:
                    types[c['type']] = types.get(c['type'], 0) + 1
                summary = ', '.join(f"{v}× {k}" for k, v in sorted(types.items(), key=lambda x: -x[1]))
                lines.append(f"**Controls:** {summary}")

            # Event handlers
            handlers = full.get('event_handlers', [])
            if handlers:
                lines.append(f"**Handlers:** {', '.join(handlers[:6])}" +
                             (f" _(+{len(handlers)-6})_" if len(handlers) > 6 else ''))

            # Nav out
            nav_out = full.get('navigation_out', [])
            if nav_out:
                targets = ', '.join(f"`{n['url']}`" for n in nav_out[:4])
                lines.append(f"**Redirects to:** {targets}")

            # Master page
            if full.get('master_page'):
                lines.append(f"**Master:** `{full['master_page']}`")

            flags = []
            if full.get('uses_ajax'):     flags.append('AJAX')
            if full.get('uses_sql_direct'): flags.append('Direct SQL')
            if full.get('has_login_controls'): flags.append('Login controls')
            if flags:
                lines.append(f"**Flags:** {', '.join(flags)}")

            lines.append('')

        lines += ['---', '']

    return '\n'.join(lines)


def generate_area_report(index: dict, area_name: str) -> str:
    """Full detail for every page in one functional area."""
    areas         = index.get('functional_areas', {})
    pages_by_path = {p['rel_path']: p for p in index.get('pages', [])}

    target_area = _find_area(areas, area_name)
    if not target_area:
        avail = '\n'.join(f'- {a} ({len(p)} pages)' for a, p in areas.items())
        return f"# Area not found: `{area_name}`\n\nAvailable areas:\n{avail}"

    area_pages = areas[target_area]
    lines = [
        f"# {target_area} — Full Area Analysis",
        f"",
        f"**{len(area_pages)} pages** in this area.",
        f"",
        _area_workflow_summary(target_area, area_pages),
        f"",
        f"---",
        f"",
    ]

    for ap in sorted(area_pages, key=lambda p: p['name']):
        full = pages_by_path.get(ap['rel_path'])
        if full:
            lines.append(f"## {full['name']}.aspx")
            lines.append('')
            lines += _page_card(full, full=True)
            lines += ['', '---', '']

    return '\n'.join(lines)


def generate_component_report(index: dict) -> str:
    """Master pages and user controls catalog."""
    controls = index.get('user_controls', [])
    masters  = index.get('master_pages', [])
    project  = index['project']

    lines = [
        f"# {project} — Component Catalog",
        f"",
        f"**{len(masters)} master pages** | **{len(controls)} user controls**",
        f"",
        f"---",
        f"",
        f"## Master Pages ({len(masters)})",
        f"",
    ]

    for m in sorted(masters, key=lambda x: -len(x['used_by_pages'])):
        lines.append(f"### `{m['rel_path']}`")
        lines.append(f"")
        lines.append(f"**Purpose:** {m['purpose']}")
        lines.append(f"**Used by:** {len(m['used_by_pages'])} pages")

        phs = m.get('content_placeholders', [])
        if phs:
            lines.append(f"**Content Placeholders:** {', '.join(f'`{p}`' for p in phs)}")

        navs = list(set(m.get('navigation_menus', [])))
        if navs:
            lines.append(f"**Navigation Controls:** {', '.join(navs)}")

        if m.get('has_login_controls'):
            lines.append(f"**Login Controls:** Yes (asp:Login / LoginView / LoginStatus)")
        if m.get('uses_ajax'):
            lines.append(f"**AJAX:** Yes (ScriptManager)")

        regs = m.get('controls_registered', [])
        if regs:
            lines.append(f"**Registered Controls:** {', '.join(r['src'] for r in regs[:6])}")

        if m['used_by_pages']:
            lines.append(f"")
            lines.append(f"**Pages using this master:**")
            for p in sorted(m['used_by_pages'])[:10]:
                lines.append(f"- `{p}`")
            if len(m['used_by_pages']) > 10:
                lines.append(f"- _{len(m['used_by_pages']) - 10} more…_")

        lines += ['', '---', '']

    lines += [f"## User Controls ({len(controls)})", '']

    ctrl_sorted = sorted(controls, key=lambda c: -len(c.get('used_by_pages', [])))
    for ctrl in ctrl_sorted:
        lines.append(f"### `{ctrl['rel_path']}`")
        lines.append(f"")
        lines.append(f"**Purpose:** {ctrl.get('purpose', '—')}")
        lines.append(f"**Used by:** {len(ctrl.get('used_by_pages', []))} pages")

        if ctrl.get('namespace') and ctrl.get('class_name'):
            lines.append(f"**Class:** `{ctrl['namespace']}.{ctrl['class_name']}`")

        props = ctrl.get('properties', [])
        if props:
            lines.append(f"**Public Properties:** {', '.join(props[:10])}")

        events = ctrl.get('event_handlers', [])
        if events:
            lines.append(f"**Event Handlers:** {', '.join(events[:8])}")

        fc = ctrl.get('form_controls', [])
        if fc:
            types = ', '.join(dict.fromkeys(c['type'] for c in fc[:10]))
            lines.append(f"**Contains Controls:** {types}")

        if ctrl.get('used_by_pages'):
            lines.append(f"")
            lines.append(f"**Pages using this control:**")
            for p in sorted(ctrl['used_by_pages'])[:8]:
                lines.append(f"- `{p}`")
            if len(ctrl['used_by_pages']) > 8:
                lines.append(f"- _{len(ctrl['used_by_pages']) - 8} more…_")

        lines += ['', '---', '']

    return '\n'.join(lines)


def generate_navigation_report(index: dict) -> str:
    """Page transition map: who links to whom."""
    nav     = index.get('navigation_map', {})
    project = index['project']
    pages   = index.get('pages', [])
    name_map = {p['rel_path'].replace('\\', '/'): p['name'] for p in pages}

    lines = [
        f"# {project} — Navigation Map",
        f"",
        f"Pages with outbound navigation links: **{len(nav)}**",
        f"",
        f"---",
        f"",
    ]

    for src, targets in sorted(nav.items()):
        src_name = name_map.get(src, Path(src).stem)
        lines.append(f"**{src_name}** (`{src}`) →")
        for t in targets:
            t_name = name_map.get(t.lstrip('/'), Path(t).stem)
            lines.append(f"  - `{t}` ({t_name})")
        lines.append('')

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _find_page(pages: List[dict], name: str) -> Optional[dict]:
    n = name.lower().replace('.aspx', '')
    for page in pages:
        if page['name'].lower() == n:
            return page
    # Partial match
    for page in pages:
        if n in page['name'].lower():
            return page
    # Filename match
    for page in pages:
        if page['filename'].lower() == name.lower() or page['filename'].lower() == n + '.aspx':
            return page
    return None


def _find_area(areas: Dict[str, list], name: str) -> Optional[str]:
    n = name.lower()
    for area in areas:
        if area.lower() == n:
            return area
    for area in areas:
        if n in area.lower() or area.lower() in n:
            return area
    return None


def _page_card(page: dict, full: bool = False) -> List[str]:
    """Format a single page as a list of markdown lines."""
    lines: List[str] = []

    if not full:
        lines.append(f"### {page['name']}.aspx")
        lines.append('')

    lines.append(f"**File:** `{page['rel_path']}`")
    lines.append(f"**Purpose:** {page.get('purpose', '—')}")
    lines.append(f"**Functional Area:** {page.get('functional_area', 'General')}")
    lines.append(f"**Auth:** `{page.get('auth', 'unknown')}`")

    if page.get('title'):
        lines.append(f"**Page Title:** {page['title']}")

    if page.get('master_page'):
        lines.append(f"**Master Page:** `{page['master_page']}`")

    if page.get('namespace') and page.get('class_name'):
        lines.append(f"**Code-Behind:** `{page['namespace']}.{page['class_name']}`"
                     + (f" <- `{page['codebehind_file']}`" if page.get('codebehind_file') else ''))

    # UI controls
    form_ctrls = page.get('form_controls', [])
    if form_ctrls:
        lines.append('')
        if full:
            lines.append(f"**UI Controls ({len(form_ctrls)}):**")
            for c in form_ctrls:
                label = c['type']
                if c.get('id'):
                    label += f" `#{c['id']}`"
                if c.get('text'):
                    label += f" — \"{c['text']}\""
                lines.append(f"- {label}")
        else:
            types: Dict[str, int] = {}
            for c in form_ctrls:
                types[c['type']] = types.get(c['type'], 0) + 1
            summary = ', '.join(f"{v}× {k}" for k, v in sorted(types.items(), key=lambda x: -x[1]))
            lines.append(f"**Controls ({len(form_ctrls)}):** {summary}")

    # Display controls (asp:Label, asp:Image, etc.)
    disp = page.get('display_controls', [])
    if disp and full:
        dtypes: Dict[str, int] = {}
        for c in disp:
            dtypes[c['type']] = dtypes.get(c['type'], 0) + 1
        dsummary = ', '.join(f"{v}× {k}" for k, v in sorted(dtypes.items(), key=lambda x: -x[1]))
        lines.append(f"**Display Controls ({len(disp)}):** {dsummary}")

    # Data sources
    ds = page.get('data_sources', [])
    if ds:
        lines.append('')
        ds_labels = [d['type'] + (f' `#{d["id"]}`' if d.get('id') else '') for d in ds]
        lines.append(f"**Data Sources:** {', '.join(ds_labels)}")

    # Flags
    flags: List[str] = []
    if page.get('uses_ajax'):
        flags.append('AJAX (UpdatePanel)')
    if page.get('uses_sql_direct'):
        flags.append('Direct SQL (SqlConnection)')
    if page.get('has_login_controls'):
        flags.append('Login controls')
    if page.get('page_load'):
        flags.append('Page_Load')
    if flags:
        lines.append(f"**Flags:** {', '.join(flags)}")

    # Registered controls
    reg = page.get('controls_registered', [])
    if reg:
        lines.append('')
        lines.append(f"**User Controls Used ({len(reg)}):**")
        for r in reg[:10]:
            lines.append(f"- `{r['src']}` (prefix: `{r.get('prefix', 'uc')}`)")
        if len(reg) > 10:
            lines.append(f"- _{len(reg) - 10} more…_")

    # Content areas (when using master)
    areas = page.get('content_areas', [])
    if areas and full:
        lines.append(f"**Content Areas:** {', '.join(f'`{a}`' for a in areas)}")

    # Event handlers
    handlers = page.get('event_handlers', [])
    if handlers:
        lines.append('')
        if full:
            lines.append(f"**Event Handlers ({len(handlers)}):**")
            for h in handlers:
                lines.append(f"- `{h}()`")
        else:
            shown = handlers[:6]
            rest  = len(handlers) - len(shown)
            lines.append(f"**Handlers:** {', '.join(f'`{h}`' for h in shown)}" +
                         (f" _(+{rest})_" if rest > 0 else ''))

    # Imports (full mode only)
    if full and page.get('imports'):
        lines.append('')
        lines.append(f"**Namespaces ({len(page['imports'])}):**")
        for imp in sorted(page['imports'])[:15]:
            lines.append(f"- `{imp}`")

    # Navigation out
    nav_out = page.get('navigation_out', [])
    if nav_out:
        lines.append('')
        lines.append(f"**Redirects / Transfers ({len(nav_out)}):**")
        for n in nav_out[:8]:
            lines.append(f"- `{n['url']}` *({n.get('type', 'redirect')})*")
        if len(nav_out) > 8:
            lines.append(f"- _{len(nav_out) - 8} more…_")

    # Internal links — .aspx refs and named-route expressions
    nav_links = page.get('navigation_links', [])
    aspx_links = [n for n in nav_links
                  if '.aspx' in n.get('url', '').lower()
                  or n.get('type') == 'route'
                  or n.get('route_name')]
    if aspx_links and full:
        lines.append('')
        lines.append(f"**Internal Links ({len(aspx_links)}):**")
        for n in aspx_links[:8]:
            txt = f' — "{n["text"]}"' if n.get('text') else ''
            rn  = f' [route: {n["route_name"]}]' if n.get('route_name') else ''
            lines.append(f"- `{n['url']}`{txt}{rn}")
        if len(aspx_links) > 8:
            lines.append(f"- _{len(aspx_links) - 8} more…_")

    return lines


_AREA_WORKFLOW: Dict[str, str] = {
    'Authentication':  "Handles user identity: login, logout, registration, and password management.",
    'Administration':  "Admin-only area for managing users, settings, and system configuration.",
    'Reports':         "Data export and analytics dashboards. Typically authenticated, read-only.",
    'Products':        "Product catalog management: listing, creation, editing, categorisation.",
    'Orders':          "Order lifecycle: shopping cart, checkout, payment, invoice, fulfilment.",
    'Users':           "User account management: profiles, preferences, membership settings.",
    'Content':         "CMS content management: articles, pages, media, publishing workflow.",
    'Search':          "Search interface: query input, filtering, results display.",
    'Configuration':   "System configuration: settings, setup wizards, options.",
    'Errors':          "Error handling: 404, 500, access denied, and exception display pages.",
    'Home':            "Application entry points: home page, landing pages, main dashboard.",
    'Contact':         "User communication: contact forms, help, FAQ, feedback.",
    'General':         "Miscellaneous pages not classified into a specific functional area.",
}


def _area_workflow_summary(area: str, area_pages: List[dict]) -> str:
    base   = _AREA_WORKFLOW.get(area, f"Pages in the {area} functional area.")
    n      = len(area_pages)
    names  = sorted(p['name'] for p in area_pages)
    sample = ', '.join(f"`{n}.aspx`" for n in names[:5])
    extra  = f" _+{n - 5} more_" if n > 5 else ''
    return f"{base}\n\nKey pages: {sample}{extra}"

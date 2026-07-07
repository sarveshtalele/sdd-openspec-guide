"""
Consolidated Business Analysis Reporter
=======================================
Produces ONE markdown file (instead of 5) for a Web Forms app, focused on
BUSINESS behaviour rather than code mechanics. Sections:

  1. Executive Business Summary & Business Impact
  2. Application Snapshot (metrics)
  3. How the Business Works — website / user-journey view
  4. Business Capabilities (per functional area: rules, data flow, dependencies)
  5. Detailed Business Logic — client format
     (File / Class / Method / Purpose / Logic / Validation / Dependencies / Data Flow)
  6. Data Architecture, Integrations & Access Control
  7. Risks & Modernization Notes

Driven entirely by the compact streaming index — no source re-reads.
"""

from pathlib import Path
from typing import Dict, List, Any

from engine.aspx_method_extractor import method_significance

_AREA_BIZ = {
    'Authentication': "Controls **who can get in**. Gatekeeps every protected capability; a failure here blocks all revenue/operational flows.",
    'Administration': "**Back-office control**. Staff configure the system, manage users and data. High blast-radius — errors affect all customers.",
    'Reports': "**Decision support**. Feeds management/finance with operational and financial numbers.",
    'Products': "**What the business sells**. Catalog accuracy directly drives discoverability and sales.",
    'Orders': "**Where money is made**. Cart → checkout → payment → invoice. The core revenue transaction path.",
    'Users': "**Customer/account lifecycle**. Profiles, preferences, membership — retention and personalization.",
    'Content': "**What the business publishes**. Articles/pages/media — marketing and information reach.",
    'Search': "**Findability**. Helps users locate products/content; weak search = lost conversions.",
    'Configuration': "**System setup**. Settings that change runtime behaviour across the app.",
    'Finance': "**Money handling**. Payments, invoices, refunds, tax — compliance-sensitive.",
    'Shipping': "**Fulfilment**. Delivery, addresses, warehouse — post-purchase customer experience.",
    'Contact': "**Customer communication**. Support, feedback, enquiries.",
    'Errors': "Failure handling & user-facing error pages.",
    'Home': "Entry points / landing experience — first impression and routing into the app.",
    'General': "Supporting pages not tied to one capability.",
}


def _h(n, t): return f"{'#' * n} {t}"


def _pg(n): return f"{n} page" + ("" if n == 1 else "s")


def _infer_domain(index) -> str:
    areas = set(index.get('functional_areas', {}).keys())
    if {'Orders', 'Products'} & areas:
        return "an **e-commerce / order-processing** application"
    if 'Reports' in areas and 'Administration' in areas:
        return "an **internal line-of-business / admin** application"
    if 'Content' in areas:
        return "a **content / CMS-style** web application"
    return "a **transactional web** application"


# ---------------------------------------------------------------------------
def _business_impact(index) -> List[str]:
    s = index['stats']; wc = index.get('web_config', {})
    areas = index.get('functional_areas', {})
    out = [_h(2, "1. Executive Business Summary & Business Impact"), ""]
    out.append(f"**{index['project']}** is {_infer_domain(index)} built on ASP.NET Web Forms "
               f"(.NET Framework). It exposes **{s['total_pages']} web pages** organised into "
               f"**{s['total_functional_areas']} business capabilities**, backed by "
               f"**{s['total_methods']} code-behind methods**"
               + (f" and **{s['total_stored_procs']} stored procedures / SQL routines**" if s['total_stored_procs'] else "")
               + ".")
    out.append("")

    # revenue / risk framing
    impact = []
    if 'Orders' in areas:
        impact.append(f"- **Revenue path present** — `Orders` capability ({_pg(len(areas['Orders']))}) carries the cart/checkout/payment flow. Any outage here directly stops sales.")
    if 'Authentication' in areas:
        impact.append(f"- **Access gate** — `Authentication` ({_pg(len(areas['Authentication']))}) protects all secured features; auth defects lock out users or expose data.")
    if 'Administration' in areas:
        impact.append(f"- **Operational control** — `Administration` ({_pg(len(areas['Administration']))}) lets staff run the business; high blast-radius changes.")
    if wc.get('connection_strings'):
        impact.append(f"- **Data dependency** — runs on database(s): {', '.join('`'+c+'`' for c in wc['connection_strings'])}. The app is the front door to this data.")
    if s['pages_with_sql_direct']:
        impact.append(f"- **Embedded business logic in SQL** — {s['pages_with_sql_direct']} pages issue direct SQL; business rules live partly in the database layer.")
    if wc.get('smtp_host'):
        impact.append(f"- **Customer comms** — sends email via `{wc['smtp_host']}` (confirmations / notifications).")
    out += impact if impact else ["- General-purpose web application; no single dominant revenue path detected automatically."]
    out.append("")
    return out


def _snapshot(index) -> List[str]:
    s = index['stats']; wc = index.get('web_config', {})
    out = [_h(2, "2. Application Snapshot"), "",
           "| Aspect | Value |", "|--------|-------|",
           f"| Pages (.aspx) | {s['total_pages']} |",
           f"| User controls (.ascx) | {s['total_controls']} |",
           f"| Master pages | {s['total_masters']} |",
           f"| Business capabilities | {s['total_functional_areas']} |",
           f"| Code-behind methods | {s['total_methods']} |",
           f"| Stored procs / SQL routines | {s['total_stored_procs']} |",
           f"| Pages with direct SQL | {s['pages_with_sql_direct']} |",
           f"| Pages with validators | {s['pages_with_validators']} |",
           f"| Pages using AJAX | {s['pages_with_ajax']} |",
           f"| Authentication mode | {wc.get('auth_mode') or 'not declared'} |",
           f"| Database(s) | {', '.join(wc.get('connection_strings', [])) or '—'} |",
           f"| Session mode | {wc.get('session_mode') or '—'} |", ""]
    return out


def _website_view(index) -> List[str]:
    areas = index.get('functional_areas', {})
    nav = index.get('navigation_map', {})
    pages = {p['rel_path']: p for p in index['pages']}
    out = [_h(2, "3. How the Business Works — Website View"), "",
           "How a real user moves through the site and what each step does for the business.", ""]

    # capability map
    out.append(_h(3, "Capability Map"))
    out.append("")
    for area in sorted(areas, key=lambda a: -len(areas[a])):
        biz = _AREA_BIZ.get(area, f"{area} capability.")
        out.append(f"- **{area}** ({_pg(len(areas[area]))}) — {biz}")
    out.append("")

    # entry points
    entries = [p for p in index['pages']
               if p['name'].lower() in ('default', 'index', 'home', 'login', 'main')]
    out.append(_h(3, "Primary Entry Points"))
    out.append("")
    if entries:
        for e in entries[:8]:
            out.append(f"- `{e['rel_path']}` — {e['purpose']} *(access: {e['auth']})*")
    else:
        out.append("- No conventional entry page detected; routing likely via RouteConfig.")
    out.append("")

    # user journeys traced from nav map (cap depth)
    out.append(_h(3, "Representative User Journeys"))
    out.append("")
    name_of = {rp.replace('\\', '/'): p['name'] for rp, p in pages.items()}
    seeds = [e['rel_path'].replace('\\', '/') for e in entries[:4]] or list(nav.keys())[:4]
    drawn = 0
    for seed in seeds:
        chain = _trace(seed, nav, name_of, max_depth=6)
        if len(chain) > 1:
            out.append(f"- {' → '.join('`'+c+'`' for c in chain)}")
            drawn += 1
    if not drawn:
        out.append("- Navigation is mostly menu/master-page driven; few inline page-to-page links were detected statically.")
    out.append("")
    return out


def _trace(start, nav, name_of, max_depth=6):
    chain, seen, cur = [], set(), start
    for _ in range(max_depth):
        nm = name_of.get(cur, Path(cur).stem)
        if cur in seen:
            break
        seen.add(cur); chain.append(nm)
        nxts = nav.get(cur) or nav.get(cur.replace('/', '\\'))
        if not nxts:
            break
        cur = nxts[0].replace('\\', '/').lstrip('/')
    return chain


def _capabilities(index, max_pages_per_area=8) -> List[str]:
    areas = index.get('functional_areas', {})
    pages = {p['rel_path']: p for p in index['pages']}
    out = [_h(2, "4. Business Capabilities in Detail"), ""]
    for area in sorted(areas, key=lambda a: -len(areas[a])):
        ap = areas[area]
        out.append(_h(3, f"{area}  ({_pg(len(ap))})"))
        out.append("")
        out.append(_AREA_BIZ.get(area, f"{area} capability."))
        out.append("")

        # aggregate business signals across the area
        full = [pages[a['rel_path']] for a in ap if a['rel_path'] in pages]
        sql_pages = [p for p in full if p.get('uses_sql_direct') or
                     any(m.get('has_sql') for m in p.get('methods', []))]
        sprocs = sorted({sp for p in full for m in p.get('methods', [])
                         for sp in m.get('stored_procs', [])})
        rules = sorted({v for p in full for m in p.get('methods', [])
                        for v in m.get('validators', [])})
        emails = any(m.get('sends_email') for p in full for m in p.get('methods', []))

        if sprocs:
            out.append(f"**Database routines:** {', '.join('`'+s+'`' for s in sprocs[:15])}"
                       + (f" _(+{len(sprocs)-15})_" if len(sprocs) > 15 else ""))
        if rules:
            out.append(f"**Validation/business rules in play:** {', '.join('`'+r+'`' for r in rules[:10])}")
        if sql_pages:
            out.append(f"**Data-touching pages:** {len(sql_pages)} of {len(full)}")
        if emails:
            out.append("**Sends email** as part of this capability.")
        out.append("")

        out.append("| Page | Purpose | Access |")
        out.append("|------|---------|--------|")
        for a in sorted(ap, key=lambda x: x['name'])[:max_pages_per_area]:
            out.append(f"| `{a['name']}.aspx` | {a['purpose']} | {a['auth']} |")
        if len(ap) > max_pages_per_area:
            out.append(f"| _… {len(ap)-max_pages_per_area} more_ | | |")
        out.append("")
    return out


# ---------------------------------------------------------------------------
def _method_block(file_rel, cls, m) -> List[str]:
    out = [_h(4, f"`{m['name']}({_short(m['params'])})`"), ""]
    out.append(f"- **File:** `{file_rel}`")
    out.append(f"- **Class:** `{cls or '—'}`")
    out.append(f"- **Method:** `{m['name']}`"
               + (f"  *(event: {m['event_control']}.{m['event_type']})*" if m['is_event'] else ""))
    out.append(f"- **Purpose:** {m['purpose']}")

    # detailed business logic narrative
    logic = []
    if m['request_inputs']:
        logic.append(f"reads input(s) {', '.join('`'+x+'`' for x in m['request_inputs'])}")
    if m['control_reads']:
        logic.append(f"reads UI fields {', '.join('`'+x+'`' for x in m['control_reads'][:8])}")
    if m['has_sql'] or m['stored_procs'] or m['orm_ops']:
        da = []
        if m['is_stored_proc'] or m['stored_procs']:
            da.append("calls stored procedure(s) " + (', '.join('`'+s+'`' for s in m['stored_procs']) or "(name resolved at runtime)"))
        elif m['has_sql']:
            da.append("executes direct SQL")
        if m['orm_ops']:
            da.append("ORM/LINQ ops " + ', '.join('`'+o+'`' for o in m['orm_ops']))
        logic.append("; ".join(da))
    if m['has_calc']:
        logic.append("performs calculations on the data")
    if m['control_writes']:
        logic.append(f"updates UI {', '.join('`'+x+'`' for x in m['control_writes'][:8])}")
    if m['session_writes']:
        logic.append(f"stores into session {', '.join('`'+x+'`' for x in m['session_writes'])}")
    if m['redirects']:
        logic.append(f"redirects to {', '.join('`'+x+'`' for x in m['redirects'])}")
    if m['sends_email']:
        logic.append("sends an email")
    out.append(f"- **Detailed business logic:** {('; '.join(logic) + '.') if logic else 'Structural/helper logic; no data or navigation side-effects detected.'}")

    # validation / conditional rules
    vrules = []
    if m['validators']:
        vrules.append("ASP.NET validators / IsValid: " + ', '.join('`'+v+'`' for v in m['validators']))
    if m['guards']:
        vrules.append("guards: " + ', '.join('`'+g+'`' for g in m['guards']))
    if m['throws']:
        vrules.append("throws: " + ', '.join('`'+t+'`' for t in m['throws']))
    cond = []
    if m['if_count']:     cond.append(f"{m['if_count']} if")
    if m['else_count']:   cond.append(f"{m['else_count']} else")
    if m['switch_count']: cond.append(f"{m['switch_count']} switch")
    if m['loop_count']:   cond.append(f"{m['loop_count']} loop")
    if m['has_try']:      cond.append("try/catch")
    if cond:
        vrules.append("branching: " + ', '.join(cond))
    out.append(f"- **Validation / conditional rules:** {('; '.join(vrules) + '.') if vrules else 'None detected.'}")

    # called components / dependencies
    if m['dependencies']:
        deps = ', '.join(f"`{d['name']}` ({d['kind']})" for d in m['dependencies'][:12])
        out.append(f"- **Called components / dependencies:** {deps}.")
    else:
        out.append("- **Called components / dependencies:** none external detected.")

    # data flow / mappings
    df = []
    src = (m['request_inputs'] and "request params") or (m['control_reads'] and "UI fields") or None
    if src: df.append(f"IN ← {src}")
    if m['app_settings']:  df.append("config ← " + ', '.join('`'+a+'`' for a in m['app_settings']))
    if m['connection_strings']: df.append("DB ← " + ', '.join('`'+c+'`' for c in m['connection_strings']))
    if m['stored_procs'] or m['has_sql']: df.append("DB ↔ persistence")
    if m['session_writes'] or m['session_reads']:
        df.append("session ↔ " + ', '.join('`'+x+'`' for x in (m['session_writes'] + m['session_reads'])[:6]))
    if m['control_writes']: df.append("OUT → UI")
    if m['redirects']:      df.append("OUT → navigate")
    out.append(f"- **Data flow / mappings:** {(' | '.join(df)) if df else 'self-contained.'}")
    out.append("")
    return out


def _short(params, n=80):
    params = ' '.join(params.split())
    return params if len(params) <= n else params[:n] + '…'


def _detailed_logic(index, max_files=40, max_methods_per_file=10,
                    area_filter=None, full_detail=False) -> List[str]:
    pages = index['pages']
    if area_filter:
        pages = [p for p in pages if p.get('functional_area', '').lower() == area_filter.lower()]

    # score pages by business significance
    scored = []
    for p in pages:
        ms = p.get('methods', [])
        if not ms:
            continue
        score = sum(method_significance(m) for m in ms)
        scored.append((score, p))
    scored.sort(key=lambda x: -x[0])

    selected = scored if full_detail else scored[:max_files]

    out = [_h(2, "5. Detailed Business Logic (per File / Class / Method)"), ""]
    if not selected:
        out.append("_No code-behind business methods were detected to detail._")
        out.append("")
        return out
    scope = ("all pages with code-behind logic" if full_detail
             else f"top {len(selected)} most business-significant pages (of {len(scored)} with logic)")
    out.append(f"Format per client spec. Showing **{scope}**. "
               "Re-run with `--detail-area <Area>` or `--full-detail` for the rest.")
    out.append("")

    for _score, p in selected:
        cls = (f"{p['namespace']}.{p['class_name']}" if p.get('namespace') and p.get('class_name')
               else p.get('class_name', ''))
        out.append(_h(3, f"{p['name']}.aspx  —  `{p['rel_path']}`"))
        out.append("")
        out.append(f"- **File Name:** `{p['filename']}`  (+ code-behind)")
        out.append(f"- **Class Name:** `{cls or '—'}`")
        out.append(f"- **Functional Area:** {p.get('functional_area', 'General')}  |  **Access:** {p.get('auth', 'unknown')}")
        out.append(f"- **Page Purpose:** {p.get('purpose', '—')}")
        out.append("")
        ms = sorted(p['methods'], key=lambda m: -method_significance(m))
        for m in ms[:max_methods_per_file]:
            out += _method_block(p['rel_path'], cls, m)
        if len(ms) > max_methods_per_file:
            out.append(f"_… {len(ms)-max_methods_per_file} more methods in this file (run `--full-detail`)._")
            out.append("")
    return out


def _architecture(index) -> List[str]:
    wc = index.get('web_config', {}); s = index['stats']
    pages = index['pages']
    sprocs = sorted({sp for p in pages for m in p.get('methods', [])
                     for sp in m.get('stored_procs', [])})
    deps = {}
    for p in pages:
        for m in p.get('methods', []):
            for d in m.get('dependencies', []):
                if d['kind'] in ('service', 'repository'):
                    deps[d['name']] = d['kind']
    out = [_h(2, "6. Data Architecture, Integrations & Access Control"), ""]
    out.append(f"- **Database(s):** {', '.join('`'+c+'`' for c in wc.get('connection_strings', [])) or 'none in web.config'}")
    if sprocs:
        out.append(f"- **Stored procedures / SQL routines ({len(sprocs)}):** "
                   + ', '.join('`'+x+'`' for x in sprocs[:30])
                   + (f" _(+{len(sprocs)-30})_" if len(sprocs) > 30 else ""))
    if deps:
        out.append(f"- **Service / repository layer:** "
                   + ', '.join(f'`{n}` ({k})' for n, k in list(deps.items())[:25]))
    out.append(f"- **Authentication:** {wc.get('auth_mode') or 'not declared'}"
               + (f", login at `{wc['forms_auth_url']}`" if wc.get('forms_auth_url') else ""))
    if wc.get('smtp_host'):
        out.append(f"- **Email integration:** SMTP `{wc['smtp_host']}`")
    if wc.get('location_rules'):
        out.append(f"- **Path access rules:** {len(wc['location_rules'])} `<location>` rules in web.config")
    out.append("")
    out.append("**Access control by page count:**")
    out.append("")
    for k, v in sorted(s.get('auth_breakdown', {}).items(), key=lambda x: -x[1]):
        out.append(f"- `{k}`: {v} pages")
    out.append("")
    return out


def _risks(index) -> List[str]:
    s = index['stats']
    out = [_h(2, "7. Risks & Modernization Notes"), ""]
    if s['pages_with_sql_direct']:
        out.append(f"- ⚠️ **{s['pages_with_sql_direct']} pages embed direct SQL** in code-behind — "
                   "tight DB coupling and SQL-injection surface. Move to a data-access/service layer.")
    if s['total_pages'] and s['pages_with_master'] / max(s['total_pages'], 1) < 0.6:
        out.append(f"- ⚠️ Only {s['pages_with_master']}/{s['total_pages']} pages use a master page — inconsistent layout.")
    unknown = s.get('auth_breakdown', {}).get('unknown', 0)
    if unknown:
        out.append(f"- ⚠️ **{unknown} pages have undetermined access control** — audit for missing auth on sensitive pages.")
    out.append("- ASP.NET Web Forms is legacy; business logic is spread across markup, code-behind and SQL. "
               "Consolidating rules into a service layer is the prerequisite for any migration (Blazor/MVC/API).")
    out.append("")
    return out


def generate_business_report(index, area_filter=None, full_detail=False,
                             max_files=40) -> str:
    out = [f"# {index['project']} — Business Analysis (ASP.NET Web Forms)", "",
           f"> Reverse-engineered business view · generated {index.get('generated_at', '')}", "",
           "> Single consolidated report: business impact, website flow, capabilities, "
           "and per-method business logic.", "", "---", ""]
    out += _business_impact(index); out += ["---", ""]
    out += _snapshot(index); out += ["---", ""]
    out += _website_view(index); out += ["---", ""]
    out += _capabilities(index); out += ["---", ""]
    out += _detailed_logic(index, max_files=max_files,
                           area_filter=area_filter, full_detail=full_detail)
    out += ["---", ""]
    out += _architecture(index); out += ["---", ""]
    out += _risks(index)
    return '\n'.join(out)

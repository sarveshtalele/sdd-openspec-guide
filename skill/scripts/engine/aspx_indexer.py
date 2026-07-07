"""
ASPX Index Builder
==================
Shared stats computation, cross-reference linking, and derived-structure
builders (navigation map, functional areas, component map) for the ASPX
JSON index. The actual page/control/master parsing + orchestration lives in
engine.aspx_stream (streaming, memory-safe for 10,000+ files) — this module
holds the logic BOTH the streaming build path and the report generator
depend on, plus index load/save.

JSON Index structure:
  project, generated_at, repo_path
  stats             — aggregate counts and breakdowns
  web_config        — auth mode, connection strings, location rules
  pages[]           — per-page metadata (no raw content)
  user_controls[]   — per-control metadata + used_by_pages list
  master_pages[]    — per-master metadata + used_by_pages list
  functional_areas  — {area: [{name, rel_path, purpose, auth}]}
  navigation_map    — {page_rel_path: [linked_rel_paths]}
  component_map     — master/control usage summary
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_VALIDATOR_TYPES = {
    'requiredfieldvalidator', 'rangevalidator', 'comparevalidator',
    'regularexpressionvalidator', 'customvalidator',
}

# Above this many pages, save_index() switches to compact (no-indent) JSON —
# indentation roughly doubles file size and serialization time on huge repos,
# and the index is read by tooling, not eyeballed, at that scale.
_PRETTY_SAVE_THRESHOLD = 500


def compute_stats(pages: List[dict], controls: List[dict], masters: List[dict],
                   functional_areas: Dict[str, list], route_map: Dict[str, str],
                   extra: Optional[dict] = None) -> dict:
    """Shared stats block — used by both the in-process build path (this
    module, via engine.aspx_stream) and any future caller, so the fields
    available to aspx_reporter.py can never drift between code paths."""
    stats = {
        'total_pages':            len(pages),
        'total_controls':         len(controls),
        'total_masters':          len(masters),
        'total_functional_areas': len(functional_areas),
        'total_named_routes':     len(route_map),
        'pages_with_ajax':        sum(1 for p in pages if p.get('uses_ajax')),
        'pages_with_sql_direct':  sum(1 for p in pages if p.get('uses_sql_direct')),
        'pages_with_master':      sum(1 for p in pages if p.get('master_page')),
        'pages_with_codebehind':  sum(1 for p in pages if p.get('class_name')),
        'pages_with_validators':  sum(
            1 for p in pages
            if any(c['type'] in _VALIDATOR_TYPES for c in p.get('form_controls', []))
        ),
        'auth_breakdown':         _auth_breakdown(pages),
        'functional_area_counts': {a: len(v) for a, v in functional_areas.items()},
    }
    if extra:
        stats.update(extra)
    return stats


def save_index(index: dict, output_path: str) -> str:
    """Serialize and save the index to disk. Auto-picks compact JSON (no
    indent) once the repo is large enough that pretty-printing meaningfully
    slows down / bloats the save — see _PRETTY_SAVE_THRESHOLD."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    total_pages = index.get('stats', {}).get('total_pages', 0)
    indent = 2 if total_pages < _PRETTY_SAVE_THRESHOLD else None
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=indent, ensure_ascii=False, default=str)
    size_kb = os.path.getsize(output_path) // 1024
    print(f"  [ok] Index saved -> {output_path}  ({size_kb} KB)")
    return output_path


def load_index(index_path: str) -> dict:
    """Load a previously saved index JSON."""
    with open(index_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _normalise_path(p: str) -> str:
    """Normalise a path string for comparison (lower, forward slashes, stripped ~/)."""
    return p.replace('~/', '').lstrip('/').replace('\\', '/').lower()


# ---------------------------------------------------------------------------
# Route config parsing
# ---------------------------------------------------------------------------

_MAP_PAGE_ROUTE = re.compile(
    r'MapPageRoute\s*\(\s*"([^"]+)"\s*,\s*"[^"]*"\s*,\s*"([^"]+)"',
    re.IGNORECASE | re.DOTALL,
)

_ROUTE_EXPR = re.compile(
    r'(?:RouteUrl:RouteName=|GetRouteUrl\s*\(\s*["\'])(\w+)',
    re.IGNORECASE,
)


def _parse_route_configs(route_records: List[dict], pages: List[dict]) -> Dict[str, str]:
    """Parse RouteConfig.cs → {route_name: page_rel_path}.

    Resolves physical paths (~/Catalog/Create.aspx) against discovered pages
    via suffix matching so solution-level path prefixes don't matter.
    """
    # Build suffix index: every suffix of a normalised page path → rel_path
    page_by_suffix: Dict[str, str] = {}
    for p in pages:
        norm = _normalise_path(p['rel_path'])
        parts = norm.split('/')
        for i in range(len(parts)):
            suffix = '/'.join(parts[i:])
            if suffix not in page_by_suffix:
                page_by_suffix[suffix] = p['rel_path']

    route_map: Dict[str, str] = {}
    for rec in route_records:
        content = rec.get('content', '')
        for rname, phys in _MAP_PAGE_ROUTE.findall(content):
            aspx_norm = _normalise_path(phys)   # e.g. "catalog/create.aspx"
            resolved  = page_by_suffix.get(aspx_norm)
            if resolved:
                route_map[rname.strip()] = resolved
    return route_map


def _link_usages(pages: List[dict], controls: List[dict], masters: List[dict]) -> None:
    """Populate used_by_pages lists on controls and masters by scanning page registrations."""
    import os as _os

    # Build lookup maps: normalised rel_path → index
    ctrl_map: Dict[str, int] = {}
    for i, c in enumerate(controls):
        ctrl_map[_normalise_path(c['rel_path'])] = i
        ctrl_map[c['filename'].lower()] = i

    # For masters: exact path lookup + filename→candidates list for proximity resolution.
    # When two masters share the same filename (e.g. two solutions each have Site.Master),
    # naively keying by filename causes the last one to win. Instead we keep all candidates
    # and pick the one whose folder is the closest ancestor of the referencing page.
    master_by_path: Dict[str, int] = {}
    master_by_name: Dict[str, List[tuple]] = {}  # filename.lower → [(idx, norm_folder)]
    for i, m in enumerate(masters):
        norm_rel = _normalise_path(m['rel_path'])
        master_by_path[norm_rel] = i
        fname = m['filename'].lower()
        norm_folder = _normalise_path(str(Path(m['rel_path']).parent))
        master_by_name.setdefault(fname, []).append((i, norm_folder))

    def _resolve_master(mp_norm: str, page_folder_norm: str) -> 'Optional[int]':
        # 1. Exact full-path match
        idx = master_by_path.get(mp_norm)
        if idx is not None:
            return idx
        # 2. Filename-only reference — pick candidate with longest common path prefix
        fname = Path(mp_norm).name.lower()
        candidates = master_by_name.get(fname, [])
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0][0]
        best_idx, best_len = candidates[0][0], -1
        for cidx, cfolder in candidates:
            common_len = len(_os.path.commonprefix([page_folder_norm, cfolder]))
            if common_len > best_len:
                best_len, best_idx = common_len, cidx
        return best_idx

    for page in pages:
        page_ref = page['rel_path']
        page_folder = _normalise_path(str(Path(page_ref).parent))

        # Master page back-link
        mp = _normalise_path(page.get('master_page', ''))
        if mp:
            idx = _resolve_master(mp, page_folder)
            if idx is not None and page_ref not in masters[idx]['used_by_pages']:
                masters[idx]['used_by_pages'].append(page_ref)

        # User control back-links
        for reg in page.get('controls_registered', []):
            src = _normalise_path(reg.get('src', ''))
            if src:
                idx = ctrl_map.get(src) or ctrl_map.get(Path(src).name.lower())
                if idx is not None and page_ref not in controls[idx]['used_by_pages']:
                    controls[idx]['used_by_pages'].append(page_ref)


def _build_navigation_map(pages: List[dict], route_map: Dict[str, str] = None) -> Dict[str, List[str]]:
    """Build page→page navigation adjacency (HyperLinks, anchors, Response.Redirect, named routes).

    route_map — {route_name: rel_path} from RouteConfig.cs; resolves
    <%$RouteUrl:RouteName=X%> and GetRouteUrl("X",...) expressions.
    """
    if route_map is None:
        route_map = {}
    nav: Dict[str, List[str]] = {}

    for page in pages:
        src   = page['rel_path'].replace('\\', '/')
        links = page.get('navigation_links', []) + page.get('navigation_out', [])
        targets: List[str] = []

        for link in links:
            url = link.get('url', '').strip()
            # 1. Direct .aspx reference
            url_clean = url.replace('~/', '').replace('\\', '/').split('?')[0].split('#')[0]
            if url_clean.lower().endswith('.aspx') and not url_clean.startswith('http'):
                targets.append(url_clean)
            # 2. Named route pre-tagged by parser (route_name key present)
            elif link.get('route_name') and route_map:
                resolved = route_map.get(link['route_name'])
                if resolved:
                    targets.append(resolved.replace('\\', '/'))
            # 3. Inline route expression not yet tagged — scan url value
            elif route_map:
                for rname in _ROUTE_EXPR.findall(url):
                    resolved = route_map.get(rname)
                    if resolved:
                        targets.append(resolved.replace('\\', '/'))

        if targets:
            nav[src] = list(dict.fromkeys(targets))

    return nav


def _build_functional_areas(pages: List[dict]) -> Dict[str, List[dict]]:
    """Group pages by functional area. Returned dict is alphabetically sorted."""
    areas: Dict[str, List[dict]] = {}
    for page in pages:
        area = page.get('functional_area', 'General')
        areas.setdefault(area, []).append({
            'name':     page['name'],
            'rel_path': page['rel_path'],
            'purpose':  page['purpose'],
            'auth':     page['auth'],
        })
    return dict(sorted(areas.items()))


def _build_component_map(controls: List[dict], masters: List[dict]) -> dict:
    """Compact usage summary for the component view."""
    return {
        'master_pages': {
            m['rel_path']: {
                'name':              m['name'],
                'pages_count':       len(m['used_by_pages']),
                'placeholders':      m.get('content_placeholders', []),
                'has_login':         m.get('has_login_controls', False),
                'navigation_menus':  list(set(m.get('navigation_menus', []))),
            }
            for m in masters
        },
        'user_controls': {
            c['rel_path']: {
                'name':        c['name'],
                'pages_count': len(c.get('used_by_pages', [])),
                'purpose':     c['purpose'],
            }
            for c in controls
        },
    }


def _auth_breakdown(pages: List[dict]) -> Dict[str, int]:
    breakdown: Dict[str, int] = {}
    for p in pages:
        auth = p.get('auth', 'unknown')
        breakdown[auth] = breakdown.get(auth, 0) + 1
    return dict(sorted(breakdown.items()))

"""
Streaming ASPX Indexer  (10,000+ file safe — the ONLY build path)
==================================================================
Both aspx_analysis_skill.py (5-view report) and aspx_business_analyzer.py
(consolidated business report) build their index through this module.

Why streaming instead of load-everything-then-parse:
  * Reading every file's raw content into in-memory lists BEFORE parsing
    (pages/controls/masters each holding full `content` + `codebehind_content`)
    pushes peak memory to roughly the whole repo's source size — on 10,000+
    file repos that exhausts memory and kills the terminal.
  * Instead: discover paths only (no content read), then process one file at
    a time (read → parse → keep compact dict → discard raw text). At most
    one file body is alive per worker at any moment, so memory stays flat
    regardless of repo size.

Optional multiprocessing fans the parse out across cores; workers return
small dicts (pickled back to the main process), never raw file bodies once
parsed.

Public:
    build_index_streaming(repo_path, repo_name, workers=0,
                          max_bytes=1_500_000, max_pages=0,
                          with_methods=True, progress=True)
        -> compact index dict (same shape aspx_reporter.py expects; plus
           per-page 'methods' when with_methods=True, used by the business
           report — the 5-view report doesn't need them, so
           aspx_analysis_skill.py passes with_methods=False to skip that
           extra regex pass over every code-behind file)
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List
from concurrent.futures import ProcessPoolExecutor

from engine.aspx_loader import discover_paths, build_codebehind_map, _read_file
from engine.aspx_parser import (
    parse_aspx_page, parse_ascx_control, parse_master_page, parse_web_config,
)
from engine.aspx_method_extractor import extract_methods
from engine.aspx_indexer import (
    compute_stats, _link_usages, _parse_route_configs, _build_navigation_map,
    _build_functional_areas, _build_component_map,
)

# generated / designer / minified files never carry business logic
_SKIP_CB_SUFFIX = ('.designer.cs', '.g.cs', '.g.i.cs', 'assemblyinfo.cs')


def _skip_cb(path: str) -> bool:
    p = path.lower()
    return any(p.endswith(s) for s in _SKIP_CB_SUFFIX)


# ---------------------------------------------------------------------------
# Worker — runs in a separate process (must be top-level & picklable)
# ---------------------------------------------------------------------------

def _process_page(args):
    """Read one .aspx (+ code-behind), return compact parsed dict (+ methods
    when the caller asked for them)."""
    rec, cb_path, max_bytes, with_methods = args
    try:
        if os.path.getsize(rec['path']) > max_bytes:
            content = _read_file(rec['path'])[:max_bytes]
        else:
            content = _read_file(rec['path'])
    except OSError:
        content = ''

    cb_content = ''
    if cb_path and not _skip_cb(cb_path):
        try:
            if os.path.getsize(cb_path) <= max_bytes:
                cb_content = _read_file(cb_path)
        except OSError:
            cb_content = ''

    parsed = parse_aspx_page({**rec, 'content': content,
                              'codebehind_content': cb_content})
    parsed['methods'] = extract_methods(cb_content) if with_methods else []
    return parsed


def _process_simple(args):
    """Generic worker for .ascx / .master (no method extraction needed)."""
    rec, cb_path, kind, max_bytes = args
    content = ''
    try:
        if os.path.getsize(rec['path']) <= max_bytes:
            content = _read_file(rec['path'])
    except OSError:
        pass
    cb_content = ''
    if cb_path and not _skip_cb(cb_path):
        try:
            if os.path.getsize(cb_path) <= max_bytes:
                cb_content = _read_file(cb_path)
        except OSError:
            pass
    full = {**rec, 'content': content, 'codebehind_content': cb_content}
    return parse_ascx_control(full) if kind == 'ascx' else parse_master_page(full)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def build_index_streaming(repo_path: str, repo_name: str,
                          workers: int = 0, max_bytes: int = 1_500_000,
                          max_pages: int = 0, with_methods: bool = True,
                          progress: bool = True) -> dict:
    repo_path = str(Path(repo_path).resolve())
    if progress:
        print(f"  Discovering files (streaming, memory-safe) in: {repo_path}")

    cap = max_pages if max_pages > 0 else 1_000_000
    paths = discover_paths(repo_path, max_pages=cap)
    cb_map = build_codebehind_map(paths)

    n_pages = len(paths['pages'])
    n_ctrls = len(paths['controls'])
    n_mast  = len(paths['masters'])
    if progress:
        print(f"  Found: {n_pages} .aspx | {n_ctrls} .ascx | {n_mast} .master | "
              f"{len(paths['cs_files'])} .cs | {len(paths.get('routes', []))} route cfg")

    def _cb_for(rec):
        lp = rec['path'].lower()
        return cb_map.get(lp) or cb_map.get(lp + '.cs', '')

    page_args = [(r, _cb_for(r), max_bytes, with_methods) for r in paths['pages']]
    ctrl_args = [(r, _cb_for(r), 'ascx', max_bytes) for r in paths['controls']]
    mast_args = [(r, _cb_for(r), 'master', max_bytes) for r in paths['masters']]

    pages: List[dict] = []
    controls: List[dict] = []
    masters: List[dict] = []

    if workers and workers > 1 and n_pages > 200:
        if progress:
            print(f"  Parsing pages across {workers} processes ...")
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for i, p in enumerate(ex.map(_process_page, page_args, chunksize=25)):
                pages.append(p)
                if progress and (i + 1) % 500 == 0:
                    print(f"    ... {i + 1}/{n_pages} pages")
            controls = list(ex.map(_process_simple, ctrl_args, chunksize=25))
            masters  = list(ex.map(_process_simple, mast_args, chunksize=25))
    else:
        if progress:
            print(f"  Parsing {n_pages} pages (single process, streaming) ...")
        for i, a in enumerate(page_args):
            pages.append(_process_page(a))
            if progress and (i + 1) % 500 == 0:
                print(f"    ... {i + 1}/{n_pages} pages")
        controls = [_process_simple(a) for a in ctrl_args]
        masters  = [_process_simple(a) for a in mast_args]

    # web.config
    web_config: dict = {}
    for cfg in paths['configs']:
        if cfg.get('filename', '').lower() == 'web.config':
            web_config = parse_web_config({**cfg, 'content': _read_file(cfg['path'])})
            break

    if progress:
        print("  Building cross-references ...")
    _link_usages(pages, controls, masters)

    route_records = [{**r, 'content': _read_file(r['path'])}
                     for r in paths.get('routes', [])]
    route_map = _parse_route_configs(route_records, pages)

    nav_map          = _build_navigation_map(pages, route_map)
    functional_areas = _build_functional_areas(pages)
    component_map    = _build_component_map(controls, masters)

    extra_stats = {}
    if with_methods:
        extra_stats['total_methods'] = sum(len(p.get('methods', [])) for p in pages)
        extra_stats['total_stored_procs'] = len({
            sp for p in pages for m in p.get('methods', []) for sp in m.get('stored_procs', [])
        })
    stats = compute_stats(pages, controls, masters, functional_areas, route_map, extra=extra_stats)

    return {
        'project': repo_name, 'repo_path': repo_path,
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'stats': stats, 'web_config': web_config,
        'pages': pages, 'user_controls': controls, 'master_pages': masters,
        'functional_areas': functional_areas, 'navigation_map': nav_map,
        'component_map': component_map, 'route_map': route_map,
    }

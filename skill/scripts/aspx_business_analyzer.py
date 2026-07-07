#!/usr/bin/env python3
"""
ASPX Business Analyzer — single-file, 10,000+ file safe
=======================================================
Streaming, memory-safe reverse-engineering of an ASP.NET Web Forms app into
ONE consolidated business markdown file (not 5). Built for huge legacy repos
where the original 5-view skill hangs / kills PowerShell.

Why this does not hang:
  * Streams files one at a time (read → parse → keep compact dict → discard).
  * Optional multiprocessing across cores.
  * Skips generated/designer/minified files and caps per-file bytes.
  * Prints only a short summary to stdout — never dumps the full report.
  * Emits ONE .md + one compact .json index for follow-up queries.

Usage:
    python aspx_business_analyzer.py <target> [options]

<target>: https://github.com/org/repo  |  C:\\path\\to\\repo  |  .

Options:
    --workers N        Parallel parser processes (default: CPU count, capped 8). 1 = serial.
    --max-bytes N      Skip code-behind files larger than N bytes (default 1500000).
    --max-pages N      Cap number of .aspx pages parsed (0 = no cap).
    --detail-area A    Emit the detailed per-method section ONLY for area A (e.g. Orders).
    --full-detail      Detail EVERY page with logic (large output; use for a single area).
    --max-files N      Cap detailed-logic pages when not --full-detail (default 40).
    --rebuild          Ignore cached index and re-parse.
    --output DIR       Output directory (default ./{repo_name}/).

Examples:
    python aspx_business_analyzer.py .
    python aspx_business_analyzer.py . --workers 8
    python aspx_business_analyzer.py . --detail-area Orders --full-detail
    python aspx_business_analyzer.py https://github.com/org/App --max-files 60
"""

import sys, os, io, re, json, shutil, subprocess, tempfile
from pathlib import Path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from engine.aspx_stream import build_index_streaming
from engine.aspx_indexer import save_index
from engine.aspx_business_reporter import generate_business_report

_HELP = __doc__


def _is_github(s): return s.startswith(('https://github.com/', 'http://github.com/'))
def _repo_name(url): return re.sub(r'[^\w\-]', '_', url.rstrip('/').removesuffix('.git').split('/')[-1])


def _clone(url, target):
    print(f"  Cloning {url} ...")
    r = subprocess.run(['git', 'clone', '--depth=1', url, target],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git clone failed:\n{r.stderr.strip()}")


def main():
    if len(sys.argv) < 2:
        print(_HELP); sys.exit(1)

    args = sys.argv[1:]
    opts = {'target': None, 'workers': None, 'max_bytes': 1_500_000, 'max_pages': 0,
            'detail_area': None, 'full_detail': False, 'max_files': 40,
            'rebuild': False, 'output': None}
    i = 0
    while i < len(args):
        a = args[i]
        if a in ('-h', '--help'): print(_HELP); sys.exit(0)
        elif a == '--workers':     opts['workers'] = int(args[i+1]); i += 2
        elif a == '--max-bytes':   opts['max_bytes'] = int(args[i+1]); i += 2
        elif a == '--max-pages':   opts['max_pages'] = int(args[i+1]); i += 2
        elif a == '--detail-area': opts['detail_area'] = args[i+1]; i += 2
        elif a == '--max-files':   opts['max_files'] = int(args[i+1]); i += 2
        elif a == '--output':      opts['output'] = args[i+1]; i += 2
        elif a == '--full-detail': opts['full_detail'] = True; i += 1
        elif a == '--rebuild':     opts['rebuild'] = True; i += 1
        elif not a.startswith('--') and opts['target'] is None: opts['target'] = a; i += 1
        else: i += 1

    target = opts['target']
    if not target:
        sys.exit('Error: no target. Use a GitHub URL, local path, or "."')
    if target == '.':
        target = os.getcwd()

    if opts['workers'] is None:
        opts['workers'] = min(8, os.cpu_count() or 2)

    tmp = None
    try:
        if _is_github(target):
            name = _repo_name(target)
            tmp = tempfile.mkdtemp(prefix='aspx_biz_')
            repo_path = os.path.join(tmp, name)
            print(f"[1/4] Cloning {target}")
            _clone(target, repo_path)
        else:
            repo_path = str(Path(target).resolve())
            if not os.path.isdir(repo_path):
                sys.exit(f"Error: path not found — {repo_path}")
            name = Path(repo_path).name or 'project'
            print(f"[1/4] Local repo: {repo_path}")

        out_dir = opts['output'] or os.path.join(os.getcwd(), name)
        os.makedirs(out_dir, exist_ok=True)
        index_path = os.path.join(out_dir, f'{name}_business_index.json')

        if os.path.exists(index_path) and not opts['rebuild']:
            print(f"[2/4] Loading cached index: {index_path}")
            with open(index_path, encoding='utf-8') as f:
                index = json.load(f)
        else:
            print(f"[2/4] Streaming parse (workers={opts['workers']}, "
                  f"max_bytes={opts['max_bytes']}) ...")
            index = build_index_streaming(
                repo_path, name, workers=opts['workers'],
                max_bytes=opts['max_bytes'], max_pages=opts['max_pages'],
                with_methods=True)
            if not index['pages'] and not index['user_controls'] and not index['master_pages']:
                print("\n[!] No ASP.NET Web Forms files found (*.aspx/*.ascx/*.master).")
                return
            save_index(index, index_path)

        print("[3/4] Generating consolidated business report ...")
        report = generate_business_report(
            index, area_filter=opts['detail_area'],
            full_detail=opts['full_detail'], max_files=opts['max_files'])

        report_path = os.path.join(out_dir, f'{name}_BusinessAnalysis.md')
        Path(report_path).write_text(report, encoding='utf-8')

        # ---- SHORT summary only (never dump full report → no terminal flood) ----
        s = index['stats']
        print("[4/4] Done.\n")
        print("=" * 60)
        print(f"  ASPX BUSINESS ANALYSIS — {index['project']}")
        print("=" * 60)
        print(f"  Pages: {s['total_pages']} | Controls: {s['total_controls']} | "
              f"Masters: {s['total_masters']}")
        print(f"  Methods: {s['total_methods']} | Stored procs: {s['total_stored_procs']} | "
              f"Capabilities: {s['total_functional_areas']}")
        print(f"  Areas: {', '.join(sorted(index['functional_areas'].keys()))}")
        print(f"\n  Report : {report_path}")
        print(f"  Index  : {index_path}")
        print(f"\n  Report size: {os.path.getsize(report_path)//1024} KB "
              f"({report.count(chr(10))} lines)")
        print("  Tip: --detail-area <Area> --full-detail for deep per-method detail of one area.")
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()

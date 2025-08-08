#!/usr/bin/env python3
"""
Scan React/Expo frontend and FastAPI backend for unused files.
- Frontend: uses `npx depcheck` if available + asset-reference scan
- Backend: uses `vulture` if available + naive import graph (suspected)
- Outputs a combined report and can optionally archive flagged files.

Usage:
  python find_unused.py --frontend ./frontend --backend ./backend \
      [--archive] [--archive-dir ./archive_unused] [--confidence 80]

Notes:
- Requires Node (for npx) to run depcheck in the frontend folder (optional).
- Requires `vulture` installed for backend dead-code hints (optional):
    pip install vulture
- Nothing is moved unless `--archive` is provided.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple

# ------------ Helpers ------------

def run(cmd: List[str], cwd: Path | None = None, timeout: int = 180) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(
            cmd, cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, timeout=timeout, check=False
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", "Timed out"

def list_files(root: Path, exts: Tuple[str, ...], ignore_dirs: Tuple[str, ...]) -> List[Path]:
    out = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(ignored in p.parts for ignored in ignore_dirs):
            continue
        if p.suffix.lower() in exts:
            out.append(p)
    return out

def rel(p: Path, base: Path) -> str:
    try:
        return str(p.relative_to(base))
    except Exception:
        return str(p)

def ensure_archive_target(base_dir: Path, archive_dir: Path, file_path: Path) -> Path:
    rel_path = file_path.relative_to(base_dir)
    target = archive_dir / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    return target

# ------------ Frontend: depcheck + asset reference scan ------------

def run_depcheck(frontend_dir: Path) -> Dict:
    """
    Runs `npx depcheck --json`. Returns parsed JSON dict or {} if unavailable.
    """
    code, out, err = run(["npx", "-y", "depcheck", "--json"], cwd=frontend_dir)
    if code != 0:
        # depcheck may fail on some projects; that's okay, we'll fall back.
        return {}
    try:
        data = json.loads(out or "{}")
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}

def frontend_asset_scan(frontend_dir: Path) -> Dict[str, List[str]]:
    """
    Conservative scan for asset files (images/fonts/css) whose *basename* isn't referenced
    anywhere in source files. Avoids node_modules and typical build dirs.
    """
    src_exts = (".js", ".jsx", ".ts", ".tsx")
    asset_exts = (".png", ".jpg", ".jpeg", ".gif", ".svg",
                  ".webp", ".mp3", ".mp4", ".wav", ".ttf", ".otf", ".woff", ".woff2",
                  ".css", ".scss")
    ignore_dirs = ("node_modules", "build", "dist", ".expo", ".turbo", ".next", ".git")

    src_files = list_files(frontend_dir, src_exts, ignore_dirs)
    asset_files = list_files(frontend_dir, asset_exts, ignore_dirs)

    # Collect source contents once (lowercased for cheap contains)
    big_source_blob = []
    for f in src_files:
        try:
            s = f.read_text(encoding="utf-8", errors="ignore").lower()
            big_source_blob.append(s)
        except Exception:
            pass
    joined = "\n".join(big_source_blob)

    suspected_unused_assets = []
    for af in asset_files:
        name = af.name.lower()
        # Heuristic: referenced if basename occurs in any source file
        if name not in joined:
            suspected_unused_assets.append(rel(af, frontend_dir))

    return {"suspected_unused_assets": sorted(set(suspected_unused_assets))}

def find_frontend_unused(frontend_dir: Path) -> Dict:
    results = {
        "depcheck_unused_files": [],
        "depcheck_unused_deps": [],
        "depcheck_missing_deps": {},
        "asset_scan": {"suspected_unused_assets": []},
        "warnings": []
    }
    # depcheck (best-effort)
    dep = run_depcheck(frontend_dir)
    if dep:
        # depcheck JSON shape can vary by version. Handle common fields.
        if isinstance(dep.get("unused"), list):
            results["depcheck_unused_deps"] = dep.get("unused", [])
        if isinstance(dep.get("missing"), dict):
            results["depcheck_missing_deps"] = dep.get("missing", {})
        # Some depcheck builds include 'unusedFiles' under 'specials' runs; try common keys:
        # Look for top-level 'files' candidates if present in some forks
        for key in ("unusedFiles", "files", "unused_files"):
            val = dep.get(key)
            if isinstance(val, list):
                results["depcheck_unused_files"].extend(val)
    else:
        results["warnings"].append("depcheck not available or failed; skipping depcheck-based file detection.")

    # Asset reference scan
    results["asset_scan"] = frontend_asset_scan(frontend_dir)
    return results

# ------------ Backend: vulture + naive import graph ------------

IMPORT_RE = re.compile(r'^\s*(?:from\s+([a-zA-Z0-9_\.]+)\s+import|import\s+([a-zA-Z0-9_\.]+))', re.MULTILINE)

def run_vulture(backend_dir: Path, min_conf: int) -> List[str]:
    """
    Runs vulture to collect file paths with dead code hits.
    Returns unique file paths (relative) with at least one finding.
    """
    code, out, err = run(["vulture", str(backend_dir), f"--min-confidence={min_conf}"])
    if code != 0:
        return []
    files_with_hits = set()
    for line in out.splitlines():
        # vulture typical line: /path/to/file.py:123: unused function 'foo'
        if ":" in line:
            fpath = line.split(":", 1)[0].strip()
            p = Path(fpath)
            if p.exists():
                try:
                    files_with_hits.add(str(Path(fpath).resolve().relative_to(backend_dir.resolve())))
                except Exception:
                    files_with_hits.add(str(p))
    return sorted(files_with_hits)

def backend_import_graph_suspects(backend_dir: Path) -> List[str]:
    """
    Very rough detector of .py files that no one imports.
    - Builds a set of module-like names used in imports.
    - Flags leaf files that are never imported AND aren't obvious entrypoints.
    """
    ignore_dirs = ("__pycache__", ".venv", "venv", ".mypy_cache", ".pytest_cache", ".git", "migrations", "alembic")
    py_files = [p for p in list_files(backend_dir, (".py",), ignore_dirs) if p.name != "__init__.py"]

    # Collect all import tokens
    imported_modules: Set[str] = set()
    for p in py_files:
        try:
            s = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in IMPORT_RE.finditer(s):
            mod = (m.group(1) or m.group(2) or "").strip()
            if mod:
                imported_modules.add(mod.split(".", 1)[0])

    suspects = []
    entrypoint_like = {"main.py", "app.py", "asgi.py", "wsgi.py"}
    for p in py_files:
        if p.name in entrypoint_like:
            continue
        # crude module name == filename without suffix
        modname = p.stem
        if modname not in imported_modules:
            suspects.append(rel(p, backend_dir))

    return sorted(suspects)

def find_backend_unused(backend_dir: Path, min_conf: int) -> Dict:
    results = {
        "vulture_files_with_findings": [],
        "suspected_unreferenced_py_files": [],
        "warnings": []
    }
    # vulture (optional but recommended)
    vul = run_vulture(backend_dir, min_conf)
    if vul:
        results["vulture_files_with_findings"] = vul
    else:
        results["warnings"].append("vulture not available or found nothing; skipping vulture findings.")

    # naive import graph suspects
    suspects = backend_import_graph_suspects(backend_dir)
    results["suspected_unreferenced_py_files"] = suspects
    return results

# ------------ Archiving ------------

def archive_files(base_dir: Path, archive_dir: Path, files: List[str]) -> List[str]:
    moved = []
    for relpath in files:
        src = (base_dir / relpath).resolve()
        if not src.exists() or not src.is_file():
            continue
        dst = ensure_archive_target(base_dir, archive_dir, src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Skip if already archived
        if dst.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        moved.append(relpath)
    return moved

# ------------ Main ------------

def main():
    ap = argparse.ArgumentParser(description="Find and optionally archive unused files in React/Expo + FastAPI repos.")
    ap.add_argument("--frontend", type=str, required=True, help="Path to frontend root (React/Expo project root with package.json).")
    ap.add_argument("--backend", type=str, required=True, help="Path to backend root (FastAPI project root).")
    ap.add_argument("--archive", action="store_true", help="Move suspected unused files to archive directory.")
    ap.add_argument("--archive-dir", type=str, default="./archive_unused", help="Archive output root (default: ./archive_unused).")
    ap.add_argument("--confidence", type=int, default=80, help="vulture --min-confidence (default: 80).")
    args = ap.parse_args()

    frontend_dir = Path(args.frontend).resolve()
    backend_dir = Path(args.backend).resolve()
    archive_root = Path(args.archive_dir).resolve()

    report = {
        "frontend": find_frontend_unused(frontend_dir),
        "backend": find_backend_unused(backend_dir, args.confidence),
        "archived": {"frontend": [], "backend": []},
        "notes": [
            "This is conservative. Review before deleting.",
            "Frontend assets are flagged when their basename is not referenced in source; dynamic references may create false positives.",
            "Backend suspected .py files are based on naive import graph; modules referenced dynamically (e.g., via importlib) won't be detected.",
        ]
    }

    if args.archive:
        # Collate candidate file lists
        fe_candidates: Set[str] = set(report["frontend"].get("depcheck_unused_files", []))
        fe_candidates.update(report["frontend"].get("asset_scan", {}).get("suspected_unused_assets", []))

        be_candidates: Set[str] = set(report["backend"].get("vulture_files_with_findings", []))
        be_candidates.update(report["backend"].get("suspected_unreferenced_py_files", []))

        # Move them into archive keeping tree layout
        fe_moved = archive_files(frontend_dir, archive_root / "frontend", sorted(fe_candidates))
        be_moved = archive_files(backend_dir,   archive_root / "backend",  sorted(be_candidates))
        report["archived"]["frontend"] = fe_moved
        report["archived"]["backend"]  = be_moved

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
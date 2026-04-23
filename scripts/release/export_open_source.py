#!/usr/bin/env python3
"""Export StataFlow main repo to StataFlow_open_source per manifest."""

import argparse
import fnmatch
import hashlib
import os
import shutil
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


def repo_root() -> Path:
    """Return the repository root (parent of scripts/release)."""
    return Path(__file__).resolve().parent.parent.parent


def load_manifest(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def expand_wildcards(root: Path, pattern: str) -> list[Path]:
    """Expand a wildcard pattern relative to root."""
    if "*" not in pattern:
        p = root / pattern
        return [p] if p.exists() else []
    parts = pattern.replace("\\", "/").split("/")
    current = [root]
    for part in parts:
        next_level = []
        for c in current:
            if not c.is_dir():
                continue
            for child in c.iterdir():
                if fnmatch.fnmatch(child.name, part):
                    next_level.append(child)
        current = next_level
    return current


def is_blacklisted(rel_path: str, patterns: list[str]) -> bool:
    """Check if a relative path matches any blacklist pattern."""
    rel = rel_path.replace("\\", "/")
    basename = os.path.basename(rel)
    for pat in patterns:
        if pat.endswith("/**"):
            seg = pat[:-3]
            if f"/{seg}/" in f"/{rel}/" or rel.startswith(seg + "/") or rel == seg:
                return True
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(basename, pat):
            return True
    return False


def collect_source_paths(root: Path, manifest: dict) -> set[Path]:
    """Collect all source paths that should be exported."""
    wl = manifest.get("whitelist", {})
    paths: set[Path] = set()

    # files (root-level)
    for p in wl.get("files", []):
        for item in expand_wildcards(root, p):
            if item.exists():
                paths.add(item.resolve())

    # specific_files
    for p in wl.get("specific_files", []):
        for item in expand_wildcards(root, p):
            if item.exists():
                paths.add(item.resolve())

    # test_files (wildcards)
    for p in wl.get("test_files", []):
        for item in expand_wildcards(root, p):
            if item.is_file():
                paths.add(item.resolve())

    # directories (recursive)
    for key in ("directories", "data_directories"):
        for p in wl.get(key, []):
            start = root / p
            if start.exists() and start.is_dir():
                for item in start.rglob("*"):
                    if item.is_file():
                        paths.add(item.resolve())

    return paths


def validate_target_path(source: Path, target: Path) -> None:
    """Ensure target does not overlap dangerously with source."""
    source = source.resolve()
    target = target.resolve()

    if target == source:
        raise ValueError(f"Target path cannot be the source repository itself: {target}")

    try:
        target.relative_to(source)
        target_inside = True
    except ValueError:
        target_inside = False

    if target_inside:
        raise ValueError(f"Target path cannot be inside the source repository: {target}")

    try:
        source.relative_to(target)
        source_inside = True
    except ValueError:
        source_inside = False

    if source_inside:
        raise ValueError(f"Target path cannot be a parent of the source repository: {target}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:  # noqa: D401
    parser = argparse.ArgumentParser(description="Export StataFlow to open-source mirror.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying them.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--target-root", default="", help="Path to target repo (default: ../StataFlow_open_source).")
    args = parser.parse_args()

    root = repo_root()
    manifest_path = root / "scripts" / "release" / "open_source_manifest.yml"
    manifest = load_manifest(manifest_path)

    if args.target_root:
        target = Path(args.target_root).resolve()
    else:
        target = root.parent / "StataFlow_open_source"

    validate_target_path(root, target)

    print(f"Source : {root}")
    print(f"Target : {target}")
    print(f"Manifest: {manifest_path}")
    print()

    source_paths = collect_source_paths(root, manifest)
    blacklist_patterns = manifest.get("blacklist", {}).get("patterns", [])

    # Apply blacklist
    filtered: list[Path] = []
    for p in source_paths:
        rel = str(p.relative_to(root)).replace("\\", "/")
        if not is_blacklisted(rel, blacklist_patterns):
            filtered.append(p)

    filtered.sort()

    if not target.exists():
        if args.dry_run:
            print(f"[DRY-RUN] Would create target directory: {target}")
        else:
            target.mkdir(parents=True, exist_ok=True)

    target_files_set: set[Path] = set()
    copy_count = 0
    skip_count = 0
    copy_size = 0

    for src in filtered:
        rel = src.relative_to(root)
        dst = target / rel
        target_files_set.add(dst.resolve())

        if not args.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)

        needs_copy = True
        if dst.exists():
            if sha256_file(src) == sha256_file(dst):
                needs_copy = False

        if needs_copy:
            if args.dry_run:
                print(f"[DRY-RUN] Would copy: {rel}")
            else:
                shutil.copy2(src, dst)
            copy_count += 1
            copy_size += src.stat().st_size
        else:
            skip_count += 1

    # Remove orphaned files in target
    remove_count = 0
    if target.exists():
        for item in target.rglob("*"):
            if not item.is_file():
                continue
            resolved = item.resolve()
            if resolved not in target_files_set:
                rel = str(resolved.relative_to(target)).replace("\\", "/")
                if rel.startswith(".git/") or rel == ".git":
                    continue
                if args.dry_run:
                    print(f"[DRY-RUN] Would remove orphaned: {rel}")
                else:
                    item.unlink()
                remove_count += 1

        # Remove empty directories
        for item in sorted(target.rglob("*"), key=lambda x: len(str(x)), reverse=True):
            if item.is_dir() and not any(item.iterdir()):
                rel = str(item.relative_to(target)).replace("\\", "/")
                if rel.startswith(".git"):
                    continue
                if args.dry_run:
                    print(f"[DRY-RUN] Would remove empty dir: {rel}")
                else:
                    item.rmdir()

    print()
    print("Export complete.")
    print(f"  Copied / updated : {copy_count} files ({copy_size:,} bytes)")
    print(f"  Unchanged        : {skip_count} files")
    print(f"  Removed orphaned : {remove_count} files")
    if args.dry_run:
        print("  (Dry-run mode: no changes were made)")

    return 0


if __name__ == "__main__":
    sys.exit(main())

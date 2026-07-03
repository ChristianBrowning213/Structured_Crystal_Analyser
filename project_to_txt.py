#!/usr/bin/env python3
from __future__ import annotations  # ← must be here (first statement)

import argparse
import io
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


DEFAULT_EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", ".venv",
    "__pycache__", "node_modules", "dist", "build", ".cache",
    ".mypy_cache", ".pytest_cache", ".next", ".turbo", ".parcel-cache"
}
DEFAULT_EXCLUDED_EXTS = {
    # archives & binaries
    ".zip", ".gz", ".bz2", ".xz", ".7z", ".rar", ".tar",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".dat", ".lock",
    # media
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".mp4", ".mov", ".avi", ".mkv", ".mp3", ".wav", ".flac",
    # docs likely huge or non-text
    ".pdf", ".psd", ".ai"
}
DEFAULT_EXCLUDED_FILES = {
    # huge / noisy lock or cache files (still text, but not helpful)
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
    "poetry.lock", "pipfile.lock", ".DS_Store", "Thumbs.db"
}

LANG_BY_EXT = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".tsx": "tsx", ".jsx": "jsx", ".json": "json", ".yml": "yaml",
    ".yaml": "yaml", ".md": "markdown", ".toml": "toml",
    ".ini": "", ".cfg": "", ".conf": "", ".txt": "",
    ".html": "html", ".css": "css", ".scss": "scss", ".sass": "sass",
    ".sh": "bash", ".ps1": "powershell", ".sql": "sql", ".xml": "xml",
    ".java": "java", ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp",
    ".rs": "rust", ".go": "go", ".rb": "ruby", ".php": "php",
    ".ipynb": "json"
}


def looks_binary(sample: bytes) -> bool:
    if b"\x00" in sample:
        return True
    # Heuristic: if >30% bytes are non-text-ish, treat as binary
    text_bytes = b"\t\n\r\f\b" + bytes(range(32, 127))
    if not sample:
        return False
    nontext = sum(ch not in text_bytes for ch in sample)
    return (nontext / len(sample)) > 0.30


def read_text_file(path: Path, max_bytes: int) -> Optional[str]:
    try:
        with path.open("rb") as f:
            sample = f.read(min(max_bytes, 4096))
            if looks_binary(sample):
                return None
        with path.open("rb") as f:
            data = f.read(max_bytes)
        text = data.decode("utf-8", errors="replace")
        return text.replace("\r\n", "\n").replace("\r", "\n")
    except Exception:
        return None


def is_hidden(p: Path) -> bool:
    # Treat names starting with '.' as hidden (works cross-platform)
    return any(part.startswith(".") and part not in {".", ".."} for part in p.parts)


# ----------------------------
# .gitignore support (lightweight)
# ----------------------------

@dataclass(frozen=True)
class GitIgnoreRule:
    base: Path         # directory containing the .gitignore file
    pattern: str       # normalized pattern
    negated: bool      # True if pattern starts with !
    dir_only: bool     # True if pattern ends with /


def _parse_gitignore_file(gitignore_path: Path) -> list[GitIgnoreRule]:
    rules: list[GitIgnoreRule] = []
    base = gitignore_path.parent

    try:
        raw = gitignore_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return rules

    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue

        negated = s.startswith("!")
        if negated:
            s = s[1:].strip()
            if not s:
                continue

        # Minimal support for escaping leading # or !
        if s.startswith(r"\#") or s.startswith(r"\!"):
            s = s[1:]

        dir_only = s.endswith("/")
        if dir_only:
            s = s[:-1].strip()
            if not s:
                continue

        # Normalize separators for Path.match
        s = s.replace("\\", "/")

        rules.append(GitIgnoreRule(base=base, pattern=s, negated=negated, dir_only=dir_only))

    return rules


def _rule_matches(rule: GitIgnoreRule, target_abs: Path, is_dir: bool) -> bool:
    """
    Good-enough .gitignore matcher:
      - patterns without '/' match basename anywhere
      - patterns with '/' are path patterns relative to the .gitignore base
        * if not anchored (no leading '/'), they can match anywhere => also try '**/pat'
      - trailing '/' (dir_only) already handled at caller
      - negation handled in is_ignored_by_gitignore (last match wins)
    """
    if rule.dir_only and not is_dir:
        return False

    try:
        rel_to_base = target_abs.relative_to(rule.base)
    except Exception:
        return False

    rel_posix = rel_to_base.as_posix()
    pat = rule.pattern

    # Path pattern
    if "/" in pat:
        anchored = pat.startswith("/")
        pat2 = pat.lstrip("/") if anchored else pat

        # direct match
        if Path(rel_posix).match(pat2) or rel_posix == pat2:
            return True

        if anchored:
            return False

        # non-anchored path patterns can match anywhere under base (key fix)
        if Path(rel_posix).match(f"**/{pat2}"):
            return True

        # small helper for non-glob literal patterns
        if not any(ch in pat2 for ch in "*?[]"):
            if rel_posix.endswith("/" + pat2):
                return True

        return False

    # Basename pattern
    return Path(target_abs.name).match(pat)


def is_ignored_by_gitignore(
    root: Path,
    target_abs: Path,
    is_dir: bool,
    rules_by_dir: dict[Path, list[GitIgnoreRule]],
) -> bool:
    """
    Apply .gitignore from root -> target parent directory.
    Last match wins; negation un-ignores.
    """
    context_dir = target_abs if is_dir else target_abs.parent
    if root != context_dir and root not in context_dir.parents:
        return False

    chain: list[Path] = []
    cur = context_dir
    while True:
        chain.append(cur)
        if cur == root:
            break
        cur = cur.parent
    chain.reverse()

    ignored = False
    for d in chain:
        rules = rules_by_dir.get(d)
        if not rules:
            continue
        for r in rules:
            if _rule_matches(r, target_abs, is_dir):
                ignored = not r.negated

    return ignored


def ensure_gitignore_loaded_for_dir(
    dirpath: Path,
    rules_by_dir: dict[Path, list[GitIgnoreRule]],
    cache: dict[Path, list[GitIgnoreRule]],
) -> None:
    """
    If dirpath/.gitignore exists, parse once and attach rules to that dir.
    """
    gi = dirpath / ".gitignore"
    if gi.exists() and gi.is_file() and gi not in cache:
        cache[gi] = _parse_gitignore_file(gi)
        rules_by_dir[dirpath] = cache[gi]


# ----------------------------
# Skip logic
# ----------------------------

def should_skip_file(p: Path, args, rel: Path, root: Path, rules_by_dir: dict[Path, list[GitIgnoreRule]]) -> bool:
    name = p.name

    if not args.include_dotfiles and (name.startswith(".") or is_hidden(rel)):
        return True

    # .gitignore
    if args.use_gitignore and is_ignored_by_gitignore(
        root=root,
        target_abs=p,
        is_dir=False,
        rules_by_dir=rules_by_dir,
    ):
        return True

    if name in args.exclude_files or name in DEFAULT_EXCLUDED_FILES:
        return True

    ext = p.suffix.lower()
    if ext in DEFAULT_EXCLUDED_EXTS or ext in args.exclude_exts:
        return True
    if args.include_exts and ext not in args.include_exts:
        return True

    try:
        size = p.stat().st_size
        if size > args.max_size_mb * 1024 * 1024:
            return True
    except Exception:
        return True

    return False


def should_skip_dir(dirpath: Path, args, rel: Path, root: Path, rules_by_dir: dict[Path, list[GitIgnoreRule]]) -> bool:
    name = dirpath.name

    if not args.include_dotfiles and (name.startswith(".") or is_hidden(rel)):
        return True

    # .gitignore
    if args.use_gitignore and is_ignored_by_gitignore(
        root=root,
        target_abs=dirpath,
        is_dir=True,
        rules_by_dir=rules_by_dir,
    ):
        return True

    if name in DEFAULT_EXCLUDED_DIRS or name in args.exclude_dirs:
        return True

    return False


def main():
    ap = argparse.ArgumentParser(
        description="Concatenate a project’s text source into one TXT for agent context."
    )
    ap.add_argument("root", help="Project root directory.")
    ap.add_argument(
        "-o", "--output", default="project_context.txt",
        help="Output TXT path (default: project_context.txt)"
    )
    ap.add_argument(
        "--max-size-mb", type=int, default=2,
        help="Skip files larger than this many MB (default: 2)"
    )
    ap.add_argument(
        "--include-dotfiles", action="store_true",
        help="Include dotfiles and hidden paths (default: skip)"
    )
    ap.add_argument(
        "--include-exts", default="",
        help="Comma-separated whitelist of extensions (e.g., .py,.md)"
    )
    ap.add_argument(
        "--exclude-exts", default="",
        help="Comma-separated extra excluded extensions (e.g., .log,.csv)"
    )
    ap.add_argument(
        "--exclude-dirs", default="",
        help="Comma-separated extra excluded dir names (exact match)"
    )
    ap.add_argument(
        "--exclude-files", default="",
        help="Comma-separated extra excluded file names (exact match)"
    )
    ap.add_argument(
        "--no-fences", action="store_true",
        help="Do not wrap contents in Markdown code fences."
    )
    ap.add_argument(
        "--no-gitignore", action="store_true",
        help="Do NOT read .gitignore files (default: use them)."
    )

    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"Error: {root} is not a directory.", file=sys.stderr)
        sys.exit(1)

    # Parse lists
    args.include_exts = {e.strip().lower() for e in args.include_exts.split(",") if e.strip()} if args.include_exts else set()
    args.exclude_exts = {e.strip().lower() for e in args.exclude_exts.split(",") if e.strip()} if args.exclude_exts else set()
    args.exclude_dirs = {d.strip() for d in args.exclude_dirs.split(",") if d.strip()} if args.exclude_dirs else set()
    args.exclude_files = {f.strip() for f in args.exclude_files.split(",") if f.strip()} if args.exclude_files else set()

    args.use_gitignore = not args.no_gitignore

    included_files: list[str] = []
    skipped = {"dir": 0, "hidden": 0, "size": 0, "binary": 0, "ext": 0, "other": 0, "gitignore": 0}

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # gitignore caches
    gitignore_cache: dict[Path, list[GitIgnoreRule]] = {}
    rules_by_dir: dict[Path, list[GitIgnoreRule]] = {}

    # load root .gitignore if present
    ensure_gitignore_loaded_for_dir(root, rules_by_dir, gitignore_cache)

    with io.open(out_path, "w", encoding="utf-8", newline="\n") as out:
        # Header / manifest preface
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        out.write("# PROJECT CONTEXT DUMP\n")
        out.write(f"# Root: {root}\n# Generated: {ts}\n")
        out.write("# Notes: Hidden paths and common junk/binaries are skipped. Sizes > max-size are skipped.\n")
        out.write("# Notes: .gitignore rules are applied (unless --no-gitignore).\n")
        out.write("#\n# Included files will follow with clear section headers.\n\n")

        # Walk
        for dirpath, dirnames, filenames in os.walk(root):
            dirpath = Path(dirpath)
            rel_dir = dirpath.relative_to(root)

            # If this directory has a .gitignore, load it once
            if args.use_gitignore:
                ensure_gitignore_loaded_for_dir(dirpath, rules_by_dir, gitignore_cache)

            # Filter directories in-place (os.walk respects modifications)
            keep_dirs = []
            for d in dirnames:
                dpath = dirpath / d
                rel = rel_dir / d

                if args.use_gitignore and is_ignored_by_gitignore(root, dpath, True, rules_by_dir):
                    skipped["gitignore"] += 1
                    continue

                if should_skip_dir(dpath, args, rel, root, rules_by_dir):
                    skipped["dir"] += 1
                    continue

                keep_dirs.append(d)
            dirnames[:] = keep_dirs

            # Files
            for fn in filenames:
                fpath = dirpath / fn
                rel = fpath.relative_to(root)

                if args.use_gitignore and is_ignored_by_gitignore(root, fpath, False, rules_by_dir):
                    skipped["gitignore"] += 1
                    continue

                if should_skip_file(fpath, args, rel, root, rules_by_dir):
                    # heuristic reason counting (best-effort)
                    name = fpath.name
                    if not args.include_dotfiles and (name.startswith(".") or is_hidden(rel)):
                        skipped["hidden"] += 1
                    elif fpath.suffix.lower() in DEFAULT_EXCLUDED_EXTS or fpath.suffix.lower() in args.exclude_exts:
                        skipped["ext"] += 1
                    else:
                        try:
                            if fpath.stat().st_size > args.max_size_mb * 1024 * 1024:
                                skipped["size"] += 1
                            else:
                                skipped["other"] += 1
                        except Exception:
                            skipped["other"] += 1
                    continue

                # Read and binary check
                with fpath.open("rb") as fb:
                    sample = fb.read(4096)
                if looks_binary(sample):
                    skipped["binary"] += 1
                    continue

                text = read_text_file(fpath, max_bytes=args.max_size_mb * 1024 * 1024)
                if text is None:
                    skipped["other"] += 1
                    continue

                included_files.append(str(rel))

                # Write section
                lang = LANG_BY_EXT.get(fpath.suffix.lower(), "")
                out.write("\n\n" + "=" * 80 + "\n")
                out.write(f"=== FILE: {rel} ===\n")
                out.write("=" * 80 + "\n\n")
                if args.no_fences:
                    out.write(text)
                else:
                    fence = lang if lang is not None else ""
                    out.write(f"```{fence}\n{text}\n```\n")

        # Manifest footer
        out.write("\n\n" + "#" * 80 + "\n")
        out.write("# MANIFEST\n")
        out.write("# Included files:\n")
        for p in included_files:
            out.write(f"#  - {p}\n")
        out.write("#\n# Skips summary:\n")
        for k, v in skipped.items():
            out.write(f"#  {k}: {v}\n")
        out.write("# END\n")

    print(f"Done. Wrote: {out_path}")
    print(f"Included files: {len(included_files)} | Skips: {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

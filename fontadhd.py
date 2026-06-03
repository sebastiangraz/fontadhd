#!/usr/bin/env python3
"""Generic font-folder organizer. Composable ops, configurable order."""

from pathlib import Path
import argparse
import re
import shutil
import sys


def normalize_name(name, strip="", lowercase=True, space_to_hyphen=True):
    if strip:
        name = name.replace(strip, "").strip()
    if lowercase:
        name = name.lower()
    if space_to_hyphen:
        name = re.sub(r"\s+", "-", name)
    return name


def rename_folders(root, strip="", lowercase=True, space_to_hyphen=True, **_):
    root = Path(root)
    for child in list(root.iterdir()):
        if not child.is_dir():
            continue
        new = normalize_name(child.name, strip, lowercase, space_to_hyphen)
        if new != child.name:
            child.rename(root / new)


def flatten_by_extension(root, extensions=("otf", "ttf"), recursive=True, **_):
    root = Path(root)
    if not root.exists():
        return
    exts = {e.lower().lstrip(".") for e in extensions}
    walker = root.rglob("*") if recursive else root.iterdir()
    for path in list(walker):
        if not path.is_file():
            continue
        if path.suffix.lower().lstrip(".") not in exts:
            continue
        # Flatten into the immediate child folder (the "family" root), not the
        # script target — preserves family grouping while collapsing weights.
        rel = path.relative_to(root)
        if len(rel.parts) < 2:
            continue
        family_root = root / rel.parts[0]
        target = family_root / path.name
        if path.resolve() == target.resolve() or target.exists():
            continue
        shutil.move(str(path), str(target))


def consolidate_families(root, separator="-", standalone_name="regular", **_):
    root = Path(root)
    if not root.exists():
        return
    names = sorted(p.name for p in root.iterdir() if p.is_dir())

    def prefixes(name):
        tokens = name.split(separator)
        return [separator.join(tokens[:i]) for i in range(1, len(tokens) + 1)]

    candidates = {}
    for name in names:
        for p in prefixes(name):
            candidates.setdefault(p, set()).add(name)
    candidates = {p: m for p, m in candidates.items() if len(m) >= 2}

    used = set()
    chosen = []
    for prefix in sorted(candidates, key=lambda p: (-len(p.split(separator)), -len(candidates[p]), p)):
        members = candidates[prefix] - used
        if len(members) < 2:
            continue
        chosen.append((prefix, members))
        used.update(members)

    for prefix, members in chosen:
        parent = root / prefix
        standalone_src = None
        if prefix in members:
            standalone_src = root / f".__tmp_consolidate_{prefix}"
            (root / prefix).rename(standalone_src)
            members = members - {prefix}
        parent.mkdir(exist_ok=True)
        for member in sorted(members):
            src = root / member
            if not src.exists():
                continue
            variant = member[len(prefix) + len(separator):]
            dest = parent / variant
            if dest.exists():
                continue
            shutil.move(str(src), str(dest))
        if standalone_src is not None:
            dest = parent / standalone_name
            i = 1
            while dest.exists():
                dest = parent / f"{standalone_name}-{i}"
                i += 1
            shutil.move(str(standalone_src), str(dest))


def remove_empty_dirs(root, **_):
    root = Path(root)
    for path in sorted(root.rglob("*"), key=lambda p: -len(p.parts)):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


OPS = {
    "rename": rename_folders,
    "flatten": flatten_by_extension,
    "consolidate": consolidate_families,
    "clean": remove_empty_dirs,
}

DEFAULT_ORDER = ["rename", "flatten", "consolidate", "clean"]


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("target", nargs="?", default=".", help="Folder to organize (default: cwd)")
    p.add_argument("--ops", help=f"Comma-separated ops in order. Available: {','.join(OPS)}. Default: {','.join(DEFAULT_ORDER)}")
    p.add_argument("--strip", default="", help="Substring to remove from folder names, anywhere it appears (e.g. 'EK ')")
    p.add_argument("--no-lowercase", action="store_true")
    p.add_argument("--no-hyphenate", action="store_true")
    p.add_argument("--extensions", default="otf,ttf", help="Comma-separated file extensions to flatten")
    p.add_argument("--no-recursive", action="store_true")
    p.add_argument("--separator", default="-", help="Token separator used to detect shared family prefixes (default: '-')")
    p.add_argument("--standalone-name", default="regular", help="Name used inside a family folder for a standalone variant (default: 'regular')")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    target = Path(args.target).resolve()
    ops = [o.strip() for o in args.ops.split(",")] if args.ops else DEFAULT_ORDER

    unknown = [o for o in ops if o not in OPS]
    if unknown:
        sys.exit(f"Unknown op(s): {', '.join(unknown)}. Available: {', '.join(OPS)}")

    kwargs = dict(
        strip=args.strip,
        lowercase=not args.no_lowercase,
        space_to_hyphen=not args.no_hyphenate,
        extensions=[e.strip() for e in args.extensions.split(",") if e.strip()],
        recursive=not args.no_recursive,
        separator=args.separator,
        standalone_name=args.standalone_name,
    )

    for op in ops:
        OPS[op](target, **kwargs)
    print(f"Done: {target} ({' -> '.join(ops)})")


if __name__ == "__main__":
    main()

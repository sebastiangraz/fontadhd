#!/usr/bin/env python3
"""Generic font-folder organizer. Composable ops, configurable order."""

from pathlib import Path
import argparse
import re
import shutil
import sys


def normalize_name(name, strip_prefix="", lowercase=True, space_to_hyphen=True):
    if strip_prefix and name.startswith(strip_prefix):
        name = name[len(strip_prefix):].lstrip()
    if lowercase:
        name = name.lower()
    if space_to_hyphen:
        name = re.sub(r"\s+", "-", name)
    return name


def rename_folders(root, strip_prefix="", lowercase=True, space_to_hyphen=True, **_):
    root = Path(root)
    for child in list(root.iterdir()):
        if not child.is_dir():
            continue
        new = normalize_name(child.name, strip_prefix, lowercase, space_to_hyphen)
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


def remove_empty_dirs(root, **_):
    root = Path(root)
    for path in sorted(root.rglob("*"), key=lambda p: -len(p.parts)):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


OPS = {
    "rename": rename_folders,
    "flatten": flatten_by_extension,
    "clean": remove_empty_dirs,
}

DEFAULT_ORDER = ["rename", "flatten", "clean"]


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("target", nargs="?", default=".", help="Folder to organize (default: cwd)")
    p.add_argument("--ops", help=f"Comma-separated ops in order. Available: {','.join(OPS)}. Default: {','.join(DEFAULT_ORDER)}")
    p.add_argument("--strip-prefix", default="", help="Prefix to remove from folder names (e.g. 'EK ')")
    p.add_argument("--no-lowercase", action="store_true")
    p.add_argument("--no-hyphenate", action="store_true")
    p.add_argument("--extensions", default="otf,ttf", help="Comma-separated file extensions to flatten")
    p.add_argument("--no-recursive", action="store_true")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    target = Path(args.target).resolve()
    ops = [o.strip() for o in args.ops.split(",")] if args.ops else DEFAULT_ORDER

    unknown = [o for o in ops if o not in OPS]
    if unknown:
        sys.exit(f"Unknown op(s): {', '.join(unknown)}. Available: {', '.join(OPS)}")

    kwargs = dict(
        strip_prefix=args.strip_prefix,
        lowercase=not args.no_lowercase,
        space_to_hyphen=not args.no_hyphenate,
        extensions=[e.strip() for e in args.extensions.split(",") if e.strip()],
        recursive=not args.no_recursive,
    )

    for op in ops:
        OPS[op](target, **kwargs)
    print(f"Done: {target} ({' -> '.join(ops)})")


if __name__ == "__main__":
    main()

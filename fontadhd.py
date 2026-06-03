#!/usr/bin/env python3
"""Generic font-folder organizer. Composable ops, configurable order."""

from pathlib import Path
import argparse
import os
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


def prune_files(root, prune=(), **_):
    root = Path(root)
    if not root.exists() or not prune:
        return
    delete_exts = {e.lower().lstrip(".") for e in prune}

    matches = {ext: [] for ext in delete_exts}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        ext = path.suffix.lower().lstrip(".")
        if ext in delete_exts:
            matches[ext].append(path)

    nonzero = {ext: paths for ext, paths in matches.items() if paths}
    if not nonzero:
        print("prune: no matching files found.")
        return

    summary = ", ".join(
        f"{len(paths)} {ext} file{'s' if len(paths) != 1 else ''}"
        for ext, paths in nonzero.items()
    )
    try:
        answer = input(f"Are you sure you want to delete {summary}? [y/N]: ").strip().lower()
    except EOFError:
        print("prune: aborted (no interactive stdin).")
        return
    if answer != "y":
        print("prune: aborted.")
        return

    for paths in nonzero.values():
        for path in paths:
            path.unlink()


FONT_EXTS = {"otf", "ttf", "otc", "ttc"}


def install_fonts(root):
    root = Path(root)
    if not root.exists():
        print(f"install: target does not exist: {root}")
        return
    fonts = sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower().lstrip(".") in FONT_EXTS
    )
    if not fonts:
        print("install: no font files found.")
        return

    if sys.platform == "darwin":
        dest = Path.home() / "Library" / "Fonts"
    elif sys.platform == "win32":
        dest = Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Windows" / "Fonts"
    else:
        print(f"install: unsupported platform '{sys.platform}'. Only macOS and Windows are supported.")
        return

    try:
        answer = input(f"Install {len(fonts)} font file(s) to {dest}? [y/N]: ").strip().lower()
    except EOFError:
        print("install: aborted (no interactive stdin).")
        return
    if answer != "y":
        print("install: aborted.")
        return

    dest.mkdir(parents=True, exist_ok=True)
    if sys.platform == "darwin":
        installed, skipped = _install_macos(fonts, dest)
    else:
        installed, skipped = _install_windows(fonts, dest)
    print(f"install: copied {installed}, skipped {skipped} (already present).")


def _install_macos(fonts, dest):
    installed = skipped = 0
    for src in fonts:
        target = dest / src.name
        if target.exists():
            skipped += 1
            continue
        shutil.copy2(str(src), str(target))
        installed += 1
    return installed, skipped


def _install_windows(fonts, dest):
    import winreg
    import ctypes

    suffix = {"ttf": " (TrueType)", "otf": " (OpenType)", "ttc": " (TrueType)", "otc": " (OpenType)"}
    key_path = r"Software\Microsoft\Windows NT\CurrentVersion\Fonts"
    installed = skipped = 0
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
        for src in fonts:
            target = dest / src.name
            if target.exists():
                skipped += 1
                continue
            shutil.copy2(str(src), str(target))
            ext = src.suffix.lower().lstrip(".")
            value_name = src.stem + suffix.get(ext, "")
            winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, str(target))
            installed += 1
    # Notify running apps so they pick up new fonts without restart.
    ctypes.windll.user32.SendMessageW(0xFFFF, 0x001D, 0, 0)
    return installed, skipped


def remove_empty_dirs(root, **_):
    root = Path(root)
    for path in sorted(root.rglob("*"), key=lambda p: -len(p.parts)):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


OPS = {
    "rename": rename_folders,
    "flatten": flatten_by_extension,
    "consolidate": consolidate_families,
    "prune": prune_files,
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
    p.add_argument("--prune", default="", help="Comma-separated extensions to DELETE when running the 'prune' op (e.g. 'ttf,woff,woff2'). Prompts for confirmation before deleting.")
    p.add_argument("--install-all", action="store_true", help="Recursively install all font files under the target into the user's font directory (macOS/Windows). Skips the default op pipeline unless --ops is also given.")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    target = Path(args.target).resolve()
    if args.ops:
        ops = [o.strip() for o in args.ops.split(",")]
    elif args.install_all:
        ops = []
    else:
        ops = DEFAULT_ORDER

    unknown = [o for o in ops if o not in OPS]
    if unknown:
        sys.exit(f"Unknown op(s): {', '.join(unknown)}. Available: {', '.join(OPS)}")

    prune_exts = [e.strip() for e in args.prune.split(",") if e.strip()]
    if "prune" in ops and not prune_exts:
        sys.exit("Error: 'prune' op requires --prune with at least one extension to delete (e.g. --prune ttf,woff2)")

    kwargs = dict(
        strip=args.strip,
        lowercase=not args.no_lowercase,
        space_to_hyphen=not args.no_hyphenate,
        extensions=[e.strip() for e in args.extensions.split(",") if e.strip()],
        recursive=not args.no_recursive,
        separator=args.separator,
        standalone_name=args.standalone_name,
        prune=prune_exts,
    )

    for op in ops:
        OPS[op](target, **kwargs)
    if args.install_all:
        install_fonts(target)
    summary = " -> ".join(ops + (["install"] if args.install_all else []))
    print(f"Done: {target} ({summary})" if summary else f"Done: {target}")


if __name__ == "__main__":
    main()

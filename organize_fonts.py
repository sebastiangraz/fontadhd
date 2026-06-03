#!/usr/bin/env python3
"""Reusable font-folder organizer. Edit the recipe at the bottom per foundry."""

from pathlib import Path
import shutil
import re
import sys


def normalize_name(name, strip_prefix="", lowercase=True, space_to_hyphen=True):
    """Strip a prefix, lowercase, and convert whitespace runs to hyphens."""
    if strip_prefix and name.startswith(strip_prefix):
        name = name[len(strip_prefix):].lstrip()
    if lowercase:
        name = name.lower()
    if space_to_hyphen:
        name = re.sub(r"\s+", "-", name)
    return name


def rename_folders(root, **kwargs):
    """Apply normalize_name to every immediate child folder of root."""
    root = Path(root)
    for child in list(root.iterdir()):
        if not child.is_dir():
            continue
        new = normalize_name(child.name, **kwargs)
        if new != child.name:
            child.rename(root / new)


def consolidate_families(root, families):
    """Move sibling folders into a shared parent. families: {parent: {variant: source}}."""
    root = Path(root)
    for parent_name, variants in families.items():
        parent_target = root / parent_name
        local_variants = dict(variants)

        if parent_target.is_dir() and parent_name in local_variants.values():
            tmp = root / f".__tmp_{parent_name}"
            parent_target.rename(tmp)
            local_variants = {
                k: (tmp.name if v == parent_name else v)
                for k, v in local_variants.items()
            }

        parent_target.mkdir(exist_ok=True)
        for variant_name, source_name in local_variants.items():
            source = root / source_name
            if source.exists():
                shutil.move(str(source), str(parent_target / variant_name))


def flatten_by_extension(folder, extensions, recursive=True):
    """Move all files matching extensions to folder root, then drop empty subdirs."""
    folder = Path(folder)
    if not folder.exists():
        return
    exts = {e.lower().lstrip(".") for e in extensions}
    walker = folder.rglob("*") if recursive else folder.iterdir()
    for path in list(walker):
        if not path.is_file():
            continue
        if path.suffix.lower().lstrip(".") not in exts:
            continue
        target = folder / path.name
        if path.resolve() == target.resolve() or target.exists():
            continue
        shutil.move(str(path), str(target))
    remove_empty_dirs(folder)


def remove_empty_dirs(folder):
    """Recursively delete empty subdirectories under folder."""
    folder = Path(folder)
    for path in sorted(folder.rglob("*"), key=lambda p: -len(p.parts)):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


# ---------------------------------------------------------------------------
# Recipe — edit this section per foundry. Below reproduces the Erkin Karamemet
# trial fonts layout. Pass a target dir as argv[1] or default to script dir.
# ---------------------------------------------------------------------------

def run_erkin_karamemet(fonts_root):
    rename_folders(fonts_root, strip_prefix="EK ", lowercase=True, space_to_hyphen=True)

    consolidate_families(fonts_root, {
        "baumer": {
            "headline": "baumer-headline",
            "plus": "baumer-plus",
            "uniwidth": "baumer-uniwidth",
        },
        "modena": {
            "regular": "modena",
            "compressed": "modena-compressed",
            "condensed": "modena-condensed",
            "expanded": "modena-expanded",
            "extended": "modena-extended",
            "mono": "modena-mono",
            "plus": "modena-plus",
            "super-compressed": "modena-super-compressed",
        },
        "notice": {
            "classic": "notice-classic",
            "decor": "notice-decor",
            "sans": "notice-sans",
        },
        "roumald": {
            "regular": "roumald",
            "mono": "roumald-mono",
        },
    })

    for family in ["baumer", "modena", "notice", "roumald", "ultimo"]:
        flatten_by_extension(Path(fonts_root) / family, [".otf", ".ttf"])


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
    run_erkin_karamemet(target)
    print(f"Done: {target}")

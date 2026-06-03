# fontadhd

A small, generic script for tidying up messy font folders. It runs a short pipeline of file-system operations against a target directory — renaming folders, flattening nested font files, grouping related families, and removing empty leftovers.

The script makes no assumptions about specific foundries, families, or naming schemes. Behavior is controlled entirely through CLI flags.

## Install

Requires Python 3.8+. No dependencies beyond the standard library.

```bash
git clone <repo> fontadhd
cd fontadhd
```

## Usage

```bash
python fontadhd.py [target] [flags]
```

If `target` is omitted, the current working directory is used.

### Example

Given a folder like:

```
trial-fonts/
├── EK Baumer Headline/
│   └── Weights/
│       ├── EKBaumerHeadline-Regular.otf
│       └── EKBaumerHeadline-Bold.otf
└── EK Modena/
    └── OTF/
        └── EKModena-Regular.otf
```

Running:

```bash
python fontadhd.py trial-fonts --strip "EK "
```

produces:

```
trial-fonts/
├── baumer-headline/
│   ├── EKBaumerHeadline-Regular.otf
│   └── EKBaumerHeadline-Bold.otf
└── modena/
    └── EKModena-Regular.otf
```

## How it works

The script is built around five composable operations that run sequentially against the target directory.

| Op            | What it does                                                                                               |
| ------------- | ---------------------------------------------------------------------------------------------------------- |
| `rename`      | Normalizes each immediate child folder name (strip substring, lowercase, hyphenate).                       |
| `flatten`     | Walks each child folder and moves font files up to the child folder's root.                                |
| `consolidate` | Detects shared name prefixes between sibling folders and groups them under a single parent.                |
| `prune`       | Deletes any file whose extension is in `--prune`. Prompts for confirmation. Opt-in (not in default order). |
| `clean`       | Removes any empty directories left behind.                                                                 |

The default order is `rename → flatten → consolidate → clean`. `prune` is omitted from the default because it is destructive. You can override which ops run and in what order with `--ops`.

### Why this order

- `rename` runs first so subsequent steps work on normalized names.
- `flatten` runs before `consolidate` because it operates on the immediate children of the target. Once `consolidate` has nested families one level deeper (e.g. `modena-expanded/` becomes `modena/expanded/`), running `flatten` on the original target would collapse variants together. Flatten the loose files into their family folders first, then group families.
- `clean` runs last to sweep up the empty subdirectories left behind by `flatten` and `consolidate`.

### Pipeline behavior

- Ops always run against the same target directory.
- Each op is independent; flags only apply to the ops that consume them (e.g. `--extensions` is only used by `flatten`).
- Unknown op names cause the script to exit with an error before any changes are made.

## Flags

### Positional

| Argument | Default | Description                              |
| -------- | ------- | ---------------------------------------- |
| `target` | `.`     | Folder to organize. Treated as the root. |

### Pipeline control

| Flag    | Default                            | Description                                                               |
| ------- | ---------------------------------- | ------------------------------------------------------------------------- |
| `--ops` | `rename,flatten,consolidate,clean` | Comma-separated ops, executed in the order given. Use to skip or reorder. |

### `rename` options

| Flag             | Default | Description                                                                                                           |
| ---------------- | ------- | --------------------------------------------------------------------------------------------------------------------- |
| `--strip`        | `""`    | Substring removed from each folder name, anywhere it appears (e.g. `"EK "`, `" Trial"`). All occurrences are removed. |
| `--no-lowercase` | off     | Disable lowercasing of folder names.                                                                                  |
| `--no-hyphenate` | off     | Disable converting whitespace runs to single hyphens.                                                                 |

### `flatten` options

| Flag             | Default   | Description                                                                          |
| ---------------- | --------- | ------------------------------------------------------------------------------------ |
| `--extensions`   | `otf,ttf` | Comma-separated file extensions to flatten. Case-insensitive, leading dots optional. |
| `--no-recursive` | off       | Only look at direct children; do not recurse into nested folders.                    |

### `consolidate` options

| Flag                | Default   | Description                                                                                          |
| ------------------- | --------- | ---------------------------------------------------------------------------------------------------- |
| `--separator`       | `-`       | Token separator used to detect shared family prefixes. Match this to whatever `rename` produces.     |
| `--standalone-name` | `regular` | Name used inside the new parent for a standalone variant (e.g. `modena/` becomes `modena/regular/`). |

#### How consolidation works

For each immediate child folder, the name is split by `--separator` into tokens, and every leading-token prefix is treated as a candidate family name. Any prefix shared by two or more folders becomes a grouping. Longer (more specific) prefixes win when groupings overlap, so:

- `modena-expanded`, `modena-condensed` → `modena/{expanded, condensed}`
- `ek-modena-expanded`, `ek-modena-condensed`, `ek-baumer-headline`, `ek-baumer-plus` → `ek-modena/{expanded, condensed}` and `ek-baumer/{headline, plus}` (the `ek` prefix is shared by all four but loses to the more specific two-token prefixes)
- `roumald`, `roumald-mono` → `roumald/{regular, mono}` (the standalone is renamed to `--standalone-name`)

Single-pass. Sub-sub-families (`modena-super-compressed`, `modena-super-extended`) form a `modena-super/` sibling of `modena/` rather than nesting inside it. Re-run if you want deeper folding.

### `prune` options

| Flag      | Default | Description                                                                                                |
| --------- | ------- | ---------------------------------------------------------------------------------------------------------- |
| `--prune` | `""`    | Comma-separated extensions to **delete** (e.g. `ttf,woff,woff2`). **Required when `prune` is in `--ops`.** |

Safety behavior:

- If `prune` appears in `--ops` without `--prune` set, the script exits with an error before any op runs.
- Before deleting, `prune` prints a per-extension count (`Are you sure you want to delete 12 ttf files, 8 woff files, 8 woff2 files? [y/N]:`) and waits for `y`. Any other answer aborts.
- If no matching files exist, `prune` prints a message and returns without prompting.
- If stdin isn't interactive (piped, no TTY), `prune` aborts rather than auto-confirming.

### `clean` options

None. Always recursive, always removes only empty directories.

## Recipes

### Just rename

```bash
python fontadhd.py ./fonts --ops rename --strip "EK "
```

### Just flatten and clean

```bash
python fontadhd.py ./fonts --ops flatten,clean --extensions otf,ttf,woff2
```

### Skip consolidation

```bash
python fontadhd.py ./fonts --ops rename,flatten,clean
```

### Consolidate without renaming (raw names)

```bash
python fontadhd.py ./fonts --ops consolidate --separator " "
```

### Delete specific formats

Delete every `.ttf`, `.woff`, and `.woff2` file anywhere under the target (with confirmation prompt):

```bash
python fontadhd.py ./fonts --ops prune,clean --prune ttf,woff,woff2
```

`clean` is paired so any folders left empty by the deletions get removed too.

### Full pipeline with format pruning

```bash
python fontadhd.py ./fonts --ops rename,flatten,consolidate,prune,clean --strip "EK " --prune ttf,woff,woff2
```

### Flatten variant subfolders after consolidating

Run `flatten` a second time after `consolidate` to collapse the variant subfolders, leaving each family with just its font files:

```bash
python fontadhd.py ./fonts --ops rename,flatten,consolidate,flatten,clean
```

Before the second `flatten`:

```
modena/
├── regular/Modena-Regular.otf
├── expanded/Modena-Expanded.otf
└── condensed/Modena-Condensed.otf
```

After:

```
modena/
├── Modena-Regular.otf
├── Modena-Expanded.otf
└── Modena-Condensed.otf
```

### Include web font formats

```bash
python fontadhd.py ./fonts --extensions otf,ttf,woff,woff2
```

### Preserve original casing

```bash
python fontadhd.py ./fonts --no-lowercase --no-hyphenate
```

## Notes

- **Destructive.** All ops modify the file system in place. `prune` is the only one that deletes file contents (everything not in `--keep`). Run on a copy first if you're unsure.
- **Idempotent.** Re-running on an already-organized folder is a no-op (including `prune` once non-matching files are gone).
- **No collision overwrites.** `flatten` skips moves when a file of the same name already exists at the destination.
- **Why the name `fontadhd`** I have ADHD, I need order, I collect trial fonts like pokemans, but I need order, hence the name.

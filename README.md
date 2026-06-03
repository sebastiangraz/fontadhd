# fontadhd

A small, generic script for tidying up messy font folders. It runs a short pipeline of file-system operations against a target directory — renaming folders, flattening nested font files, and removing empty leftovers.

The script makes no assumptions about specific foundries, families, or naming schemes. Behavior is controlled entirely through CLI flags.

## Install

Requires Python 3.8+. No dependencies beyond the standard library.

```bash
git clone <repo> fontadhd
cd fontadhd
```

## Usage

```bash
python organize_fonts.py [target] [flags]
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
python organize_fonts.py trial-fonts --strip "EK "
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

The script is built around three composable operations that run sequentially against the target directory.

| Op        | What it does                                                                 |
| --------- | ---------------------------------------------------------------------------- |
| `rename`  | Normalizes each immediate child folder name (strip prefix, lowercase, hyphenate). |
| `flatten` | Walks each child folder and moves font files up to the child folder's root. |
| `clean`   | Removes any empty directories left behind.                                   |

The default order is `rename → flatten → clean`. You can override which ops run and in what order with `--ops`.

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

| Flag     | Default                  | Description                                                                |
| -------- | ------------------------ | -------------------------------------------------------------------------- |
| `--ops`  | `rename,flatten,clean`   | Comma-separated ops, executed in the order given. Use to skip or reorder. |

### `rename` options

| Flag              | Default | Description                                                |
| ----------------- | ------- | ---------------------------------------------------------- |
| `--strip`  | `""`    | Substring removed from each folder name, anywhere it appears (e.g. `"EK "`, `" Trial"`). All occurrences are removed. |
| `--no-lowercase`  | off     | Disable lowercasing of folder names.                       |
| `--no-hyphenate`  | off     | Disable converting whitespace runs to single hyphens.      |

### `flatten` options

| Flag              | Default   | Description                                                              |
| ----------------- | --------- | ------------------------------------------------------------------------ |
| `--extensions`    | `otf,ttf` | Comma-separated file extensions to flatten. Case-insensitive, leading dots optional. |
| `--no-recursive`  | off       | Only look at direct children; do not recurse into nested folders.        |

### `clean` options

None. Always recursive, always removes only empty directories.

## Recipes

### Just rename

```bash
python organize_fonts.py ./fonts --ops rename --strip "EK "
```

### Just flatten and clean

```bash
python organize_fonts.py ./fonts --ops flatten,clean --extensions otf,ttf,woff2
```

### Include web font formats

```bash
python organize_fonts.py ./fonts --extensions otf,ttf,woff,woff2
```

### Preserve original casing

```bash
python organize_fonts.py ./fonts --no-lowercase --no-hyphenate
```

## Notes

- **Destructive.** `rename`, `flatten`, and `clean` all modify the file system in place. Run on a copy first if you're unsure.
- **Idempotent.** Re-running on an already-organized folder is a no-op.
- **No collision overwrites.** `flatten` skips moves when a file of the same name already exists at the destination.

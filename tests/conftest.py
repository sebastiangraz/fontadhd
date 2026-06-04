from pathlib import Path

import pytest


def _make_tree(root, spec):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for name, value in spec.items():
        path = root / name
        if isinstance(value, dict):
            _make_tree(path, value)
        elif isinstance(value, list):
            path.mkdir(parents=True, exist_ok=True)
            for fname in value:
                (path / fname).touch()
        else:
            raise TypeError(
                f"make_tree spec for {name!r} must be dict or list, got {type(value).__name__}"
            )


def _snapshot(root):
    root = Path(root)
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))


@pytest.fixture
def make_tree():
    return _make_tree


@pytest.fixture
def snapshot():
    return _snapshot

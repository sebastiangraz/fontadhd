"""Tests for the GUI bridge (gui.Api).

These exercise the bridge logic only — no pywebview/window is needed, since the
webview import in gui.py is lazy and only pick_folder()/main() use it.
"""

import pytest

from gui import Api


def _names(tree):
    """Flatten a gui._snapshot tree into a set of 'a/b/c' paths (excludes root)."""
    out = set()

    def walk(node, prefix):
        for child in node.get("children", []):
            path = f"{prefix}/{child['name']}" if prefix else child["name"]
            out.add(path)
            if child["type"] == "dir":
                walk(child, path)

    walk(tree, "")
    return out


@pytest.fixture
def api():
    return Api()


def test_preview_leaves_original_untouched(api, tmp_path, make_tree, snapshot):
    make_tree(tmp_path, {
        "EK Modena Expanded": ["Modena-Expanded.otf"],
        "EK Modena Condensed": {"desktop": ["Modena-Condensed.otf"]},
    })
    before_disk = snapshot(tmp_path)

    res = api.preview(str(tmp_path), ["rename", "flatten", "consolidate", "clean"],
                      {"strip": "EK "})

    assert "error" not in res
    # The real folder on disk is byte-for-byte unchanged by a preview.
    assert snapshot(tmp_path) == before_disk
    # The previewed "after" reflects the organized result.
    after = _names(res["after"])
    assert "modena/expanded/Modena-Expanded.otf" in after
    assert "modena/condensed/Modena-Condensed.otf" in after


def test_preview_matches_apply(api, tmp_path, make_tree, snapshot):
    spec = {
        "EK Modena Expanded": ["Modena-Expanded.otf"],
        "EK Modena Condensed": {"web": ["Modena-Condensed.otf"]},
        "EK Other": ["Other.otf"],
    }
    ops = ["rename", "flatten", "consolidate", "clean"]
    opts = {"strip": "EK "}

    make_tree(tmp_path, spec)
    previewed = _names(api.preview(str(tmp_path), ops, opts)["after"])

    # Same input, applied for real, must produce the same tree the preview showed.
    res = api.apply(str(tmp_path), ops, opts)
    assert "error" not in res
    applied = _names(res["tree"])
    assert previewed == applied


def test_ops_order_matters(api, tmp_path, make_tree):
    # flatten-before-consolidate vs consolidate-before-flatten yield different trees.
    spec = {
        "modena-expanded": {"weights": ["Modena-Expanded.otf"]},
        "modena-condensed": {"weights": ["Modena-Condensed.otf"]},
    }

    make_tree(tmp_path / "a", spec)
    flat_first = _names(api.preview(str(tmp_path / "a"),
                                    ["flatten", "consolidate", "clean"], {})["after"])

    make_tree(tmp_path / "b", spec)
    cons_first = _names(api.preview(str(tmp_path / "b"),
                                    ["consolidate", "flatten", "clean"], {})["after"])

    assert flat_first != cons_first


def test_apply_prune_deletes_without_prompt(api, tmp_path, make_tree, monkeypatch):
    # assume_yes=True is injected by the bridge, so prune must not call input().
    def boom(*_a, **_k):
        raise AssertionError("input() should not be called from the GUI bridge")

    monkeypatch.setattr("builtins.input", boom)
    make_tree(tmp_path, {"fam": ["keep.otf", "drop.ttf"]})

    res = api.apply(str(tmp_path), ["prune"], {"prune": "ttf"})

    assert "error" not in res
    names = _names(res["tree"])
    assert "fam/keep.otf" in names
    assert "fam/drop.ttf" not in names


def test_unknown_op_is_reported(api, tmp_path, make_tree):
    make_tree(tmp_path, {"fam": ["a.otf"]})
    res = api.preview(str(tmp_path), ["rename", "bogus"], {})
    assert "error" in res
    assert "bogus" in res["error"]


def test_scan_rejects_non_folder(api, tmp_path):
    missing = tmp_path / "nope"
    res = api.scan(str(missing))
    assert "error" in res


def test_list_ops_shape(api):
    info = api.list_ops()
    assert info["default"] == ["rename", "flatten", "consolidate", "clean"]
    assert "prune" in info["available"]
    assert set(info["params"]) == set(info["available"])

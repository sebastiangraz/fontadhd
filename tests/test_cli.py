import pytest

from fontadhd import main


def test_default_pipeline_end_to_end(tmp_path, make_tree, snapshot):
    make_tree(tmp_path, {
        "EK Modena Expanded": ["Modena-Expanded.otf"],
        "EK Modena Condensed": {
            "desktop": ["Modena-Condensed.otf"],
            "web": ["Modena-Condensed.woff2"],
        },
        "EK Other": ["Other.otf"],
    })
    main([str(tmp_path), "--strip", "EK "])
    assert snapshot(tmp_path) == [
        "modena",
        "modena/condensed",
        "modena/condensed/Modena-Condensed.otf",
        "modena/condensed/web",
        "modena/condensed/web/Modena-Condensed.woff2",
        "modena/expanded",
        "modena/expanded/Modena-Expanded.otf",
        "other",
        "other/Other.otf",
    ]


def test_ops_override_runs_only_specified(tmp_path, make_tree):
    make_tree(tmp_path, {
        "EK Modena": ["Font.otf"],
    })
    main([str(tmp_path), "--ops", "rename,clean", "--strip", "EK "])
    # Only rename + clean ran; flatten and consolidate were skipped.
    assert (tmp_path / "modena" / "Font.otf").exists()


def test_ops_consolidate_alone_does_not_rename(tmp_path, make_tree):
    make_tree(tmp_path, {
        "Modena-Expanded": ["a.otf"],
        "Modena-Condensed": ["b.otf"],
    })
    main([str(tmp_path), "--ops", "consolidate"])
    # No rename happened, so casing is preserved and the family folder uses the matched prefix.
    assert (tmp_path / "Modena" / "Expanded" / "a.otf").exists()
    assert (tmp_path / "Modena" / "Condensed" / "b.otf").exists()


def test_prune_op_without_prune_list_exits(tmp_path):
    with pytest.raises(SystemExit):
        main([str(tmp_path), "--ops", "prune"])


def test_unknown_op_exits(tmp_path):
    with pytest.raises(SystemExit):
        main([str(tmp_path), "--ops", "definitely-not-an-op"])


def test_double_flatten_max_flat_workflow(tmp_path, make_tree, snapshot):
    # The 'max-flat' recipe: flatten before consolidate collapses variant
    # internals, then flatten after consolidate collapses the variant folders
    # themselves into a single family folder of loose font files.
    make_tree(tmp_path, {
        "EK Modena Expanded": {
            "desktop": ["Modena-Expanded.otf"],
        },
        "EK Modena Condensed": ["Modena-Condensed.otf"],
    })
    main([
        str(tmp_path),
        "--ops", "rename,flatten,consolidate,flatten,clean",
        "--strip", "EK ",
    ])
    assert snapshot(tmp_path) == [
        "modena",
        "modena/Modena-Condensed.otf",
        "modena/Modena-Expanded.otf",
    ]


def test_prune_via_cli(tmp_path, make_tree, monkeypatch):
    make_tree(tmp_path, {
        "modena": ["a.otf", "b.ttf", "c.woff2"],
    })
    monkeypatch.setattr("builtins.input", lambda _: "y")
    main([str(tmp_path), "--ops", "prune", "--prune", "ttf,woff2"])
    assert (tmp_path / "modena" / "a.otf").exists()
    assert not (tmp_path / "modena" / "b.ttf").exists()
    assert not (tmp_path / "modena" / "c.woff2").exists()

from fontadhd import flatten_by_extension


def test_nested_files_moved_to_family_root(tmp_path, make_tree, snapshot):
    make_tree(tmp_path, {
        "modena": {
            "desktop": ["Modena.otf"],
        },
    })
    flatten_by_extension(tmp_path)
    assert snapshot(tmp_path) == [
        "modena",
        "modena/Modena.otf",
        "modena/desktop",
    ]


def test_only_configured_extensions_moved(tmp_path, make_tree, snapshot):
    make_tree(tmp_path, {
        "modena": {
            "desktop": ["Modena.otf", "Modena.ttf"],
            "web": ["Modena.woff2"],
        },
    })
    flatten_by_extension(tmp_path, extensions=("otf",))
    assert snapshot(tmp_path) == [
        "modena",
        "modena/Modena.otf",
        "modena/desktop",
        "modena/desktop/Modena.ttf",
        "modena/web",
        "modena/web/Modena.woff2",
    ]


def test_file_already_at_family_root_is_noop(tmp_path, make_tree, snapshot):
    make_tree(tmp_path, {
        "modena": ["Modena.otf"],
    })
    flatten_by_extension(tmp_path)
    assert snapshot(tmp_path) == [
        "modena",
        "modena/Modena.otf",
    ]


def test_collision_at_family_root_preserves_both(tmp_path):
    (tmp_path / "modena").mkdir()
    (tmp_path / "modena" / "Modena.otf").touch()
    (tmp_path / "modena" / "desktop").mkdir()
    (tmp_path / "modena" / "desktop" / "Modena.otf").touch()
    flatten_by_extension(tmp_path)
    # Both copies preserved; the deeper one is not silently overwritten.
    assert (tmp_path / "modena" / "Modena.otf").exists()
    assert (tmp_path / "modena" / "desktop" / "Modena.otf").exists()


def test_non_recursive_skips_deep_files(tmp_path, make_tree):
    make_tree(tmp_path, {
        "modena": {
            "desktop": ["Modena.otf"],
        },
    })
    flatten_by_extension(tmp_path, recursive=False)
    assert (tmp_path / "modena" / "desktop" / "Modena.otf").exists()
    assert not (tmp_path / "modena" / "Modena.otf").exists()


def test_root_level_files_ignored(tmp_path):
    (tmp_path / "stray.otf").touch()
    flatten_by_extension(tmp_path)
    assert (tmp_path / "stray.otf").exists()


def test_multiple_variants_collapsed_under_each_family(tmp_path, make_tree, snapshot):
    make_tree(tmp_path, {
        "alpha": {
            "regular": ["Alpha.otf"],
            "bold": ["Alpha-Bold.otf"],
        },
        "beta": {
            "thin": ["Beta-Thin.otf"],
        },
    })
    flatten_by_extension(tmp_path)
    assert snapshot(tmp_path) == [
        "alpha",
        "alpha/Alpha-Bold.otf",
        "alpha/Alpha.otf",
        "alpha/bold",
        "alpha/regular",
        "beta",
        "beta/Beta-Thin.otf",
        "beta/thin",
    ]

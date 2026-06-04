from fontadhd import flatten


def test_nested_files_moved_to_family_root(tmp_path, make_tree, snapshot):
    make_tree(tmp_path, {
        "modena": {
            "desktop": ["Modena.otf"],
        },
    })
    flatten(tmp_path)
    assert snapshot(tmp_path) == [
        "modena",
        "modena/Modena.otf",
        "modena/desktop",
    ]


def test_all_known_font_formats_moved(tmp_path, make_tree, snapshot):
    # Flatten now moves any known font format (desktop + web), and leaves
    # non-font files alone.
    make_tree(tmp_path, {
        "modena": {
            "desktop": ["Modena.otf", "Modena.ttf", "Modena.otc"],
            "web": ["Modena.woff", "Modena.woff2", "Modena.eot"],
            "docs": ["README.txt", "license.pdf"],
        },
    })
    flatten(tmp_path)
    assert snapshot(tmp_path) == [
        "modena",
        "modena/Modena.eot",
        "modena/Modena.otc",
        "modena/Modena.otf",
        "modena/Modena.ttf",
        "modena/Modena.woff",
        "modena/Modena.woff2",
        "modena/desktop",
        "modena/docs",
        "modena/docs/README.txt",
        "modena/docs/license.pdf",
        "modena/web",
    ]


def test_file_already_at_family_root_is_noop(tmp_path, make_tree, snapshot):
    make_tree(tmp_path, {
        "modena": ["Modena.otf"],
    })
    flatten(tmp_path)
    assert snapshot(tmp_path) == [
        "modena",
        "modena/Modena.otf",
    ]


def test_collision_at_family_root_preserves_both(tmp_path):
    (tmp_path / "modena").mkdir()
    (tmp_path / "modena" / "Modena.otf").touch()
    (tmp_path / "modena" / "desktop").mkdir()
    (tmp_path / "modena" / "desktop" / "Modena.otf").touch()
    flatten(tmp_path)
    # Both copies preserved; the deeper one is not silently overwritten.
    assert (tmp_path / "modena" / "Modena.otf").exists()
    assert (tmp_path / "modena" / "desktop" / "Modena.otf").exists()


def test_non_recursive_skips_deep_files(tmp_path, make_tree):
    make_tree(tmp_path, {
        "modena": {
            "desktop": ["Modena.otf"],
        },
    })
    flatten(tmp_path, recursive=False)
    assert (tmp_path / "modena" / "desktop" / "Modena.otf").exists()
    assert not (tmp_path / "modena" / "Modena.otf").exists()


def test_root_level_files_ignored(tmp_path):
    (tmp_path / "stray.otf").touch()
    flatten(tmp_path)
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
    flatten(tmp_path)
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

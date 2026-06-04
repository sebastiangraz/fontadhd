from fontadhd import consolidate_families


def test_basic_two_variant_group(tmp_path, make_tree, snapshot):
    make_tree(tmp_path, {
        "modena-expanded": ["Modena-Exp.otf"],
        "modena-condensed": ["Modena-Cnd.otf"],
    })
    consolidate_families(tmp_path)
    assert snapshot(tmp_path) == [
        "modena",
        "modena/condensed",
        "modena/condensed/Modena-Cnd.otf",
        "modena/expanded",
        "modena/expanded/Modena-Exp.otf",
    ]


def test_shared_outer_prefix_picks_longest(tmp_path, make_tree, snapshot):
    # All three share 'ek-', but only modena variants share 'ek-modena'.
    # The longest matching prefix wins, leaving 'ek-other' untouched.
    make_tree(tmp_path, {
        "ek-modena-expanded": ["a.otf"],
        "ek-modena-condensed": ["b.otf"],
        "ek-other": ["c.otf"],
    })
    consolidate_families(tmp_path)
    assert snapshot(tmp_path) == [
        "ek-modena",
        "ek-modena/condensed",
        "ek-modena/condensed/b.otf",
        "ek-modena/expanded",
        "ek-modena/expanded/a.otf",
        "ek-other",
        "ek-other/c.otf",
    ]


def test_standalone_alongside_variants(tmp_path, make_tree, snapshot):
    # 'modena' exists as a sibling of 'modena-expanded' / 'modena-condensed'.
    # The standalone gets nested under the family as 'regular'.
    make_tree(tmp_path, {
        "modena": ["plain.otf"],
        "modena-expanded": ["exp.otf"],
        "modena-condensed": ["cnd.otf"],
    })
    consolidate_families(tmp_path)
    assert snapshot(tmp_path) == [
        "modena",
        "modena/condensed",
        "modena/condensed/cnd.otf",
        "modena/expanded",
        "modena/expanded/exp.otf",
        "modena/regular",
        "modena/regular/plain.otf",
    ]


def test_standalone_name_collision_falls_back_to_suffix(tmp_path, make_tree, snapshot):
    # 'modena-regular' becomes 'regular', so the standalone 'modena' has to
    # take a numeric-suffixed slot.
    make_tree(tmp_path, {
        "modena": ["plain.otf"],
        "modena-regular": ["regfont.otf"],
        "modena-expanded": ["exp.otf"],
    })
    consolidate_families(tmp_path)
    # Note: '-' (0x2D) sorts before '/' (0x2F), so 'modena/regular-1' and its
    # contents interleave before 'modena/regular/regfont.otf'.
    assert snapshot(tmp_path) == [
        "modena",
        "modena/expanded",
        "modena/expanded/exp.otf",
        "modena/regular",
        "modena/regular-1",
        "modena/regular-1/plain.otf",
        "modena/regular/regfont.otf",
    ]


def test_single_match_no_consolidation(tmp_path, make_tree, snapshot):
    make_tree(tmp_path, {
        "modena-expanded": ["a.otf"],
        "other-bold": ["b.otf"],
    })
    consolidate_families(tmp_path)
    assert snapshot(tmp_path) == [
        "modena-expanded",
        "modena-expanded/a.otf",
        "other-bold",
        "other-bold/b.otf",
    ]


def test_custom_separator_and_standalone_name(tmp_path, make_tree, snapshot):
    make_tree(tmp_path, {
        "modena_expanded": ["a.otf"],
        "modena_condensed": ["b.otf"],
        "modena": ["plain.otf"],
    })
    consolidate_families(tmp_path, separator="_", standalone_name="default")
    assert snapshot(tmp_path) == [
        "modena",
        "modena/condensed",
        "modena/condensed/b.otf",
        "modena/default",
        "modena/default/plain.otf",
        "modena/expanded",
        "modena/expanded/a.otf",
    ]


def test_empty_root_is_noop(tmp_path, snapshot):
    consolidate_families(tmp_path)
    assert snapshot(tmp_path) == []


def test_nonexistent_root_is_noop(tmp_path):
    # Should not raise.
    consolidate_families(tmp_path / "does-not-exist")

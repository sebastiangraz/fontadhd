from fontadhd import remove_empty_dirs


def test_empty_leaf_removed(tmp_path):
    (tmp_path / "empty").mkdir()
    remove_empty_dirs(tmp_path)
    assert not (tmp_path / "empty").exists()


def test_cascading_empty_chain_removed(tmp_path):
    (tmp_path / "a" / "b" / "c").mkdir(parents=True)
    remove_empty_dirs(tmp_path)
    assert not (tmp_path / "a").exists()


def test_non_empty_directory_preserved(tmp_path):
    (tmp_path / "modena").mkdir()
    (tmp_path / "modena" / "font.otf").touch()
    remove_empty_dirs(tmp_path)
    assert (tmp_path / "modena").is_dir()
    assert (tmp_path / "modena" / "font.otf").is_file()


def test_target_root_never_removed_when_empty(tmp_path):
    remove_empty_dirs(tmp_path)
    assert tmp_path.is_dir()


def test_mixed_tree(tmp_path):
    (tmp_path / "alpha").mkdir()
    (tmp_path / "beta").mkdir()
    (tmp_path / "beta" / "font.otf").touch()
    (tmp_path / "gamma" / "empty").mkdir(parents=True)
    remove_empty_dirs(tmp_path)
    assert not (tmp_path / "alpha").exists()
    assert (tmp_path / "beta").is_dir()
    assert (tmp_path / "beta" / "font.otf").exists()
    assert not (tmp_path / "gamma").exists()


def test_empties_below_non_empty_still_removed(tmp_path):
    # A non-empty parent should still get its empty children cleaned out.
    (tmp_path / "modena").mkdir()
    (tmp_path / "modena" / "font.otf").touch()
    (tmp_path / "modena" / "empty-sub").mkdir()
    remove_empty_dirs(tmp_path)
    assert (tmp_path / "modena" / "font.otf").exists()
    assert not (tmp_path / "modena" / "empty-sub").exists()

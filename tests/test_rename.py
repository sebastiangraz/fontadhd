from fontadhd import rename_folders


def test_strip_prefix_lowercase_and_hyphenate(tmp_path):
    (tmp_path / "EK Modena").mkdir()
    rename_folders(tmp_path, strip="EK ")
    assert (tmp_path / "modena").is_dir()
    assert not (tmp_path / "EK Modena").exists()


def test_strip_in_middle(tmp_path):
    (tmp_path / "Foo EK Bar").mkdir()
    rename_folders(tmp_path, strip="EK ")
    assert (tmp_path / "foo-bar").is_dir()


def test_files_at_root_untouched(tmp_path):
    (tmp_path / "Stray File.otf").touch()
    (tmp_path / "EK Modena").mkdir()
    rename_folders(tmp_path, strip="EK ")
    assert (tmp_path / "Stray File.otf").is_file()
    assert (tmp_path / "modena").is_dir()


def test_no_lowercase(tmp_path):
    (tmp_path / "EK Modena").mkdir()
    rename_folders(tmp_path, strip="EK ", lowercase=False)
    assert (tmp_path / "Modena").is_dir()


def test_no_hyphenate(tmp_path):
    (tmp_path / "EK Modena Pro").mkdir()
    rename_folders(tmp_path, strip="EK ", space_to_hyphen=False)
    assert (tmp_path / "modena pro").is_dir()


def test_no_strip_just_normalize(tmp_path):
    (tmp_path / "Modena Pro").mkdir()
    rename_folders(tmp_path)
    assert (tmp_path / "modena-pro").is_dir()


def test_only_immediate_children_renamed(tmp_path):
    # Nested folders are not touched.
    nested = tmp_path / "EK Modena" / "Sub Folder"
    nested.mkdir(parents=True)
    rename_folders(tmp_path, strip="EK ")
    assert (tmp_path / "modena").is_dir()
    # The nested folder keeps its original name.
    assert (tmp_path / "modena" / "Sub Folder").is_dir()

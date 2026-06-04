import pytest

from fontadhd import prune_files


def test_confirmation_y_deletes_only_matching(tmp_path, make_tree, monkeypatch):
    make_tree(tmp_path, {
        "modena": ["Modena.otf", "Modena.ttf", "Modena.woff2"],
        "other": ["Other.otf", "Other.ttf"],
    })
    monkeypatch.setattr("builtins.input", lambda _: "y")
    prune_files(tmp_path, prune=("ttf", "woff2"))
    assert (tmp_path / "modena" / "Modena.otf").exists()
    assert not (tmp_path / "modena" / "Modena.ttf").exists()
    assert not (tmp_path / "modena" / "Modena.woff2").exists()
    assert (tmp_path / "other" / "Other.otf").exists()
    assert not (tmp_path / "other" / "Other.ttf").exists()


def test_confirmation_n_keeps_everything(tmp_path, make_tree, monkeypatch):
    make_tree(tmp_path, {
        "modena": ["Modena.otf", "Modena.ttf"],
    })
    monkeypatch.setattr("builtins.input", lambda _: "n")
    prune_files(tmp_path, prune=("ttf",))
    assert (tmp_path / "modena" / "Modena.otf").exists()
    assert (tmp_path / "modena" / "Modena.ttf").exists()


def test_confirmation_other_input_treated_as_no(tmp_path, make_tree, monkeypatch):
    # Anything that isn't exactly "y" should abort.
    make_tree(tmp_path, {
        "modena": ["Modena.ttf"],
    })
    monkeypatch.setattr("builtins.input", lambda _: "yes please")
    prune_files(tmp_path, prune=("ttf",))
    assert (tmp_path / "modena" / "Modena.ttf").exists()


def test_eof_aborts_cleanly(tmp_path, make_tree, monkeypatch):
    make_tree(tmp_path, {
        "modena": ["Modena.ttf"],
    })

    def _raise(_):
        raise EOFError

    monkeypatch.setattr("builtins.input", _raise)
    prune_files(tmp_path, prune=("ttf",))
    assert (tmp_path / "modena" / "Modena.ttf").exists()


def test_no_matching_files_skips_prompt(tmp_path, make_tree, monkeypatch):
    make_tree(tmp_path, {
        "modena": ["Modena.otf"],
    })

    def _fail(_):
        pytest.fail("input was called even though no files matched")

    monkeypatch.setattr("builtins.input", _fail)
    prune_files(tmp_path, prune=("ttf",))
    assert (tmp_path / "modena" / "Modena.otf").exists()


def test_extension_with_or_without_leading_dot(tmp_path, make_tree, monkeypatch):
    make_tree(tmp_path, {
        "modena": ["a.ttf", "b.woff"],
    })
    monkeypatch.setattr("builtins.input", lambda _: "y")
    prune_files(tmp_path, prune=(".ttf", "woff"))
    assert not (tmp_path / "modena" / "a.ttf").exists()
    assert not (tmp_path / "modena" / "b.woff").exists()


def test_empty_prune_list_is_noop(tmp_path, make_tree, monkeypatch):
    make_tree(tmp_path, {
        "modena": ["Modena.ttf"],
    })

    def _fail(_):
        pytest.fail("input was called with empty prune list")

    monkeypatch.setattr("builtins.input", _fail)
    prune_files(tmp_path, prune=())
    assert (tmp_path / "modena" / "Modena.ttf").exists()

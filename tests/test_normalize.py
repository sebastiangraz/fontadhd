from fontadhd import normalize_name


def test_no_strip_default_lower_and_hyphenate():
    assert normalize_name("Hello World") == "hello-world"


def test_strip_at_start():
    assert normalize_name("EK Modena", strip="EK ") == "modena"


def test_strip_at_end():
    assert normalize_name("Modena EK", strip=" EK") == "modena"


def test_strip_in_middle():
    assert normalize_name("Foo EK Bar", strip="EK ") == "foo-bar"


def test_strip_multiple_occurrences():
    assert normalize_name("Foo EK Bar EK Baz", strip="EK ") == "foo-bar-baz"


def test_lowercase_off():
    assert normalize_name("Modena Pro", lowercase=False) == "Modena-Pro"


def test_hyphenate_off():
    assert normalize_name("Hello World", space_to_hyphen=False) == "hello world"


def test_multiple_spaces_collapse_to_single_hyphen():
    assert normalize_name("foo   bar") == "foo-bar"


def test_strip_then_trim_whitespace():
    # After removing the substring, surrounding whitespace is trimmed.
    assert normalize_name("  EK Modena  ", strip="EK ") == "modena"

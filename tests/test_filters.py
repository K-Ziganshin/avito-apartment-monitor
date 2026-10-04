from avito_filters import is_blacklisted, parse_blacklist


def test_blacklist():
    assert is_blacklisted("м. Девяткино, 5 мин", ["девяткино"])
    assert not is_blacklisted("м. Парнас", ["Девяткино"])
    assert not is_blacklisted("anything", [""])


def test_parse_blacklist():
    assert parse_blacklist(" A, B ,,") == ["A", "B"]

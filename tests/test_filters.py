from avito_filters import Listing, extract_listing, is_blacklisted, new_listings, parse_blacklist


class FakeCard:
    def __init__(self, ad_id="1", location="м. Парнас, 5 мин", price="35 000 ₽", link="https://example.com/1"):
        self.data = {"data-item-id": ad_id, "item-location": location, "item-price": price, "item-title": link}

    def attr(self, name):
        return self.data.get(name)

    def text_of(self, marker):
        return self.data.get(marker)

    def link_of(self, marker):
        return self.data.get(marker)


def test_blacklist():
    assert is_blacklisted("м. Девяткино, 5 мин", ["девяткино"])
    assert not is_blacklisted("м. Парнас", ["Девяткино"])
    assert not is_blacklisted("anything", [""])


def test_parse_blacklist():
    assert parse_blacklist(" A, B ,,") == ["A", "B"]
    assert parse_blacklist("") == []


def test_extract_listing():
    assert extract_listing(FakeCard()) == Listing("1", "м. Парнас, 5 мин", "35 000 ₽", "https://example.com/1")


def test_incomplete_card_is_skipped():
    assert extract_listing(FakeCard(price=None)) is None
    assert extract_listing(FakeCard(ad_id="")) is None


def test_new_listings_skips_seen_blacklisted_and_duplicates():
    cards = [FakeCard("1"), FakeCard("2", location="м. Девяткино"), FakeCard("3"), FakeCard("3")]
    seen = {"1"}
    result = new_listings(cards, seen, ["Девяткино"])
    assert [x.ad_id for x in result] == ["3"]
    assert seen == {"1", "3"}


def test_message_format():
    assert Listing("1", "Loc", "10 ₽", "https://x").message() == "New listing\nLoc\n10 ₽\n\nhttps://x"

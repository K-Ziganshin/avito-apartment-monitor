"""Pure listing logic: blacklist filter and card parsing (no browser, easy to unit-test)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Card(Protocol):
    """What the monitor needs from one search-result card (a Selenium element in production)."""

    def attr(self, name: str) -> str | None: ...
    def text_of(self, marker: str) -> str | None: ...
    def link_of(self, marker: str) -> str | None: ...


@dataclass(frozen=True)
class Listing:
    ad_id: str
    location: str
    price: str
    link: str

    def message(self) -> str:
        return f"New listing\n{self.location}\n{self.price}\n\n{self.link}"


def is_blacklisted(location: str, blacklist: list[str]) -> bool:
    """True if the listing location contains any blacklisted metro station."""
    loc = location.lower()
    return any(name.strip().lower() in loc for name in blacklist if name.strip())


def parse_blacklist(raw: str) -> list[str]:
    """Parse a comma-separated env value into a clean list."""
    return [part.strip() for part in raw.split(",") if part.strip()]


def extract_listing(card: Card) -> Listing | None:
    """Build a Listing from a card, or None if the card is incomplete (ad, partial render, changed markup)."""
    ad_id = card.attr("data-item-id")
    location = card.text_of("item-location")
    price = card.text_of("item-price")
    link = card.link_of("item-title")
    if not (ad_id and location and price and link):
        return None
    return Listing(ad_id, location.strip(), price.strip(), link)


def new_listings(cards: list[Card], seen: set[str], blacklist: list[str]) -> list[Listing]:
    """Listings that were not sent before and are not near a blacklisted station, in page order."""
    result = []
    for card in cards:
        listing = extract_listing(card)
        if listing and listing.ad_id not in seen and not is_blacklisted(listing.location, blacklist):
            result.append(listing)
            seen.add(listing.ad_id)
    return result

"""Monitors a classifieds search page and sends new listings to Telegram.

Controlled from Telegram: /stop pauses the search, /start resumes it.
For personal use only - respect the target site's terms of service.
"""

from __future__ import annotations

import logging
import os
import random
import threading
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from avito_filters import Card, new_listings, parse_blacklist
from store import SeenStore
from tg_client import Telegram

log = logging.getLogger("monitor")
BASE_DIR = Path(__file__).resolve().parent


class SeleniumCard:
    """Adapts a Selenium element to the Card protocol used by the pure logic."""

    def __init__(self, element) -> None:
        self._el = element

    def _child(self, marker: str):
        from selenium.common.exceptions import NoSuchElementException
        from selenium.webdriver.common.by import By

        try:
            return self._el.find_element(By.CSS_SELECTOR, f'[data-marker="{marker}"]')
        except NoSuchElementException:
            return None

    def attr(self, name: str) -> str | None:
        return self._el.get_attribute(name)

    def text_of(self, marker: str) -> str | None:
        child = self._child(marker)
        return child.text if child else None

    def link_of(self, marker: str) -> str | None:
        child = self._child(marker)
        return child.get_attribute("href") if child else None


def fetch_cards(search_url: str, profile_dir: Path) -> list[Card]:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By

    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--disable-notifications")
    driver = uc.Chrome(options=options)
    try:
        driver.get(search_url)
        time.sleep(random.uniform(7, 12))  # let the page render like a person would
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)
        # read everything before the browser closes
        return [_Snapshot(SeleniumCard(el)) for el in driver.find_elements(By.CSS_SELECTOR, '[data-marker="item"]')]
    finally:
        driver.quit()


class _Snapshot:
    """Copies the fields out of a live element so they survive driver.quit()."""

    def __init__(self, card: SeleniumCard) -> None:
        self._attr = {"data-item-id": card.attr("data-item-id")}
        self._text = {m: card.text_of(m) for m in ("item-location", "item-price")}
        self._link = {"item-title": card.link_of("item-title")}

    def attr(self, name: str) -> str | None:
        return self._attr.get(name)

    def text_of(self, marker: str) -> str | None:
        return self._text.get(marker)

    def link_of(self, marker: str) -> str | None:
        return self._link.get(marker)


class Monitor:
    def __init__(self, tg: Telegram, store: SeenStore, search_url: str, blacklist: list[str]) -> None:
        self.tg, self.store, self.search_url, self.blacklist = tg, store, search_url, blacklist
        self.running = threading.Event()
        self.running.set()

    def handle_command(self, command: str) -> None:
        if command == "/stop" and self.running.is_set():
            self.running.clear()
            self.tg.send("Search paused. Send /start to resume.")
            log.info("Paused by owner")
        elif command == "/start" and not self.running.is_set():
            self.running.set()
            self.tg.send("Search resumed.")
            log.info("Resumed by owner")

    def poll_commands(self) -> None:
        while True:
            try:
                for command in self.tg.owner_commands():
                    self.handle_command(command)
            except requests.RequestException as exc:
                log.warning("Polling Telegram failed: %s", type(exc).__name__)
                time.sleep(5)

    def check_once(self, cards: list[Card]) -> int:
        seen = self.store.load()
        sent = 0
        for listing in new_listings(cards, seen, self.blacklist):
            if self.tg.send(listing.message()):
                self.store.add(listing.ad_id)
                sent += 1
                time.sleep(random.uniform(0.5, 1.5))
        log.info("Checked %d cards, sent %d new", len(cards), sent)
        return sent

    def run(self, profile_dir: Path) -> None:
        threading.Thread(target=self.poll_commands, daemon=True, name="tg-commands").start()
        self.tg.send("Search started. Send /stop to pause.")
        while True:
            if self.running.is_set():
                try:
                    self.check_once(fetch_cards(self.search_url, profile_dir))
                except Exception:  # browser crashes must not stop the monitor
                    log.exception("Check cycle failed, will retry next cycle")
            time.sleep(random.uniform(150, 240))  # 2.5-4 minutes between checks


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)-7s %(name)s: %(message)s"
    )
    load_dotenv(BASE_DIR / ".env")
    monitor = Monitor(
        Telegram(os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"]),
        SeenStore(BASE_DIR / "seen_ids.txt"),
        os.environ["SEARCH_URL"],
        parse_blacklist(os.getenv("BLACKLIST_METRO", "")),
    )
    monitor.run(BASE_DIR / "chrome_profile")


if __name__ == "__main__":
    main()

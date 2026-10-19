from unittest.mock import MagicMock

from store import SeenStore
from tests.test_filters import FakeCard
from tg_client import Telegram


def test_seen_store_roundtrip(tmp_path):
    store = SeenStore(tmp_path / "seen.txt")
    assert store.load() == set()
    store.add("1")
    store.add("2")
    assert store.load() == {"1", "2"}


def test_owner_texts_ignores_other_chats_and_advances_offset():
    tg = Telegram("token", "42", session=MagicMock())
    updates = [
        {"update_id": 5, "message": {"chat": {"id": 42}, "text": "/STOP "}},
        {"update_id": 6, "message": {"chat": {"id": 99}, "text": "/start"}},
        {"update_id": 7, "edited_message": {}},
    ]
    assert tg.owner_texts(updates) == ["/stop"]
    assert tg._offset == 7


def make_monitor(tmp_path, monkeypatch):
    import monitor as m

    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    tg = MagicMock()
    tg.send.return_value = True
    return m.Monitor(tg, SeenStore(tmp_path / "seen.txt"), "https://example.com", ["Девяткино"]), tg


def test_check_once_sends_only_new_and_remembers(tmp_path, monkeypatch):
    mon, tg = make_monitor(tmp_path, monkeypatch)
    cards = [FakeCard("1"), FakeCard("2", location="м. Девяткино")]
    assert mon.check_once(cards) == 1
    assert mon.check_once(cards) == 0  # already sent
    assert tg.send.call_count == 1


def test_failed_send_is_retried_next_cycle(tmp_path, monkeypatch):
    mon, tg = make_monitor(tmp_path, monkeypatch)
    tg.send.return_value = False
    assert mon.check_once([FakeCard("1")]) == 0
    assert mon.store.load() == set()


def test_pause_and_resume(tmp_path, monkeypatch):
    mon, tg = make_monitor(tmp_path, monkeypatch)
    mon.handle_command("/stop")
    assert not mon.running.is_set()
    mon.handle_command("/stop")  # idempotent, no second message
    mon.handle_command("/start")
    assert mon.running.is_set()
    assert tg.send.call_count == 2

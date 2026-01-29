import asyncio
from datetime import datetime, date

from scraper import messages


class DummyUser:
    def __init__(self, first_name=None, last_name=None, username=None):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username


class DummyForwardHeader:
    def __init__(self, from_name=None, from_id=None):
        self.from_name = from_name
        self.from_id = from_id


def test_get_sender_name_and_forward_info(monkeypatch):
    monkeypatch.setattr(messages, "User", DummyUser)
    monkeypatch.setattr(messages, "MessageFwdHeader", DummyForwardHeader)

    sender = DummyUser(first_name="Alice", last_name="A")
    assert messages._get_sender_name(sender) == "Alice A"

    channel = type("Channel", (), {"title": "News"})
    assert messages._get_sender_name(channel) == "News"
    assert messages._get_sender_name(None) is None

    fwd = type("Fwd", (), {"fwd_from": DummyForwardHeader(from_name="Forwarded")})()
    assert messages._get_forward_info(fwd) == "Forwarded"

    fwd = type("Fwd", (), {"fwd_from": DummyForwardHeader(from_id=123)})()
    assert messages._get_forward_info(fwd) == "123"

    fwd = type("Fwd", (), {"fwd_from": DummyForwardHeader()})()
    assert messages._get_forward_info(fwd) == "forwarded"


def test_sort_and_filter_messages():
    messages_list = [
        {"sender_id": 2, "timestamp": "2024-01-02T10:00:00", "text": "Hello"},
        {"sender_id": 1, "timestamp": "2024-01-01T10:00:00", "text": "World"},
        {"sender_id": 2, "timestamp": "2024-01-03T10:00:00", "text": "Keyword"},
    ]

    grouped = messages.sort_messages(messages_list)
    assert [msg["timestamp"] for msg in grouped] == [
        "2024-01-02T10:00:00",
        "2024-01-03T10:00:00",
        "2024-01-01T10:00:00",
    ]

    chronological = messages.sort_messages(messages_list, chronological=True)
    assert [msg["timestamp"] for msg in chronological] == [
        "2024-01-01T10:00:00",
        "2024-01-02T10:00:00",
        "2024-01-03T10:00:00",
    ]

    filtered = messages.filter_by_keywords(messages_list, ["keyword"])
    assert len(filtered) == 1
    assert filtered[0]["text"] == "Keyword"


def test_scrape_messages_basic(monkeypatch):
    async def noop_sleep(*_args, **_kwargs):
        return None

    monkeypatch.setattr(messages.asyncio, "sleep", noop_sleep)
    monkeypatch.setattr(messages.random, "uniform", lambda *_args: 0)
    monkeypatch.setattr(messages, "User", DummyUser)

    class DummyMedia:
        pass

    class DummyMessage:
        def __init__(self, sender_id, sender, message_id, text, ts, has_media=False):
            self.sender_id = sender_id
            self._sender = sender
            self.id = message_id
            self.message = text
            self.date = ts
            self.reply_to = None
            self.reply_to_msg_id = None
            self.fwd_from = None
            self.media = DummyMedia() if has_media else None

        async def get_sender(self):
            return self._sender

    async def iter_messages(_entity, limit=None):
        msgs = [
            DummyMessage(
                1,
                DummyUser(first_name="Alice", last_name="A", username="alice"),
                3,
                "Newer",
                datetime(2024, 1, 3, 10, 0, 0),
                has_media=True,
            ),
            DummyMessage(
                1,
                DummyUser(first_name="Alice", last_name="A", username="alice"),
                2,
                "Middle",
                datetime(2024, 1, 2, 10, 0, 0),
            ),
            DummyMessage(
                1,
                DummyUser(first_name="Alice", last_name="A", username="alice"),
                1,
                "Older",
                datetime(2024, 1, 1, 10, 0, 0),
            ),
        ]
        for msg in msgs[:limit]:
            yield msg

    class DummyClient:
        def iter_messages(self, entity, limit=None):
            return iter_messages(entity, limit=limit)

    results = asyncio.run(
        messages.scrape_messages(
            DummyClient(),
            entity="group",
            since=date(2024, 1, 2),
            until=date(2024, 1, 3),
        )
    )

    assert len(results) == 2
    assert results[0]["text"] == "Newer"
    assert results[0]["has_media"] is True
    assert results[0]["media_type"] == "DummyMedia"

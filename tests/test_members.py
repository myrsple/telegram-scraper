import asyncio
from datetime import datetime

from scraper import members


class DummyStatusOnline:
    pass


class DummyStatusOffline:
    def __init__(self, was_online):
        self.was_online = was_online


class DummyStatusRecently:
    pass


class DummyStatusLastWeek:
    pass


class DummyStatusLastMonth:
    pass


def test_extract_last_seen_variants(monkeypatch):
    monkeypatch.setattr(members, "UserStatusOnline", DummyStatusOnline)
    monkeypatch.setattr(members, "UserStatusOffline", DummyStatusOffline)
    monkeypatch.setattr(members, "UserStatusRecently", DummyStatusRecently)
    monkeypatch.setattr(members, "UserStatusLastWeek", DummyStatusLastWeek)
    monkeypatch.setattr(members, "UserStatusLastMonth", DummyStatusLastMonth)

    user = type("User", (), {"status": DummyStatusOnline()})
    assert members._extract_last_seen(user) == "online"

    ts = datetime(2024, 1, 2, 3, 4, 5)
    user = type("User", (), {"status": DummyStatusOffline(ts)})
    assert members._extract_last_seen(user) == ts.isoformat()

    user = type("User", (), {"status": DummyStatusRecently()})
    assert members._extract_last_seen(user) == "recently"

    user = type("User", (), {"status": DummyStatusLastWeek()})
    assert members._extract_last_seen(user) == "last_week"

    user = type("User", (), {"status": DummyStatusLastMonth()})
    assert members._extract_last_seen(user) == "last_month"

    user = type("User", (), {"status": object()})
    assert members._extract_last_seen(user) == "hidden"

    user = type("User", (), {"status": None})
    assert members._extract_last_seen(user) is None


def test_scrape_members_basic(monkeypatch):
    async def noop_sleep(*_args, **_kwargs):
        return None

    monkeypatch.setattr(members.asyncio, "sleep", noop_sleep)
    monkeypatch.setattr(members.random, "uniform", lambda *_args: 0)
    async def fake_get_user_bio(*_args, **_kwargs):
        return "bio"

    monkeypatch.setattr(members, "_get_user_bio", fake_get_user_bio)
    monkeypatch.setattr(members, "_extract_last_seen", lambda *_args, **_kwargs: "online")

    class DummyUser:
        def __init__(self, user_id, username):
            self.id = user_id
            self.username = username
            self.first_name = "First"
            self.last_name = "Last"
            self.phone = None
            self.bot = False
            self.status = None
            self.premium = False

    async def iter_participants(_entity, limit=None):
        users = [DummyUser(1, "alice"), DummyUser(2, "bob")]
        for user in users[:limit]:
            yield user

    class DummyClient:
        def iter_participants(self, entity, limit=None):
            return iter_participants(entity, limit=limit)

    results = asyncio.run(members.scrape_members(DummyClient(), entity="group", limit=1))
    assert len(results) == 1
    assert results[0]["username"] == "alice"
    assert results[0]["bio"] == "bio"
    assert results[0]["last_seen"] == "online"


def test_scrape_members_admin_required(monkeypatch):
    async def iter_participants(_entity, limit=None):
        raise members.ChatAdminRequiredError(request=None, message="nope")
        yield  # pragma: no cover

    class DummyClient:
        def iter_participants(self, entity, limit=None):
            return iter_participants(entity, limit=limit)

    results = asyncio.run(members.scrape_members(DummyClient(), entity="group"))
    assert results == []

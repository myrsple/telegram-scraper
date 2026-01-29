from datetime import datetime

from scraper.combined import build_combined


def test_build_combined_merges_and_sorts_by_user_id():
    members = [
        {
            "user_id": 2,
            "username": "bob",
            "first_name": "Bob",
            "last_name": "B",
            "phone": None,
            "bio": "Hi",
            "last_seen": "online",
            "is_premium": False,
            "is_bot": False,
        },
        {
            "user_id": 1,
            "username": "alice",
            "first_name": "Alice",
            "last_name": "A",
            "phone": None,
            "bio": None,
            "last_seen": None,
            "is_premium": True,
            "is_bot": False,
        },
    ]
    messages = [
        {
            "sender_id": 1,
            "sender_username": "alice",
            "timestamp": "2024-01-02T10:00:00",
            "text": "Hello",
        },
        {
            "sender_id": 1,
            "sender_username": "alice",
            "timestamp": "2024-01-03T10:00:00",
            "text": "Second",
        },
        {
            "sender_id": 3,
            "sender_username": "charlie",
            "timestamp": "2024-01-01T09:00:00",
            "text": "No member entry",
        },
    ]

    rows = build_combined(members, messages, recent_limit=2)

    assert [row["user_id"] for row in rows] == [1, 2, 3]
    alice = rows[0]
    assert alice["message_count"] == 2
    assert alice["first_message_at"] == "2024-01-02T10:00:00"
    assert alice["last_message_at"] == "2024-01-03T10:00:00"
    assert "Hello" in alice["recent_messages"]
    assert "Second" in alice["recent_messages"]

    bob = rows[1]
    assert bob["message_count"] == 0
    assert bob["recent_messages"] == ""

    charlie = rows[2]
    assert charlie["username"] == "charlie"
    assert charlie["message_count"] == 1


def test_build_combined_recent_messages_truncates():
    members = [{"user_id": 1}]
    messages = [
        {
            "sender_id": 1,
            "sender_username": None,
            "timestamp": datetime(2024, 1, 1, 10, 0, 0).isoformat(),
            "text": "A " * 50,
        }
    ]

    rows = build_combined(members, messages, recent_limit=1, max_recent_chars=20)

    assert rows[0]["recent_messages"].endswith("…")
    assert len(rows[0]["recent_messages"]) <= 21

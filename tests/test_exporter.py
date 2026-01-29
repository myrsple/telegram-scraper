import csv
from datetime import datetime

from scraper import exporter


class FixedDateTime:
    @classmethod
    def now(cls):
        return datetime(2024, 1, 2, 3, 4, 5)


def test_sanitize_filename():
    assert exporter._sanitize_filename("My Group!") == "My_Group"
    assert exporter._sanitize_filename("  Spaces  ") == "Spaces"
    assert exporter._sanitize_filename("Weird__Name") == "Weird_Name"


def test_export_members_creates_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(exporter, "datetime", FixedDateTime)

    members = [
        {
            "user_id": 1,
            "username": "alice",
            "first_name": "Alice",
            "last_name": "A",
            "phone": None,
            "is_bot": False,
            "last_seen": "online",
            "is_premium": True,
            "bio": "Hello",
        }
    ]

    filepath = exporter.export_members(members, "My Group!", output_dir=tmp_path)
    assert filepath.name.startswith("My_Group_members_20240102_030405")

    with open(filepath, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert rows[0]["username"] == "alice"
    assert rows[0]["bio"] == "Hello"


def test_export_messages_creates_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(exporter, "datetime", FixedDateTime)

    messages = [
        {
            "sender_id": 1,
            "sender_username": "alice",
            "sender_name": "Alice A",
            "message_id": 10,
            "timestamp": "2024-01-02T10:00:00",
            "text": "Hi",
            "reply_to_id": None,
            "forward_from": None,
            "has_media": False,
            "media_type": None,
        }
    ]

    filepath = exporter.export_messages(messages, "My Group!", output_dir=tmp_path)
    assert filepath.name.startswith("My_Group_messages_20240102_030405")

    with open(filepath, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert rows[0]["text"] == "Hi"
    assert rows[0]["sender_name"] == "Alice A"


def test_export_combined_creates_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(exporter, "datetime", FixedDateTime)

    rows = [
        {
            "user_id": 1,
            "username": "alice",
            "first_name": "Alice",
            "last_name": "A",
            "phone": None,
            "bio": None,
            "last_seen": None,
            "is_premium": False,
            "is_bot": False,
            "message_count": 2,
            "first_message_at": "2024-01-01T10:00:00",
            "last_message_at": "2024-01-02T10:00:00",
            "recent_messages": "One | Two",
        }
    ]

    filepath = exporter.export_combined(rows, "My Group!", output_dir=tmp_path)
    assert filepath.name.startswith("My_Group_combined_20240102_030405")

    with open(filepath, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert rows[0]["message_count"] == "2"
    assert rows[0]["recent_messages"] == "One | Two"

"""Combine member and message data into a single AI-ready export."""

from datetime import datetime


def _normalize_text(text):
    if not text:
        return ""
    return " ".join(text.split())


def build_combined(members, messages, recent_limit=10, max_recent_chars=2000):
    """
    Build a combined per-user view from members + messages.

    Args:
        members: list of member dicts
        messages: list of message dicts
        recent_limit: max number of recent messages to include per user
        max_recent_chars: max total chars in recent_messages field

    Returns:
        list of combined dicts (one row per user)
    """
    by_user = {}

    for member in members or []:
        user_id = member.get("user_id")
        if user_id is None:
            continue
        by_user[user_id] = {
            "user_id": user_id,
            "username": member.get("username"),
            "first_name": member.get("first_name"),
            "last_name": member.get("last_name"),
            "phone": member.get("phone"),
            "bio": member.get("bio"),
            "last_seen": member.get("last_seen"),
            "is_premium": member.get("is_premium"),
            "is_bot": member.get("is_bot"),
            "message_count": 0,
            "first_message_at": None,
            "last_message_at": None,
            "recent_messages": "",
        }

    messages_by_user = {}
    for msg in messages or []:
        sender_id = msg.get("sender_id")
        if sender_id is None:
            continue
        messages_by_user.setdefault(sender_id, []).append(msg)

    for sender_id, msgs in messages_by_user.items():
        # Ensure a base entry exists (for users missing from members list)
        if sender_id not in by_user:
            by_user[sender_id] = {
                "user_id": sender_id,
                "username": None,
                "first_name": None,
                "last_name": None,
                "phone": None,
                "bio": None,
                "last_seen": None,
                "is_premium": None,
                "is_bot": None,
                "message_count": 0,
                "first_message_at": None,
                "last_message_at": None,
                "recent_messages": "",
            }

        msgs_sorted = sorted(msgs, key=lambda m: m.get("timestamp") or "")
        entry = by_user[sender_id]
        entry["message_count"] = len(msgs_sorted)
        if msgs_sorted:
            entry["first_message_at"] = msgs_sorted[0].get("timestamp")
            entry["last_message_at"] = msgs_sorted[-1].get("timestamp")

        # Fill username if missing from member info
        if not entry.get("username"):
            for msg in reversed(msgs_sorted):
                username = msg.get("sender_username")
                if username:
                    entry["username"] = username
                    break

        # Recent messages (most recent N)
        recent_msgs = []
        for msg in reversed(msgs_sorted[-recent_limit:]):
            text = _normalize_text(msg.get("text"))
            if text:
                recent_msgs.append(text)
        recent_blob = " | ".join(recent_msgs)
        if len(recent_blob) > max_recent_chars:
            recent_blob = recent_blob[:max_recent_chars].rstrip() + "…"
        entry["recent_messages"] = recent_blob

    # Keep deterministic order by user_id
    return [by_user[user_id] for user_id in sorted(by_user.keys())]

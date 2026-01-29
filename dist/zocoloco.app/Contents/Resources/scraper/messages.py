"""Message scraping logic."""

import asyncio
import random
from datetime import datetime
from collections import defaultdict
from telethon.errors import FloodWaitError
from telethon.tl.types import User, MessageFwdHeader


def _get_sender_name(sender):
    """Get display name from sender."""
    if sender is None:
        return None
    if isinstance(sender, User):
        parts = [sender.first_name, sender.last_name]
        return ' '.join(p for p in parts if p)
    return getattr(sender, 'title', None)


def _get_forward_info(message):
    """Extract forward source info."""
    fwd = message.fwd_from
    if not fwd:
        return None
    
    if isinstance(fwd, MessageFwdHeader):
        if fwd.from_name:
            return fwd.from_name
        if fwd.from_id:
            return str(fwd.from_id)
    
    return 'forwarded'


async def scrape_messages(client, entity, limit=None, since=None, until=None, delay_range=(1, 3)):
    """
    Scrape message history from a group.
    
    Args:
        client: Telegram client
        entity: Group entity
        limit: Max messages to fetch (None = all)
        since: Start date (datetime.date or None)
        until: End date (datetime.date or None)
        delay_range: (min, max) seconds to delay between batches
    
    Returns:
        List of message dictionaries
    """
    messages = []
    count = 0
    batch_size = 100
    
    try:
        async for message in client.iter_messages(entity, limit=limit):
            msg_date = message.date.date()
            
            # Date filtering
            if until and msg_date > until:
                continue  # Skip messages newer than until
            if since and msg_date < since:
                break  # Stop when we reach messages older than since
            
            sender = await message.get_sender()
            
            msg_data = {
                'sender_id': message.sender_id,
                'sender_username': getattr(sender, 'username', None) if sender else None,
                'sender_name': _get_sender_name(sender),
                'message_id': message.id,
                'timestamp': message.date.isoformat(),
                'text': message.message or '',
                'reply_to_id': message.reply_to_msg_id if message.reply_to else None,
                'forward_from': _get_forward_info(message),
                'has_media': bool(message.media),
                'media_type': message.media.__class__.__name__ if message.media else None,
            }
            messages.append(msg_data)
            count += 1
            
            # Progress indicator
            if count % 100 == 0:
                print(f"  Scraped {count} messages...")
            
            # Rate limiting
            if count % batch_size == 0:
                delay = random.uniform(*delay_range)
                await asyncio.sleep(delay)
    
    except FloodWaitError as e:
        print(f"\nRate limited. Waiting {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        print(f"Returning {len(messages)} messages scraped before rate limit.")
    
    except Exception as e:
        print(f"\nError scraping messages: {e}")
        if messages:
            print(f"Returning {len(messages)} messages scraped before error.")
    
    return messages


def sort_messages(messages, chronological=False):
    """
    Sort messages.
    
    Default: Group by sender, then chronological within each sender.
    With chronological=True: Pure time-based order.
    """
    if chronological:
        return sorted(messages, key=lambda m: m['timestamp'])
    
    # Group by sender
    by_sender = defaultdict(list)
    for msg in messages:
        by_sender[msg['sender_id']].append(msg)
    
    # Sort each sender's messages by time, flatten
    result = []
    for sender_id in by_sender:
        sender_msgs = sorted(by_sender[sender_id], key=lambda m: m['timestamp'])
        result.extend(sender_msgs)
    
    return result


def filter_by_keywords(messages, keywords):
    """
    Filter messages to only those containing any of the keywords.
    
    Args:
        messages: List of message dicts
        keywords: List of keywords (case-insensitive)
    
    Returns:
        Filtered list of messages
    """
    if not keywords:
        return messages
    
    # Normalize keywords to lowercase
    keywords_lower = [kw.lower() for kw in keywords]
    
    filtered = []
    for msg in messages:
        text = (msg.get('text') or '').lower()
        if any(kw in text for kw in keywords_lower):
            filtered.append(msg)
    
    return filtered

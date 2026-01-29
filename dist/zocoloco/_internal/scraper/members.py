"""Member scraping logic."""

import asyncio
import random
from telethon.errors import FloodWaitError, ChatAdminRequiredError
from telethon.tl.types import UserStatusOnline, UserStatusOffline, UserStatusRecently
from telethon.tl.types import UserStatusLastWeek, UserStatusLastMonth
from telethon.tl.functions.users import GetFullUserRequest


def _extract_last_seen(user):
    """Extract last seen status from user."""
    status = user.status
    
    if status is None:
        return None
    if isinstance(status, UserStatusOnline):
        return 'online'
    if isinstance(status, UserStatusOffline):
        return status.was_online.isoformat() if status.was_online else 'offline'
    if isinstance(status, UserStatusRecently):
        return 'recently'
    if isinstance(status, UserStatusLastWeek):
        return 'last_week'
    if isinstance(status, UserStatusLastMonth):
        return 'last_month'
    
    return 'hidden'


async def _get_user_bio(client, user):
    """Fetch user bio (requires additional API call)."""
    try:
        full_user = await client(GetFullUserRequest(user))
        return full_user.full_user.about
    except FloodWaitError as e:
        print(f"\n  Rate limited on bio fetch. Waiting {e.seconds}s...")
        await asyncio.sleep(e.seconds)
        # Retry once after waiting
        try:
            full_user = await client(GetFullUserRequest(user))
            return full_user.full_user.about
        except Exception:
            return None
    except Exception:
        return None


async def scrape_members(client, entity, limit=None):
    """
    Scrape member list from a group.
    
    Args:
        client: Telegram client
        entity: Group entity
        limit: Max members to fetch (None = all)
    
    Returns:
        List of member dictionaries
    """
    members = []
    count = 0
    
    try:
        async for user in client.iter_participants(entity, limit=limit):
            # Small delay before each bio fetch to stay safe
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Fetch bio (extra API call per user)
            bio = await _get_user_bio(client, user)
            
            member = {
                'user_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,  # Usually None due to privacy
                'is_bot': user.bot,
                'last_seen': _extract_last_seen(user),
                'is_premium': getattr(user, 'premium', False),
                'bio': bio,
            }
            members.append(member)
            count += 1
            
            # Progress indicator
            if count % 25 == 0:
                print(f"  Scraped {count} members...")
            
            # Longer pause every 10 users
            if count % 10 == 0:
                delay = random.uniform(2, 4)
                await asyncio.sleep(delay)
            
            # Even longer pause every 50 users
            if count % 50 == 0:
                print(f"  Pausing to avoid rate limits...")
                await asyncio.sleep(random.uniform(5, 10))
    
    except FloodWaitError as e:
        print(f"\nRate limited. Waiting {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        # Continue where we left off would require more complex logic
        # For now, return what we have
        print(f"Returning {len(members)} members scraped before rate limit.")
    
    except ChatAdminRequiredError:
        print("\nError: Admin privileges required to access member list.")
        print("This group restricts member list access to admins only.")
        return []
    
    except Exception as e:
        print(f"\nError scraping members: {e}")
        if members:
            print(f"Returning {len(members)} members scraped before error.")
    
    return members

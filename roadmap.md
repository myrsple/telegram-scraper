# Implementation Roadmap

Build order for the Telegram Group Scraper. Each step is a working checkpoint.

---

## Step 1: Project Setup

Create the file structure and dependencies.

```
telegram-scraper/
├── scraper/
│   ├── __init__.py
│   ├── client.py
│   ├── members.py
│   ├── messages.py
│   └── exporter.py
├── output/
├── .env.example
├── .gitignore
├── requirements.txt
└── main.py
```

**Files to create:**

```
# requirements.txt
telethon>=1.34.0
python-dotenv>=1.0.0
```

```
# .env.example
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_PHONE=
```

```
# .gitignore
.env
*.session
output/
__pycache__/
```

**Checkpoint:** Project structure exists, can `pip install -r requirements.txt`

---

## Step 2: Authentication (`scraper/client.py`)

Handle Telegram connection and login flow.

**Reference from unnohwn repo:**
- Phone auth with 2FA handling (`SessionPasswordNeededError`)
- Session file persistence (Telethon handles this automatically)
- API credential prompting

**Implementation:**

```python
# Core pattern to use
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

async def get_client(api_id, api_hash, phone):
    client = TelegramClient('session', api_id, api_hash)
    await client.connect()
    
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        code = input("Enter code: ")
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            password = input("2FA password: ")
            await client.sign_in(password=password)
    
    return client
```

**What to build:**
- `load_credentials()` — Read from .env, prompt if missing, save to .env
- `get_client()` — Connect and authenticate
- Graceful error messages for invalid credentials, banned accounts

**Checkpoint:** Can run script, authenticate, and see "Connected successfully"

---

## Step 3: Group Resolution & Info Command

Resolve group identifiers and display info.

**Reference from unnohwn repo:**
- Entity resolution pattern: `PeerChannel(int(id))` for numeric IDs
- Username resolution: pass string directly to `get_entity()`

**Implementation:**

```python
# Pattern for resolving any group format
from telethon.tl.types import PeerChannel

async def resolve_group(client, identifier):
    # Handle: @username, https://t.me/..., -100123456789
    if identifier.lstrip('-').isdigit():
        entity = await client.get_entity(PeerChannel(int(identifier)))
    else:
        entity = await client.get_entity(identifier)
    return entity
```

**What to build:**
- `resolve_group(client, identifier)` — Handle all input formats
- `get_group_info(entity)` — Return title, member count, type
- Wire up `info` command in main.py

**Checkpoint:** `python main.py info @testgroup` shows group details

---

## Step 4: Member Scraping (`scraper/members.py`)

Extract member list from a group.

**Note:** This doesn't exist in unnohwn repo — build from Telethon docs.

**Implementation:**

```python
# Core pattern
async def scrape_members(client, entity, limit=None):
    members = []
    async for user in client.iter_participants(entity, limit=limit):
        members.append({
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,  # Usually None due to privacy
            'is_bot': user.bot,
            'is_premium': getattr(user, 'premium', False),
            # last_seen requires checking user.status
        })
    return members
```

**What to build:**
- `scrape_members(client, entity, limit)` — Iterate participants
- `extract_last_seen(user)` — Parse UserStatus variants
- Rate limiting: 1-3 sec random delay between batches
- Progress indicator (simple print, no fancy bars)

**Checkpoint:** `python main.py members @testgroup` outputs member data

---

## Step 5: CSV Export (`scraper/exporter.py`)

Write data to CSV files.

**Implementation:**

```python
import csv
from pathlib import Path
from datetime import datetime

def export_members(members, group_name, output_dir='output'):
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{group_name}_members_{timestamp}.csv"
    filepath = Path(output_dir) / filename
    
    fieldnames = ['user_id', 'username', 'first_name', 'last_name', 
                  'phone', 'is_bot', 'last_seen', 'is_premium']
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(members)
    
    return filepath
```

**What to build:**
- `export_members(members, group_name, output_dir)`
- `export_messages(messages, group_name, output_dir)`
- Sanitize group names for filenames

**Checkpoint:** Members export creates valid CSV in `./output/`

---

## Step 6: Message Scraping (`scraper/messages.py`)

Extract message history from a group.

**Reference from unnohwn repo:**
- Message iteration: `client.iter_messages(entity, limit=...)`
- Sender resolution: `await message.get_sender()`
- Reply handling: `message.reply_to_msg_id`

**Implementation:**

```python
# Core pattern
async def scrape_messages(client, entity, limit=None, since=None, until=None):
    messages = []
    async for message in client.iter_messages(entity, limit=limit):
        # Apply date filters
        if since and message.date.date() < since:
            continue
        if until and message.date.date() > until:
            break
            
        sender = await message.get_sender()
        messages.append({
            'sender_id': message.sender_id,
            'sender_username': getattr(sender, 'username', None),
            'sender_name': _get_sender_name(sender),
            'message_id': message.id,
            'timestamp': message.date.isoformat(),
            'text': message.message or '',
            'reply_to_id': message.reply_to_msg_id if message.reply_to else None,
            'forward_from': _get_forward_info(message),
            'has_media': bool(message.media),
            'media_type': message.media.__class__.__name__ if message.media else None,
        })
    return messages
```

**What to build:**
- `scrape_messages(client, entity, limit, since, until)`
- Date filtering logic
- Forward info extraction
- Progress indicator

**Checkpoint:** `python main.py messages @testgroup --limit 100` works

---

## Step 7: Message Sorting (Group by Sender)

Default: group messages by sender, then chronological within each sender.

**Implementation:**

```python
def sort_messages(messages, chronological=False):
    if chronological:
        return sorted(messages, key=lambda m: m['timestamp'])
    
    # Group by sender, maintain order within each sender
    from collections import defaultdict
    by_sender = defaultdict(list)
    for msg in messages:
        by_sender[msg['sender_id']].append(msg)
    
    # Sort each sender's messages, flatten
    result = []
    for sender_id in by_sender:
        sender_msgs = sorted(by_sender[sender_id], key=lambda m: m['timestamp'])
        result.extend(sender_msgs)
    
    return result
```

**Checkpoint:** Messages CSV shows all messages from user A, then user B, etc.

---

## Step 8: CLI with Argparse (`main.py`)

Build the full command-line interface.

**Commands:**
- `members <group>` — Scrape member list
- `messages <group>` — Scrape messages
- `info <group>` — Show group info
- `examples` — Print usage examples

**Options:**
- `--limit N` — Max items
- `--since DATE` — Start date (messages)
- `--until DATE` — End date (messages)
- `--chronological` — Time order instead of grouped
- `--output DIR` — Custom output directory

**Implementation pattern:**

```python
import argparse

def main():
    parser = argparse.ArgumentParser(description='Telegram Group Scraper')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # members command
    members_parser = subparsers.add_parser('members', help='Scrape member list')
    members_parser.add_argument('group', help='Group identifier')
    members_parser.add_argument('--limit', type=int)
    members_parser.add_argument('--output', default='output')
    
    # messages command
    messages_parser = subparsers.add_parser('messages', help='Scrape messages')
    messages_parser.add_argument('group', help='Group identifier')
    messages_parser.add_argument('--limit', type=int)
    messages_parser.add_argument('--since', help='Start date YYYY-MM-DD')
    messages_parser.add_argument('--until', help='End date YYYY-MM-DD')
    messages_parser.add_argument('--chronological', action='store_true')
    messages_parser.add_argument('--output', default='output')
    
    # info command
    info_parser = subparsers.add_parser('info', help='Show group info')
    info_parser.add_argument('group', help='Group identifier')
    
    # examples command
    subparsers.add_parser('examples', help='Show usage examples')
    
    args = parser.parse_args()
    asyncio.run(run_command(args))
```

**Checkpoint:** All commands work with `--help` at every level

---

## Step 9: Error Handling & Polish

Add robust error handling throughout.

**Error cases to handle:**
- Missing/invalid .env credentials
- Group not found
- No access (private group, banned)
- Rate limiting (`FloodWaitError`)
- Network errors (retry with backoff)
- Session expired

**Pattern for rate limits (from unnohwn repo):**

```python
from telethon.errors import FloodWaitError

try:
    # API call
except FloodWaitError as e:
    print(f"Rate limited. Waiting {e.seconds} seconds...")
    await asyncio.sleep(e.seconds)
    # Retry
```

**Checkpoint:** Errors produce clear, actionable messages

---

## Step 10: Testing & README

Test on various group types and write documentation.

**Test scenarios:**
- Public group via @username
- Private group via invite link
- Group via numeric ID
- Small group (<100 members)
- Large group (>1000 members)
- Group where you're not a member (expect error)

**README sections:**
- Quick start (3 steps)
- Getting API credentials
- Usage examples
- Limitations & warnings

**Checkpoint:** Fresh clone → working tool in under 5 minutes

---

## Summary: Build Order

1. ✅ Project setup (files, deps)
2. ✅ Authentication flow
3. ✅ Group resolution + info command
4. ✅ Member scraping
5. ✅ CSV export
6. ✅ Message scraping
7. ✅ Message sorting
8. ✅ Full CLI
9. ✅ Error handling
10. ✅ Testing & docs

Each step builds on the previous. Don't skip ahead — verify each checkpoint before moving on.

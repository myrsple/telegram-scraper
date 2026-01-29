# Telegram Group Scraper - Development Plan

## Project Overview

A CLI tool for occasional scraping of group members and message history from Telegram groups. Built with Python and Telethon for direct MTProto API access. Outputs to CSV for easy manipulation in spreadsheets or other tools.

**Use case:** Ad-hoc extraction of contacts and messages from specific Telegram groups. Not for continuous monitoring or automation - manual execution when needed.

**Why CLI (not a Telegram bot):**
- This is a **userbot** (logs in as your account), not a bot
- Telegram bots cannot access member lists or message history - they're sandboxed
- Scraping requires MTProto client API, which only works as a user client
- CLI is the natural fit: run when needed, get CSV output, done

**Constraints:**
- Violates Telegram ToS - use secondary account, expect potential bans
- Phone numbers rarely accessible due to privacy settings
- Large groups (>10k) have API-enforced member limits
- Rate limiting requires delays between requests

---

## Technical Stack

- **Language:** Python 3.10+
- **Telegram client:** Telethon
- **Output format:** CSV (for easy spreadsheet manipulation)
- **Config:** .env file for credentials
- **Session persistence:** Telethon SQLite session file

---

## Project Structure

```
telegram-scraper/
├── scraper/
│   ├── __init__.py
│   ├── client.py          # Telegram client initialization and auth
│   ├── members.py         # Member scraping logic
│   ├── messages.py        # Message scraping logic
│   └── exporter.py        # CSV export utilities
├── output/                # Generated exports (gitignored)
├── .env.example           # Template for credentials
├── .env                   # Actual credentials (gitignored)
├── .gitignore
├── requirements.txt
├── README.md
└── main.py                # CLI entry point
```

---

## Core Features

### 1. Authentication
- First run: prompt for phone number, handle 2FA if enabled
- Session file persists auth for subsequent runs
- Graceful handling of session expiry or account ban

### 2. Group Selection
- Accept group by: username (@groupname), invite link, or numeric ID
- Validate access before attempting scrape
- Display group info (title, member count) before proceeding

### 3. Member Scraping
- Extract: user_id, username, first_name, last_name, phone (if available), is_bot, last_seen
- Handle private groups vs public groups
- Respect API limits, implement delays (1-3 sec randomized between batches)
- Progress indicator for large groups

### 4. Message Scraping
- Extract: sender_id, sender_username, sender_name, message_id, timestamp, text, reply_to_id, forward_from, has_media, media_type
- **Default sort: grouped by sender** (all messages from same user together, then by timestamp within each user)
- Optional `--chronological` flag for pure time-based order
- Sender columns first in CSV for easy cross-referencing with members export
- Configurable: limit by count (e.g., last 1000) or date range
- Handle deleted messages and unavailable senders gracefully

**Workflow:** Export members and messages separately. Messages CSV grouped by user lets you scan what each person said, then tab to members CSV to find their contact details (user_id, username match between both files).

### 5. Export
- CSV format: flat structure, one row per member/message
- Easy to open in Excel, Google Sheets, or process with pandas
- Filename format: `{group_name}_{type}_{timestamp}.csv`
- Output to `./output/` directory

**Members CSV columns:**
`user_id, username, first_name, last_name, phone, is_bot, last_seen, is_premium`

**Messages CSV columns:**
`sender_id, sender_username, sender_name, message_id, timestamp, text, reply_to_id, forward_from, has_media, media_type`

Cross-reference via `user_id` ↔ `sender_id` or `username` ↔ `sender_username`.

---

## CLI Interface

```bash
# Basic usage
python main.py members @groupname
python main.py messages @groupname

# With options
python main.py messages @groupname --limit 500
python main.py messages @groupname --since 2024-01-01 --until 2024-06-01
python main.py messages @groupname --chronological  # time order instead of grouped by user

# Info only (no scrape)
python main.py info @groupname

# Help
python main.py --help              # general help
python main.py members --help      # command-specific help
python main.py examples            # show usage examples
```

**Arguments:**
- `command`: members | messages | info | examples
- `group`: @username, invite link, or ID
- `--limit`: max items to fetch (default: all available)
- `--since`: start date for messages (YYYY-MM-DD)
- `--until`: end date for messages (YYYY-MM-DD)
- `--chronological`: sort messages by time instead of grouping by sender (default: grouped by user)
- `--output`: custom output directory
- `--help`, `-h`: show help for any command

---

## Help System

Robust help at every level so users can quickly find what they need.

### Global Help (`python main.py --help`)
```
Telegram Group Scraper - Extract members and messages from Telegram groups

Usage: python main.py <command> <group> [options]

Commands:
  members    Scrape group member list to CSV
  messages   Scrape message history to CSV (grouped by user)
  info       Show group details without scraping
  examples   Show common usage examples

Run 'python main.py <command> --help' for command-specific options.

Setup:
  1. Get API credentials at https://my.telegram.org/apps
  2. Copy .env.example to .env and fill in your credentials
  3. First run will prompt for phone verification
```

### Command Help (`python main.py members --help`)
```
Scrape member list from a Telegram group

Usage: python main.py members <group> [options]

Arguments:
  group       Group identifier: @username, invite link, or numeric ID

Options:
  --limit N        Max members to fetch (default: all)
  --output DIR     Custom output directory (default: ./output)
  -h, --help       Show this help

Output:
  CSV with columns: user_id, username, first_name, last_name, phone, 
                    is_bot, last_seen, is_premium

Examples:
  python main.py members @mycryptogroup
  python main.py members https://t.me/+AbCdEfG123 --limit 500
  python main.py members -100123456789 --output ./exports
```

### Message Help (`python main.py messages --help`)
```
Scrape message history from a Telegram group

Usage: python main.py messages <group> [options]

Arguments:
  group       Group identifier: @username, invite link, or numeric ID

Options:
  --limit N        Max messages to fetch (default: all)
  --since DATE     Start date filter (YYYY-MM-DD)
  --until DATE     End date filter (YYYY-MM-DD)
  --chronological  Sort by time instead of grouping by user
  --output DIR     Custom output directory (default: ./output)
  -h, --help       Show this help

Output:
  CSV with columns: sender_id, sender_username, sender_name, message_id,
                    timestamp, text, reply_to_id, forward_from, has_media, media_type
  Default sort: grouped by sender, then chronological within each sender

Examples:
  python main.py messages @mycryptogroup
  python main.py messages @mycryptogroup --limit 1000 --since 2024-01-01
  python main.py messages @mycryptogroup --chronological
```

### Examples Command (`python main.py examples`)
```
Common usage examples:

FIRST-TIME SETUP
  1. Get API credentials at https://my.telegram.org/apps
  2. cp .env.example .env
  3. Edit .env with your TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE
  4. python main.py info @anygroup   # triggers phone verification

SCRAPE MEMBERS
  python main.py members @groupname              # all members
  python main.py members @groupname --limit 100  # first 100 only

SCRAPE MESSAGES  
  python main.py messages @groupname                           # all, grouped by user
  python main.py messages @groupname --limit 500               # last 500 messages
  python main.py messages @groupname --since 2024-06-01        # from date onwards
  python main.py messages @groupname --chronological           # time order

GROUP INFO
  python main.py info @groupname                 # preview before scraping

GROUP FORMATS (all work)
  @username                    # public group username
  https://t.me/username        # public link
  https://t.me/+AbCdEfG123     # private invite link
  -100123456789                # numeric group ID

WORKFLOW: Find active users and their contact info
  1. python main.py messages @target --limit 1000   # see who's talking
  2. python main.py members @target                  # get their details
  3. Cross-reference sender_id with user_id in both CSVs
```

### Implementation Notes
- Use Python's `argparse` with subparsers for command structure
- Each command has its own help via `add_parser(..., help=...)`
- `examples` is a pseudo-command that just prints the examples block
- Help text should fit in 80-char terminal width
- Error messages should suggest `--help` when user makes mistakes

---

## Implementation Phases

### Phase 1: Foundation
1. Set up project structure and dependencies
2. Implement client.py with authentication flow
3. Test connection and session persistence
4. Create .env handling for API credentials

**Verification:** Can authenticate and list user's joined groups

### Phase 2: Member Scraping
1. Implement group resolution (username/link/ID → entity)
2. Build member iteration with pagination
3. Add rate limiting with randomized delays
4. Implement CSV exporter for members
5. Add progress output

**Verification:** Can export member list from a test group to CSV

### Phase 3: Message Scraping
1. Implement message iteration with pagination
2. Add date range filtering
3. Handle edge cases (deleted messages, unavailable users)
4. Implement CSV exporter for messages

**Verification:** Can export message history with filters to CSV

### Phase 4: Polish & Help System
1. Implement help system with argparse subparsers
2. Add `info` command for group inspection
3. Add `examples` command with common workflows
4. Improve error messages (suggest `--help` on mistakes)
5. Write README with quick start guide
6. Test on various group types (public, private, large, small)

**Verification:** Running `--help` at any level gives clear, actionable guidance

---

## Error Handling

| Scenario | Handling |
|----------|----------|
| Missing .env | Prompt for credentials, save to .env |
| Invalid API credentials | Clear message, prompt to check my.telegram.org |
| Invalid phone/code | Clear message, prompt retry |
| 2FA required | Prompt for password |
| Session expired | Delete session file, re-auth |
| Group not found | Exit with clear error |
| No access to group | Explain (private/banned) |
| Rate limited | Back off, warn user, continue |
| Account banned | Detect and inform user |
| Network errors | Retry with exponential backoff (3 attempts) |

---

## Rate Limiting Strategy

- Delay 1-3 seconds (randomized) between pagination requests
- Delay 5-10 seconds if rate limit warning received
- Maximum 200 members per request batch
- Maximum 100 messages per request batch
- Optional `--slow` flag for extra-cautious delays

---

## Security & Privacy Notes

- **Credentials in .env only** - never hardcode API_ID/API_HASH in scripts
- Never commit `.env` or `*.session` files (ensure they're in `.gitignore`)
- Session file contains auth tokens - treat as password
- Scraped data may contain PII - handle responsibly
- Consider GDPR implications if used in EU context

---

## Dependencies

```
telethon>=1.34.0
python-dotenv>=1.0.0
```

---

## Configuration

### Credentials Setup (.env)

Credentials are stored in a `.env` file to keep them out of your code and version control. **Never hardcode API credentials directly in scripts.**

**First-time setup:**
1. Get API credentials from https://my.telegram.org/apps
2. Copy `.env.example` to `.env`
3. Fill in your values

**.env.example** (commit this):
```
# Telegram API credentials
# Get yours at https://my.telegram.org/apps
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_PHONE=
```

**.env** (never commit - already in .gitignore):
```
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_PHONE=+420123456789
```

**How it works:**
- `python-dotenv` loads `.env` automatically on startup
- If `.env` is missing or incomplete, the script prompts for credentials interactively
- Credentials entered interactively are saved to `.env` for next run

**.gitignore must include:**
```
.env
*.session
output/
```

---

## Future Considerations (Out of Scope)

- Media downloading
- JSON export format
- Web interface
- Multiple account rotation
- Proxy support for ban evasion

These are intentionally excluded to keep the tool simple for occasional use.
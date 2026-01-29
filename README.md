![zocoloco header](assets/zoco-gh.png)

# zocoloco — Telegram group scraper

Scrape TG groups and get loco on the zoco. Pull members, messages, and a combined view into clean CSVs for analysis, AI workflows, or outreach.

## What it does

- **Members at scale**: export member lists with bios, premium status, and last-seen hints.
- **Message timelines**: fetch history with date ranges, keyword filters, and sorting options.
- **Combined view**: one CSV per user, stitched from members + messages (handy for scoring).
- **Desktop UI + CLI**: the glossy desktop app or a fast terminal flow.

## Quick start (from source)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get API credentials at https://my.telegram.org/apps

# 3. Set up credentials
cp .env.example .env
# Fill in TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE
```

### Desktop app

```bash
python app.py
```

### CLI

```bash
# First run will prompt for verification code
python main.py info @groupname

# Members
python main.py members @groupname
python main.py members @groupname --limit 100

# Messages
python main.py messages @groupname
python main.py messages @groupname --limit 500
python main.py messages @groupname --since 2024-01-01 --until 2024-06-01
python main.py messages @groupname --keywords "audit, risk"
python main.py messages @groupname --chronological

# Combined
python main.py combined @groupname --limit 500

# See all examples
python main.py examples
```

## Group formats

All of these work:
- `@username` — public group handle
- `https://t.me/username` — public link
- `https://t.me/+AbCdEfG123` — private invite link
- `-100123456789` — numeric ID

## Output

CLI exports land in `./output/` by default:
- `{group}_members_{timestamp}.csv`
- `{group}_messages_{timestamp}.csv`
- `{group}_combined_{timestamp}.csv`

The desktop app lets you choose an output folder (defaults to your Desktop).

## CSV fields

- **Members**: `user_id`, `username`, `first_name`, `last_name`, `phone`, `is_bot`, `last_seen`, `is_premium`, `bio`
- **Messages**: `sender_id`, `sender_username`, `sender_name`, `message_id`, `timestamp`, `text`, `reply_to_id`, `forward_from`, `has_media`, `media_type`
- **Combined**: `user_id`, `username`, `first_name`, `last_name`, `phone`, `bio`, `last_seen`, `is_premium`, `is_bot`, `message_count`, `first_message_at`, `last_message_at`, `recent_messages`

## Notes

- You must be a member of the group to scrape it.
- Member lists can be admin-only in some groups.
- Phone numbers are often hidden by privacy settings.
- Large groups and frequent requests can trigger rate limits.
- Don't get too loco or Telegram will ban you.

# Telegram Group Scraper

Extract members and messages from Telegram groups to CSV.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get API credentials at https://my.telegram.org/apps

# 3. Set up credentials
cp .env.example .env
# Edit .env with your API_ID, API_HASH, and phone number

# 4. Run (first run will prompt for verification code)
python main.py info @groupname
```

## Usage

```bash
# Show group info
python main.py info @groupname

# Scrape members
python main.py members @groupname
python main.py members @groupname --limit 100

# Scrape messages
python main.py messages @groupname
python main.py messages @groupname --limit 500
python main.py messages @groupname --since 2024-01-01 --until 2024-06-01
python main.py messages @groupname --chronological  # time order (default: grouped by sender)

# See all examples
python main.py examples
```

## Group Formats

All these work:
- `@username` — public group handle
- `https://t.me/username` — public link
- `https://t.me/+AbCdEfG123` — private invite link
- `-100123456789` — numeric ID

## Output

CSV files are saved to `./output/` with format:
- `{group}_members_{timestamp}.csv`
- `{group}_messages_{timestamp}.csv`

## Requirements

- Python 3.10+
- Must be a member of the group to scrape
- API credentials from my.telegram.org

## Limitations

- Phone numbers rarely visible (privacy settings)
- Large groups (>10k) may have API-enforced member limits
- Rate limiting requires delays between requests
- Violates Telegram ToS — use responsibly

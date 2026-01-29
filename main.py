#!/usr/bin/env python3
"""Telegram Group Scraper - CLI entry point."""

import argparse
import asyncio
import sys
from datetime import datetime

from scraper.client import get_client, resolve_group, get_group_info
from scraper.members import scrape_members
from scraper.messages import scrape_messages, sort_messages, filter_by_keywords
from scraper.combined import build_combined
from scraper.exporter import export_members, export_messages, export_combined


def parse_date(date_str):
    """Parse date string to date object."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        print(f"Error: Invalid date format '{date_str}'. Use YYYY-MM-DD")
        sys.exit(1)


async def cmd_info(args):
    """Show group info."""
    client = await get_client()
    
    try:
        entity = await resolve_group(client, args.group)
        info = await get_group_info(client, entity)
        
        print(f"\n{'='*40}")
        print(f"  {info['title']}")
        print(f"{'='*40}")
        print(f"  Type: {info['type']}")
        print(f"  ID: {info['id']}")
        if info['username']:
            print(f"  Username: @{info['username']}")
        if info['members_count']:
            print(f"  Members: {info['members_count']:,}")
        print(f"{'='*40}\n")
    
    except ValueError as e:
        print(f"Error: Could not find group '{args.group}'")
        print("Make sure you're a member of the group and the identifier is correct.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await client.disconnect()


async def cmd_members(args):
    """Scrape group members."""
    client = await get_client()
    
    try:
        print(f"Resolving group: {args.group}")
        entity = await resolve_group(client, args.group)
        info = await get_group_info(client, entity)
        
        print(f"Scraping members from: {info['title']}")
        if info['members_count']:
            print(f"Group has ~{info['members_count']:,} members")
        
        if args.limit:
            print(f"Limit: {args.limit} members")
        
        print()
        members = await scrape_members(client, entity, limit=args.limit)
        
        if not members:
            print("No members found (or no access).")
            return
        
        filepath = export_members(members, info['title'], output_dir=args.output)
        print(f"\nExported {len(members)} members to: {filepath}")
    
    except ValueError as e:
        print(f"Error: Could not find group '{args.group}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await client.disconnect()


async def cmd_messages(args):
    """Scrape group messages."""
    client = await get_client()
    
    try:
        print(f"Resolving group: {args.group}")
        entity = await resolve_group(client, args.group)
        info = await get_group_info(client, entity)
        
        print(f"Scraping messages from: {info['title']}")
        
        since = parse_date(args.since) if args.since else None
        until = parse_date(args.until) if args.until else None
        keywords = [kw.strip() for kw in args.keywords.split(',')] if args.keywords else None
        
        if args.limit:
            print(f"Limit: {args.limit} messages")
        if since:
            print(f"Since: {since}")
        if until:
            print(f"Until: {until}")
        if keywords:
            print(f"Keywords: {', '.join(keywords)}")
        
        print()
        messages = await scrape_messages(
            client, entity,
            limit=args.limit,
            since=since,
            until=until
        )
        
        if not messages:
            print("No messages found.")
            return
        
        # Filter by keywords if specified
        if keywords:
            original_count = len(messages)
            messages = filter_by_keywords(messages, keywords)
            print(f"\nFiltered: {len(messages)} of {original_count} messages match keywords")
        
        if not messages:
            print("No messages match the specified keywords.")
            return
        
        # Sort messages
        sort_label = "chronological" if args.chronological else "grouped by sender"
        print(f"Sorting: {sort_label}")
        messages = sort_messages(messages, chronological=args.chronological)
        
        filepath = export_messages(messages, info['title'], output_dir=args.output)
        print(f"Exported {len(messages)} messages to: {filepath}")
    
    except ValueError as e:
        print(f"Error: Could not find group '{args.group}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await client.disconnect()


async def cmd_combined(args):
    """Scrape members + messages and export a combined CSV."""
    client = await get_client()

    try:
        print(f"Resolving group: {args.group}")
        entity = await resolve_group(client, args.group)
        info = await get_group_info(client, entity)

        print(f"Scraping combined view from: {info['title']}")

        since = parse_date(args.since) if args.since else None
        until = parse_date(args.until) if args.until else None
        keywords = [kw.strip() for kw in args.keywords.split(',')] if args.keywords else None

        if args.limit:
            print(f"Limit: {args.limit} messages")
        if since:
            print(f"Since: {since}")
        if until:
            print(f"Until: {until}")
        if keywords:
            print(f"Keywords: {', '.join(keywords)}")

        print()
        members = await scrape_members(client, entity)
        messages = await scrape_messages(
            client, entity,
            limit=args.limit,
            since=since,
            until=until
        )

        if keywords and messages:
            original_count = len(messages)
            messages = filter_by_keywords(messages, keywords)
            print(f"\nFiltered: {len(messages)} of {original_count} messages match keywords")

        combined_rows = build_combined(members, messages)
        if not combined_rows:
            print("No data found to export.")
            return

        filepath = export_combined(combined_rows, info['title'], output_dir=args.output)
        print(f"Exported {len(combined_rows)} rows to: {filepath}")

    except ValueError:
        print(f"Error: Could not find group '{args.group}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await client.disconnect()


def cmd_examples(args):
    """Print usage examples."""
    print("""
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
""")


def main():
    parser = argparse.ArgumentParser(
        description='Telegram Group Scraper - Extract members and messages from Telegram groups',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run 'python main.py <command> --help' for command-specific options."
    )
    
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # info command
    info_parser = subparsers.add_parser(
        'info',
        help='Show group details without scraping'
    )
    info_parser.add_argument('group', help='Group: @username, invite link, or ID')
    
    # members command
    members_parser = subparsers.add_parser(
        'members',
        help='Scrape group member list to CSV'
    )
    members_parser.add_argument('group', help='Group: @username, invite link, or ID')
    members_parser.add_argument('--limit', type=int, help='Max members to fetch')
    members_parser.add_argument('--output', default='output', help='Output directory (default: output)')
    
    # messages command
    messages_parser = subparsers.add_parser(
        'messages',
        help='Scrape message history to CSV'
    )
    messages_parser.add_argument('group', help='Group: @username, invite link, or ID')
    messages_parser.add_argument('--limit', type=int, help='Max messages to fetch')
    messages_parser.add_argument('--since', help='Start date (YYYY-MM-DD)')
    messages_parser.add_argument('--until', help='End date (YYYY-MM-DD)')
    messages_parser.add_argument('--keywords', help='Filter by keywords (comma-separated)')
    messages_parser.add_argument('--chronological', action='store_true',
                                 help='Sort by time instead of grouping by sender')
    messages_parser.add_argument('--output', default='output', help='Output directory (default: output)')
    
    # combined command
    combined_parser = subparsers.add_parser(
        'combined',
        help='Export a combined per-user CSV (members + messages)'
    )
    combined_parser.add_argument('group', help='Group: @username, invite link, or ID')
    combined_parser.add_argument('--limit', type=int, help='Max messages to fetch')
    combined_parser.add_argument('--since', help='Start date (YYYY-MM-DD)')
    combined_parser.add_argument('--until', help='End date (YYYY-MM-DD)')
    combined_parser.add_argument('--keywords', help='Filter by keywords (comma-separated)')
    combined_parser.add_argument('--output', default='output', help='Output directory (default: output)')

    # examples command
    subparsers.add_parser('examples', help='Show usage examples')
    
    args = parser.parse_args()
    
    if args.command == 'examples':
        cmd_examples(args)
    elif args.command == 'info':
        asyncio.run(cmd_info(args))
    elif args.command == 'members':
        asyncio.run(cmd_members(args))
    elif args.command == 'messages':
        asyncio.run(cmd_messages(args))
    elif args.command == 'combined':
        asyncio.run(cmd_combined(args))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)

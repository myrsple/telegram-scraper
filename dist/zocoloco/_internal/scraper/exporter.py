"""CSV export utilities."""

import csv
import re
from pathlib import Path
from datetime import datetime


def _sanitize_filename(name):
    """Remove/replace characters that aren't safe for filenames."""
    # Replace spaces and special chars with underscores
    sanitized = re.sub(r'[^\w\-]', '_', name)
    # Collapse multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    return sanitized.strip('_')


def export_members(members, group_name, output_dir='output'):
    """
    Export member list to CSV.
    
    Returns:
        Path to created file
    """
    Path(output_dir).mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = _sanitize_filename(group_name)
    filename = f"{safe_name}_members_{timestamp}.csv"
    filepath = Path(output_dir) / filename
    
    fieldnames = [
        'user_id', 'username', 'first_name', 'last_name',
        'phone', 'is_bot', 'last_seen', 'is_premium', 'bio'
    ]
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(members)
    
    return filepath


def export_messages(messages, group_name, output_dir='output'):
    """
    Export messages to CSV.
    
    Returns:
        Path to created file
    """
    Path(output_dir).mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = _sanitize_filename(group_name)
    filename = f"{safe_name}_messages_{timestamp}.csv"
    filepath = Path(output_dir) / filename
    
    fieldnames = [
        'sender_id', 'sender_username', 'sender_name', 'message_id',
        'timestamp', 'text', 'reply_to_id', 'forward_from',
        'has_media', 'media_type'
    ]
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(messages)
    
    return filepath


def export_combined(rows, group_name, output_dir='output'):
    """
    Export combined per-user rows to CSV.

    Returns:
        Path to created file
    """
    Path(output_dir).mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = _sanitize_filename(group_name)
    filename = f"{safe_name}_combined_{timestamp}.csv"
    filepath = Path(output_dir) / filename

    fieldnames = [
        'user_id', 'username', 'first_name', 'last_name',
        'phone', 'bio', 'last_seen', 'is_premium', 'is_bot',
        'message_count', 'first_message_at', 'last_message_at',
        'recent_messages'
    ]

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return filepath

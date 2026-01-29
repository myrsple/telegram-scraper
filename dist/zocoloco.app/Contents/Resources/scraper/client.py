"""Telegram client initialization and authentication."""

import os
import sys
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from dotenv import load_dotenv, set_key


def load_credentials():
    """Load credentials from .env file, prompt if missing."""
    load_dotenv()
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    env_path = Path('.env')
    
    # Prompt for missing credentials
    if not api_id:
        print("\n=== Telegram API Setup ===")
        print("Get credentials at https://my.telegram.org/apps\n")
        api_id = input("API ID: ").strip()
        if not api_id.isdigit():
            print("Error: API ID must be a number")
            sys.exit(1)
        _save_to_env(env_path, 'TELEGRAM_API_ID', api_id)
    
    if not api_hash:
        api_hash = input("API Hash: ").strip()
        _save_to_env(env_path, 'TELEGRAM_API_HASH', api_hash)
    
    if not phone:
        phone = input("Phone number (with country code, e.g. +1234567890): ").strip()
        _save_to_env(env_path, 'TELEGRAM_PHONE', phone)
    
    return int(api_id), api_hash, phone


def _save_to_env(env_path, key, value):
    """Save a key-value pair to .env file."""
    if not env_path.exists():
        env_path.touch()
    set_key(str(env_path), key, value)


async def get_client():
    """Initialize and authenticate Telegram client."""
    api_id, api_hash, phone = load_credentials()
    
    client = TelegramClient('session', api_id, api_hash)
    await client.connect()
    
    if not await client.is_user_authorized():
        print(f"\nSending verification code to {phone}...")
        await client.send_code_request(phone)
        
        code = input("Enter the code you received: ").strip()
        
        try:
            await client.sign_in(phone, code)
        except PhoneCodeInvalidError:
            print("Error: Invalid code. Please try again.")
            await client.disconnect()
            sys.exit(1)
        except SessionPasswordNeededError:
            print("\nTwo-factor authentication is enabled.")
            password = input("Enter your 2FA password: ").strip()
            try:
                await client.sign_in(password=password)
            except Exception as e:
                print(f"Error: Authentication failed - {e}")
                await client.disconnect()
                sys.exit(1)
        
        print("Successfully authenticated!")
    
    return client


async def resolve_group(client, identifier):
    """
    Resolve a group identifier to a Telegram entity.
    
    Accepts:
        - @username
        - https://t.me/username
        - https://t.me/+invitecode
        - -100123456789 (numeric ID)
    """
    from telethon.tl.types import PeerChannel
    
    identifier = identifier.strip()
    
    # Handle numeric IDs
    if identifier.lstrip('-').isdigit():
        return await client.get_entity(PeerChannel(int(identifier)))
    
    # Handle all other formats (usernames, links)
    return await client.get_entity(identifier)


async def get_group_info(client, entity):
    """Get basic info about a group/channel."""
    from telethon.tl.types import Channel, Chat
    from telethon.tl.functions.channels import GetFullChannelRequest
    
    info = {
        'id': entity.id,
        'title': getattr(entity, 'title', 'Unknown'),
        'username': getattr(entity, 'username', None),
        'type': 'Unknown',
        'members_count': None,
    }
    
    if isinstance(entity, Channel):
        info['type'] = 'Channel' if entity.broadcast else 'Group'
        # Get participant count
        try:
            full_channel = await client(GetFullChannelRequest(entity))
            info['members_count'] = full_channel.full_chat.participants_count
        except Exception:
            pass
    elif isinstance(entity, Chat):
        info['type'] = 'Group'
        info['members_count'] = getattr(entity, 'participants_count', None)
    
    return info

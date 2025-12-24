#!/usr/bin/env python3
"""
Combined runner for Instagram DM Bot + Telegram Admin Bot
Runs both bots concurrently in a single process for Railway.
"""

import asyncio
import threading
import os
from dotenv import load_dotenv

load_dotenv()

def run_admin_bot():
    """Run the Telegram admin bot in a separate thread."""
    try:
        from admin_bot import main as admin_main
        admin_main()
    except Exception as e:
        print(f"[Admin Bot] Error: {e}")

async def run_instagram_bot():
    """Run the Instagram DM bot."""
    from wezaxy.test import test
    
    while True:
        use_proxy = os.getenv('USE_PROXY', 'false').lower() == 'true'
        username = os.getenv('IG_USERNAME')
        password = os.getenv('IG_PASSWORD')
        language = os.getenv('LANGUAGE')
        group_messages = os.getenv('GROUP_MESSAGES', 'false').lower() == 'true'

        if not username or not password or not language:
            print("Required information is empty in environment variables")
            break

        # Load knowledge base if it exists
        knowledge = ""
        if os.path.exists('knowledge.txt'):
            with open('knowledge.txt', 'r', encoding='utf-8') as kf:
                knowledge = kf.read().strip()

        if use_proxy:
            with open('proxies.txt', 'r') as proxy_file:
                proxies = proxy_file.read().splitlines()
            for proxy in proxies:
                result = await test(username, password, language, proxy, group_messages, knowledge)
                print("the last dm message that came in:", result)
        else:
            result = await test(username, password, language, None, group_messages, knowledge)
            print("the last dm message that came in:", result)
        
        if use_proxy is False:
            await asyncio.sleep(2)

def main():
    """Start both bots."""
    print("=" * 50)
    print("Starting Instagram DM Agent + Admin Bot")
    print("=" * 50)
    
    # Start admin bot in a separate thread (it has its own event loop)
    admin_token = os.getenv('TELEGRAM_ADMIN_BOT_TOKEN')
    if admin_token:
        admin_thread = threading.Thread(target=run_admin_bot, daemon=True)
        admin_thread.start()
        print("[Combined] Admin bot started in background thread")
    else:
        print("[Combined] No TELEGRAM_ADMIN_BOT_TOKEN, admin bot disabled")
    
    # Run Instagram bot in main thread
    print("[Combined] Starting Instagram DM bot...")
    asyncio.run(run_instagram_bot())

if __name__ == "__main__":
    main()

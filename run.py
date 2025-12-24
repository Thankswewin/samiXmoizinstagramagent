#!/usr/bin/env python3
"""
Combined runner for Instagram DM Bot + Telegram Admin Bot
Runs both bots concurrently in a single process for Railway.
"""

import asyncio
import threading
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def run_admin_bot_sync():
    """Run the Telegram admin bot in a separate thread with its own event loop."""
    import asyncio
    
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Import here to avoid issues
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
        
        # Import admin bot functions
        from admin_bot import (
            start, status, stats, persona, knowledge, setknowledge, 
            gif, restart, persona_callback, gif_callback, handle_text,
            load_config, save_config
        )
        from datetime import datetime
        
        token = os.getenv('TELEGRAM_ADMIN_BOT_TOKEN')
        if not token:
            print("[Admin Bot] No token found")
            return
            
        print("[Admin Bot] Starting...")
        
        # Initialize config if first run
        config = load_config()
        if not config.get('started_at'):
            config['started_at'] = datetime.now().isoformat()
            save_config(config)
        
        # Create application
        app = Application.builder().token(token).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("status", status))
        app.add_handler(CommandHandler("stats", stats))
        app.add_handler(CommandHandler("persona", persona))
        app.add_handler(CommandHandler("knowledge", knowledge))
        app.add_handler(CommandHandler("setknowledge", setknowledge))
        app.add_handler(CommandHandler("gif", gif))
        app.add_handler(CommandHandler("restart", restart))
        
        # Callback handlers
        app.add_handler(CallbackQueryHandler(persona_callback, pattern="^persona_"))
        app.add_handler(CallbackQueryHandler(gif_callback, pattern="^gif_"))
        
        # Text handler for setknowledge flow
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        print("[Admin Bot] Running!")
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"[Admin Bot] Error: {e}")
        import traceback
        traceback.print_exc()

async def run_instagram_bot():
    """Run the Instagram DM bot."""
    from wezaxy.test import test
    
    while True:
        try:
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
        except Exception as e:
            print(f"[Instagram Bot] Error: {e}")
            await asyncio.sleep(5)

def main():
    """Start both bots."""
    print("=" * 50)
    print("Starting Instagram DM Agent + Admin Bot")
    print("=" * 50)
    
    # Start admin bot in a separate thread (it creates its own event loop)
    admin_token = os.getenv('TELEGRAM_ADMIN_BOT_TOKEN')
    if admin_token:
        admin_thread = threading.Thread(target=run_admin_bot_sync, daemon=True)
        admin_thread.start()
        print("[Combined] Admin bot started in background thread")
    else:
        print("[Combined] No TELEGRAM_ADMIN_BOT_TOKEN, admin bot disabled")
    
    # Small delay to let admin bot initialize
    import time
    time.sleep(2)
    
    # Run Instagram bot in main thread
    print("[Combined] Starting Instagram DM bot...")
    asyncio.run(run_instagram_bot())

if __name__ == "__main__":
    main()

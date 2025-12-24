#!/usr/bin/env python3
"""
Combined runner for Instagram DM Bot + Telegram Admin Bot
Runs both bots concurrently in a single process for Railway.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

async def run_admin_bot_async():
    """Run the Telegram admin bot asynchronously."""
    try:
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
        
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
        
        # Use initialize + start + stop pattern instead of run_polling
        # This avoids the signal handler issue
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        
        # Keep running forever
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour, loop will be cancelled on shutdown
            
    except asyncio.CancelledError:
        print("[Admin Bot] Shutting down...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
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

async def main():
    """Start both bots concurrently."""
    print("=" * 50)
    print("Starting Instagram DM Agent + Admin Bot")
    print("=" * 50)
    
    tasks = []
    
    # Start admin bot if token is set
    admin_token = os.getenv('TELEGRAM_ADMIN_BOT_TOKEN')
    if admin_token:
        tasks.append(asyncio.create_task(run_admin_bot_async()))
        print("[Combined] Admin bot task created")
    else:
        print("[Combined] No TELEGRAM_ADMIN_BOT_TOKEN, admin bot disabled")
    
    # Start Instagram bot
    print("[Combined] Starting Instagram DM bot...")
    tasks.append(asyncio.create_task(run_instagram_bot()))
    
    # Wait for all tasks
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

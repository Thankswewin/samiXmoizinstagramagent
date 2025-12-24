#!/usr/bin/env python3
"""
Telegram Admin Bot for Instagram DM Agent
Allows remote management of the Instagram bot via Telegram commands.
"""

import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Config file path
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agent_config.json')
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

# Default config
DEFAULT_CONFIG = {
    "active_persona": "custom",
    "custom_knowledge": "",
    "gif_enabled": True,
    "gif_chance": 0.15,
    "started_at": None,
    "messages_sent": 0
}

def load_config():
    """Load agent config from file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save agent config to file."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

def get_available_templates():
    """Get list of available persona templates."""
    templates = {}
    if os.path.exists(TEMPLATES_DIR):
        for filename in os.listdir(TEMPLATES_DIR):
            if filename.startswith('knowledge_') and filename.endswith('.txt'):
                name = filename.replace('knowledge_', '').replace('.txt', '')
                filepath = os.path.join(TEMPLATES_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    templates[name] = f.read().strip()
    return templates

def get_knowledge_content():
    """Get current knowledge.txt content."""
    knowledge_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knowledge.txt')
    if os.path.exists(knowledge_file):
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return ""

def set_knowledge_content(content):
    """Update knowledge.txt content."""
    knowledge_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knowledge.txt')
    with open(knowledge_file, 'w', encoding='utf-8') as f:
        f.write(content)

def is_admin(user_id):
    """Check if user is admin."""
    admin_id = os.getenv('ADMIN_USER_ID', '')
    if not admin_id:
        return True  # If no admin set, allow everyone (not recommended)
    return str(user_id) == str(admin_id)

# === COMMAND HANDLERS ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    print(f"[Admin Bot] /start from {user.username} (ID: {user.id})")
    if not is_admin(update.effective_user.id):
        print(f"[Admin Bot] Unauthorized user: {user.id}")
        await update.message.reply_text("⛔ Unauthorized")
        return
    
    welcome = """
🤖 *Instagram Agent Admin Panel*

Available commands:

📊 *Status & Info*
/status - View current config
/stats - View message stats

🎭 *Persona Management*
/persona - Switch persona
/knowledge - View current knowledge
/setknowledge - Update knowledge

⚙️ *Settings*
/gif - Toggle GIF reactions
/restart - Force re-login

Type any command to get started!
"""
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    print(f"[Admin Bot] /status from {update.effective_user.id}")
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized")
        return
    
    config = load_config()
    ig_user = os.getenv('IG_USERNAME', 'Not set')
    use_proxy = os.getenv('USE_PROXY', 'false')
    language = os.getenv('LANGUAGE', 'english')
    
    status_text = f"""
📊 *Agent Status*

*Instagram Account:* `{ig_user}`
*Language:* {language}
*Proxy:* {'✅ Enabled' if use_proxy.lower() == 'true' else '❌ Disabled'}

*Active Persona:* {config.get('active_persona', 'custom')}
*GIF Reactions:* {'✅ On' if config.get('gif_enabled', True) else '❌ Off'}
*GIF Chance:* {int(config.get('gif_chance', 0.15) * 100)}%
"""
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized")
        return
    
    config = load_config()
    started = config.get('started_at')
    messages = config.get('messages_sent', 0)
    
    if started:
        try:
            start_time = datetime.fromisoformat(started)
            uptime = datetime.now() - start_time
            uptime_str = f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m"
        except:
            uptime_str = "Unknown"
    else:
        uptime_str = "Not started"
    
    stats_text = f"""
📈 *Agent Statistics*

*Uptime:* {uptime_str}
*Messages Sent:* {messages}
"""
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def persona(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /persona command - show persona selection."""
    print(f"[Admin Bot] /persona from {update.effective_user.id}")
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized")
        return
    
    templates = get_available_templates()
    config = load_config()
    current = config.get('active_persona', 'custom')
    
    keyboard = []
    for name in templates.keys():
        emoji = "✅" if name == current else "⚪"
        keyboard.append([InlineKeyboardButton(f"{emoji} {name.title()}", callback_data=f"persona_{name}")])
    keyboard.append([InlineKeyboardButton("✏️ Custom", callback_data="persona_custom")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🎭 *Select Persona*\n\nCurrent: *{current.title()}*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def persona_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle persona selection callback."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    persona_name = query.data.replace("persona_", "")
    config = load_config()
    
    if persona_name == "custom":
        config['active_persona'] = 'custom'
        save_config(config)
        print(f"[Admin Bot] Persona switched to: custom")
        await query.edit_message_text("✅ Switched to *Custom* persona.\n\nUse /setknowledge to update the knowledge base.", parse_mode='Markdown')
    else:
        templates = get_available_templates()
        if persona_name in templates:
            # Update knowledge.txt with template content
            set_knowledge_content(templates[persona_name])
            config['active_persona'] = persona_name
            save_config(config)
            print(f"[Admin Bot] Persona switched to: {persona_name}")
            await query.edit_message_text(f"✅ Switched to *{persona_name.title()}* persona!\n\nKnowledge base updated.", parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ Template not found")

async def knowledge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /knowledge command - show current knowledge."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized")
        return
    
    content = get_knowledge_content()
    if len(content) > 3500:
        content = content[:3500] + "...\n\n_(truncated)_"
    
    await update.message.reply_text(
        f"📚 *Current Knowledge Base*\n\n```\n{content}\n```",
        parse_mode='Markdown'
    )

async def setknowledge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setknowledge command."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized")
        return
    
    # Check if knowledge was provided with command
    if context.args:
        new_knowledge = ' '.join(context.args)
        set_knowledge_content(new_knowledge)
        config = load_config()
        config['active_persona'] = 'custom'
        save_config(config)
        await update.message.reply_text("✅ Knowledge base updated!")
    else:
        context.user_data['awaiting_knowledge'] = True
        await update.message.reply_text(
            "📝 *Send me the new knowledge base*\n\nType or paste the knowledge text in your next message.",
            parse_mode='Markdown'
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (for setknowledge flow)."""
    if not is_admin(update.effective_user.id):
        return
    
    if context.user_data.get('awaiting_knowledge'):
        new_knowledge = update.message.text
        set_knowledge_content(new_knowledge)
        config = load_config()
        config['active_persona'] = 'custom'
        save_config(config)
        context.user_data['awaiting_knowledge'] = False
        await update.message.reply_text("✅ Knowledge base updated!")

async def gif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /gif command - toggle GIF reactions."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized")
        return
    
    config = load_config()
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Enable", callback_data="gif_on"),
            InlineKeyboardButton("❌ Disable", callback_data="gif_off")
        ],
        [
            InlineKeyboardButton("10%", callback_data="gif_10"),
            InlineKeyboardButton("15%", callback_data="gif_15"),
            InlineKeyboardButton("25%", callback_data="gif_25"),
        ]
    ]
    
    status = "On" if config.get('gif_enabled', True) else "Off"
    chance = int(config.get('gif_chance', 0.15) * 100)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🎬 *GIF Settings*\n\nStatus: *{status}*\nChance: *{chance}%*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def gif_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle GIF settings callback."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    config = load_config()
    action = query.data.replace("gif_", "")
    
    if action == "on":
        config['gif_enabled'] = True
    elif action == "off":
        config['gif_enabled'] = False
    elif action in ["10", "15", "25"]:
        config['gif_chance'] = int(action) / 100
    
    save_config(config)
    
    status = "On" if config.get('gif_enabled', True) else "Off"
    chance = int(config.get('gif_chance', 0.15) * 100)
    
    await query.edit_message_text(
        f"✅ *GIF Settings Updated*\n\nStatus: *{status}*\nChance: *{chance}%*",
        parse_mode='Markdown'
    )

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /restart command - force re-login."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized")
        return
    
    # Delete Authorization.json to force re-login
    auth_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wezaxy', 'Authorization.json')
    if os.path.exists(auth_file):
        os.remove(auth_file)
        await update.message.reply_text("🔄 Authorization cleared. Bot will re-login on next message.")
    else:
        await update.message.reply_text("ℹ️ No authorization file found.")

def main():
    """Start the admin bot."""
    token = os.getenv('TELEGRAM_ADMIN_BOT_TOKEN')
    if not token:
        print("[Admin Bot] TELEGRAM_ADMIN_BOT_TOKEN not set, admin bot disabled")
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

if __name__ == "__main__":
    main()

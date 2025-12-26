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

# Availability modes with delay ranges (min, max in seconds)
MODES = {
    "available": {"emoji": "🟢", "min_delay": 10, "max_delay": 60, "auto_reply": True},
    "busy": {"emoji": "🟡", "min_delay": 120, "max_delay": 480, "auto_reply": True},
    "away": {"emoji": "🟠", "min_delay": 600, "max_delay": 1800, "auto_reply": True},
    "sleep": {"emoji": "🔴", "min_delay": 0, "max_delay": 0, "auto_reply": False},
    "dnd": {"emoji": "⛔", "min_delay": 0, "max_delay": 0, "auto_reply": False}
}

# Default config
DEFAULT_CONFIG = {
    "active_persona": "custom",
    "custom_knowledge": "",
    "gif_enabled": True,
    "gif_chance": 0.15,
    "started_at": None,
    "messages_sent": 0,
    # Availability mode settings
    "current_mode": "available",
    "message_queue": [],
    "skipped_threads": []
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
    
    config = load_config()
    mode = config.get('current_mode', 'available')
    mode_emoji = MODES.get(mode, {}).get('emoji', '🟢')
    
    welcome = f"""
🤖 *Instagram Agent Admin Panel*

*Current Mode:* {mode_emoji} {mode.title()}

Available commands:

🎯 *Availability*
/mode - Switch availability mode
/queue - View pending messages
/wakeup - Reply to all queued

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

async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mode command - show/switch availability mode."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized")
        return
    
    config = load_config()
    current = config.get('current_mode', 'available')
    
    # Build keyboard with all modes
    keyboard = []
    for mode_name, mode_info in MODES.items():
        emoji = "✅" if mode_name == current else mode_info['emoji']
        label = f"{emoji} {mode_name.title()}"
        if mode_info['auto_reply']:
            label += f" ({mode_info['min_delay']//60}-{mode_info['max_delay']//60}m)"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"mode_{mode_name}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    current_info = MODES.get(current, {})
    status_text = f"""
🎯 *Availability Mode*

Current: {current_info.get('emoji', '🟢')} *{current.title()}*
Auto-reply: {'✅ On' if current_info.get('auto_reply', True) else '❌ Off'}
Delay: {current_info.get('min_delay', 0)//60}-{current_info.get('max_delay', 0)//60} minutes

Select a mode:
"""
    await update.message.reply_text(status_text, reply_markup=reply_markup, parse_mode='Markdown')

async def mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mode selection callback."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    mode_name = query.data.replace("mode_", "")
    if mode_name not in MODES:
        await query.edit_message_text("❌ Invalid mode")
        return
    
    config = load_config()
    config['current_mode'] = mode_name
    save_config(config)
    
    mode_info = MODES[mode_name]
    print(f"[Admin Bot] Mode switched to: {mode_name}")
    
    if mode_info['auto_reply']:
        desc = f"Replies in {mode_info['min_delay']//60}-{mode_info['max_delay']//60} minutes"
    else:
        desc = "Messages will be queued"
    
    await query.edit_message_text(
        f"✅ Mode changed to {mode_info['emoji']} *{mode_name.title()}*\n\n{desc}",
        parse_mode='Markdown'
    )

async def queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /queue command - show pending messages."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized")
        return
    
    config = load_config()
    message_queue = config.get('message_queue', [])
    
    if not message_queue:
        await update.message.reply_text("📭 *Queue Empty*\n\nNo pending messages.", parse_mode='Markdown')
        return
    
    queue_text = f"📬 *Message Queue* ({len(message_queue)} pending)\n\n"
    for i, msg in enumerate(message_queue[:10]):  # Show max 10
        user = msg.get('user', 'Unknown')
        text = msg.get('message', '')[:30] + "..." if len(msg.get('message', '')) > 30 else msg.get('message', '')
        reply_at = msg.get('reply_at', 'Unknown')
        queue_text += f"{i+1}. *{user}*: {text}\n   ⏰ Reply at: {reply_at}\n\n"
    
    if len(message_queue) > 10:
        queue_text += f"_...and {len(message_queue) - 10} more_"
    
    await update.message.reply_text(queue_text, parse_mode='Markdown')

async def wakeup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /wakeup command - process all queued messages immediately."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized")
        return
    
    config = load_config()
    message_queue = config.get('message_queue', [])
    queue_count = len(message_queue)
    
    if queue_count == 0:
        await update.message.reply_text("📭 No messages in queue.")
        return
    
    # Mark all messages to be replied immediately
    from datetime import datetime
    now = datetime.now().isoformat()
    for msg in message_queue:
        msg['reply_at'] = now
    
    config['message_queue'] = message_queue
    save_config(config)
    
    await update.message.reply_text(
        f"⏰ *Waking up!*\n\n{queue_count} messages will be replied to shortly.",
        parse_mode='Markdown'
    )

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /skip command - skip a queued message."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /skip <queue_number>\n\nUse /queue to see message numbers.")
        return
    
    try:
        idx = int(context.args[0]) - 1
    except ValueError:
        await update.message.reply_text("❌ Invalid number")
        return
    
    config = load_config()
    message_queue = config.get('message_queue', [])
    
    if idx < 0 or idx >= len(message_queue):
        await update.message.reply_text("❌ Message not found in queue")
        return
    
    removed = message_queue.pop(idx)
    config['message_queue'] = message_queue
    save_config(config)
    
    await update.message.reply_text(
        f"✅ Skipped message from *{removed.get('user', 'Unknown')}*",
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
    # Availability mode commands
    app.add_handler(CommandHandler("mode", mode))
    app.add_handler(CommandHandler("queue", queue))
    app.add_handler(CommandHandler("wakeup", wakeup))
    app.add_handler(CommandHandler("skip", skip))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(persona_callback, pattern="^persona_"))
    app.add_handler(CallbackQueryHandler(gif_callback, pattern="^gif_"))
    app.add_handler(CallbackQueryHandler(mode_callback, pattern="^mode_"))
    
    # Text handler for setknowledge flow
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("[Admin Bot] Running!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

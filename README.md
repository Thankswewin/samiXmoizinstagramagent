# 🤖 Instagram AI DM Auto-Responder Pro

**The Ultimate AI-Powered Instagram DM Automation Tool**

Automatically respond to Instagram Direct Messages with intelligent, human-like AI responses. Built for businesses, influencers, and anyone who wants 24/7 automated customer engagement.

> 📦 **Get this tool exclusively from [@samiXmoiz_bot](https://t.me/samiXmoiz_bot)**

---

## ✨ Features

### Core Features
- **🤖 AI-Powered Responses** — Uses ChatGPT to generate intelligent, context-aware replies
- **💬 Auto-Reply to DMs** — Automatically reads and responds to all incoming messages
- **🔄 Proxy Support** — Use proxy servers for safe, anonymous operation
- **👥 Group Message Control** — Enable or disable responses to group chats

### Advanced Features (NEW!)
- **📝 Knowledge Base System** — Train the AI with your business info, pricing, and FAQs
- **⌨️ Real-Time Typing Indicator** — Shows "typing..." to recipients for a human-like experience
- **⏱️ Dynamic Response Timing** — Simulates realistic human typing speed based on message length
- **😎 Casual Persona Mode** — AI responds in a natural, friendly tone with emojis
- **🔒 Secure `.env` Configuration** — Keep your credentials safe and organized

---

## 🎯 Who Is This For?

### 💼 Business & E-Commerce
Perfect for brands handling customer inquiries 24/7:
- Answer product questions automatically
- Provide pricing and availability info
- Handle support requests while you sleep
- Professional yet friendly tone

### 💕 Dating & Social
Ultra-human responses for personal accounts:
- Flirty, playful conversation style
- Natural emoji usage and lowercase text
- Keeps conversations engaging
- Mirrors the other person's energy

### 📢 Marketing & Promotion
Ideal for promoting products, crypto, or services:
- Casual, relatable messaging
- Creates curiosity and FOMO
- Handles objections smoothly
- Subtle but effective call-to-actions

> 📁 **Pre-made templates included!** Check the `templates/` folder for ready-to-use knowledge bases.

---

## 🚀 Quick Start

### Option 1: Easy Setup Wizard (Recommended)

Run the interactive setup wizard — it guides you through everything:

```bash
python setup.py
```

The wizard will:
1. ✅ Install all dependencies
2. ✅ Ask for your Instagram credentials
3. ✅ Let you choose your use case (Business/Dating/Promo)
4. ✅ Configure everything automatically
5. ✅ Start the bot for you

---

### Option 2: Manual Setup

If you prefer to configure manually:
   ```bash
   python install.py
   ```

2. **Configure Your Credentials**:
   
   Edit the `.env` file:
   ```env
   IG_USERNAME=your_instagram_username
   IG_PASSWORD=your_instagram_password
   LANGUAGE=english
   USE_PROXY=false
   GROUP_MESSAGES=false
   ```

3. **Set Up Your Knowledge Base** (Optional):
   
   Edit `knowledge.txt` to train the AI with your info:
   ```
   I run a photography business. 
   Prices start at $50 per session.
   We're based in NYC and available on weekends.
   Payment via PayPal or Crypto.
   ```

4. **Add Proxies** (Optional):
   
   Add proxies to `proxies.txt`:
   ```
   username:password@proxy_host:port
   ```

5. **Run the Bot**:
   ```bash
   python main.py
   ```

---

## ⚙️ Configuration

### `.env` File Options

| Variable | Description | Values |
|----------|-------------|--------|
| `IG_USERNAME` | Your Instagram username or email | String |
| `IG_PASSWORD` | Your Instagram password | String |
| `LANGUAGE` | Language for AI responses | `english`, `spanish`, etc. |
| `USE_PROXY` | Enable proxy rotation | `true` / `false` |
| `GROUP_MESSAGES` | Respond to group chats | `true` / `false` |

### `knowledge.txt` — AI Training

Write anything you want the AI to know about your business:
- Your services and pricing
- Business hours and location
- FAQs and common responses
- Your brand personality and tone

The AI will use this context to provide accurate, personalized responses.

---

## 🎯 How It Works

1. **Login** → Bot securely logs into your Instagram account
2. **Monitor** → Continuously checks your DM inbox for new messages
3. **Detect** → Identifies incoming messages from other users
4. **Type** → Shows "typing..." indicator to the sender
5. **Generate** → AI creates a personalized response using your knowledge base
6. **Send** → Delivers the response with realistic human-like timing

---

## 📁 File Structure

```
├── setup.py             # 🆕 Interactive setup wizard
├── main.py              # Main bot entry point
├── install.py           # Dependency installer
├── .env                 # Your credentials (keep private!)
├── knowledge.txt        # AI training data
├── proxies.txt          # Proxy list (optional)
├── config.json          # Legacy config (deprecated)
├── templates/           # Pre-made knowledge base templates
│   ├── knowledge_business.txt    # For customer support
│   ├── knowledge_dating.txt      # For dating/social
│   └── knowledge_shilling.txt    # For promotion/marketing
└── wezaxy/              # Core bot modules
    ├── ai.py            # ChatGPT integration
    ├── test.py          # DM processing logic
    ├── login.py         # Instagram authentication
    ├── sendmessage.py   # Message sending
    └── Authorization.json # Session tokens
```

---

## ⚠️ Important Notes

- **Use a secondary account** — Recommended for safety
- **Respect Instagram's ToS** — Avoid spammy behavior
- **Keep credentials private** — Never share your `.env` file
- **Use quality proxies** — Residential proxies recommended

---

## 📞 Support & Purchase

**Get the full package with support from:**

🤖 **Telegram Bot:** [@samiXmoiz_bot](https://t.me/samiXmoiz_bot)

---

## 📜 License

This software is provided as-is for personal use. Redistribution or resale without permission is prohibited.

**© 2024 samiXmoiz — All Rights Reserved**

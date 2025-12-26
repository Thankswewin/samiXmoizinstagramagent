import asyncio, aiohttp, time, uuid, json, threading, os, random, base64, re
from datetime import datetime, timedelta
from wezaxy.sendmessage import mesj
from wezaxy.login import login
from wezaxy.ai import gpt4o, gpt4o_with_image
from wezaxy.sendgif import should_send_gif, get_random_gif, send_gif_async

# Track processed message IDs to avoid double-responding
_processed_items = set()

# Availability modes configuration
MODES = {
    "available": {"min_delay": 10, "max_delay": 60, "auto_reply": True},
    "busy": {"min_delay": 120, "max_delay": 480, "auto_reply": True},
    "away": {"min_delay": 600, "max_delay": 1800, "auto_reply": True},
    "sleep": {"min_delay": 0, "max_delay": 0, "auto_reply": False},
    "dnd": {"min_delay": 0, "max_delay": 0, "auto_reply": False}
}

def load_agent_config():
    """Load agent config for mode settings."""
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agent_config.json')
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"current_mode": "available", "message_queue": [], "skipped_threads": []}

def save_agent_config(config):
    """Save agent config."""
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agent_config.json')
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"[Config] Error saving config: {e}")

def get_current_mode():
    """Get the current availability mode settings."""
    config = load_agent_config()
    mode_name = config.get('current_mode', 'available')
    return mode_name, MODES.get(mode_name, MODES['available'])

def calculate_reply_delay():
    """Calculate a random delay based on current mode."""
    mode_name, mode_settings = get_current_mode()
    if not mode_settings.get('auto_reply', True):
        return None  # No auto-reply in this mode
    
    min_delay = mode_settings.get('min_delay', 10)
    max_delay = mode_settings.get('max_delay', 60)
    delay = random.uniform(min_delay, max_delay)
    return delay

def add_to_queue(thread_id, user, message, reply_delay=None):
    """Add a message to the queue for delayed processing."""
    config = load_agent_config()
    queue = config.get('message_queue', [])
    
    # Calculate when to reply
    if reply_delay is not None:
        reply_at = (datetime.now() + timedelta(seconds=reply_delay)).isoformat()
    else:
        reply_at = None  # Will be set by /wakeup command
    
    queue.append({
        "thread_id": str(thread_id),
        "user": str(user),
        "message": message[:200],  # Truncate for storage
        "timestamp": datetime.now().isoformat(),
        "reply_at": reply_at
    })
    
    config['message_queue'] = queue
    save_agent_config(config)
    print(f"[Queue] Added message from {user} - reply at {reply_at}")

def get_ready_messages():
    """Get messages that are ready to be processed (reply_at has passed)."""
    config = load_agent_config()
    queue = config.get('message_queue', [])
    now = datetime.now()
    
    ready = []
    remaining = []
    
    for msg in queue:
        reply_at = msg.get('reply_at')
        if reply_at is None:
            remaining.append(msg)  # Not scheduled yet
            continue
        
        try:
            reply_time = datetime.fromisoformat(reply_at)
            if reply_time <= now:
                ready.append(msg)
            else:
                remaining.append(msg)
        except:
            remaining.append(msg)
    
    # Update queue with remaining messages
    if ready:
        config['message_queue'] = remaining
        save_agent_config(config)
    
    return ready

# GitHub Gist for dynamic token storage (no Railway redeploy needed!)
GIST_ID = os.getenv('GITHUB_GIST_ID')  # Will be set after first upload
GITHUB_TOKEN = os.getenv('GITHUB_GIST_TOKEN')

async def upload_token_to_gist(auth_token, user_id):
    """Upload Instagram token to GitHub Gist for Railway to fetch."""
    global GIST_ID
    import aiohttp
    
    github_token = os.getenv('GITHUB_GIST_TOKEN')
    if not github_token:
        print("[Gist] No GITHUB_GIST_TOKEN set, skipping upload")
        return False
    
    gist_content = json.dumps({
        "auth": auth_token,
        "myuserid": str(user_id),
        "updated_at": datetime.now().isoformat()
    })
    
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    gist_id = os.getenv('GITHUB_GIST_ID')
    
    try:
        async with aiohttp.ClientSession() as session:
            if gist_id:
                # Update existing gist
                url = f"https://api.github.com/gists/{gist_id}"
                payload = {
                    "files": {
                        "instagram_token.json": {"content": gist_content}
                    }
                }
                async with session.patch(url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        print(f"[Gist] ✅ Token uploaded to Gist {gist_id}")
                        return True
                    else:
                        error = await resp.text()
                        print(f"[Gist] Update failed: {resp.status} - {error[:200]}")
            else:
                # Create new gist
                url = "https://api.github.com/gists"
                payload = {
                    "description": "Instagram DM Bot Token (auto-updated)",
                    "public": False,
                    "files": {
                        "instagram_token.json": {"content": gist_content}
                    }
                }
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status == 201:
                        data = await resp.json()
                        new_gist_id = data.get("id")
                        print(f"[Gist] ✅ Created new Gist: {new_gist_id}")
                        print(f"[Gist] ⚠️ Add this to Railway env vars: GITHUB_GIST_ID={new_gist_id}")
                        GIST_ID = new_gist_id
                        return True
                    else:
                        error = await resp.text()
                        print(f"[Gist] Create failed: {resp.status} - {error[:200]}")
    except Exception as e:
        print(f"[Gist] Error: {e}")
    
    return False

async def fetch_token_from_gist():
    """Fetch Instagram token from GitHub Gist (used by Railway)."""
    import aiohttp
    
    gist_id = os.getenv('GITHUB_GIST_ID')
    github_token = os.getenv('GITHUB_GIST_TOKEN')
    
    if not gist_id:
        print("[Gist] No GITHUB_GIST_ID set")
        return None
    
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.github.com/gists/{gist_id}"
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data.get("files", {}).get("instagram_token.json", {}).get("content")
                    if content:
                        token_data = json.loads(content)
                        print(f"[Gist] ✅ Fetched token (updated: {token_data.get('updated_at', 'unknown')})")
                        return token_data
                else:
                    print(f"[Gist] Fetch failed: {resp.status}")
    except Exception as e:
        print(f"[Gist] Fetch error: {e}")
    
    return None

# Track when we last sent a token alert (avoid spam)
_last_token_alert = None

async def notify_token_expired():
    """Send Telegram notification when Instagram token expires."""
    global _last_token_alert
    import aiohttp
    
    # Only alert once per hour to avoid spam
    now = datetime.now()
    if _last_token_alert and (now - _last_token_alert).seconds < 3600:
        return
    
    token = os.getenv('TELEGRAM_ADMIN_BOT_TOKEN')
    admin_id = os.getenv('ADMIN_USER_ID')
    
    if not token or not admin_id:
        print("[Alert] Can't send Telegram alert - missing TELEGRAM_ADMIN_BOT_TOKEN or ADMIN_USER_ID")
        return
    
    message = """⚠️ *Instagram Token Expired!*

Your IG_AUTH_TOKEN is no longer valid.

To fix:
1. Run the bot locally
2. It will generate a new token
3. Copy IG_AUTH_TOKEN and IG_USER_ID to Railway env vars

_Bot will continue trying with current token._"""
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        async with aiohttp.ClientSession() as session:
            await session.post(url, json={
                "chat_id": admin_id,
                "text": message,
                "parse_mode": "Markdown"
            })
        _last_token_alert = now
        print("[Alert] Token expiry notification sent to Telegram")
    except Exception as e:
        print(f"[Alert] Failed to send Telegram notification: {e}")

async def sync_token_to_railway(auth_token, user_id):
    """
    Sync new Instagram token to Railway automatically.
    
    Requires these environment variables:
    - RAILWAY_API_TOKEN: Your Railway API token (from Railway dashboard -> Account -> Tokens)
    - RAILWAY_PROJECT_ID: Your Railway project ID
    - RAILWAY_SERVICE_ID: Your Railway service ID (optional, will find if not provided)
    - TELEGRAM_ADMIN_BOT_TOKEN: For sending confirmation via Telegram
    - ADMIN_USER_ID: Your Telegram user ID
    """
    import aiohttp
    
    railway_token = os.getenv('RAILWAY_API_TOKEN')
    project_id = os.getenv('RAILWAY_PROJECT_ID')
    service_id = os.getenv('RAILWAY_SERVICE_ID')
    telegram_token = os.getenv('TELEGRAM_ADMIN_BOT_TOKEN')
    admin_id = os.getenv('ADMIN_USER_ID')
    
    success_railway = False
    
    # Try Railway API sync first
    if railway_token and project_id:
        try:
            # Railway uses GraphQL API
            graphql_url = "https://backboard.railway.app/graphql/v2"
            headers = {
                "Authorization": f"Bearer {railway_token}",
                "Content-Type": "application/json"
            }
            
            # If no service_id, we need to get it first
            if not service_id:
                query = """
                query GetProject($projectId: String!) {
                    project(id: $projectId) {
                        services {
                            edges {
                                node {
                                    id
                                    name
                                }
                            }
                        }
                    }
                }
                """
                async with aiohttp.ClientSession() as session:
                    async with session.post(graphql_url, headers=headers, json={
                        "query": query,
                        "variables": {"projectId": project_id}
                    }) as resp:
                        data = await resp.json()
                        services = data.get("data", {}).get("project", {}).get("services", {}).get("edges", [])
                        if services:
                            service_id = services[0]["node"]["id"]
                            print(f"[Railway] Found service ID: {service_id}")
            
            if service_id:
                # Update environment variables
                mutation = """
                mutation UpdateVariables($input: VariableCollectionUpsertInput!) {
                    variableCollectionUpsert(input: $input)
                }
                """
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(graphql_url, headers=headers, json={
                        "query": mutation,
                        "variables": {
                            "input": {
                                "projectId": project_id,
                                "serviceId": service_id,
                                "variables": {
                                    "IG_AUTH_TOKEN": auth_token,
                                    "IG_USER_ID": user_id
                                }
                            }
                        }
                    }) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if not data.get("errors"):
                                success_railway = True
                                print("[Railway] ✅ Environment variables updated successfully!")
                            else:
                                print(f"[Railway] API Error: {data.get('errors')}")
                        else:
                            print(f"[Railway] HTTP Error: {resp.status}")
                            
        except Exception as e:
            print(f"[Railway] Failed to sync: {e}")
    else:
        print("[Railway] Skipping auto-sync - missing RAILWAY_API_TOKEN or RAILWAY_PROJECT_ID")
    
    # Always send via Telegram as backup/confirmation
    if telegram_token and admin_id:
        try:
            if success_railway:
                message = f"""✅ *Instagram Token Auto-Synced to Railway!*

The new token has been automatically pushed to Railway.
Your bot should restart automatically.

*Token:*
`{auth_token[:50]}...`

*User ID:*
`{user_id}`"""
            else:
                message = f"""🔑 *New Instagram Token Generated*

Railway auto-sync {'failed' if railway_token else 'not configured'}.
Please copy these to Railway manually:

*IG_AUTH_TOKEN:*
```
{auth_token}
```

*IG_USER_ID:*
```
{user_id}
```

_Tip: Add RAILWAY_API_TOKEN, RAILWAY_PROJECT_ID to .env for auto-sync_"""
            
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            async with aiohttp.ClientSession() as session:
                await session.post(url, json={
                    "chat_id": admin_id,
                    "text": message,
                    "parse_mode": "Markdown"
                })
            print("[Telegram] Token notification sent!")
        except Exception as e:
            print(f"[Telegram] Failed to send notification: {e}")
    
    return success_railway

def smart_split_message(message):
    """
    Intelligently split a message into human-like chunks.
    
    The logic is DYNAMIC:
    - Very short messages (< 30 chars): Never split
    - Single sentence: Usually don't split
    - Multiple sentences: Sometimes split (based on length and content)
    - Very long messages: More likely to split
    - Questions: Less likely to split
    - Casual vibes (lol, haha): More likely to split after them
    """
    message = message.strip()
    
    # Never split very short messages
    if len(message) < 30:
        return [message]
    
    # Count sentences
    sentences = re.split(r'(?<=[.!?])\s+', message)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Single sentence - usually don't split (80% keep whole)
    if len(sentences) <= 1:
        return [message]
    
    # 2 sentences and short total - 70% keep whole
    if len(sentences) == 2 and len(message) < 80:
        if random.random() < 0.7:
            return [message]
    
    # Questions tend to stay whole (they need context)
    if message.count('?') >= 2:
        if random.random() < 0.6:
            return [message]
    
    # Long messages (> 120 chars) - more likely to split (70%)
    if len(message) > 120:
        should_split = random.random() < 0.7
    # Medium messages - 50/50
    elif len(message) > 60:
        should_split = random.random() < 0.5
    else:
        should_split = random.random() < 0.3
    
    if not should_split:
        return [message]
    
    # Smart splitting logic
    chunks = []
    current_chunk = ""
    
    for i, sentence in enumerate(sentences):
        # Check if adding this sentence makes it too long
        potential = (current_chunk + " " + sentence).strip() if current_chunk else sentence
        
        # Natural break points - split after these
        has_break = any(word in sentence.lower() for word in ['lol', 'haha', 'anyway', 'btw', 'oh', 'hmm'])
        
        if len(potential) > 70 or (has_break and len(current_chunk) > 20):
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk = potential
    
    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Filter out empty or tiny chunks, merge if too many
    chunks = [c for c in chunks if c and len(c) > 5]
    
    # If we ended up with too many tiny chunks, merge some
    if len(chunks) > 4:
        merged = []
        for i in range(0, len(chunks), 2):
            if i + 1 < len(chunks):
                merged.append(chunks[i] + " " + chunks[i+1])
            else:
                merged.append(chunks[i])
        chunks = merged
    
    return chunks if chunks else [message]


def get_all_unread_messages(items, my_user_id):
    """
    Collect ALL consecutive unread messages from the other person.
    This handles rapid-fire messages like:
        User: hey
        User: are you there
        User: i need help
    Returns them in chronological order.
    """
    messages = []
    for item in items:
        sender = str(item.get('user_id', ''))
        if sender == str(my_user_id):
            break  # Stop when we hit our own message
        
        text = item.get('text')
        item_type = item.get('item_type', 'text')
        
        if text:
            messages.append({
                'text': text,
                'item_id': item.get('item_id'),
                'type': item_type
            })
        elif item_type in ['media', 'raven_media', 'visual_media']:
            # Include image messages
            messages.append({
                'text': '[sent an image]',
                'item_id': item.get('item_id'),
                'type': item_type,
                'has_media': True
            })
    
    # Reverse to get chronological order (oldest first)
    return messages[::-1]


async def download_image_as_base64(session, image_url, headers):
    """Download an image from Instagram and return as base64."""
    try:
        # Use minimal headers for image download
        img_headers = {
            "User-Agent": headers.get("User-Agent", "Instagram 342.0.0.33.103 Android"),
        }
        async with session.get(image_url, headers=img_headers) as response:
            if response.status == 200:
                image_data = await response.read()
                return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        print(f"[Image download error: {e}]")
    return None

async def send_typing_indicator(session, headers, thread_id, sender_id=None, proxy=None):
    """
    Send a typing indicator to make the bot feel more human.
    This shows "User is typing..." on the recipient's screen.
    Uses the indicate_activity endpoint which is the correct private API.
    """
    try:
        # Use the indicate_activity broadcast endpoint
        typing_url = f"https://i.instagram.com/api/v1/direct_v2/threads/{thread_id}/indicate_activity/"
        typing_data = {"activity_status": "1", "client_context": str(uuid.uuid4())}
        
        async with session.post(typing_url, proxy=proxy, headers=headers, data=typing_data) as res:
            response_text = await res.text()
            if res.status == 200:
                print(f"[Typing indicator sent] thread={thread_id} sender={sender_id}")
            else:
                print(f"[Typing indicator FAILED] thread={thread_id} sender={sender_id} status={res.status} response={response_text[:200]}")
    except Exception as e:
        print(f"[Typing indicator ERROR] thread={thread_id} sender={sender_id} error={e}")

async def test(username, password, language, proxy, group_messages, knowledge=""):
    print("[DM Bot v2.0] Starting inbox check...")  # Confirm new code is running
    raw_proxy = proxy  # Save raw proxy for login function (without http://)
    timestamp = int(time.time())
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8","Host": "i.instagram.com","Priority": "u=3","User-Agent": "Instagram 342.0.0.33.103 Android (31/12; 454dpi; 1080x2254; Xiaomi/Redmi; Redmi Note 9 Pro; joyeuse; qcom; tr_TR; 627400398)","X-Bloks-Is-Layout-RTL": "false","X-Bloks-Is-Prism-Enabled": "true","X-Bloks-Prism-Button-Version": "CONTROL","X-Bloks-Prism-Colors-Enabled": "true","X-Bloks-Prism-Font-Enabled": "false","X-Bloks-Version-Id": "dummy","X-FB-Connection-Type": "WIFI","X-FB-HTTP-Engine": "Tigon-HUC-Fallback","X-FB-Network-Properties": "dummy","X-IG-Android-ID": "android-a19180f55839e822","X-IG-App-ID": "567067343352427","X-IG-App-Locale": "tr_TR","X-IG-Bandwidth-Speed-KBPS": "1934.000","X-IG-Bandwidth-TotalBytes-B": "1375348","X-IG-Bandwidth-TotalTime-MS": "785","X-IG-Capabilities": "3brTv10=","X-IG-CLIENT-ENDPOINT": "DirectThreadFragment:direct_thread","X-IG-Connection-Type": "WIFI","X-IG-Device-ID": "android-a19180f55839e822","X-IG-Device-Locale": "tr_TR","X-IG-Family-Device-ID": "dummy","X-IG-Mapped-Locale": "tr_TR","X-IG-Nav-Chain": "dummy","X-IG-SALT-IDS": "dummy","X-IG-SALT-LOGGER-IDS": "dummy","X-IG-Timezone-Offset": "10800","X-IG-WWW-Claim": "dummy","X-MID": "dummy","X-Pigeon-Rawclienttime": str(timestamp),"X-Pigeon-Session-Id": f"dummy-{uuid.uuid4()}"}

    # Check for Railway/environment-based auth first (persists across container restarts)
    env_auth = os.getenv('IG_AUTH_TOKEN')
    env_userid = os.getenv('IG_USER_ID')
    
    # First, try fetching from Gist (dynamic token without redeploy)
    gist_token = await fetch_token_from_gist()
    if gist_token and gist_token.get('auth'):
        mydata = {'auth': gist_token['auth'], 'myuserid': gist_token['myuserid']}
        print("[Auth] ✅ Using token from GitHub Gist (dynamic sync)")
    elif env_auth and env_userid:
        # Use environment variables (Railway deployment fallback)
        mydata = {'auth': env_auth, 'myuserid': env_userid}
        print("[Auth] Using environment variables for authentication")
    else:
        # Fall back to file-based auth (local development)
        auth_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Authorization.json')
        
        # Create Authorization.json if it doesn't exist
        if not os.path.exists(auth_file):
            with open(auth_file, 'w') as fs:
                json.dump({'auth': None, 'myuserid': None}, fs, indent=4)
        
        with open(auth_file, 'r') as fs:
            mydata = json.load(fs)
            if mydata.get('auth') is None:
                lt = login(username, password, raw_proxy)
                if lt[0] is True:
                    data = {'auth': lt[1], 'myuserid': str(lt[2])}
                    with open(auth_file, 'w') as fs:
                        json.dump(data, fs, indent=4)
                    mydata = data
                    # Print for Railway setup - copy these to Railway environment variables
                    print("\n" + "="*60)
                    print("[AUTH] NEW TOKEN GENERATED - Copy to Railway env vars:")
                    print(f"IG_AUTH_TOKEN={lt[1]}")
                    print(f"IG_USER_ID={lt[2]}")
                    print("="*60 + "\n")
                    # Auto-sync to Gist (Railway will fetch from there - no redeploy!)
                    await upload_token_to_gist(lt[1], str(lt[2]))

    headers["Authorization"] = f"{mydata.get('auth')}"
    session = aiohttp.ClientSession()
    if not proxy == None:
        proxy=f"http://{proxy}"
        
        

    async with session.get("https://i.instagram.com/api/v1/direct_v2/inbox/",proxy=proxy, headers=headers, params={"persistentBadging": "true", "use_unified_inbox": "true"})as re:
        # Debug: log raw response
        raw_text = await re.text()
        print(f"[API] Status: {re.status}, Response length: {len(raw_text)}")
        
        try:
            res = json.loads(raw_text) if raw_text else {}
        except json.JSONDecodeError as e:
            print(f"[Instagram Bot] Error: {e}")
            print(f"[API] Raw response (first 500 chars): {raw_text[:500]}")
            await session.close()
            return None
            
        if not res.get('logout_reason') is None:
            print("[Auth] Session expired detected in response")
            # Only try re-login if NOT using environment tokens (local dev only)
            if not env_auth:
                print("[Auth] Attempting re-login (local mode)...")
                lt = login(username, password, raw_proxy)
                if lt[0] is True:
                    data = {'auth': lt[1], 'myuserid': str(lt[2])}
                    auth_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Authorization.json')
                    with open(auth_file, 'w') as fs:
                        json.dump(data, fs, indent=4)
                    print("\n" + "="*60)
                    print("[AUTH] NEW TOKEN GENERATED - Copy to Railway env vars:")
                    print(f"IG_AUTH_TOKEN={lt[1]}")
                    print(f"IG_USER_ID={lt[2]}")
                    print("="*60 + "\n")
                    # Auto-sync to Railway and notify via Telegram
                    await sync_token_to_railway(lt[1], str(lt[2]))
            else:
                print("[Auth] Using env tokens - skipping re-login (will notify via Telegram)")
                await notify_token_expired()
        if not res.get('is_spam') is None:
            print('your ip is stuck at rate limit try again after 50 seconds')
            time.sleep(50)

    print(f"[API] Inbox response status: {re.status}")
    
    # Handle auth failures
    if re.status in [401, 403]:
        # Only try re-login if NOT using environment tokens
        if not env_auth:
            print("[Auth] Token expired, attempting re-login (local mode)...")
            lt = login(username, password, raw_proxy)
            if lt[0] is True:
                data = {'auth': lt[1], 'myuserid': str(lt[2])}
                auth_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Authorization.json')
                with open(auth_file, 'w') as fs:
                    json.dump(data, fs, indent=4)
                print("[Auth] Re-login successful!")
                print("\n" + "="*60)
                print("[AUTH] NEW TOKEN GENERATED - Copy to Railway env vars:")
                print(f"IG_AUTH_TOKEN={lt[1]}")
                print(f"IG_USER_ID={lt[2]}")
                print("="*60 + "\n")
                # Auto-sync to Railway and notify via Telegram
                await sync_token_to_railway(lt[1], str(lt[2]))
            else:
                print("[Auth] Re-login FAILED!")
        else:
            # Railway mode - don't try password login, just notify
            print("[Auth] 403 error but using env tokens - NOT attempting password login")
            await notify_token_expired()
        await session.close()
        return None
    
    if re.status == 200:
        data = await re.json()
        threads = data.get("inbox", {}).get("threads", [])
        print(f"[Inbox] Found {len(threads)} threads to check")

        for thread in threads:
            thread_id = thread.get('thread_id')
            items = thread.get("items", [])
            is_group = thread.get("is_group", False)  
            
            if is_group == True and group_messages == False:  
                print(f"[Skip] Group thread {thread_id} - group messages disabled")
                continue 
            if items:
                last_item = items[0]  
                item_id = last_item.get("item_id")
                text = last_item.get("text", None)
                sender = last_item.get("user_id", None)
                item_type = last_item.get("item_type", "text")
                
                # Check for image/media messages
                image_url = None
                if item_type == "media" or item_type == "raven_media":
                    # Regular media or disappearing media
                    media = last_item.get("media", {}) or last_item.get("visual_media", {}).get("media", {})
                    if media:
                        # Try to get the best quality image
                        image_versions = media.get("image_versions2", {}).get("candidates", [])
                        if image_versions:
                            image_url = image_versions[0].get("url")
                elif item_type == "visual_media":
                    # Another format for visual media
                    vm = last_item.get("visual_media", {})
                    media = vm.get("media", {})
                    if media:
                        image_versions = media.get("image_versions2", {}).get("candidates", [])
                        if image_versions:
                            image_url = image_versions[0].get("url")

                # If no text AND no image, skip this thread
                if text is None and image_url is None:
                    print(f"[Skip] Thread {thread_id} - no text or image")
                    continue  

                my_user_id = mydata.get('myuserid', None)

                if str(sender) == str(my_user_id):
                    # Last message is from us, skip to next thread
                    print(f"[Skip] Thread {thread_id} - last message is from us (already replied)")
                    continue
                
                # Check if we already processed this message
                if item_id in _processed_items:
                    continue
                
                # === NEW: Collect ALL unread messages from this thread ===
                all_unread = get_all_unread_messages(items, my_user_id)
                
                if not all_unread:
                    continue
                
                # Mark all these items as processed to avoid double-responding
                for msg in all_unread:
                    _processed_items.add(msg['item_id'])
                
                # Keep processed items set from growing too large
                if len(_processed_items) > 1000:
                    _processed_items.clear()
                
                # Combine multiple messages into one prompt
                if len(all_unread) > 1:
                    combined_texts = [msg['text'] for msg in all_unread if msg.get('text')]
                    combined_message = "\n".join(combined_texts)
                    print(f"[Rapid-fire] {len(all_unread)} messages from {sender}:")
                    for msg in all_unread:
                        print(f"  → {msg['text'][:50]}...")
                else:
                    combined_message = text or ""
                    print(f"Message from {sender}: {combined_message[:100]}")
                
                # Check for images in the latest message
                if image_url:
                    print(f"📷 Image from {sender}" + (f" with text: {text}" if text else ""))
                
                # === MODE-AWARE DELAY LOGIC ===
                mode_name, mode_settings = get_current_mode()
                print(f"[Mode] Current mode: {mode_name}")
                
                # Check if this thread should be skipped
                config = load_agent_config()
                if str(thread_id) in config.get('skipped_threads', []):
                    print(f"[Skip] Thread {thread_id} is in skip list")
                    continue
                
                # Handle no-auto-reply modes (sleep, dnd)
                if not mode_settings.get('auto_reply', True):
                    if mode_name == 'dnd':
                        print(f"[DND] Ignoring message from {sender}")
                        continue
                    else:
                        # Sleep mode - queue the message
                        print(f"[Sleep] Queueing message from {sender}")
                        add_to_queue(thread_id, sender, combined_message, reply_delay=None)
                        continue
                
                # Calculate dynamic delay based on mode
                reply_delay = calculate_reply_delay()
                if reply_delay and reply_delay > 30:
                    # Long delay - queue it and process later
                    print(f"[{mode_name.title()}] Delay {reply_delay:.0f}s - queueing message")
                    add_to_queue(thread_id, sender, combined_message, reply_delay=reply_delay)
                    continue
                elif reply_delay:
                    # Short delay - wait now
                    print(f"[{mode_name.title()}] Waiting {reply_delay:.0f}s before replying...")
                    await asyncio.sleep(reply_delay)
                
                # Send initial typing indicator
                await send_typing_indicator(session, headers, thread_id, sender_id=sender, proxy=proxy)
                
                # Get AI response - use multimodal if image present
                if image_url:
                    print("[Downloading image for AI analysis...]")
                    image_base64 = await download_image_as_base64(session, image_url, headers)
                    if image_base64:
                        print("[Image downloaded, sending to AI...]")
                        ai = await gpt4o_with_image(image_base64, combined_message, language, knowledge)
                    else:
                        ai = "nice pic 👀"
                else:
                    ai = await gpt4o(combined_message, language, knowledge)
                
                # === NEW: Smart split the response into human-like chunks ===
                chunks = smart_split_message(str(ai))
                print(f"[Response] {len(chunks)} chunk(s): {[c[:30]+'...' if len(c) > 30 else c for c in chunks]}")
                
                # Send each chunk with typing indicator and natural delay
                for i, chunk in enumerate(chunks):
                    # Calculate human-like delay for this chunk
                    chunk_length = len(chunk)
                    
                    if i == 0:
                        # First chunk - include "reading" time
                        thinking_time = random.uniform(0.5, 1.5)
                    else:
                        # Subsequent chunks - just typing time + small pause
                        thinking_time = random.uniform(0.3, 0.8)
                    
                    typing_speed = random.uniform(5, 8)  # Characters per second
                    typing_time = chunk_length / typing_speed
                    
                    total_delay = min(thinking_time + typing_time, 6.0)  # Max 6 seconds per chunk
                    total_delay = max(total_delay, 0.8)  # Min 0.8 seconds
                    
                    print(f"[Chunk {i+1}/{len(chunks)}] Typing {total_delay:.1f}s...")
                    await asyncio.sleep(total_delay)
                    
                    # Send this chunk
                    t = threading.Thread(target=mesj, args=(
                        str(mydata.get('auth')),
                        str(my_user_id),
                        "android-1",
                        chunk,
                        [sender],
                        str(thread_id),
                        str(item_id)
                    ))
                    t.start()
                    t.join()
                    print(f"[Chunk {i+1}/{len(chunks)}] Sent: {chunk[:50]}...")
                    
                    # Send typing indicator between chunks (not after last one)
                    if i < len(chunks) - 1:
                        await send_typing_indicator(session, headers, thread_id, sender_id=sender, proxy=proxy)
                
                print("All messages sent successfully")
                
                # Check if we should send a GIF reaction (15% chance when trigger detected)
                # Only check the full response, not each chunk
                gif_reaction = should_send_gif(str(ai))
                if gif_reaction:
                    giphy_id = get_random_gif(gif_reaction)
                    if giphy_id:
                        await asyncio.sleep(random.uniform(0.8, 2.0))
                        print(f"[Sending {gif_reaction} GIF reaction...]")
                        await send_gif_async(
                            session,
                            str(mydata.get('auth')),
                            str(my_user_id),
                            "android-1",
                            giphy_id,
                            [sender],
                            str(thread_id),
                            str(item_id),
                            proxy
                        )
                
            else:
                pass
    await session.close()


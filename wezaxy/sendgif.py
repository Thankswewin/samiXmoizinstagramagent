import aiohttp
import uuid
import time
import json
import os
import random
from urllib.parse import quote

# Load GIF library
def load_gif_library():
    """Load the GIF library from gifs.json"""
    gif_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gifs.json')
    if os.path.exists(gif_file):
        with open(gif_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"reactions": {}, "triggers": {}, "settings": {"gif_chance": 0.15}}

def _load_gif_proxy():
    """Load a proxy for GIF sending (uses same proxies as ChatGPT)."""
    proxy_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'chatgpt_proxies.txt')
    if os.path.exists(proxy_file):
        with open(proxy_file, 'r') as f:
            proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        if proxies:
            proxy_line = random.choice(proxies)
            # Convert format: user:pass:ip:port -> http://user:pass@ip:port
            parts = proxy_line.split(':')
            if len(parts) == 4:
                return f"http://{parts[0]}:{parts[1]}@{parts[2]}:{parts[3]}"
    return None

def should_send_gif(message_text):
    """
    Determine if we should send a GIF based on the AI response.
    Returns the reaction type if we should, None otherwise.
    Uses the gif_chance from settings (default 15%).
    """
    gif_data = load_gif_library()
    triggers = gif_data.get("triggers", {})
    settings = gif_data.get("settings", {})
    gif_chance = settings.get("gif_chance", 0.15)  # Default 15%
    
    message_lower = message_text.lower()
    
    for reaction_type, trigger_words in triggers.items():
        for trigger in trigger_words:
            if trigger in message_lower:
                # Check probability from settings
                if random.random() < gif_chance:
                    return reaction_type
    return None

def get_random_gif(reaction_type):
    """Get a random GIPHY ID for a reaction type."""
    gif_data = load_gif_library()
    reactions = gif_data.get("reactions", {})
    
    gifs = reactions.get(reaction_type, [])
    if gifs:
        return random.choice(gifs)
    return None

async def send_gif_async(
    session,
    token,
    user_id,
    device_id,
    giphy_id,
    user_ids,
    thread_id,
    item_id,
    proxy=None,
    timestamp=None
):
    """
    Send a GIF in Instagram DM using GIPHY ID (async version).
    Uses proxy from chatgpt_proxies.txt to avoid Railway IP blocks.
    
    Args:
        session: aiohttp ClientSession
        token: Authorization token
        user_id: Your user ID
        device_id: Device ID
        giphy_id: GIPHY GIF ID (e.g., "3o7aCWJavAgtBzLWrS")
        user_ids: List of recipient user IDs
        thread_id: Thread ID
        item_id: Item ID to reply to
        proxy: Optional proxy override
        timestamp: Optional timestamp
    """
    if timestamp is None:
        timestamp = int(time.time())

    # Use proxy from chatgpt_proxies.txt if not provided
    if proxy is None:
        proxy = _load_gif_proxy()
        if proxy:
            print(f"[GIF using proxy: {proxy.split('@')[-1] if '@' in proxy else 'direct'}]")

    headers = {
        "Authorization": token,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Host": "i.instagram.com",
        "IG-INTENDED-USER-ID": user_id,
        "IG-U-DS-USER-ID": user_id,
        "IG-U-IG-DIRECT-REGION-HINT": f"CLN,{user_id},{timestamp}:dummy",
        "IG-U-SHBID": f"dummy,{user_id},{timestamp}:dummy",
        "IG-U-SHBTS": f"dummy,{user_id},{timestamp}:dummy",
        "Priority": "u=3",
        "User-Agent": "Instagram 342.0.0.33.103 Android (31/12; 454dpi; 1080x2254; Xiaomi/Redmi; Redmi Note 9 Pro; joyeuse; qcom; tr_TR; 627400398)",
        "X-Bloks-Is-Layout-RTL": "false",
        "X-Bloks-Is-Prism-Enabled": "true",
        "X-Bloks-Prism-Button-Version": "CONTROL",
        "X-Bloks-Prism-Colors-Enabled": "true",
        "X-Bloks-Prism-Font-Enabled": "false",
        "X-Bloks-Version-Id": "dummy",
        "X-FB-Connection-Type": "WIFI",
        "X-FB-HTTP-Engine": "Tigon-HUC-Fallback",
        "X-FB-Network-Properties": "dummy",
        "X-IG-Android-ID": device_id,
        "X-IG-App-ID": "567067343352427",
        "X-IG-App-Locale": "tr_TR",
        "X-IG-Bandwidth-Speed-KBPS": "1934.000",
        "X-IG-Bandwidth-TotalBytes-B": "1375348",
        "X-IG-Bandwidth-TotalTime-MS": "785",
        "X-IG-Capabilities": "3brTv10=",
        "X-IG-CLIENT-ENDPOINT": "DirectThreadFragment:direct_thread",
        "X-IG-Connection-Type": "WIFI",
        "X-IG-Device-ID": device_id,
        "X-IG-Device-Locale": "tr_TR",
        "X-IG-Family-Device-ID": "dummy",
        "X-IG-Mapped-Locale": "tr_TR",
        "X-IG-Nav-Chain": "dummy",
        "X-IG-SALT-IDS": "dummy",
        "X-IG-SALT-LOGGER-IDS": "dummy",
        "X-IG-Timezone-Offset": "10800",
        "X-IG-WWW-Claim": "dummy",
        "X-MID": "dummy",
        "X-Pigeon-Rawclienttime": str(timestamp),
        "X-Pigeon-Session-Id": f"dummy-{uuid.uuid4()}"
    }

    # Instagram uses broadcast/animated_media/ for GIFs
    data = (
        f"action=send_item&is_x_transport_forward=false&is_shh_mode=0"
        f"&send_silently=false&send_attribution=giphy"
        f"&client_context={timestamp}&device_id={device_id}"
        f"&mutation_token={timestamp}&_uuid={device_id}"
        f"&nav_chain=dummy&offline_threading_id={timestamp}"
        f"&recipient_users={quote(str([[int(uid) for uid in user_ids]]))}"
        f"&thread_id={thread_id}&item_id={item_id}"
        f"&id={giphy_id}&is_sticker=0"
    )

    try:
        async with session.post(
            "https://i.instagram.com/api/v1/direct_v2/threads/broadcast/animated_media/", 
            data=data, 
            headers=headers,
            proxy=proxy
        ) as response:
            status = response.status
            if status == 200:
                print(f"[GIF sent: {giphy_id}] ✓")
                return True
            else:
                response_text = await response.text()
                print(f"[GIF send failed: {giphy_id}] status={status} response={response_text[:150]}")
                return False
    except Exception as e:
        print(f"[GIF send error: {e}]")
        return False

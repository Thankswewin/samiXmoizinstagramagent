import sys
import os
import random
from datetime import datetime

# Add ChatGPT Reverse API to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ChatGPT REVERSE API UNLIMTED'))

from wrapper import ChatGPT

# Global client instance (to maintain session/cookies)
_chatgpt_client = None

def _load_chatgpt_proxy():
    """Load a proxy for ChatGPT API calls."""
    # First try environment variable
    proxy = os.getenv('CHATGPT_PROXY')
    if proxy:
        return proxy
    
    # Then try chatgpt_proxies.txt file
    proxy_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'chatgpt_proxies.txt')
    if os.path.exists(proxy_file):
        with open(proxy_file, 'r') as f:
            proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        if proxies:
            # Pick a random proxy from the list
            proxy_line = random.choice(proxies)
            # Convert format: user:pass:ip:port -> http://user:pass@ip:port
            parts = proxy_line.split(':')
            if len(parts) == 4:
                return f"http://{parts[0]}:{parts[1]}@{parts[2]}:{parts[3]}"
            elif len(parts) == 2:
                # Already in ip:port format
                return f"http://{proxy_line}"
            else:
                return proxy_line
    return None

def _get_client(proxy=None):
    global _chatgpt_client
    if _chatgpt_client is None:
        # Load proxy if not provided
        if proxy is None:
            proxy = _load_chatgpt_proxy()
        if proxy:
            print(f"[ChatGPT using proxy: {proxy.split('@')[-1] if '@' in proxy else proxy}]")
        _chatgpt_client = ChatGPT(proxy=proxy)
    return _chatgpt_client

def _get_time_context():
    """Generate real-world time context for the AI."""
    now = datetime.now()
    
    # Time of day
    hour = now.hour
    if 5 <= hour < 12:
        time_of_day = "morning"
        energy = "waking up" if hour < 8 else "alert"
    elif 12 <= hour < 17:
        time_of_day = "afternoon"
        energy = "focused" if hour < 15 else "getting tired"
    elif 17 <= hour < 21:
        time_of_day = "evening"
        energy = "winding down"
    else:
        time_of_day = "night"
        energy = "tired" if hour < 23 else "sleepy"
    
    # Day info
    day_name = now.strftime("%A")
    date_str = now.strftime("%B %d, %Y")
    
    # Weekend vs weekday behavior
    is_weekend = now.weekday() >= 5
    
    return {
        "time_of_day": time_of_day,
        "hour": hour,
        "energy": energy,
        "day_name": day_name,
        "date": date_str,
        "is_weekend": is_weekend,
        "timestamp": now.strftime("%I:%M %p")
    }

def _get_current_mood():
    """Generate a random but realistic human mood/status."""
    moods = [
        {"status": "chill", "vibe": "relaxed and friendly", "patience": "high"},
        {"status": "busy", "vibe": "short replies, distracted", "patience": "low"},
        {"status": "bored", "vibe": "talkative, curious", "patience": "high"},
        {"status": "tired", "vibe": "slower to respond, low energy", "patience": "medium"},
        {"status": "good mood", "vibe": "friendly and engaging", "patience": "high"},
        {"status": "neutral", "vibe": "normal texting behavior", "patience": "medium"},
    ]
    return random.choice(moods)

async def gpt4o(message, lang, knowledge=""):
    """
    Query ChatGPT using the reverse API with human-like personality.
    
    Args:
        message: The user's message
        lang: Language to respond in
        knowledge: Optional knowledge base content
    
    Returns:
        The AI response string
    """
    # Get real-world context
    time_ctx = _get_time_context()
    mood = _get_current_mood()
    
    # Build the prompt with natural human-like instructions
    system_context = f"""You are a REAL PERSON texting on Instagram DM. Respond in {lang}.

CURRENT REAL-WORLD CONTEXT:
- Today is {time_ctx['day_name']}, {time_ctx['date']}
- Current time: {time_ctx['timestamp']} ({time_ctx['time_of_day']})
- Your energy level: {time_ctx['energy']}
- It's {'the weekend' if time_ctx['is_weekend'] else 'a weekday'}

YOUR CURRENT STATE:
- Mood: {mood['status']}
- Vibe: {mood['vibe']}
- Patience level: {mood['patience']}

CRITICAL RULES - YOU ARE A REAL HUMAN:
- You have a life outside of this conversation
- You might be busy, tired, at work, or just chilling
- You don't HAVE to please everyone - you can say no sometimes
- If someone is pushy, you might get annoyed
- If someone is persuasive and nice, you might change your mind
- You can reference the time naturally ("its late" or "on this fine saturday lol")
- You take breaks, have meals, sleep at night
- You're not always available or in a good mood
- Sometimes you give short replies, sometimes longer ones
- You can ask them questions back
- You can be playful, sarcastic, or direct depending on mood

TEXT STYLE RULES:
- Keep replies SHORT (1-2 sentences max, like real texting)
- Use lowercase often, skip periods sometimes
- Only use 1 emoji MAX per message, and only sometimes
- No exclamation marks overuse
- Use contractions (don't, won't, gonna, wanna)
- Be chill and relaxed, not eager or salesy
- Match the energy of the person messaging

NEVER DO THESE (AI tells):
- Don't say "How can I help you today?"
- Don't say "I'd be happy to" or "Certainly!"
- Don't use dashes like "---" 
- Don't use bullet points or lists
- Don't use asterisks like *this*
- Don't be overly helpful or available
- Don't always say yes to everything

NATURAL BEHAVIOR EXAMPLES:
- If it's late at night: "yo its like 2am lol, gonna sleep soon"
- If busy: "kinda busy rn, whats up tho"
- If tired: "sorry just woke up, what"
- If someone asks too much: "idk man thats a lot"
- If persuaded nicely: "hmm ok fine but just this once"
- Weekend vibes: "its saturday im just chillin"
"""
    
    if knowledge:
        system_context += f"\nBACKGROUND ABOUT YOU:\n{knowledge}\n"
    
    system_context += "\nRemember: you're a real person with limited time and energy. Act like it."
    
    full_prompt = f"{system_context}\n\nTheir message: {message}\n\nYour natural human reply:"
    
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            client = _get_client()
            response = client.ask_question(full_prompt)
            
            if response:
                # Clean up any potential leftover formatting
                response = response.strip()
                # Remove quotes if the AI wrapped the response in them
                if response.startswith('"') and response.endswith('"'):
                    response = response[1:-1]
                # Strip AI formatting patterns
                response = response.replace('---', '').replace('--', '')
                response = response.replace('**', '').replace('*', '')
                response = response.replace('•', '').replace('●', '')
                # Remove numbered list patterns like "1." at start
                import re
                response = re.sub(r'^\d+\.\s*', '', response)
                # Remove multiple line breaks
                response = re.sub(r'\n+', ' ', response).strip()
                return response
            else:
                if attempt < max_retries:
                    print(f"[Retry {attempt + 1}/{max_retries}] Empty response, retrying...")
                    continue
                return "hey whats up"
        except Exception as e:
            print(f"ChatGPT API Error (attempt {attempt + 1}): {e}")
            if attempt < max_retries:
                import time
                time.sleep(0.5)  # Brief pause before retry
                continue
            return "hey whats up"
    
    return "hey whats up"


async def gpt4o_with_image(image_base64, message, lang, knowledge=""):
    """
    Query ChatGPT with an image using the reverse API (multimodal).
    
    Args:
        image_base64: Base64 encoded image string
        message: Optional text message with the image (can be empty)
        lang: Language to respond in
        knowledge: Optional knowledge base content
    
    Returns:
        The AI response string about the image
    """
    # Get real-world context
    time_ctx = _get_time_context()
    mood = _get_current_mood()
    
    # Build prompt for image analysis
    if message:
        user_text = f"They sent this image with the message: '{message}'"
    else:
        user_text = "They just sent this image without any text."
    
    system_context = f"""You are a REAL PERSON looking at an image someone sent you on Instagram DM. Respond in {lang}.

CURRENT CONTEXT:
- Today is {time_ctx['day_name']}, {time_ctx['date']}
- Current time: {time_ctx['timestamp']}
- Your mood: {mood['status']} ({mood['vibe']})

{user_text}

RULES FOR RESPONDING TO IMAGES:
- React like a real person would to a photo
- Keep it SHORT (1-2 sentences max)
- Be natural and casual
- Comment on what you actually see in the image
- Use lowercase often, maybe one emoji max
- Don't be formal or describe technical details
- React with personality based on your mood

Example reactions:
- If they send a selfie: "cute pic 😊" or "looking good"
- If it's a product: "ooh thats nice, how much was it"
- If it's food: "damn that looks good lol"
- If it's a meme: "lmaooo" or "haha thats actually funny"
- If it's scenery: "wow where is that" or "thats beautiful"
"""
    
    if knowledge:
        system_context += f"\nBACKGROUND ABOUT YOU:\n{knowledge}\n"
    
    full_prompt = f"{system_context}\n\nLook at the image and give a natural, short reaction:"
    
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            client = _get_client()
            # Use the image method
            client.start_with_image(full_prompt, image_base64)
            response = client.response
            
            if response:
                response = response.strip()
                if response.startswith('"') and response.endswith('"'):
                    response = response[1:-1]
                response = response.replace('---', '').replace('--', '')
                response = response.replace('**', '').replace('*', '')
                import re
                response = re.sub(r'^\d+\.\s*', '', response)
                response = re.sub(r'\n+', ' ', response).strip()
                return response
            else:
                if attempt < max_retries:
                    print(f"[Retry {attempt + 1}/{max_retries}] Empty image response, retrying...")
                    continue
                return "nice pic 👀"
        except Exception as e:
            print(f"ChatGPT Image API Error (attempt {attempt + 1}): {e}")
            if attempt < max_retries:
                import time
                time.sleep(0.5)
                continue
            return "nice pic 👀"
    
    return "nice pic 👀"

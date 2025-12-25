import asyncio, aiohttp, time, uuid, json, threading, os, random, base64
from wezaxy.sendmessage import mesj
from wezaxy.login import login
from wezaxy.ai import gpt4o, gpt4o_with_image
from wezaxy.sendgif import should_send_gif, get_random_gif, send_gif_async

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
    timestamp = int(time.time())
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8","Host": "i.instagram.com","Priority": "u=3","User-Agent": "Instagram 342.0.0.33.103 Android (31/12; 454dpi; 1080x2254; Xiaomi/Redmi; Redmi Note 9 Pro; joyeuse; qcom; tr_TR; 627400398)","X-Bloks-Is-Layout-RTL": "false","X-Bloks-Is-Prism-Enabled": "true","X-Bloks-Prism-Button-Version": "CONTROL","X-Bloks-Prism-Colors-Enabled": "true","X-Bloks-Prism-Font-Enabled": "false","X-Bloks-Version-Id": "dummy","X-FB-Connection-Type": "WIFI","X-FB-HTTP-Engine": "Tigon-HUC-Fallback","X-FB-Network-Properties": "dummy","X-IG-Android-ID": "android-a19180f55839e822","X-IG-App-ID": "567067343352427","X-IG-App-Locale": "tr_TR","X-IG-Bandwidth-Speed-KBPS": "1934.000","X-IG-Bandwidth-TotalBytes-B": "1375348","X-IG-Bandwidth-TotalTime-MS": "785","X-IG-Capabilities": "3brTv10=","X-IG-CLIENT-ENDPOINT": "DirectThreadFragment:direct_thread","X-IG-Connection-Type": "WIFI","X-IG-Device-ID": "android-a19180f55839e822","X-IG-Device-Locale": "tr_TR","X-IG-Family-Device-ID": "dummy","X-IG-Mapped-Locale": "tr_TR","X-IG-Nav-Chain": "dummy","X-IG-SALT-IDS": "dummy","X-IG-SALT-LOGGER-IDS": "dummy","X-IG-Timezone-Offset": "10800","X-IG-WWW-Claim": "dummy","X-MID": "dummy","X-Pigeon-Rawclienttime": str(timestamp),"X-Pigeon-Session-Id": f"dummy-{uuid.uuid4()}"}

    # Use os.path.join for cross-platform compatibility
    auth_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Authorization.json')
    
    # Create Authorization.json if it doesn't exist
    if not os.path.exists(auth_file):
        with open(auth_file, 'w') as fs:
            json.dump({'auth': None, 'myuserid': None}, fs, indent=4)
    
    with open(auth_file, 'r') as fs:
        mydata = json.load(fs)
        if mydata.get('auth') is None:
            lt = login(username, password)
            if lt[0] is True:
                data = {'auth': lt[1], 'myuserid': str(lt[2])}
                with open(auth_file, 'w') as fs:
                    json.dump(data, fs, indent=4)
                mydata = data

    headers["Authorization"] = f"{mydata.get('auth')}"
    session = aiohttp.ClientSession()
    if not proxy == None:
        proxy=f"http://{proxy}"
        
        

    async with session.get("https://i.instagram.com/api/v1/direct_v2/inbox/",proxy=proxy, headers=headers, params={"persistentBadging": "true", "use_unified_inbox": "true"})as re:
        res = await re.json(content_type=None)
        if not res.get('logout_reason') is None:
            lt = login(username, password)
            if lt[0] is True:
                data = {'auth': lt[1], 'myuserid': str(lt[2])}
                with open(f'{os.path.dirname(os.path.abspath(__file__))}\\Authorization.json', 'w') as fs:
                    json.dump(data, fs, indent=4)
        if not res.get('is_spam') is None:
            print('your ip is stuck at rate limit try again after 50 seconds')
            time.sleep(50)

    print(f"[API] Inbox response status: {re.status}")
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
                    continue
                
                # Log the message type
                if image_url:
                    print(f"📷 Image from {sender}" + (f" with text: {text}" if text else ""))
                else:
                    print(f"Message from {sender}: {text}")
                
                # Send typing indicator to show "User is typing..."
                await send_typing_indicator(session, headers, thread_id, sender_id=sender, proxy=proxy)
                
                # Get AI response - use multimodal if image present
                if image_url:
                    print("[Downloading image for AI analysis...]")
                    image_base64 = await download_image_as_base64(session, image_url, headers)
                    if image_base64:
                        print("[Image downloaded, sending to AI...]")
                        ai = await gpt4o_with_image(image_base64, text or "", language, knowledge)
                    else:
                        # Fallback if image download fails
                        ai = "nice pic 👀"
                else:
                    ai = await gpt4o(text, language, knowledge)
                

                # Add a human-like delay based on message length
                # Average person types ~5-7 characters per second on mobile
                # Plus some "thinking" time before they start typing
                message_length = len(str(ai))
                thinking_time = random.uniform(0.5, 1.5)  # Time to "read" and think
                typing_speed = random.uniform(5, 7)  # Characters per second
                typing_time = message_length / typing_speed
                
                # Cap the total delay to avoid very long waits
                total_delay = min(thinking_time + typing_time, 8.0)  # Max 8 seconds
                total_delay = max(total_delay, 1.5)  # Min 1.5 seconds
                
                print(f"[Simulating typing for {total_delay:.1f}s ({message_length} chars)...]")
                await asyncio.sleep(total_delay)
                
                t = threading.Thread(target=mesj, args=(
                    str(mydata.get('auth')),
                    str(my_user_id),
                    "android-1",
                    str(ai),
                    [sender],
                    str(thread_id),
                    str(item_id)
                ))
                t.start()
                t.join()  
                print("message sent successfully")
                
                # Check if we should send a GIF reaction (15% chance when trigger detected)
                gif_reaction = should_send_gif(str(ai))
                if gif_reaction:
                    giphy_id = get_random_gif(gif_reaction)
                    if giphy_id:
                        await asyncio.sleep(random.uniform(0.8, 2.0))  # Natural delay before GIF
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


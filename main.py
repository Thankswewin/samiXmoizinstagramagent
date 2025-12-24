# Instagram AI DM Auto-Responder Pro | @samiXmoiz_bot
from wezaxy.test import test
import json
import asyncio

from dotenv import load_dotenv
import os

async def main():
    load_dotenv()
    while True:
        use_proxy = os.getenv('USE_PROXY', 'false').lower() == 'true'
        username = os.getenv('IG_USERNAME')
        password = os.getenv('IG_PASSWORD')
        language = os.getenv('LANGUAGE')
        group_messages = os.getenv('GROUP_MESSAGES', 'false').lower() == 'true'

        if not username or not password or not language:
            print("Required information is empty in config.json")
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
                    print("the last dm message that came in:",result)

        else:
            
            result = await test(username, password, language, None, group_messages, knowledge)
            print("the last dm message that came in:",result)
        if use_proxy is False:
         await asyncio.sleep(2) 

if __name__ == "__main__":
    asyncio.run(main())

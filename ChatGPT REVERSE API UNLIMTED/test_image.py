import base64

with open('images/image.png', 'rb') as f:
    img_data = f.read()

img_b64 = base64.b64encode(img_data).decode()

from wrapper import ChatGPT

client = ChatGPT()

response = client.ask_question("What's in this image?", f"data:image/png;base64,{img_b64}")

print(response)
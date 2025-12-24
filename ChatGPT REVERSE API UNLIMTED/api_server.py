from fastapi      import FastAPI, HTTPException
from urllib.parse import urlparse, ParseResult
from pydantic     import BaseModel
from wrapper      import ChatGPT
from uvicorn      import run


app = FastAPI()

class ConversationRequest(BaseModel):
    proxy: str
    message: str
    image: str = None

def format_proxy(proxy: str) -> str:
    
    if not proxy.startswith(("http://", "https://")):
        proxy: str = "http://" + proxy
    
    try:
        parsed: ParseResult = urlparse(proxy)

        if parsed.scheme not in ("http", ""):
            raise ValueError("Not http scheme")

        if not parsed.hostname or not parsed.port:
            raise ValueError("No url and port")

        if parsed.username and parsed.password:
            return f"http://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}"
        
        else:
            return f"http://{parsed.hostname}:{parsed.port}"
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid proxy format: {str(e)}")

@app.post("/conversation")
async def create_conversation(request: ConversationRequest):
    if not request.proxy or not request.message:
        raise HTTPException(status_code=400, detail="Proxy and message are required")
    
    proxy = format_proxy(request.proxy)
    
    try:
        if request.image:
            answer: str = ChatGPT(proxy).ask_question(request.message, request.image)
        else:
            answer: str = ChatGPT(proxy).ask_question(request.message)
        
        return {
            "status": "success",
            "result": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=6970)
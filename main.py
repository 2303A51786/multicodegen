from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import os

from parser import parse_code
from translator import translate_nodes

app = FastAPI(title="Multi-Language Code Translator (Offline Version)")

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

class TranslationRequest(BaseModel):
    source_code: str
    source_lang: str
    target_lang: str

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r") as f:
        return f.read()

@app.post("/translate")
async def translate_endpoint(req: TranslationRequest):
    try:
        nodes = parse_code(req.source_code, req.source_lang)
        translated_code = translate_nodes(nodes, req.target_lang)
        return {"status": "success", "translated_code": translated_code}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

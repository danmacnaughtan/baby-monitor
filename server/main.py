import io
import logging

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from stream_service import StreamService


logger = logging.getLogger(__name__)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

stream_service = None


@app.on_event("startup")
def startup_event():
    global stream_service
    stream_service = StreamService().run()


@app.on_event("shutdown")
def shutdown_event():
    global stream_service
    stream_service.stop()


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/stream.mjpg")
def stream():
    global stream_service
    return StreamingResponse(
        stream_service.generate_frames(),
        headers={
            "Age": "0",
            "Cache-Control": "no-cache, private",
            "Pragma": "no-cache",
            "Content-Type": "multipart/x-mixed-replace; boundary=FRAME",
        },
    )

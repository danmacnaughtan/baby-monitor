import datetime
import io
import json
import logging
import secrets
import typing as t

import bcrypt
from fastapi import Cookie, Depends, FastAPI, Form, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from stream_service import StreamService


logging.basicConfig(
    filename="stream.log",
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

security = HTTPBasic()

stream_service = StreamService()


try:
    with open("data/users.json", "r") as f:
        users = json.loads(f.read())
except FileNotFoundError:
    users = {}

sessions = {}


def is_user(username: str, password: str) -> bool:
    global users
    valid_usr = username in users
    valid_pwd = bcrypt.checkpw(password.encode(), users.get(username).encode())
    return valid_usr and valid_pwd


def create_session(username: str) -> str:
    global sessions
    token = secrets.token_hex(16)
    expiry = (datetime.datetime.now() + datetime.timedelta(days=1)).timestamp()
    sessions[token] = {"user": username, "expiry": expiry}
    return token


def is_valid_session(session_token: t.Optional[str] = Cookie(None)) -> bool:
    global sessions
    if session_token not in sessions:
        return False
    _, expiry = sessions.get(session_token).values()
    if expiry < datetime.datetime.now().timestamp():
        sessions.pop(session_token)
        return False
    return True


@app.on_event("startup")
def startup_event():
    global stream_service
    stream_service.run()


@app.on_event("shutdown")
def shutdown_event():
    global stream_service
    stream_service.stop()


@app.get("/")
async def index(request: Request, allowed: bool = Depends(is_valid_session)):
    if not allowed:
        return RedirectResponse("/login")
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/login")
async def login(
    username: t.Optional[str] = Form(None), password: t.Optional[str] = Form(None)
):
    if not (all((username, password)) and is_user(username, password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie(key="session_token", value=create_session(username))
    return resp


@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/logout")
async def login_page(session_token: t.Optional[str] = Cookie(None)):
    global sessions
    sessions.pop(session_token, None)
    return RedirectResponse("/login")


@app.get("/stream.mjpg")
async def stream(allowed: bool = Depends(is_valid_session)):
    global stream_service

    if not allowed:
        return RedirectResponse("/login")

    return StreamingResponse(
        stream_service.generate_frames(),
        headers={
            "Age": "0",
            "Cache-Control": "no-cache, private",
            "Pragma": "no-cache",
            "Content-Type": "multipart/x-mixed-replace; boundary=FRAME",
        },
    )

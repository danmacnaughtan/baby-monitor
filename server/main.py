import config  # isort:skip

import logging
import typing as t

from fastapi import Cookie, Depends, FastAPI, Form, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import auth
from stream_service import StreamService


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

stream_service = StreamService()


@app.on_event("startup")
def startup_event():
    global stream_service
    stream_service.run()

    auth.remove_expired_sessions()


@app.on_event("shutdown")
def shutdown_event():
    global stream_service
    stream_service.stop()


@app.get("/")
async def index(request: Request, allowed: bool = Depends(auth.is_valid_session)):
    if not allowed:
        return RedirectResponse("/login")
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/login")
async def login(
    username: t.Optional[str] = Form(None), password: t.Optional[str] = Form(None)
):
    if not (all((username, password)) and auth.is_user(username, password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie(key="session_token", value=auth.create_session(username))
    return resp


@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/logout")
async def login_page(session_token: t.Optional[str] = Cookie(None)):
    auth.clear_session(session_token)
    return RedirectResponse("/login")


@app.get("/stream.mjpg")
async def stream(allowed: bool = Depends(auth.is_valid_session)):
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

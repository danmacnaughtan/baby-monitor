import io
import json
import logging
import secrets

import bcrypt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
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


# Load users from file... passwords hashed w/ bcrypt
try:
    with open("data/users.json", "r") as f:
        users = json.loads(f.read())
except FileNotFoundError:
    users = {}

# Key: username
# Value: {'token': <token>, 'expiry': <expiry>}
sessions = {}


def auth_user(credentials: HTTPBasicCredentials = Depends(security)):
    valid_usr = credentials.username in users
    valid_pwd = bcrypt.checkpw(
        credentials.password.encode(), users.get(credentials.username).encode()
    )

    if not (valid_usr and valid_pwd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


@app.on_event("startup")
def startup_event():
    global stream_service
    stream_service.run()


@app.on_event("shutdown")
def shutdown_event():
    global stream_service
    stream_service.stop()


@app.get("/")
async def index(request: Request, user: str = Depends(auth_user)):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/stream.mjpg")
def stream(user: str = Depends(auth_user)):
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

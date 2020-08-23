import datetime
import json
import secrets
import typing as t

import bcrypt
from fastapi import Cookie

import config


def _load_json_file(filename):
    try:
        with open(filename, "r") as f:
            return json.loads(f.read())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


users = _load_json_file(config.USERS_FILE)

sessions = _load_json_file(config.SESSIONS_FILE)

access_tokens = _load_json_file(config.ACCESS_TOKENS_FILE)


def is_user(username: str, password: str) -> bool:
    global users

    valid_usr = username in users

    valid_pwd = bcrypt.checkpw(password.encode(), users.get(username).encode())

    return valid_usr and valid_pwd


def add_user(usrname: str, password: str):
    global users

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    users.update({usrname: hashed.decode()})

    with open(config.USERS_FILE, "w") as f:
        f.write(json.dumps(users, indent=4))


def create_session(username: str) -> str:
    global sessions

    token = secrets.token_hex(16)

    expiry = (
        datetime.datetime.now() + datetime.timedelta(days=config.DEFAULT_SESSION_LENGTH)
    ).timestamp()

    sessions[token] = {"user": username, "expiry": expiry}

    with open(config.SESSIONS_FILE, "w") as f:
        f.write(json.dumps(sessions, indent=4))

    return token


def clear_session(session_token: str):
    global sessions

    sessions.pop(session_token, None)

    with open(config.SESSIONS_FILE, "w") as f:
        f.write(json.dumps(sessions, indent=4))


def remove_expired_sessions():
    global sessions

    expired = lambda s: s.get("expiry") < datetime.datetime.now().timestamp()

    sessions = {k: v for k, v in sessions.items() if not expired(v)}

    with open(config.SESSIONS_FILE, "w") as f:
        f.write(json.dumps(sessions, indent=4))


def is_valid_session(session_token: t.Optional[str] = Cookie(None)) -> bool:
    global sessions

    if session_token not in sessions:
        return False

    _, expiry = sessions.get(session_token).values()

    if expiry < datetime.datetime.now().timestamp():
        clear_session(session_token)
        return False

    return True


def create_access_token(name: str) -> str:
    global access_tokens

    lookup = secrets.token_hex(4)
    token = secrets.token_hex(16)

    token_hash = bcrypt.hashpw(token.encode(), bcrypt.gensalt())

    access_tokens[lookup] = {"token_hash": token_hash.decode(), "name": name}

    with open(config.ACCESS_TOKENS_FILE, "w") as f:
        f.write(json.dumps(access_tokens, indent=4))

    return f"{lookup}.{token}"


def is_valid_access_token(access_token: str) -> bool:
    global access_tokens

    lookup, token = access_token.split(".")

    if lookup not in access_tokens:
        return False

    token_hash = access_tokens.get(lookup).get("token_hash")

    return bcrypt.checkpw(token.encode(), token_hash.encode())

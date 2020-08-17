import argparse
import json
import sys
from getpass import getpass
from pathlib import Path

import bcrypt


DATA_PATH = Path("data")
DATA_PATH.mkdir(parents=True, exist_ok=True)
USERS_FILE = DATA_PATH / "users.json"


def add_user(usr, pwd_hash):
    try:
        with open(USERS_FILE, "r") as f:
            users = json.loads(f.read())
    except FileNotFoundError:
        users = {}

    if usr in users:
        if not (
            input("User already exists. Replace user/pwd? [y/n]: ")
            .lower()
            .startswith("y")
        ):
            print("No changes have been made.")
            return

    users.update({usr: pwd_hash.decode()})

    with open(USERS_FILE, "w") as f:
        f.write(json.dumps(users, indent=4))

    print(f"User, {usr}, added.")


def createuser(*args, **kwargs):
    print("*** Creating a new user ***")

    usr = input("Enter username: ")
    pwd = getpass("Enter password: ")
    if pwd != getpass("Re-enter password: "):
        print("Passwords don't match!")
        return

    hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt())

    add_user(usr, hashed)
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title="commands")

    parser_createuser = subparsers.add_parser("createuser", help="Create a new user.")
    parser_createuser.set_defaults(func=createuser)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

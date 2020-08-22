import argparse
import json
import sys
from getpass import getpass

import auth
import config


def createuser(*args, **kwargs):
    print("*** Creating a new user ***")

    usr = input("Enter username: ")
    pwd = getpass("Enter password: ")
    if pwd != getpass("Re-enter password: "):
        print("Passwords don't match!")
        return

    if usr in auth.users:
        if not (
            input("User already exists. Replace user/pwd? [y/n]: ")
            .lower()
            .startswith("y")
        ):
            print("No changes have been made.")
            return

    auth.add_user(usr, pwd)

    print(f"User, {usr}, added.")


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

import argparse
import json
import sys
from getpass import getpass

import auth
import config


def create_user(*args, **kwargs):
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


def create_access_token(*args, **kwargs):
    print("*** Creating a new access token ***")

    name = input("Enter a name for the access token: ")

    token = auth.create_access_token(name)

    print("Access token created.")
    print("\nWARNING: Save this token now. It is the only time it will be shown:")
    print(f"\n{token}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title="commands")

    parser_create_user = subparsers.add_parser("create_user", help="Create a new user.")
    parser_create_user.set_defaults(func=create_user)

    parser_create_access_token = subparsers.add_parser(
        "create_access_token", help="Create a new access token."
    )
    parser_create_access_token.set_defaults(func=create_access_token)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

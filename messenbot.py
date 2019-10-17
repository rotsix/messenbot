#!/usr/bin/env python3
# small messenger bot
# rotsix © wtfpl 2019

"""
small messenger bot
"""

import argparse
from getpass import getpass
import json
import subprocess
from fbchat import Client
from fbchat.models import Message, ThreadType


def write_cookies(cookies_location):
    mail = input("mail: ")
    password = getpass("password: ")
    client = Client(mail, password)
    session_cookies = client.getSession()
    with open(cookies_location, "w") as cookies_file:
        cookies_file.write(json.dumps(session_cookies))
    client.logout()


def read_cookies(cookies_location):
    with open(cookies_location, "r") as cookies_file:
        return json.loads(cookies_file.readline())
    return None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-C", "--cookies", dest="cookies", help="connection cookies location <TODO>"
    )
    parser.add_argument("-u", "--user-id", dest="user_id", help="user to listen to")
    return parser.parse_args()


class MessenBot(Client):
    def set_listener(self, user_id):
        self.user_to_listen_to = user_id

    def onMessage(
        self, mid, author_id, message_object, thread_id, thread_type, **kwargs
    ):
        if thread_type == ThreadType.GROUP:
            # that's a group message
            return

        if author_id != self.user_to_listen_to:
            # don't fuckin talk to me
            self.send(
                Message(text="lol who are u?"),
                thread_id=author_id,
                thread_type=ThreadType.USER,
            )
            return

        if author_id == self.user_to_listen_to and thread_type == ThreadType.USER:
            # talking to the right person, and in a private conversation
            self.markAsDelivered(thread_id, mid)
            try:
                process = subprocess.run(
                    message_object.text.split(" "),
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding="utf-8",
                )
                msg = "```\n"
                for line in process.stdout.splitlines():
                    msg += line + "\n"
                msg += "```"
                send_msg(self, msg)
            except subprocess.CalledProcessError as e:
                msg = "```\n"
                msg += "ERROR:\n"
                msg += f"STATUS: {e.returncode}\n"
                if e.stdout:
                    msg += "\nSTDOUT:\n"
                    for line in e.stdout.splitlines():
                        msg += line + "\n"
                if e.stderr:
                    msg += "\nSTDERR:\n"
                    for line in e.stderr.splitlines():
                        msg += line + "\n"
                msg += "```"
                send_msg(self, msg)
            except FileNotFoundError:
                send_msg(self, f"command not found: `{message_object.text}`")
            finally:
                return


def send_msg(client, msg):
    client.send(
        Message(text=msg),
        thread_id=client.user_to_listen_to,
        thread_type=ThreadType.USER,
    )


def main():
    args = parse_args()
    client = None
    if not args.user_id:
        print("please, provide a user_id (see --help)")
        exit(1)

    if args.cookies:
        session_cookies = read_cookies(args.cookies)
        if not session_cookies:
            print("couldn't parse cookies, aborting")
            exit(1)
        client = MessenBot("mark", "zuckerberg", session_cookies=session_cookies)
    else:
        mail = input("mail: ")
        password = getpass("password: ")
        client = MessenBot(mail, password)

    if client:
        client.set_listener(args.user_id)
        client.listen()


if __name__ == "__main__":
    main()

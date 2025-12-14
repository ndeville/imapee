#!/usr/bin/env python3

251209-2114 NOT WORKING

import subprocess
import re
import os
import getpass
import requests
import sys
from urllib.parse import quote

from dotenv import load_dotenv
load_dotenv()

MIGADU_USERNAME = os.getenv('MIGADU_USERNAME')
MIGADU_PASSWORD = os.getenv('MIGADU_PASSWORD')
DOMAIN = "nicolasdeville.com"

# Email regex for basic validation
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

def get_clipboard():
    try:
        return subprocess.check_output(['pbpaste']).decode('utf-8').strip()
    except Exception as e:
        print(f"Error reading clipboard: {e}", file=sys.stderr)
        sys.exit(1)

def is_valid_email(email):
    return bool(EMAIL_REGEX.match(email))

def get_denylist(domain, password):
    url = f"https://migadu.com/api/domains/{quote(domain, safe='')}/recipient_denylist"
    try:
        resp = requests.get(url, auth=(domain, password))
        resp.raise_for_status()
        return [item['recipient'] for item in resp.json()]
    except requests.RequestException as e:
        print(f"Error fetching denylist: {e}", file=sys.stderr)
        sys.exit(1)

def add_to_denylist(domain, password, recipient):
    url = f"https://migadu.com/api/domains/{quote(domain, safe='')}/recipient_denylist/{quote(recipient, safe='')}"
    try:
        resp = requests.post(url, auth=(domain, password))
        if resp.status_code in (200, 204, 201):
            print(f"Successfully added '{recipient}' to recipient_denylist for domain '{domain}'.")
        else:
            print(f"Failed to add '{recipient}': HTTP {resp.status_code} - {resp.text}", file=sys.stderr)
    except requests.RequestException as e:
        print(f"Error adding to denylist: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    content = get_clipboard()
    if not content:
        print("Clipboard is empty.", file=sys.stderr)
        sys.exit(1)

    if not is_valid_email(content):
        print(f"'{content}' is not a valid email address.", file=sys.stderr)
        sys.exit(1)

    print(f"Clipboard content: {content}")
    confirm = input("Add this email to recipient_denylist? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Aborted.")
        sys.exit(0)

    # Check if already in denylist
    denylist = get_denylist(DOMAIN, MIGADU_PASSWORD)
    if content in denylist:
        print(f"'{content}' is already in the recipient_denylist for '{DOMAIN}'.")
        sys.exit(0)
    
    # Add it
    add_to_denylist(DOMAIN, MIGADU_PASSWORD, content)

if __name__ == "__main__":
    main()

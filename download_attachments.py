from datetime import datetime
print(f"Starting at {datetime.now().strftime('%H:%M:%S')}")
import time
start_time = time.time()

import os

from dotenv import load_dotenv
load_dotenv()
SAVE_TO_NDUK = os.getenv("SAVE_TO_NDUK")
SAVE_TO_NDCOM = os.getenv("SAVE_TO_NDCOM")
PATH_INDEXEE = os.getenv("PATH_INDEXEE")

import sys
sys.path.append(PATH_INDEXEE)

from imap_tools import MailBox, AND, MailMessageFlags
# import re

import pprint
pp = pprint.PrettyPrinter(indent=4)
print()

count = 0

v = True
test = False

# DEFINE VARIABLES HERE
account = 'NDCOM' # NDUK / NDCOM
mailbox_category = 'Sent' # Inbox / Sent (other categories not yet implemented: Drafts / Spam / Trash)
###

if account == 'NDUK':
    EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT_NDUK")
    PASSWORD = os.getenv("PASSWORD_NDUK")
    EMAIL_SERVER = os.getenv("EMAIL_SERVER_NDUK")
    save_to = SAVE_TO_NDUK
if account == 'NDCOM':
    EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT_ND")
    PASSWORD = os.getenv("PASSWORD_ND")
    EMAIL_SERVER = os.getenv("EMAIL_SERVER_ND")
    save_to = SAVE_TO_NDCOM

count_processed = 0
count_errors = 0
count_mark_as_read = 0
count_deleted = 0
count_attach = 0

list_errors = []

with MailBox(EMAIL_SERVER).login(EMAIL_ACCOUNT, PASSWORD) as mailbox:

    if mailbox_category == 'Inbox':

        mailbox.folder.set('Inbox') # Inbox / Sent / 

        # for msg in mailbox.fetch(AND(from_='Mail Delivery'), mark_seen=False): # example with search string
        for msg in mailbox.fetch(mark_seen=False, reverse=True, bulk=False): # get all emails from most recent without changing read status

            count += 1

            date = msg.date.strftime('%y%m%d')

            for att in msg.attachments:
                count_attach += 1
                print(count, date, att.filename, att.content_type)
                try:
                    with open(f'{save_to}/{date}-{msg.from_}-{att.filename}', 'wb') as f:
                        f.write(att.payload)
                except:
                    print(f"ERROR with {date}-{msg.from_}-{att.filename}")
                    list_errors.append(f"{date}-{msg.from_}-{att.filename}")
                    count_errors += 1

    if mailbox_category == 'Sent':

        mailbox.folder.set('Sent') # Inbox / Sent / Drafts / Spam / Trash

        for msg in mailbox.fetch(mark_seen=False, reverse=True, bulk=False): # get all emails from most recent without changing read status

            count += 1

            date = msg.date.strftime('%y%m%d')

            for att in msg.attachments:
                count_attach += 1
                print(count, date, att.filename, att.content_type)
                try:
                    with open(f'{save_to}/{date}-{msg.from_}-{att.filename}', 'wb') as f:
                        f.write(att.payload)
                except:
                    print(f"ERROR with {date}-{msg.from_}-{att.filename}")
                    list_errors.append(f"{date}-{msg.from_}-{att.filename}")
                    count_errors += 1

print()
for error in list_errors:
    print(error)

########################################################################################################

if __name__ == '__main__':
    print()
    print('-------------------------------')
    print(f"Count Total Emails = {count} emails found")
    print(f"count_attach = {count_attach} attachments")
    print(f"count_errors = {count_errors}")
    print()

    print('-------------------------------')
    run_time = round((time.time() - start_time)/60, 1)
    print(f"{os.path.basename(__file__)} finished in {run_time} minutes at {datetime.now().strftime('%H:%M:%S')}.")
    print()
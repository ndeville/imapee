from datetime import datetime
print(f"Starting at {datetime.now().strftime('%H:%M:%S')}")
import time
start_time = time.time()

import os

from dotenv import load_dotenv
load_dotenv()
PATH_INDEXEE = os.getenv("PATH_INDEXEE")

import sys
sys.path.append(PATH_INDEXEE)

from dotenv import load_dotenv
load_dotenv()


from imap_tools import MailBox, AND, MailMessageFlags
import re

import pprint
pp = pprint.PrettyPrinter(indent=4)
print()
count = 0
####################

"""
Clean mailbox of unwanted emails
based on strings in To, From, Subject fields
Strings are in /Users/nic/Python/imapee/data/delete_if_in_from.txt
"""

v = False

EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT_ND")
PASSWORD = os.getenv("PASSWORD_ND")
EMAIL_SERVER = os.getenv("EMAIL_SERVER_ND")

EMAIL_REGEX1 = r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""

set_emails_dne = set() # Set of dicts: {email: , src:, first: }
set_new_emails = set()
set_email_checked = set()
added_to_WN_contacts = []
updated_in_WN001 = []

list_remove = ['?', 'png', 'reply', 'DAEMON', 'Daemon', '.jpg', '.gif']

count_processed = 0
count_errors = 0
count_mark_as_read = 0
count_deleted = 0

def get_tuple_from_file(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
    # Remove trailing newline characters and create tuple
    return tuple(line.strip() for line in lines)

delete_if_in_to = get_tuple_from_file(os.getenv("DELETE_IF_IN_TO")) # tuple of strings
delete_if_in_from = get_tuple_from_file(os.getenv("DELETE_IF_IN_FROM")) # tuple of strings
delete_if_in_subject = get_tuple_from_file(os.getenv("DELETE_IF_IN_SUBJECT")) # tuple of strings

with MailBox(EMAIL_SERVER).login(EMAIL_ACCOUNT, PASSWORD) as mailbox:

    # for msg in mailbox.fetch(AND(from_='Mail Delivery'), mark_seen=False): # example with search string
    for msg in mailbox.fetch(mark_seen=False, reverse=True, bulk=True): # get all emails from most recent without changing read status

    ### REFERENCE
    # criteria = ‘ALL’, message search criteria, query builder
    # charset = ‘US-ASCII’, indicates charset of the strings that appear in the search criteria. See rfc2978
    # limit = None, limit on the number of read emails, useful for actions with a large number of messages, like “move”
    # miss_no_uid = True, miss emails without uid
    # mark_seen = True, mark emails as seen on fetch
    # reverse = False, in order from the larger date to the smaller
    # headers_only = False, get only email headers (without text, html, attachments)
    # bulk = False, False - fetch each message separately per N commands - low memory consumption, slow; True - fetch all messages per 1 command - high memory consumption, fast

        count += 1

        # print("\r" + str(count), end='')

        # PRINT EACH EMAIL
        # print(f"\n\n\n>>> {count:,}\n\n{msg.date_str=}")
        # print(f"{msg.from_=}")
        # print(f"{msg.to=}")
        # print(f"{msg.subject=}")
        # print(f"{msg.text=}")


        ### DELETE

        ## BASED ON TO FIELD

        # Delete based on string in To field (delete_if_in_to)
        try:
            if len(msg.to) > 0:
                if any(ele in msg.to[0] for ele in delete_if_in_to):
                # if 'test@' in msg.to[0]:
                    # print(f"{msg.date=}")
                    print(f"\n{msg.date_str=}")
                    print(f"{msg.from_=}")
                    # print(f"{msg.from_values.name=}")
                    print(f"{msg.to=}")
                    print(f"{msg.subject=}")
                    
                    print(f"✅ DELETING {msg.uid=}")
                    mailbox.delete([msg.uid])
                    count_deleted += 1

                    print()
        except:
            count_errors += 1
            continue

        ## BASED ON FROM FIELD
        try:
            if any(ele in msg.from_ for ele in delete_if_in_from):
                print(f"\n{msg.date_str=}")
                print(f"{msg.from_=}")
                print(f"{msg.to=}")
                print(f"{msg.subject=}")
                
                print(f"✅ DELETING {msg.uid=}")
                mailbox.delete([msg.uid])
                count_deleted += 1

                print()
        except:
            count_errors += 1
            continue

        ## BASED ON SUBJECT FIELD
        try:
            if any(ele in msg.subject for ele in delete_if_in_subject):
                print(f"\n{msg.date_str=}")
                print(f"{msg.from_=}")
                print(f"{msg.to=}")
                print(f"{msg.subject=}")
                
                print(f"✅ DELETING {msg.uid=}")
                mailbox.delete([msg.uid])
                count_deleted += 1

                print()
        except:
            count_errors += 1
            continue

########################################################################################################

if __name__ == '__main__':
    print()
    print('-------------------------------')
    print(f"Count Total Emails = {count:,} emails found")
    print(f"Count Emails Processed = {count_processed} emails processed")
    print(f"Count Mark As Read = {count_mark_as_read}")
    print(f"Count set_new_emails = {len(set_new_emails)}")
    print(f"count_errors = {count_errors}")
    print(f"Email DELETED = {count_deleted}")
    print()

    if len(set_emails_dne) > 0:
        print("set_emails_dne:")
        for emails_dne in set_emails_dne:
            print(emails_dne)
        print('set_emails_dne: ', len(set_emails_dne))

    print('-------------------------------')
    run_time = round((time.time() - start_time)/60, 1)
    print(f"{os.path.basename(__file__)} finished in {run_time} minutes at {datetime.now().strftime('%H:%M:%S')}.")
    print()
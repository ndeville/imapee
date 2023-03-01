from datetime import datetime
print(f"Starting at {datetime.now().strftime('%H:%M:%S')}")
import time
start_time = time.time()
ts = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"

import os

from dotenv import load_dotenv
load_dotenv()
PATH_INDEXEE = os.getenv("PATH_INDEXEE")
PATH_SCRAPEE = os.getenv("PATH_SCRAPEE")
BTOB_DB_FILE = os.getenv("BTOB_DB_FILE")

#####
import sys
sys.path.append(PATH_INDEXEE)
sys.path.append(PATH_SCRAPEE)

import my_utils
import dbee
import sqlite3

import pprint
pp = pprint.PrettyPrinter(indent=4)
print()
count = 0
####################

v = False # verbose True or False

### ADD namedtuple Contact to get First name instead of just set of emails

## DEPRECATED with validate.validate_email()
# blacklist_domains = dbee.get_blacklist_domains()
# blacklist_email_prefixes = dbee.get_blacklist_email_prefixes()
# list_blacklist_emails = dbee.get_blacklist_emails()
# list_existing_emails = dbee.get_existing_emails()

EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT_INBOX")
PASSWORD = os.getenv("PASSWORD_INBOX")

set_emails = set() # Set of dicts: {email: , src:, first: }

from imap_tools import MailBox, AND, MailMessageFlags
import re

# EMAIL_REGEX = r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""
EMAIL_REGEX = r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+"

print()

with MailBox('imap.gmail.com').login(EMAIL_ACCOUNT, PASSWORD) as mailbox:
    for msg in mailbox.fetch(mark_seen=False):
    # for msg in mailbox.fetch(AND(from_='Mail Delivery'), mark_seen=False):
        count += 1
        print(f"{'imapee_INBOX'} | {datetime.now().strftime('%H:%M:%S')} | {count}")
        if v:
            print('---------------')
            print('msg.uid', type(msg.uid), '------', msg.uid)
            print('msg.from_', type(msg.from_), '------', msg.from_)
            # print('msg.to', type(msg.to), '------', msg.to)
            print('msg.flags', type(msg.flags), '------', msg.flags)
            print('msg.date_str', type(msg.date_str), '------', msg.date_str)
        #     print('msg.from_values', type(msg.from_values), '------', msg.from_values)
            print('msg.from_values_name', type(msg.from_values.name), '------', msg.from_values.name)
            print('msg.from_values_email', type(msg.from_values.email), '------', msg.from_values.email)
            print('msg.subject', type(msg.subject), '------', msg.subject)
            print()

        ## Get email From sender 
        email_sender = msg.from_values.email.strip().lower()
        if email_sender not in set_emails:
            if dbee.validate_email(email_sender,v=False):
                if v:
                    print('email_sender', type(email_sender), '------', email_sender)
                set_emails.add(email_sender)
        
        ## Get email from Cc
        emails_cc = msg.cc_values
        if len(emails_cc) > 0:
            for contact in emails_cc:
                email_cc = contact.email
                if email_cc not in set_emails:
                    if dbee.validate_email(email_cc,v=False):
                        if v:
                            print('email_cc', type(email_cc), '------', email_cc)
                        set_emails.add(email_cc)

        # print('msg.text', type(msg.text), '------', msg.text)
        # print('msg.html', type(msg.html), '------', msg.html)
        if v:
            print()

        ## Get emails in HTML Body
        for re_match in re.finditer(EMAIL_REGEX, msg.html.lower()):
            new_email_from_html = re_match.group()
            new_email_from_html = new_email_from_html.strip().lower()
            if new_email_from_html not in set_emails:
                if dbee.validate_email(new_email_from_html,v=False):
                    if v:
                        print('new_email_from_html', type(new_email_from_html), '------', new_email_from_html)
                    set_emails.add(new_email_from_html)

        ## Get emails in Text Body
        for re_match in re.finditer(EMAIL_REGEX, msg.text.lower()):
            new_email_from_text = re_match.group()
            new_email_from_text = new_email_from_text.strip().lower()
            if new_email_from_text not in set_emails:
                if dbee.validate_email(new_email_from_text,v=False):
                    if v:
                        print('new_email_from_text', type(new_email_from_text), '------', new_email_from_text)
                    set_emails.add(new_email_from_text)

        # # Mark email as Unread
        # mailbox.flag(msg.uid, MailMessageFlags.SEEN, False)

    # mailbox.flag(mailbox.fetch(AND(from_="Milsom")), MailMessageFlags.SEEN, False)


# ADD TO DB 

db = sqlite3.connect(BTOB_DB_FILE)
c = db.cursor()

list_new = []

print(f"\nset_emails: {set_emails}\n")

for email in set_emails:
    first = my_utils.first_from_email(email)
    print(f"First: {first}")
    domain = my_utils.domain_from_email(email)
    list_new.append( 
        (
            email.strip().lower(),
            first,
            domain,
            'WN',
            f"{os.path.basename(__file__)[:-3]}_{ts}",
            f"{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        )
    )

create_query = """
		INSERT INTO contacts 
		(email, first, domain, db, src, created)
		VALUES (?,?,?,?,?,?)
		"""
    
c.executemany(create_query, list_new)

db.commit()
db.close()

print()
if len(list_new) > 0:
    count_new_email = 0
    for new_email in list_new:
        count_new_email += 1
        print(count_new_email, '\t', new_email)

    print(f"\n{len(list_new)} NEW emails added to Contacts.")
else:
    print(f"NO new emails added to Contacts this time round.")

########################################################################################################

if __name__ == '__main__':
    print()
    print('-------------------------------')
    print(f"Count Messages = {count} messages.")
    print(f"New email addresses = {len(set_emails)} email addresses found.")

    print('-------------------------------')
    run_time = round((time.time() - start_time)/60, 1)
    print(f'{os.path.basename(__file__)} finished in {run_time} minutes.')
    print()
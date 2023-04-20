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
# DRYFTA EMAIL AUTOMATIN

import my_utils

v = False

EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT_DR")
PASSWORD = os.getenv("PASSWORD_DR")
EMAIL_SERVER = os.getenv("EMAIL_SERVER_DR")

EMAIL_REGEX1 = r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""
EMAIL_REGEX = r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+"

set_emails = set() 

set_emails_dne = set() # Set of dicts: {email: , src:, first: }
set_new_emails = set()
set_email_checked = set()
added_to_WN_contacts = []
updated_in_WN001 = []

mail_error_prefixes = [
    'mailer-daemon',
]

safe_domains = (
    'dryfta.com',
    'skoolsonline.com',
)

list_emails_errors = []

count_processed = 0
count_errors = 0
count_mark_as_read = 0
count_deleted = 0

# FUNCTIONS


def get_tuple_from_file(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
    # Remove trailing newline characters and create tuple
    return tuple(line.strip() for line in lines)





# MAIN

def process(v=False):
    global count
    global count_processed
    global count_errors
    global count_mark_as_read
    global count_deleted
    global set_emails
    global set_emails_dne
    global set_new_emails
    global set_email_checked
    global added_to_WN_contacts
    global updated_in_WN001
    global list_emails_errors


    with MailBox(EMAIL_SERVER).login(EMAIL_ACCOUNT, PASSWORD) as mailbox:

        # for msg in mailbox.fetch(AND(from_='Mail Delivery'), mark_seen=False): # example with search string
        for msg in mailbox.fetch(mark_seen=False, reverse=False, bulk=True): # get all emails from most recent without changing read status

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
            # email_sender = msg.from_values.email.strip().lower()
            email_sender = my_utils.validate_email_format(msg.from_values.email.strip().lower())
            if email_sender != False:
                if v:
                    print('email_sender', type(email_sender), '------', email_sender)
                set_emails.add(email_sender)
            else:
                print(f"❌ EMAIL FORMAT ERROR: email_sender is not valid: {email_sender}")
            
            ## Get email from Cc
            emails_cc = msg.cc_values
            if len(emails_cc) > 0:
                for contact in emails_cc:
                    # email_cc = contact.email
                    email_cc = my_utils.validate_email_format(contact.email.strip().lower())
                    if email_cc != False:
                        if my_utils.validate_email_format(email_cc):
                            if v:
                                print('email_cc', type(email_cc), '------', email_cc)
                            set_emails.add(email_cc)
                    else:
                        if v:
                            print(f"❌ EMAIL FORMAT ERROR: email_cc is not valid: {email_cc}")

            # print('msg.text', type(msg.text), '------', msg.text)
            # print('msg.html', type(msg.html), '------', msg.html)
            if v:
                print()

            ## Get emails in HTML Body
            for re_match in re.finditer(EMAIL_REGEX, msg.html.lower()):
                new_email_from_html = re_match.group()
                # new_email_from_html = new_email_from_html.strip().lower()
                new_email_from_html = my_utils.validate_email_format(new_email_from_html.strip().lower())
                if new_email_from_html != False:
                    # if my_utils.validate_email_format(new_email_from_html):
                    if v:
                        print('new_email_from_html', type(new_email_from_html), '------', new_email_from_html)
                    set_emails.add(new_email_from_html)
                else:
                    if v:
                        print(f"❌ EMAIL FORMAT ERROR: new_email_from_html is not valid: {new_email_from_html}")

            ## Get emails in Text Body
            for re_match in re.finditer(EMAIL_REGEX, msg.text.lower()):
                new_email_from_text = re_match.group()
                # new_email_from_text = new_email_from_text.strip().lower()
                new_email_from_text = my_utils.validate_email_format(new_email_from_text.strip().lower())
                if new_email_from_text != False:
                    # if my_utils.validate_email_format(new_email_from_text):
                    if v:
                        print('new_email_from_text', type(new_email_from_text), '------', new_email_from_text)
                    set_emails.add(new_email_from_text)
                else:
                    if v:
                        print(f"❌ EMAIL FORMAT ERROR: new_email_from_text is not valid: {new_email_from_text}")

            # MAIL ERRORS
            for error_prefix in mail_error_prefixes:
                if error_prefix in msg.from_.lower():

                    count_errors += 1

                    if v:
                        print(f"\n❌ MAIL ERROR {count} - {msg.from_}")
                        print(f"From: {msg.subject}")
                        # print(f"To: {msg.to}")
                        # print(f"Date: {msg.date}")
                        # print(f"Date_str: {msg.date_str}")
                        # print(f"Body: {msg.text}")

                    error_email = set()

                    for re_match in re.finditer(EMAIL_REGEX, msg.text.lower()):
                        potential_error_email = my_utils.validate_email_format(re_match.group().strip().lower())
                        if potential_error_email != False:
                            if not potential_error_email.endswith(safe_domains):
                                error_email.add(potential_error_email)
                    
                    if len(error_email) == 1:
                        error_email = next(iter(error_email))
                        if v:
                            print(f"✅ potential_error_email: {error_email}")
                        list_emails_errors.append(error_email)


                    # if MDS: 
                    #     - update to DNE & add 'MDS' in notes
                    #     - lookup any other email on 'HOLD' for same domain with first available and not '-'


                    else:
                        if v:
                            print(f"❌ conflicting error emails: {error_email}")
                        for e in error_email:
                            list_emails_errors.append(e)

                    # Mark Error Email as Read
                    if not __name__ == '__main__':
                        mailbox.flag(msg.uid, MailMessageFlags.SEEN, True)
    
    # Dedupe
    list_emails_errors = list(set(list_emails_errors))

    return list_emails_errors

        # DB updates

        # if 'automat' in subject.lower():







# print(f"\n\n\nSET EMAILS: {len(set_emails)}\n")
# pp.pprint(set_emails)

########################################################################################################

if __name__ == '__main__':

    process(v=True)
    print(f"\nlist_emails_errors:")
    for i, email_error in enumerate(list_emails_errors):
        print(i+1, email_error)

    print()
    print('-------------------------------')
    print(f"Count Total Emails = {count} emails found")
    print(f"Count Emails Processed = {count_processed} emails processed")
    print(f"Count Mark As Read = {count_mark_as_read}")
    print(f"Count set_new_emails = {len(set_new_emails)}")
    print(f"count_errors = {count_errors}")
    print(f"Email DELETED = {count_deleted}")
    print()

    
    if len(set_emails_dne) > 0:
        # print("set_emails_dne:")
        # for emails_dne in set_emails_dne:
        #     print(emails_dne)
        print('set_emails_dne: ', len(set_emails_dne))

    print('-------------------------------')
    
    run_time = round((time.time() - start_time), 3)
    if run_time < 1:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time*1000)}ms at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 60:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time)}s at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 3600:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/60)}mns at {datetime.now().strftime("%H:%M:%S")}.\n')
    else:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/3600, 2)}hrs at {datetime.now().strftime("%H:%M:%S")}.\n')
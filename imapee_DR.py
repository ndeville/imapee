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

# IMPORTS

import my_utils
import re
from tqdm import tqdm


# GLOBALS

v = False

EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT_DR")
PASSWORD = os.getenv("PASSWORD_DR")
EMAIL_SERVER = os.getenv("EMAIL_SERVER_DR")

EMAIL_REGEX1 = r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""
EMAIL_REGEX = r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+"

set_emails = set() 

emails = [] # List of Email objects

set_emails_dne = set() # Set of dicts: {email: , src:, first: }
set_new_emails = set()
set_email_checked = set()
added_to_WN_contacts = []
updated_in_WN001 = []

mail_error_prefixes = (
    'mailer-daemon',
    'no-reply@tmes.trendmicro.eu', # Undelivered Mail
    'noreply@esa4.umd.iphmx.com', # Undelivered Mail
    'postmasters@uci.edu', # Undelivered Mail
    'postmaster', # Undelivered Mail
)

blacklist_prefix = (
    'noreply',
    'no-reply',
    'no_reply',
    'no.reply',
    'notify',
    'thehubspotteam',
    'analytics-',
)

safe_domains = (
    'dryfta.com',
    'skoolsonline.com',
)

list_emails_errors = []

count_processed = 0
count_errors = 0
count_mark_as_read = 0
count_deleted = 0


# CLASSES


class Email:
    def __init__(
        self,
        uid,
        from_,
        flags,
        date_str,
        date,
        from_values_name,
        from_values_email,
        subject,
        text,
        cc,
    ):
        self.uid = uid
        self.from_ = from_
        self.flags = flags
        self.date_str = date_str
        self.date = date
        self.from_values_name = from_values_name
        self.from_values_email = from_values_email.lower()
        self.subject = subject
        self.text = text
        self.cc = cc

    def __str__(self):
        return (
            f"uid:{' ' * (15 - len('uid'))}\t{self.uid}\n"
            f"from_:{' ' * (15 - len('from_'))}\t{self.from_}\n"
            f"flags:{' ' * (15 - len('flags'))}\t{', '.join(self.flags)}\n"
            f"date_str:{' ' * (15 - len('date_str'))}\t{self.date_str}\n"
            f"date:{' ' * (15 - len('date'))}\t{self.date}\n"
            f"from_values_name:{' ' * (15 - len('from_values_name'))}\t{self.from_values_name}\n"
            f"from_values_email:{' ' * (15 - len('from_values_email'))}\t{self.from_values_email}\n"
            f"subject:{' ' * (15 - len('subject'))}\t{self.subject}\n"
            f"cc:{' ' * (15 - len('cc'))}\t{', '.join(str(email_addr.email) for email_addr in self.cc)}\n"
            f"text:{' ' * (15 - len('text'))}\t(edited out)\n"
        )




# FUNCTIONS


def get_tuple_from_file(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
    # Remove trailing newline characters and create tuple
    return tuple(line.strip() for line in lines)


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
    global emails


    with MailBox(EMAIL_SERVER).login(EMAIL_ACCOUNT, PASSWORD) as mailbox:

        # for msg in mailbox.fetch(AND(from_='Mail Delivery'), mark_seen=False): # example with search string
        for msg in tqdm(mailbox.fetch(mark_seen=False, reverse=False, bulk=True)): # get all emails from most recent without changing read status

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

            # if v:
            #     print('---------------')
            #     print('msg.uid', type(msg.uid), '------', msg.uid)
            #     print('msg.from_', type(msg.from_), '------', msg.from_)
            #     # print('msg.to', type(msg.to), '------', msg.to)
            #     print('msg.flags', type(msg.flags), '------', msg.flags)
            #     print('msg.date_str', type(msg.date_str), '------', msg.date_str)
            #     print('msg.date', type(msg.date), '------', msg.date)
            # #     print('msg.from_values', type(msg.from_values), '------', msg.from_values)
            #     print('msg.from_values_name', type(msg.from_values.name), '------', msg.from_values.name)
            #     print('msg.from_values_email', type(msg.from_values.email), '------', msg.from_values.email)
            #     print('msg.subject', type(msg.subject), '------', msg.subject)
            #     print()


            # email_obj = Email(
            #     uid=msg.uid,
            #     from_=msg.from_,
            #     flags=msg.flags,
            #     date_str=msg.date_str,
            #     date=msg.date,
            #     from_values_name=msg.from_values.name,
            #     from_values_email=msg.from_values.email,
            #     subject=msg.subject,
            #     text=msg.text
            # )

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


            email_obj = Email(
                    uid=msg.uid,
                    from_=msg.from_,
                    flags=msg.flags,
                    date_str=msg.date_str,
                    date=msg.date,
                    from_values_name=msg.from_values.name,
                    from_values_email=msg.from_values.email,
                    subject=msg.subject,
                    text=msg.text,
                    cc=msg.cc_values,
                )
            
            emails.append(email_obj)
    
    # Dedupe
    list_emails_errors = list(set(list_emails_errors))

    # return list_emails_errors
    return emails

        # DB updates

        # if 'automat' in subject.lower():



def get_list_emails_errors():
    # process() # TODO extract out to be called only once when importing script
    return list(set(list_emails_errors))


def get_all_emails(v=False):
    if v:
        for count_e, email in enumerate(emails):
            print(f"\n\n======= {count_e + 1} =======")
            print(email)
    return emails

def get_all_from_emails():
    return list(set([email.from_.lower() for email in emails]))


def get_dict_from_emails_with_date_and_message(v=True):

    email_list = emails

    email_dict = {}
    
    for email_obj in email_list:
        email = email_obj.from_values_email
        subject = email_obj.subject.lower()


        if (not email.startswith(blacklist_prefix)) and (not email.startswith(mail_error_prefixes)) and (not email.endswith(safe_domains)):

            if 'auto' not in subject:
        
                # Format email text
                text = email_obj.text[:200].strip()
                if '\n' in text:
                    text = text.replace('\n', ' ')
                if '\r' in text:
                    text = text.replace('\r', ' ')
                # Remove extra spaces
                text = re.sub(' +', ' ', text)
                # Remove original email
                if 'From:' in text:
                    text = text.split('From:')[0]
                # Remove intro

                intros = [
                    'Hi Nicolas,',
                    'Hello Nicolas,',
                    'Dear Nicolas,',
                    'Dear Nic,',
                    'Thank you Nicolas',
                    'Thank you, Nicholas',
                    'Thank you Nicholas',
                    'Hi Nic,',
                    'Good morning Nicole,',
                    'Good morning Nic, ',
                    'Good morning Nicolas, ',
                ]

                for intro in intros:
                    if intro in text:
                        text = text.split(intro)[1]


                # Remove signature

                outros = [
                    'Best,',
                    'Thanks,',
                    'Regards,',
                    'Kind',
                ]

                for outro in outros:
                    if outro in text:
                        text = text.split(outro)[0]
                
                # Check if the email is already in the dictionary
                if email in email_dict:
                    # Update the date if the current email is older
                    if email_obj.date < email_dict[email][0]:
                        email_dict[email] = (email_obj.date, text, subject)
                else:
                    email_dict[email] = (email_obj.date, text, subject)

    return email_dict


def get_automated_replies():
    # TODO expand on logic
    return [email for email in emails if 'auto' in email.subject.lower()]


# MAIN

# Load all Emails in `emails` list
process()

# get_all_emails()

# emails_dict = get_dict_from_emails_with_date_and_message()

# for k,v in emails_dict.items():
#     print(f"\n\n========= {k}")
#     print(v[0])
#     print(repr(v[1]))
#     print(f"\nsubject: {v[2]}")



# print(f"\n\n\nSET EMAILS: {len(set_emails)}\n")
# pp.pprint(set_emails)

########################################################################################################

if __name__ == '__main__':

    # process(v=True)
    # print(f"\nlist_emails_errors:")
    # for i, email_error in enumerate(list_emails_errors):
    #     print(i+1, email_error)

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
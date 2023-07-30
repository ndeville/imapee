"""
SCRIPT for webinar_platform@hubilo.cloud & @hubilo-webinar.com
to get webinar vendors
"""

from datetime import datetime
print(f"Starting at {datetime.now().strftime('%H:%M:%S')}")
ts_db = f"{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
import time
start_time = time.time()

import os

from dotenv import load_dotenv
load_dotenv()
PATH_INDEXEE = os.getenv("PATH_INDEXEE")
DB_BTOB = os.getenv("DB_BTOB")

import sys
sys.path.append(PATH_INDEXEE)

from dotenv import load_dotenv
load_dotenv()


from imap_tools import MailBox, AND, MailMessageFlags
import re
from DB.tools import select_all_records, update_record, create_record, delete_record

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

from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse


# GLOBALS

test = 1
verbose = 1
delete = 0

# if not test:
#     import backup_db

# EMAIL_HUBILO_CLOUD = os.getenv("EMAIL_HUBILO_CLOUD")
# PASSWORD_HUBILO_CLOUD = os.getenv("PASSWORD_HUBILO_CLOUD")
# SERVER_HUBILO_CLOUD= os.getenv("SERVER_HUBILO_CLOUD")

EMAIL_HUBILO_WEBINAR_COM = os.getenv("EMAIL_HUBILO_WEBINAR_COM")
PASSWORD_HUBILO_WEBINAR_COM = os.getenv("PASSWORD_HUBILO_WEBINAR_COM")
SERVER_HUBILO_WEBINAR_COM= os.getenv("SERVER_HUBILO_WEBINAR_COM")


email_accounts = {
    'webinar_platform@hubilo.cloud': {
        'password': os.getenv("PASSWORD_HUBILO_CLOUD"),
        'server': os.getenv("EMAIL_SERVER_WEBINAR_HUBILO_CLOUD"),
    },
    'nicolas@hubilo-webinar.com': {
        'password': os.getenv("PASSWORD_WEBINAR_HUBILO_WEBINAR"),
        'server': os.getenv("EMAIL_SERVER_WEBINAR_HUBILO_WEBINAR"),
    },
}


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
    'mailer-daemon',
)

blacklist_url = [
    'http://www.mailchimp.com/email-referral/',
    'http://pages.qualtrics.com/',
    'qualtrics.com/',
    'memberclicks.com',
]

safe_domains = (
    'dryfta.com',
    'skoolsonline.com',
    'webinar.net',
)

blacklist_emails = list(my_utils.get_all_vendors_domains()) + [
    'support@google.com',
    'report@microsoft.com',
    '@amazonses.com',
    'postmaster',
    'mailer-daemon',
]

list_emails_errors = []

count_processed = 0
count_errors = 0
count_mark_as_read = 0
count_deleted = 0
count_total = 0
count_records_created = 0

uids = set()

existing_emails = my_utils.get_all_people_emails()


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


vendors_domains = my_utils.get_all_vendors_domains()


def extract_urls_with_domain(html_code):
    global vendors_domains
    global blacklist_url

    urls = []
    soup = BeautifulSoup(html_code, 'html.parser')

    class URL:
        def __init__(self, domain, url):
            self.domain = domain
            self.url = url

        def __str__(self):
            return f"URL(domain={self.domain}, url={self.url})"
    
    # Find all <a> tags in the HTML
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:

            # Parse the URL to extract the domain name
            parsed_url = urlparse(href)

            if not any(blacklist_element in href for blacklist_element in blacklist_url):

                url_domain = parsed_url.netloc.lower()
                
                # Check if the domain name is in the specified list
                for domain in vendors_domains:
                    
                    if f".{domain}" in url_domain or f"/{domain}" in url_domain:

                        urls.append(URL(domain=domain, url=href))

                        # break  # Break out of the inner loop if a match is found
    
    return urls



def process(EMAIL_SERVER, EMAIL_ACCOUNT, PASSWORD):
    global count_total
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
    global count_records_created
    global existing_emails
    global blacklist_emails
    
    verbose = True

    delete_uids = []


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

            count_processed += 1

            ## Get email From sender 

            # email_sender = msg.from_values.email.strip().lower()
            email_sender = my_utils.validate_email_format(msg.from_values.email.strip().lower())

            if verbose:
                print(f"\n\n\n========= {count_processed}\nemail_sender: {email_sender}\nsubject: {msg.subject}\n")

            if type(email_sender) == str:

                email_sender_domain = my_utils.domain_from_email(email_sender)

                # Extract vendor URLS from body

                if email_sender_domain not in vendors_domains:

                    vendors_in_email = extract_urls_with_domain(msg.html.lower())

                    if len(vendors_in_email) > 0:

                        for vendor in vendors_in_email:

                            count += 1    

                            if verbose:
                                print(f"\n✅\t{vendor.domain} used by {email_sender_domain} with URL: {vendor.url}")

                            if not test:

                                # ADD to using_vendor table

                                uid = f"{email_sender_domain}-{vendor.domain}"

                                if uid not in uids:

                                    try:
                                        create_record(DB_BTOB, 'using_vendor', {
                                            'domain': email_sender_domain,
                                            'vendor': vendor.domain,
                                            'url': vendor.url,
                                            'src': f'imapee_HU_WebReg {ts_db}',
                                            'created': ts_db,
                                        })

                                        count_records_created += 1

                                    except:
                                        print(f"\n❌ using_vendor: {email_sender_domain}-{vendor.domain} already in DB")
                                        continue

                                    # ADD to webinar table

                                    try:
                                        create_record(DB_BTOB, 'webinars', {
                                            'website_org': email_sender_domain,
                                            'domain': email_sender_domain,
                                            'url_reg': vendor.url,
                                            'webinar_provider': vendor.domain,
                                            'src': f'imapee_HU_WebReg {ts_db}',
                                            'created': ts_db,
                                        })

                                        count_records_created += 1

                                    except:
                                        print(f"\n❌ webinar {vendor.url} already in DB")
                                        continue

                                    uids.add(uid)




                # Add email to DB

                if email_sender not in existing_emails and not any(blacklist_element in email_sender for blacklist_element in blacklist_emails):

                    if not test:

                        try:
                            create_record(DB_BTOB, 'people', {
                                'email': email_sender,
                                'domain': email_sender_domain,
                                'src': f'imapee_HU_WebReg {ts_db}',
                                'created': ts_db,
                            })

                            count_records_created += 1

                        except:
                            print(f"\n❌ {email_sender} already in DB")
                            continue
                    
                    else:

                        print(f"\nℹ️  \t{email_sender} to be added to DB")

                    existing_emails.append(email_sender)


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

            if delete:

                delete_uids.append(msg.uid)

                print(f"❌ Added to delete: {msg.uid} - {msg.subject}")
    

        if len(delete_uids) > 0:

            mailbox.delete(delete_uids)

    # return list_emails_errors
    return emails


process(SERVER_HUBILO_WEBINAR_COM, EMAIL_HUBILO_WEBINAR_COM, PASSWORD_HUBILO_WEBINAR_COM)


########################################################################################################

if __name__ == '__main__':

    print()
    print('-------------------------------')
    print(f"Count Emails Processed = {count_processed}")
    print(f"count vendors found = {count}")
    # print(f"Count Mark As Read = {count_mark_as_read}")
    # print(f"Count set_new_emails = {len(set_new_emails)}")
    # print(f"count_errors = {count_errors}")
    # print(f"Email DELETED = {count_deleted}")
    print(f"count_records_created = {count_records_created}")
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
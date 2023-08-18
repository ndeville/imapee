"""
SCRIPT for webinar_platform@hubilo.cloud & @hubilo-webinar.com
to get webinar vendors
"""

from datetime import datetime
print(f"\nStarting at {datetime.now().strftime('%H:%M:%S')}")
ts_db = f"{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
import time
start_time = time.time()

import os

from dotenv import load_dotenv
load_dotenv()
PATH_INDEXEE = os.getenv("PATH_INDEXEE")
PATH_LINKEDINEE = os.getenv("PATH_LINKEDINEE")
DB_BTOB = os.getenv("DB_BTOB")

import sys
sys.path.append(PATH_INDEXEE)
sys.path.append(PATH_LINKEDINEE)

from dotenv import load_dotenv
load_dotenv()


from imap_tools import MailBox, AND, MailMessageFlags
import re
from DB.tools import select_all_records, update_record, create_record, delete_record

import check_proxycurl

import pprint
pp = pprint.PrettyPrinter(indent=4)
print()
count = 0
####################
# HUBILO WEBINAR REGISTRATION

# IMPORTS

import my_utils
import re
from tqdm import tqdm

from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
from typing import List, Dict, Tuple, Set, Union


# LOGGING
# logger = my_utils.setup_logger(__name__, log_file='log.log', level=logging.INFO)

import logging
logger = my_utils.setup_logger(log_file='log.log', level=logging.INFO)


# GLOBALS

test = 1
# verbose = 1
check_with_proxycurl = 0
delete = 0


# if not test:
#     import backup_db

# EMAIL_HUBILO_CLOUD = os.getenv("EMAIL_HUBILO_CLOUD")
# PASSWORD_HUBILO_CLOUD = os.getenv("PASSWORD_HUBILO_CLOUD")
# SERVER_HUBILO_CLOUD= os.getenv("SERVER_HUBILO_CLOUD")

EMAIL_HUBILO_WEBINAR_COM = os.getenv("EMAIL_HUBILO_WEBINAR_COM")
PASSWORD_HUBILO_WEBINAR_COM = os.getenv("PASSWORD_HUBILO_WEBINAR_COM")
SERVER_HUBILO_WEBINAR_COM= os.getenv("SERVER_HUBILO_WEBINAR_COM")

# To be used later
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

existing_emails_in_people = my_utils.get_all_people_emails()
existing_emails = my_utils.get_all_people_emails()
existing_emails_in_mailingee = my_utils.get_all_mailingee_emails()

set_emails_dne = set() # Set of dicts: {email: , src:, first: }
set_new_emails = set()
set_email_checked = set()

domains_in_this_run = []

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

socials_domains = [
    'facebook.com',
    'twitter.com',
    'linkedin.com',
    'instagram.com',
    'youtube.com',
]

safe_domains = (
    'dryfta.com',
    'skoolsonline.com',
    'webinar.net',
)

vendors_domains = my_utils.get_all_vendors_domains_with_og_domain()

blacklist_emails = list(vendors_domains) + list(socials_domains) + [
    'support@google.com',
    'report@microsoft.com',
    '@amazonses.com',
    'postmaster',
    'mailer-daemon',
    'register@hubilo-webinar.com',
    '.png',
    'optout',
    'privacy',
    'noreply',
    'no-reply',
    'no_reply',
    'no.reply',
    'notify',
    'thehubspotteam',
    'analytics-',
    'mailer-daemon',
    'register@hubilo-webinaar.com',
    'news@',
    'do_not_reply',
    'hubilo-webinar.com',
]

blacklist_subject = [
    "Sorry you couldn't attend this Webcast",
]

register_links = [
    'https://global.gotowebinar.com/join/',

]

list_emails_errors = []

count_processed = 0
count_errors = 0
count_mark_as_read = 0
count_deleted = 0
count_total = 0
count_records_created = 0

uids = set()

email_collector = {}


# CLASSES



class SenderDomain:
    def __init__(self):
        self.email_direct = ""
        self.email_indirect = ""
        self.vendor = ""

    def __str__(self):
        return f"SenderDomain(email_direct={self.email_direct}, email_indirect={self.email_indirect}, vendor={self.vendor})"


class EmailData:
    def __init__(self):
        self.sender_domain = ""
        self.emails = ""
        self.vendor_domain = ""
        self.webinar_title = ""
        self.url_reg = ""

    def __str__(self):
        return f"""
        EmailData(
            sender_domain\t{self.sender_domain}
            emails\t\t{self.emails}
            vendor_domain\t{self.vendor_domain}
            webinar_title\t{self.webinar_title}
            url_reg\t\t{self.url_reg}
        """



# FUNCTIONS


def get_emails(email_html_text) -> Set:

    set_emails = set() # start with set to avoid duplicates

    email_regex = r"(?:href=\"mailto:)?([a-zA-Z0-9_.+-]+(?:@|\(at\))[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"

    matches = re.findall(email_regex, email_html_text)

    if len(matches) > 0:

        for match in matches:
            if '(at)' in match:
                match = match.replace('(at)','@')
            email = match.strip().lower()
            parts = email.split('@')
            email_domain = parts[1]

            if not any(ele in email for ele in blacklist_emails):

                if email_domain not in vendors_domains:

                    valid_email = my_utils.validate_email_format(email)

                    # Validate function returns cleaned up email if typo, else False if non-valid format
                    if valid_email != False and valid_email not in set_emails:

                        set_emails.add(valid_email)

                        add_email_to_domain_dict(valid_email)

                        if valid_email not in existing_emails:

                            create_record(DB_BTOB, 'people', 
                                {
                                'email': valid_email,
                                'domain': my_utils.domain_from_email(valid_email),
                                'src': f"imapee_HU_WebReg {ts_db}",
                                # 'notes': f"Eventee {ts_db}",
                                'created': ts_db,
                                })
                            
                            existing_emails_in_people.append(valid_email)

                        # logger.info(f"ℹ️\tADDED {email} to set_emails")

    return set_emails





def socials(email_html_text):

    social_media_urls = {}
    soup = BeautifulSoup(email_html_text, 'html.parser')

    # Define regular expressions for different social media platforms
    social_media_regex = {
        'facebook': r'(?:https?:\/\/)?(?:www\.)?facebook\.com\/[^\/\n]+',
        'twitter': r'(?:https?:\/\/)?(?:www\.)?twitter\.com\/[^\/\n]+',
        'linkedin': r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/[^\/\n]+',
        'youtube': r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/[^\/\n]+',
    }

    for platform, regex in social_media_regex.items():
        urls = soup.find_all('a', href=re.compile(regex, re.IGNORECASE))
        for url in urls:
            # social_media_urls.append({platform: url['href']})
            social_media_urls[platform] = url['href']

    return social_media_urls







def extract_webinar_title(html_string):
    soup = BeautifulSoup(html_string, 'html.parser')

    title_element = soup.find('strong', string='Title:')

    if title_element:
        webinar_title = title_element.parent.find_next('span').text.strip()
        return webinar_title
    else:

        title_element = soup.find('span', {'class': 'mktoText em_cent em_font h3'})
        if title_element:
            return title_element.text.strip()

        else:
            return None




def extract_url_reg(html_text):
    global vendors_domains
    # Initialize an empty list to store the matched URLs
    matched_urls = set()

    # Create a BeautifulSoup object to parse the HTML text
    soup = BeautifulSoup(html_text, 'html.parser')

    # Find all anchor tags (links) in the HTML
    anchor_tags = soup.find_all('a', href=True)

    # Iterate through each anchor tag
    for tag in anchor_tags:
        url = tag['href']

        # Check if the URL contains any of the specified domain names
        if any(domain in url for domain in vendors_domains):

            # GTW
            if 'goto' in url:
                if 'gotowebinar.com/join/' in url:
                    matched_urls.add(my_utils.clean_long_url(url))
                else:
                    continue

            # ON24
            if 'on24' in url:
                if 'wcc' in url:
                    matched_urls.add(my_utils.clean_long_url(url))
                else:
                    continue

            # ZOOM
            if 'zoom' in url:
                if 'zoom.us/w/' in url:
                    matched_urls.add(my_utils.clean_long_url(url))
                else:
                    continue

            # CVENT
            if 'cvent' in url:
                if 'cvent.com/d/' in url:
                    matched_urls.add(my_utils.clean_long_url(url))
                else:
                    continue

            # EVENTBRITE
            if 'eventbrite' in url:
                if 'eventbrite.com/e/' in url:
                    matched_urls.add(my_utils.clean_long_url(url))
                else:
                    continue

            matched_urls.add(my_utils.clean_long_url(url))

    return matched_urls



def add_email_to_domain_dict(email):
    global email_collector
    domain = email.split('@')[1]
    if domain in email_collector:
        email_collector[domain].add(email)
    else:
        email_collector[domain] = {email}



EMAIL_SERVER = SERVER_HUBILO_WEBINAR_COM
EMAIL_ACCOUNT = EMAIL_HUBILO_WEBINAR_COM
PASSWORD = PASSWORD_HUBILO_WEBINAR_COM


delete_uids = []



with MailBox(EMAIL_SERVER).login(EMAIL_ACCOUNT, PASSWORD) as mailbox:

    for msg in mailbox.fetch(mark_seen=False, reverse=False, bulk=True): # get all emails from most recent without changing read status

        email_sender_domain = None
        vendor_domain = None
        non_vendor_emails = None
        cc_emails = None
        url_reg = None
        webinar_title = None
        clean_emails_list = None

        email_data = EmailData()



        count_processed += 1

        to_delete = False

        if count_processed < 1000000: # FOR TESTING ONLY

            ## Get email From sender 
            # email_sender = my_utils.validate_email_format(msg.from_values.email)
            email_sender = msg.from_values.email.strip().lower()

            print(f"\n\n\n========= {count_processed} / {email_sender}: {msg.subject}\n")


            # DELETE EMAILS

            blacklist_subject = [
                'Reminder: ',
                'Sorry you couldn\'t attend',
            ]

            blacklist_from = [
                'richard_mutkoski@agilent.com',
                'assp.org',
                'gartnerwebinars',
                'gartner.com',
                'hydac.co.uk',
                'zscaler.com',
                'five9.com',
                'ragan.com',
                'autotrader.co.uk',
            ]

            if any(ele in msg.subject for ele in blacklist_subject): # Add more logic here to delete emails

                print(f"❌ DELETE \t{msg.subject}")
                to_delete = True

            if any(ele in msg.from_ for ele in blacklist_from): # Add more logic here to delete emails

                print(f"❌ DELETE \tfrom {msg.from_}")
                to_delete = True


            # PROCESS EMAILS

            else:

                # EMAIL SENDER DOMAIN

                # Try to get email_sender_domain from email_sender
                if not any(ele in email_sender for ele in blacklist_emails):
                    email_sender_domain = my_utils.domain_from_email(email_sender)

                # Try to get domain from social links
                social_links = socials(msg.html)
                if check_with_proxycurl:
                    print(f"ℹ️  Checking with proxycurl, will cost credits.")
                    if email_sender_domain == None and len(social_links) > 0:
                        if 'linkedin' in social_links:
                            email_sender_domain = check_proxycurl.get_domain_from_linkedin(social_links['linkedin'])


                # NON-VENDOR EMAILS



                # Get all emails in email body
                non_vendor_emails = get_emails(msg.html.lower()) # -> set

                # Add email_sender to non_vendor_emails if not in vendors_domains
                if not any(ele in email_sender for ele in vendors_domains):
                    non_vendor_emails.add(email_sender)

                # Add Cc emails to non_vendor_emails if not in vendors_domains
                cc_emails = msg.cc
                if cc_emails and len(cc_emails) > 0:
                    for cc_email in cc_emails:
                        cc_email = my_utils.validate_email_format(cc_email)
                        if cc_email != False:
                            if not any(ele in cc_email for ele in vendors_domains):
                                non_vendor_emails.add(cc_email)

                # Add Reply-To emails to non_vendor_emails if not in vendors_domains
                reply_to_emails = msg.reply_to
                if reply_to_emails and len(reply_to_emails) > 0:
                    for reply_to_email in reply_to_emails:
                        if not any(ele in reply_to_email for ele in vendors_domains):
                            non_vendor_emails.add(reply_to_email)


                if email_sender_domain == None and len(non_vendor_emails) > 0:

                    email_sender_domain = my_utils.domain_from_email(list(non_vendor_emails)[0])




                # WEBINAR REGISTRATION URL

                # TODO
                url_reg = extract_url_reg(msg.html)

                # CLEAN EMAILS LIST
                clean_emails_list = [x for x in non_vendor_emails if not any(ele in x for ele in blacklist_emails) and not any(ele in x for ele in socials_domains)]

                # Try to get email_sender_domain from non_vendor_email if no email_sender_domain
                if email_sender_domain == None and len(clean_emails_list) > 0:

                    for email_found in clean_emails_list:

                        print(f"#626 email_found:\t{email_found=}")

                        # if not any(ele in email_found for ele in socials_domains) and not any(ele in email_found for ele in vendors_domains):
                        if not any(ele in email_sender for ele in blacklist_emails):

                            email_sender_domain = my_utils.domain_from_email(email_found)

                            break


                if email_sender_domain == None and url_reg != None:

                    print(f"ADD LOGIC to match my url_reg")



                if email_sender_domain != None:



                    # VENDOR DOMAIN

                    for vd in vendors_domains:

                        if vd in email_sender:

                            vendor_domain = vd

                            # logger.info(f"✅\t{vd} (from email_sender)")
                            print(f"✅\t{vd} (from email_sender)")

                            break

                    if vendor_domain == None:

                        for vd in vendors_domains:

                            if vd in msg.html.lower():

                                vendor_domain = vd

                                # logger.info(f"✅\t{vd} (from msg.html)")
                                print(f"✅\t{vd} (from msg.html)")

                                break

                    if vendor_domain != None:

                        vendor_domain = vendors_domains[vendor_domain]






                    # WEBINAR TITLE

                    webinar_title_cleaning = [
                        "You’ve Registered for ",
                        "Confirmation",
                        "Registration  to ",
                        "[Registration Confirmation]",
                        "Registration approved for Webex webinar:",
                        "Watch on-demand now:",
                        "Registration Confirmed -",
                        "You've Registered for the ",
                        "Webinar",
                    ]


                    webinar_title = None

                    # Get title from subject if first email ever received from this domain
                    if webinar_title == None and email_sender_domain not in domains_in_this_run:

                        webinar_title = msg.subject.strip()

                        # Cleaning
                        for wtc in webinar_title_cleaning:
                            if wtc in webinar_title:
                                webinar_title = webinar_title.replace(wtc, "")

                        webinar_title = webinar_title.strip()

                        if webinar_title == "Thank you for registering":

                            webinar_title = extract_webinar_title(msg.html)

                        domains_in_this_run.append(email_sender_domain)








                # # Construct an email object with all the info
                # email_obj = Email(
                #         uid=msg.uid,
                #         from_=msg.from_,
                #         flags=msg.flags,
                #         date_str=msg.date_str,
                #         date=msg.date,
                #         from_values_name=msg.from_values.name,
                #         from_values_email=msg.from_values.email,
                #         subject=msg.subject,
                #         text=msg.text,
                #         cc=msg.cc_values,
                #         vendor=vendor_domain,
                #         domain=email_sender_domain,
                #         emails=clean_emails_list,
                #         webinar_title=webinar_title,
                #         url_reg=url_reg
                #     )
                
                # emails.append(email_obj)

                # print(f"{email_obj}")


                campaigns = [
                    'on24.com',
                    'zoom.com',
                    'gotowebinar.com',
                ]

                # if not to_delete and email_obj.vendor != None:

                #     if email_obj.vendor in campaigns:

                #         if email_obj.domain != None and len(email_obj.emails) > 0 and email_obj.webinar_title != None:

                #             for email_to_add in email_obj.emails: # loop through all emails found in email

                #                 if email_to_add not in existing_emails_in_mailingee:

                #                     print(f"\n✅✅ ADD TO MAILINGEE: {email_obj}")

                #                     count_records_created += 1

                #                     existing_emails_in_mailingee.append(email_to_add)

                #         else:

                #             print(f"Missing elements in email_obj: {email_obj}")


                email_data.sender_domain = email_sender_domain
                email_data.vendor_domain = vendor_domain
                email_data.webinar_title = webinar_title
                email_data.emails = clean_emails_list
                email_data.url_reg = url_reg

                print(f"\n{email_data}")





        else:
            print(f"{count_processed} max_emails reached")



        if to_delete:

            print(f"TO DO: Deleting {msg.uid} emails...")

            mailbox.delete(msg.uid)

# # TODO
# - split email_direct/email_indirect
# - domain_vendor 
# - update Grist


# sort email_collector dict by keys
email_collector = dict(sorted(email_collector.items(), key=lambda item: item[0]))
print(f"\n\n{pp.pprint(email_collector)}")


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



# TODO
# - Check webinar title
# - Get OG vendor domains
# - Get domain from socials
# - Add emails to DB
# - Add to using_vendor table
# - Extract webinar registration URL
# - Add to Mailingee

# GOAL
# populate Grist DB with emails from inbox
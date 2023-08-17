from datetime import datetime
import os
ts_db = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
ts_time = f"{datetime.now().strftime('%H:%M:%S')}"
print(f"\n---------- {ts_time} starting {os.path.basename(__file__)}")
import time
start_time = time.time()

from dotenv import load_dotenv
load_dotenv()
DB_TWITTER = os.getenv("DB_TWITTER")
DB_BTOB = os.getenv("DB_BTOB")
DB_MAILINGEE = os.getenv("DB_MAILINGEE")
DB_EMAILEE = os.getenv("DB_EMAILEE")

import pprint
pp = pprint.PrettyPrinter(indent=4)

####################
# OUTBOXEE: log all outgoing emails to DB.emailee.outboxee

# IMPORTS (script-specific)

import my_utils
from imap_tools import MailBox, AND, MailMessageFlags
import grist_HU_ext

from DB.tools import select_all_records, update_record, create_record, delete_record

# GLOBALS

test = 1
verbose = 1

count_total = 0
count = 0
count_row = 0


# FUNCTIONS


import re

def remove_non_alphabet_leading_characters(input_str):
    # Define the regular expression pattern to match non-alphabet characters at the beginning
    pattern = r'^[^a-zA-Z]*'

    # Use the re.sub() function to remove the leading non-alphabet characters
    cleaned_str = re.sub(pattern, '', input_str)

    return cleaned_str


# MAIN


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



EMAIL_SERVER = SERVER_HUBILO_WEBINAR_COM
EMAIL_ACCOUNT = EMAIL_HUBILO_WEBINAR_COM
PASSWORD = PASSWORD_HUBILO_WEBINAR_COM


emails_in_grist = [x.email for x in grist_HU_ext.Webinars.fetch_table('Sent')]
print(f"\n{len(emails_in_grist)=}")


with MailBox(EMAIL_SERVER).login(EMAIL_ACCOUNT, PASSWORD, initial_folder=None) as mailbox:

    mailbox.folder.set('Gesendete Objekte')

    for msg in mailbox.fetch(mark_seen=False, reverse=False, bulk=True): # get all emails from most recent without changing read status

        count_total += 1

        # print(f"\n\n{count_total} {msg.date} {msg.to} {msg.subject}")

        for rcp in msg.to:

            rcp = rcp.lower().strip()

            subject = msg.subject
            if '\r\n' in subject:
                subject = subject.replace('\r\n', ' ')
            if '\n' in subject:
                subject = subject.replace('\n', ' ')

            # body = remove_non_alphabet_leading_characters(msg.text)[:100]
            body = remove_non_alphabet_leading_characters(msg.text)

            date_email = msg.date.strftime('%Y-%m-%d %H:%M')

            uid_email = f"{rcp}-{msg.date}-{subject}"

            from_email = msg.from_

            # ADD TO LOCAL DB
            
            # try:
            create_record(DB_EMAILEE, 'outboxee', {
                'date': date_email,
                'mailbox': from_email,
                'email': rcp,
                'subject': subject,
                'msg': body,
                'domain': my_utils.domain_from_email(rcp),
                'created': ts_db,
            })

            # except Exception as e:
            #     print(f"\n{msg.to} from {msg.date}: ERROR {e}\n")

            # ADD TO GRIST

            if rcp not in emails_in_grist:

                grist_HU_ext.Webinars.add_records('Sent', [
                                                {   'email': rcp,
                                                    'domain': my_utils.domain_from_email(rcp),
                                                    'subject': subject,
                                                    }
                                            ])

                emails_in_grist.append(rcp)









########################################################################################################

if __name__ == '__main__':
    print('\n\n-------------------------------')
    if 'count_total' in locals():
        print(f"\n{count_total=}")
    if 'count' in locals():
        print(f"{count=}")
    run_time = round((time.time() - start_time), 3)
    if run_time < 1:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time*1000)}ms at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 60:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time)}s at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 3600:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/60)}mns at {datetime.now().strftime("%H:%M:%S")}.\n')
    else:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/3600, 2)}hrs at {datetime.now().strftime("%H:%M:%S")}.\n')
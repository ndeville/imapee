from datetime import datetime
import os
ts_db = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
ts_time = f"{datetime.now().strftime('%H:%M:%S')}"
print(f"\n---------- {ts_time} starting {os.path.basename(__file__)}")
import time
start_time = time.time()

from dotenv import load_dotenv
load_dotenv()
DB_BTOB = os.getenv("DB_BTOB")
DB_MAILINGEE = os.getenv("DB_MAILINGEE")

import pprint
pp = pprint.PrettyPrinter(indent=4)

####################
# IMAPee Blacklist: extract bounced emails and delete specific emails
# Function to be used by indeXee in blacklist-emails.py
# 2024-12-31 10:24

# IMPORTS

# import my_utils
# from DB.tools import select_all_records, update_record, create_record, delete_record
import sqlite3

# GLOBALS

test = 0
verbose = 0
cleanup = 0 # Delete bounced email notifications

count_row = 0
count_total = 0
count = 0
count_deleted = 0


# FUNCTIONS


def get_bounced_emails(verbose=verbose):
    """
    Scans IMAP mailboxes for bounced emails and returns a set of unique bounced email addresses.
    
    Args:
        verbose (bool): If True, prints detailed processing information
    
    Returns:
        set: A set of unique email addresses that have bounced
    """
    from datetime import datetime
    import os
    import time
    from dotenv import load_dotenv
    import sqlite3
    from imap_tools import MailBox, AND
    import re

    global count_deleted

    load_dotenv()
    DB_BTOB = os.getenv("DB_BTOB")
    
    IGNORED_DOMAINS = {
        'audience-engage.com',
    }

    bounced_emails = set()
    total_messages_processed = 0

    with sqlite3.connect(DB_BTOB) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT user_name, password, imap_host 
            FROM email_accounts
        """)
        email_accounts = cur.fetchall()
        total_accounts = len(email_accounts)

    print(f"\nProcessing {total_accounts} email accounts to find bounced emails & delete warmup emails:")
    
    for account_idx, email_account in enumerate(email_accounts, 1):
        user_name, password, imap_host = email_account
        print(f"\n[{account_idx:,}/{total_accounts:,}] Checking {user_name}...", end='', flush=True)

        try:
            with MailBox(imap_host).login(user_name, password) as mailbox:
                messages = list(mailbox.fetch(mark_seen=False, reverse=True, bulk=True))
                msg_count = len(messages)
                print(f" found {msg_count:,} messages")

                for i, msg in enumerate(messages, 1):
                    if i % 100 == 0:  # Show progress every 100 messages
                        print(f"  Processing: {i}/{msg_count} messages", end='\r', flush=True)
                    
                    body_text = msg.text or msg.html or ""
                    
                    # Delete warmup emails
                    warmup_indicators = [
                        "basis-angry",
                        "water-class",
                        "chair-sense",
                        "fifty-uncle",
                        "might-smile",
                        "speak-chose",
                        "local-shown",
                        "depth-among",
                        "stand-exist",
                        "globe-lucky",
                        "curve-reach",
                        "order-slope",
                        "stage-about",
                        "solar-trunk",
                        "equal-uncle",
                        "broad-grade",
                        "sides-clear",
                        "human-brain",
                        "right-brick",
                        ]
                    if any(indicator in body_text.lower() for indicator in warmup_indicators):
                        print(f"ℹ️  Deleting warmup email #{msg.uid} from {user_name}")
                        mailbox.delete(msg.uid)
                        count_deleted += 1
                        continue
                    
                    # Delete emails coming from specific emails
                    from_emails = [
                        "Mail Delivery System",
                        "DAEMON",
                        "noreply@ionos.de",
                        "leo.pearce@claremontconsulting.com",
                        "karen.cruise@ifourtechnology.com",
                        "@marketnewsinsights.com",
                        "@premiummarketinsights.com",
                        "@hitkend.com",
                        "@wondermusic.us",
                        "@sevenzone.us",
                        "@reportsweb.com",
                        "mail.monday.com",
                        "attendeeslist@outlook.com",
                        "delegate@outlook.com",
                        "@conversationaltechsummit.com",
                        "@salesmanago.com",
                        "@salesmanago.io",
                        "@inflexionaiteams.com",
                        "@flariestudio.io",
                        "@attendeesnames.biz",
                        "leads@outlook.com",
                        "@leadcarnivals.biz",
                    ]
                    if any(from_email in msg.from_ for from_email in from_emails):
                        print(f"ℹ️  Deleting email in {user_name} from {msg.from_}")
                        mailbox.delete(msg.uid)
                        count_deleted += 1
                        continue

                    # Delete emails with specific subjects
                    subjects = [
                        "TYZEQ2Y",
                    ]
                    if any(subject in msg.subject for subject in subjects):
                        print(f"ℹ️  Deleting email in {user_name} with subject containing '{msg.subject}'")
                        mailbox.delete(msg.uid)
                        count_deleted += 1
                        continue


                    # Check for bounce indicators in subject or body
                    bounce_indicators = [
                        "Mail Delivery Failed",
                        "Delivery Status Notification",
                        "Undeliverable:",
                        "Failed Delivery",
                        "Delivery Failure",
                        "Non-Delivery Report"
                    ]
                    
                    is_bounce = any(indicator.lower() in msg.subject.lower() for indicator in bounce_indicators) or \
                            "550" in msg.text or "554" in msg.text or \
                            "Mail Delivery System" in msg.from_ or "DAEMON" in msg.from_.upper()

                    if is_bounce:
                        body_text = msg.text or msg.html or ""
                        body_text = body_text.replace('\n', ' ').replace('\r', '')
                        found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', body_text)
                        valid_emails = [
                            email for email in found_emails 
                            if '@' in email 
                            and '.' in email 
                            and not any(email.lower().endswith(f'@{domain}') for domain in IGNORED_DOMAINS)
                        ]
                        bounced_emails.update(valid_emails)

                        # if verbose:
                        #     print(f"Found bounce from: {msg.from_}")
                        #     print(f"Subject: {msg.subject}")
                        #     print(f"Found emails: {valid_emails}")

                        #     print("---")

                        if cleanup: # Delete bounced email notifications
                            print(f"ℹ️  Deleting bounced email notification from {msg.from_} - Subject: {msg.subject}")
                            mailbox.delete(msg.uid)
                            count_deleted += 1

                total_messages_processed += msg_count
                
        except Exception as e:
            print(f"\n❌ Error processing {user_name}: {str(e)}")

    print(f"\nTotal messages processed across {total_accounts} accounts: {total_messages_processed:,}")
    print(f"Count emails deleted: {count_deleted:,}")
    return bounced_emails



# MAIN





if __name__ == '__main__':
    # Only run this if script is run directly (not imported)
    from datetime import datetime
    import time
    
    start_time = time.time()
    bounced = get_bounced_emails()
    
    # print("\nBounced email addresses found:")
    # for email in sorted(bounced):
    #     print(email)

    pp.pprint(bounced)

    print(f"\nTotal unique bounced emails: {len(bounced)}")
    
    run_time = round((time.time() - start_time), 3)
    print(f'\nScript finished in {run_time}s at {datetime.now().strftime("%H:%M:%S")}.\n')
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
count_to_be_deleted = 0


# FUNCTIONS


def get_bounced_emails(verbose=verbose):
    global test, count_to_be_deleted
    """
    Scans IMAP mailboxes for bounced emails and returns a set of unique bounced email addresses.
    Deletes warmup emails.
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
        'kaltura.com',
        'kaltura.cloud',
        'kaltura.email',
        'kalturavideocloud.com',
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
                        if not test:
                            print(f"ℹ️  Deleting warmup email #{msg.uid} from {user_name}")
                            mailbox.delete(msg.uid)
                            count_deleted += 1
                        else:
                            count_to_be_deleted += 1
                            print(f"ℹ️  #{count_to_be_deleted:,} WARMUP EMAIL WOULD BE DELETED: {msg.subject} from {msg.from_}:\n{body_text}\n\n")
                        continue

                    
                    # Delete emails coming from specific emails
                    from_emails = [
                        "Mail Delivery System",
                        # "DAEMON",
                        # "noreply@ionos.de",
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
                        "spitfirestudios.com",
                        "storyblocks.com",
                    ]
                    if any(from_email in msg.from_ for from_email in from_emails):
                        if not test:
                            print(f"ℹ️  Deleting email in {user_name} from {msg.from_}")
                            mailbox.delete(msg.uid)
                            count_deleted += 1
                        else:
                            count_to_be_deleted += 1
                            print(f"ℹ️  #{count_to_be_deleted:,} EMAIL FROM BLACKLIST WOULD BE DELETED: {msg.subject} from {msg.from_}:\n{body_text}\n\n")
                        continue

                    # Delete emails with specific subjects
                    subjects = [
                        "TYZEQ2Y",
                        "Spambericht",
                        "Checking Mailbox Status",
                    ]
                    if any(subject in msg.subject for subject in subjects):
                        if not test:
                            print(f"ℹ️  Deleting email in {user_name} with subject containing '{msg.subject}'")
                            mailbox.delete(msg.uid)
                            count_deleted += 1
                        else:
                            count_to_be_deleted += 1
                            print(f"ℹ️  #{count_to_be_deleted:,} EMAIL FROM BLACKLIST SUBJECT LINES WOULD BE DELETED: {msg.subject} from {msg.from_}:\n{body_text}\n\n")
                        continue


                    # # TODO 250423-0948 Commenting out for now - need stronger logic to only delete bounced emails that are not related to actual contacts AND/OR better logic to handle those.
                    # # Check for bounce indicators in subject or body
                    # bounce_indicators = [
                    #     "Mail Delivery Failed",
                    #     "Delivery Status Notification",
                    #     "Undeliverable:",
                    #     "Failed Delivery",
                    #     "Delivery Failure",
                    #     "Non-Delivery Report"
                    # ]
                    
                    # is_bounce = any(indicator.lower() in msg.subject.lower() for indicator in bounce_indicators) or \
                    #         "550" in msg.text or "554" in msg.text or \
                    #         "Mail Delivery System" in msg.from_ or "DAEMON" in msg.from_.upper()

                    # if is_bounce:

                    #     print(f"\n=== Processing bounced email #{msg.uid} from {user_name} - Subject: {msg.subject}")

                    #     # Extract email from message body for bounced emails
                    #     email_in_body = None
                    #     body_text = msg.text or ''
                    #     # Common patterns for failed delivery notifications
                    #     email_patterns = [
                    #         r'Original-Recipient:.*?rfc822;([^\s<>]+@[^\s<>]+)',
                    #         r'Final-Recipient:.*?rfc822;([^\s<>]+@[^\s<>]+)', 
                    #         r'(?:failed|undeliverable|returned).*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                    #         r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    #     ]
                    #     # Try each pattern until we find a match
                    #     for pattern in email_patterns:
                    #         matches = re.findall(pattern, body_text, re.IGNORECASE)
                    #         if matches:
                    #             potential_email = matches[0].strip().lower()
                    #             if not any(potential_email.endswith(f'@{domain}') for domain in IGNORED_DOMAINS):
                    #                 email_in_body = potential_email
                    #                 print(f"ℹ️  Found bounced email address: {email_in_body}")
                    #                 break


                    #     if email_in_body:
                            
                    #         if 'spam' not in body_text.lower():

                    #             bounced_emails.add(email_in_body)

                    #             # move email address to email_old
                    #             with sqlite3.connect(DB_BTOB) as conn:
                    #                 cur = conn.cursor()
                    #                 cur.execute("""
                    #                     UPDATE people 
                    #                     SET dne = 1,
                    #                         email_old = email,
                    #                         email = NULL,
                    #                         email_status = NULL,
                    #                         updated = ?
                    #                     WHERE email = ?
                    #                 """, (ts_db, email_in_body))
                    #                 conn.commit()
                    #                 if cur.rowcount > 0:
                    #                     print(f"✅ Moved {email_in_body} to email_old and set email_status to NULL.")


                    #     else:
                    #         print(f"ℹ️  Spam-related bounced email:\n{msg.from_=}\n{msg.subject=}\n{body_text}")

                    #     if cleanup: # Delete bounced email notifications
                    #         if not test:
                    #             print(f"ℹ️  Deleting bounced email notification from {msg.from_} - Subject: {msg.subject}")
                    #             mailbox.delete(msg.uid)
                    #             count_deleted += 1
                    #         else:
                    #             print(f"ℹ️  #{count_to_be_deleted:,} WOULD BE DELETED: {msg.subject} from {msg.from_}:\n{body_text}\n\n")

                total_messages_processed += msg_count
                
        except Exception as e:
            print(f"\n❌ Error processing {user_name}: {str(e)}")

    print(f"\nTotal messages processed across {total_accounts} accounts: {total_messages_processed:,}")
    print(f"Count emails to be deleted: {count_to_be_deleted:,}")
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
    print(f'\n--------------------\nScript finished in {run_time}s at {datetime.now().strftime("%H:%M:%S")}.\n')
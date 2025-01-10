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
# DB_MAILINGEE = os.getenv("DB_MAILINGEE")

import pprint
pp = pprint.PrettyPrinter(indent=4)


####################
# IMAPee KAltura: manage outbound emails across multiple accounts
# 2024-12-31 10:26

# IMPORTS

# import my_utils
# from DB.tools import select_all_records, update_record, create_record, delete_record
import sqlite3

from datetime import datetime
from dotenv import load_dotenv
from imap_tools import MailBox, AND
import re

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# First, we extract bounced emails from the IMAP mailboxes and delete specific emails
import DB.blacklist_emails

# GLOBALS

test = 0
verbose = 0
cleanup = 0 # Delete bounced email notifications

count_row = 0
count_total = 0
count = 0
count_deleted = 0


# FUNCTIONS



total_messages_processed = 0

with sqlite3.connect(DB_BTOB) as conn:
    cur = conn.cursor()
    cur.execute("""
        SELECT user_name, password, imap_host, smtp_host
        FROM email_accounts
    """)
    email_accounts = cur.fetchall()
    total_accounts = len(email_accounts)

print(f"\nProcessing {total_accounts} email accounts to manage outbound emails:")

for account_idx, email_account in enumerate(email_accounts, 1):
    user_name, password, imap_host, smtp_host = email_account
    print(f"\n\n\n[{account_idx:,}/{total_accounts:,}] Checking {user_name}...", end='', flush=True)


    with MailBox(imap_host).login(user_name, password) as mailbox:
        messages = list(mailbox.fetch(mark_seen=False, reverse=True, bulk=True))
        msg_count = len(messages)
        print(f" found {msg_count:,} messages")

        for i, msg in enumerate(messages, 1):
            if i % 100 == 0:  # Show progress every 100 messages
                print(f"  Processing: {i}/{msg_count} messages", end='\r', flush=True)
            
            body_text = msg.text or msg.html or ""

            subject = msg.subject

            print(f"\n\n\n\n================= {user_name} #{i}/{msg_count}\n---")
            print(f"Date:\t\t{msg.date_str}")
            print(f"From:\t\t{msg.from_}")
            print(f"To:\t\t{msg.to[0]}")
            print(f"Subject:\t{msg.subject}")
            # print(f"{msg.headers=}")
            # print(f"{msg.attachments=}")
            print(f"\n{msg.text}")
            print(f"\n---")

            user_input = input("\n📝 >>> (del)ete / (f)orward / / (dne) / skip: ")

            if user_input.lower() == 'del': # Delete the email

                mailbox.delete([msg.uid])
                count_deleted += 1
                print(f"\n✅ DELETED {msg.subject} from {msg.from_}")

            elif user_input.lower() == 'f': # Forward the email using SMTP
                print("\nForwarding email...")
                # Get forwarding address from user
                forward_to = "nicolas.deville@kaltura.com"

                # Create message
                forward_msg = MIMEMultipart()
                forward_msg['From'] = user_name
                forward_msg['To'] = forward_to
                forward_msg['Subject'] = f"Fwd: {msg.subject}"

                # Add original message body
                body = f"""
                ---------- Forwarded message ----------
                From: {msg.from_}
                Date: {msg.date_str}
                Subject: {msg.subject}
                To: {msg.to[0]}

                {body_text}
                """
                forward_msg.attach(MIMEText(body, 'plain'))

                # Send the email
                try:
                    with smtplib.SMTP(smtp_host) as smtp:
                        smtp.starttls()
                        smtp.login(user_name, password)
                        smtp.send_message(forward_msg)
                    print(f"✅ Forwarded to {forward_to} with {user_name}")
                    # Delete the email
                    mailbox.delete([msg.uid])
                    count_deleted += 1
                    print(f"\n✅ & DELETED {msg.subject} from {msg.from_}")
                except Exception as e:
                    print(f"❌ Failed to forward: {str(e)}")

            elif user_input.lower() == 'dne': # Do Not Email
                # Extract email from msg.from_
                if user_name != 'thomas.anderson@audience-engage.com':
                    from_email = msg.from_.lower()
                    if from_email:
                        # Update record in people table to set dne=1
                        with sqlite3.connect(DB_BTOB) as conn:
                            cur = conn.cursor()
                            cur.execute("""
                                UPDATE people 
                                SET dne = 1,
                                    updated = ?
                                WHERE email = ?
                            """, (ts_db, from_email))
                            conn.commit()
                            if cur.rowcount > 0:
                                print(f"\n✅ Updated {from_email} with dne=1")
                                # Delete the email
                                mailbox.delete([msg.uid])
                                count_deleted += 1
                                print(f"\n✅ & DELETED {msg.subject} from {msg.from_}")
                            else:
                                print(f"❌ No record found for {from_email}")
                    else:
                        print("\n❌ Could not extract email from From field")
                else:
                    print("\n❌ SKIPPED DNE for thomas.anderson@audience-engage.com")

            else:
                print(f"\n❌ SKIPPED {msg.subject}")
                continue




########################################################################################################

if __name__ == '__main__':
    print('\n\n-------------------------------')
    # print(f"\ncount_row:\t{count_row:,}")
    # print(f"count_total:\t{count_total:,}")
    # print(f"count:\t\t{count:,}")
    run_time = round((time.time() - start_time), 3)
    if run_time < 1:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time*1000)}ms at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 60:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time)}s at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 3600:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/60)}mns at {datetime.now().strftime("%H:%M:%S")}.\n')
    else:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/3600, 2)}hrs at {datetime.now().strftime("%H:%M:%S")}.\n')
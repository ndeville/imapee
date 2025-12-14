import os
import re
from datetime import datetime
from pathlib import Path
import imapclient
import email
from email import policy
from email.utils import parsedate_to_datetime
import html2text
from tqdm import tqdm
from dotenv import load_dotenv
load_dotenv()

# Config

# ### IRENADEVILLE.COM
# IMAP_SERVER = os.getenv("EMAIL_SERVER_ID")
# IMAP_PORT = 993
# USERNAME = os.getenv("EMAIL_ACCOUNT_ID")
# PASSWORD = os.getenv("PASSWORD_ID")
# BACKUP_DIR = Path(os.getenv("BACKUP_DIR_ID"))
# INBOX_FOLDER = 'Archive/2024'

### DEVYER
# IMAP_SERVER = os.getenv("EMAIL_SERVER_NIC_DEVYER")
# IMAP_PORT = 993
# USERNAME = os.getenv("EMAIL_ACCOUNT_NIC_DEVYER")
# PASSWORD = os.getenv("PASSWORD_NIC_DEVYER")
# BACKUP_DIR = Path('/Users/nic/eml/nicolas@devyer-ventures.com')
# INBOX_FOLDER = 'INBOX'


### NICOLASDEVILLE.COM
# USERNAME = os.getenv("EMAIL_ACCOUNT_ND")
# PASSWORD = os.getenv("PASSWORD_ND")



### DEVYER NICOLAS
IMAP_SERVER = os.getenv("IMAP_SERVER_DEVYER")
IMAP_PORT = 993
USERNAME = os.getenv("USERNAME_DEVYER")
PASSWORD = os.getenv("PASSWORD_DEVYER")
BACKUP_DIR = Path(os.getenv("BACKUP_DIR_DEVYER"))
INBOX_FOLDER = 'INBOX'




BATCH_SIZE = 500
html_converter = html2text.HTML2Text()
html_converter.ignore_links = False
html_converter.ignore_images = False

def debug_folders(client):  # FIXED: Safe unpack/decode
    print("=== ALL FOLDERS ===")
    folders = client.list_folders()
    folder_dict = {}
    for ft in sorted(folders, key=lambda x: x[0]):
        folder_name_bytes, flags_bytes_list, sep_bytes = ft  # 3-tuple
        name = folder_name_bytes.decode('utf-8') if isinstance(folder_name_bytes, bytes) else str(folder_name_bytes)
        flags_str = [f.decode('utf-8') if isinstance(f, bytes) else str(f) for f in flags_bytes_list]
        sep = sep_bytes.decode('utf-8') if isinstance(sep_bytes, bytes) else str(sep_bytes)
        print(f"  '{name}' | Flags: {flags_str} | Sep: '{sep}'")
        folder_dict[name] = (flags_str, sep)
    print("====================")
    return folder_dict

def clean_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)[:80]

def load_existing_uids(backup_path):
    existing = set()
    for md_file in backup_path.glob('*.md'):
        uid_match = re.match(r'(\d+)_', md_file.stem)
        if uid_match:
            existing.add(int(uid_match.group(1)))
    print(f"Found {len(existing)} existing emails. Skipping...")
    return existing

def save_uid_list(uids, path):
    path.write_text('\n'.join(map(str, sorted(uids))))

def save_email(email_msg, folder_path, uid, attachments_dir):
    subject = email_msg['Subject'] or 'No Subject'
    # Handle date parsing with error handling for invalid/missing dates
    try:
        date_header = email_msg['Date']
        if date_header:
            date = parsedate_to_datetime(date_header)
        else:
            date = None
    except (ValueError, TypeError, AttributeError):
        date = None
    if date is None:
        date = datetime.now()
    from_ = email_msg['From'] or 'Unknown'
    to_ = email_msg['To'] or 'Unknown'
    
    frontmatter = f"""---
from: {from_}
to: {to_}
subject: {subject}
date: {date.isoformat()}
uid: {uid}
---

"""
    
    # Body → MD (plain > HTML)
    body_md = ''
    
    def extract_text_from_part(part):
        """Recursively extract text from email parts, handling multipart containers."""
        ctype = part.get_content_type()
        
        # Skip multipart containers - they don't have direct content
        if ctype.startswith('multipart/'):
            return None
        
        # Only process text parts
        if not ctype.startswith('text/'):
            return None
        
        try:
            charset = part.get_content_charset() or 'utf-8'
            payload = part.get_payload(decode=True)
            if payload is None:
                return None
            text = payload.decode(charset, errors='ignore')
            return (ctype, text)
        except Exception:
            return None
    
    if email_msg.is_multipart():
        # Prefer plain text, fall back to HTML
        plain_text = None
        html_text = None
        
        for part in email_msg.walk():
            result = extract_text_from_part(part)
            if result:
                ctype, text = result
                if ctype == 'text/plain' and plain_text is None:
                    plain_text = text
                elif ctype == 'text/html' and html_text is None:
                    html_text = text
        
        if plain_text:
            body_md = plain_text
        elif html_text:
            body_md = html_converter.handle(html_text)
    else:
        result = extract_text_from_part(email_msg)
        if result:
            ctype, text = result
            if ctype == 'text/html':
                body_md = html_converter.handle(text)
            else:
                body_md = text
    
    md_content = frontmatter + (body_md or 'No body.')
    
    safe_subject = clean_filename(subject)
    date_prefix = date.strftime('%y%m%d')
    filename = f"{date_prefix}_{safe_subject}.md"
    (folder_path / filename).write_text(md_content, encoding='utf-8')
    
    # Attachments (date-prefixed)
    att_count = 0
    for part in email_msg.walk():
        content_disp = part.get('Content-Disposition', '').lower()
        if 'attachment' in content_disp or part.get_filename():
            att_count += 1
            fname = part.get_filename() or f'att_{att_count:03d}.bin'
            att_path = attachments_dir / f"{date_prefix}_{clean_filename(fname)}"
            with open(att_path, 'wb') as f:
                payload = part.get_payload(decode=True)
                if payload is not None:
                    f.write(payload)

def backup_inbox(client, base_dir, existing_uids):
    print(f"Selecting '{INBOX_FOLDER}'...")
    client.select_folder(INBOX_FOLDER)  # Works!
    
    all_uids = sorted(client.search(['ALL']))
    print(f"Total emails on server: {len(all_uids)}")
    
    missing_uids = [uid for uid in all_uids if uid not in existing_uids]
    print(f"Missing/new: {len(missing_uids)}")
    
    if not missing_uids:
        print("All backed up!")
        return
    
    folder_path = base_dir / 'INBOX'  # English for consistency
    folder_path.mkdir(parents=True, exist_ok=True)
    attachments_dir = folder_path / 'attachments'
    attachments_dir.mkdir(exist_ok=True)
    
    uid_list_path = base_dir / 'all_uids.txt'
    save_uid_list(all_uids, uid_list_path)
    
    with tqdm(total=len(missing_uids), desc="Backing up") as pbar:
        for i in range(0, len(missing_uids), BATCH_SIZE):
            batch_uids = missing_uids[i:i + BATCH_SIZE]
            try:
                messages = client.fetch(batch_uids, ['RFC822'])  # Safe PEEK
                for uid, msg_data in messages.items():
                    email_msg = email.message_from_bytes(msg_data[b'RFC822'], policy=policy.default)
                    save_email(email_msg, folder_path, uid, attachments_dir)
                    pbar.update(1)
                    pbar.set_postfix({'Processed': pbar.n})
            except Exception as e:
                print(f"Batch {i//BATCH_SIZE +1} error: {e}")
    
    print("✅ Backup complete! Server unchanged.")

def main():
    BACKUP_DIR.mkdir(exist_ok=True)
    emails_dir = BACKUP_DIR / 'INBOX'
    existing_uids = load_existing_uids(emails_dir)
    
    with imapclient.IMAPClient(IMAP_SERVER, IMAP_PORT, ssl=True) as client:
        client.login(USERNAME, PASSWORD)
        # folder_dict = debug_folders(client)  # Optional: Uncomment to re-run
        backup_inbox(client, BACKUP_DIR, existing_uids)
        client.logout()
    
    print(f"📁 Final backup: {BACKUP_DIR}")

if __name__ == '__main__':
    main()

import os
from datetime import datetime
import time
from dotenv import load_dotenv
from imap_tools import MailBox, AND
import zipfile
import io
import pprint

def process_dmarc_reports():
    load_dotenv()

    # Hardcoded values
    EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT_ND")
    PASSWORD = os.getenv("PASSWORD_ND")
    EMAIL_SERVER = os.getenv("EMAIL_SERVER_ND")
    DMARC_ADDRESSES = (
        "dmarc@nicolasdeville.com",
        "dmarc_spaceship@nicolasdeville.com",
        "dmarc_ionos@nicolasdeville.com"
    )
    OUTPUT_DIR = "/Users/nic/Python/imapee/dmarc"
    VERBOSE = True

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    count = 0
    count_processed = 0
    count_errors = 0
    count_xml_saved = 0

    start_time = time.time()

    if VERBOSE:
        print(f"Starting DMARC report processing at {datetime.now().strftime('%H:%M:%S')}")

    with MailBox(EMAIL_SERVER).login(EMAIL_ACCOUNT, PASSWORD) as mailbox:
        for dmarc_address in DMARC_ADDRESSES:
            if VERBOSE:
                print(f"\n\nProcessing emails for: {dmarc_address}")
            for msg in mailbox.fetch(AND(to=dmarc_address), mark_seen=False, bulk=True):
                count += 1
                if VERBOSE:
                    print(f"\r    Processing email {count} - From: {msg.from_} - Subject: {msg.subject}", end='')

                try:
                    xml_saved = False
                    for att in msg.attachments:
                        if att.filename.lower().endswith(('.zip', '.gz')):
                            content = io.BytesIO(att.payload)
                            if att.filename.lower().endswith('.zip'):
                                if zipfile.is_zipfile(content):
                                    with zipfile.ZipFile(content) as zf:
                                        for xml_file in zf.namelist():
                                            if xml_file.lower().endswith('.xml'):
                                                xml_content = zf.read(xml_file)
                                                xml_filename = f"dmarc_report_{count}_{xml_file}"
                                                xml_path = os.path.join(OUTPUT_DIR, xml_filename)
                                                with open(xml_path, 'wb') as f:
                                                    f.write(xml_content)
                                                count_xml_saved += 1
                                                xml_saved = True
                            elif att.filename.lower().endswith('.gz'):
                                import gzip
                                try:
                                    with gzip.GzipFile(fileobj=content) as gz:
                                        xml_content = gz.read()
                                        xml_filename = f"dmarc_report_{count}_{att.filename[:-3]}.xml"
                                        xml_path = os.path.join(OUTPUT_DIR, xml_filename)
                                        with open(xml_path, 'wb') as f:
                                            f.write(xml_content)
                                        count_xml_saved += 1
                                        xml_saved = True
                                except gzip.BadGzipFile:
                                    print(f"\nError: {att.filename} is not a valid gzip file.")
                            count_processed += 1
                    if xml_saved:
                        mailbox.delete([msg.uid])
                        if VERBOSE:
                            print(f"\n❌ ✅    Deleted email {msg.uid} after successful XML extraction")
                except Exception as e:
                    if VERBOSE:
                        print(f"\nError processing email: {e}")
                    count_errors += 1
    results = {
        'total_emails': count,
        'zip_files_processed': count_processed,
        'xml_files_saved': count_xml_saved,
        'errors': count_errors,
        'output_directory': OUTPUT_DIR,
        'runtime_minutes': round((time.time() - start_time)/60, 1)
    }

    if VERBOSE:
        pp = pprint.PrettyPrinter(indent=4)
        print("\n")
        print('-------------------------------')
        pp.pprint(results)
        print('-------------------------------')
        print(f"Finished at {datetime.now().strftime('%H:%M:%S')}.")

    return results

if __name__ == "__main__":
    process_dmarc_reports()

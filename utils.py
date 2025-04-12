import email
import email.utils
import mimetypes
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def create_eml(sender, recipient, subject, plain_text, html_text="", attachments=[], output_filename="email.eml", private_key="my_private_key"):
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg["Date"] = email.utils.format_datetime(datetime.datetime.now())
    msg["Message-ID"] = email.utils.make_msgid()

    msg["Authentication-Results"] = "lbp.com; dkim=pass header.i=@lbp.com; spf=pass smtp.mailfrom=lbp.com; dmarc=pass policy.dmarc=lbp.com"

    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText(plain_text, "plain"))
    if html_text != "":
        alt_part.attach(MIMEText(html_text, "html"))
    msg.attach(alt_part)

    for file_path in attachments:
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = "application/octet-stream"

            main_type, sub_type = mime_type.split("/", 1)

            with open(file_path, "rb") as f:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(f.read())
                encoders.encode_base64(part)

            part.add_header("Content-Disposition", f'attachment; filename="{file_path.split("/")[-1]}"')
            msg.attach(part)

        except Exception as e:
            print(f"Error attaching {file_path}: {e}")

    email_bytes = msg.as_bytes()
    # dkim_signature = DKIM(email_string, private_key)
    dkim_signature = 'a'

    msg["DKIM-Signature"] = dkim_signature

    with open(output_filename, "w") as f:
        f.write(msg.as_string())

    return msg.as_string()

import requests
import json

def get_request(url, params, response_field):
    response = requests.get(url, params=params)
    return json.loads(response.text)[response_field]

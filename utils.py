import email
import email.utils
import mimetypes
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def create_eml(sender: str, recipient: str, subject: str, body: str, signer, output_filename="email.eml"):
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg["Date"] = email.utils.format_datetime(datetime.datetime.now())
    msg["Message-ID"] = email.utils.make_msgid()

    sender_hostname, sender_domain = sender.split("@")
    recipient_hostname, recipient_domain = recipient.split("@")

    msg["Authentication-Results"] = f"{sender_domain}; dkim=pass header.i=@{sender_domain}; spf=pass smtp.mailfrom={sender_domain}; dmarc=pass policy.dmarc={sender_domain}"

    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText(body, "plain"))
    msg.attach(alt_part)

    dkim_signature = signer.generate_dkim_signature(msg, body)
    msg["DKIM-Signature"] = dkim_signature

    with open(output_filename, "w") as f:
        f.write(msg.as_string())

    return msg.as_string()

import requests
import json

def get_request(url, params, response_field):
    response = requests.get(url, params=params)
    return json.loads(response.text)[response_field]

def post_request(url, headers, body):
    requests.post(url, headers=headers, json=body)


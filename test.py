# Test Case

from algorithms.rsa_sha256 import *
import email
import email.utils
import mimetypes
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

signer = RSA2048Signer()
signer.generate_keys()

# Create email with FULL headers
email_headers = {
    "From": "test@domain.com",
    "To": "recipient@domain.com", 
    "Subject": "Test",
    "Date": email.utils.format_datetime(datetime.datetime.now()),
    "Message-ID": email.utils.make_msgid()
}
body = "Hello\r\nWorld\r\n"

# Generate signature
dkim_sig = signer.generate_dkim_signature(email_headers, body)

# For verification, we need:
# 1. The original headers EXCLUDING DKIM-Signature
original_headers_str = "\r\n".join(
    [f"{k}: {v}" for k, v in email_headers.items()]
)

# 2. The full email with DKIM-Signature added
full_email = f"{original_headers_str}\r\nDKIM-Signature: {dkim_sig}\r\n\r\n{body}"

# Verify - pass original headers (without DKIM-Sig) and body
verifier = RSA2048Verifier(signer.dkim_record()[1])
assert verifier.verify_dkim_signature(dkim_sig, original_headers_str, body)
"""
Internet Mail Format Implementation (RFC 5322 Compliant)

Key Specifications:
- UTF-8 support
- Lines delimited by CRLF ('\r\n')
- 1000 character line limit (including CRLF)
- Message structure: Header + Body
- Header fields: Name + ':' + value
- Field names: ASCII 33-126 + space(32) + tab(9)
- Date/From/To fields follow sections 3.3/3.4
- Required headers per section 3.6
"""

from utils import *
from p2p import *

# Constants
SMTP_PORT = 2525
MAX_LINE_LENGTH = 1000
RESPONSE_SUCCESS_CODES = {
    'CONNECTION': b'220',
    'COMMAND': b'250',
    'DATA': b'354'
}

def send_email(data: Dict[str, str]) -> bytes:
    """Send email via SMTP protocol"""
    
    sender_email = data["from"]
    recipient_email = data["to"]

    sender_hostname, sender_domain = sender_email.split("@")
    recipient_hostname, recipient_domain = recipient_email.split("@")

    recipient_ip = peer.get_ip(recipient_hostname)

    if ip_address(recipient_ip) is None:
        raise Exception(f"Hostname {recipient_hostname} not found")
    
    email_message = create_eml(
        sender_email,
        recipient_email,
        data["subject"],
        data["body"]
    )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((recipient_ip, SMTP_PORT))
        
        # SMTP Protocol Handshake
        commands = [
            (f"HELO {sender_domain}", 'CONNECTION'),
            (f"MAIL FROM:<{sender_email}>", 'COMMAND'),
            (f"RCPT TO:<{recipient_email}>", 'COMMAND'),
            ("DATA", 'DATA')
        ]
        
        for cmd, expected in commands:
            s.recv(1024)
            s.send(cmd.encode())

        print(s.recv(1024))
        s.send(email_message.encode())
        s.send(b"\r\n.")
        return s.recv(1024)

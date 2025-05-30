from email import *
from pymongo import MongoClient
from utils import *
from p2p import *

from algorithms.rsa_sha256 import *
from algorithms.ed25519_sha256 import *
from algorithms.ecdsa_sha256 import *
from algorithms.dilithium import *

import threading
import socket
import signal
import re
import os
import time

# Configuration
MAILDIR = "~/Maildir"
HOSTNAME = socket.gethostname()
SMTP_PORT = 2525
DOMAIN = f"{HOSTNAME}.com"

class SMTPServer:
    def __init__(self):
        self.running = False
        self.server_socket = None
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def start(self):
        """Start the SMTP server in a separate thread"""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', SMTP_PORT))
        self.server_socket.listen(5)
        
        print(f"SMTP Server running on port {SMTP_PORT}")
        threading.Thread(target=self.accept_connections, daemon=True).start()

    def accept_connections(self):
        """Accept incoming SMTP connections"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, addr),
                    daemon=True
                ).start()
            except OSError:
                break

    def handle_client(self, client_socket, client_address):
        """Handle SMTP client session"""
        try:
            state = {
                "HELO": False,
                "MAIL": False,
                "RCPT": False,
                "DATA": False,
                "client_hostname": "",
                "client_domain": ""
            }

            def reset_state():
                nonlocal state
                state = {
                    "HELO": False,
                    "MAIL": False,
                    "RCPT": False,
                    "DATA": False,
                    "client_hostname": "",
                    "client_domain": ""
                }

            client_socket.send(f"220 SMTP {HOSTNAME} 1.0\n".encode())

            while True:
                message = client_socket.recv(1024).strip().decode().split()
                
                if not message:
                    continue

                command = message[0].upper()

                # HELO Command
                if command == "HELO":

                    if len(message) != 2:
                        client_socket.send(b"501 Syntax: HELO hostname \n")
                    else:
                        if state["HELO"]:
                            reset_state()

                        state["HELO"] = True
                        state["client_domain"] = message[1]
                        client_socket.send(f"250 {DOMAIN} OK \n".encode())

                # MAIL FROM Command
                elif command == "MAIL" and len(message) > 1 and message[1].startswith("FROM:<"):

                    if not state["HELO"]:
                        client_socket.send(b"503 5.5.1 Error: send HELO first \n")
                    elif state["MAIL"]:
                        client_socket.send(b"503 5.5.1 Error: nested MAIL command \n")
                    elif len(message) != 2:
                        client_socket.send(b"501 5.5.4 Syntax: MAIL FROM:<address> \n")
                    else:
                        if not re.match(r"FROM:<[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+>$", message[1], re.IGNORECASE):
                            client_socket.send(b"501 5.1.7 Bad sender address syntax \n")
                        else:
                            state["MAIL"] = True
                            client_hostname, client_domain = message[1][len("FROM:<"):-len(">")].split("@")
                            state["client_hostname"] = client_hostname
                            state["client_domain"] = client_domain
                            client_socket.send(b"250 2.1.0 OK \n")

                # RCPT TO Command
                elif command == "RCPT" and len(message) > 1 and message[1].startswith("TO:<"):

                    if not state["MAIL"]:
                        client_socket.send(b"503 5.1.1 Bad sequence of commands \n")
                    elif len(message) != 2:
                        client_socket.send(b"501 5.5.4 Syntax: RCPT TO:<address> \n")
                    else:
                        if not re.match(r"TO:<[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+>$", message[1], re.IGNORECASE):
                            client_socket.send(b"501 5.1.7 Bad recipient address syntax \n")
                        else:
                            recipient_hostname, recipient_domain = message[1][len("TO:<"):-len(">")].split("@")
                            
                            if recipient_hostname != HOSTNAME:
                                client_socket.send(b"550 5.1.1 Mailbox unavailable \n")
                            elif recipient_hostname == HOSTNAME and recipient_domain != DOMAIN:
                                print("handle what if wrong recipient domain")  ###
                            else:
                                state["RCPT"] = True
                                client_socket.send(b"250 2.1.0 OK \n")

                # DATA Command
                elif command == "DATA":

                    if not (state["HELO"] and state["MAIL"] and state["RCPT"]):
                        print("handle errors for data")
                        continue

                    client_socket.send(b"354 End data with <CR><LF>.<CR><LF> \n")
                    
                    if not os.path.isdir(MAILDIR):
                        os.makedirs(MAILDIR)

                    mail_dir = os.path.expanduser(f"{MAILDIR}/{recipient_domain}")
                    
                    if not os.path.isdir(mail_dir):
                        os.makedirs(mail_dir)
                    
                    mail_sender = f"{mail_dir}/{state['client_hostname']}"

                    if not os.path.isdir(mail_sender):
                        os.makedirs(mail_sender)

                    counter = 1
                    while os.path.isfile(f"{mail_sender}/{counter}.txt"):
                        counter += 1

                    eml = ""
                    
                    with open(f"{mail_sender}/{counter}.txt", "w") as open_file:

                        while True:
                            data_message = client_socket.recv(1024)
                            print(data_message, len(data_message))

                            if b"\r\n.\r\n" not in data_message:
                                eml += data_message.decode()
                                open_file.write(data_message.decode())
                            else:
                                decoded_data = data_message.split(b"\r\n.\r\n")[0].decode()
                                eml += decoded_data
                                open_file.write(decoded_data)
                                client_socket.send(b"250 OK: Message accepted \n")
                                break

                    parsed_eml = self.parse_eml(eml)
                    self.verify_email_integrity(parsed_eml)
                    
                # QUIT Command
                elif command == "QUIT":
                    client_socket.send(b"221 2.0.0 Bye \n")
                    client_socket.close()
                    return
                
                # Unknown Command
                else:
                    client_socket.send(b"500 5.5.2 Syntax error, command unrecognized \n")
            
        except Exception as e:
            print(f"SMTP Error: {e}")
            
        finally:
            client_socket.close()

    def verify_email_integrity(self, parsed_eml):
        params = {
            "domain": f'default._domainkey.{parsed_eml["sender"].split("@")[1]}',
            "type": "TXT"
        }

        dns_ip = peer.get_ip("dns")
        dns_port = 5353
        dns_retrieve_url = f"http://{dns_ip}:{dns_port}/retrieve"

        dkim_public_key = get_request(dns_retrieve_url, params, "message")

        strargv: List[str] = [str(x) for x in sys.argv]

        if "-a" in strargv or "--algorithm" in strargv:
            position = 1 + (strargv.index("-a") if strargv.index("-a") != -1 else strargv.index("--algorithm"))
            if len(strargv) <= position:
                raise Exception("Incorrect use of the flag \"-a\" or \"--algorithm\". Please specify the signature algorithm following the flag \"-a\".")
            
            algorithm: str = strargv[position]

            if "rsa" in algorithm.lower():
                verifier = RSA2048Verifier(dkim_public_key)

            elif "ed25519" in algorithm.lower():
                verifier = ED25519Verifier(dkim_public_key)

            elif "ecdsa" in algorithm.lower():
                verifier = ECDSAVerifier(dkim_public_key)

            elif "dilithium" in algorithm.lower():
                if algorithm.lower() == "dilithium-44":
                    verifier = DilithiumVerifier("44", dkim_public_key)
                elif algorithm.lower() == "dilithium-65":
                    verifier = DilithiumVerifier("65", dkim_public_key)
                elif algorithm.lower() == "dilithium-87":
                    verifier = DilithiumVerifier("87", dkim_public_key)
                
        dkim_signature = parsed_eml["dkim-signature"]
        email_headers = {
            "From": parsed_eml["sender"],
            "To": parsed_eml["recipient"],
            "Subject": parsed_eml["subject"],
            "Date": parsed_eml["date"]
        }

        headers_to_sign = ["From", "To", "Subject", "Date"]
        header_string = "\r\n".join(
            f"{h}: {email_headers[h]}" for h in headers_to_sign if h in email_headers
        )

        if verifier.verify_dkim_signature(dkim_signature, header_string, parsed_eml["body"]):
            email_entry = {
                "type": "Inbox",
                "from": parsed_eml["sender"],
                "to": parsed_eml["recipient"],
                "subject": parsed_eml["subject"],
                "body": parsed_eml["body"],
                "time": str(time.time()),
                "read": False,
                "starred": False
            }

            inserted_id = self.insert_email(email_entry)
            print(f"Inserted email with ID: {inserted_id}")

    def get_db_connection(self, DB_NAME):
        MONGO_URI = "mongodb://localhost:27017/"
        
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        return db

    def insert_email(self, email_data):
        db = self.get_db_connection("emails")
        emails_collection = db["emails"]

        result = emails_collection.insert_one(email_data)
        return result.inserted_id

    def parse_eml(self, eml_string):
        """Parse an EML string back into its components"""
        msg = message_from_string(eml_string)
        
        result = {
            "headers": dict(msg.items()),
            "sender": msg["From"],
            "recipient": msg["To"],
            "subject": msg["Subject"],
            "date": msg["Date"],
            "message_id": msg["Message-ID"],
            "dkim-signature": msg["DKIM-Signature"],
            "plain_text": ""
        }

        # Process each part of the message
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Plain text
            if content_type == "text/plain" and "attachment" not in content_disposition:
                result["body"] = part.get_payload(decode=True).decode()

        return result

    def shutdown(self, signum=None, frame=None):
        """Graceful shutdown"""
        print("\nShutting down SMTP server...")
        self.running = False
        if self.server_socket:
            self.server_socket.close()

smtp_server = SMTPServer()
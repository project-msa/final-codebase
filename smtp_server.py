import threading
import socket
import signal
import re
import os
import time
from email import *
from pymongo import MongoClient
from p2p import *

# Configuration
MAILDIR = "~/Maildir"
HOSTNAME = socket.gethostname()
SERVER_IP = peer.get_ip(HOSTNAME)
SMTP_PORT = 2525
DOMAIN = "lbp.com"

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

            # Send SMTP greeting
            client_socket.send(b"220 SMTP kh4rg0sh 1.0\n")

            while True:
                message = client_socket.recv(1024).strip().decode().split()
                
                if not message:
                    continue

                command = message[0].upper()

                # HELO Command
                if command == "HELO":
                    print("test HELO")  ###

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
                    print("test MAIL FROM")  ###

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
                    print("test RCPT TO")  ###

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
                    print("test DATA")  ###

                    if not (state["HELO"] and state["MAIL"] and state["RCPT"]):
                        print("handle errors for data")
                        continue

                    client_socket.send(b"354 End data with <CR><LF>.<CR><LF> \n")
                    
                    print(MAILDIR)  ###
                    if not os.path.isdir(MAILDIR):
                        print("create maildir")  ###
                        os.makedirs(MAILDIR)

                    mail_dir = os.path.expanduser(f"{MAILDIR}/{recipient_domain}")
                    print(mail_dir)  ###
                    
                    if not os.path.isdir(mail_dir):
                        print("created mail_dir")  ###
                        os.makedirs(mail_dir)
                    
                    mail_sender = f"{mail_dir}/{state['client_hostname']}"
                    print(mail_sender)  ###

                    if not os.path.isdir(mail_sender):
                        print("created mail_sender")  ###
                        os.makedirs(mail_sender)

                    counter = 1
                    while os.path.isfile(f"{mail_sender}/{counter}.txt"):
                        counter += 1

                    eml = ""
                    
                    with open(f"{mail_sender}/{counter}.txt", "w") as open_file:
                        print(f"{mail_sender}/{counter}.txt")  ###

                        while True:
                            data_message = client_socket.recv(1024).strip().decode()
                            print(data_message)
                            
                            if data_message != ".":
                                eml += data_message
                                open_file.write(data_message)
                            else:
                                client_socket.send(b"250 OK: Message accepted \n")
                                break
                    
                    parsed_eml = self.parse_eml(eml)
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
            "plain_text": "",
            "html_text": "",
            "attachments": []
        }

        # Process each part of the message
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Plain text
            if content_type == "text/plain" and "attachment" not in content_disposition:
                result["body"] = part.get_payload(decode=True).decode()

            # HTML text
            elif content_type == "text/html" and "attachment" not in content_disposition:
                result["html_text"] = part.get_payload(decode=True).decode()

            # Attachments
            elif "attachment" in content_disposition:
                attachment = {
                    "content_type": content_type,
                    "filename": part.get_filename(),
                    "payload": part.get_payload(decode=True),
                    "size": len(part.get_payload(decode=True))
                }
                result["attachments"].append(attachment)

        return result

    def shutdown(self, signum=None, frame=None):
        """Graceful shutdown"""
        print("\nShutting down SMTP server...")
        self.running = False
        if self.server_socket:
            self.server_socket.close()

smtp_server = SMTPServer()
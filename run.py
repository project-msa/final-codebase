from utils import *
from smtp_server import *
from smtp_client import *

from waitress import serve
from flask import Flask, request, jsonify
from typing import Dict, Tuple

import subprocess
import sys
import signal

FRONTEND_PORT = 3000
EXPRESS_PORT = 3001
FLASK_PORT = 3002
SMTP_PORT = 2525
P2P_PORT = 5555

MAX_LINE_LENGTH = 1000
RESPONSE_SUCCESS_CODES = {
    'CONNECTION': b'220',
    'COMMAND': b'250',
    'DATA': b'354'
}

HOSTNAME = socket.gethostname()
SERVER_IP = peer.get_ip(HOSTNAME)

while SERVER_IP is None:
    SERVER_IP = peer.get_ip(HOSTNAME)

class ServiceManager:
    def __init__(self):
        self.should_exit = threading.Event()
        self.processes = []
        self.threads = []
        
        # Configuration
        self.SERVER_IP = self._get_server_ip()
        self.PORTS = {
            'frontend': 3000,
            'express': 3001,
            'flask': 3002,
            'smtp': 2525,
            'p2p': 5555
        }

    def _get_server_ip(self):
        """Wait until P2P network provides our IP"""
        while not peer.peers.get(socket.gethostname()):
            time.sleep(1)
        return peer.get_ip(socket.gethostname())

    def start_frontend(self):
        env = {
            **os.environ,
            'SERVER_IP': self.SERVER_IP,
            'EXPRESS_URL': f'http://{self.SERVER_IP}:{self.PORTS["express"]}/',
            'EXPRESS_PORT': str(self.PORTS["express"]),
            'FROM': HOSTNAME
        }
        proc = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd='client',
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        self.processes.append(proc)

    def start_backend(self):
        env = {
            **os.environ,
            'PYTHON_API_URL': f'http://{self.SERVER_IP}:{self.PORTS["flask"]}/',
            'FRONTEND_PORT': str(self.PORTS["frontend"]),
            'EXPRESS_PORT': str(self.PORTS["express"]),
            'FLASK_PORT': str(self.PORTS["flask"]),
            'SERVER_IP': self.SERVER_IP
        }
        proc = subprocess.Popen(
            ['npm', 'start'],
            cwd='server',
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        self.processes.append(proc)

    def start_flask(self):
        app = Flask(__name__)
        
        @app.route("/health")
        def health():
            return jsonify({"status": "ok"})
        
        @app.route("/send", methods=["POST"])
        def send() -> Tuple[Dict, int]:
            """Email sending endpoint"""
            data = request.json
            required_fields = {'from', 'to', 'subject', 'body'}
            
            if not required_fields.issubset(data.keys()):
                return jsonify({"error": "Missing required fields"}), 400

            try:
                response = send_email(data)
                return jsonify({
                    "message": "Email sent successfully",
                    "response": response.decode()
                }), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/peers", methods=["GET"])
        def get_peers():
            """Endpoint to list known P2P peers"""
            peers = [
                {"id": p.id, "ip": p.ip, "port": p.port}
                for p in peer.peers.values()
            ]
            return jsonify({"peers": peers})

        @app.route("/current_ip", methods=["GET"])
        def get_current():
            return jsonify({"hostname": HOSTNAME, "server_ip": SERVER_IP})
            
        thread = threading.Thread(
            target=lambda: serve(app, host='0.0.0.0', port=self.PORTS["flask"]),
            daemon=True
        )

        thread.start()
        self.threads.append(thread)

    def run(self):
        # Start services
        print("hi")
        self.start_frontend()
        print("hi")
        self.start_backend()
        self.start_flask()
        smtp_server.start()
        
        # Handle shutdown
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
        # Keep alive
        while not self.should_exit.is_set():
            time.sleep(1)

    def shutdown(self, signum, frame):
        print("\nInitiating shutdown...")
        self.should_exit.set()
        
        # Stop SMTP server
        smtp_server.shutdown()
        
        # Terminate subprocesses
        for proc in self.processes:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        
        # Exit forcefully if needed
        os._exit(0)

if __name__ == '__main__':
    print("hi")
    manager = ServiceManager()
    manager.run()

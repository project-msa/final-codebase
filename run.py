from utils import *
from smtp_client import *
from pathlib import Path

import subprocess
import platform
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

if SERVER_IP is None:
    raise Exception("Unable to initiate a network connection")

class ServiceManager:
    def __init__(self, SERVER_IP):
        self.should_exit = threading.Event()
        self.processes = []
        self.threads = []

        self.SERVER_IP = SERVER_IP
        self.PORTS = {
            'frontend': 3000,
            'express': 3001,
            'flask': 3002,
            'smtp': 2525,
            'p2p': 5555
        }

        self.os_type = platform.system().lower()
        self.project_root = Path(__file__).parent.resolve()
        self.install_dependencies()
        
    def install_dependencies(self):
        """Run the appropriate dependency installer for the OS"""
        try:
            if self.os_type == 'windows':
                self._run_windows_installer()
            else:
                self._run_unix_installer()
            
            print("\n✓ All dependencies installed successfully")
            return True
        except Exception as e:
            print(f"\n✗ Dependency installation failed: {str(e)}")
            return False

    def _run_windows_installer(self):
        """Execute the Windows batch installer"""
        bat_path = self.project_root / 'dependencies.bat'
        subprocess.run(
            [str(bat_path)],
            cwd=self.project_root,
            shell=True,
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr
        )

    def _run_unix_installer(self):
        """Execute the Unix shell script installer"""
        sh_path = self.project_root / 'dependencies.sh'
        
        if not os.access(sh_path, os.X_OK):
            os.chmod(sh_path, 0o755)
            
        subprocess.run(
            [str(sh_path)],
            cwd=self.project_root,
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr
        )

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
        from flask import Flask, request, jsonify
        from waitress import serve

        app = Flask(__name__)
        
        @app.route("/send", methods=["POST"])
        def send() -> Tuple[Dict, int]:
            """Email sending endpoint"""
            data = request.json
            required_fields = {'from', 'to', 'subject', 'body'}
            
            if not required_fields.issubset(data.keys()):
                return jsonify({"error": "Missing required fields"}), 400

            try:
                response = send_email(data)
                print(response)
                return jsonify({
                    "message": "Email sent successfully",
                    "response": response.decode()
                }), 200
            except Exception as e:
                print(e)
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
        self.start_frontend()
        self.start_backend()
        self.start_flask()

        from smtp_server import smtp_server
        smtp_server.start()
        
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
        while not self.should_exit.is_set():
            time.sleep(1)

    def shutdown(self, signum, frame):
        print("\nInitiating shutdown...")
        self.should_exit.set()
        
        from smtp_server import smtp_server
        smtp_server.shutdown()
        
        for proc in self.processes:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        
        os._exit(0)

if __name__ == '__main__':
    manager = ServiceManager(SERVER_IP)
    manager.run()

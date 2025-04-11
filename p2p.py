from dataclasses import dataclass
from ipaddress import ip_address
from typing import Dict, List, Tuple

import threading
import socket
import time 
import sys
import os

@dataclass
class Peer():
    id: str
    ip: str
    port: int
    timestamp: int

class P2PNode:
    def __init__(self, broadcast_ip, port=5555):
        if port < 1024 and not os.geteuid() == 0:
            raise PermissionError("Ports below 1024 require root privileges")
        
        self.id = socket.gethostname()
        self.broadcast_ip = broadcast_ip
        self.port = port
        self.peers: Dict[str, Peer] = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('0.0.0.0', port))

        self.discovery_lapse = 10
        self.inactivity_lapse = 10
        self.inactivity_threshold = 30

        """
        once the peer is initialised:
            1. it sends a broadcast packet and listens for acknowledgement
            2. add all those peers to list of active peers that give it the acknowledgement
            3. send an acknowledgement back to those who it received acknowledgement from
            4. ping and check the activity of peers
        """

        threading.Thread(target=self.discover_peers, daemon=True).start()
        threading.Thread(target=self.listen, daemon=True).start()
        threading.Thread(target=self.maintain_peers, daemon=True).start()
    
    def listen(self):
        """
        if you received:
            1. JOIN: -> somebody wants to join you
            format: JOIN|(my_port)|(my_id)

            2. PING: -> somebody is asking if you are alive reply to them with a PONG
            format: PING|(my_port)|(my_id)
            
            3. PONG: -> somebody has replied to your ping, so update their timestamp
            format: PONG|(my_port)|(my_id)
            
            4. PEER_LIST -> you have received someone's peer list, merge theirs with yours
            format: PEER_LIST|(peer_list: (peer_id, peer_ip, peer_port))
        """
        while True:
            data, addr = self.socket.recvfrom(1024)
            
            try:
                msg = data.decode().split('|')

                if msg[0] == 'JOIN':
                    self.handle_join(addr[0], int(msg[1]), msg[2])

                elif msg[0] == 'PING':
                    self.reply_ping(addr[0], int(msg[1]), msg[2])

                elif msg[0] == 'PONG':
                    self.timestamp(addr[0], int(msg[1]), msg[2])

                elif msg[0] == 'PEER_LIST':
                    self.update_peers(msg[1:])

            except:
                pass
    
    def discover_peers(self):
        """Periodic peer discovery"""
        while True:
            self.socket.sendto(f"JOIN|{self.port}|{self.id}".encode(), (self.broadcast_ip, self.port))
            time.sleep(self.discovery_lapse)

    def handle_join(self, ip: str, port: int, peer_id: str):
        """Process new peer"""
        self.send_peer_list(ip, port)
        self.add_peer(peer_id, ip, port)
    
    def add_peer(self, peer_id: str, ip: str, port: int):
        """Add the new peer to our peer list"""
        if peer_id not in self.peers:
            self.peers[peer_id] = Peer(peer_id, ip, port, int(time.time()))
            print(f"Added new peer {peer_id} at {ip}:{port}")
        
    def send_peer_list(self, ip: str, port: int):
        """Send our known peers to requester"""
        peer_list = '|'.join([f"{p.id}:{p.ip}:{p.port}" for p in self.peers.values()])
        msg = f"PEER_LIST|{peer_list}"
        self.socket.sendto(msg.encode(), (ip, port))
    
    def update_peers(self, peers: List[str]):
        """Update the list of peers from requester"""
        for peer in peers:
            try:
                id, ip, port = peer.split(':')
                self.add_peer(id, ip, int(port))

            except:
                pass
            
    def maintain_peers(self):
        """Check if the peers are active"""
        while True:
            dead_peers = set()
            for peer_id, peer in list(self.peers.items()):
                if int(time.time()) - peer.timestamp > self.inactivity_threshold:
                    dead_peers.add(peer_id)
                else:
                    self.ping_peer(peer.ip, peer.port)
            
            for peer_id in dead_peers:
                self.peers.pop(peer_id, None)
                print(f"Removed dead peer {peer_id}")
            
            time.sleep(self.inactivity_lapse)

    def ping_peer(self, ip: str, port: int):
        """Ping the peer"""
        try:
            self.socket.sendto(f"PING|{self.port}|{self.id}".encode(), (ip, port))

        except:
            pass

    def reply_ping(self, ip: str, port: int, peer_id: str):
        """Reply to ping"""
        self.socket.sendto(f"PONG|{self.port}|{self.id}".encode(), (ip, port))

    def timestamp(self, ip: str, port: int, peer_id: str):
        """Update timestamp"""
        if peer_id not in self.peers.keys():
            # new peer add it to the list
            self.add_peer(peer_id, ip, int(port))

        else:
            # just update the timestamp
            self.peers[peer_id].timestamp = int(time.time())

    def get_ip(self, hostname):
        for peer_id, peer in self.peers.items():
            if peer_id == hostname:
                return peer.ip

    def list_peers(self):
        print(f"\nActive Peers: ")
        for peer in self.peers.values():
            print(f"{peer.id} {peer.ip} {peer.port} {peer.timestamp}")
        print()

ip_address(sys.argv[1])
peer = P2PNode(sys.argv[1])

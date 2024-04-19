from typing import Any
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor, defer
import json
import copy
import ecdsa
from hashlib import sha256

from blockchain import Block, Blockchain
import datetime as date

class Server(DatagramProtocol):
    def __init__(self):
        self.clients = {}   # Dictionary to keep list of clients
        self.private_key = ecdsa.SigningKey.generate()  # Generate private key
        self.pem_private_key = self.private_key.to_pem()

        self.leader = None

        self.node_list = ['UNHMSDS01', 'UNHMSDS02', 'UNHMSDS03', 'UNHMSDS04', 'UNHMSDS05', 'UNHMSDS06', 'UNHMSDS07', 'UNHMSDS08']

        try:
            # Open the file in read mode
            with open("list_of_clients.json", "r") as f:
                # Read the dictionary from the file
                for key, value in json.load(f).items():
                    self.clients[key]=tuple(value)
        except FileNotFoundError:
            print('File not found')

        self.temp_exist = {}  # Dictionary to handle existing host
        self.temp_coming = {}   # Dictionary to handle on coming host
        self.pending_pings = {}  # Dictionary to keep track of pending pings

        # Initialize blockchain
        self.blockchain = Blockchain()
        self.temp_block = None
        
        print("Server started......")
    
    def datagramReceived(self, datagram, addr):
        datagram = datagram.decode('utf-8')
        try:
            data=json.loads(datagram)
            if data['type']=='ID' and data['id'] in self.node_list:
                if data['id'] in self.clients:
                    self.temp_coming[data['id']] = addr
                    self.temp_exist[data['id']] = self.clients[data['id']]
                    self.ping_client(self.clients[data['id']])
                else:
                    self.clients[data['id']] = addr

                    with open("list_of_clients.json", "w") as f:
                        # Write the dictionary to the file
                        json.dump(self.clients, f)
                    
                    print('List of clients:')
                    for user_id, info in self.clients.items():
                        print(f"User ID: {user_id}, Address: {info}")
                    
                    addresses=copy.copy(self.clients)
                    addresses['type']='list'
                    addresses["private_key"] = self.pem_private_key.decode()
                    add_json = json.dumps(addresses)
                    for value in self.clients.values():
                        self.transport.write(add_json.encode('utf-8'), value)
            
            elif data['type'] == 'pong':
                self.handle_pong(addr)
            
            elif data['type']=='leader':
                self.leader = data['nodeid']
            
            elif data['type']=='block':
                del data['type']
                new_block = Block.from_dict(data)
                self.blockchain.add_block(new_block)

                print("block added ....\n")
                print("Block #" + str(new_block.index))
                print("Timestamp: " + str(new_block.timestamp))
                print("Data: " + str(new_block.data))
                print("Hash: " + new_block.hash)
                print("Previous Hash: " + new_block.previous_hash)
                print("\n")
        
        except json.JSONDecodeError:
            print("Invalid JSON received:", datagram)
        
    def ping_client(self, ip):
        dic = {'type':'ping','message':'pingpong'}
        dic_json=json.dumps(dic)
        self.transport.write(dic_json.encode('utf-8'), ip)
        # Schedule a timeout to check for "pong" response
        d = defer.Deferred()
        d.addCallback(self.handle_pong)
        d.addErrback(self.handle_timeout, ip)  # Add errback for timeout
        print("defer: ",d, "type :", type(d))
        self.pending_pings[ip] = d
        print(self.pending_pings)
        reactor.callLater(2, self.handle_timeout, TimeoutError("Timeout occurred"), ip)

    def handle_pong(self, ip):
        if ip in self.pending_pings:
            print("Received pong from:", ip)
            # Cancel the timeout if pong is received before timeout
            if not self.pending_pings[ip].called:
                self.pending_pings[ip].callback(None)
                del self.pending_pings[ip]  # Remove the deferred for this client
                dic = {'type':'invalidhost','message':'enter a new name'}
                dic_json=json.dumps(dic)
                for value in self.temp_coming.values():
                    self.transport.write(dic_json.encode('utf-8'), value)
                self.temp_coming.clear()
                self.temp_exist.clear()
                # self.ip=None

    def handle_timeout(self, failure, ip):
        # ip=self.ip
        if ip in self.pending_pings:
            if not self.pending_pings[ip].called:
                self.pending_pings[ip].errback(failure)
                del self.pending_pings[ip]  # Remove the deferred for this client
                for key, value in self.temp_coming.items():
                    self.clients[key]=value

                with open("list_of_clients.json", "w") as f:
                        # Write the dictionary to the file
                        json.dump(self.clients, f)

                self.temp_coming.clear()
                self.temp_exist.clear()

                for user_id, info in self.clients.items():
                    print(f"User ID: {user_id}, Address: {info}")
                addresses=copy.copy(self.clients)
                addresses['type']='list'
                addresses["private_key"] = self.pem_private_key.decode()
                add_json = json.dumps(addresses)
                for value in self.clients.values():
                    self.transport.write(add_json.encode('utf-8'), value)


if __name__ == '__main__':
    reactor.listenUDP(9999, Server())
    reactor.run()
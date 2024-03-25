from typing import Any
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor, defer
import json
import copy

class Server(DatagramProtocol):
    def __init__(self):
        self.clients = {}   # Dictionary to keep list of clients
        self.temp_exist = {}  # Dictionary to handle existing host
        self.temp_coming = {}   # Dictionary to handle on coming host
        self.pending_pings = {}  # Dictionary to keep track of pending pings
    
    def datagramReceived(self, datagram, addr):
        datagram = datagram.decode('utf-8')
        try:
            data=json.loads(datagram)
            if data['type']=='ID':
                if data['id'] in self.clients:
                    self.temp_coming[data['id']] = addr
                    self.temp_exist[data['id']] = self.clients[data['id']]
                    self.ping_client(self.clients[data['id']])
                else:
                    self.clients[data['id']] = addr
                    print('List of clients:')
                    for user_id, info in self.clients.items():
                        print(f"User ID: {user_id}, Address: {info}")
                    
                    addresses=copy.copy(self.clients)
                    addresses['type']='list'
                    add_json = json.dumps(addresses)
                    for value in self.clients.values():
                        self.transport.write(add_json.encode('utf-8'), value)
            
            elif data['type'] == 'pong':
                self.handle_pong(addr)
        
        except json.JSONDecodeError:
            print("Invalid JSON received:", datagram)
        
    def ping_client(self, ip):
        dic = {'type':'ping','message':'pingpong'}
        dic_json=json.dumps(dic)
        self.transport.write(dic_json.encode('utf-8'), ip)
        print("Pinging client:", ip)
        # Schedule a timeout to check for "pong" response
        d = defer.Deferred()
        d.addCallback(self.handle_pong)
        d.addErrback(self.handle_timeout, ip)  # Add errback for timeout
        self.pending_pings[ip] = d
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

    def handle_timeout(self, failure, ip):
        if ip in self.pending_pings:
            if not self.pending_pings[ip].called:
                print("Timeout occurred:", failure)
                self.pending_pings[ip].errback(failure)
                del self.pending_pings[ip]  # Remove the deferred for this client
                for key, value in self.temp_coming.items():
                    self.clients[key]=value
                self.temp_coming.clear()
                self.temp_exist.clear()
                print('List of clients:')
                for user_id, info in self.clients.items():
                    print(f"User ID: {user_id}, Address: {info}")
                addresses=copy.copy(self.clients)
                addresses['type']='list'
                add_json = json.dumps(addresses)
                for value in self.clients.values():
                    self.transport.write(add_json.encode('utf-8'), value)


if __name__ == '__main__':
    reactor.listenUDP(9999, Server())
    reactor.run()
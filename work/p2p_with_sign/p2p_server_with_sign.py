from typing import Any
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import ecdsa
from hashlib import sha256
import json

class Server(DatagramProtocol):
    def __init__(self):
        self.clients = set()
        self.private_key = ecdsa.SigningKey.generate()  # Generate private key
        self.pem_private_key = self.private_key.to_pem()
    
    def datagramReceived(self, datagram, addr):
        datagram = datagram.decode('utf-8')
        if datagram == "ready":
            addresses = "\n".join([str(x) for x in self.clients])
            # Convert addresses to JSON with "type": "clients"
            addre = { "type": "clients", "address": addresses }
            addresses_json = json.dumps(addre)
            self.transport.write(addresses_json.encode(), addr)
            # add clients to the clients set
            self.clients.add(addr)
            # print(self.clients)
        if datagram == "keys":
            key_data = {
            "type": "keys",
            "private_key": self.pem_private_key.decode()
            }
            key_json = json.dumps(key_data)
            self.transport.write(key_json.encode(), addr)
            print("Key pair sent:", key_data)
            

if __name__ == '__main__':
    reactor.listenUDP(9999, Server())
    reactor.run()
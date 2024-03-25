from typing import Any
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import json
import copy

class Server(DatagramProtocol):
    def __init__(self):
        self.clients = {}
    
    def datagramReceived(self, datagram, addr):
        # datagram = datagram.decode('utf-8')
        data=json.loads(datagram)
        if data['type']=='ID':
            if data['id'] in self.clients:
                self.clients[data['id']] = addr
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


if __name__ == '__main__':
    reactor.listenUDP(9999, Server())
    reactor.run()
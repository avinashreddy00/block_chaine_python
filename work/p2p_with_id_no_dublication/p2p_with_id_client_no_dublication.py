from typing import Any
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from random import randint
import json
import copy
import base64

# addresses=[]

class Client(DatagramProtocol):
    def __init__(self, host, port):
        if host == 'localhost':
            host = "127.0.0.1"

        self.hostname = ''
        self.address = {}
        self.id = host, port
        self.server = '127.0.0.1', 9999
        print("working on id:", self.id)
    
    def startProtocol(self):
        # self.transport.write("ready".encode('utf-8'), self.server)
        self.hostname = input("Enter your ID:")
        mes = { "type": "ID", "id": self.hostname }
        mes_json = json.dumps(mes)
        self.transport.write(mes_json.encode(), self.server)
        
    def datagramReceived(self, datagram, addr):
        # datagram = datagram.decode('utf-8')
        data=json.loads(datagram)

        if addr == self.server:
            if data['type']=='list':
                # print("Choose a client from these:\n")
                self.address.clear()
                # self.address=copy.copy(data)
                del data['type']
                del data[self.hostname]
                print(type(self.address))
                for user_id, info in data.items():
                    self.address[user_id]=tuple(info)
                    print(f"User ID: {user_id}, Address: {info}")
                
                print(self.address)
            
            elif data['type']=='ping':
                print(data['message'])
                dic = {'type':'pong',
                        'message':'pingpong'}
                dic_json=json.dumps(dic)
                self.transport.write(dic_json.encode(), self.server)
                # self.transport.write("pong".encode('utf-8'), self.server)

            elif data['type']=='invalidhost':
                print(data['message'])
                self.hostname = input("Enter your ID:")
                mes = { "type": "ID", "id": self.hostname }
                mes_json = json.dumps(mes)
                self.transport.write(mes_json.encode(), self.server)

            reactor.callInThread(self.send_message)

        elif data['type']=='message':
            for key, val in self.address.items():
                if val == addr:
                    print(key, ":", data['message'])

    def send_message(self):
        while True:
            message = input("::: ")
            mes = { "type": "message",
                    "message": message
                    }
            mes_json = json.dumps(mes)
            for address in self.address.values():
                print('sending to: ',address)
                self.transport.write(mes_json.encode(), address)


if __name__ == '__main__':
    port = randint(1000, 5000)
    reactor.listenUDP(port, Client('localhost', port))
    reactor.run()

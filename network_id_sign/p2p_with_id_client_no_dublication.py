from typing import Any
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from random import randint
import json
import copy
import base64
import ecdsa
from hashlib import sha256


class Client(DatagramProtocol):
    def __init__(self, host, port):
        if host == 'localhost':
            host = "127.0.0.1"

        self.hostname = ''
        self.address = {}
        self.private_key = None
        self.public_key = None
        self.id = host, port
        self.responses = 0
        self.server = '127.0.0.1', 9999
        print("working on id:", self.id)
    
    def startProtocol(self):
        self.host_name()
        
    def datagramReceived(self, datagram, addr):
        # datagram = datagram.decode('utf-8')
        data=json.loads(datagram)
        if addr == self.server:
            if data['type']=='list':
                key_data = json.loads(datagram.decode())  # Decode JSON string
                self.private_key = ecdsa.SigningKey.from_pem(key_data["private_key"].encode())
                self.public_key = self.private_key.get_verifying_key()
                self.address.clear()
                del data['type']
                del data['private_key']
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
                self.host_name()

            reactor.callInThread(self.send_message)

        elif data['type']=='message':
            # Extract message and signature
            message_sign = data["message"].encode("utf-8")  # Encode for signing/verification
            encoded_signature = data["signature"]
            signature = base64.b64decode(encoded_signature)
            try:
                assert self.public_key.verify(signature, message_sign)
                print("Signature is valid.")
                mes = { "type": "response",
                    "message": f"Signature is valid response from {self.hostname}",
                    }
                mes_json = json.dumps(mes)
                self.transport.write(mes_json.encode(), addr)
                for key, val in self.address.items():
                    if val == addr:
                        print(key, ":", data['message'])
            except ecdsa.BadSignatureError:
                for key, val in self.address.items():
                    if val == addr:
                        print("Signature is invalid from : ",key)

        elif data['type']=='response':
            print(data["message"])
            self.responses+=1
            print("Responses count: ",self.responses)
        
        else:
            for key, val in self.address.items():
                    if val == addr:
                        print('Invalied data from : ',key)

    def send_message(self):
        while True:
            message = input("::: ")
            message_sign = message.encode('utf-8')
            signature = self.private_key.sign(message_sign)
            # Encode data as base64 string (common choice)
            encoded_signature = base64.b64encode(signature).decode("utf-8")

            mes = { "type": "message",
                    "message": message,
                    "signature": encoded_signature
                    }
            
            mes_json = json.dumps(mes)
            for address in self.address.values():
                self.transport.write(mes_json.encode(), address)
    
    def host_name(self):
        self.hostname = input("Enter your ID:")
        mes = { "type": "ID", "id": self.hostname }
        mes_json = json.dumps(mes)
        self.transport.write(mes_json.encode(), self.server)

if __name__ == '__main__':
    port = randint(1000, 5000)
    reactor.listenUDP(port, Client('localhost', port))
    reactor.run()

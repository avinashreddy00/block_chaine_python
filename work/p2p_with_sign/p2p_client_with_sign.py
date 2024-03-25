from typing import Any
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from random import randint
import json
import ecdsa
from hashlib import sha256
import base64

addresses=[]

class Client(DatagramProtocol):
    def __init__(self, host, port):
        if host == 'localhost':
            host = "127.0.0.1"

        self.id = host, port
        self.server = '127.0.0.1', 9999
        self.private_key = None
        self.public_key = None
        print("working on id:", self.id)
    
    def server_cmd(self, cmd_server):
        if cmd_server=='ready':
            self.transport.write("ready".encode('utf-8'), self.server)
        if cmd_server=='keys':
            self.transport.write("keys".encode('utf-8'), self.server)

    def startProtocol(self):
        self.server_cmd('ready')
        
    def datagramReceived(self, datagram, addr):
        data=json.loads(datagram)

        if addr == self.server:
            if data['type']=='clients':
                print("Choose a client from these:\n")
                print(data['address'])
                a = input("write host:"), int(input("write port:"))
                addresses.append(a)

            if data['type']=='keys':
                key_data = json.loads(datagram.decode())  # Decode JSON string
                self.private_key = ecdsa.SigningKey.from_pem(key_data["private_key"].encode())
                self.public_key = self.private_key.get_verifying_key()

            reactor.callInThread(self.send_message)
        elif data['type']=='message':
            # Extract message and signature
            message_sign = data["message"].encode("utf-8")  # Encode for signing/verification
            encoded_signature = data["signature"]
            signature = base64.b64decode(encoded_signature)
            # print(addr, ":", data['message'])
            try:
                assert self.public_key.verify(signature, message_sign)
                print("Signature is valid.")
                print(addr, ":", data['message'])
            except ecdsa.BadSignatureError:
                print("Signature is invalid from : ",addr)

        else:
            print('Invalied data from : ',addr)

    def send_message(self):
        while True:
            message = input("::: ")
            if message.lower() == 'ready':
                self.server_cmd('ready')
            
            if message.lower() == 'keys':
                self.server_cmd('keys')

            else:
                message_sign = message.encode('utf-8')
                signature = self.private_key.sign(message_sign)
                # Encode data as base64 string (common choice)
                encoded_signature = base64.b64encode(signature).decode("utf-8")

                mes = { "type": "message",
                       "message": message,
                       "signature": encoded_signature
                       }
                mes_json = json.dumps(mes)
                for address in addresses:
                    # self.transport.write(message.encode('utf-8'), address)
                    self.transport.write(mes_json.encode(), address)


if __name__ == '__main__':
    port = randint(1000, 5000)
    reactor.listenUDP(port, Client('localhost', port))
    reactor.run()

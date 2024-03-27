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

        self.hostname = None
        self.address = {}
        self.private_key = None
        self.public_key = None
        self.id = host, port

        self.leader_votes = 0
        self.validation_votes = 0
        self.leader_flag = False
        self.follower_flag = True
        self.temp_message = None

        self.server = '127.0.0.1', 9999
        print("working on id:", self.id)
    
    def startProtocol(self):
        print("Starting as follower .....")
        print("Connecting to Network ......")
        self.host_name()
    
    def host_name(self):
        self.hostname = None
        self.hostname = input("Enter your ID:")
        mes = { "type": "ID", "id": self.hostname }
        mes_json = json.dumps(mes)
        self.transport.write(mes_json.encode(), self.server)
        
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
                # print(type(self.address))
                for user_id, info in data.items():
                    self.address[user_id]=tuple(info)
                    # print(f"User ID: {user_id}, Address: {info}")
                # print(self.address)
            
            elif data['type']=='ping':
                # print(data['message'])
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
                # print("Signature is valid.")
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
        
        elif data['type']=='leadervoting':
            print(data["message"])
            if self.leader_flag == True and self.follower_flag == False:
                mes = { "type": "leadervotingresponse",
                    "message": "deny"
                    }
                mes_json = json.dumps(mes)
                self.transport.write(mes_json.encode(), addr)
            else:
                mes = { "type": "leadervotingresponse",
                    "message": "approved"
                    }
                mes_json = json.dumps(mes)
                self.transport.write(mes_json.encode(), addr)

        elif data['type']=='leadervotingresponse':
            if data["message"] == "approved":
                self.leader_votes+=1
                for key, val in self.address.items():
                    if val == addr:
                        print(key, ":", data['message'])
        
        elif data['type']=='response':
            print(data["message"])
            self.validation_votes+=1
        
        else:
            for key, val in self.address.items():
                    if val == addr:
                        print('Invalied data from : ',key)
        
    
    def leader_election(self):
        if self.leader_votes >= 2:
            print(f"Response count in 2 seconds: {self.leader_votes}")
            print("Got sufficient votes and elected as leader")
            self.leader_flag = True
            self.follower_flag = False
            self.message_validation()
            print("Voting for validation started ...")
            reactor.callLater(3, self.reset_follower)  # Reset leader and follower flags
        else:
            print(f"Response count in 2 seconds: {self.leader_votes}")
            print("Got not enough votes and con't be a leader at this time")
        self.leader_votes = 0  # Reset response count
        print("Leader election ended ...")
    
    def reset_follower(self):
        if self.validation_votes >=2:
            print(f"Votes for validation: {self.validation_votes}")
            print("Got sufficient votes create the block and distrubute")
        else:
            print(f"Votes for validation: {self.validation_votes}")
            print("Got insufficient votes can not create the block")
        self.leader_flag = False
        self.follower_flag = True
        self.validation_votes = 0
        self.temp_message = None
        print("Validation election ended ...")
        print("Leader time up and back to follower")
    
    def message_validation(self):
        message_sign = self.temp_message.encode('utf-8')
        signature = self.private_key.sign(message_sign)
        # Encode data as base64 string (common choice)
        encoded_signature = base64.b64encode(signature).decode("utf-8")

        mes = { "type": "message",
                "message":self.temp_message,
                "signature": encoded_signature
                }
        
        mes_json = json.dumps(mes)
        for address in self.address.values():
            self.transport.write(mes_json.encode(), address)
    

    def send_message(self):
        while True:
            self.temp_message = input(":::")
            mes = { "type": "leadervoting",
                "message":f"{self.hostname} want to become leader"
                }
        
            mes_json = json.dumps(mes)
            for address in self.address.values():
                self.transport.write(mes_json.encode(), address)
            print("leader election started ...")
            reactor.callLater(2, self.leader_election)  # Reset counter after 2 seconds
    

if __name__ == '__main__':
    port = randint(1000, 5000)
    reactor.listenUDP(port, Client('localhost', port))
    reactor.run()

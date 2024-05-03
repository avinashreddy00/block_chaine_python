from typing import Any
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from random import randint
import json
import copy
import base64
import ecdsa
from hashlib import sha256

from blockchain import Block, Blockchain
import datetime as date

import pandas as pd

import random


class Client(DatagramProtocol):
    def __init__(self, host, port):
        if host == 'localhost':
            host = "127.0.0.1"

        self.hostname = 'UNHMSDS06'
        self.address = {}
        self.private_key = None
        self.public_key = None
        self.id = host, port

        self.loop_calling = None
        self.follower_time = None
        self.election_time = None
        self.leader_votes = 0
        self.validation_votes = 0

        self.election_term = 0
        self.total_votes = 0
        self.voted_for = []
        self.load_election_data()
        self.leader = None

        self.vote_flag = False
        
        self.leader_flag = False
        self.candidate_flag  =False
        self.follower_flag = True
        self.temp_message = []

        self.df = pd.read_csv("8005.csv")

        self.server = '127.0.0.1', 9999
        print("working on id:", self.id)

        # Initialize blockchain
        self.blockchain = Blockchain()
        self.temp_block = None
        # self.validation_block = None
        # self.temp_dict = None
    
    def startProtocol(self):
        print("Starting as follower .....")
        print("Connecting to Network ......")
        self.host_name()
        self._follower()
    
    def host_name(self):
        mes = { "type": "ID", "id": self.hostname }
        mes_json = json.dumps(mes)
        self.transport.write(mes_json.encode(), self.server)

    def load_election_data(self):
        try:
            with open("election_data.json", "r") as file:
                saved_data = json.load(file)
                self.election_term = saved_data.get("election_term", 0)
                self.total_votes = saved_data.get("total_votes", 0)
        except FileNotFoundError:
            # If file does not exist, initialize variables
            self.election_term = 0
            self.total_votes = 0

    def save_election_data(self):
        data = {
            "election_term": self.election_term,
            "total_votes": self.total_votes,
            "nodeid":f'{self.hostname}'
        }
        with open("election_data.json", "w") as file:
            json.dump(data, file)

    
    def _follower(self):
        # self.loop_calling.stop
        self.follower_flag = True
        self.candidate_flag = False
        self.leader_flag = False
        print("Follower ...")
        random_number = random.randint(3, 30)
        self.follower_time = reactor.callLater(random_number, self._candidate)
    
    def _candidate(self):
        # self.loop_calling.stop
        self.follower_flag = False
        self.candidate_flag = True
        self.leader_flag = False
        self.follower_time = None

        self.vote_flag = False
        
        # Increment election term
        self.election_term += 1

        # Reset votes for this term
        self.total_votes = 0
        self.leader_votes = 0

        print("Candidate ...")
        # send votting request for to other nodes
        last_block = self.blockchain.get_latest_block()

        mes = { "type": "leadervoting",
               "index":last_block.index,
               "term":self.election_term,
               "nodeid":f'{self.hostname}',
                "message":f"voting for {self.hostname}"
                }
        
        mes_json = json.dumps(mes)
        for address in self.address.values():
            self.transport.write(mes_json.encode(), address)

        self.election_time = reactor.callLater(10, self._leader)
        pass

    def _leader(self):
        if self.leader_votes >= 5:
            self.follower_flag = False
            self.candidate_flag = False
            self.leader_flag = True
            self.total_votes = self.leader_votes
            self.save_election_data()
            mes = { "type": "leader",
               "nodeid":f'{self.hostname}'
                }
        
            mes_json = json.dumps(mes)
            for address in self.address.values():
                self.transport.write(mes_json.encode(), address)
            self.transport.write(mes_json.encode(), self.server)

            print("Leader ...")
            self.loop_calling = LoopingCall(self.send_message)
            self.loop_calling.start(5)
            reactor.callLater(20, self.loop_calling.stop)
            reactor.callLater(20, self._candidate)
        
        else:
            self.leader_votes = 0
            self.follower_flag = True
            self.candidate_flag = False
            self.leader_flag = False
            print("Not becoming Leader ...")
            self._follower()
    
    def send_message(self):
        if self.follower_flag == False and self.candidate_flag == False and self.leader_flag == True:
            last_block = self.blockchain.get_latest_block()
            # request for data from all the nodes, create and send block to all the nodes
            mes = { "type": "values",
                "index":last_block.index
                }
            mes_json = json.dumps(mes)
            for address in self.address.values():
                self.transport.write(mes_json.encode(), address)
            print("requested for data ...")
            values = self.df.iloc[last_block.index]
            host = f'{self.hostname}'
            self.temp_message.append(str((host,values['Consumed'],values['Produced'])))
            reactor.callLater(3, self._block_sending)
        
    def _block_sending(self):
        # create block and send
        self.temp_block = self.blockchain.create_block(Block(index=Block.last_index + 1, timestamp=date.datetime.now(), data=str(self.temp_message), previous_hash=""))
        mes = Block.to_dict(self.temp_block)
        mes ['type'] = "block"
        mes_json = json.dumps(mes)
        for address in self.address.values():
            self.transport.write(mes_json.encode(), address)
        self.transport.write(mes_json.encode(), self.server)
        self.blockchain.add_block(self.temp_block)
        self.temp_message.clear()

        print("block added ....\n")
        print("Block #" + str(self.temp_block.index))
        print("Timestamp: " + str(self.temp_block.timestamp))
        print("Data: " + str(self.temp_block.data))
        print("Hash: " + self.temp_block.hash)
        print("Previous Hash: " + self.temp_block.previous_hash)
        print("\n")
    
        
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

            # reactor.callInThread(self.send_message)
        
        elif data['type']=='leadervoting':
            print(data["message"])
            last_block = self.blockchain.get_latest_block()
            if self.leader_flag == False and (self.candidate_flag == True or self.follower_flag == True) and last_block.index <= data['index']:
                # We have to check the election term and index
                # need to check the leader election term
                self.voted_for.append(data['nodeid'])
                mes = { "type": "leadervotingresponse",
                    "message": "approved"
                    }
                mes_json = json.dumps(mes)
                self.transport.write(mes_json.encode(), addr)
                self.vote_flag = True

        elif data['type']=='leadervotingresponse':
            if data["message"] == "approved":
                self.leader_votes+=1
                for key, val in self.address.items():
                    if val == addr:
                        print(key, ":", data['message'] + "for leader election")
                    
        elif data['type']=='leader':
            self.leader = data['nodeid']
        
        elif data['type']=='values':
            index = data['index']
            # check if this request is from leader or not if leader
            # send sensor values to leader
            self.voted_for = []
            values = self.df.iloc[index]
            mes = { "type": "valuesresponse",
                    "Host": f'{self.hostname}',
                    "Consumed": str(values['Consumed']),
                    "Produced": str(values['Produced'])
                    }
            mes_json = json.dumps(mes)
            self.transport.write(mes_json.encode(), addr)
        
        elif data['type']=='valuesresponse':
            # Note responses from all the nodes and form a list
            self.temp_message.append(str((data['Host'],data['Consumed'],data['Produced'])))
        
        elif data['type']=='block':
            del data['type']
            new_block = Block.from_dict(data)
            self.blockchain.add_block(new_block)
            self.vote_flag = False

            print("block added ....\n")
            print("Block #" + str(new_block.index))
            print("Timestamp: " + str(new_block.timestamp))
            print("Data: " + str(new_block.data))
            print("Hash: " + new_block.hash)
            print("Previous Hash: " + new_block.previous_hash)
            print("\n")

            if self.follower_flag == True:
                self.follower_time.cancel()
                self._follower()

            elif self.candidate_flag == True:
                self.election_time.cancel()
                self._follower()

        
        else:
            for key, val in self.address.items():
                    if val == addr:
                        print('Invalied data from : ',key)
        
    

if __name__ == '__main__':
    port = randint(1000, 5000)
    reactor.listenUDP(port, Client('localhost', port))
    reactor.run()

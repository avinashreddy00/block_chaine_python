import ecdsa
from hashlib import sha256
from typing import Any
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from random import randint

addresses = []

class Client(DatagramProtocol):
    def __init__(self, host, port):
        if host == 'localhost':
            host = "127.0.0.1"

        self.id = host, port
        self.server = '127.0.0.1', 9999
        self.private_key = ecdsa.SigningKey.generate()  # Generate private key
        self.public_key = self.private_key.get_verifying_key()  # Derive public key
        print("Working on id:", self.id)

    def startProtocol(self):
        self.transport.write("ready".encode('utf-8'), self.server)

    def datagramReceived(self, datagram, addr):
        # datagram = datagram.decode('utf-8')

        if addr == self.server:
            datagram = datagram.decode('utf-8')
            print("Choose a client from these:\n", datagram)
            a = input("Write host:"), int(input("Write port:"))
            addresses.append(a)
            reactor.callInThread(self.send_message)
        else:
            if self.verify_signature(datagram, addr):
                print(addr, ":", datagram.decode())
            else:
                print("Invalid signature from:", addr)

    def send_message(self):
        while True:
            message = input("::: ")
            if message.lower() == 'ready':
                self.transport.write("ready".encode('utf-8'), self.server)
            for address in addresses:
                self.send_signed_message(message, address)

    def send_signed_message(self, message, address):
        message=message.encode('utf-8')
        signature = self.private_key.sign(sha256(message).digest())  # Sign the message
        # self.transport.write(message + signature, address)  # Send message with signature
        self.transport.write(message+signature, address)  # Send message with signature

    def verify_signature(self, message, addr):
        # Extract signature from the received messagee
        print(message)

        received_signature = message[-self.private_key.curve.baselen:]
        print(received_signature)

        received_message = message[:-self.private_key.curve.baselen]
        print(received_message)

        # Retrieve public key associated with the sender's address
        sender_public_key = self.get_public_key(addr)
        print(sender_public_key)

        # Verify the signature using the sender's public key
        try:
            sender_public_key.verify(received_signature, sha256(received_message).digest())
            m=received_message.decode()
            print(m)
            
            print(addr, ":", m.decode('utf-8'))
            return True
        except ecdsa.BadSignatureError:
            return False

    def get_public_key(self, addr):
        # For simplicity, assume the public key is known for each client
        # In a real-world scenario, you'd need a way to retrieve the public key associated with an address
        return self.public_key


if __name__ == '__main__':
    port = randint(1000, 5000)
    reactor.listenUDP(port, Client('localhost', port))
    reactor.run()

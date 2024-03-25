from twisted.internet import reactor
# from twisted.internet.interfaces import IAddress
from twisted.internet.protocol import Protocol, connectionDone
from twisted.internet.protocol import ServerFactory as servFactory
from twisted.internet.endpoints import TCP4ServerEndpoint

class Server(Protocol):
    def __init__(self, users):
        self.users=users
        self.name = ""

    def connectionMade(self):
        print("New Connection")
        # self.users.append(self)
        # self.transport.write("Hellow from server".encode('utf-8'))

    def add_user(self, name):
        if name not in self.users:
            self.users[self] = name
            self.name = name
        else:
            self.transport.write("wrong username, try another".encode("utf-8"))

    def dataReceived(self, data):
        data = data.decode("utf-8")

        if not self.name:
            self.add_user(data)
            return

        for protocol in self.users.keys():
            if protocol != self:
                protocol.transport.write(f"{self.name}: {data}".encode('utf-8'))

    def connectionLost(self, reason=connectionDone):...

class ServerFactory(servFactory):
    def __init__(self):
        self.users={}

    def buildProtocol(self, addr):
        return Server(self.users)

if __name__ == '__main__':
    endpoint = TCP4ServerEndpoint(reactor,2000)
    endpoint.listen(ServerFactory())
    reactor.run()
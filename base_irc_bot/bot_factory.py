from twisted.internet import protocol
from twisted.internet import reactor

class BotFactory(protocol.ClientFactory):
    """A factory for BaseIRCbot.

    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    # e.g. BaseIRCBot
    # protocol = BaseIRCBot

    def __init__(self, channel, protocol, logfile_path):
        self.channel = channel
        self.protocol = protocol
        self.filename = logfile_path

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


    def connect(self, server, port):
        """Connect the factory to the host/port"""
        reactor.connectTCP(server, port, self)

    def run(self):
        """Run the bot"""
        reactor.run()

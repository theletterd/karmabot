import time
from twisted.words.protocols import irc

from message_logger import MessageLogger

class BaseIRCBot(irc.IRCClient, object):

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.logger = MessageLogger(open(self.factory.filename, "a"))
        self.logger.log(
            "[connected at %s]" %
            time.asctime(time.localtime(time.time()))
        )

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.log(
            "[disconnected at %s]" %
            time.asctime(time.localtime(time.time()))
        )
        self.logger.close()

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        # i.e. /me <something>
        user = user.split('!', 1)[0]
        self.logger.log("* %s %s" % (user, msg))

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        self.logger.log(msg)

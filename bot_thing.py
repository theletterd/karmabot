# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.


"""
An example IRC log bot - logs a channel's events to a file.

If someone says the bot's name in the channel followed by a ':',
e.g.

  <foo> logbot: hello!

the bot will reply:

  <logbot> foo: I am a log bot

Run this script with two arguments, the channel name the bot should
connect to, and file to log to, e.g.:

  $ python ircLogBot.py test test.log

will log channel #test to the file 'test.log'.
"""


# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# mine
from persistence import Persistence
from eightball import EightBall
from message_logger import MessageLogger

# system imports
import time, sys

import re
karma_regex = re.compile('\w+\+\+|\w+--')


class HyacinthBot(irc.IRCClient):
    """An IRC bot."""

    nickname = "Hyacinth"

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.logger = MessageLogger(open(self.factory.filename, "a"))
        self.logger.log("[connected at %s]" %
                        time.asctime(time.localtime(time.time())))

        # this is a stupid place for it
        self.persistence = Persistence()
        self.eightball = EightBall()

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.log("[disconnected at %s]" %
                        time.asctime(time.localtime(time.time())))
        self.logger.close()


    # callbacks for events

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        self.logger.log("[I have joined %s]" % channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        self.logger.log(msg)

        # Check to see if they're sending me a private message
        if channel == self.nickname:
            msg = "It isn't nice to whisper!  Play nice with the group."
            self.msg(user, msg)
            return

        # Otherwise check to see if it is a message directed at me
        if msg.startswith(self.nickname + ":"):
            msg = "%s: I am a log bot" % user
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))
            return

        self.process_message(user, channel, msg)

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        # i.e. /me <something>
        user = user.split('!', 1)[0]
        self.logger.log("* %s %s" % (user, msg))

    # irc callbacks

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        self.logger.log("%s is now known as %s" % (old_nick, new_nick))


    # For fun, override the method that determines how a nickname is changed on
    # collisions. The default method appends an underscore.
    def alterCollidedNick(self, nickname):
        """
        Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration.
        """
        return nickname + '^'

    def process_message(self, user, channel, msg):
        self.record_karmas(user, channel, msg)
        if msg.startswith('!karma'):
            self.process_karmastring(user, channel, msg)
        elif msg.startswith('!8ball') and msg.endswith('?'):
            self.msg(channel, self.eightball.get_answer())
        elif msg.startswith('!markov'):
            self.msg(channel, 'not just yet')
        elif msg.startswith('!commands'):
            self.msg(channel, '!karma, !8ball, !markov, !commands')


    def process_karmastring(self, user, channel, msg):
        # this is a stupid hack, since if there's not a space at the end
        # it fails strangely
        msg = msg + ' '
        split_msg = msg.split(' ')
        if len(split_msg) == 1:
            requested_user = user
        else:
            requested_user = split_msg[1]
        msg = self.persistence.get_karma(requested_user)
        self.msg(channel, str(msg))

    def record_karmas(self, user, channel, msg):
        karmas = karma_regex.findall(msg)

        # fuckin' indentation
        if not karmas:
            return

        for karma in karmas:
            recipient = karma[:-2]
            if recipient == user:
                self.msg(channel, 'no altering your own karma, %s' % user)
                continue
            if karma.endswith('--'):
                self.persistence.record_karma(recipient, up=False)
            else:
                self.persistence.record_karma(recipient, up=True)


class HyacinthBotFactory(protocol.ClientFactory):
    """A factory for HyacinthBots.

    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    protocol = HyacinthBot

    def __init__(self, channel, filename):
        self.channel = channel
        self.filename = filename

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)

    # create factory protocol and application
    f = HyacinthBotFactory(sys.argv[1], sys.argv[2])

    # connect factory to this host and port
    reactor.connectTCP("irc.freenode.net", 6667, f)

    # run bot
    reactor.run()

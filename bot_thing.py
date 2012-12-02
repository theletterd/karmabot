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

# system imports
import random
import re
import sys
import time

import config

from base_irc_bot.base_irc_bot import BaseIRCBot
from base_irc_bot.bot_factory import BotFactory
from eightball.eightball import EightBall
from greeter.greeter import Greeter
from karmastore.karmastore import KarmaStore
from markov.markov import Markov
from rate_limiter.rate_limiter import RateLimiter
from roller.roller import Roller

karma_regex = re.compile('\w+\+\+|\w+--')


class HyacinthBot(BaseIRCBot):
    """An IRC bot."""

    nickname = "Hyacinth"

    def __init__(self, *args, **kwargs):
        super(HyacinthBot, self).__init__(*args, **kwargs)
        self.karma_store = KarmaStore(config.karma_db_path)
        self.eightball = EightBall(config.eightball_answers_path)
        self.markov = Markov(config.markov_db_path)
        self.roller = Roller()
        self.rate_limiter = RateLimiter()
        self.greeter = Greeter(config.greetings_path)

    # callbacks for events
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
            msg = "%s: I am the little death that brings total oblivion" % user
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))
            return

        self.process_message(user, channel, msg)

    def userJoined(self, user, channel):
        """Greets a user when they join the channel"""
        greeting = self.greeter.greet(user)
        if greeting:
            self.msg(channel, greeting)

    def process_message(self, user, channel, msg):
        self.record_karmas(user, channel, msg)
        self.markov.add_single_line(msg)

        if msg.startswith('!'):
            self.rate_limiter.add_request(user)
            if not self.rate_limiter.is_rate_limited(user):
                self.process_command(user, channel, msg)
        else:
            self.send_markov_sentence(user, channel, msg)

    def process_command(self, user, channel, msg):
        if msg.startswith('!karma'):
            self.process_karmastring(user, channel, msg)
        elif msg.startswith('!8ball') and msg.endswith('?'):
            self.msg(channel, self.eightball.get_answer())
        elif msg.startswith('!markov'):
            new_msg = msg.replace('!markov', '')
            self.send_markov_sentence(user, channel, new_msg, force=True)
        elif msg.startswith('!roll'):
            new_msg = msg.replace('!roll', '')
            self.roll(user, channel, new_msg)
        elif msg.startswith('!commands'):
            self.msg(channel, '!karma, !8ball, !markov, !roll, !commands')

    def send_markov_sentence(self, user, channel, message, force=False):
        thing_to_say = self.markov.generate_sentence(message)
        if force or (len(thing_to_say.split()) > 5 and random.random() > 0.995):
            self.msg(channel, thing_to_say)

    def process_karmastring(self, user, channel, msg):
        # this is a stupid hack, since if there's not a space at the end
        # it fails strangely
        msg = msg + ' '
        split_msg = msg.split(' ')
        if len(split_msg) == 1:
            requested_user = user
        else:
            requested_user = split_msg[1]
        msg = self.karma_store.get_karma(requested_user)
        self.msg(channel, str(msg))

    def record_karmas(self, user, channel, msg):
        karmas = karma_regex.findall(msg)

        if not karmas:
            return

        for karma in karmas:
            recipient = karma[:-2] # on account of the ++ or --
            if recipient == user:
                self.msg(channel, 'no altering your own karma, %s' % user)
                continue
            if karma.endswith('--'):
                self.karma_store.record_karma(recipient, up=False)
            else:
                self.karma_store.record_karma(recipient, up=True)

    def roll(self, user, channel, msg):
        die, value = self.roller.roll(msg)
        roll_string = '%s rolls %s... %d' % (user, die, value)
        self.msg(channel, roll_string)


if __name__ == '__main__':
    channel = sys.argv[1]
    factory = BotFactory(channel, HyacinthBot, config.logfile_path)
    factory.connect("irc.freenode.net", 6667)
    factory.run()

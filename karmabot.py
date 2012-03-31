import sys
import socket, ssl
import os
import sqlite3
import time
import re

SQLITE_DB = 'karma'
SERVER = 'irc.freenode.net'
PORT = 6697
USERNAME = 'Lizzypants'
BOTNICK = 'Hyacinth'
CHANNEL = '#r.crossdressing'
PASSWORD = ''
KARMA_TABLE = 'karmalog'
karma_regex = re.compile('\w+\+\+|\w+--')


def connect_to_irc():
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((SERVER, PORT)) #Connect to server
  ircsocket = ssl.wrap_socket(s)
  ircsocket.send('PASS %s\n' % PASSWORD)
  ircsocket.send('NICK %s\n' % BOTNICK)
  ircsocket.send('USER %s %s %s :%s\n' % (USERNAME, USERNAME, SERVER, BOTNICK)) #Identify to server
  ircsocket.send('JOIN %s\n' % CHANNEL)
  return ircsocket


def connect_to_db():
  conn = sqlite3.connect(SQLITE_DB)
  c = conn.cursor()

  # check that the table existsxs
  c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = '%s'" % KARMA_TABLE)
  table_exists = c.fetchone()
  if not table_exists:
    c.execute("""
      create table %s
      (time integer, name text, score integer)""" % KARMA_TABLE)

  return conn, c

def say(msg):
  ircsocket.send('PRIVMSG %s :%s\n' % (CHANNEL, msg))

def update_karma(msg):
  karmas = karma_regex.findall(msg)
  for karma in karmas:
    recipient = karma[:-2]
    if karma.endswith('--'):
      score = -1
    else:
      score = 1

    c.execute('insert into %s values (?,?,?)' % KARMA_TABLE, (int(time.time()), recipient, score))
    conn.commit()

def get_karma(username):
    c.execute('select name, sum(score) from %s where name = ?' % KARMA_TABLE, (username,))
    username_score = c.fetchone()
    user_karma = 'karma for %s is %s. ' % username_score

    c.execute('select name, sum(score) as sum_score from %s group by name order by sum_score desc limit 3' % KARMA_TABLE)
    top_3 = "Most karmic: " + ', '.join("%s (%s)" % entry for entry in c)

    say(user_karma + top_3)


ircsocket = connect_to_irc()
conn, c = connect_to_db()

while 1:
  line = ircsocket.recv(2048).strip('\r\n')
  if "PING :" in line:
    ircsocket.send('PONG :pingis\n')
  elif "PRIVMSG " in line:
    sender = line.split('!')[0][1:]

    # ignore anything the bot says
    if sender == BOTNICK:
      continue

    msg = line.split('PRIVMSG')[1]
    msg_start_index = msg.find(':')
    msg = msg[msg_start_index+1:]

    if msg.startswith('!karma'):
      get_karma(sender)
    elif msg.startswith('!commands'):
      say('Supported commands: !karma, !commands')
    else:
      update_karma(msg)

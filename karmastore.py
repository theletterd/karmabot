import sqlite3
import time

import config

KARMA_TABLE = 'karmalog'
KARMA_TABLE_CREATE = 'create table %s (time integer, name text, score integer)' % KARMA_TABLE


class KarmaStore(object):

    def __init__(self):
        cursor = self.get_cursor()

        if not self.table_exists(cursor, KARMA_TABLE):
            cursor.execute(KARMA_TABLE_CREATE)

        self.close_cursor(cursor)

    # maybe it makes sense to write your own context manager
    def get_cursor(self):
        return sqlite3.connect(config.karma_db).cursor()

    def close_cursor(self, cursor):
        cursor.connection.commit()
        cursor.close()

    def txn(f, *args, **kwargs):
        def wrapped_func(self, *args, **kwargs):
            cursor = self.get_cursor()
            result = f(self, cursor, *args, **kwargs)
            self.close_cursor(cursor)
            return result
        return wrapped_func

    def table_exists(self, cursor, table):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = '%s'" % table)
        return bool(cursor.fetchone())

    def connect_to_db(self):
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        return conn, cursor

    # interesting stuff
    # this should be split off into somewhere else, a bit.
    @txn
    def record_karma(self, cursor, username, up=True):
        score = 1 if up else -1
        now_timestamp = int(time.time())
        cursor.execute('insert into %s values (?,?,?)' % KARMA_TABLE, (now_timestamp, username, score))
        cursor.connection.commit()

    @txn
    def get_karma(self, cursor, username=None):
        if username:
            cursor.execute('select sum(score), count(*) from %s where name = ?' % KARMA_TABLE, (username,))
            total_score, count = cursor.fetchone()
            if not count:
                return "No karma recorded for %s :(" % username

            # if we just assume that there's only ever increments and decrements, we
            # can figure out upvotes and downvotes ourselves

            increments = (count + total_score) / 2
            decrements = increments - total_score

            return "%s has karma of %s (+%d/-%d)" % (username, total_score, increments, decrements)
        else:
            cursor.execute('select name, sum(score) as sum_score from %s group by name order by sum_score desc limit 3' % KARMA_TABLE)
            return  "Most karmic: " + ', '.join("%s (%s)" % entry for entry in cursor)





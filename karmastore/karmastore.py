import sqlite3
import time

import config


class KarmaStore(object):

    def __init__(self, db_path):
        self.db_path = db_path
        self.create_table_if_non_existent()

    def db_transaction(function):
        def wrapped_func(self, *args, **kwargs):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            result = function(self, cursor, *args, **kwargs)

            conn.commit()
            cursor.close()

            return result
        return wrapped_func

    @db_transaction
    def create_table_if_non_existent(self, cursor):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = '%s'" % config.karma_table)
        name = cursor.fetchone()

        if not name:
            cursor.execute(
                """
                    CREATE TABLE %s (
                        time INTEGER NOT NULL,
                        name text NOT NULL,
                        score integer
                    )
                """ % config.karma_table
            )
            cursor.execute("CREATE INDEX name_index ON %s(name)" % config.karma_table)


    @db_transaction
    def record_karma(self, cursor, username, up=True):
        score = 1 if up else -1
        now_timestamp = int(time.time())
        cursor.execute('insert into %s values (?,?,?)' % config.karma_table, (now_timestamp, username, score))

    @db_transaction
    def get_karma(self, cursor, username=None):
        if username:
            cursor.execute('select sum(score), count(*) from %s where name = ?' % config.karma_table, (username,))
            total_score, count = cursor.fetchone()
            if not count:
                return "No karma recorded for %s :(" % username

            # if we just assume that there's only ever increments and decrements, we
            # can figure out upvotes and downvotes ourselves

            increments = (count + total_score) / 2
            decrements = increments - total_score

            return "%s has karma of %s (+%d/-%d)" % (username, total_score, increments, decrements)
        else:
            cursor.execute('select name, sum(score) as sum_score from %s group by name order by sum_score desc limit 3' % config.karma_table)
            return  "Most karmic: " + ', '.join("%s (%s)" % entry for entry in cursor)





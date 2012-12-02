import itertools
import random
import sqlite3

import config
from wordbag import WordBag

class MarkovStorage(object):

    def __init__(self, db_path):
        self.db_path = db_path
        self.create_table_if_non_existent()

    def db_transaction(function):
        def wrapped(self, *args, **kwargs):
            # get the connection and cursor
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # call the original function
            result = function(self, cursor, *args, **kwargs)

            # close everything
            conn.commit()
            cursor.close()

            # return the result
            return result
        return wrapped

    @db_transaction
    def create_table_if_non_existent(self, cursor):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=(?)", (config.word_table,))
        name = cursor.fetchone()

        # create table if it doesn't exist
        if not name:
            cursor.execute(
                """
	            CREATE TABLE %s (
	                id INTEGER PRIMARY KEY,
	                phrase varchar(255) NOT NULL,
	                word varchar(255) NOT NULL,
	                count int NOT NULL
	            )
	            """ % config.word_table
	    )
            cursor.execute("CREATE INDEX phrase_index ON %s(phrase)" % config.word_table)


    @db_transaction
    def store_phrases_and_words(self, cursor, input):
        # Expect input to be a list of tuples, where the first element is the phrase
        # and the second element is a word
        cursor.executemany('INSERT INTO %s values (NULL, ?, ?, 1)' % config.word_table, input)

    @db_transaction
    def get_wordbag_for_phrase(self, cursor, phrase):
        cursor.execute('SELECT word from %s where phrase = ?' % config.word_table, [phrase])
        results = cursor.fetchall()
        return WordBag(itertools.chain(*results))

    def phrase_exists(self, phrase):
        return bool(self.get_wordbag_for_phrase(phrase))

    @db_transaction
    def get_candidate_phrases(self, cursor, words):
        phrases = []
        for word in words:
            cursor.execute('SELECT phrase from %s where phrase like ? || "%%" LIMIT 1000' % config.word_table, [word])
            phrases.extend(cursor.fetchall())
        return [' '.join(phrase) for phrase in phrases]

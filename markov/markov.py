# -*- coding: utf-8 -*-

import random
import re

import config

from markov_storage import MarkovStorage

URL_REGEX = '(https?://)|(www.*\.)|([a-z0-9.\-]+[\.][a-z]{2,4}/)'
# from http://daringfireball.net/2010/07/improved_regex_for_matching_urls, not working properly yet.
# URL_REGEX_2 = """(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))"""

class Markov(object):
    chain_length = 2
    default_max_words = 50
    min_sentence_length = 5

    def __init__(self, db_path, training_file=None):
        self.training_file = training_file
        self.db_storage = MarkovStorage(db_path)

        if self.training_file:
            print 'Training brain...'
            # TODO drop db table
            self.train(self.training_file)
            print 'Training completed!'

    def train(self, filename):
        """Given a filename, parse the log file and add the words to the brain.
        Note: THIS DOES NOT WIPE OUT THE CURRENT BRAIN
        """
        with open(filename, 'r') as f:
            phrases_and_words = []

            for index, line in enumerate(f):
                # decoding, since input is not unicode
                cleaned_line = self.get_cleaned_line(line.decode('utf-8', 'ignore'))

                if cleaned_line:
                    phrases_and_words.extend(self.get_phrase_and_words_from_line(cleaned_line))

                if index % 10000 == 0:
                    self.db_storage.store_phrases_and_words(phrases_and_words)
                    phrases_and_words = []

        self.db_storage.store_phrases_and_words(phrases_and_words)

    def add_single_line(self, line):
        # decoding, since input is not unicode
        cleaned_line = self.get_cleaned_line(line.decode('utf-8', 'ignore'))
        if cleaned_line:
            phrases_and_words = self.get_phrase_and_words_from_line(cleaned_line)
            self.db_storage.store_phrases_and_words(phrases_and_words)

    def redact_urls(self, msg):
        words = []
        for word in msg.split(' '):
            if re.match(URL_REGEX, word):
                word = u'URL_REDACTED'
            words.append(word)
        return ' '.join(words)

    def get_cleaned_line(self, msg):
        # remove any timing information, assuming it's from our logging whatsit
        msg = re.sub('\[\d\d:\d\d:\d\d\]', '', msg)
        msg = msg.strip()

        if not msg:
            return

        # this ensures we ignore any commands.
        if msg.startswith('!'):
            return

        # redact urls
        msg = self.redact_urls(msg)

        # this is annoying.
        msg = re.sub('\.+', ' ', msg)
        words = msg.split()

        # to save space, only allow sentences greater than a certain length
        # to enter the brain
        if len(words) < self.min_sentence_length:
            return

        return ' '.join(words)

    def get_phrase_and_words_from_line(self, line):
        phrases_and_words = []

        buf = [config.stop_word] * self.chain_length

        for word in line.split():
            # make the key lowercase
            low_buffer = ' '.join(map(unicode.lower, buf))
            phrases_and_words.append((low_buffer, word))
            del buf[0]
            buf.append(word)

        # also need to add the stop word
        low_buffer = ' '.join(map(unicode.lower, buf))
        phrases_and_words.append((low_buffer, config.stop_word))

        return phrases_and_words

    def generate_sentence(self, input_message, max_words=default_max_words):
        # input needs decoding
        input_words = input_message.decode('utf-8', 'ignore').strip().split()

        # let's choose `chain_length` consecutive words from the input_message
        random_appropriate_index = random.randint(0, max(0, len(input_words) - self.chain_length))
        buf = input_words[random_appropriate_index:random_appropriate_index + self.chain_length]

        if len(buf) < self.chain_length or not self.db_storage.phrase_exists(' '.join(buf)):
            # ok, so we'll cheat - let's randomly choose a word from what we've got
            # and then generate a buffer from that.
            random_word = random.choice(input_words)

            # build up some candidate phrases
            candidates = self.db_storage.get_candidate_phrases([random_word])

            if candidates:
                buf = random.choice(candidates).split()
            else:
                # in the case of nothing, let's just return nothing.
                return u''

        output_words = buf[:]
        for _ in xrange(max_words):
            low_buffer = ' '.join(map(unicode.lower, buf))
            word_bag = self.db_storage.get_wordbag_for_phrase(low_buffer)

            if word_bag:
                next_word = word_bag.weighted_random_word()
            else:
                next_word = config.stop_word
                # if we don't have a word_bag, we assume that it's because
                # a stop-word word-bag was trimmed, so consider it a dead end.
                break

            # or similarly here.
            if next_word == config.stop_word:
                break

            output_words.append(next_word)
            buf.append(next_word)

            # now, if appropriate, trim buf down
            while len(buf) > self.chain_length:
                del buf[0]

        return ' '.join(output_words).encode('utf-8')

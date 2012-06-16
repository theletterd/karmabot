from collections import defaultdict
import cPickle as pickle
import random
import re

STOP_WORD = "\n"

class Markov(object):
    chain_length = 2
    default_max_words = 50

    def __init__(self, brain_file=None, training_file=None):
        self.brain = defaultdict(list)
        self.brain_file = brain_file
        self.training_file = training_file

        if self.training_file:
            print 'Training brain...'
            self.retrain(self.training_file)
            print 'Training completed!'
        if self.brain_file:
            self.load_brain(self.brain_file)

    def dump_brain(self, filename):
        with open(filename, 'w') as f:
            pickle.dump(self.brain, f)

    def load_brain(self, filename):
        with open(filename, 'r'):
            self.brain = pickle.load(f)

    def retrain(self, filename):
        with open(filename, 'r') as f:
            for line in f:
                if line:
                    self.add_to_brain(line)

    def add_to_brain(self, msg):
        # remove any timing information, assuming it's from our logging whatsit
        msg = re.sub('\[\d\d:\d\d:\d\d\]', '', msg)
        msg = msg.strip()

        if not msg:
            return
        buf = [STOP_WORD] * self.chain_length
        for word in msg.split():
            self.brain[tuple(buf)].append(word)
            del buf[0]
            buf.append(word)
        self.brain[tuple(buf)].append(STOP_WORD)


    def generate_sentence(self, input_message, max_words=default_max_words):
        # let's choose `chain_length` consecutive words from the input_message
        input_words = input_message.strip().split()
        random_appropriate_index = random.randint(0, max(0, len(input_words) - self.chain_length))
        buf = input_words[random_appropriate_index:random_appropriate_index + self.chain_length]

        if len(buf) < self.chain_length or tuple(buf) not in self.brain:
            # ok, so we'll cheat - let's randomly choose a word from what we've got
            # and then generate a buffer from that.
            random_word = random.choice(input_words)
            # build up some candidate phrases
            candidates = [word_tuple for word_tuple in self.brain if random_word in word_tuple]
            buf = list(random.choice(candidates))

        output_words = buf[:]
        for i in xrange(max_words):
            try:
                next_word = random.choice(self.brain[tuple(buf)])
            except IndexError:
                continue
            if next_word == STOP_WORD:
                break
            output_words.append(next_word)
            buf.append(next_word)

            # now, if appropriate, trim buf down
            while len(buf) > self.chain_length:
                del buf[0]

        return ' '.join(output_words)

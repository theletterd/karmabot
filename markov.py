from collections import defaultdict
import cPickle as pickle
import random

STOP_WORD = "\n"

class Markov(object):

    def __init__(self, brain_file=None, training_file=None):
        self.brain = defaultdict(list)
        self.brain_file = brain_file
        self.training_file = training_file

        if self.training_file:
            self.retrain(self.training_file)
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
                line = line.strip()
                if line:
                    self.add_to_brain(line, 2)

    def add_to_brain(self, msg, chain_length=2):
        if not msg:
            return
        buf = [STOP_WORD] * chain_length
        for word in msg.split():
            self.brain[tuple(buf)].append(word)
            del buf[0]
            buf.append(word)
        self.brain[tuple(buf)].append(STOP_WORD)

    def generate_sentence(self, msg, chain_length=2, max_words=100):
        buf = msg.split()[:chain_length]
        if len(msg.split()) > chain_length:
            message = buf[:]
        else:
            message = []
            for i in xrange(chain_length):
                message.append(random.choice(self.brain[random.choice(self.brain.keys())]))
        for i in xrange(max_words):
            try:
                next_word = random.choice(self.brain[tuple(buf)])
            except IndexError:
                continue
            if next_word == STOP_WORD:
                break
            message.append(next_word)
            del buf[0]
            buf.append(next_word)
        return ' '.join(message)

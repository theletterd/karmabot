import random

class Greeter(object):

    def __init__(self, greetings_path):
        self.greetings = []
        with open(greetings_path, 'r') as f:
            for line in f:
                self.greetings.append(line)

    def greet(self, username):
        greeting = random.choice(self.greetings)
        if '%s' in greeting:
            return greeting % username


import random

class Greeter(object):

    def __init__(self, greetings_path, greeting_probability=0.25):
        self.greetings = []
        self.greeting_probability = greeting_probability
        with open(greetings_path, 'r') as f:
            for line in f:
                self.greetings.append(line)

    def greet(self, username):
        # only greet some percentage of the time
        if random.random() > self.greeting_probability:
            return

        greeting = random.choice(self.greetings)
        if '%s' in greeting:
            return greeting % username


import random

class EightBall(object):

    def __init__(self):
        self.answers = []
        with open('answers.txt', 'r') as f:
            for line in f:
                self.answers.append(line.strip())

    def get_answer(self):
        return random.choice(self.answers)

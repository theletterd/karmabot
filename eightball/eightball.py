import random

class EightBall(object):

    def __init__(self, answers_path):
        self.answers = []
        with open(answers_path, 'r') as f:
            for line in f:
                self.answers.append(line.strip())

    def get_answer(self):
        return random.choice(self.answers)

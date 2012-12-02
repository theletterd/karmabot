# -*- coding: utf-8 -*-

from collections import Counter
import random

import config

class WordBag(Counter):

    def weighted_random_word(self):
        # not sure why this should ever happen.
        if not self:
            return config.stop_word

        total_words = sum(self.values())
        random_word = random.randrange(total_words)
        count = 0
        for word, value in self.iteritems():
            if count >= random_word:
                return word
            count += value

        return config.stop_word

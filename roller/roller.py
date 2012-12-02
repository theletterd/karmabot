import random
import re

MAX_DIES = 1000
MAX_LIMIT = 1000
DEFAULT_DIES = 1
DEFAULT_LIMIT = 20
DD_RE = '\d*d?\d+'

class Roller(object):

    def roll(self, msg):
        match = re.match(DD_RE, msg.strip())
        first_match = match.group() if match else None

        num_dies = DEFAULT_DIES
        limit = DEFAULT_LIMIT

        if first_match:
            try:
                groups = first_match.strip().replace('d', ' ').split()
                if len(groups) != 2: # this is not defensive
                    groups = [DEFAULT_DIES] + groups

                num_dies, limit = int(groups[0]), int(groups[1])
            except Exception, e:
                print e

        # clamp the inputs to 1..x
        num_dies = max(1, min(MAX_DIES, num_dies))
        limit = max(1, min(MAX_LIMIT, limit))

        # no point rolling a d1
        if limit == 1:
            limit = DEFAULT_LIMIT

        die = '%dd%d' % (num_dies, limit)
        value = sum([random.randint(1, limit) for _ in xrange(num_dies)])
        return die, value


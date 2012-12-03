from collections import defaultdict
import time

class RateLimiter(object):

    def __init__(self, timeout=600, max_requests=5):
        self.timeout = timeout
        self.max_requests = max_requests
        self.requests_by_user = defaultdict(list)

    def add_request(self, username):
        now = int(time.time())
        self.requests_by_user[username].append(now)

    def is_rate_limited(self, username):
        self.cleanup_requests()
        return len(self.requests_by_user[username]) > self.max_requests

    def cleanup_requests(self):
        now = int(time.time())
        for username, timestamps in self.requests_by_user.iteritems():
            self.requests_by_user[username] = [timestamp for timestamp in timestamps if timestamp > (now - self.timeout)]


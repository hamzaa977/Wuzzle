from letters import Letter_state
from collections import defaultdict
class Wuzzle:
    max_word_length=5
    max_attempts=6

    def __init__(self, secret: str):
        self.secret: str=secret.upper()
        self.attempts=[]

    def is_solved(self):
        return bool(self.attempts) and self.attempts[-1]==self.secret

    def attempt(self, word: str):
        self.attempts.append(word.upper())

    def guess(self, word: str):
        word = word.upper()
        result = []
        secret_counts = defaultdict(int)

        for ch in self.secret:
            secret_counts[ch] += 1

        for i in range(self.max_word_length):
            result.append(Letter_state(word[i]))

        for i in range(self.max_word_length):
            if word[i] == self.secret[i]:
                result[i].in_position = True
                result[i].in_word = True
                secret_counts[word[i]] -= 1

        for i in range(self.max_word_length):
            if not result[i].in_position and secret_counts[word[i]] > 0:
                result[i].in_word = True
                secret_counts[word[i]] -= 1

        return result

    def remaining_attempts(self):
        return self.max_attempts - len(self.attempts)

    def can_attempt(self):
        return self.remaining_attempts() > 0 and not self.is_solved()
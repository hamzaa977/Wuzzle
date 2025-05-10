from collections import defaultdict

class AISolver:
    def __init__(self, word_list):
        self.all_words = word_list
        self.reset()

    def reset(self):
        self.possible_words = self.all_words.copy()
        self.guess_history = []

    def solve(self, secret_word):
        self.reset()
        solution = []

        for attempt in range(6):
            guess, explanation = self._select_guess_with_explanation()
            feedback = self._get_feedback(guess, secret_word)

            solution.append({
                'guess': guess,
                'remaining': len(self.possible_words),
                'feedback': feedback,
                'explanation': explanation
            })

            if guess == secret_word:
                break

            self._apply_constraints(guess, feedback)

        return solution

    def _select_guess_with_explanation(self):
        if not self.guess_history:
            return "CRANE", "First guess: Using optimal starting word 'CRANE'"

        if len(self.possible_words) > 200:
            return self._select_by_letter_frequency()

    
        return self._select_by_minimax()

    def _select_by_letter_frequency(self):
        letter_freq = defaultdict(int)
        for word in self.possible_words:
            for letter in set(word):
                letter_freq[letter] += 1

        def score(word):
            return sum(letter_freq[letter] for letter in set(word))

        best_word = max(self.possible_words, key=score)
        explanation = f"CSP-style: Picked word with most common letters among {len(self.possible_words)} words"
        return best_word, explanation

    def _select_by_minimax(self):
        best_guess = None
        min_max_remaining = float('inf')

        for guess in self.possible_words:
            feedback_buckets = defaultdict(int)

            for secret in self.possible_words:
                feedback = tuple(self._get_feedback(guess, secret))
                feedback_buckets[feedback] += 1

            worst_case = max(feedback_buckets.values())

            if worst_case < min_max_remaining:
                min_max_remaining = worst_case
                best_guess = guess

        explanation = f"Minimax: Picked word that minimizes worst-case remaining words to {min_max_remaining}"
        return best_guess, explanation

    def _get_feedback(self, guess, secret):
        feedback = ['absent'] * 5
        secret_letter_counts = defaultdict(int)

        for letter in secret:
            secret_letter_counts[letter] += 1

        for i in range(5):
            if guess[i] == secret[i]:
                feedback[i] = 'correct'
                secret_letter_counts[guess[i]] -= 1

        for i in range(5):
            if feedback[i] == 'correct':
                continue
            if secret_letter_counts[guess[i]] > 0:
                feedback[i] = 'present'
                secret_letter_counts[guess[i]] -= 1

        return feedback


    def _apply_constraints(self, guess, feedback):
        new_possible = []

        for word in self.possible_words:
            keep_word = True
            temp_word = list(word)

            for i in range(5):
                if feedback[i] == 'correct':
                    if word[i] != guess[i]:
                        keep_word = False
                        break
                    temp_word[i] = None

            if not keep_word:
                continue

            for i in range(5):
                if feedback[i] == 'present':
                    if guess[i] not in temp_word:
                        keep_word = False
                        break
                    temp_word[temp_word.index(guess[i])] = None
                elif feedback[i] == 'absent':
                    if guess[i] in temp_word:
                        keep_word = False
                        break

            if keep_word:
                new_possible.append(word)

        self.possible_words = new_possible
        self.guess_history.append(guess)
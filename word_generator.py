import random
from collections import Counter
import nltk
from nltk.corpus import words as nltk_words


nltk.download('words')
class WordGenerator:
    def __init__(self):
        self.valid_words = [w.upper() for w in nltk_words.words() if len(w) == 5 and w.isalpha()]
        
        self.position_probs = self._train_probability_model()

    def _train_probability_model(self):
        """Calculate how often each letter appears in each position"""
        position_probs = [{} for _ in range(5)]

        for pos in range(5):
            counter = Counter(word[pos] for word in self.valid_words)
            total_letters = sum(counter.values())
            
            position_probs[pos] = {char: count/total_letters 
                                    for char, count in counter.items()}
        return position_probs

    def generate_word(self):
        """Generate a word using letter probabilities"""
        for _ in range(100):
            letters = [
                random.choices(
                    list(self.position_probs[pos].keys()),
                    weights=list(self.position_probs[pos].values())
                )[0]
                for pos in range(5)
            ]
            candidate = ''.join(letters)
            
            if candidate in self.valid_words:
                return candidate
        
        return random.choice(self.valid_words)


class Letter_state:
    def __init__(self, character: str):
        self.character: str = character
        self.in_word: bool = False
        self.in_position: bool = False

    def __repr__(self):
        status = f"{self.character} - In Word: {self.in_word}, In Position: {self.in_position}"
        return status

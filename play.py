from logic import Wuzzle
from colorama import Fore

def main():
    wuzzle=Wuzzle("rayan")

    while wuzzle.can_attempt():
        x=input("GUESS: ")


        if len(x) != wuzzle.max_word_length:
            print(Fore.RED+
                  f"Word must be {wuzzle.max_word_length} letters." 
                  +Fore.RESET)
            continue
        
        wuzzle.attempt(x)
        result=wuzzle.guess(x)
        print(*result, sep="\n")

    if wuzzle.is_solved():
        print("Correct!")
    else:
        print(f"Incorrect! The word was {wuzzle.secret}")

main()
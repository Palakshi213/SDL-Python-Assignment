
'''
Author: Palakshi Rattan
Date: 26/9/26

Fizzbuzz is a mathematical game used to help kids learn their times tables. In
the game, a group of people will count up from 1, replacing any multiples of
3 by "Fizz" and any multiples of 5 by "Buzz". Numbers, such as 15,
which are multiples of both 3 and 5 are replaced by "FizzBuzz" in the
counting sequence


FizzBuzz.py includes:
    1. Default Setting:
    2. Custom Setting:
    3. Function to create a custom set of rules
    4. User input for the max number

'''

import argparse

def fizzbuzz(num_range, rules):
    """
    Replaces numbers in a list with replacement words

    Parameters:
    ------------
    num_range: range of numbers, used when the user tells us max number
    rules: Default, Extended, or Custom, this will include the custom word and replacement

    Returns:
   -------------
    output_list: list with replacement words
   """

    # Basic control flow for replacing numbers with words and creating list
    output_list = []
    for i in num_range:
       output = ""
       for factor, rep_word in rules:
           if i % factor == 0:
               output += rep_word
       if output:
         output_list.append(output)
       else:
           output_list.append(i)
    return output_list


def default():
    """
    Default FizzBuzz Game Rules
    """
    return [(3, "Fizz"), (5, "Buzz")]

def extended():
    """
    Extended FizzBuzz Game Rules
    """
    return [(3, "Fizz"), (5, "Buzz"), (7, "Fang"), (11, "Bang")]

def parseRules(input_str):
    """

    Parses rules to use for game from user input string

    Parameters:
    ------------
    input_str: user input for custom rules

    Returns:
    ------------
    rules: rules to use from user input
   """

    rules = []

    # Format the string
    for pair in input_str.split(","):
        factor_str, rep_word = pair.split(":")
        rules.append((int(factor_str.strip()), rep_word.strip()))
    return rules

def makeRules(num_str, words_str):
    """
    Creates the rules to use for game from user input string

    Parameters:
    ------------
    num_str: The numbers to replace as a string
    words_str: The words to replace as a string

    Returns:
    ------------
    A list of tuples which pairs words and numbers together

       """
    # "3,5" -> [3,5]
    # This is for creating the new rules for custom use

    numbers = [int(n.strip()) for n in num_str.split(",")]
    # "Fresh,Juice" -> ["Fresh", "Juice"]
    words = [w.strip() for w in words_str.split(",")]

    # Check for error in user input
    try:
        numbers = [int(n) for n in numbers]
    except ValueError:
        raise ValueError("numbers must be whole numbers, e.g. 4,6")

    # Ensure the number input by user is greater than 1
    if any(n < 1 for n in numbers):
        raise ValueError("numbers must be at least 1 ")
    if len(set(numbers)) != len(numbers):
        raise ValueError("each number can only be used once")
    if len(numbers) != len(words):
        raise ValueError(f"Input mismatched: {len(numbers)} number(s) given but "
                         f"{len(words)} word(s)")

    return list(zip(numbers, words))

def askUser(default_max, default_rules):
    """
    Asks the users for inputs and creates rules

    Parameters:
    ------------
    default_max: A default number to count up to when playing FizzBuzz
    default_rules: The rules for a default game

    Returns:
    ------------
    Either default, extended or custom rules set depending on user input
    """

    print("Starting FizzBuzz Game:")
    print(" Default Rules: Replace 3,5 respectively with 'Fizz' and 'Buzz' \n Extended Rules: Replace 3,5 respectively with 'Fizz' and 'Buzz' AND replace 7,11 respectively with 'Fang' and 'Bang' \n Custom Rules: Allow you to set your own rules \n " )
    print("If there is no input or an error, then Default Rules will be used (press Enter) \n")
    mode = input("Use default rules, extended version, or custom? [default/extended/custom] or [d/e/c] : ").strip().lower()

    # Check if the maximum number is a positive integer, defaults to a preset maximum in main()
    max_number = askPos(
        f"How high would you like to count? (leave blank for {default_max}): ",
        default_max,
    )

    # Allow typos by only checking from first letter of the input.
    # If the letter is something else, it will default to main
    # This could be more thorough with further looping to re-ask the user until a valid input is entered
    # Since they can just play the game again, I decided not to include this feature

    if mode.startswith("e"):
        return max_number, extended()
    if not mode.startswith("c"):
        return max_number, default_rules()

    # Custom rules: re-ask until valid; blank numbers falls back to defaults
    while True:
        print("Enter the numbers to replace separated by comma.")
        print("Example: 4,6   (leave blank to use the default rules)")
        numbers_str = input("Numbers: ").strip()
        if not numbers_str:
            print("No numbers entered, using default rules.")
            return max_number, default_rules()

        # User can create their own matching numbers and words rules.
        print("Enter the matching words to replace numbers, separated by commas.")
        print("Example: Fresh, Juice")
        words_str = input("Words: ").strip()

        # More checking for invalid character inputs
        try:
            return max_number, makeRules(numbers_str, words_str)
        except ValueError as e:
            print(f"Error: {e}. Please try again.\n")

def formatOutput(results):
    """ Prints the list of outputs with correct indexing """
    for i, value in enumerate(results):
        print(f"{i+1}. {value}")

def checkPos(num):
    """Argparse type: accept only whole numbers >= 1."""
    try:
        value = int(num)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{num!r} is not a whole number")
    if value < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1, got {value}")
    return value

def askPos(question, default_value):
    """
    Ask until the user gives a whole number >= 1. Blank returns the default.

    Parameters:
    ------------
    question: The user input question
    default_value: The value used if the user input is blank (if they press Enter)

    Returns:
    ------------
    value: Number entered by user, turned into an integer and verified

    """

    # This loop
    while True:
        raw = input(question).strip()
        if not raw:
            return default_value
        try:
            value = int(raw)
        except ValueError:
            print(f"{raw!r} is not a whole number. Please try again.")
            continue
        if value < 1:
            print("The number must be at least 1. Please try again.")
            continue
        return value

         
def main():
    """
    Main function: Deals with the user inputs, obtaining results for the game depending on the mode chosen
    and includes a loop if the player wants to keep playing again with different rules
    """

    # User interaction
    parser = argparse.ArgumentParser(description="Play FizzBuzz with default, extended, or custom rules.")

    # Check if user inputs for number is valid
    parser.add_argument("--max", type=checkPos, default=100, help="Max number to count to (default: 100)")
    parser.add_argument(
        "--mode",
        choices=["default", "extended", "custom"],
        default="custom",
        help="Pick rules directly, or go interactive and get asked (default: custom)",
    )
    args = parser.parse_args()

    # Loop to play the game depending on mode
    play_again = True
    while play_again:
        if args.mode == "default":
            max_number, rules = args.max, default()
        elif args.mode == "extended":
            max_number, rules = args.max, extended()
        else:
            max_number, rules = askUser(args.max, default)

        # Obtains game results, and formats the output
        results = fizzbuzz(range(1, max_number + 1), rules)
        formatOutput(results)

        # Asks user option to play again with different rules
        again = input("\nPlay again? [y/n]: ").strip().lower()
        play_again = again.startswith("y")

    print("Ending Fizzbuzz")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nFinished.")








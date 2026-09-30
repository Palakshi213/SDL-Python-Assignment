
'''
Palakshi Rattan
Date: 26/9/26
FizzBuzz.py includes:
    1. Default Setting:
    2. Custom Setting:
    3. Function to create a custom set of rules
    4. User input for the max number

'''

import argparse

def fizzbuzz(num_range, rules):
    '''
    numberRange: range of numbers, used when the user tells us max number
    rules: Default or Custom, this will include the custom word and replacement

    Variables:
    factor: number to replace input from user (divisor)
    repWord: replacement word input from user
    '''
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
    return [(3, "Fizz"), (5, "Buzz")]

def extended():
    return [(3, "Fizz"), (5, "Buzz"), (7, "Fang"), (11, "Bang")]

def parseRules(input_str):
    '''
    inputString: user input for custom rules
    factor_str: the number input by user as a string
    rep_word: replacement word input from user
    '''
    rules = []
    for pair in input_str.split(","):
        factor_str, rep_word = pair.split(":")
        rules.append((int(factor_str.strip()), rep_word.strip()))
    return rules

def makeRules(num_str, words_str):
    # "3,5" -> [3,5]
    # This is for creating the new rules for custom use

    numbers = [int(n.strip()) for n in num_str.split(",")]
    # "Fresh,Juice" -> ["Fresh", "Juice"]
    words = [w.strip() for w in words_str.split(",")]

    return list(zip(numbers, words))

def askUser(default_max, default_rules):
    print("Starting FizzBuzz Game:")

    mode = input("Use default rules, extended version, or custom? [default/extended/custom]: ").strip().lower()

    print(f"How high would you like to count? (leave blank for {default_max}): ")
    max_str = input("Max number: ").strip()
    max_number = int(max_str) if max_str else default_max

    if mode not in ("custom", "extended"):
        return max_number, default_rules()

    if mode == "extended":
        return max_number, extended()

    # Only "custom" reaches here — ask the remaining questions in order.
    print("Enter the numbers to replace separated by comma.")
    print("Example: 4,6")
    numbers_str = input("Numbers: ").strip()

    print("Enter the matching words to replace numbers, separated by commas.")
    print("Example: Banana, Apple")
    words_str = input("Words: ").strip()

    try:
        rules = makeRules(numbers_str, words_str)
    except ValueError as e:
        print(f"Error: {e}")
        print("Default rules.")
        rules = default_rules()

    return max_number, rules

def formatOutput(results):
    for i, value in enumerate(results):
        print(f"{i+1}. {value}")

         
def main():
    parser = argparse.ArgumentParser(description="Play FizzBuzz with default, extended, or custom rules.")
    parser.add_argument("--max", type=int, default=100, help="Max number to count to (default: 100)")
    parser.add_argument(
        "--mode",
        choices=["default", "extended", "custom"],
        default="custom",
        help="Pick rules directly, or go interactive and get asked (default: custom)",
    )
    args = parser.parse_args()

    play_again = True
    while play_again:
        if args.mode == "default":
            max_number, rules = args.max, default()
        elif args.mode == "extended":
            max_number, rules = args.max, extended()
        else:
            max_number, rules = askUser(args.max, default)

        results = fizzbuzz(range(1, max_number + 1), rules)
        formatOutput(results)

        again = input("\nPlay again? [y/n]: ").strip().lower()
        play_again = again.startswith("y")

    print("Ending Fizzbuzz!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nFinished.")








#!/usr/bin/env python 3
# powertracker.py
# Author: Martin CLOTUCHE

import random


def power_tracker():
    """
    Repeatedly generates a random integer between 1 & 20.
    At each iteration:
        - randomly choose to ^2 or ^3 number
        - store result
        - track largest & smallest result
        - check if current result divisible by previous one -> exit condition
            - Bonus: invalid if previous number is one or the same as previous
    """

    # Set initial numbers to None
    prev_nb = None
    max_nb_mult = None
    min_nb_mult = None

    i = 1
    exit_bool = False

    # Iterate while the current result is not divisible by the previous one
    while not exit_bool:
        # Generate random integer between 1 & 20
        cur_nb = random.randint(1, 20)

        # Randomly square or cube it
        square_or_cube_nb = random.randint(2, 3)
        cur_nb_mult = cur_nb**square_or_cube_nb

        # Track largest & smallest results
        if max_nb_mult is None or cur_nb_mult > max_nb_mult:
            max_nb_mult = cur_nb_mult
        if min_nb_mult is None or cur_nb_mult < min_nb_mult:
            min_nb_mult = cur_nb_mult

        # Check if current result divisible by previous one
        # BONUS 1: invalid if previous number is 1
        # BONUS 2: invalid if previous number is the same as the current one
        exit_bool = (
            (prev_nb is not None)
            and (prev_nb != 1)
            and (prev_nb != cur_nb)
            and (cur_nb % prev_nb == 0)
        )

        # Logging
        print(f"Loop {i}: {cur_nb}^{square_or_cube_nb} = {cur_nb_mult}")

        # Loop variable update
        i += 1
        prev_nb = cur_nb if not exit_bool else prev_nb

    # Final logging
    print(f"The largest result is {max_nb_mult}")
    print(f"The smallest result is {min_nb_mult}")
    print(f"{cur_nb} is divisible by {prev_nb}")
    print(f"We completed {i} loops")


if __name__ == "__main__":
    power_tracker()

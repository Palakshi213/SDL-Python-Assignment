# Introduction to Programming: FizzBuzz

## Pair Programming

Pair programming is a development strategy in which two people work together
at one screen to develop code. It usually involves two roles, the driver and
the navigator. The driver leads development with control of the keyboard and
mouse. The navigator gives advice, suggestions and corrections to the code
being developed on screen.

Both roles work together to solve the problem quickly. The two programmers
usually swap roles frequently. This allows both of them to share their ideas
and expertise in both the driver and navigator roles.


When developing the code for the task keep in mind what makes well structured
and well presented code. The grading rubric gives the expectations that your
code will be marked according to and so can be a helpful source for ideas of
what makes good code.


## The Task

Fizzbuzz is a mathematical game used to help kids learn their times tables. In
the game, a group of people will count up from 1, replacing any multiples of
3 by "Fizz" and any multiples of 5 by "Buzz". Numbers, such as 15,
which are multiples of both 3 and 5 are replaced by "FizzBuzz" in the
counting sequence.

Write a program called `fizzbuzz.py` that generates a sequence from 1 to 100
according to the rules of the FizzBuzz word game so that:
1. numbers which are multiples of 3 are replaced by "Fizz";
1. numbers which are multiples of 5 are replaced by "Buzz";
1. and numbers which are multiples of both 3 and 5 are printed as "FizzBuzz".

The output should look something like:
```
$ python fizzbuzz.py 
  1 : 1
  2 : 2
  3 : Fizz
  4 : 4
  5 : Buzz
  6 : Fizz
  7 : 7
  8 : 8
  9 : Fizz
 10 : Buzz
 11 : 11
 12 : Fizz
 13 : 13
 14 : 14
 15 : FizzBuzz
...
```

### Extensions

* The FizzBuzz game can be extended to multiples of other numbers as
  well. Extend FizzBuzz program so that (in addition to the previous rules):
    * numbers which are multiples of 7 are replaced by "Fang";
    * numbers which are multiples of 11 are replaced by "Bang";
    * and numbers with multiple factors show the correct combination of words.

* Can you extend the program to allow the user to provide an arbitrary list of
  factors and replacement words

* Can you extend the program to allow the user to specify the maximum number?


## Useful Python Skills

* Control flow statements
* Functions
* Command line arguments & `argparse`
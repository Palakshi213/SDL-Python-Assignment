# Introduction to Programming: Power Tracker

## The Task

Write a program called `powertracker.py` that repeatedly generates a random integer between 1 and 20. This should be done with a `while`-loop. At each iteration, your code should:
1. randomly choose whether to square or cube this number;
1. store the squared or cubed result;
1. track the largest and smallest results;
1. and check if the current result is divisible by the previous result.

Your program should exit if the current result is divisible by the previous result. Once your program has ended, you should print the largest and smallest of the squared or cubed numbers, state which two numbers caused the loop to break, and inform the user of the total number of iterations that the program completed. 

As an example, your output may look like:

```
$ python powertracker.py 
  Loop 1: 9^2 = 81
  Loop 2: 17^3 = 4913
  Loop 3: 3^3 = 27
  Loop 4: 4^2 = 16
  Loop 5: 4^3 = 64
  The largest result is 4913
  The smallest result is 16
  64 is divisible by 16.
  We completed 5 loops.
```

### Extensions

If you are feeling adventurous, you can include other conditional controls; for example, every number is divisible by 1, so you could choose to end the loop if the current number is divisible by the previous number **and** the previous number is *not* 1. This is, of course, optional.

## Useful Python Skills

* Control flow statements
* `while`-loop control

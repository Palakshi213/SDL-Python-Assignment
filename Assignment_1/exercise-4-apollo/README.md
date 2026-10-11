# Exercise 2: Blast Off!

The Apollo 10 mission was the fourth crewed mission in the Apollo program and
acted as a dress rehearsal for the first Moon landing by Apollo 11 two months
later.

The as-505-ascent-phase-data.txt document contains data from the Apollo 10
launch aboard a Saturn V rocket on May 18 1969, covering its ascent from launch
upto its parking orbit in Low Earth Orbit.


## The Problem

Write a Python script containing a pipeline which: 
* reads the data from the text file;
* converts the values from strings to integers;
* stores the data from the table columns as arrays within a dictionary;  
* and uses the dictionary to make plots with the data. 

You should plot:

1. all 11 parameters as functions of time. Your code should be able to make
  these plots using the information in the table (in particular, you should be
  able to get the field names from the table header).
2. the Apollo 10 rocket's groundtrack, given by its longitude (LONG) and
  latitude (GC LAT). For extra kudos, display this on a map of the
  Earth. For even more kudos, change the colour of the line to show the
  rocket's altitude.


## Notes:

* Start by thinking about what goes into and comes out of your pipeline: your
  input will be the name of the .txt file containing the data. The output will
  be a dictionary with the data field names (TIME, GC DIST, etc.) as keys, and
  the data from the table columns as its values. Write these down on a piece of
  paper, and then write out the steps that you need to go through to get from
  input to output.
* The data in the text file contains comments which give details about the
  ascent phase of the launch vehicle; you will need to ignore these when you
  extract the data. You will just want the table itself.
* Take into account the whitespace while the data is in string format before
  converting to integer format.
* Matplotlib is a popular plotting library, which you can use to make plots in
  this task.
* Make sure your plots look nice, with gridlines, appropriate axes, and axis
  labels. Your axis labels will need units, which you can extract from the data
  file.
* We have provided you with two map images which you might want to use for the
  second problem. These are given in geographic projection, so latitude and
  longitude are equally spaced on the y and x axes. The full image covers the
  whole world, while the cropped image covers only longitudes from 120W to 30W,
  and latitudes from 15N to 60N. You can plot an image on a graph in Matplotlib
  using `im = plt.imread(filename)` to read in the image, and `ax.imshow(im,
  extent=[left, right, bottom, top])` to plot it. Also, make sure you fix the
  chart aspect ratio with `ax.set_aspect('equal')`.


## Useful Python skills

* Extracting data from a file
* Converting between strings and numbers
* Choosing data structures
* Plotting data with Matplotlib

#!/home/devon/anaconda2/bin/python

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import copy
import caco
import time
import sys

# set up color printing to the terminal for easier readability!
action_colors = ["\033[0;32m", "\033[1;33m", "\033[1;31m", "\033[1;36m"]
def print_color_no_return(str, color):
    sys.stdout.write(color)
    print str,
    sys.stdout.write("\033[0;0m")

# a new infinite shoe
shoe = caco.Shoe(numdecks=-1)
tstart = time.time()

# first, hard hands 
print "\n-- Hard hands --"
print "    Dealer:\t",
for dealer_card in caco.allCards:
    print ("%d\t\t\t"%dealer_card),
print "\nMe:",
for my_points in xrange(20, 4, -1):
    print ("\n%d\t\t" % my_points), 
    for dealer_card in caco.allCards:

        # shuffle and deal
        shoe.shuffle()
        dealer_hand = caco.Hand()
        dealer_hand.addCard(dealer_card)

        # set the player hand artificially since there
        # are many ways to make these hands
        my_hand = caco.Hand()
        my_hand.points = my_points
        my_hand.numcards = 2
        my_hand.ispair = 0
        
        # get the best possible action and its expected value
        action, exp =  caco.getOptimalMove(shoe, dealer_hand, my_hand)
        print_color_no_return("%s (%+.5f)\t" % (caco.actionLabels[action], exp),
                action_colors[action])
print 

# soft hands 
print "\n-- Soft hands --"
print "    Dealer:\t",
for dealer_card in caco.allCards:
    print ("%d\t\t\t"%dealer_card),
print "\nMe:",
for my_points in xrange(10, 1, -1):
    print ("\nA,%d\t\t" % my_points), 
    for dealer_card in caco.allCards:

        # shuffle the shoe and deal the hand
        shoe.shuffle()
        dealer_hand = caco.Hand()
        my_hand = caco.Hand()
        dealer_hand.addCard(dealer_card)
        my_hand.addCard(11)
        my_hand.addCard(my_points)

        # get the best possible action and its expected value
        action, exp =  caco.getOptimalMove(shoe, dealer_hand, my_hand)
        print_color_no_return("%s (%+.5f)\t" % (caco.actionLabels[action], exp),
                action_colors[action])
print 

# pairs 
print "\n-- Pairs --"
print "    Dealer:\t",
for dealer_card in caco.allCards:
    print ("%d\t\t\t"%dealer_card),
print "\nMe:",
for my_points in xrange(11, 1, -1):
    print ("\n%s,%s\t\t" % (caco.cardLabels[my_points], caco.cardLabels[my_points])), 
    for dealer_card in caco.allCards:

        # shuffle the shoe and deal the hand
        shoe.shuffle()
        dealer_hand = caco.Hand()
        my_hand = caco.Hand()
        dealer_hand.addCard(dealer_card)
        my_hand.addCard(my_points)
        my_hand.addCard(my_points)

        # get the best possible action and its expected value
        action, exp =  caco.getOptimalMove(shoe, dealer_hand, my_hand)
        print_color_no_return("%s (%+.5f)\t" % (caco.actionLabels[action], exp),
                action_colors[action])
print 
print 

# time it
tstop = time.time()
print "elapsed time = %f" % (tstop-tstart)
print 

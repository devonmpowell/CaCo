#!/home/devon/anaconda2/bin/python

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import copy
import caco
import time

# a new infinite shoe
shoe = caco.Shoe(numdecks = -1)
print shoe


# iterate over all possible starting hands

tstart = time.time()

# first, hard hands 
print "\n-- Hard hands --"
print "\tDealer:\t",
for dealer_card in caco.allCards:
    print ("%d\t\t\t"%dealer_card),
print "\nMe:",
for my_points in xrange(20, 5, -1):
    print ("\n%d\t\t" % my_points), 
    for dealer_card in caco.allCards:
        dealer_hand = caco.Hand()
        dealer_hand.addCard(dealer_card)
        my_hand = caco.Hand()
        my_hand.points = my_points
        my_hand.numcards = 2
        
        action, exp =  caco.getOptimalMove(shoe, dealer_hand, my_hand)
         
        print ("%s (%f)\t\t" % (caco.actionLabels[action], exp)),
print ""

# soft hands 
print "\n-- Soft hands --"
print "\tDealer:\t",
for dealer_card in caco.allCards:
    print ("%d\t\t\t"%dealer_card),
print "\nMe:",
for my_points in xrange(20, 13, -1):
    print ("\n%d\t\t" % my_points), 
    for dealer_card in caco.allCards:
        dealer_hand = caco.Hand()
        dealer_hand.addCard(dealer_card)
        my_hand = caco.Hand()
        my_hand.points = my_points
        my_hand.softness = 1
        my_hand.numcards = 2
        
        action, exp =  caco.getOptimalMove(shoe, dealer_hand, my_hand)
         
        print ("%s (%f)\t\t" % (caco.actionLabels[action], exp)),
print ""

# pairs 
print "\n-- Pairs --"
print "\tDealer:\t",
for dealer_card in caco.allCards:
    print ("%d\t\t\t"%dealer_card),
print "\nMe:",
for my_points in xrange(22, 4, -2):
    print ("\n%d\t\t" % my_points), 
    for dealer_card in caco.allCards:
        dealer_hand = caco.Hand()
        dealer_hand.addCard(dealer_card)
        my_hand = caco.Hand()
        my_hand.points = my_points
        my_hand.softness = 2*(my_points == 22)
        my_hand.numcards = 2
        my_hand.ispair = 1
        
        action, exp =  caco.getOptimalMove(shoe, dealer_hand, my_hand)
         
        print ("%s (%f)\t\t" % (caco.actionLabels[action], exp)),
print ""


tstop = time.time()

print "elapsed time = %f" % (tstop-tstart)

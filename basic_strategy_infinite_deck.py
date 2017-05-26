#!/home/devon/anaconda2/bin/python

import numpy as np
import matplotlib
import matplotlib.pyplot as plt 
import matplotlib.ticker as plticker 
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

best_action = np.empty((10, 35), dtype=np.int32)
all_exp = np.empty((10, 35, 6), dtype=np.float64)

row = 0

# first, hard hands 
print "\n-- Hard hands --"
print "    Dealer:\t",
for dealer_card in caco.allCards:
    print ("%d\t\t\t"%dealer_card),
print "\nMe:",
for my_points in xrange(20, 4, -1):
    print ("\n%d: %d\t\t" % (row, my_points)), 
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
        print_color_no_return("%s (%+.5f)\t" % (caco.actionLabels[action], exp[action]),
                action_colors[action])
        ind = caco.getChartIndFromCards(my_hand, dealer_hand)
        best_action[ind] = action 
        all_exp[ind] = exp 

    row += 1
print 

# soft hands 
print "\n-- Soft hands --"
print "    Dealer:\t",
for dealer_card in caco.allCards:
    print ("%d\t\t\t"%dealer_card),
print "\nMe:",
for my_points in xrange(10, 1, -1):
    #print ("\n%d: A,%d\t\t" % (row, my_points)), 
    print ("\n%d: %d\t\t" % (row, my_points)), 
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
        print_color_no_return("%s (%+.5f)\t" % (caco.actionLabels[action], exp[action]),
                action_colors[action])
        ind = caco.getChartIndFromCards(my_hand, dealer_hand)
        best_action[ind] = action 
        all_exp[ind] = exp 
    row += 1
print 

# pairs 
print "\n-- Pairs --"
print "    Dealer:\t",
for dealer_card in caco.allCards:
    print ("%d\t\t\t"%dealer_card),
print "\nMe:",
for my_points in xrange(11, 1, -1):
    #print ("\n%s,%s\t\t" % (caco.cardLabels[my_points], caco.cardLabels[my_points])), 
    print ("\n%d: %d\t\t" % (row, 2*my_points)), 
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
        print_color_no_return("%s (%+.5f)\t" % (caco.actionLabels[action], exp[action]),
                action_colors[action])
        ind = caco.getChartIndFromCards(my_hand, dealer_hand)
        best_action[ind] = action 
        all_exp[ind] = exp 
    row += 1
print 
print 

# time it
tstop = time.time()
print "elapsed time = %f" % (tstop-tstart)
print 

fig, ax = caco.plotChart(best_action, title='Optimal strategy, infinite shoe', textarr =
        all_exp, textfmt =(lambda exp, act: '%s'%caco.actionLabels[act]))
fig.savefig('img/basic_strategy_infinite_deck.png', bbox_inches = 'tight', pad_inches = 0)
best_action.tofile('tables/basic_strategy_infinite_deck_actions.np')
all_exp.tofile('tables/basic_strategy_infinite_deck_exp.np')


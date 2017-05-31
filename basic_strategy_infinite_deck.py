#!/home/devon/anaconda2/bin/python

import numpy as np
import matplotlib
import matplotlib.pyplot as plt 
import matplotlib.ticker as plticker 
import copy
import coca
import time
import sys

# set up color printing to the terminal for easier readability!
action_colors = ["\033[0;32m", "\033[1;33m", "\033[1;31m", "\033[1;36m", "\033[1;37m"]
def print_color_no_return(str, color):
    sys.stdout.write(color)
    print str,
    sys.stdout.write("\033[0;0m")

# a new infinite shoe
shoe = coca.Shoe(numdecks=-1)
rules = coca.Rules(allowed_actions=[1,1,1,1,1,0], max_split_depth=2, double_after_split=1,
        dealer_hits_soft_17=0, can_hit_split_aces=0, errtol=1.0e-5)
strategy = coca.Strategy(type='optimal_infinite_deck')
#strategy = coca.Strategy(type='optimal')
best_action = np.empty((10, 34), dtype=np.int32)
all_exp = np.empty((10, 34, 6), dtype=np.float64)
tstart = time.time()

# first, hard hands 
print "\n-- Hard hands --"
print "    Dealer:\t",
for dealer_card in coca.allCards:
    print ("%d\t\t\t"%dealer_card),
print "\nMe:",
for my_points in xrange(19, 4, -1):
    print ("\n %d\t\t" % (my_points)), 
    for dealer_card in coca.allCards:

        # shuffle and deal
        shoe.shuffle()
        dealer_hand = coca.Hand()
        dealer_hand.addCard(dealer_card)

        # set the player hand artificially since there
        # are many ways to make these hands
        my_hand = coca.Hand()
        my_hand.points = my_points
        my_hand.numcards = 2
        my_hand.depth = 2
        my_hand.ispair = 0
        
        # get the best possible action and its expected value
        action, exp =  coca.getAction(shoe, dealer_hand, my_hand, rules=rules, strategy=strategy)
        #print exp
        print_color_no_return("%s (%+.5f)\t" % (coca.actionLabels[action], exp[action]),
                action_colors[action])
        ind = coca.getChartIndFromCards(my_hand, dealer_hand)
        best_action[ind] = action 
        all_exp[ind] = exp 
print 

# soft hands 
print "\n-- Soft hands --"
print "    Dealer:\t",
for dealer_card in coca.allCards:
    print ("%d\t\t\t"%dealer_card),
print "\nMe:",
for my_points in xrange(10, 1, -1):
    print ("\n %d\t\t" % (my_points)), 
    for dealer_card in coca.allCards:

        # shuffle the shoe and deal the hand
        shoe.shuffle()
        dealer_hand = coca.Hand()
        my_hand = coca.Hand()
        dealer_hand.addCard(dealer_card)
        my_hand.addCard(11)
        my_hand.addCard(my_points)

        # get the best possible action and its expected value
        action, exp =  coca.getAction(shoe, dealer_hand, my_hand, rules=rules, strategy=strategy)
        print_color_no_return("%s (%+.5f)\t" % (coca.actionLabels[action], exp[action]),
                action_colors[action])
        ind = coca.getChartIndFromCards(my_hand, dealer_hand)
        best_action[ind] = action 
        all_exp[ind] = exp 
print 

# pairs 
print "\n-- Pairs --"
print "    Dealer:\t",
for dealer_card in coca.allCards:
    print ("%d\t\t\t"%dealer_card),
print "\nMe:",
for my_points in xrange(11, 1, -1):
    #print ("\n%s,%s\t\t" % (coca.cardLabels[my_points], coca.cardLabels[my_points])), 
    print ("\n %d\t\t" % (2*my_points)), 
    for dealer_card in coca.allCards:

        # shuffle the shoe and deal the hand
        shoe.shuffle()
        dealer_hand = coca.Hand()
        my_hand = coca.Hand()
        dealer_hand.addCard(dealer_card)
        my_hand.addCard(my_points)
        my_hand.addCard(my_points)

        # get the best possible action and its expected value
        action, exp =  coca.getAction(shoe, dealer_hand, my_hand, rules=rules, strategy=strategy)
        print_color_no_return("%s (%+.5f)\t" % (coca.actionLabels[action], exp[action]),
                action_colors[action])
        ind = coca.getChartIndFromCards(my_hand, dealer_hand)
        best_action[ind] = action 
        all_exp[ind] = exp 
print 
print 

# time it
tstop = time.time()
print "elapsed time = %f" % (tstop-tstart)
print 

fig, ax = coca.plotChart(best_action, title='Optimal strategy, infinite shoe', textarr =
        all_exp, textfmt =(lambda exp, act: '%s'%coca.actionLabels[act]))

# WARNING: uncommenting this will overwrite the default files!
#fig.savefig('img/basic_strategy_infinite_deck.png', bbox_inches = 'tight', pad_inches = 0)
#best_action.tofile('tables/basic_strategy_infinite_deck_actions.np')
#all_exp.tofile('tables/basic_strategy_infinite_deck_exp.np')



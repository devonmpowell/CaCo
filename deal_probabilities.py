#!/home/devon/anaconda2/bin/python

import numpy as np
import matplotlib
import matplotlib.pyplot as plt 
import matplotlib.ticker as plticker 
import copy
import coca
import time
import sys

# a new infinite shoe
shoe = coca.Shoe(numdecks=-1)
dealprob = np.zeros((10, 34), dtype=np.float64)
weightedexp = np.zeros((10, 34), dtype=np.float64)

best_action = np.fromfile('tables/basic_strategy_infinite_deck_actions.np', 
         dtype=np.int32).reshape((10,34))
all_exp = np.fromfile('tables/basic_strategy_infinite_deck_exp.np',
         dtype=np.float64).reshape((10,34,6))
best_exp = np.array([[all_exp[d,m,best_action[d,m]] for m in xrange(34)] for d in xrange(10)])

print '[',
for a in best_action.flatten():
    print '%d,'%a,
print ']'

# pairs 
tstart = time.time()
for d0 in coca.allCards: 
    for m0 in coca.allCards: 
        for m1 in coca.allCards: 

            # shuffle the shoe and deal the hand
            shoe.shuffle()
            dealer_hand = coca.Hand()
            my_hand = coca.Hand()

            # just to test a skewed deck
            #for c in xrange(2,6):
                #delta = shoe.num[c]/2
                #shoe.num[c] -= delta
                #shoe.total -= delta

            prb = 1.0;
            prb *= coca.dealCardToHand(shoe, dealer_hand, card=d0, way='choose')
            prb *= coca.dealCardToHand(shoe, my_hand, card=m0, way='choose')
            prb *= coca.dealCardToHand(shoe, my_hand, card=m1, way='choose')
            ind = coca.getChartIndFromCards(my_hand, dealer_hand)
            #coca.getAction(shoe, my_hand, dealer_hand, )
            ind = coca.getChartIndFromCards(my_hand, dealer_hand)
            dealprob[ind] += prb 
            weightedexp[ind] += prb*best_exp[ind]

# time it
tstop = time.time()
print "elapsed time = %f" % (tstop-tstart)
print 'Total error in deal prob = %.5e' % np.abs(1.0-np.sum(dealprob))

# also save the unweighted exp 
vrange = (min(-np.abs(np.min(best_exp)), -np.abs(np.max(best_exp))), 
        max(np.abs(np.min(best_exp)),np.abs(np.max(best_exp))))
fig, ax = coca.plotChart(best_exp, 
        title='Expected win/loss given perfect play,\ninfinite shoe (total = %+.3f pct)' %
        (100.0*np.sum(weightedexp)), 
        textarr=best_exp, textfmt=(lambda x, a: '%+.4f'%x), cmap=plt.cm.RdYlGn, vrange=vrange)
fig.savefig('img/hand_expectations.png', bbox_inches = 'tight', pad_inches = 0)


fig, ax = coca.plotChart(dealprob, title='Deal probability, infinite shoe', 
        textarr=dealprob,
        textfmt=(lambda x, a: '%.3e'%x), cmap=plt.cm.PuBuGn_r)
fig.savefig('img/deal_probabilities.png', bbox_inches = 'tight', pad_inches = 0)




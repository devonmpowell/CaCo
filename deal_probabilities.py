#!/home/devon/anaconda2/bin/python

import numpy as np
import matplotlib
import matplotlib.pyplot as plt 
import matplotlib.ticker as plticker 
import copy
import caco
import time
import sys

# a new infinite shoe
shoe = caco.Shoe(numdecks=-1)
tstart = time.time()

dealprob = np.zeros((10, 35), dtype=np.float64)
weightedexp = np.zeros((10, 35), dtype=np.float64)

best_action = np.fromfile('tables/basic_strategy_infinite_deck_actions.np', dtype=np.int32).reshape((10,35))
all_exp = np.fromfile('tables/basic_strategy_infinite_deck_exp.np', dtype=np.float64).reshape((10,35,6))
best_exp = np.array([[all_exp[d,m,best_action[d,m]] for m in xrange(35)] for d in xrange(10)])

# pairs 
for d0 in caco.allCards: 
    for m0 in caco.allCards: 
        for m1 in caco.allCards: 

            # shuffle the shoe and deal the hand
            prb = 1.0;
            shoe.shuffle()
            dealer_hand = caco.Hand()
            prb *= caco.dealCardToHand(shoe, dealer_hand, card=d0, way='choose')
            my_hand = caco.Hand()
            prb *= caco.dealCardToHand(shoe, my_hand, card=m0, way='choose')
            prb *= caco.dealCardToHand(shoe, my_hand, card=m1, way='choose')
            ind = caco.getChartIndFromCards(my_hand, dealer_hand)
            dealprob[ind] += prb 
            weightedexp[ind] += prb*best_exp[ind]
            #print 'Player', my_hand, "vs. Dealer", dealer_hand, " prob =", prb
# time it
tstop = time.time()
print "elapsed time = %f" % (tstop-tstart)
#print 'Total error in deal prob = %.5e' % np.abs(1.0-np.sum(dealprob))
fig, ax = caco.plotChart(dealprob, title='Deal probability, infinite shoe', textarr=dealprob,
        textfmt=(lambda x, a: '%.1e'%x), cmap=plt.cm.RdBu_r)
fig.savefig('img/deal_probabilities.png', bbox_inches = 'tight', pad_inches = 0)


# make the color scale symmetric about zero
vrange = (np.min(-np.abs(np.min(weightedexp)), -np.abs(np.max(weightedexp))), 
        np.max(np.abs(np.min(weightedexp)),np.abs(np.max(weightedexp))))
fig, ax = caco.plotChart(weightedexp, 
        title='Expected win/loss weighted by deal prob. (total = %+.1e), infinite shoe' %
        np.sum(weightedexp), 
        textarr=weightedexp, textfmt=(lambda x, a: '%.1e'%x), cmap=plt.cm.RdYlGn, vrange=vrange)
fig.savefig('img/deal_weighted_hand_expectations.png', bbox_inches = 'tight', pad_inches = 0)

# also save the unweighted exp 
vrange = (min(-np.abs(np.min(best_exp)), -np.abs(np.max(best_exp))), 
        max(np.abs(np.min(best_exp)),np.abs(np.max(best_exp))))
fig, ax = caco.plotChart(best_exp, 
        title='Expected win/loss given perfect play, infinite shoe', 
        textarr=best_exp, textfmt=(lambda x, a: '%.1e'%x), cmap=plt.cm.RdYlGn, vrange=vrange)
fig.savefig('img/hand_expectations.png', bbox_inches = 'tight', pad_inches = 0)








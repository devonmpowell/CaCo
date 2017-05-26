import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.collections import PolyCollection
from matplotlib import colors
import ctypes
from ctypes import *
import warnings
import os 
import time
import inspect 
import itertools
from scipy.stats import norm

# nice plot styling
matplotlib.rcParams['text.usetex'] = True
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['font.serif'] = 'computer modern roman'

# load the underlying C shared library
_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
_caco = ctypes.CDLL('%s/blackjack.so'%_path)
_caco.deal_card_to_hand_choose.restype = c_double 
_caco.expected_value.restype = c_double 

# nice helpers
allCards = [2,3,4,5,6,7,8,9,10,11]
cardLabels = ["", "", "2","3","4","5","6","7","8","9","10","A"]
actionLabels = ["Stand ", "Hit   ", "Double", "Split ", "Surrender", "Insurance"]

class Hand(Structure):

    # c struct fields 
    _fields_ = [("points", c_int), ("softness", c_int), ("numcards", c_int), ("ispair", c_int)] 

    def __init__(self):
        self.reset()

    def reset(self):
        _caco.init_hand(byref(self))

    def addCard(self, card):
        if card < 2 or card > 11:
            raise ValueError("Invalid card value.")
        _caco.add_card_to_hand(byref(self), c_int(card))

    def __str__(self):
        if self.ispair:
            return 'Pair of %ds' % (self.points/2)
        elif self.points == 21 and self.numcards == 2:
            return 'Blackjack'
        elif self.points > 21:
            return 'Bust'
        elif self.softness > 0:
            return 'Soft %d' % self.points
        else:
            return 'Hard %d' % self.points

class Shoe(Structure):

    # c struct fields 
    _fields_ = [("num", 12*c_int), ("total", c_int), ("numdecks", c_int),] 

    def __init__(self, numdecks = -1):

        # numdecks < 0 indicates an infinite deck
        self.numdecks = numdecks
        self.shuffle()

    def shuffle(self):
        _caco.init_shoe(byref(self), c_int(self.numdecks))

    def __str__(self):
        if self.numdecks < 0:
            dstr = "Infinite"
        else:
            dstr = '%d-deck' % self.numdecks
        return "%s Shoe with current distribution [%d %d %d %d %d %d %d %d %d %d]" % (dstr, 
                    self.num[2], self.num[3], self.num[4], self.num[5], self.num[6], self.num[7],
                    self.num[8], self.num[9], self.num[10], self.num[11])


# deals the specified card from the shoe to the hand
# returns the probability of this deal occuring given the
# state of the shoe. If the card is not in the shoe, 
# the hand and shoe are untouched and we return 0.
def dealCardToHand(shoe, hand, card = 11, way = 'random'):
    if card < 2 or card > 11:
        raise ValueError("Invalid card value.")
    if way == 'choose':
        prb = _caco.deal_card_to_hand_choose(byref(shoe), byref(hand), c_int(card))
    elif way == 'random':
        prb = _caco.deal_card_to_hand_random(byref(shoe), byref(hand), c_int(card))
    return prb


# returns the optimal move based on the desired strategy 
def getOptimalMove(shoe, dealer_hand, my_hand, strategy = 'omniscient'):


    if strategy == 'omniscient':
        bet = c_double(1.0)
        allowed_moves = np.array([1,1,1,2,0,0], dtype=np.int32) 
        exp_values = np.array([0.0,0.0,0.0,0.0,0.0,0.0], dtype=np.float64) 
        action = c_int(0)

        _caco.expected_value(bet, my_hand, dealer_hand, shoe,
                allowed_moves.ctypes.data_as(POINTER(c_int)), byref(action),
                exp_values.ctypes.data_as(POINTER(c_double)), c_int(0))

        return action.value, exp_values



# returns the optimal move based on the desired strategy 
def getChartIndFromCards(my_hand, dealer_hand):

    my_ind = c_int(0); 
    dealer_ind = c_int(0); 

    _caco.chart_ind_from_hands(my_hand, dealer_hand, byref(my_ind), byref(dealer_ind));

    return (dealer_ind.value, my_ind.value) 


def plotChart(ar, title=None, cmap=colors.ListedColormap(['green','yellow','red','cyan']),
        vrange=None, grid=True, textarr=None, textfmt=None):

    # set up the axes 
    fig, ax = plt.subplots(3, 1, figsize=(8, 20), gridspec_kw={'height_ratios': [16./35.,9./35.,10./35.]},sharex=True)
    fig.subplots_adjust(hspace=0.02)
    if title is not None:
        ax[0].set_title(title, fontsize=18) 
    dticks = np.linspace(2, 10, 11)
    for axx in ax:
        if grid:
            axx.grid(ls='-', lw=0.3)
        axx.set_xticks(dticks)
        axx.set_xticks(dticks+0.4, minor=True)
        axx.set_xticklabels('')
        axx.set_yticklabels('')
    hardticks = np.linspace(5, 21, 16)
    ax[0].set_yticks(hardticks)
    ax[0].set_yticks(hardticks+0.4, minor=True)
    ax[0].set_yticklabels(["%d"%i for i in range(5,22)], minor=True)
    ax[0].set_ylabel("Hard hands")
    softticks = np.linspace(13, 21, 10)
    ax[1].set_yticks(softticks)
    ax[1].set_yticks(softticks+0.4, minor=True)
    ax[1].set_yticklabels(["A,%d"%(i-11) for i in range(13,22)], minor=True)
    ax[1].set_ylabel("Soft hands")
    pairticks = np.linspace(2, 11, 11)
    ax[2].set_yticks(pairticks)
    ax[2].set_yticks(pairticks+0.4, minor=True)
    ax[2].set_yticklabels(["%s,%s"%(cardLabels[i], cardLabels[i]) for i in xrange(2,12)], minor=True)
    ax[2].set_ylabel("Pairs")
    ax[2].set_xticklabels(["%s"%(cardLabels[i]) for i in xrange(2,12)], minor=True)
    ax[2].set_xlabel("Dealer up")

    # plot it
    if vrange is None:
        vrange = (np.min(ar), np.max(ar))
    imargs = {'interpolation': 'nearest', 'aspect': 'auto', 'cmap': cmap, 'vmin': vrange[0],
            'vmax': vrange[1]}
    hard_actions = ar[:,:16]
    imargs['extent'] = [2,10,5,22] 
    ax[0].imshow(hard_actions.T, **imargs)
    soft_actions = ar[:,16:25]
    imargs['extent'] = [2,10,13,21] 
    ax[1].imshow(soft_actions.T, **imargs)
    split_actions = ar[:,25:35]
    imargs['extent'] = [2,10,2,11] 
    ax[2].imshow(split_actions.T, **imargs)
    
    # draw text if asked for
    if textarr is not None and textfmt is not None:
        hard_text = textarr[:,:16]
        for d in xrange(0, 10):
            for m in xrange(0, 16):
                ax[0].text(dticks[d]+0.4, (26-hardticks[m])+0.4, textfmt(hard_text[d,m],
                    hard_actions[d,m]), va='center', ha='center')
        soft_text = textarr[:,16:25]
        for d in xrange(0, 10):
            for m in xrange(0, 9):
                ax[1].text(dticks[d]+0.4, (33-softticks[m])+0.4, textfmt(soft_text[d,m],
                    soft_actions[d,m]), va='center', ha='center')
        pair_text = textarr[:,25:35]
        for d in xrange(0, 10):
            for m in xrange(0, 10):
                ax[2].text(dticks[d]+0.4, (12-pairticks[m])+0.4, textfmt(pair_text[d,m],
                    split_actions[d,m]), va='center', ha='center')
    
    plt.show()
    return fig, ax

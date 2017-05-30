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
_caco = ctypes.CDLL('%s/cocalib.so'%_path)
_caco.deal_card_to_hand_choose.restype = c_double 
_caco.expected_value.restype = c_double 

# nice helpers
allCards = [2,3,4,5,6,7,8,9,10,11]
cardLabels = ["", "", "2","3","4","5","6","7","8","9","10","A"]
actionLabels = ["Stand ", "Hit   ", "Double", "Split ", "Surrender", "Insurance", ""]

# TODO: define different sets of default rules?
vegasRules = {}

class Hand(Structure):

    # c struct fields 
    _fields_ = [("points", c_int), ("softness", c_int), ("numcards", c_int), ("depth", c_int), ("ispair", c_int)] 

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

class Rules(Structure):

    # c struct fields 
    _fields_ = [("allowed", 6*c_int), ("max_split_depth", c_int), ("double_after_split", c_int),
            ("dealer_hits_soft_17", c_int), ("can_hit_split_aces", c_int), ("errtol", c_double)]

    def __init__(self, allowed_actions=[1,1,1,1,1,0], max_split_depth=2, double_after_split=1,
        dealer_hits_soft_17=0, can_hit_split_aces=0, errtol=1.0e-10):

        for i, act in enumerate(allowed_actions):
            self.allowed[i] = act
        self.max_split_depth = max_split_depth
        self.double_after_split = double_after_split
        self.dealer_hits_soft_17 = dealer_hits_soft_17
        self.can_hit_split_aces = can_hit_split_aces
        self.errtol = errtol

    def __str__(self):
        mystr = 'Rules:\n'
        #mystr += ' allowed_moves = '
        return mystr


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
def getOptimalMove(shoe, dealer_hand, my_hand, rules=Rules(), strategy = 'optimal'):

    if strategy == 'optimal':
        exp_values = np.array([0.0,0.0,0.0,0.0,0.0,0.0], dtype=np.float64) 
        action = c_int(0)
        _caco.simulate_unit_bet(my_hand, dealer_hand, shoe, rules, byref(action),
                exp_values.ctypes.data_as(POINTER(c_double)))

        return action.value, exp_values

def getChartIndFromCards(my_hand, dealer_hand):

    my_ind = c_int(0); 
    dealer_ind = c_int(0); 

    _caco.chart_ind_from_hands(my_hand, dealer_hand, byref(my_ind), byref(dealer_ind));

    return (dealer_ind.value, my_ind.value) 


# returns the optimal move based on the desired strategy 
def simulateGame(max_hands=50, num_decks=6, num_players=4, rules=vegasRules, strategy='omniscient', seed=None):

    if seed is None:
        _caco.seed_rand(c_int(int(1000*time.time())))
    else:
        _caco.seed_rand(c_int(seed))

    shoe = Shoe(numdecks=num_decks)
    dealer = Hand()
    players = (num_players*Hand)() 

    print ' == Begin hand =='

    # one hand at a time for now
    shoe.shuffle()
    print 'Shoe:', shoe 
    for p, player in enumerate(players):
        dealCardToHand(shoe, player, way='random')
    dealCardToHand(shoe, dealer, way='random')
    print 'Starting hands:'
    print ' - Dealer has', dealer 
    for p, player in enumerate(players):
        print ' - Player %d has'%p, player

    print 'Shoe:', shoe 

    # deal a second round of cards
    dealer_peek = 0
    for p, player in enumerate(players):
        dealCardToHand(shoe, player, way='random')
        dealer_peek |= _caco.blackjack(player)
    if dealer_peek:
        # TODO: still not right...
        print ' - One or more players has blackjack. Dealer peeks!'
        hole_card = _caco.random_card_from_shoe(byref(shoe))

    print 'Shoe:', shoe 

    # if dealer blackjack...

    for p, player in enumerate(players):
        print 'Player %d acting now:'%p 
        print ' -', player

        action, _ = getOptimalMove(shoe, dealer, player, strategy=strategy)
        print ' - best action =', actionLabels[action]

        if action == 0:
            print ' - stood on', player

        atmp = action
        while atmp == 1:
            dealCardToHand(shoe, player, way='random')
            print ' - hit and got', player
            atmp, _ = getOptimalMove(shoe, dealer, player, strategy=strategy)

        if action == 2:
            dealCardToHand(shoe, player, way='random')
            print ' - doubled and got', player

        if action == 3:
            print ' - no splits yet!' 

        #if action == 3:



    #if _caco.blackjack(dealer):

    #for h in xrange(max_hands):
        ## todo: when to shuffle?
        #shoe.shuffle()


def plotChart(ar, title=None, cmap=None,
        vrange=None, grid=True, textarr=None, textfmt=None, contours=None):

    # set up the axes 
    fig, ax = plt.subplots(3, 1, figsize=(10, 20), gridspec_kw={'height_ratios': [16./35.,9./35.,10./35.]},sharex=True)
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
    hardticks = np.linspace(5, 20, 16)
    ax[0].set_yticks(hardticks)
    ax[0].set_yticks(hardticks+0.4, minor=True)
    ax[0].set_yticklabels(["%d"%i for i in range(5,20)], minor=True)
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
    if cmap is None:
        cmap = colors.ListedColormap(['green','yellow','red','cyan','white'])
        bounds = [0,1,2,3,4,5] 
        norm = colors.BoundaryNorm(bounds, cmap.N)
    else:
        norm = None

    imargs = {'interpolation': 'nearest', 'aspect': 'auto', 'cmap': cmap, 'vmin': vrange[0],
            'vmax': vrange[1], 'norm': norm}
    hard_actions = ar[:,:15]
    imargs['extent'] = [2,10,5,20] 
    ax[0].imshow(hard_actions.T, **imargs)
    soft_actions = ar[:,15:24]
    imargs['extent'] = [2,10,13,21] 
    ax[1].imshow(soft_actions.T, **imargs)
    split_actions = ar[:,24:34]
    imargs['extent'] = [2,10,2,11] 
    ax[2].imshow(split_actions.T, **imargs)

    # draw contours
    if contours is not None:
        for area, char in zip(contours, ['X','O']):
            for ind in area:
                if ind[1] < 16:
                    ax[0].text(dticks[ind[0]]+0.4, 26-hardticks[ind[1]]+0.4, char, va='center', ha='center')
                elif ind[1] < 25:
                    print ind[1]
                    ax[1].text(dticks[ind[0]]+0.4, 33-softticks[ind[1]-16]+0.4, char, va='center', ha='center')
                else:
                    ax[2].text(dticks[ind[0]]+0.4, 12-pairticks[ind[1]-25]+0.4, char, va='center', ha='center')
    
    # draw text if asked for
    if textarr is not None and textfmt is not None:
        hard_text = textarr[:,:15]
        for d in xrange(0, 10):
            for m in xrange(0, 15):
                ax[0].text(dticks[d]+0.4, (24-hardticks[m])+0.4, textfmt(hard_text[d,m],
                    hard_actions[d,m]), va='center', ha='center')
        soft_text = textarr[:,15:24]
        for d in xrange(0, 10):
            for m in xrange(0, 9):
                ax[1].text(dticks[d]+0.4, (33-softticks[m])+0.4, textfmt(soft_text[d,m],
                    soft_actions[d,m]), va='center', ha='center')
        pair_text = textarr[:,24:34]
        for d in xrange(0, 10):
            for m in xrange(0, 10):
                ax[2].text(dticks[d]+0.4, (12-pairticks[m])+0.4, textfmt(pair_text[d,m],
                    split_actions[d,m]), va='center', ha='center')
    
    plt.show()
    return fig, ax



def getChartContours(ar):


    sorted_inds = np.dstack(np.unravel_index(np.argsort(ar.ravel()), ar.shape))[0]

    # tally a cumulative probabilty through the sorted cells, breaking at 
    # standard deviations from the unit bet
    one_sigma = []
    two_sigma = []
    cumprb = 0.0
    invartot = 1.0/np.sum(ar)
    for ind in sorted_inds: 
        ind = tuple(ind)
        prb = np.abs(ar[ind]*invartot)
        if cumprb < 0.6827:
            one_sigma.append(ind)
        elif cumprb < 0.9545:
            two_sigma.append(ind)
        cumprb += prb

    return one_sigma, two_sigma


import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.collections import PolyCollection
import ctypes
from ctypes import *
import warnings
import os 
import time
import inspect 
import itertools
from scipy.stats import norm

# nice plot styling
matplotlib.rcParams['font.family'] = 'monospace'
matplotlib.rcParams['font.size'] = 20.0
matplotlib.rcParams['text.usetex'] = False#True
matplotlib.rcParams['figure.figsize'] = (15,10)
matplotlib.rcParams['lines.linewidth'] = 1.0
matplotlib.rcParams['grid.linewidth'] = 1.5

# load the underlying C shared library
_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
_caco = ctypes.CDLL('%s/blackjack.so'%_path)
_caco.deal_card_to_hand_choose.restype = c_double 

# nice helpers
allCards = [2,3,4,5,6,7,8,9,10,11]
cardLabels = ["2","3","4","5","6","7","8","9","10","A"]
#actionLabels = ["Stand", "Hit", "Double", "Split", "Surrender", "Insurance"]
actionLabels = ["Sta", "Hit", "Dbl", "Split", "Surrender", "Insurance"]

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
        exp = c_double(0.0)
        bet = c_double(1.0)
        allowed_moves = np.array([1,1,1,0,0,0], dtype=np.int32) 
        depth = c_int(2)
        action = c_int(0)

        _caco.expected_value(bet, my_hand, dealer_hand, shoe,
                allowed_moves.ctypes.data_as(POINTER(c_int)), byref(action), byref(exp), depth)

        return action.value, exp.value



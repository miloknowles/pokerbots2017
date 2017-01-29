import time
from cfr import *
from random import random
import json


# load the cumulative strategy into memory
with open('cumulativeStrategy.json') as csFile:   
    CUMULATIVE_STRATEGY = json.load(csFile)
    print "Loaded in cumulative strategy"


def getStrategy(I):
	"""
	If information set I is in the trained strategy, return it (normalized)
	If not, return None
	"""
	if I in CUMULATIVE_STRATEGY:
		s = CUMULATIVE_STRATEGY[I]

		s_sum = 0
		for a in s.itervalues():
			s_sum+=a

		s_norm = {}
		for k in s.keys():
			s_norm[k] = float(s[k]) / s_sum

		return s_norm

	else:
		print "Info. set not found in cumulative strategy, returning None"
		return None


def testHistoryAgainstCurrentStrategy():
    """
    Try playing out a game against the current strategy from training.
    """
    initialDealer = Dealer()
    h = History([], 0, 0, 0, 0, initialDealer, 0, 0, 0, 0, 200, 200, [], [], [])

    while(h.NodeType != 2): # while not terminal, simulate
        if h.NodeType == 0:
            h.printAttr()
            print "-----SIMULATING CHANCE------"
            h = h.simulateChance()
        elif h.NodeType == 1:
            h.printAttr()
            actions = h.getLegalActions()
            print "Legal Actions:", actions

            givenAction=False
            while(not givenAction):
                action = raw_input("Choose action: ")
                if action in actions:
                    givenAction=True
                else:
                    print "Action not allowed. Try again."
            print "-----SIMULATING ACTION------"
            h = h.simulateAction(action)
            print convertHtoI(h, 0)
        else:
            print "ERROR, not recognized nodetype"

    print "------TERMINAL NODE REACHED------"
    h.printAttr()
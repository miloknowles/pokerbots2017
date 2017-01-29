import time
from cfr import *
from random import random, choice
import json


# load the cumulative strategy into memory
with open('./jsons/currentStrategy/cumulativeStrategy.json') as csFile:   
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


def chooseAction(action_dict):
    """
    Chooses an action from a dict of action:prob pairs
    Tested with a million choices, is very close in practice to the profile given.
    """
    action_dict_sum = sum(action_dict.itervalues())
    assert (action_dict_sum < 1.03 and action_dict_sum > 0.97), "Error: Strategy profile probabilities do not add up to 1."

    random_float = random()
    cutoff = 0
    for a in action_dict.keys():
        cutoff += action_dict[a]
        if random_float <= cutoff:
            return a

def chooseActionRandom(legal_actions):
	"""
	Chooses at random from a list of legal_actions
	"""
	return choice(legal_actions)

def testHistoryAgainstCurrentStrategy():
    """
    Try playing out a game against the current strategy from training.
    """
    initialDealer = Dealer()
    h = History([], 0, 0, 0, 0, initialDealer, 0, 0, 0, 0, 200, 200, [], [], [])

    while(h.NodeType != 2): # while not terminal, simulate
        if h.NodeType == 0:
            #h.printAttr()
            print "-----SIMULATING CHANCE------"
            h = h.simulateChance()

        elif h.NodeType == 1:

        	h.printAttr()
        	actions = h.getLegalActions()
        	print "Legal Actions:", actions

        	# if it's an opponent move
        	if h.ActivePlayer == 1:
        		I_opp = convertHtoI(h, 1)
        		s = getStrategy(I_opp)
        		print "Opponent Strategy:", s
        		opp_action = chooseActionRandom(actions) if s==None else chooseAction(s)
        		
        		h.simulateAction(opp_action)

        	else: # our move, so ask for an action

	            givenAction=False

	            while(not givenAction):
	                action = raw_input("Choose action: ")
	                if action in actions:
	                    givenAction=True
	                else:
	                    print "Action not allowed. Try again."

	            print "-----SIMULATING ACTION------"
	            h = h.simulateAction(action)

        else:
            print "ERROR, not recognized nodetype"

    print "------TERMINAL NODE REACHED------"
    h.printAttr()
    p1_util, p2_util = h.getTerminalUtilities()
    print "P1_Util:", p1_util, "P2_Util:", p2_util


testHistoryAgainstCurrentStrategy()




#!/usr/bin/env
import time
from cfr import *
from random import random
import json

# DEFINE PARAMETERS AND TABLES #
CUMULATIVE_REGRETS = {} # dictionary of dictionaries
CUMULATIVE_STRATEGY = {} # dictionary of dictionaries
EPSILON = 0.05
TAU = 1000
BETA = 10
HAND_STRENGTH_ITERS = 1000

def writeCumulativeRegretsToFiles():
	with open('cumulativeRegrets.json', 'w') as f:
		json.dump(CUMULATIVE_REGRETS, f, indent=1)

def writeCumulativeStrategyToFiles():
	with open('cumulativeStrategy.json', 'w') as f:
		json.dump(CUMULATIVE_STRATEGY, f, indent=1)


def WalkTree(h, i, q):
	"""
	h: a History object
	i: the current player (information set will be from their perspective)
	q: the sample probability of getting to this node in the tree
	"""
	if h.NodeType == 2: # if h is terminal
		p1_utility, p2_utility = h.getTerminalUtilities() # returns (p1_util, p2_util)
		return p1_utility if i==0 else p2_utility

	elif h.NodeType == 0: # if h is a chance node
		newH = h.simulateChance()
		return WalkTree(newH, i, q)

	# get the current regret matched strategy
	I = convertHtoI(h)
	sigma = getCurrentRegretMatchedStrategy(I)

	else: # this must be an action node
		assert h.NodeType == 1, "Error: expected an action node!"

		if h.ActivePlayer != i: # if it's an opponent action, sample from current strategy

			# first, update the cumulative strategy
			updateCumulativeStrategy(I, sigma, q)

			# now sample an opponent action based on on the current regret matched strategy
			legalActions = h.getLegalActions()

			# replace annoying colons from the history
			for i in range(len(legalActions)):
				legalActions[i]=legalActions[i].replace(":","")
				legalActions.replace(":","")

			oppAction = chooseAction(sigma)
			newH = h.simulateAction(oppAction)
			return WalkTree(newH, i, q)


		elif h.ActivePlayer==i: # if it's our action
			legalActions = h.getLegalActions()

			# replace annoying colons from the history
			for i in range(len(legalActions)):
				legalActions[i]=legalActions[i].replace(":","")
				legalActions.replace(":","")

			# get the cumulative strategy for our current infoset
			s = getCumulativeStrategy(I) # s = {action1:1.232 action2:17.384, action3:3.129 etc}

			# this will store the counterfactual value of each action
			actionValues = {}

			# sum up the items in s so that we can normalize them
			cumulativeStrategySum = 0
			actions = s.keys()
			for a in actions:
				values[a] = 0 #set the value of all actions to zero initially
				cumulativeStrategySum+=s[a]

			# go through each action and decide 
			for a in actions:
				# all actions get sampled with probability at least epsilon
				rho = max(EPSILON, float(s[a]) / cumulativeStrategySum)

				if random() < rho:
					newH = h.simulateAction(a)
					actionValues[a] = WalkTree(newH, i, q*min(1,rho))

			# determine the EV of the current regret-matched strategy (sigma)
			sigmaEV = 0
			for a in actions:
				sigmaEV += sigma[a] * actionValues[a]

			# finally, update the cumulative regrets
			for a in actions:
				CUMULATIVE_REGRETS[I][a] += (values[a] - sigmaEV)

			return sigmaEV

		else:
			assert False, "Error: ActivePlayer was neither player."


def updateCumulativeRegrets(I, regrets, weight):
    """
    Updates the cumulative regret table for information set I by adding new regrets.
    I (string): the information set we're working with
    regrets: a list of regrets for each action at the current information set
    """
    if I in CUMULATIVE_REGRETS:
        assert len(CUMULATIVE_REGRETS[I]) == len(regrets), "ERROR: Tried to update cumulative regrets with wrong number of regrets."

        # add the new set of regrets on to the cumulative regrets
        for a in range(len(regrets)):
            CUMULATIVE_REGRETS[I][a] += regrets[a]
    else:
        print "Information set ", I, " not found in cumulative regrets. Adding first regrets."
        CUMULATIVE_REGRETS[I] = regrets

    #TODO: need to weight regret update by some probability
    assert(False)


def getCumulativeStrategy(I):
    """
    I (string): the information set that we want to look up the cumulative strategy for

    Gets cumulative strategy for information set I if it exists, else returns 0.
    """
    if I in CUMULATIVE_STRATEGY:
        return CUMULATIVE_STRATEGY[I]
    else:
        print "Infoset ", I, " not in CUMULATIVE_STRATEGY, returning None" 
        return None


def updateCumulativeStrategy(I, action_dict, weight):
    """
    Updates the cumulative strategy table for information set I by adding on latest strategy profile.
    I (string): the information set we're working with
    strategy: a strategy profile (list of weights associated with each action)
    """
    if I in CUMULATIVE_STRATEGY:
        assert len(CUMULATIVE_STRATEGY[I]) == len(action_dict), "ERROR: Tried to update cumulative strategy with wrong number of actions."

        # add the new set of strategy probabilities on to the cumulative strategy
        for a in action_dict.keys():
            CUMULATIVE_STRATEGY[I][a] += action_dict[a]
    else:
        print "Information set ", I, " not found in cumulative strategy. Adding first strategy profile."
        CUMULATIVE_STRATEGY[I] = action_dict

    #TODO: need to weight strategy update by some probability
    assert(False)

def getCumulativeRegrets(I):
"""
I (string): the information set that we want to look up the cumulative regrets for

Gets cumulative regrets for information set I if they exist, else returns 0.
"""
	if I in CUMULATIVE_REGRETS:
	    return CUMULATIVE_REGRETS[I]
	else:
	    print "Infoset ", I, " not in CUMULATIVE_REGRETS, returning None" 
	    return None


def getCurrentRegretMatchedStrategy(I, legalActions):
    """
    I (string): the information set we want to get the CURRENT strategy for
    legalActions: a list of legal action strings

    If we haven't hit this information set before, strategy will be evenly distributed across all legal actions.
    Otherwise, do regret matching on cumulative regrets for this information set.
    """
    cumulativeRegrets = getCumulativeRegrets(I) # a dictionary with action:regret pairs

    if cumulativeRegrets == None: #have not hit this infoset yet: choose randomly from actions
    	for a in legalActions:
    		strategy[a] = 1.0 / len(legalActions)

    else: # do regret matching

        # check that we have the same number of legal actions as actions stored in cumulative regret tables
        assert len(cumulativeRegrets)==len(legalActions), "Number of actions stored in cum. regret tables does not match num. of legal actions for I!"

        # regret matching: normalize regrets
        rsum = float(sum(cumulativeRegrets.itervalues()))
        for a in legalActions:
        	strategy[a] = cumulativeRegrets[a] / rsum

    return strategy


def chooseAction(action_dict):
    """
    Chooses an action from a dict of action:prob pairs
    Tested with a million choices, is very close in practice to the profile given.
    """
    action_dict_sum = sum(action_dict.itervalues)
    assert (action_dict_sum < 1.03 and action_dict_sum > 0.97), "Error: Strategy profile probabilities do not add up to 1."

    random_float = random()
    cutoff = 0
    for a in range(len(strategy)):
        cutoff += action_dict[a]
        if random_float <= cutoff:
            return a



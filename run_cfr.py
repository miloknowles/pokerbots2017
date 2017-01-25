#!/usr/bin/env
import time
from cfr import *

# DEFINE PARAMETERS AND TABLES #
CUMULATIVE_REGRETS = {}
CUMULATIVE_STRATEGY = {}
EPSILON = 0.05
TAU = 1000
BETA = 10e6
HAND_STRENGTH_ITERS = 1000

def writeCumulativeRegretsToFiles():
	# TODO
	pass

def writeCumulativeStrategyToFiles():
	# TODO 
	pass


def WalkTree(h, i, q):




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
    I (string): the information set that we want to look up the cumulative regrets for

    Gets cumulative regrets for information set I if they exist, else returns 0.
    """
    if I in CUMULATIVE_STRATEGY:
        return CUMULATIVE_STRATEGY[I]
    else:
        print "Infoset ", I, " not in CUMULATIVE_STRATEGY, returning None" 
        return None


def updateCumulativeStrategy(I, strategy, weight):
    """
    Updates the cumulative strategy table for information set I by adding on latest strategy profile.
    I (string): the information set we're working with
    strategy: a strategy profile (list of weights associated with each action)
    """
    if I in CUMULATIVE_STRATEGY:
        assert len(CUMULATIVE_STRATEGY[I]) == len(strategy), "ERROR: Tried to update cumulative strategy with wrong number of actions."

        # add the new set of strategy probabilities on to the cumulative strategy
        for a in range(len(strategy)):
            CUMULATIVE_STRATEGY[I][a] += strategy[a]
    else:
        print "Information set ", I, " not found in cumulative strategy. Adding first strategy profile."
        CUMULATIVE_STRATEGY[I] = strategy

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

    If we haven't hit this information set before, strategy will be evenly distributed across all legal actions.
    Otherwise, do regret matching on cumulative regrets for this information set.
    """
    cumulativeRegrets = getCumulativeRegrets(I)

    if cumulativeRegrets == None: #have not hit this infoset yet: choose randomly from actions
        strategy = [1.0 / float(len(legalActions)) for i in range(len(legalActions))]

    else: # do regret matching

        # check that we have the same number of legal actions as actions stored in cumulative regret tables
        assert len(cumulativeRegrets)==len(legalActions), "Number of actions stored in cumulative regret tables does not match number of legal actions for the current state!"

        # regret matching: normalize regrets
        rsum = sum(cumulativeRegrets)
        strategy = [float(a) / float(rsum) for a in cumulativeRegrets]

    return strategy


def chooseAction(strategy):
    """
    Chooses an action from the strategy profile.
    strategy: a strategy profile of weights for each action 1,2,...,len(strategy)
    Tested with a million choices, is very close in practice to the profile given.
    """
    assert (sum(strategy) < 1.03 and sum(strategy) > 0.97), "Error: Strategy profile probabilities do not add up to 1."

    random_float = random.random()
    cutoff = 0
    for a in range(len(strategy)):
        cutoff += strategy[a]
        if random_float <= cutoff:
            return a
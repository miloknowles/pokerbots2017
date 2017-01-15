import time
from pokereval.card import Card
from pokereval.hand_evaluator import HandEvaluator
import random
from numpy.random import choice
from itertools import combinations


def buildFullDeck():
	"""
	Vals: 2-14 = 2-A
	Suits: [1,2,3,4] = [s,h,d,c]
	"""
	deck = []
	vals = [i for i in range(2,15)]
	suits = [1,2,3,4]
	for v in vals:
		for s in suits:
			deck.append(Card(v,s))
	return deck


class Dealer(object):
    def __init__(self):
        self.deck = buildFullDeck()
        random.shuffle(self.deck)
        random.shuffle(self.deck)
    
    def dealHand(self):
        hand = []
        hand.append(self.deck.pop(0))
        hand.append(self.deck.pop(0))
        return hand
    
    def dealCard(self):
        return self.deck.pop(0)

    def dealFlop(self):
        table = []
        for n in range(3):
            table.append(self.dealCard())
        return table

    def resetDeck(self):
    	self.deck = buildFullDeck()

    def getCurrentDeck(self):
    	return self.deck


# DEFINE THINGS #
CUMULATIVE_REGRETS = {}
CUMULATIVE_STRATEGY = {}
EPSILON = 0.05
TAU = 1000
BETA = 10e6
# END DEFINITIONS #


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
	Tested with a million choices.
	"""
	assert (sum(strategy) < 1.03 and sum(strategy) > 0.97), "Error: Strategy profile probabilities do not add up to 1."

	random_float = random.random()
	cutoff = 0
	for a in range(len(strategy)):
		cutoff += strategy[a]
		if random_float <= cutoff:
			return a

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



def convertHtoI(history):
	"""
	Uses predefined abstraction rules to convert a sequency (history) into an information set.
	"""
	# TODO
	raise NotImplementedError


def getHandStrengthSquaredExhaustive(hand, board, deck):
	"""
	Computes the hand strength squared: the expectation of the square of the hand strength after the last card is revealed
	hand: (list of Card objects)
	deck: the current deck (hand should be removed from it), should be shuffled also
	"""
	assert len(hand) + len(board) <= 7, "Error: hand cannot have more than 7 cards."
	assert len(hand) + len(board) + len(deck) == 52, "Error: hand and deck should add up to 52 cards"

	numCardsToSample = 5 - len(board)
	# compute the expectation of the hand strength squared when there is a full board
	# this is the average hand strength over all possible outcomes for the board
	remainingCardCombs = combinations(deck, numCardsToSample)
	handStrengthSum = 0
	numCombsConsidered = 0
	for comb in remainingCardCombs:
		newBoard = board+list(comb)
		numCombsConsidered+=1
		handStrengthSum += (HandEvaluator.evaluate_hand(hand,newBoard) ** 2)

	avgHandStrength = float(handStrengthSum) / numCombsConsidered
	return avgHandStrength

def getHandStrengthSquaredSampled(hand, board, deck):
	t0 = time.time()
	assert len(hand) + len(board) <= 7, "Error: hand cannot have more than 7 cards."
	assert len(hand) + len(board) + len(deck) == 52, "Error: hand and deck should add up to 52 cards"

	numCardsToSample = 5 - len(board)

	num_samples = 100
	remainingCardCombs = []
	for s in range(num_samples):
		comb = []
		
		while len(comb) < numCardsToSample:
			card = random.choice(deck)
			if card not in comb:
				comb.append(card)

		remainingCardCombs.append(comb)

	handStrengthSum = 0
	numCombsConsidered = 0

	# this is taking all the time
	for c in remainingCardCombs:
		numCombsConsidered+=1
		handStrengthSum += (HandEvaluator.evaluate_hand(hand,board+c) ** 2)

	avgHandStrength = float(handStrengthSum) / numCombsConsidered
	t1 = time.time()
	#print(t1-t0)
	return avgHandStrength


def testHandStrengthFunctions():
	diffs = []
	for i in range(10):
		print "Iteration", i
		d = Dealer()
		hand = d.dealHand()
		flop = d.dealFlop()
		deck = d.getCurrentDeck()

		print "Hand", hand
		print "Board", flop
		initial_strenght = HandEvaluator.evaluate_hand(hand, [])
		print "Initial strength:", initial_strenght**2

		hss_sampled = getHandStrengthSquaredSampled(hand,flop,deck)
		print "Sampled:", hss_sampled

		#hss = getHandStrengthSquaredExhaustive(hand, flop, deck)
		#print "Exhaustive:", hss

		#diffs.append(abs(hss-hss_sampled))

	#print "Average difference between sampled and exhaustive:", sum(diffs) / 10

#testHandStrengthFunctions()

def writePreflopHandStrengthSquaredFile():
	deck = buildFullDeck()
	hands = combinations(deck, 2)

	with open('hss_preflop.txt', 'w') as f:
		counter = 0
		for h in hands:
			counter += 1
			print "Working on hand", counter
			hand = list(h)
			current_deck = deck[:]
			current_deck.remove(hand[0])
			current_deck.remove(hand[1])
			hss_sampled = getHandStrengthSquaredSampled(h, [], current_deck)

			handstr = str(hand[0]) + str(hand[1])
			handstr.replace('<Card(', '')
			handstr.replace(')>', '')

			f.write(handstr+":"+str(hss_sampled)+"\n")
			f.flush()
	
	f.close()

writePreflopHandStrengthSquaredFile()

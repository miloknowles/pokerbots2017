import time
from pokereval.card import Card
from pokereval.hand_evaluator import HandEvaluator
from numpy.random import choice
from numpy import var, std, mean
from random import shuffle
from itertools import combinations
from operator import attrgetter
import os
from pbots_calc import calc, Results

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
        shuffle(self.deck)
        shuffle(self.deck)
    
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



def getRiverHSS(hand,river):
	"""
	Gets the HSS of a hand and a given board on the river.
	There is no lookup, just calls the HandEvaluator.evaluate_hand() function
	"""
	return (HandEvaluator.evaluate_hand(hand,river) ** 2)


def getHandStrength(hand, board, iters=1000):
	"""
	Uses pbots calc library to get the hand strength of a given hand against a given board.
	hand: a list of 2 Card objects
	board: a list of Card objects (could be [] or contain up to 5 cards)
	
	With iters=500: 95% of data within 3.8% of actual
	With iters=1000: 95% of data within 2.7% of actual
	With iters=2000: 95% of data within 2.2% of actual
	With iters=4000: 95% of data within 1.7% of actual
	"""
	assert len(board) <= 5, "Error: board must have 3-5 cards"
	assert (len(hand)==2), "Error: hand must contain exactly 2 cards"

	# the "xx" tells pbots_calc to compare hand against a random opponent hand
	handstr = convertSyntax(hand)+":xx"
	boardstr = convertSyntax(board)

	#note the empty "" parameter is telling pbots_calc not to remove any extra cards from the deck
	res = calc(handstr, boardstr, "", iters)
	return res.ev[0] # return the EV of our hand


def convertSyntax(cards):
	"""
	Converts a list of Card objects to correct syntax for pbots_calc
	i.e Card(4,1) -> 4s

	OR, if cards is just a single cards, it converts a single card object into a string
	"""

	if type(cards) == list:
		cardstr = ""
		for c in cards:
			cardstr+=(c.RANK_TO_STRING[c.rank]+c.SUIT_TO_STRING[c.suit])
		return cardstr
	else:
		return cards.RANK_TO_STRING[cards.rank]+cards.SUIT_TO_STRING[cards.suit]


def testGetHandStrength():
	iters = 1000
	hand = [Card(9,1), Card(4,3)]
	flop = [Card(2,1), Card(13,2), Card(13,3)]
	time0=time.time()
	strengths = []
	for i in range(1000):
		strengths.append(getHandStrength(hand,flop,iters))
		print getHandStrength(hand, flop)
	time1 = time.time()
	print "Time:", time1-time0

	print "STD:", std(strengths)
	print "Var:", var(strengths)
	print "95 percent data within:", 2*std(strengths)


def determineBestDiscard(hand, board, min_improvement=0.03, iters=1000):
	"""
	Given a hand and either a flop or turn board, returns whether the player should discard, and if so, which card they should choose.
	hand: a list of Card objects
	board: a list of Card objects
	"""
	originalHandStr = convertSyntax(hand)+":xx"
	boardstr = convertSyntax(board)

	originalHandEV = calc(originalHandStr, boardstr, "", 1000).ev[0]

	swapFirstEVSum = 0
	swapSecondEVSum = 0
	numCards = 0

	for card in FULL_DECK:
		if card in board or card in hand:
			continue
		else:
			# increment
			numCards += 1

			cardstr = convertSyntax(card)

			# compare original hand to the hand made by replacing first card with CARD
			swapFirstStr = "%s%s%s" % (cardstr,originalHandStr[2:4],":xx")

			# compare original hand to the hand made by replacing second card with CARD
			swapSecondStr = "%s%s%s" % (originalHandStr[0:2],cardstr,":xx")

			# print("First:", swapFirstStr)
			# print("Second:", swapSecondStr)

			swap_first_res = calc(swapFirstStr, boardstr, "", iters)
			swap_second_res = calc(swapSecondStr, boardstr, "", iters)

			swapFirstEVSum += swap_first_res.ev[0]
			swapSecondEVSum += swap_second_res.ev[0]

	# calculate the average EV of swapping first and second when we play them against the original hand
	avgSwapFirstEV = float(swapFirstEVSum) / numCards
	avgSwapSecondEV = float(swapSecondEVSum) / numCards

	# if either swap increases EV by more than 5%
	if avgSwapFirstEV > originalHandEV+min_improvement or avgSwapSecondEV > originalHandEV+min_improvement:
		if avgSwapFirstEV > avgSwapSecondEV:
			return (True, 0, avgSwapFirstEV, originalHandEV)
		else:
			return (True, 1, avgSwapSecondEV, originalHandEV)
	else:
		return (False, None, 0, originalHandEV)


def determineBestCardToKeep(hand, board, iters=1000):
	"""
	Given a hand and either a flop or turn board, returns whether the player should discard, and if so, which card they should choose.
	hand: a list of Card objects
	board: a list of Card objects
	"""
	originalHandStr = convertSyntax(hand)
	boardStr = convertSyntax(board)

	# create a neutral deck that does not contain any cards from the hand or board
	neutralDeck = []
	for card in FULL_DECK:
		if card in board or card in hand:
			continue
		else:
			neutralDeck.append(card)

	# shuffle so that we can pop random cards off of top
	shuffle(neutralDeck)

	# get two comparison cards that will be swapped
	
	cmpCard1 = neutralDeck.pop(0)

	# note: we make sure that these comparison cards are not the same rank as either card in our hand!
	while cmpCard1.rank==hand[0].rank or cmpCard1.rank==hand[1].rank or cmpCard1.suit==hand[0].suit or cmpCard1.suit==hand[1].suit:
		cmpCard1 = neutralDeck.pop(0)

	cmpCard2 = neutralDeck.pop(0)
	while cmpCard2.rank==hand[0].rank or cmpCard2.rank==hand[1].rank or cmpCard2.suit==hand[0].suit or cmpCard2.suit == hand[1].suit:
		cmpCard2 = neutralDeck.pop(0)

	cmpCard3 = neutralDeck.pop(0)
	while cmpCard3.rank==hand[0].rank or cmpCard3.rank==hand[1].rank or cmpCard3.suit==hand[0].suit or cmpCard3.suit == hand[1].suit:
		cmpCard3 = neutralDeck.pop(0)

	cmpCard4 = neutralDeck.pop(0)
	while cmpCard4.rank==hand[0].rank or cmpCard4.rank==hand[1].rank or cmpCard4.suit==hand[0].suit or cmpCard4.suit == hand[1].suit:
		cmpCard4 = neutralDeck.pop(0)
	# now we have 2 "neutral" comparison cards
	cmpCard1Str = convertSyntax(cmpCard1)
	cmpCard2Str = convertSyntax(cmpCard2)
	cmpCard3Str = convertSyntax(cmpCard3)
	cmpCard4Str = convertSyntax(cmpCard4)

	# play [C_1, C1*] against [C_2, C2*]
	res1 = calc("%s%s:%s%s" % (originalHandStr[0:2], cmpCard1Str, originalHandStr[2:4], cmpCard2Str), boardStr, "", iters)
	# play [C_1, C2*] against [C_2, C1*]
	res2 = calc("%s%s:%s%s" % (originalHandStr[0:2], cmpCard2Str, originalHandStr[2:4], cmpCard1Str), boardStr, "", iters)

	res3 = calc("%s%s:%s%s" % (originalHandStr[0:2], cmpCard3Str, originalHandStr[2:4], cmpCard4Str), boardStr, "", iters)

	res4 = calc("%s%s:%s%s" % (originalHandStr[0:2], cmpCard4Str, originalHandStr[2:4], cmpCard3Str), boardStr, "", iters)

	# determine which card is stronger, and should be kept
	C1_scores = [res1.ev[0], res2.ev[0], res3.ev[0], res4.ev[0]] # the EVs for hands where we KEPT C1
	C2_scores = [res1.ev[1], res2.ev[1], res3.ev[1], res4.ev[1]] # the EVs for hands where we KEPT C2

	# keepCard = None
	# if C1_scores[0] > C2_scores[0] and C1_scores[1] > C2_scores[1]: # C1 is clearly better to keep (won in both cases)
	# 	keepCard = 0
	# elif C2_scores[0] > C1_scores[0] and C2_scores[1] > C1_scores[1]: # C2 is clearly better to keep
	# 	keepCard = 1

	# else: # C1 and C2 are somewhat close in their value to keep

	avgC1Score = mean(C1_scores)
	avgC2Score = mean(C2_scores)

	if avgC1Score > avgC2Score: # C1 is better to keep
		keepCard = 0
	else:
		keepCard = 1

	return keepCard


def determineBestDiscardFast(hand, board, min_improvement=0.03, iters=1000):
	"""
	min_improvement: the EV % that swapping must increase our hand by in order to go for the swap

	Returns:
	-whether we should swap
	-if so, the index of the card in our hand we should swap (0 or 1)
	-the avg. EV of swapping that card
	-the original EV of our hand as is 
	"""

	# if we were to keep a card, determine which one is best
	keepCard = determineBestCardToKeep(hand, board)
	print "Playoff thinks we should discard:", 1-keepCard

	boardStr = convertSyntax(board)
	originalHandEV = calc("%s:xx" % convertSyntax(hand), boardStr, "", 1000).ev[0]

	numCards = 0
	swapEVSum = 0
	for card in FULL_DECK:
		if card in board or card in hand:
			continue
		else:
			# increment
			numCards += 1

			cardstr = convertSyntax(card)

			# remember, we want to KEEP our keepCard and swap the other card!!!
			swapStr = "%s%s%s" % (cardstr,convertSyntax(hand[keepCard]),":xx")
			swapRes = calc(swapStr, boardStr, "", iters)
			swapEVSum += swapRes.ev[0]

	# calculate the average EV of swapping the card besides our keepCard
	avgSwapEV = float(swapEVSum) / numCards

	# if either swap increases EV by more than 5%
	if avgSwapEV > originalHandEV + min_improvement:
		return (True, 1-keepCard, avgSwapEV, originalHandEV)
	else:
		return (False, None, 0, originalHandEV)


# DEFINE THINGS #
FULL_DECK = buildFullDeck()
CUMULATIVE_REGRETS = {}
CUMULATIVE_STRATEGY = {}
EPSILON = 0.05
TAU = 1000
BETA = 10e6
HAND_STRENGTH_ITERS = 1000
# END DEFINITIONS #


def testDetermineDiscard():

	bool_disagrees = 0
	card_disagrees = 0

	for i in range(500):
		print(i)
		d = Dealer()
		hand = d.dealHand()
		flop = d.dealFlop()
		print "Hand:", hand
		print "Flop:", flop

		# check with exhaustive method
		time0 = time.time()
		exhaustive = determineBestDiscard(hand,flop, 0.05, 100)
		print "Exhaustive:", exhaustive
		time1 = time.time()
		print "Time:", time1-time0

		# check with the playoff method
		time0 = time.time()
		fast = determineBestDiscardFast(hand,flop, 0.05, 100)
		print "Fast:", fast
		time1 = time.time()
		print "Time:", time1-time0

		if exhaustive[0] != fast[0]:
			bool_disagrees += 1
		elif exhaustive[1] != fast[1]:
			card_disagrees += 1

	print "T/F Different:", float(bool_disagrees) / 500
	print "Card disagrees:", float(card_disagrees) / 500

testDetermineDiscard()


# d = Dealer()
# hand = d.dealHand()
# flop = d.dealFlop()
# deck = d.getCurrentDeck()
# s = time.time()
# ev = HandEvaluator.evaluate_hand(hand,flop)
# f = time.time()
# print f-s
# print ev


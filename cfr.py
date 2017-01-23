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
from copy import deepcopy

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



def determineBestDiscard(hand, board, min_improvement=0.05, iters=100):
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


def determineBestCardToKeep(hand, board, iters=1000, highcard_weight=0.03):
	"""
	A helper function for determineDiscardFast().
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

	# can't let comparison card be within +/- of value of cards in the hand
	forbiddenRanks = [hand[0].rank, hand[1].rank, hand[0].rank-1, hand[1].rank-1, hand[0].rank+1, hand[1].rank+1]

	# shuffle so that we can pop random cards off of top
	shuffle(neutralDeck)

	# get two comparison cards that will be swapped
	cmpCard1 = neutralDeck.pop(0)

	# note: we make sure that these comparison cards are not the same rank as either card in our hand!
	while cmpCard1.rank in forbiddenRanks or cmpCard1.suit==hand[0].suit or cmpCard1.suit==hand[1].suit:
		cmpCard1 = neutralDeck.pop(0)

	cmpCard2 = neutralDeck.pop(0)
	while cmpCard2.rank in forbiddenRanks or cmpCard2.suit==hand[0].suit or cmpCard2.suit == hand[1].suit:
		cmpCard2 = neutralDeck.pop(0)

	# now we have 2 "neutral" comparison cards
	cmpCard1Str = convertSyntax(cmpCard1)
	cmpCard2Str = convertSyntax(cmpCard2)
	print "Cmp Cards:", cmpCard1Str, cmpCard2Str

	# play [C_1, C1*] against [C_2, C2*]
	res1 = calc("%s%s:%s%s" % (originalHandStr[0:2], cmpCard1Str, originalHandStr[2:4], cmpCard2Str), boardStr, "", iters)
	# play [C_1, C2*] against [C_2, C1*]
	res2 = calc("%s%s:%s%s" % (originalHandStr[0:2], cmpCard2Str, originalHandStr[2:4], cmpCard1Str), boardStr, "", iters)

	# determine which card is stronger, and should be kept
	C1_scores = [res1.ev[0], res2.ev[0]] # the EVs for hands where we KEPT C1
	C2_scores = [res1.ev[1], res2.ev[1]] # the EVs for hands where we KEPT C2

	print C1_scores
	print C2_scores

	avgC1Score = mean(C1_scores) + highcard_weight * (hand[0].rank-hand[1].rank)
	avgC2Score = mean(C2_scores) + highcard_weight * (hand[1].rank-hand[0].rank)

	if avgC1Score > avgC2Score: # C1 is better to keep
		keepCard = 0
	else:
		keepCard = 1

	return keepCard


def determineBestDiscardFast(hand, board, min_improvement=0.05, iters=100):
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

# DEFINE THINGS #
FULL_DECK = buildFullDeck()
CUMULATIVE_REGRETS = {}
CUMULATIVE_STRATEGY = {}
EPSILON = 0.05
TAU = 1000
BETA = 10e6
HAND_STRENGTH_ITERS = 1000
BB=2
SB=1
STARTING_STACK=200
# END DEFINITIONS #



class History(object):
	"""
	Gets passed down a game tree.
	"""
	def __init__(self, history, node_type, current_street, current_round, button_player, dealer, \
					active_player, pot, p1_inpot, p2_inpot, bank_1, bank_2, p1_hand, p2_hand, board):
		"""
		history: a list of strings representing the history of actions so far
		node_type: (0,1,2)for chance, action, or terminal
		current_street: (0,1,2,3) for preflop, flop, turn, or river
		current_round: a string representing the round within the current street (B1=betting1, D=discard, etc)
		button_player: (0,1) the player who has the button (has the SB, acts first before flop, second after flop)
		dealer: a Dealer object, which will contain the deck at the current moment in history
		active_player: the player whose move it is (0,1)

		p1_inpot: the amount that P1 has contributed to the CURRENT betting round
		p2_inpot: the amount that P2 has contributed to the CURRENT betting round
		"""
		self.History = history
		self.NodeType = node_type
		self.Street = current_street
		self.Round = current_round
		self.ButtonPlayer = button_player
		self.Dealer = dealer
		self.ActivePlayer = active_player
		self.Pot = pot
		self.P1_inPot = p1_inpot
		self.P2_inPot = p2_inpot
		self.P1_Bankroll = bank_1
		self.P2_Bankroll = bank_2
		self.P1_Hand = p1_hand
		self.P2_Hand = p2_hand
		self.Board = board

	def printAttr(self):
		"""
		Prints all the attributes out of the current history.
		"""
		print "HISTORY:", self.History
		print "NODETYPE:%d STREET:%d ROUND:%s" % (self.NodeType, self.Street, self.Round)
		print "ACTIVE PLAYER:%d SB:%d" % (self.ActivePlayer, self.ButtonPlayer)
		print "POT:%d P1_INPOT:%d P2_INPOT:%d" % (self.Pot, self.P1_inPot, self.P2_inPot)
		print "P1_BANK:%d P2_BANK:%d" % (self.P1_Bankroll, self.P2_Bankroll)
		print "P1_HAND:%s P2_HAND:%s BOARD:%s" % (convertSyntax(self.P1_Hand), convertSyntax(self.P2_Hand), convertSyntax(self.Board))


	def getLegalActions(self):
		"""
		Gets the legal actions available at this point in the game (current history object)
		"""
		assert self.NodeType == 1, "Error: trying to get legal actions for a non-action node!"

		# IF WE ARE AT A DISCARD ACTION NODE
		if self.Street == 1 or self.Street == 2 and self.Round == "D": # flop/turn, and we have the option to discard
			return ["CHECK", "DISCARD:0", "DISCARD:1"]

		# ELSE THIS IS A BETTING ACTION NODE
		else:
			# determine if there was a bet already during this round
			prevBetAmt = abs(self.P1_inPot-self.P2_inPot)

			# if there have already been 3 betting rounds, end the betting with either fold or call
			if self.Round == "B3":
				assert prevBetAmt > 0, "Error: previous bet amount must have been > 0 to reach B3"
				actions = ["FOLD", "CALL"]

			else: #B1 or B2

				# if no bets yet: we can check, bet half-pot, bet pot, or go all-in
				if prevBetAmt==0:
					actions = ["CHECK", "BET:H", "BET:P", "BET:A"]

				# if a bet HAS been placed during this round: we can fold, call, raise by pot, or raise by all-in amount
				if prevBetAmt > 0:
					actions = ["FOLD", "CALL", "RAISE:P", "RAISE:A"]

				# remove any bets (besides all-in) that would make us or the opponent pot-committed
				if (float(self.Pot) / 2) > self.P1_Bankroll*0.6 or (float(self.Pot) / 2) > self.P2_Bankroll*0.6:
					actions.remove("BET:P")
					if "BET:H" in actions: actions.remove("BET:H")

		return actions


	def simulateAction(self, action):
		"""
		Appends the given action to the current history, advancing the game forward.
		Returns: a History object that represents the advanced game history
		"""
		# create a copy of the current history, which will be advanced forward
		newHistory = deepcopy(self)

		# double check that this action is actually allowed
		assert action in self.getLegalActions(), "Error: tried to simulate an action that is not allowed."

		# BASIC ACTIONS
		if action=="FOLD":
			newHistory.NodeType = 2 # the advanced node will be terminal
			

		elif action=="CHECK":
			# see if check was during a discard round OR betting round
			if self.Round == "D":
				# if the active player is the LAST to act, we move on to betting
				# else, we remain in the discard round for the next player
				newHistory.Round = "B1" if self.ActivePlayer==self.ButtonPlayer else "D"

			else: # betting round
				# preflop if the bb checks, the betting round is over
				if self.Street == 0:
					if self.ActivePlayer != self.ButtonPlayer: # if the BB checks
						newHistory.Street += 1
						newHistory.NodeType = 0
						newHistory.Round = "0"

				# if the player is the second to act and checks, then the betting round is over
				else: 
					if self.ActivePlayer == self.ButtonPlayer:
						newHistory.Street += 1
						# if we're finishing the river, then we've reachd a terminal node
						# else, next up is a chance node 
						newHistory.NodeType = 2 if self.Street == 4 else 0
						newHistory.Round = "0"

					else: # the player was first to act, so we just go to the next player without making many changes
						pass


		elif action=="CALL":

			if self.Street != 0: # if not preflop, a call ends the current betting round
				newHistory.NodeType = 2 if self.Street == 4 else 0
				newHistory.Street += 1

			else: # during preflop, calling is more complicated
				# if call is during B1, betting continues (SB called the BB)
				if self.Round == "B1":
					newHistory.NodeType = 1
					
				else: # otherwise, calling ends the betting round, so advance the street and go to a chance node
					newHistory.Street += 1
					newHistory.NodeType = 0


			# this is the amount a player must add to call
			prevBetAmt = abs(self.P1_inPot-self.P2_inPot)

			if self.ActivePlayer==0:
				assert self.P1_inPot < self.P2_inPot, "Error: P1 is calling but does not have less in the pot than P2"
				newHistory.P1_Bankroll -= prevBetAmt
				newHistory.P1_inPot += prevBetAmt
				newHistory.Pot += prevBetAmt

			else:
				assert self.P2_inPot < self.P1_inPot, "Error: P2 is calling but does not have less in the pot than P1"
				newHistory.P2_Bankroll -= prevBetAmt
				newHistory.P2_inPot += prevBetAmt
				newHistory.Pot += prevBetAmt
			

		else: # PARSED ACTIONS

			parsedAction = action.split(":")
			assert len(parsedAction) == 2, "Error: Parsed actions should contain exactly 2 items i.e BET:2 or DISCARD:Ah!"

			# DISCARD
			if parsedAction[0] == "DISCARD":
				# replace the card at the correct index with a new one from the dealer
				if self.ActivePlayer==0:
					newHistory.P1_Hand[parsedAction[1]] = newHistory.Dealer.dealCard()
				else:
					newHistory.P2_Hand[parsedAction[1]] = newHistory.Dealer.dealCard()

				# if the second-to-act player just discarded, go to betting round
				newHistory.Round = "B1" if self.ActivePlayer==self.ButtonPlayer else "D"

			# BETTING
			else:
				# determine betting range
				prevBetAmt = abs(self.P1_inPot-self.P2_inPot)

				# minBet/Raise is the same for both players
				minBet=max(2, prevBetAmt) # min bet is at least a BB (2)
				minRaise=self.P1_inPot+self.P2_inPot+minBet
				
				if self.ActivePlayer==0:
					maxBet=self.P1_Bankroll
					maxRaise=self.P1_inPot+self.P2_inPot+self.P1_Bankroll # current street pot + P1's bankroll		
				else:
					maxBet=self.P2_Bankroll
					maxRaise=self.P1_inPot+self.P2_inPot+self.P2_Bankroll # current street pot + P1's bankroll

				# convert H, P, and A into integer bet amounts
				if parsedAction[1]=="H": # half pot bet
					halfPot = int(float(self.Pot) / 2)
					if halfPot >= minBet and halfPot <= maxBet:
						betAmount = halfPot
					else: # choose the minBet or maxBet, depending on which is closer to the half pot
						betAmount = minBet if (float(halfPot) / minBet <= float(maxBet) / halfPot) else maxBet

				elif parsedAction[1]=="P": # full pot bet
					fullPot = self.Pot
					# if full pot bet is allowed, do that, otherwise put in as much as possible
					betAmount = fullPot if (fullPot <= maxBet) else maxBet

				elif parsedAction[1]=="A": # all in bet
					betAmount = maxBet # the max bet always corresponds to going all in

				else:
					assert False, "The active player gave a bet/raise amount that was not H,P, or A"


				if parsedAction[0] == "BET":
					assert P1_inPot==P2_inPot, "Error: if betting, P1 and P2 should have same amount in pot before bet!"

					if self.ActivePlayer==0: # P1 bets
						newHistory.P1_Bankroll -= betAmount
						newHistory.P1_inPot += betAmount
						newHistory.Pot += betAmount

					else: # P2 bets
						newHistory.P2_Bankroll -= betAmount
						newHistory.P2_inPot += betAmount
						newHistory.Pot += betAmount

					# advance to next betting round
					newHistory.Round = "B%s" % str(int(self.Round[1])+1)

				elif parsedAction[0] == "RAISE":
					assert P1_inPot != P2_inPot, "Error: if raising, P1 and P2 should have unequal amounts in pot"

					# we have to call the previous bet AND add the betAmount on top of that
					raiseAmount = prevBetAmt + betAmount
					if self.ActivePlayer == 0: # P1 raising
						newHistory.P1_Bankroll -= raiseAmount
						newHistory.P1_inPot += raiseAmount
						newHistory.Pot += raiseAmount

					else: # P2 raising
						newHistory.P2_Bankroll -= raiseAmount
						newHistory.P2_inPot += raiseAmount
						newHistory.Pot += raiseAmount

					# advance to next betting round
					newHistory.Round = "B%s" % str(int(self.Round[1])+1)

				else:
					print "Error: submitted an action that didn't fall into any category!"


		# if we entered a new street, reset the inPot values
		if newHistory.Street > self.Street:
			newHistory.P1_inPot = 0
			newHistory.P2_inPot = 0
		
		# append the action we just simulated to the history list
		newHistory.History.append("%s:%s" % (str(self.ActivePlayer), action))

		# alternate to the next player for an action
		newHistory.ActivePlayer = (self.ActivePlayer + 1) % 2

		# finally, return the new history
		return newHistory


	def simulateChance(self):
		"""
		Simulates chance actions automatically for preflop/flop/turn/river.
		"""
		assert self.NodeType == 0, "Error: trying to simulate a chance event for a non-chance node!"
		# we make a copy of the current history, and modify it to be returned
		newHistory = deepcopy(self)

		if self.Street == 0: # preflop
			newHistory.P1_Hand = newHistory.Dealer.dealHand()
			newHistory.P2_Hand = newHistory.Dealer.dealHand()
			newHistory.Round = "B1" # betting round 1 is next

			# also, put in the bb and sb
			if self.ButtonPlayer==0:
				newHistory.P1_Bankroll -= 1
				newHistory.P1_inPot += 1
				newHistory.P2_Bankroll -= 2
				newHistory.P2_inPot += 2
			else:
				newHistory.P2_Bankroll -= 1
				newHistory.P2_inPot += 1
				newHistory.P1_Bankroll -= 2
				newHistory.P1_inPot += 2
			newHistory.Pot = 3


		elif self.Street == 1:
			if self.Round == "0": # start of street, dealer should deal flop
				newHistory.Board = newHistory.Dealer.dealFlop()
				newHistory.Round = "D" # discard round is next

		elif self.Street == 2:
			if self.Round == "0": # start of street, dealer should add a card for turn
				newHistory.Board.append(newHistory.Dealer.dealCard())
				newHistory.Round = "D" # discard round is next

		elif self.Street == 3: # river, add a card
			newHistory.Board.append(newHistory.Dealer.dealCard())
			newHistory.Round = "B1" # betting round 1 is next

		newHistory.NodeType = 1 # an action node always follows a chance node
		return newHistory



def testHistory():
	"""
	(history, node_type, current_street, current_round, button_player, dealer, \
					active_player, pot, p1_inpot, p2_inpot, bank_1, bank_2, p1_hand, p2_hand, board)
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
		else:
			print "ERROR, not recognized nodetype"

	print "------TERMINAL NODE REACHED------"
	print h.printAttr()



testHistory()







"""
Validation and efficiency tests for many of the functions in cfr.py
"""

def testHandStrengthFunctions():
	"""

	"""
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


def determineBestDiscard2(hand, board, min_improvement=0.05, iters=100):
	"""
	Given a hand and either a flop or turn board, returns whether the player should discard, and if so, which card they should choose.
	hand: a list of Card objects
	board: a list of Card objects
	"""
	originalHandStr = convertSyntax(hand)
	boardstr = convertSyntax(board)

	neutral_deck = []
	for c in FULL_DECK:
		if c in board or c in hand:
			continue
		else:
			neutral_deck.append(c)

	shuffle(neutral_deck)

	# using neutral deck, choosing an intermediary hand that we can compare to
	cmp_hand1 = neutral_deck[0:2]
	cmp_hand2 = neutral_deck[2:4]
	cmp_hand3 = neutral_deck[4:6]
	cmp_hand4 = neutral_deck[6:8]


	cmp_hand_str1 = convertSyntax(cmp_hand1)
	cmp_hand_str2 = convertSyntax(cmp_hand2)
	cmp_hand_str3 = convertSyntax(cmp_hand3)
	cmp_hand_str4 = convertSyntax(cmp_hand4)

	cmp_hand_strs = [cmp_hand_str1, cmp_hand_str2, cmp_hand_str3, cmp_hand_str4]

	EV_VS_ORIGINAL_HAND_LIST = [calc(originalHandStr + ":" + cmp_hand_str1, boardstr, "", 500).ev[0],
								calc(originalHandStr + ":" + cmp_hand_str2, boardstr, "", 500).ev[0],
								calc(originalHandStr + ":" + cmp_hand_str3, boardstr, "", 500).ev[0],
								calc(originalHandStr + ":" + cmp_hand_str4, boardstr, "", 500).ev[0]]


	avgSwapFirstEVList = []
	avgSwapSecondEVList = []

	for chs in cmp_hand_strs:
		swapFirstEVSum = 0
		swapSecondEVSum = 0
		numCards = 0
		for i in range(8, len(neutral_deck)):

			cardstr = convertSyntax(neutral_deck[i])

			# compare original hand to the hand made by replacing first card with CARD
			swapFirstStr = "%s%s:%s" % (cardstr,originalHandStr[2:4],chs)

			# compare original hand to the hand made by replacing second card with CARD
			swapSecondStr = "%s%s:%s" % (originalHandStr[0:2],cardstr,chs)

			swap_first_res = calc(swapFirstStr, boardstr, "", iters)
			swap_second_res = calc(swapSecondStr, boardstr, "", iters)

			# increment
			numCards += 1

			swapFirstEVSum += swap_first_res.ev[0]
			swapSecondEVSum += swap_second_res.ev[0]


		# calculate the average EV of swapping first and second when we play them against the original hand
		avgSwapFirstEVList.append(float(swapFirstEVSum) / numCards)
		avgSwapSecondEVList.append(float(swapSecondEVSum) / numCards)

	print avgSwapFirstEVList
	print avgSwapSecondEVList

	# we have 3 comparison hands
	# computed the average EV if we swap the first card vs. each comparison hand
	# computed the avg EV if we swap the second card vs. each comparison hand 

	if (float(sum(avgSwapFirstEVList)) / 4) > (float(sum(avgSwapSecondEVList)) / 4):
		bestDiscard = 0
	else:
		bestDiscard = 1

	if bestDiscard==0:
		beatsum = 0
		if avgSwapFirstEVList[0]>EV_VS_ORIGINAL_HAND_LIST[0]:
			beatsum += 1
		if avgSwapFirstEVList[1]>EV_VS_ORIGINAL_HAND_LIST[1]:
			beatsum += 1
		if avgSwapFirstEVList[2]>EV_VS_ORIGINAL_HAND_LIST[2]:
			beatsum += 1
		if avgSwapFirstEVList[3] > EV_VS_ORIGINAL_HAND_LIST[3]:
			beatsum += 1

		if beatsum >= 3:
			return (True, 0.5, 0)
		else:
			return(False,0,None)
	else:
		beatsum=0
		if avgSwapSecondEVList[0]>EV_VS_ORIGINAL_HAND_LIST[0]:
			beatsum += 1
		if avgSwapSecondEVList[1]>EV_VS_ORIGINAL_HAND_LIST[1]:
			beatsum += 1
		if avgSwapSecondEVList[2]>EV_VS_ORIGINAL_HAND_LIST[2]:
			beatsum += 1
		if avgSwapSecondEVList[3] > EV_VS_ORIGINAL_HAND_LIST[3]:
			beatsum += 1

		if beatsum >=3:
			return (True, 0.5, 1)
		else:
			return (False, 0, None)




def determineBestDiscardSampled(hand, board, min_improvement=0.1, iters=50, num_cards_to_sample=25):
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

	for sample in range(num_cards_to_sample):
		card = choice(FULL_DECK)
		if card in board or card in hand:
			continue
		else:
			# increment
			numCards += 1

			cardstr = convertSyntax(card)+":xx"

			# compare original hand to the hand made by replacing first card with CARD
			swapFirstStr = originalHandStr[2:4]+cardstr

			# compare original hand to the hand made by replacing second card with CARD
			swapSecondStr = originalHandStr[0:2]+cardstr

			time0=time.time()
			swapFirstEVSum += calc(swapFirstStr, boardstr, "", iters).ev[0]
			swapSecondEVSum += calc(swapSecondStr, boardstr, "", iters).ev[0]
			time1=time.time()
			#print time1-time0

	# calculate the average EV of swapping first and second when we play them against the original hand
	avgSwapFirstEV = float(swapFirstEVSum) / numCards
	avgSwapSecondEV = float(swapSecondEVSum) / numCards

	# if either swap increases EV by more than 5%
	if avgSwapFirstEV > originalHandEV+min_improvement or avgSwapSecondEV > originalHandEV+min_improvement:
		if avgSwapFirstEV > avgSwapSecondEV:
			return (True, avgSwapFirstEV, 0, originalHandEV)
		else:
			return (True, avgSwapSecondEV, 1, originalHandEV)
	else:
		return (False, 0, None)



def testDiscard():
	"""
	T/F Different: 0.136
	Card disagrees: 0.202
	"""
	bool_disagrees = 0
	card_disagrees = 0
	for i in range(100):
		print(i)
		d = Dealer()
		hand = d.dealHand()
		flop = d.dealFlop()
		print hand
		print flop

		time0 = time.time()
		exhaustive = determineBestDiscard(hand,flop)
		print "Exhaustive:", exhaustive
		time1 = time.time()
		print "Time:", time1-time0

		time2 = time.time()
		playoff = determineShouldDiscard(hand,flop)
		time3 = time.time()
		print sampled
		print "Time:", time3-time2

		if exhaustive[0] != sampled[0]:
			bool_disagrees += 1
		elif exhaustive[2] != sampled[2]:
			card_disagrees += 1

	print "T/F Different:", float(bool_disagrees) / 100
	print "Card disagrees:", float(card_disagrees) / 100



def testDetermineDiscard():

	bool_disagrees = 0
	card_disagrees = 0

	for i in range(500):

		assert len(FULL_DECK)==52, "Full deck is depleted!"
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
			print "------------------ BOOL DISAGREES --------------------"
		elif exhaustive[1] != fast[1]:
			card_disagrees += 1
			print "------------------ CARD DISAGREES --------------------"

	print "T/F Different:", float(bool_disagrees) / 500
	print "Card disagrees:", float(card_disagrees) / 500

#testDetermineDiscard()

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


def testDetermineWinner():
	"""
	Experimentally determined that about 4% of hands end in a tie.
	"""
	tie_ctr = 0
	iters = 10000
	for i in range(iters):
		d = Dealer()
		p1_hand = d.dealHand()
		p2_hand = d.dealHand()

		board = d.dealFlop()
		board.append(d.dealCard())
		board.append(d.dealCard())

		winner = determineWinner(p1_hand, p2_hand, board)
		print "P1: ", p1_hand, "P2: ", p2_hand, "Board: ", board

		if winner == 3:
			tie_ctr += 1
			print "TIE"
		else:
			print "Winner: ", winner

		print " -------- "

	print "%f percent of hands resulted in ties" % (float(tie_ctr) / iters)


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
	h.printAttr()


def testHistoryRandom():
	"""
	Randomly choose actions from the game engine to try to find every edge case possible

	(history, node_type, current_street, current_round, button_player, dealer, \
					active_player, pot, p1_inpot, p2_inpot, bank_1, bank_2, p1_hand, p2_hand, board)
	"""
	num_simulations = 1000
	sb_player = 0

	time0 = time.time()
	for i in range(num_simulations):

		if i % 10 == 0:
			print i
		#print "############# HAND:", i, "###############"

		initialDealer = Dealer()
		h = History([], 0, 0, 0, sb_player, initialDealer, sb_player, 0, 0, 0, 200, 200, [], [], [])

		while(h.NodeType != 2): # while not terminal, simulate
			if h.NodeType == 0:
				#h.printAttr()
				h = h.simulateChance()
			elif h.NodeType == 1:
				#h.printAttr()
				actions = h.getLegalActions()
				#print "Legal Actions:", actions

				action = choice(actions)
				#print "Choosing action:", action
				h = h.simulateAction(action)
			
			else:
				assert False, "Not recognized node type"

		#print "End of hand ----------"
		#h.printAttr()

		sb_player = (sb_player+1) % 2 # alternate sb players each time

	time1 = time.time()
	print "Simulated", num_simulations, "hands in", time1-time0, "secs"


# def determineBestCardToKeep(hand, board, iters=1000):
# 	"""
# 	Given a hand and either a flop or turn board, returns whether the player should discard, and if so, which card they should choose.
# 	hand: a list of Card objects
# 	board: a list of Card objects
# 	"""
# 	originalHandStr = convertSyntax(hand)
# 	boardStr = convertSyntax(board)

# 	# create a neutral deck that does not contain any cards from the hand or board
# 	neutralDeck = []
# 	for card in FULL_DECK:
# 		if card in board or card in hand:
# 			continue
# 		else:
# 			neutralDeck.append(card)

# 	# shuffle so that we can pop random cards off of top
# 	shuffle(neutralDeck)

# 	# get two comparison cards that will be swapped
	
# 	cmpCard1 = neutralDeck.pop(0)

# 	# note: we make sure that these comparison cards are not the same rank as either card in our hand!
# 	while cmpCard1.rank==hand[0].rank or cmpCard1.rank==hand[1].rank or cmpCard1.suit==hand[0].suit or cmpCard1.suit==hand[1].suit:
# 		cmpCard1 = neutralDeck.pop(0)

# 	cmpCard2 = neutralDeck.pop(0)
# 	while cmpCard2.rank==hand[0].rank or cmpCard2.rank==hand[1].rank or cmpCard2.suit==hand[0].suit or cmpCard2.suit == hand[1].suit:
# 		cmpCard2 = neutralDeck.pop(0)

# 	cmpCard3 = neutralDeck.pop(0)
# 	while cmpCard3.rank==hand[0].rank or cmpCard3.rank==hand[1].rank or cmpCard3.suit==hand[0].suit or cmpCard3.suit == hand[1].suit:
# 		cmpCard3 = neutralDeck.pop(0)

# 	cmpCard4 = neutralDeck.pop(0)
# 	while cmpCard4.rank==hand[0].rank or cmpCard4.rank==hand[1].rank or cmpCard4.suit==hand[0].suit or cmpCard4.suit == hand[1].suit:
# 		cmpCard4 = neutralDeck.pop(0)
# 	# now we have 2 "neutral" comparison cards
# 	cmpCard1Str = convertSyntax(cmpCard1)
# 	cmpCard2Str = convertSyntax(cmpCard2)
# 	cmpCard3Str = convertSyntax(cmpCard3)
# 	cmpCard4Str = convertSyntax(cmpCard4)

# 	# play [C_1, C1*] against [C_2, C2*]
# 	res1 = calc("%s%s:%s%s" % (originalHandStr[0:2], cmpCard1Str, originalHandStr[2:4], cmpCard2Str), boardStr, "", iters)
# 	# play [C_1, C2*] against [C_2, C1*]
# 	res2 = calc("%s%s:%s%s" % (originalHandStr[0:2], cmpCard2Str, originalHandStr[2:4], cmpCard1Str), boardStr, "", iters)

# 	res3 = calc("%s%s:%s%s" % (originalHandStr[0:2], cmpCard3Str, originalHandStr[2:4], cmpCard4Str), boardStr, "", iters)

# 	res4 = calc("%s%s:%s%s" % (originalHandStr[0:2], cmpCard4Str, originalHandStr[2:4], cmpCard3Str), boardStr, "", iters)

# 	# determine which card is stronger, and should be kept
# 	C1_scores = [res1.ev[0], res2.ev[0], res3.ev[0], res4.ev[0]] # the EVs for hands where we KEPT C1
# 	C2_scores = [res1.ev[1], res2.ev[1], res3.ev[1], res4.ev[1]] # the EVs for hands where we KEPT C2

# 	# keepCard = None
# 	# if C1_scores[0] > C2_scores[0] and C1_scores[1] > C2_scores[1]: # C1 is clearly better to keep (won in both cases)
# 	# 	keepCard = 0
# 	# elif C2_scores[0] > C1_scores[0] and C2_scores[1] > C1_scores[1]: # C2 is clearly better to keep
# 	# 	keepCard = 1

# 	# else: # C1 and C2 are somewhat close in their value to keep

# 	avgC1Score = mean(C1_scores)
# 	avgC2Score = mean(C2_scores)

# 	if avgC1Score > avgC2Score: # C1 is better to keep
# 		keepCard = 0
# 	else:
# 		keepCard = 1

# 	return keepCard


#testDiscard()

# d = Dealer()
# hand = d.dealHand()
# flop = d.dealFlop()
# deck = d.getCurrentDeck()
# flop.append(d.dealCard())
# flop.append(d.dealCard())

# time0 = time.time()
# hss = getRiverHSS(hand,flop)
# time1 = time.time()
# print time1-time0
# print hss

# # time0 = time.time()
# # hss = getPreflopHSS(hand)
# # time1 = time.time()
# # print hand
# # print time1-time0
# # print hss

#writeFlopHandStrengthSquaredFile()
#writeRiverHandStrengthFile()
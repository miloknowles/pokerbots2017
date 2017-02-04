#!/usr/bin/env 


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

	num_samples = 10
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


def getHandStrengthSampled(hand, board, deck):
	t0 = time.time()
	assert len(hand) + len(board) <= 7, "Error: hand cannot have more than 7 cards."
	assert len(hand) + len(board) + len(deck) == 52, "Error: hand and deck should add up to 52 cards"

	numCardsToSample = 5 - len(board)

	num_samples = 500
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
		handStrengthSum += HandEvaluator.evaluate_hand(hand,board+c)

	avgHandStrength = float(handStrengthSum) / numCombsConsidered
	t1 = time.time()
	#print(t1-t0)
	return avgHandStrength


def getPreflopHSS(hand):
	"""
	Gets preflop HSS values from lookup table (hss_preflop.txt)
	"""
	# this sort works because card1 is guaranteed to be <= the rank of card2 in lookup tables
	hand = sorted(hand, key=attrgetter('rank','suit'))
	handstr = str(hand[0]) + str(hand[1])
	handstr = handstr.replace('<Card(', '')
	handstr = handstr.replace(')>', '')
	with open('hss_preflop.txt') as f:
		for line in f:
			if handstr[0]==line[0]:
				if handstr[1]==line[1]:
					if handstr==line[0:4]:
						hss = float(line.split(":")[1])
						f.close()
						return hss
	f.close()
	return None


def writePreflopHandStrengthSquaredFile():
	"""
	Creates a text file that contains every hand (two cards) and it's HSS value with sampling.
	"""
	time0 = time.time()
	deck = buildFullDeck()
	hands = combinations(deck, 2)

	with open('hss_preflop2.txt', 'w') as f:
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
			handstr = handstr.replace('<Card(', '')
			handstr = handstr.replace(')>', '')

			f.write(handstr+":"+str(hss_sampled)+"\n")
			f.flush()
	
	time1 = time.time()
	print "Took", time1-time0, "secs"
	f.close()


def writeRiverHandStrengthFile():
	"""
	Writes a file to directory /rank1/rank2/rank3/rank4/rank5/hand.txt
	"""
	time0 = time.time()
	deck = buildFullDeck()
	boards = combinations(deck,5)
	counter = 0
	for b in boards:
		b = list(b)
		board_start_time = time.time()
		counter += 1
		print "Working on board", counter

		# navigate to correct folder
		boardstr = str(b[0]) + str(b[1]) + str(b[2]) + str(b[3]) + str(b[4])
		boardstr = boardstr.replace('<Card(', '')
		boardstr = boardstr.replace(')>', '')
		path = './hs_river/%s/%s/%s/%s/%s' % (boardstr[0],boardstr[2],boardstr[4],boardstr[6],boardstr[8])

		filename = boardstr+".txt"

		# if we haven't been in this folder before, create it
		if not os.path.isdir(path):
			os.makedirs(path)

		with open(path+filename, 'w') as f:
			f.write("BOARD: " + boardstr + "\n")
			new_deck = []
			for card in deck:
				if card not in b:
					new_deck.append(card)

			#now we have a deck with cards from board removed
			hands = list(combinations(new_deck, 2))
			assert len(hands) == 1081, "Error: should be 1081 hands"

			for h in hands:
				h = list(h)

				current_deck = new_deck[:]
				current_deck.remove(h[0])
				current_deck.remove(h[1])

				hs = HandEvaluator.evaluate_hand(h,b)
				handstr = str(h[0]) + str(h[1])
				handstr = handstr.replace('<Card(', '')
				handstr = handstr.replace(')>', '')
				f.write(handstr+":"+str(hs)[0:5]+"\n")
				f.flush()
			f.close()
		board_end_time = time.time()
		print "Board took", board_end_time-board_start_time, "secs"

	time_end = time.time()
	print "Overall took", time_end-time0, "secs"


def writeFlopHandStrengthSquaredFile():
	time0 = time.time()
	deck = buildFullDeck()
	boards = combinations(deck,3)
	counter = 0
	for b in boards:
		b = list(b)
		board_start_time = time.time()
		counter += 1
		print "Working on board", counter

		# navigate to correct folder
		boardstr = str(b[0]) + str(b[1]) + str(b[2])
		boardstr = boardstr.replace('<Card(', '')
		boardstr = boardstr.replace(')>', '')
		path = './hss_flop/%s/%s/%s/' % (boardstr[0],boardstr[2],boardstr[4])

		filename = boardstr+".txt"

		# if we haven't been in this folder before, create it
		if not os.path.isdir(path):
			os.makedirs(path)

		with open(path+filename, 'w') as f:
			f.write("BOARD: " + boardstr + "\n")
			new_deck = []
			for card in deck:
				if card not in b:
					new_deck.append(card)

			#now we have a deck with cards from board removed
			hands = list(combinations(new_deck, 2))
			assert len(hands) == 1176, "Error: should be 1176 hands"

			for h in hands:
				h = list(h)

				current_deck = new_deck[:]
				current_deck.remove(h[0])
				current_deck.remove(h[1])

				hss_sampled = getHandStrengthSquaredSampled(h, b, current_deck)
				handstr = str(h[0]) + str(h[1])
				handstr = handstr.replace('<Card(', '')
				handstr = handstr.replace(')>', '')
				f.write(handstr+":"+str(hss_sampled)[0:5]+"\n")
				f.flush()
			f.close()
		board_end_time = time.time()
		print "Board took", board_end_time-board_start_time, "secs"

	time_end = time.time()
	print "Overall took", time_end-time0, "secs"


def writePreflopHandStrengthFile():
	time0 = time.time()
	deck = buildFullDeck()
	hands = combinations(deck, 2)

	with open('hand_strength_preflop.txt', 'w') as f:
		counter = 0
		for h in hands:
			counter += 1
			print "Working on hand", counter
			hand = list(h)
			current_deck = deck[:]
			current_deck.remove(hand[0])
			current_deck.remove(hand[1])
			hss_sampled = getHandStrengthSampled(h, [], current_deck)

			handstr = str(hand[0]) + str(hand[1])
			handstr = handstr.replace('<Card(', '')
			handstr = handstr.replace(')>', '')

			f.write(handstr+":"+str(hss_sampled)+"\n")
			f.flush()
	
	time1 = time.time()
	print "Took", time1-time0, "secs"
	f.close()


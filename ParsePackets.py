#!/usr/bin/env
from pokereval.card import Card


# mappings used by the NEWHAND class
rankDict = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, 'T':10, 'J':11, 'Q':12, 'K':13, 'A':14}
suitDict = {'s': 1, 'h': 2, 'd': 3, 'c': 4}


def convertToCard(card_str):
    """
    Takes a card string (i.e Kd Th 8c), and converts to a Card object
    """
    card = Card(rankDict[card_str[0]], suitDict[card_str[1]])
    return card


class NEWGAME(object):
    """
    Used to parse the data from a NEWGAME packet
    See: http://mitpokerbots.com/docs/grammar.html`

    NEWGAME yourName opp1Name stackSize bb numHands timeBank
    NEWGAME pysamplebot test2 200 2 100 10.000000
    """
    def __init__(self, data):
        itemized = data.split(" ")

        self.type = itemized[0]
        assert(self.type=="NEWGAME")

        self.ourName = itemized[1]
        self.oppName = itemized[2]
        self.stackSize = int(itemized[3]) # number of chips we have at start of game
        self.bb = int(itemized[4]) # big blind amount being used for the game (guaranteed multiple of 2)
        self.numHands = int(itemized[5]) # max number of hands to be played in this match
        self.timeBank = float(itemized[6]) # number of seconds left for our bot to return an action


class NEWHAND(object):
    """

    Used to parse the data from a NEWHAND packet
    See: http://mitpokerbots.com/docs/grammar.html

    NEWHAND handId button holeCard1 holeCard2 myBank otherBank timeBank
    NEWHAND 4 false 5c Ad -1 1 9.994724
    """
    def __init__(self, data):
        itemized = data.split(" ")

        self.type = itemized[0]
        assert(self.type=="NEWHAND")

        self.handID = int(itemized[1])
        self.button = itemized[2]
        self.hand = [itemized[3], itemized[4]] # stores as card strings
        self.myBank = int(itemized[5])
        self.oppBank = int(itemized[6])
        self.timeBank = float(itemized[7])

    def getHand(self):
        """
        Returns the hand as card objects.
        """
        hand = []
        hand.append(convertToCard(self.hand[0]))
        hand.append(convertToCard(self.hand[1]))
        return hand


       
class GETACTION(object):
    """
    Used to parse the data from a GETACTION packet
    For packet sections of variable length, uses for loops
    See: http://mitpokerbots.com/docs/grammar.html

    GETACTION potSize numBoardCards [boardCards] numLastActions [lastActions] numLegalActions [legalActions] timebank
    GETACTION 3 0 2 POST:1:pysamplebot POST:2:test2 3 CALL FOLD RAISE:4:200 9.994723895
    """
    def __init__(self, data):
        itemized = data.split(" ")

        self.type = itemized[0]
        assert(self.type=="GETACTION")

        self.potSize = int(itemized[1])
        self.numBoardCards = int(itemized[2])
        
        parse_index = 3
        self.boardCards = []
        for i in range(self.numBoardCards):
            self.boardCards.append(itemized[parse_index])
            parse_index+=1

        #print "Parse Index for numLast Actions:", parse_index
        self.numLastActions = int(itemized[parse_index])
        parse_index += 1
        
        self.lastActions = []
        for i in range(self.numLastActions):
            self.lastActions.append(itemized[parse_index])
            parse_index +=1

        #print "Parse Index for num Legal Actions:", parse_index
        self.numLegalActions = int(itemized[parse_index])

        self.legalActions = []
        for i in range(self.numLegalActions):
            parse_index += 1
            self.legalActions.append(itemized[parse_index])

    def getBoard(self):
        """
        Returns the board as Card objects
        """
        board = []
        for c in self.boardCards:
            board.append(Card(rankDict[c[0]], suitDict[c[1]]))
        return board

    def getBettingRange(self):
        for a in self.legalActions:
            a_parsed = a.split(':')
            if a_parsed[0] == 'BET':
                minBet = int(a_parsed[1])
                maxBet = int(a_parsed[2])
                return (minBet, maxBet)

    def getRaisingRange(self):
        for a in self.legalActions:
            a_parsed = a.split(':')
            if a_parsed[0] == 'RAISE':
                minRaise = int(a_parsed[1])
                maxRaise = int(a_parsed[2])
                return (minRaise, maxRaise)





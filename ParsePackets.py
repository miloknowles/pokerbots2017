#!/usr/bin/env 

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
        self.stackSize = itemized[3] # number of chips we have at start of game
        self.bb = itemized[4] # big blind amount being used for the game (guaranteed multiple of 2)
        self.numHands = itemized[5] # max number of hands to be played in this match
        self.timeBank = itemized[6] # number of seconds left for our bot to return an action


class NEWHAND:
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

        self.handID = itemized[1]
        self.button = itemized[2]
        self.hand = [itemized[3], itemized[4]]
        self.myBank = itemized[5]
        self.oppBank = itemized[6]
        self.timeBank = itemized[7]

    def getHand(self):
        return self.hand


       
class GETACTION:
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

        self.potSize = itemized[1]
        self.numBoardCards = int(itemized[2])
        
        parse_index = 3
        self.BoardCards = []
        for i in range(self.numBoardCards):
            self.BoardCards.append(itemized[parse_index])
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
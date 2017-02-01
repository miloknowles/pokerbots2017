#!/usr/bin/env 

import argparse
import socket
import sys
import time
from random import random, choice
from pokereval.card import Card
from query_cfr import chooseAction, chooseActionRandom, getStrategy
from cfr import getHandStrength, determineBestDiscardFast, convertHtoI, LightweightHistory, convertSyntax
import json
from ParsePackets import *


# when we get an opponent action, map it into the abstracted space and use a History object to simulate it
# ask the History for legal actions when it's our turn
# deal with discrepancies between History's allowed actions and engine's allowed actions
	# all actions from History should be in engine's allowed actions, but not necessarily other way around
# when we get to a discard, use the History to determine which one?


global NEWGAME_PACKET, NEWHAND_PACKET, GETACTION_PACKET, HISTORY,
CURRENT_ROUND = 0 # chance round

# (self, history, node_type, current_street, current_round, button_player, \
# active_player, pot, p1_inpot, p2_inpot, bank_1, bank_2, p1_hand, p2_hand, board):
HISTORY = LightweightHistory([], 0, 0, 0, 0, 0, 0, 0, 0, 200, 200, [], [], [])


def mapBetToAbstraction(betAmt):
    """
    Given an amount that an opponent bet, determines whether this corresponds to H/P/A
    Note: this is used to map raises also, which still have a "bet" amount associated with their increase over the last bet.
    Returns: H, P, or A (halfpot, pot, or all-in)
    """
    # get legal actions for the opponent based on the actions we've given to history so far
	legalActions = HISTORY.getLegalActions(1) 

    # extract the betting options to consider from the legal options
    betOptions = []
    betOptionAmounts = []
    for a in legalActions:
        parsedAction = a.split(':')

        if parsedAction[0] == 'B' or parsedAction[0] == 'R':
            betOptions.append(parsedAction[1]) # add the string

            # also add to the list of int amounts associated with each string amount
            if parsedAction[1]=='H':
                betOptionAmounts.append(float(HISTORY.Pot) / 2)

            elif parsedAction[1]=='P':
                betOptionAmounts.append(HISTORY.Pot)

            elif parsedAction[1]=='A':

                # a player can never bet/raise to amount greater than their bankroll or the other player's
                allInAmt = min(HISTORY.P1_Bankroll, HISTORY.P2_Bankroll)
                betOptionsAmounts.append(allInAmt)


    assert len(betOptions)>0, "Error: history doesn't think there are any legal betting options"

    # now determine which of the bet options our opponent's betAmt was closest to
    if len(betOptions) == 1:
        return betOptions[0]

    else:
        best_index, best_ratio = 0, float('inf')
        for j in range(len(betOptions)):
            ratio = (float(betAmt)/betOptionAmounts[j] if betAmt>betOptionAmounts[j]) else (float(betOptionAmounts[j])/betAmt)
            
            if ratio < best_ratio:
                best_ratio, best_index = ratio, j
        return betOptions[best_index]


def resetHistory():
    """
    Resets the global HISTORY to defaults.
    """
    global HISTORY
    HISTORY.P1_inPot, HISTORY.p2_inPot, HISTORY.Pot = 0, 0, 0 # reset the in-pot and pot for this street
    HISTORY.ButtonPlayer = 0 if NEWHAND_PACKET.button==True else 1
    HISTORY.P1_Bankroll, HISTORY.P2_Bankroll = 200, 200 # reset both bankrolls to 200
    HISTORY.Street, HISTORY.CurrentRound, HISTORY.NodeType = 0,0,0 # preflop
    HISTORY.P1_Hand, HISTORY.P2_Hand, HISTORY.Board = [], [], []


def handleDiscard(hand, board):
    """
    Decides whether to discard, and which card.
    Returns either "CHECK" or "DISCARD:*card*", which is the action to be sent.
    """
    # first, do a sanity check
    global GETACTION_PACKET
    assert ("DISCARD:%s" % hand[0]) in GETACTION_PACKET.legalActions

    shouldSwap, swapIndex, swapEV, originalEV = determineBestDiscardFast(hand, board)

    if shouldSwap:
        return "DISCARD:%s\n" % hand[swapIndex]
    else:
        return "CHECK\n"


def extractOppActionAndDiscardResult():
    """
    Reads through lastActions in GETACTION_PACKET and updates global information if an opponent betting action was made.
    """
    global GETACTION_PACKET, NEWGAME_PACKET, HISTORY

    for action in GETACTION_PACKET.lastActions:
        parsedAction = a.split(':')

        # note: engine puts action first, and the "actor" as the last item
        if parsedAction[0] == 'BET' or parsedAction[0] == 'RAISE':
            assert (parsedAction[2] == NEWGAME_PACKET.oppName), "Error: expected the opp. betting/raising action to be associated with %s" % NEWGAME_PACKET.oppName

            # increase the Pot, P2_inPot, and update P2_Bankroll
            HISTORY.Pot = GETACTION_PACKET.potSize

            if parsedAction[0]=='BET': # increment the P2_inPot
                betAmount = int(parsedAction[1])

                # TODO: map the bet amount to an action (abstracted)
                oppActionStr = "B:%s" % mapBetToAbstraction(betAmount)
                HISTORY.History.append(oppActionStr)

                # update the history AFTER abstraction determined!!
                HISTORY.P2_inPot += betAmount
                HISTORY.P2_Bankroll -= betAmount


            elif parsedAction[0] == 'RAISE': # P2_inPot should be EQUAL to the amount that they raise 'to'

                callAmount = HISTORY.P2_inPot - HISTORY.P1_inPot # calculate the amount the opponent had to put in to call
                assert callAmount > 0, "Error: expected positive call amount for opponent"

                raiseToAmount = int(parsedAction[1]) # determine amount of money that the opp raised to
                betAmount = raiseToAmount - HISTORY.P1_Bankroll # this is the ammount that the player added on top of calling
                raiseAmount = callAmount + betAmount # the amount to call + the bet amount on top of that

                # TODO: map the raise-to amount to an action (abstracted)
                oppActionStr = "R:%s" % mapBetToAbstraction(betAmount)
                HISTORY.History.append(oppActionStr)

                # update the history AFTER abstraction determined!!
                HISTORY.P2_inPot += raiseAmount
                HISTORY.P2_Bankroll -= raiseAmount

            assert (HISTORY.P1_Bankroll+HISTORY.P2_Bankroll+HISTORY.Pot) == 400, "Error: bankroll's and pot to not match up for oppponent"


        elif parsedAction[0] == 'CALL':
            # update the global history
            callAmount = HISTORY.P1_inPot - HISTORY.P2_inPot # calculate the amount the opponent had to put in to call
            assert callAmount > 0, "Error: expected positive call amount for opponent"
            HISTORY.P2_inPot += callAmount
            HISTORY.P2_Bankroll -= callAmount
            HISTORY.Pot = GETACTION_PACKET.potSize
            HISTORY.History.append('1:CL')

        elif parsedAction[0] == 'CHECK':
            HISTORY.History.append('1:CK')

        elif parsedAction[0] == 'DISCARD':
            # DISCARD:(oldcard):(newcard):PLAYER
            # only append the discard if it was done by the other player
            if parsedAction[3] == NEWGAME_PACKET.oppName:
                HISTORY.History.append('1:D')
            
            else: # our discard
                assert parsedAction[3] == NEWGAME_PACKET.ourName, "Error: expected discard action to be done by us, but instead it was %s" % parsedAction[3]
                
                # update our hand with the new card we received
                old_card, new_card = parsedAction[1], parsedAction[2]
                index = 0 if (old_card==HISTORY.P1_HandStr[0:2]) else 1
                HISTORY.updateHandDiscard(new_card, index)

        elif parsedAction[0] == 'FOLD':
            HISTORY.History.append('1:F')

        elif parsedAction[0] == 'DEAL':
            pass

        else:
            assert False, "Error: encountered unknown opponent action %s from lastActions" % parsedAction[0]


def convertSyntaxToEngine(i_action):
    """
    i_action: an action in the format that the HISTORY object returns them

    Returns the action in a syntax that the engine recognizes.
    Also maps bets to legal integer values.

    Note: this function only works for OUR player!!! Do not use for opponent.
    """
    if i_action=="CK":
        a = "CHECK\n"
    elif i_action=="CL":
        a = "CALL\n"
    elif i_action=="F":
        a = "FOLD\n"
    else: # parsed action
        if i_action[0]=='B':
            # get the legal betting range
            minBet, maxBet = GETACTION_PACKET.getBettingRange()

            # amounts must be between min and max bets
            if i_action[1] == 'H':
                betAmt = max(minBet, min(int(float(HISTORY.Pot) / 2), maxBet))

            elif i_action[1] == 'P':
                betAmt = max(minBet, min(HISTORY.Pot, maxBet))

            elif i_action[1] == 'A':
                betAmt = maxBet

            a = 'BET:%s\n' % str(betAmt)

        elif i_action[0]=='R':

            # get the legal raising range
            minRaise, maxRaise = GETACTION_PACKET.getRaisingRange()

            # amounts must be between min and max raises
            if i_action[1] == 'H':
                betAmt = int(float(HISTORY.Pot) / 2)
                raiseAmt = HISTORY.P2_inPot + betAmt # we raise by betAmt OVER the opponent's current amount in the pot

            elif i_action[1] == 'P':
                betAmt = HISTORY.Pot
                raiseAmt = HISTORY.P2_inPot + betAmt # we raise by betAmt OVER the opponent's current amount in the pot

            elif i_action[1] == 'A':
                raiseAmt = maxRaise

            a = 'RAISE:%s\n' % str(raiseAmt)

    # finally, return the action
    return a



class Player:
    def run(self, input_socket):
        # Get a file-object for reading packets from the socket.
        # Using this ensures that you get exactly one packet per read.
        f_in = input_socket.makefile()
        
        while True:
            # Block until the engine sends us a packet.
            data = f_in.readline().strip()
            # If data is None, connection has closed.
            if not data:
                print "Gameover, engine disconnected."
                break

            print data # print the latest packet

            # determine what type of packet this is
            word = data.split()[0]

            if word == "GETACTION":
                # store the current action information globally
                global GETACTION_PACKET, HISTORY
                GETACTION_PACKET = GETACTION(data)

                # check if we entered a new street
                if "DEAL:FLOP" in GETACTION_PACKET.lastActions:
                	HISTORY.P1_inPot, P2_inPot = 0, 0 # reset the in pot for this street
                    HISTORY.updateBoard(GETACTION_PACKET.getBoard())

            	elif "DEAL:TURN" in GETACTION_PACKET.lastActions:
            		HISTORY.P1_inPot, P2_inPot = 0, 0 # reset the in pot for this street
                    HISTORY.updateBoard(GETACTION_PACKET.getBoard())

            	elif "DEAL:RIVER" in GETACTION_PACKET.lastActions
            		HISTORY.P1_inPot, P2_inPot = 0, 0 # reset the in pot for this street
                    HISTORY.updateBoard(GETACTION_PACKET.getBoard())

                # extract information from the lastActions to update HISTORY
                # this will add opponent actions to the HISTORY list, and update our hand if we discarded
                extractOppActionAndDiscardResult()

                # determine if this is a discard action
                inDiscardSection = False
                parsedLegalActions = [i.split(':') for i in GETACTION_PACKET.legalActions]
                for legalAction in parsedLegalActions:
                    if legalAction[0] == 'DISCARD':
                        inDiscardSection = True
                        break

                # if a discard section
                if inDiscardSection:
                    shouldDiscard, discardIndex, swapEV, originalHandEV = determineBestDiscardFast(HISTORY.P1_Hand, HISTORY.Board)

                    if shouldDiscard:
                        discardAction = 'DISCARD:%s\n' % convertSyntax(HISTORY.P1_Hand[discardIndex])
                        s.send(discardAction)

                    else:
                        s.send('CHECK\n')


                # otherwise, betting action
                else:

                    # convert the current HISTORY to an information set from our perspective
                    playerActions = HISTORY.getLegalActions(0)
                    I_player = convertHtoI(HISTORY, 0)

                    # look up our strategy for the given info. set
                    strategy = getStrategy(I_player)
                    print "I:", I_player
                    print "Strategy:", strategy

                    # if we could find a learned strategy, use it, otherwise choose randomly from available actions
                    action_i = chooseActionRandom(player_actions) if s==None else chooseAction(strategy)

                    # convert actions to HISTORY list syntax to get appended
                    if action_i[0]=='B' or action_i[0]=='R':
                        action_h = "0:%s:%s" % (action_i[0], action_i[1])
                    else: # just add the player 0 tag to the beginning of the action
                        action_h = "0:%s" % action_i
                    HISTORY.History.append(action_h)

                    # convert the action we chose to syntax compatible with the engine
                    # bet amounts like H/P/A are converted to integer values
                    action_e = convertSyntaxToEngine(action_h)
                    s.send(action_e)


            elif word=="NEWGAME":

                # store game information globally
            	global NEWGAME_PACKET
                NEWGAME_PACKET = NEWGAME(data)

                # just in case
                resetHistory()


            elif word=="NEWHAND":

                # update the global NEWHAND packet
            	global NEWHAND_PACKET
                NEWHAND_PACKET = NEWHAND(data)

                # update the player's hand in the HISTORY
                # doing so will also automatically append the right item to the HISTORY list
                HISTORY.updateHand(NEWHAND_PACKET.getHand())

                # reset the global HISTORY to defaults for the start of a hand
                resetHistory()

            elif word == "REQUESTKEYVALUES":
                # At the end, the engine will allow your bot save key/value pairs.
                # Send FINISH to indicate you're done.
                s.send("FINISH\n")

        # Clean up the socket.
        s.close()



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='A Pokerbot.', add_help=False, prog='pokerbot')
    parser.add_argument('-h', dest='host', type=str, default='localhost', help='Host to connect to, defaults to localhost')
    parser.add_argument('port', metavar='PORT', type=int, help='Port on host to connect to')
    args = parser.parse_args()

    # Create a socket connection to the engine.
    print 'Connecting to %s:%d' % (args.host, args.port)
    try:
        s = socket.create_connection((args.host, args.port))
    except socket.error as e:
        print 'Error connecting! Aborting'
        exit()

    bot = Player()
    bot.run(s)

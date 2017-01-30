#!/usr/bin/env 

import argparse
import socket
import sys
import time
from random import random, choice
from pokereval.card import Card
from query_cfr import chooseAction, chooseActionRandom, getStrategy
from cfr import getHandStrength, determineBestDiscardFast, convertHtoI, LightweightHistory
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


def mapBetToAbstraction(bet_amt, bet_options):
	raise NotImplementedError


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


def extractOppBetting():
    """
    Reads through lastActions in GETACTION_PACKET and updates global information if an opponent betting action was made.
    """
    global GETACTION_PACKET
    for a in GETACTION_PACKET.lastActions:


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

                if "DEAL:FLOP" in GETACTION_PACKET.lastActions:
                	HISTORY.P1_inPot, P2_inPot = 0, 0 # reset the in pot for this street

            	elif "DEAL:TURN" in GETACTION_PACKET.lastActions:
            		HISTORY.P1_inPot, P2_inPot = 0, 0 # reset the in pot for this street

            	elif "DEAL:RIVER" in GETACTION_PACKET.lastActions
            		HISTORY.P1_inPot, P2_inPot = 0, 0 # reset the in pot for this street


            elif word=="NEWGAME":

                # store game information globally
            	global NEWGAME_PACKET
                NEWGAME_PACKET = NEWGAME(data)


            elif word=="NEWHAND":

                # update the global NEWHAND packet
            	global NEWHAND_PACKET
                NEWHAND_PACKET = NEWHAND(data)

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

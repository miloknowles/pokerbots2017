#!/usr/bin/env 

import time
from random import random, choice
from query_cfr import chooseAction, chooseActionRandom, getStrategy
from cfr import getHandStrength, determineBestDiscardFast, convertHtoI, LightweightHistory
import json
from ParsePackets import *


# when we get an opponent action, map it into the abstracted space and use a History object to simulate it
# ask the History for legal actions when it's our turn
# deal with discrepancies between History's allowed actions and engine's allowed actions
	# all actions from History should be in engine's allowed actions, but not necessarily other way around
# when we get to a discard, use the History to determine which one?


global NEWGAME_PACKET, NEWHAND_PACKET, GETACTION_PACKET


def mapBetToAbstraction(bet_amt, bet_options):
	raise NotImplementedError


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

            word = data.split()[0]

            if word == "GETACTION":
                GETACTION_PACKET = GETACTION(data)

            elif word=="NEWGAME":
                NEWGAME_PACKET = NEWGAME(data)

            elif word=="NEWHAND":
                NEWHAND_PACKET = NEWHAND(data)


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

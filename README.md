# pokerbots2017

Code for the MIT Pokerbots 2017 Competition.

This project contains my implementation of CFR with average strategy sampling.

Pseudocode for the algorithm: http://webdocs.cs.ualberta.ca/~games/poker/publications/NIPS12.pdf (page 5)

The betting abstraction used was from: https://www.cs.cmu.edu/~sandholm/tartanian.AAMAS08.pdf



The 'PineappleBot' folder contains the code used to train our bot with CFR and run it against an opponent using the game engine.

- cfr.py contains helper functions and classes used to train and run the bot
- ParsePackets.py contains helper classes to parse information packets from the game engine
- Pineapple.py contains the code to run the bot.
- run_cfr.py contains code to train the bot using CFR and store results to .json files
- query_cfr.py contains code to load in the trained strategy from .json files and get action weights for a given history.

The 'misc' folder contains code used for testing helper functions and counting the number of histories in our game abstraction.


Note: my code uses the following libraries:

-- pbots_calc library, which is found here: https://github.com/mitpokerbots/pbots_calc

-- pokereval library, which is found here: https://pypi.python.org/pypi/pokereval/


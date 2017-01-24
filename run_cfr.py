#!/usr/bin/env

import time
from cfr import *

CUMULATIVE_REGRETS = {}
CUMULATIVE_STRATEGY = {}
EPSILON = 0.05
TAU = 1000
BETA = 10e6
HAND_STRENGTH_ITERS = 1000
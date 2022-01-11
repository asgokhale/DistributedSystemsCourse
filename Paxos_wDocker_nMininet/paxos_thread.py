#!/usr/bin/python
#  
#
# Vanderbilt University Computer Science
# Author: Aniruddha Gokhale
# Course: CS4287-5287 Principles of Cloud Computing
# Created: Spring 2021
#
# Purpose: Threads used in barrier synchronization for acceptors
#
# Since we have learned ZooKeeper, we could as well use the ZooKeeper API

# system and time
import os
import sys

# shared data structure and threading
import threading

# subclass from the threading.Thread
class Paxos_Thread (threading.Thread):
    # constructor
    def __init__ (self, func, arg):
        threading.Thread.__init__(self)
        self.func = func
        self.arg = arg   # the arg is going to indicate what phase (start, phase1, phase 2) 

    # override the run method here which is invoked by start
    def run (self):
        print("Starting " + self.name)
        self.func (self.arg)
        print("Exiting " + self.name)


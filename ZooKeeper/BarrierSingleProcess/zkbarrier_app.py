#!/usr/bin/python
#  
#
# Vanderbilt University Computer Science
# Author: Aniruddha Gokhale
# Course: CS 6381 Distributed Systems Principles
# Created: Spring 2018
# Modified: Spring 2019 (to make compliant with Python 3)
#
# Purpose: Demonstrate Zookeeper Barrier Synchronization
#
# This is the client application running as a thread
#
# Approach:
#
# We maintain a driver program which creates a "/barrier" znode
# and maintains a count of how many children nodes it has noticed appear
# under the tree.
#
# A client is implemented as a thread. Its job in life is to create a child
# node under "/barrier" with its thread name and wait to see what is the
# value maintained by the parent znode. The moment the number reaches the
# barrier value, the client declares success and proceeds to do its work
# which here is pretty much nothing and then exits. Because it creates a
# ephemeral node, when the client exits, its znode is automatically
# deleted by ZooKeeper.
#
# In the meantime, after all client threads have exited, the driver will
# cleanup its znode and then disconnect from ZooKeeper and then exit.
#

# system and time
import os
import sys

# shared data structure and threading
import threading

# Now import the kazoo package that supports Python binding
# to ZooKeeper
from kazoo.client import KazooClient

# to avoid any warning about no handlers for logging purposes, we
# do the following but there is some exception getting thrown so for
# now I am commenting this out.
import logging
logging.basicConfig ()

#--------------------------------------------------------------------
# subclass from the threading.Thread
# The purpose of this class is to represent a client who is
# waiting to ensure that a certain barrier condition has reached
# after which it can proceed with its work.  The work that the client
# wants to do is not of relevance here. All we need to show is how a
# client will participate in a barrier synchronization.
class AppThread (threading.Thread):
    # constructor
    def __init__ (self, name, func, args):
        threading.Thread.__init__(self, name=name)
        self.zkIPAddr = args['server']  # ZK server IP address
        self.zkPort = args['port'] # ZK server port num
        self.cond = args['cond'] # used as barrier condition
        self.ppath = args['ppath'] # refers to the parent znode path
        self.zk = None  # session handle to the server
        self.func = func  # thread function
        self.barrier = False
        
    # override the run method which is invoked by start
    def run (self):
        # It is here that we connect with the zookeeper server
        # and see if the condition has been met
        try:
            print(("AppThread::run - Client {} now running and opening connection to zookeeper".format (self.name)))

            # Instantiate zookeeper client object
            # right now only one host; it could be the ensemble
            hosts = self.zkIPAddr + str (":") + str (self.zkPort)
            self.zk = KazooClient (hosts)
            print(("App::run -- state = {}".format (self.zk.state)))

            # Open connection to zookeeper
            self.zk.start ()

            # now our job is to create an ephemeral znode under the parent
            # znode to indicate that we are up. Since it is possible that the
            # parent may not have yet create a znode, we keep testing for it
            while (True):
                if self.zk.exists (self.ppath):
                    print ("AppThread::run - parent znode is set")
                    # in that case we create our child node
                    self.zk.create (self.ppath + str ("/") + self.name, value=bytes (self.name, 'utf-8'), ephemeral=True, makepath=True)
                    # make sure to exit the loop
                    break
            else:
                print ("AppThread::run -- parent znode is not yet up")

            # now that we are out, we now invoke our thread function
            self.func (self)
            
        except:
            print("Unexpected error in AppThread::run", sys.exc_info()[0])
            raise
    


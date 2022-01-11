#!/usr/bin/python
#  
#
# Vanderbilt University Computer Science
# Author: Aniruddha Gokhale
# Course: CS 6381 Distributed Systems Principles
# Created: Spring 2018
#
# Purpose: Demonstrate Zookeeper Barrier Synchronization inside Mininet
#
# Code builds on the single process threaded version but here each
# client is a process on its own and runs on a host of Mininet. 
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
import time

# argument parser
import argparse

# Now import the kazoo package that supports Python binding
# to ZooKeeper
from kazoo.client import KazooClient

# to avoid any warning about no handlers for logging purposes, we
# do the following but there is some exception getting thrown so for
# now I am commenting this out.
import logging
logging.basicConfig ()

#--------------------------------------------------------------------
# The purpose of this class is to represent a client who is
# waiting to ensure that a certain barrier condition has reached
# after which it can proceed with its work.  The work that the client
# wants to do is not of relevance here. All we need to show is how a
# client will participate in a barrier synchronization.
class ZK_ClientApp ():
    # constructor
    def __init__ (self, args):
        self.name = args.name
        self.zkIPAddr = args.zkIPAddr  # ZK server IP address
        self.zkPort = args.zkPort # ZK server port num
        self.cond = args.cond # used as barrier condition
        self.ppath = "/barrier" # refers to the parent znode path
        self.zk = None  # session handle to the server
        self.barrier = False  # indicating if barrier has reached
        
    # override the run method which is invoked by start
    def init_client (self):
        # It is here that we connect with the zookeeper server
        # and see if the condition has been met
        try:
            print(("ClientApp::run - Client {} now running and opening connection to zookeeper".format (self.name)))

            # Instantiate zookeeper client object
            # right now only one host; it could be the ensemble
            hosts = self.zkIPAddr + str (":") + str (self.zkPort)
            self.zk = KazooClient (hosts)
            print(("ClientApp::run -- state = {}".format (self.zk.state)))

        except:
            print("Unexpected error in ClientApp::run", sys.exc_info()[0])
            raise

    # main logic of the client
    def run_client (self):
        """main logic of client"""

        try:
            # First, open connection to zookeeper
            self.zk.start ()

            # next our job is to create an ephemeral znode under the parent
            # znode to indicate that we are up. Since it is possible that the
            # parent may not have yet created a znode, we keep testing for it
            while (True):
                if self.zk.exists (self.ppath):
                    print(("ClientApp::run {} - parent znode is set".format (self.name)))
                    # in that case we create our child node
                    self.zk.create (self.ppath + str ("/") + self.name, value=self.name.encode(), ephemeral=True)
                    # make sure to exit the loop
                    break
                else:
                    print(("ClientApp::run {} -- parent znode is not yet up".format (self.name)))
                    time.sleep (1)

            # first we set a watcher for our parent's znode data.
            #---------------------------------------------------------
            # define a data watch function on the parent znode
            # note that this is a nested function defn
            @self.zk.DataWatch (self.ppath)
            def data_change_watcher (data, stat):
                """Data Change Watcher"""
                print(("ClientApp::DataChangeWatcher {} - data = {}, stat = {}".format (self.name, data, stat)))
                # check if barrier has reached
                value = int (data)
                if (value == self.cond):
                    print(("ClientApp: {}, barrier is reached".format (self.name)))
                    self.barrier = True

            #---------------------------------------------------------

            # now keep checking until barrier has reached
            while (self.barrier == False):
                # now let us retrieve the parent znode and set a watch
                # Note that we always check existence as a defensive programming
                print(("ClientApp {} barrier not reached yet".format (self.name)))
                if self.zk.exists (self.ppath):
                    # note that we do not need to set a watch because we have
                    # used Kazoo's decorator above to watch data change on the
                    # parent znode
                    value,stat = self.zk.get (self.ppath)
                    print(("ClientApp {} found parent znode value = {}, stat = {}".format (self.name, value, stat)))
    
                else:
                    print(("{} znode does not exist yet (strange)".format (self.ppath)))
    
            # out of the loop
            print(("ClientApp {} has reached the barrier and so we disconnect from zookeeper".format (self.name)))

            # since the data has reached the value of the barrier, 
            # we just disconnect from the zookeeper and our ephemeral
            # node will go away
            self.zk.stop ()
            self.zk.close ()

            print(("ClientApp {}: Bye Bye ".format (self.name)))
    
        except:
            print("Unexpected error in ClientApp::run", sys.exc_info()[0])
            raise
    

##################################
# Command line parsing
##################################
def parseCmdLineArgs ():
    # parse the command line
    parser = argparse.ArgumentParser ()

    # add optional arguments
    parser.add_argument ("-a", "--zkIPAddr", default="127.0.0.1", help="ZooKeeper server ip address, default 127.0.0.1")
    parser.add_argument ("-c", "--cond", type=int, default=5, help="Barrier Condition representing number of client apps in the barrier, default 5")
    parser.add_argument ("-p", "--zkPort", type=int, default=2181, help="ZooKeeper server port, default 2181")
    
    # add positional arguments in that order
    parser.add_argument ("name", help="client name")

    # parse the args
    args = parser.parse_args ()

    return args
    
#------------------------------------------
# main function
def main ():
    """ Main program """

    print("Demo program for ZooKeeper-based Barrier Sync: Client Appln")
    parsed_args = parseCmdLineArgs ()
    
    # 
    # invoke the driver program
    client = ZK_ClientApp (parsed_args)

    # initialize the client
    client.init_client ()
    
    # start the main logic
    client.run_client ()

#----------------------------------------------
if __name__ == '__main__':
    main ()

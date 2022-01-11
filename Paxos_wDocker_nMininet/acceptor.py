#!/usr/bin/python
#  
# Purpose: Paxos Acceptor
#
# Vanderbilt University Computer Science
# Author: Aniruddha Gokhale
# Course: CS6381 Distributed Systems Principles
# Created: Spring 2021
#
# Can be used on Mininet, insider a Docker cluster, and directly on distributed hosts
#
#

# system and time
import os
import sys
import time

import random # for random numbers

import argparse   # argument parser

import zmq                   # ZeroMQ library
import json                  # json
import pickle                # serialization


# ----------------------------------------------------------------------------------------------------
# The Paxos Acceptor
#
class Paxos_Acceptor ():
    """ The acceptor class """

    #################################################################
    # constructor
    #################################################################
    def __init__ (self, args):
        self.id = None                          # ID we receive in a given round
        self.baseport = args.baseport    # base port of proposer
        self.ipaddr = args.ipaddr           # IP Address of proposer
        self.delay = args.delay            # artificially inserted max delay
        self.timeout = args.timeout     # max allowed delay to receive any message from proposer
        self.iters = args.iters               # number of iterations
        self.prop_num = None              # holds the proposal number we have
        self.prop_val = None                 # holds the value being proposed/accepted

        self.timed_out = False             # did not receive msg within the full timeout
        self.proposer_stale = False         # Proposer's proposal number is old
        
        self.poller = None                    # ZMQ poller object
        self.sender4barrier = None         # respond with an acceptor up signal
        self.rcv4propose = None               # used to receive propose messages
        self.sender4promise = None        # used to send promise messages
        self.rcv4accept = None             # used to receive accept messages
        self.sender4learn = None             # used to send the learned value

        # stores the incoming messages
        self.msgs = {'propose': [], 'accepted': []}    # received msgs

    # -----------------------------------------------------------------------
    # Initialize the network connections
    def init_acceptor (self):
        """Initialize the networking part of the acceptor"""

        try:
            # obtain the ZeroMQ context
            context = zmq.Context()

            # obtain the poller object
            self.poller = zmq.Poller ()
            
            # Socket to send and receive messages. Note, we use the ZMQ divide-conquer
            # pattern using PUSH and PULL
            #
            #           This is our protocol
            # base port + 0 to push "I am up" message to proposer
            # base port + 1 to pull propose message from proposer
            # base port + 2 to push promise result to proposer
            # base port + 3 to pull accept message from proposer
            # base port + 4 to push learn message to proposer

            # first, the barrier message to proposer (PUSH)
            self.sender4barrier = context.socket (zmq.PUSH)
            # set high water mark and LINGER option to ensure messages
            # get sent.
            self.sender4barrier.setsockopt (zmq.LINGER, -1)
            self.sender4barrier.setsockopt (zmq.SNDHWM, 0)
            bind_addr = "tcp://" + self.ipaddr + ":" + str (self.baseport+0)
            print("For acceptor->proposer up PUSH, bind addr is: ", bind_addr)
            self.sender4barrier.connect (bind_addr)

            # next, the propose message (PULL)
            self.rcv4propose = context.socket (zmq.PULL)
            # set high water mark to ensure messages gets received.
            self.rcv4propose.setsockopt (zmq.RCVHWM, 0)
            bind_addr = "tcp://" + self.ipaddr + ":" + str (self.baseport+1)
            print("For proposer->acceptor propose message, bind addr is: ", bind_addr)
            self.rcv4propose.connect  (bind_addr)

            # next, the promise message to proposer (PUSH)
            self.sender4promise = context.socket (zmq.PUSH)
            # set high water mark and LINGER option to ensure messages
            # get sent.
            self.sender4promise.setsockopt (zmq.LINGER, -1)
            self.sender4promise.setsockopt (zmq.SNDHWM, 0)
            bind_addr = "tcp://" + self.ipaddr + ":" + str (self.baseport+2)
            print("For acceptor->proposer promise PUSH, bind addr is: ", bind_addr)
            self.sender4promise.connect (bind_addr)

            # next, the accept message (PULL)
            self.rcv4accept = context.socket (zmq.PULL)
            # set high water mark to ensure messages gets received.
            self.rcv4accept.setsockopt (zmq.RCVHWM, 0)
            bind_addr = "tcp://" + self.ipaddr + ":" + str (self.baseport+3)
            print("For proposer->acceptor accept message, bind addr is: ", bind_addr)
            self.rcv4accept.connect  (bind_addr)

            # finally, the learn message to proposer (PUSH)
            self.sender4learn = context.socket (zmq.PUSH)
            # set high water mark and LINGER option to ensure messages
            # get sent.
            self.sender4learn.setsockopt (zmq.LINGER, -1)
            self.sender4learn.setsockopt (zmq.SNDHWM, 0)
            bind_addr = "tcp://" + self.ipaddr + ":" + str (self.baseport+4)
            print("For acceptor->proposer promise PUSH, bind addr is: ", bind_addr)
            self.sender4learn.connect (bind_addr)

        except:
            print("Unexpected error in init_server:", sys.exc_info()[0])
            raise

    # -----------------------------------------------------------------------
    # reset data structures for the next iteration
    def reset_acceptor (self):
        """reset data structures"""
        print ("Proposer::reset_proposer")

        # disconnect from all sockets
        #bind_addr = "tcp://" + self.ipaddr + ":" + str (self.baseport+0)
        #self.sender4barrier.disconnect (bind_addr)
        #bind_addr = "tcp://" + self.ipaddr + ":" + str (self.baseport+1)
        #self.rcv4propose.disconnect  (bind_addr)
        #bind_addr = "tcp://" + self.ipaddr + ":" + str (self.baseport+2)
        #self.sender4promise.disconnect (bind_addr)
        #bind_addr = "tcp://" + self.ipaddr + ":" + str (self.baseport+3)
        #self.rcv4accept.disconnect  (bind_addr)
        #bind_addr = "tcp://" + self.ipaddr + ":" + str (self.baseport+4)
        #self.sender4learn.disconnect (bind_addr)

        # close all sockets
        self.sender4barrier.close (linger=0)
        self.rcv4propose.close (linger=0)
        self.sender4promise.close (linger=0)
        self.rcv4accept.close (linger=0)
        self.sender4learn.close (linger=0)

        self.prop_num = None
        self.prop_val = None

        self.timed_out = False
        self.proposer_stale = False
      
        self.msgs['propose'] = []
        self.msgs['accept'] = []

        
    ###################################################################
    # This method sends acceptor up message to proposer
    ###################################################################
    def send_acceptor_up_msg (self):
        "create the json object for acceptor up message to be sent to proposer"

        try:
            print ("Acceptor::send_acceptor_up_msg")
            up_msg = {
                'status': 'up'
            }
            # now send this to our proposer
            self.sender4barrier.send_json (up_msg)
            
        except:
            print("Unexpected error in send_acceptor_up_msg:", sys.exc_info()[0])
            raise

    ###################################################################
    # This method sends promise message to proposer
    ###################################################################
    def send_promise_msg (self):
        "create the json object for promise message to be sent to proposer"

        try:
            print ("Acceptor::send_promise_msg")
            promise_msg = {
                'id': self.id,
                'prop_num': self.prop_num
            }

            # insert an artificial random delay
            delay = random.randint (0, self.delay)
            print ("Inserting an artificial delay of {} secs before sending promise msg".format (delay))
            time.sleep (delay)  # in secs
            
            # now send this to our proposer
            self.sender4promise.send_json (promise_msg)
            
        except:
            print("Unexpected error in send_promise_msg:", sys.exc_info()[0])
            raise

    ###################################################################
    # This method sends learn message to proposer
    ###################################################################
    def send_learn_msg (self):
        "create the json object for learn message to be sent to proposer"

        try:
            print ("Acceptor::send_learn_msg")
            learn_msg = {
                'id': self.id,
                'prop_num': self.prop_num,
                'prop_val': self.prop_val
            }

            # insert an artificial random delay
            delay = random.randint (0, self.delay)
            print ("Inserting an artificial delay of {} secs before sending learn msg".format (delay))
            time.sleep (delay)  # in secs
            
            # now send this to our proposer
            self.sender4learn.send_json (learn_msg)
            
        except:
            print("Unexpected error in send_learn_msg:", sys.exc_info()[0])
            raise

    ###########################################################
    # Process the propose messages coming from proposer within the timeout.
    #
    # If the proposal number we hold is equal or higher than the proposed, we know the proposer has
    # stale info.
    #
    ###########################################################
    def rcv_and_process_propose_msg (self):
        """ function to process propose message """

        print ("Acceptor::rcv_and_process_propose_msg")

        self.poller.register (self.rcv4propose, zmq.POLLIN)

        while True:

            # insert an artificial delay to mimic n/w delay and then read the message
            delay = random.randint (0, self.delay)
            print ("Inserting an artificial delay of {} sec before receiving propose msg".format (delay))
            time.sleep (delay) # that many secs

            # poll the socket for incoming request with the timeout
            events = dict (self.poller.poll (self.timeout*1000))  # timeout is in seconds so we convert to msec
 
            # The incoming event better be on the socket we have enabled else
            # it must be a timeout
            if (self.rcv4propose not in events):
                # break the loop
                print ("Acceptor::rcv_and_process_propose_msg: timer expired, returning")
                self.timed_out = True
                break
        
            msg = self.rcv4propose.recv_json ()
            self.id = msg['id']
            if (self.prop_num >= msg['num']):
                print ("====Acceptor: our prop num ({}) is equal or greater than that of proposer ({})====".format (self.prop_num, msg['num']))
                self.proposer_stale = True
            else:
                print ("====Acceptor: our prop num ({}) is less than that of proposer ({})====".format (self.prop_num, msg['num']))

            break  # nothing more to do in this loop

        # unregister from the poller
        self.poller.unregister (self.rcv4propose)
        
    ###########################################################
    # Process the accept message coming from proposer within the timeout.
    #
    # The safety property of the Paxos algo ensures that what we get now is the highest numbered
    # proposal in the system
    #
    ###########################################################
    def rcv_and_process_accept_msg (self):
        """ function to process accept message """

        print ("Acceptor::rcv_and_process_accept_msg")

        self.poller.register (self.rcv4accept, zmq.POLLIN)

        while True:

            # insert an artificial delay to mimic n/w delay and then read the message
            delay = random.randint (0, self.delay)
            print ("Inserting an artificial delay of {} sec before receiving accept msg".format (delay))
            time.sleep (delay) # that many secs

            # poll the socket for incoming request with the timeout
            events = dict (self.poller.poll (self.timeout*1000))  # timeout is in seconds so we convert to msec
 
            # The incoming event better be on the socket we have enabled else
            # it must be a timeout
            if (self.rcv4accept not in events):
                # break the loop
                print ("Acceptor::rcv_and_process_accept_msg: timer expired, returning")
                self.timed_out = True
                break
        
            msg = self.rcv4accept.recv_json ()
            self.prop_num = msg['num']
            self.prop_val = msg['val']

            print ("===== Acceptor::rcv_and_process_accept_msg: prop num = {}, prop_val = {} ====".format (self.prop_num, self.prop_val))
            break  # nothing more to do in this loop

        # unregister from the poller
        self.poller.unregister (self.rcv4accept)
        print ("Acceptor::rcv_and_process_accept_msg: updated our proposal num and value")
        

    #####################################################################
    # The method starts the single decree Paxos algorithm
    # 
    # This is the main "driver" function for the acceptor logic.
    #####################################################################
    def single_decree_consensus (self):
        """ Start the Paxos single decree consensus """

        try:
            # ask the user to decide on a proposer number
            self.prop_num = input ("Select some proposal number between 1 and 10: ")
            
            # inform our proposer that we are up
            self.send_acceptor_up_msg ()

            # now receive and process the propose message
            self.rcv_and_process_propose_msg ()

            # if timed out receiving the msg, give up
            if (self.timed_out):
                # most likely because nothing showed up within the timeout we have
                print ("Acceptor::single_decree_consensus: giving up waiting for propose msg")
                return
            
            # now send promise message even if our number is higher than that of proposer
            self.send_promise_msg ()

            # check if proposer is stale in which case, we do not proceed with next steps
            if (self.proposer_stale):
                print ("Proposer with proposal number: {} is stale".format (self.prop_num))
                return
            
            # now receive and process the accept message
            self.rcv_and_process_accept_msg ()

            # if timed out receiving the msg, give up
            if (self.timed_out):
                # most likely because nothing showed up within the timeout we have
                print ("Acceptor::single_decree_consensus: giving up waiting for accept msg")
                return
            
            # now send learned message
            self.send_learn_msg ()

            print ("Acceptor::single_decree_consensus: done sending learned info")
            return
            
        except:
            print("Unexpected error in single_decree_consensus method:", sys.exc_info()[0])
            raise

    ############################################################
    # Run the iterations of the Paxos consensus algorithm for the Acceptor role
    ############################################################
    def run_paxos_iterations (self):
        """Run the iterations of the Paxos consensus"""

        try:
            ############  the real work starts now ###########

            for i in range (self.iters):
                print ("****** Next iteration of Acceptor ************")
            
                print("Acceptor::run_paxos_iterations - initialize acceptor")
                self.init_acceptor ()
            
                print("Acceptor::run_paxos_iterations - run single decree algorithm")
                self.single_decree_consensus ()
            
                print("Acceptor::run_paxos_iterations - cleanup")
                self.reset_acceptor ()

                time.sleep (10)   # give some time for the sockets to clear up
            
        except:
            print("Unexpected error in run_paxos_iterations method:", sys.exc_info()[0])
            raise


##################################
# Command line parsing
##################################
def parseCmdLineArgs ():
    # parse the command line
    parser = argparse.ArgumentParser ()

    # add optional arguments
    parser.add_argument ("-a", "--ipaddr", default="localhost", help="IP Address of Proposer")
    parser.add_argument ("-p", "--baseport", type=int, default=5555, help="Base port, default 5555")
    parser.add_argument ("-d", "--delay", type=int, default=5, help="Artificially inserted delay to mimic n/w conditions, default max 5 secs")
    parser.add_argument ("-t", "--timeout", type=int, default=20, help="Max time to wait for req from proposer, default 20 secs")
    parser.add_argument ("-i", "--iters", type=int, default=5, help="Number of iterations, default 5")
    
    # parse the args
    args = parser.parse_args ()

    return args
    
#------------------------------------------
# main function
def main ():
    """ Main program """

    print("Paxos Acceptor Main program")

    random.seed ()
    
    # parse the args
    print ("Paxos Aceptor Main: parse the args")
    parsed_args = parseCmdLineArgs ()
    
    # instantiate the proposer object
    print ("Paxos Acceptor Main: instantiate acceptor object")
    acceptor = Paxos_Acceptor (parsed_args)

    # start the iterations
    print ("Paxos Acceptor Main: run the Paxos iterations")
    acceptor.run_paxos_iterations ()

#----------------------------------------------
if __name__ == '__main__':
    main ()
        

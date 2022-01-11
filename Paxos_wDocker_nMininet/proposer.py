#!/usr/bin/python
#  
# Purpose: Paxos Proposer
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

import random  # for random numbers

import argparse   # argument parser

import zmq                   # ZeroMQ library
import json                  # json

from paxos_thread import Paxos_Thread  # for barrier synchronization and other operations

#---------------------------------------------------------------------------------------------
# Thread function that implements barrier, a sink and timer
#
# This function is executed by a thread in parallel to the main program, where
# the main program will block until all desired responses are received.
#
def thread_func (args):
    """ Thread function to execute when proposer starts a parallel thread """

    try:
        # Before the proposer can start proposing, we need to make sure that
        # our quorum of acceptors is ready.  So we have a barrier synchronization.
        # Other scenarios include receiving promise and learn messages within
        # the given timeout
        #
        # To do that, we start the ZeroMQ sink task. When the required number
        # of responses are received, the thread terminates doing any processing
        # that is needed. We may also terminate if the timer expires.  This is
        # handled using the ZMQ Poller
        
        print("Paxos thread function starting with args: ", args)
        proposer = args['proposer']   # should be the proposer object
        timeout = args['timeout']

        # get the appropriate socket based on what the operation is
        print("Paxos thread function setting the right receiver")
        if (args['op'] == "acceptor_up"):
            receiver = proposer.rcv4barrier
        elif (args['op'] == "promise"):
            receiver = proposer.rcv4promise
        elif (args['op'] == "learn"):
            receiver = proposer.rcv4learn
        else:
            print("Unknown operation. Should be aborted")
            receiver = None
            raise

        # Now register this receiver with the poller. The reason we are using a poller
        # is because we want to also involve a timeout
        print ("Paxos thread function registering the receiver")
        proposer.poller.register (receiver, zmq.POLLIN)

        # The logic here is that we wait until the required number of
        # ACKs are received 
        i = 0
        elapsed_time = 0 # we need this because we need to keep reducing the timeout 

        # continue trying to receive until condition is met or we run out of timeout
        while (i < args['cond']):

            # get current time
            start_time = time.time ()  
                
            # deduct elapsed time from the timeout if it is not set to infinity
            if (timeout is not None):
                print ("Paxos thread function: waiting for propose or learn msg")
                timeout = timeout - elapsed_time

                # insert an artificial delay to read the message
                delay = random.randint (0, proposer.delay)
                print ("Inserting an artificial delay of {} sec before reading promise or learn msg".format (delay))
                time.sleep (delay) # that many secs
                
                # poll the socket for incoming connections with the timeout
                events = dict (proposer.poller.poll (timeout*1000))  # timeout is in seconds so we convert to msec
 
                # The incoming event better be on the socket we have enabled else
                # it must be a timeout
                if (receiver not in events):
                    # break the loop
                    print ("Paxos Thread: timer expired, returning")
                    break

            else:
                print ("Paxos thread function: waiting for acceptor up signal")
                events = dict (proposer.poller.poll ())  # for up msg, no timeout
                # since there was no timeout, our receiver better be enabled
                print ("Paxos thread function: assertion check")
                assert (receiver in events)


            # if everything goes according to plan, read the message
            print ("Paxos thread func: receiving json message")
            msg = receiver.recv_json ()
            
            print ("Paxos thread func: appending json message")
            proposer.msgs [args['op']].append (msg)

            end_time = time.time ()
            elapsed_time = end_time - start_time
                           
            # increment the number of acks received
            i = i + 1

        # Now unregister the receiver from the poller
        print ("Paxos thread func: unregistering from the poller")
        proposer.poller.unregister (receiver)

        print ("Paxos thread exiting")

        return
    
    except:
        print("Unexpected error in paxos thread function: ", sys.exc_info()[0])
        raise
        

# ----------------------------------------------------------------------------------------------------
# The Paxos Proposer
#
class Paxos_Proposer ():
    """ The proposer class """

    #################################################################
    # constructor
    #################################################################
    def __init__ (self, args):
        self.quorum = args.quorum        # number of acceptors
        self.baseport = args.baseport    # port on which we push to acceptors
        self.timeout = args.timeout     # timeout used for each round
        self.delay = args.delay            # artificial delay
        self.iters = args.iters               # number of iterations
        self.majority = None                # simple majority
        self.num_responders = 0          # keeps track of how many responded
        self.prop_num = None              # holds the proposal number
        self.prop_val = None                 # holds the value being proposed

        self.error_cond = False            # some internal error
        
        self.poller = None                    # ZMQ poller object
        self.rcv4barrier = None               # used to receive acceptor up signals
        self.sender4propose = None                # used to send propose messages
        self.rcv4promise = None               # used to receive promise messages
        self.sender4accept = None             # used to send accept messages
        self.rcv4learn = None             # used to receive learn messages

        # stores the incoming messages
        self.msgs = {'acceptor_up': [], 'promise': [], 'learn': []}    # received msgs

        self.defeated = None            # whether our proposal is defeated or not
        
        # an object we need for the arguments to send to our thread function
        self.thr_obj_dict = {'acceptor_up': None, 'promise': None, 'learn': None}  
        
    # -----------------------------------------------------------------------
    # Initialize the network connections and the barriers
    def init_proposer (self):
        """Initialize the networking part of the proposer"""

        try:
            # compute the simple majority
            self.majority = int (self.quorum/2) + 1 # handles both odd and even cases

            # defeated status (start with non defeated)
            self.defeated = False
            
            # obtain the ZeroMQ context
            context = zmq.Context()

            # obtain the poller object
            self.poller = zmq.Poller ()
            
            # Socket to send and receive messages. Note, we use the ZMQ divide-conquer
            # pattern using PUSH and PULL
            #
            #           This is our protocol
            # base port + 0 to pull "I am up" messages from acceptors
            # base port + 1 to push propose messages to acceptors
            # base port + 2 to pull promise results from acceptors
            # base port + 3 to push accept messages to acceptors
            # base port + 4 to pull learn messages from acceptors

            # first, the barrier messages from all our acceptors (PULL)
            self.rcv4barrier = context.socket (zmq.PULL)
            # set high water mark as unlimited
            self.rcv4barrier.setsockopt (zmq.RCVHWM, 0)
            bind_addr = "tcp://*:" + str (self.baseport+0)
            print("For acceptors up->proposer PULL, bind addr is: ", bind_addr)
            self.rcv4barrier.bind (bind_addr)

            # next, the propose message (PUSH)
            self.sender4propose = context.socket (zmq.PUSH)
            # set high water mark and LINGER option to ensure messages
            # get sent.
            self.sender4propose.setsockopt (zmq.LINGER, -1)
            self.sender4propose.setsockopt (zmq.SNDHWM, 0)
            bind_addr = "tcp://*:" + str (self.baseport+1)
            print("For proposer->acceptor propose message, bind addr is: ", bind_addr)
            self.sender4propose.bind  (bind_addr)

            # next, the pull promise messages from acceptors
            self.rcv4promise = context.socket (zmq.PULL)
            # set high water mark as unlimited
            self.rcv4promise.setsockopt (zmq.RCVHWM, 0)
            bind_addr = "tcp://*:" + str (self.baseport+2)
            print("For acceptor promise->propose PULL, bind addr is: ", bind_addr)
            self.rcv4promise.bind (bind_addr)

            # finally, the push of accept to acceptors
            self.sender4accept = context.socket (zmq.PUSH)
            # set high water mark and LINGER option to ensure messages
            # get sent.
            self.sender4accept.setsockopt (zmq.LINGER, -1)
            self.sender4accept.setsockopt (zmq.SNDHWM, 0)
            bind_addr = "tcp://*:" + str (self.baseport+3)
            print("For proposer->acceptor accept PUSH, bind addr is: ", bind_addr)
            self.sender4accept.bind  (bind_addr)

            # next, the pull the learned value from all acceptors
            self.rcv4learn = context.socket (zmq.PULL)
            # set high water mark as unlimited
            self.rcv4learn.setsockopt (zmq.RCVHWM, 0)
            bind_addr = "tcp://*:" + str (self.baseport+4)
            print("For acceptor->proposer learn PULL, bind addr is: ", bind_addr)
            self.rcv4learn.bind (bind_addr)

        except:
            print("Unexpected error in init_server:", sys.exc_info()[0])
            raise

    # -----------------------------------------------------------------------
    # reset data structures for the next iteration
    def reset_proposer (self):
        """reset data structures"""
        print ("Proposer::reset_proposer")

        # Now unbind all the bound addresses
        #
        #bind_addr = "tcp://*:" + str (self.baseport+0)
        #self.rcv4barrier.unbind (bind_addr)
        #bind_addr = "tcp://*:" + str (self.baseport+1)
        #self.sender4propose.unbind  (bind_addr)
        #bind_addr = "tcp://*:" + str (self.baseport+2)
        #self.rcv4promise.unbind (bind_addr)
        #bind_addr = "tcp://*:" + str (self.baseport+3)
        #self.sender4accept.unbind  (bind_addr)
        #bind_addr = "tcp://*:" + str (self.baseport+4)
        #self.rcv4learn.unbind (bind_addr)

        # close all sockets
        self.rcv4barrier.close (linger=0)
        self.sender4propose.close (linger=0)
        self.rcv4promise.close (linger=0)
        self.sender4accept.close (linger=0)
        self.rcv4learn.close (linger=0)

        # cleanup all our variables
        self.num_responders = 0
        self.msgs['acceptor_up'] = []
        self.msgs['promise'] = []
        self.msgs['learn'] = []
        self.defeated = False
        self.thr_obj_dict = {'acceptor_up': None, 'promise': None, 'learn': None}  

    # -----------------------------------------------------------------------
    # Create the thread-based barrier sink. 
    def start_paxos_thread (self, op):
        """Start a barrier thread to ensure all expected replies are received"""

        try:
            # The different operations that are possible are: (a) acceptor_up, (b) promise,
            # and (c) learn
            if (op == "acceptor_up"):
                # need to receive response from these many workers
                cond = self.quorum
                timer = None
            elif (op == "promise"):
                # need to receive response from these many workers
                cond = self.quorum
                timer = self.timeout
            elif (op == "learn"):
                # need to receive response from these many workers
                cond = self.quorum
                timer = self.timeout
                
            else:
                print ("bad op in starting paxos thread")
                raise

            # create the args to send to the thread
            args = {'op': op, 'cond': cond, 'timeout': timer, 'proposer': self}
            
            # instantiate a thread obj and start the thread
            print("Proposer::start_paxos_thread - invoke thread func with args: ", args)
            self.thr_obj_dict[op] = Paxos_Thread (thread_func, args)
            self.thr_obj_dict[op].start ()

        except:
            print("Unexpected error in init_server:", sys.exc_info()[0])
            raise

    ###################################################################
    # This method sends propose message to acceptors
    ###################################################################
    def send_propose_msg (self):
        "create the json object for propose message to be sent to all acceptors"

        try:
            print ("Proposer::send_propose_msg - sending to {} acceptors:".format(self.quorum))

            # create an artificial delay to mimic n/w delay. Earlier, we had this inside the loop but that was
            # becoming too much.
            delay = random.randint (0, self.delay)
            print ("Inserting an artificial delay of {} sec to mimic n/w delay before sending propose msg".format (delay))
            time.sleep (delay)
                
            for i in range (self.quorum):
                propose_msg = {
                    'id': i,  # this is the id the acceptor gets and must send back
                    'num': self.prop_num
                }

                # now send this and one of the acceptors will receive it
                # according to the PUSH-PULL pattern we are using
                print ("Proposer::send_propose_msg: sending {} to next acceptor.".format (propose_msg))
                self.sender4propose.send_json (propose_msg)

            
        except:
            print("Unexpected error in send_propose_msg:", sys.exc_info()[0])
            raise

    ###################################################################
    # This method sends the accept message to acceptors
    ###################################################################
    def send_accept_msg (self):
        "create the json object for accept message to be sent to all acceptors"

        try:
            # technically, we should be sending to only those acceptors who responded to us.
            # But that logic will become complicated. So we send to all acceptors. The hope is that
            # an acceptor who was partitioned due to CAP issues is back and gets this, and sees that
            # it has a higher proposal number will not learn the info, which will be a RED flag for the
            # system
            print ("Proposer::send_accept_msg - sending to {} acceptors:".format(self.quorum))

            # create an artificial delay to mimic n/w delay. Earlier, we had this inside the loop but that was
            # sometimes creating too much delay
            delay = random.randint (0, self.delay)
            print ("Inserting an artificial delay of {} sec to mimic n/w delay before sending accept msg".format (delay))
            time.sleep (delay)
                
            for i in range (self.quorum):
                accept_msg = {
                    'num': self.prop_num,
                    'val': self.prop_val
                }

                # now send this and one of the acceptors will receive it
                # according to the PUSH-PULL pattern we are using
                print ("Proposer::send_accept_msg: sending {} to next acceptor.".format (accept_msg))
                self.sender4accept.send_json (accept_msg)

            
        except:
            print("Unexpected error in send_accept_msg:", sys.exc_info()[0])
            raise

    ###########################################################
    # Process the promise messages coming from acceptors within the timeout.
    #
    # We need to ensure that our proposal number was the highest not seen before, and
    # only if we have heard from a majority of acceptors do we proceed to the next step
    #
    # if any of the acceptors tells us that they have a higher number, we give up
    #
    ###########################################################
    def process_promise_msgs (self):
        """ function to process promise messages """

        print ("Proposer::process_promise_msgs")

        # here we check if all the promises we have received confirm that our proposal number
        # is the highest in the system, and that we have received messages from at least a majority
        # if not the entire quorum

        self.num_responders = len (self.msgs['promise'])
        print ("Proposer::process_promise_msgs - {} number of acceptors out of {} responded".format (self.num_responders, self.quorum))
        
        if (self.num_responders < self.majority):
            # we did not receive sufficient number of responses. So cannot proceed
            print ("==== Proposer::process_promise_msgs: Majority messages not received; Give up :-( =====")
            self.defeated = True
            return

        # now go thru all the received promises and make sure that the highest promised proposal
        # number is less than what we have proposed. If any one is higher, we give up
        for i in range (self.num_responders):
            # just for readability, I am using an extra variable here.
            response = self.msgs['promise'][i]
            if (response['prop_num'] >= self.prop_num):
                # the proposal number reported by this acceptor is equal or higher than ours, give up :-(
                print ("Proposer::process_promise_msgs: Acceptor {} has higher or equal proposal number = {}; Give up :-(".format (response['id'], response['prop_num']))
                self.defeated = True
                return

        # if we reach here, then we are in great shape :-)
        print ("==== Proposer::process_promise_msgs: Our proposal number was the highest :-). Proceed with Phase 2. ====")


    ###########################################################
    # Process the learn messages coming from acceptors within the timeout.
    #
    # We need to make sure that we have received the same message from majority of our acceptors
    # at which point we declare victory
    #
    ###########################################################
    def process_learn_msgs (self):
        """ function to process learn messages """

        # Note that we are implementing this learn part using our interpretation. The Paxos approach
        # lets acceptors send to a set of learners. Here we have only one learner who is the original
        # proposer. Technically, all those responders should be learners but we are not complicating
        # things here. Maybe we could use an InfluxDB time series and every "learning" proposer dumps
        # its accepted value with a proposal number to InfluxDB
        
        print("Proposer::process_learn_msgs")

        # here we check if all the acceptors who responded have learned the value or not
        if (len (self.msgs['learn']) < self.num_responders):
            # we did not receive sufficient number of responses. So cannot proceed
            print ("==== Proposer::process_learn_msgs: Did not receive learn confirmation from all responders; Give up :-( on proposal num {} with value {} ===".format (self.prop_num, self.prop_val))
            self.defeated = True
        else:
            # technically, we should make sure that majority of values learned are the same but here we
            # assume they will be.
            print (":-) :-) :-) Proposer::process_learn_msgs: Proposal num {} with value {} has been learned :-) :-) :-)".format (self.prop_num, self.prop_val))

    #####################################################################
    # The method starts the single decree Paxos algorithm
    # 
    # This is the main "driver" function for the proposer logic.
    #####################################################################
    def single_decree_consensus (self):
        """ Start the Paxos single decree consensus """

        try:
            print ("^^^^^ Proposer::single_decree_consensus - Start the Process ^^^^^")
            # obtain some inputs from the user
            self.prop_num = input ("Select some proposal number between 1 and 10: ")
            
            # ask the proposer to decide on a proposal number
            self.prop_val = input ("Select some value for the proposal: ")
            
            # start the paxos thread so we can wait for the acceptors to be up
            print ("Proposer::single_decree_consensus - start thread for acceptors to join: ")
            self.start_paxos_thread ("acceptor_up")
            
            # wait for thread to exit to ensure all acceptors are up
            print ("Proposer::single_decree_consensus - wait for thread to exit")
            self.thr_obj_dict["acceptor_up"].join ()

            # now send propose message
            print ("Proposer::single_decree_consensus - send_propose_msg")
            self.send_propose_msg ()
            
            # start the paxos thread so we can wait for the acceptors to be up
            print ("Proposer::single_decree_consensus - start thread for acceptors to send promise msg")
            self.start_paxos_thread ("promise")
            
            # wait for thread to exit. We provide a timeout to join so that replies are expected prior
            # to that
            print ("Proposer::single_decree_consensus - wait for promise thread to exit")
            #self.thr_obj_dict["promise"].join (self.timeout)
            self.thr_obj_dict["promise"].join ()

            # process the received promise messages
            print ("Proposer::single_decree_consensus - process_promise_msg")
            self.process_promise_msgs ()
            
            if self.defeated:
                print ("Proposer with proposal number: {} and value: {} is defeated".format (self.prop_num, self.prop_val))
                return
            
            # now send accept message
            print ("Proposer::single_decree_consensus - send_accept_msg")
            self.send_accept_msg ()
            
            # start the paxos thread so we can wait for the acceptors to learn
            print ("Proposer::single_decree_consensus - start thread for acceptors to send learn msg")
            self.start_paxos_thread ("learn")
            
            # wait for thread to exit. We provide a timeout to join so that replies are expected prior
            # to that
            print ("Proposer::single_decree_consensus - wait for learn thread to exit")
            #self.thr_obj_dict["learn"].join (self.timeout)
            self.thr_obj_dict["learn"].join ()

            # process the received learn messages
            print ("Proposer::single_decree_consensus - process_learn_msg")
            self.process_learn_msgs ()

            if self.defeated:
                print ("Proposer with proposal number: {} and value: {} is defeated".format (self.prop_num, self.prop_val))
                return
            
            print ("^^^^^ Proposer::single_decree_consensus - End the Process ^^^^^")
        except:
            print("Unexpected error in single_decree_consensus method:", sys.exc_info()[0])
            raise

    ############################################################
    # Run the iterations of the Paxos consensus algorithm for the Proposer role
    ############################################################
    def run_paxos_iterations (self):
        """Run the iterations of the Paxos consensus"""

        try:
            ############  the real work starts now ###########

            for i in range (self.iters):
                print ("****** Next iteration of Proposer ************")
            
                print("Proposer::run_paxos_iterations - initialize proposer")
                self.init_proposer ()
            
                print("Proposer::run_paxos_iterations - run single decree algorithm")
                self.single_decree_consensus ()
            
                print("Proposer::run_paxos_iterations - cleanup")
                self.reset_proposer ()

                time.sleep (10)  # for sockets to be available again
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
    parser.add_argument ("-p", "--baseport", type=int, default=5555, help="Base port, default 5555")
    parser.add_argument ("-q", "--quorum", type=int, default=3, help="Quorum of acceptors, default 3")
    parser.add_argument ("-t", "--timeout", type=int, default=10, help="Timeout to receive responses in sec, default 10 sec")
    parser.add_argument ("-d", "--delay", type=int, default=5, help="Artificial delay to mimic n/w delays, default of max 5 sec")
    parser.add_argument ("-i", "--iters", type=int, default=5, help="Number of iterations, default 5")
    
    # parse the args
    args = parser.parse_args ()

    return args
    
#------------------------------------------
# main function
def main ():
    """ Main program """

    print("Paxos Proposer Main program")

    random.seed ()
    
    # parse the args
    print ("Paxos Proposer Main: parse the args")
    parsed_args = parseCmdLineArgs ()
    
    # instantiate the proposer object
    print ("Paxos Proposer Main: instantiate proposer object")
    proposer = Paxos_Proposer (parsed_args)

    # start the iterations
    print ("Paxos Proposer Main: run the iterations")
    proposer.run_paxos_iterations ()

#----------------------------------------------
if __name__ == '__main__':
    main ()
        

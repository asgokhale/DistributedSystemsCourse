# Sample code for CS6381
# Vanderbilt University
# Instructor: Aniruddha Gokhale
#
# Code taken from ZeroMQ examples with additional
# comments or extra statements added to make the code
# more self-explanatory  or tweak it for our purposes
#
# We can execute locally or in Mininet or Cloud native environments
#

import sys
import argparse  # command line parsing
import logging  # for logger
import random # for random number generator for the sleep param
import time # for sleep

# we need to import this package
import zmq

###################################
#
# Parse command line arguments
#
###################################
def parseCmdLineArgs ():
  # instantiate a ArgumentParser object
  parser = argparse.ArgumentParser (description="Client Application")
  
  # Now specify all the optional arguments we support
  
  parser.add_argument ("-n", "--name", default="tier1.1", help="This tier's name, default = tier1")

  parser.add_argument ("-p", "--port", type=int, default=4444, help="Port number on which this tier executes, default 4444")
  
  parser.add_argument ("-u", "--url", default=None, help="URL of the next tier we connect to. Not supplying anything stops the chain")
    
  parser.add_argument ("-l", "--loglevel", type=int, default=logging.DEBUG, choices=[logging.DEBUG,logging.INFO,logging.WARNING,logging.ERROR,logging.CRITICAL], help="logging level, choices 10,20,30,40,50: default 10=logging.DEBUG")
  
  return parser.parse_args()


###################################
#
# Main program
#
###################################
def main ():
  try:
    # obtain a system wide logger and initialize it to debug level to begin with
    logging.info ("Main - acquire a child logger and then log messages in the child")
    logger = logging.getLogger ("Tier")
    
    logger.debug ("Current libzmq version is %s" % zmq.zmq_version())
    logger.debug ("Current  pyzmq version is %s" % zmq.__version__)

    # first parse the arguments
    logger.debug ("Main: parse command line arguments")
    args = parseCmdLineArgs ()

    # reset the log level to as specified
    logger.debug ("Main: resetting log level to {}".format (args.loglevel))
    logger.setLevel (args.loglevel)
    logger.debug ("Main: effective log level is {}".format (logger.getEffectiveLevel ()))

    # To use ZMQ, every session needs this singleton context object
    logger.debug ("Acquire ZMQ context")
    context = zmq.Context()

    # get the poller
    logger.debug ("Acquire the poller object")
    poller = zmq.Poller ()

    #  Socket to respond to previous tier. Note that because the tier in the role of
    # server responds or replies, we create a REP socket
    logger.debug ("Obtain a REP socket for replies")
    rep = context.socket (zmq.REP)

    # Now bind this to the port we are listening on
    bind_str = "tcp://*:" + str (args.port)
    logger.debug ("Bind the REP socket for replies")
    rep.bind (bind_str)

    # register this socket for POLLIN events
    logger.debug ("Register the REP socket for POLLIN events")
    poller.register (rep, zmq.POLLIN)
    
    #  Socket to talk to next tier. Note that because the client is the "requestor", we
    # create a socket of type REQ only if there is a chain ahead of us
    req = None
    if args.url:
      logger.debug ("Obtain socket to next tier")
      req = context.socket (zmq.REQ)

      logger.debug ("Connecting to {}".format (args.url))
      # our URL could be a comma separated list. So we connect to each
      # Note, ZMQ will load balance requests to connected peers
      connect_str_list = args.url.split (",")
      for item in connect_str_list:
        connect_str = "tcp://" + item
        req.connect (connect_str)

      # register this socket for POLLIN events
      logger.debug ("Register the REQ socket for POLLIN events")
      poller.register (req, zmq.POLLIN)
    
    else:
      logger.debug ("Chain stops at this server")
    
    # handle incoming requests and propagate ahead if there is  chain
    while True:

      logger.debug ("Poller waiting for next event")
      events = dict (poller.poll ())

      # now check which socket is enabled
      if (rep in events):
        # incoming request from previous tier
        incoming_request = rep.recv_string ()
        logger.debug ("Received incoming request from previous tier: {}".format (incoming_request))
        # if we have a tier chained to us next, relay the request else reply
        # to the previous tier
        if req:
          # let us add our name to the request
          updated_request = args.name + "->" + incoming_request
          logger.debug ("Relaying updated request to next tier")
          req.send_string (updated_request)
        else:
          # We are the last in the chain. So add our name and send back
          final_reply = args.name + "->" + incoming_request
          logger.debug ("Replying {} to prev tier". format (final_reply))
          rep.send_string (final_reply)

      # if we have a chain ahead of us, then we are going to get something from
      # the next one in the chain.
      if req and (req in events):
        # incoming request from previous tier
        incoming_reply = req.recv_string ()
        logger.debug ("Relaying incoming reply from next tier: {}".format (incoming_reply))
        rep.send_string (incoming_reply)

      #sleep_time = random.choice ([0.2, 0.4, 0.6, 0.8, 1])
      sleep_time = random.choice ([0.2, 0.4, 0.6])
      time.sleep (sleep_time)
      
  except Exception as e:
    logger.error ("Exception caught in main - {}".format (e))
    return

    
###################################
#
# Main entry point
#
###################################
if __name__ == "__main__":

  # set underlying default logging capabilities
  logging.basicConfig (level=logging.DEBUG,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  main ()
    

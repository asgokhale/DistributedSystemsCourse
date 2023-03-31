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
  
  parser.add_argument ("-n", "--name", default="client", help="This client's name, default = client")

  parser.add_argument ("-i", "--iters", type=int, default=25, help="Number of iterations, default = 25")

  parser.add_argument ("-u", "--url", default="localhost:4444", help="URL of the next tier we connect to or comma separated list of tiers to connect to, default=localhost:4444")
    
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
    logger = logging.getLogger ("Client")
    
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

    #  Socket to talk to server. Note that because the client is the "requestor", we
    # create a socket of type REQ
    logger.debug ("Obtain socket to next tier")
    req = context.socket (zmq.REQ)

    logger.debug ("Connect to {}".format (args.url))
    connect_str_list = args.url.split (",")
    for item in connect_str_list:
      connect_str = "tcp://" + item
      req.connect (connect_str)
    
    # Now send a dummy req and wait for response from the chain.
    for i in range (args.iters):
      request = args.name + " request# " + str (i+1)
      logger.debug ("Sending request %s ..." % request)
      req.send_string (request)

      #  Get the reply.
      reply = req.recv_string()
      logger.debug ("Received reply %s for request [ %s ]" % (reply, request))

    # we are done so close the connection
    logger.debug ("client closing connection")
    req.close ()

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
    

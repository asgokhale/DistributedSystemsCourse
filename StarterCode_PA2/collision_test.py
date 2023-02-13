# Author: Aniruddha Gokhale
# Vanderbilt University
#
# Purpose:
#
# This code uses code suggested in
#
#     https://stackoverflow.com/questions/67219691/python-hash-function-that-returns-32-or-64-bits
#
# that retrieves as 32 or 64 bit integer from a hashlib.sha256 hash value (digest). But then, we want
# to know if this will result in any collisions. So we are going to generate a large number of
# registration strings (like what publishers or subscribers would send) as well as the Discovery
# service's string which results in a node number (to be eventually used in Chord)
#
# Instead of 64, we try 48 and at least the multiple runs of this did not show any collisions with
# a 48 bit hash. So this may be an attractive hash function to use for PA2 that is going to use Chord.

import os
import random # random number generation
import hashlib  # for the secure hash library
import argparse # argument parsing
import logging # for logging. Use it in place of print statements.

class HashCollisionTester ():
  # This is a class variable
  prefixes = ["pub", "sub", "disc"]  # our ids always start with one of these

  #################
  # constructor
  #################
  def __init__ (self, logger):
    # The following uses the hash value as key and value is the id;
    # if same hash val for another id => collision
    self.name_dict = {}
    self.iters = None
    self.num_entities = None
    self.num_hosts = None
    self.lower_port = None
    self.upper_port = None
    self.bits_hash = None
    self.logger = logger

  #################
  # configuration
  #################
  def configure (self, args):
    # Here we initialize any internal variables
    self.logger.debug ("HashCollisionTester::configure")

    self.iters = args.iters
    self.num_entities = args.num_entities
    self.num_hosts = args.num_hosts
    self.lower_port = args.lower_port
    self.upper_port = args.upper_port
    self.bits_hash = args.bits_hash

    self.logger.debug ("HashCollisionTester::Dump")
    self.logger.debug ("\tIterations = {}".format (self.iters))
    self.logger.debug ("\tNum Hosts = {}".format (self.num_hosts))
    self.logger.debug ("\tLower port = {}".format (self.lower_port))
    self.logger.debug ("\tUpper port = {}".format (self.upper_port))
    self.logger.debug ("\tBits in hash = {}".format (self.bits_hash))

  #################
  # Driver program
  #################
  def driver (self):
    self.logger.debug ("CollisionTester::driver")

    # First, seed the random number generator
    random.seed ()  

    # track the number of collisions
    num_collisions = 0
    
    # We run this code for very large number of iterations (default 1 M)
    i = 0
    while (i < self.iters):  # test for very high number of runs
      # now generate an id that we hope to use in our DHT when we supply it to our hash
      # function. It will be of the form: some prefix like pub or sub or disc, followed by
      # entity number, followed by its IP address on which it runs, followed by port num
      # it uses. Here, we do not care about reuse of port num on the same host (which is
      # what it really should be checked for)
      #
      # We could have used
      id = random.choice (HashCollisionTester.prefixes) \
          + str (random.randint (1, self.num_entities)) \
          + ":10.0.0." \
          + str (random.randint (1, self.num_hosts)) \
          + ":" \
          + str (random.randint (self.lower_port, self.upper_port)) 
      
      if i % 10000 == 0:
        # since we are running so many iterations, just to inform us that the program is
        # running so that we don't panic :-), we print something once in a while
        self.logger.debug ("iteration num {}".format (i))

      # first get the digest from hashlib and then take the desired number of bytes from the
      # lower end of the 256 bits hash. Big or little endian does not matter.
      hash_digest = hashlib.sha256 (bytes (id, "utf-8")).digest ()  # this is how we get the digest or hash value
      # figure out how many bytes to retrieve
      num_bytes = int(self.bits_hash/8)  # otherwise we get float which we cannot use below
      hash_val = int.from_bytes (hash_digest[:num_bytes], "big")  # take lower N number of bytes

      # now check if this hash val exists in our dictionary, which means collision occurred
      # for these generated ids. But note that because we are generating an id using random
      # number generation, we could also end up generating the same id and such an id will
      # obviously collide. So we ignore that and do not increment our loop counter.
      if hash_val in self.name_dict.keys ():
        # since our random generation of a string may result in duplicates, clearly this will
        # cause a collision. We do not count these collisions.
        if id != self.name_dict[hash_val]:
          self.logger.debug ("*******Collision occurred for {} bit hash {}, id {} and existing entry {}".format (self.bits_hash, hash_val, id, self.name_dict[hash_val]))
          i += 1
          num_collisions += 1
      else:
        # this hash value was seen the first time. Save the entry
        self.name_dict[hash_val] = id  # save this entry here for this hash value as this is the first time it is seen
        i += 1

    self.logger.debug ("\n********\tNumber of collisions found = {} **********".format (num_collisions))
      
###################################
#
# Parse command line arguments
#
###################################
def parseCmdLineArgs ():
  # instantiate a ArgumentParser object
  parser = argparse.ArgumentParser (description="HashCollisionTest")
  
  # Now specify all the optional arguments we support
  #
  # Specify number of bits of hash to test
  
  parser.add_argument ("-b", "--bits_hash", type=int, choices=[8,16,24,32,40,48,56,64], default=32, help="Number of bits of hash value to test for collision: allowable values between 6 and 64 in increments of 8 bytes, default 32")

  parser.add_argument ("-e", "--num_entities", type=int, default=100, help="Number of entities like pub, sub, discovery etc, default 100")

  parser.add_argument ("-i", "--iters", type=int, default=1000000, help="Number of iterations, default 1 million")

  parser.add_argument ("-n", "--num_hosts", type=int, default=10, help="Number of hosts in our mininet environment, default 10")

  parser.add_argument ("-p", "--lower_port", type=int, default=5555, help="lower bound of the port for whoever runs on the host, default 5555")

  parser.add_argument ("-P", "--upper_port", type=int, default=7777, help="upper bound of the port for whoever runs on the host, default 7777")

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
    logger = logging.getLogger ("HashCollisionTest")
    
    # first parse the arguments
    logger.debug ("Main: parse command line arguments")
    args = parseCmdLineArgs ()

    # reset the log level to as specified
    logger.debug ("Main: resetting log level to {}".format (args.loglevel))
    logger.setLevel (args.loglevel)
    logger.debug ("Main: effective log level is {}".format (logger.getEffectiveLevel ()))

    # Obtain the test object
    logger.debug ("Main: obtain the HashCollisionTest object")
    test_obj = HashCollisionTester (logger)

    # configure the object
    logger.debug ("Main: configure the test object")
    test_obj.configure (args)

    # now invoke the driver program
    logger.debug ("Main: invoke the test obj driver")
    test_obj.driver ()

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

# Author: Aniruddha Gokhale
# Vanderbilt University
#
# Purpose:
#
# Experiment generator where we create scripts that can be run on Mininet
# for now, and later for cloud Kubernetes.
#
# We ask the user to supply the topology, e.g., single,N or linear,N or
# tree,fanout=N,depth=M
# The user must also supply us the number of expected Discovery DHT nodes in the system
# and the number of publishers and subscribers. Since it is possible that multiple publishers
# and discovery DHT nodes may end up on the same host, we must also ensure that
# their port numbers are different. Hence, we also provide the user to define the base port
# number to be used by discovery (e.g., 5555) and publisher (e.g., 7777), and then we
# keep adding 1 to the port if the same service gets deployed on the same node.
#
# Since our topic helper has 9 topics, we also have to make sure that the num of topics
# published or subscribed are 5 or more so that there is some overlap.
#
# Note, our script generation logic will place these entities randomly across the nodes of
# system. We make no effort to load balance or just use round robin allocation (which would
# have been simpler). But this becomes too deterministic and sort of equally distributed
# scenario.

import os
import random # random number generation
import hashlib  # for the secure hash library
import argparse # argument parsing
import json # for JSON
import logging # for logging. Use it in place of print statements.

##########################
#
# ExperimentGenerator class.
#
# This will be our base class eventually.
# But for now we will do all mininet generation
# from here.
#
##########################
class ExperimentGenerator ():

  #################
  # constructor
  #################
  def __init__ (self, logger):
    self.num_disc_dht = None  # num of discovery DHT instances
    self.num_pub = None  # num of publishers
    self.num_sub = None  # num of subscribers
    self.disc_base_port = None  # starting port num if multiple of the same service is deployed on the node
    self.pub_base_port = None  # same for this
    self.num_mn_nodes = None # num of nodes in mininet topo; will be derived
    self.bits_hash = None # number of bits in hash value (default 48)
    self.disc_dict = {} # dictionary of generated discovery DHT instances
    self.pub_dict = {} # dictionary of generated publisher instances
    self.sub_dict = {} # dictionary of generated subscriber instances
    self.script_file = None  # for the experiment script
    self.json_file = None # for the database of DHT 
    self.logger = logger # The logger

  #################
  # configuration
  #################
  def configure (self, args):
    # Here we initialize any internal variables
    self.logger.debug ("ExperimentGenerator::configure")

    self.bits_hash = args.bits_hash
    self.num_disc_dht = args.num_disc_dht
    self.num_pub = args.num_pub
    self.num_sub = args.num_sub
    self.disc_base_port = args.disc_base_port
    self.pub_base_port = args.pub_base_port
    self.script_file = args.script_file
    self.json_file = args.json_file
    
    # Now let us parse the mininet topo and derive how many nodes
    # we have in mininet topology
    #
    # Recall that the syntax has a comma and so we can split the components using
    # comma as separator
    mn_topo = args.mn_topo.split (",")
    if (mn_topo[0] == "single" or mn_topo[0] == "linear"):
      self.num_mn_nodes = int (mn_topo[1])
    elif (mn_topo[0] == "tree"):
      fanout = int (mn_topo[1].split ("=")[1])
      depth = int (mn_topo[2].split ("=")[1])
      self.num_mn_nodes = fanout ** depth
    else:
      raise ValueError ("Bad mininet topology")

    # Now let us initialize the dictionaries. Since the entities can be deployed
    # across any host of the mininet topology, the dictionary is keyed by
    # mininet host name. We assume montonically increasing host names.
    for i in range (self.num_mn_nodes):
      # we maintain a list of entities of a type per dict. So initialize to empty
      self.disc_dict["h"+str(i+1)] = []
      self.pub_dict["h"+str(i+1)] = []
      self.sub_dict["h"+str(i+1)] = []
      
  #################
  # debugging output
  #################
  def dump (self):

    self.logger.debug ("*******ExperimentGenerator::DUMP***********")
    self.logger.debug ("Num of bits in hash fn = {}".format (self.bits_hash))
    self.logger.debug ("Num DHT instances = {}".format (self.num_disc_dht))
    self.logger.debug ("Num pubs = {}".format (self.num_pub))
    self.logger.debug ("Num subs = {}".format (self.num_sub))
    self.logger.debug ("Base discovery port = {}".format (self.disc_base_port))
    self.logger.debug ("Base pub port = {}".format (self.pub_base_port))
    self.logger.debug ("Num Mininet nodes = {}".format (self.num_mn_nodes))
    self.logger.debug ("Discovery dictionary = {}".format (self.disc_dict))
    self.logger.debug ("Publisher dictionary = {}".format (self.pub_dict))
    self.logger.debug ("Subscriber dictionary = {}".format (self.sub_dict))
    self.logger.debug ("**************************************************")

  #################
  # hash value
  #################
  def hash_func (self, id):
    self.logger.debug ("ExperimentGenerator::hash_func")

    # first get the digest from hashlib and then take the desired number of bytes from the
    # lower end of the 256 bits hash. Big or little endian does not matter.
    hash_digest = hashlib.sha256 (bytes (id, "utf-8")).digest ()  # this is how we get the digest or hash value
    # figure out how many bytes to retrieve
    num_bytes = int(self.bits_hash/8)  # otherwise we get float which we cannot use below
    hash_val = int.from_bytes (hash_digest[:num_bytes], "big")  # take lower N number of bytes

    return hash_val

  #################
  # gen dictionary values
  #
  # called by the populate method
  #################
  def gen_dict_values (self, prefix, index):
    self.logger.debug ("ExperimentGenerator::gen_dict_values")

    # here we generate the dictionary values.
    # prefix, such as pub, sub or disc must be specified
    # index should be monotonically increasing.

    # generate our id
    id = prefix + str (index)

    # generate a host on which we will deploy this entity
    mn_host_num = random.randint (1, self.num_mn_nodes)
    host = "h" + str (mn_host_num)
    ip = "10.0.0." + str(mn_host_num)

    # if there already is a service of that type running on that host
    # then, we cannot reuse that port and so must generate the next
    # port in the sequence
    if prefix == "disc":
      port = self.disc_base_port + len (self.disc_dict[host])
    elif prefix == "pub":
      port = self.pub_base_port - len (self.pub_dict[host])
    else:
      port = None

    # return the generated parameters
    return id, host, ip, port
  
  #################
  # check for collision
  #
  #################
  def check4collision (self, hash_val, dictionary):
    self.logger.debug ("ExperimentGenerator::check4collision")

    # check the dictionary if the hash value already exists
    for i in range (self.num_mn_nodes):
      host_list = dictionary["h"+str (i+1)]
      for nested_dict in host_list:
        if nested_dict["hash"] == hash_val:
          return True

    return False # otherwise
  
  #################
  # populate a given dict.
  #
  # Generic method
  #################
  def populate_dict (self, prefix, num_entities):
    self.logger.debug ("ExperimentGenerator::populate_dict")

    # populate the dictionary corresponding to the entity
    # we are dealing with (identified by prefix). Ensure
    # that there is no duplicate and no hash collision on the
    # generated name (but that means our hash fn is not good)
    #
    # We can guarantee no duplicate because we will be
    # generating sequentially for each entity and
    # not randomly but must check for collision

    # check if no prefix is passed
    if not prefix:
      raise ValueError ("populate_dict::prefix not supplied")

    # Since we are making this a generic method (exploiting the fact that
    # all dictionaries look very similar), so we must set the handle to
    # point to the correct dictionary
    if prefix == "disc":
      target_dict = self.disc_dict
    elif prefix == "pub":
      target_dict = self.pub_dict
    elif prefix == "sub":
      target_dict = self.sub_dict
    else:
      raise ValueError ("populate_dict::unknown prefix: {}".format (prefix))
      
    for i in range (num_entities):
      collision = True  # assume there is collision
      while (collision):
        # keep generating values until no collision
        id, host, ip, port = self.gen_dict_values (prefix, index=i+1)
        if port:
          string = id + ":" + ip + ":" + str (port)  # will be the case for disc and pubs
        else:
          string = id + ":" + ip  # will be the case for subscribers

        # now get the hash value for this string
        hash_val = self.hash_func (string)
        
        # check if this hash value already exists anywhere in our dict
        collision = self.check4collision (hash_val, target_dict)
        if collision:
          self.logger.debug ("ExperimentGenerator::populate_dict -- collision occurred for string {}".format (str))

      # now that we know that the generated values do not cause collision
      # insert it into our dictionary
      target_dict[host].append ({"id": id, "hash": hash_val, "IP": ip, "port": port})

  #######################
  # Generate the experiment script
  #
  # Change/extend this code to suit your needs
  #######################
  def gen_exp_script (self):
    self.logger.debug ("ExperimentGenerator::gen_exp_script")

    # Here we are going to generate the command line to run each
    # entity in our system, which otherwise would have to be done
    #manually
    with open (self.script_file, "w") as f:

      # Let us first generate all the commands to run the dictionary DHT nodes
      # I am thinking that because we now have multiple Discovery instances
      # due to the DHT ring, we may need to supply an ID plus we need to supply a
      # database of all the DHT nodes via a json file. So I am extending the
      # params. Alternately, you can send it via config.ini. Still somewhere we need
      # to extend.
      for i in range (self.num_mn_nodes):
        host = "h" + str (i+1)
        host_list = self.disc_dict[host]
        for nested_dict in host_list:
          cmdline = host + " python3 DiscoveryAppln.py " + \
            "-n " + nested_dict["id"]  + " " + \
            "-j " + self.json_file + " " + \
            "-p " + str(nested_dict["port"]) + " " + \
            "-P " + str(self.num_pub) + " " + \
            "-S " + str(self.num_sub) + " " + \
            "> " + nested_dict["id"] + ".out 2>&1 &\n"
          f.write (cmdline)

      # Do similar things with publishers. Here I am suggesting that we pass
      # the same JSON file to publisher and then it decides which discovery service
      # to use from among all the nodes (pick at random) or for experiments
      # choose one by one.  So we remove the "-d <discovery details>" and instead
      # add "-j <json>"
      for i in range (self.num_mn_nodes):
        host = "h" + str (i+1)
        host_list = self.pub_dict[host]
        for nested_dict in host_list:
          # generate intested in topics in the range of 5 to 9 because
          # our topic helper currently has 9 topics in it.
          num_topics = random.randint (5, 9)
          frequency = random.choice ([0.25, 0.5, 0.75, 1, 2, 3, 4])
          iterations = random.choice ([1000, 2000, 3000])

          # build the command line
          cmdline = host + " python3 PublisherAppln.py " + \
            "-n " + nested_dict["id"]  + " " + \
            "-j " + self.json_file + " " + \
            "-a " + str(nested_dict["IP"]) + " " + \
            "-p " + str(nested_dict["port"]) + " " + \
            "-T " + str(num_topics) + " " + \
            "-f " + str(frequency) + " " + \
            "-i " + str(iterations) + " " + \
            "> " + nested_dict["id"] + ".out 2>&1 &\n"
          f.write (cmdline)

      # Do similar things with subscribers. Here I am suggesting that we pass
      # the same JSON file to subscriber and then it decides which discovery service
      # to use from among all the nodes (pick at random) or for experiments
      # choose one by one.  So we remove the "-d <discovery details>" and instead
      # add "-j <json>"
      for i in range (self.num_mn_nodes):
        host = "h" + str (i+1)
        host_list = self.sub_dict[host]
        for nested_dict in host_list:
          # generate intested in topics in the range of 5 to 9 because
          # our topic helper currently has 9 topics in it.
          num_topics = random.randint (5, 9)

          # build the command line
          cmdline = host + " python3 SubscriberAppln.py " + \
            "-n " + nested_dict["id"]  + " " + \
            "-j " + self.json_file + " " + \
            "-T " + str(num_topics) + " " + \
            "> " + nested_dict["id"] + ".out 2>&1 &\n"
          f.write (cmdline)

      
    f.close ()
          
  #######################
  # Generate the JSONified DB of DHT nodes
  #
  # Change/extend this code to suit your needs
  #######################
  def jsonify_dht_db (self):
    self.logger.debug ("ExperimentGenerator::jsonify_dht_db")

    # first get an in-memory representation of our DHT DB, which is a
    # dictionary with key dht
    dht_db = {}  # empty dictionary
    dht_db["dht"] = []
    for i in range (self.num_mn_nodes):
      host = "h" + str (i+1)
      host_list = self.disc_dict[host]
      for nested_dict in host_list:
        dht_db["dht"].append ({"id": nested_dict["id"], "hash": nested_dict["hash"], \
                               "IP": nested_dict["IP"], "port": nested_dict["port"], "host": host})
    
    # Here we are going to generate a DB of all the DHT node details and
    # save it as a json file
    with open (self.json_file, "w") as f:
      json.dump (dht_db, f)
      
    f.close ()
          

  #################
  # Driver program
  #################
  def driver (self):
    self.logger.debug ("ExperimentGenerator::driver")

    # Just dump the contents
    self.dump ()
    
    # First, seed the random number generator
    random.seed ()  

    # Now generate the entries for our discovery dht nodes
    self.populate_dict ("disc", self.num_disc_dht)

    # Now generate the entries for our publishers
    self.populate_dict ("pub", self.num_pub)

    # Now generate the entries for our subscribers
    self.populate_dict ("sub", self.num_sub)

    self.dump ()

    # Now JSONify the DHT DB
    self.jsonify_dht_db ()
    
    # Now generate experiment script
    self.gen_exp_script ()
      
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
  parser.add_argument ("-b", "--bits_hash", type=int, choices=[8,16,24,32,40,48,56,64], default=48, help="Number of bits of hash value to test for collision: allowable values between 6 and 64 in increments of 8 bytes, default 48")

  parser.add_argument ("-D", "--num_disc_dht", type=int, default=20, help="Number of Discovery DHT instances, default 20")

  parser.add_argument ("-P", "--num_pub", type=int, default=5, help="number of publishers, default 5")
  
  parser.add_argument ("-S", "--num_sub", type=int, default=5, help="number of subscribers, default 5")

  parser.add_argument ("-d", "--disc_base_port", type=int, default=5555, help="base port for discovery, default 5555")

  parser.add_argument ("-p", "--pub_base_port", type=int, default=7777, help="base port for publishers, default 7777")

  parser.add_argument ("-t", "--mn_topo", default="single,20", help="Mininet topology, default single,20 - other possibilities include linear,N or tree,fanout=N,depth=M")

  parser.add_argument ("-f", "--script_file", default="mnexperiment.txt", help="Experiment file to be sourced from Mininet prompt, default mnexperiment.txt")

  parser.add_argument ("-j", "--json_file", default="dht.json", help="JSON file with the database of all DHT nodes, default dht.json")

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
    logger = logging.getLogger ("ExperimentGenerator")
    
    # first parse the arguments
    logger.debug ("Main: parse command line arguments")
    args = parseCmdLineArgs ()

    # reset the log level to as specified
    logger.debug ("Main: resetting log level to {}".format (args.loglevel))
    logger.setLevel (args.loglevel)
    logger.debug ("Main: effective log level is {}".format (logger.getEffectiveLevel ()))

    # Obtain the test object
    logger.debug ("Main: obtain the ExperimentGenerator object")
    gen_obj = ExperimentGenerator (logger)

    # configure the object
    logger.debug ("Main: configure the generator object")
    gen_obj.configure (args)

    # now invoke the driver program
    logger.debug ("Main: invoke the driver")
    gen_obj.driver ()

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

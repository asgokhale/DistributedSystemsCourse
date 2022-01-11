This directory contains code to showcase coordination for barrier
synchronization in mininet-based emulated system.  Here both the
driver and client applications are individual processes instead of the
thread-based approach as depicted in the thread-based approach.

As before, the driver program creates a parent barrier znode called
"/barrier". Each client application then creates a child to denote
itself under the parent znode. When the total number of children
reaches the expected barrier value, all clients come to know this and
the different processes end after cleaning up everything. 

Suppose we start a mininet topology as follows:

prompt> sudo mn --topo=tree,depth=3,fanout=2
*** Creating network
*** Adding controller
*** Adding hosts:
h1 h2 h3 h4 h5 h6 h7 h8 
*** Adding switches:
s1 s2 s3 s4 s5 s6 s7 
*** Adding links:
(s1, s2) (s1, s5) (s2, s3) (s2, s4) (s3, h1) (s3, h2) (s4, h3) (s4, h4) (s5, s6) (s5, s7) (s6, h5) (s6, h6) (s7, h7) (s7, h8) 
*** Configuring hosts
h1 h2 h3 h4 h5 h6 h7 h8 
*** Starting controller
c0 
*** Starting 7 switches
s1 s2 s3 s4 s5 s6 s7 ...
*** Starting CLI:
mininet> 

Make sure you have started the ZooKeeper server on one of the mininet
hosts, say, h1 as follows:

mininet> xterm h1

Note: h1 will get an IP address of 10.0.0.1 by default.

h1> cd <your distribution of zookeeper>
h1> ./bin/zkServer.sh start

Then run

mininet> xterm h2

h2> python zkbarrier_driver.py -a 10.0.0.1

If you have a small number of barrier group, you can create xterms for
each host and do something like this:

h3> python zkbarrier_client.py -a 10.0.0.1 C1
h4> python zkbarrier_client.py -a 10.0.0.1 C2
h5> python zkbarrier_client.py -a 10.0.0.1 C3
h6> python zkbarrier_client.py -a 10.0.0.1 C4
h7> python zkbarrier_client.py -a 10.0.0.1 C5

If you have very large number of barrier processes, you can create a
commands.txt file like the sample provided and do the following
instead. Note that this command file is for the hosts in this topology:

mininet> source commands.txt

If you use the commands.txt file, there will be a bunch of debug o/p
generated in several out files. You will need to manually delete these
after the experiment is done and you have had a chance to observe the
debug o/p

*** Also, before exiting from mininet, make sure to stop the zookeeper
server by doing

./bin/zkServer.sh stop


General Usage:
--------------
Driver Program
--------------
prompt> python zkbarrier_driver.py -h
Demo program for ZooKeeper-based Barrier Sync
usage: zkbarrier_driver.py [-h] [-a ZKIPADDR] [-c NUMCLIENTS] [-p ZKPORT]

optional arguments:
  -h, --help            show this help message and exit
  -a ZKIPADDR, --zkIPAddr ZKIPADDR
                        ZooKeeper server ip address, default 127.0.0.1
  -c NUMCLIENTS, --numClients NUMCLIENTS
                        Number of client apps in the barrier, default 5
  -p ZKPORT, --zkPort ZKPORT
                        ZooKeeper server port, default 2181


Client Program
--------------
prompt> python zkbarrier_client.py -h
Demo program for ZooKeeper-based Barrier Sync: Client Appln
usage: zkbarrier_client.py [-h] [-a ZKIPADDR] [-c COND] [-p ZKPORT] name

positional arguments:
  name                  client name

optional arguments:
  -h, --help            show this help message and exit
  -a ZKIPADDR, --zkIPAddr ZKIPADDR
                        ZooKeeper server ip address, default 127.0.0.1
  -c COND, --cond COND  Barrier Condition representing number of client apps
                        in the barrier, default 5
  -p ZKPORT, --zkPort ZKPORT
                        ZooKeeper server port, default 2181

Files in the directory:
-----------------------
zkbarrier_driver.py  (driver program)
zkbarrier_client.py (client application program running as a process)

README.txt (this file)

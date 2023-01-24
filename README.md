# DistributedSystemsCourse
Scaffolding code for the Vanderbilt University CS 6381 Distributed Systems class
Instructor: Aniruddha Gokhale

This is the top-level README file explaining what all is in this directory
and a general set of recommendations for the order in which we can
browse through these.  See the individual README files in each directory
for more explanation on each of individual code bases.

(0) POSIX_Sockets
I give it a number 0 because it is optional. The purpose of showcasing this
code is to give the student an idea as to how hard and error-prone it can
become to write even simple client-server programs using low-level sockets.
This then motivates the use of higher level frameworks like ZeroMQ.

(1) ZeroMQ
Since our Distributed Systems class will use ZeroMQ as the underlying
middleware to develop our assignment solutions, the first set of examples
one must go through are the ones in the ZeroMQ directory. These examples
are taken from the ZeroMQ guide but modified a bit to suit our purpose.

Note that ZeroMQ offers the the right level of abstraction for the Distributed
Systems class because it provides a sufficiently higher-level of abstraction
where we as the developer need not be too concerned with low-level,
accidental challenges. At the same time, it does not provide full-scale
solutions like what Kafka or other frameworks do; rather we will need to
use ZeroMQ to build solutions like Kafka.

(3) InfluxDB_ZMQ
We are going to collect a whole bunch of metrics in our assignments. Since
most of this is going to be time series data (e.g., a publisher inserts a
sending time stamp, receiver stamps its timestamp, etc), we will store
all of such collected data in a time series database like InfluxDB. We will use
the Python binding to insert the data into InfluxDB.

Status: Currently TO-DO

(4) Flatbuf_ZMQ
Serialization (or marshaling) is an important aspect of any networked system.
To that end, here we showcase the use of the Flat Buffers serialization technology
and how it can be used to send/receive serialized data types across the
network via ZeroMQ. This will be necessary for Assignment 2 onward.

(5) MininetGenerator
Mininet is a framework that allows a user to emulate arbitrarily complex
networking topologies on a single laptop (say inside our VirtualBox VM). We
can test our distributed systems code (and as such all these scaffolding code)
on mininet-generated topologies. This can be used to place publishers and
subscribers on desired hosts of our specified topology, and then the code
can execute and tested in such a setup before we attempt it in a real distributed
setup such as on real distributed nodes or in a kubernetes cluster.

(5) Kademlia DHT
We will be studying DHT-based discovery/lookup. To that end, we will use an
elegant solution called Kademlia for publishers and subscribers to discover
each other.  This codebase shows a simple example that can use a mininet
generated topology (from the above) to place our nodes.  It can also be used
locally on a laptop as well as in a Kubernetes cluster.

Status: Kubernetes part is still TO-DO

(6) ZooKeeper
Apache ZooKeeper is a coordination framework. We will be using ZooKeeper
in our Assignments 3 and 4.

(7) Paxos_wDocker_nMininet
A simple implementation of single degree Paxos and realized as containerized
execution units. Can also be executed on emulated networks via Mininet.

(8) MCAST_ZMQ
ZeroMQ with multicast.

Status: Still needs work as we haven't gotten things working yet with the
egpm protocol.

(9) StarterCode_ProgAssign
This is the code that students use to get started with the programming assignments.



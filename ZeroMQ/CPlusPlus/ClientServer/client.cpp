// Sample code for CS6381
// Vanderbilt University
// Instructor: Aniruddha Gokhale
//
// Code taken from ZeroMQ examples with additional
// comments or extra statements added to make the code
// more self-explanatory  or tweak it for our purposes
//
// We are executing these samples on a Mininet-emulated environment
//
//



//
//  Hello World client in C++
//  Connects REQ socket to tcp://localhost:5555
//  Sends "Hello" to server, expects "World" back
//
#include <zmq.hpp>
#include <string>
#include <iostream>

int main (int argc, char *argv[])
{
    //  Prepare our context and socket
    zmq::context_t context (1);
    zmq::socket_t socket (context, ZMQ_REQ);

    std::cout << "Connecting to hello world server...." << std::endl;
    std::string connect_str = "tcp://";
    if (argc == 2)
        connect_str += argv[1];
    else
        connect_str += "localhost";
    connect_str += ":5555";
          
    // socket.connect ("tcp://localhost:5555");
    socket.connect (connect_str.c_str ());

    //  Do 10 requests, waiting each time for a response
    for (int request_nbr = 0; request_nbr != 10; request_nbr++) {
        zmq::message_t request (5);
        memcpy (request.data (), "Hello", 5);
        std::cout << "Sending Hello " << request_nbr << "..." << std::endl;
        socket.send (request);

        //  Get the reply.
        zmq::message_t reply;
        socket.recv (&reply);
        std::cout << "Received World " << request_nbr << std::endl;
    }
    return 0;
}

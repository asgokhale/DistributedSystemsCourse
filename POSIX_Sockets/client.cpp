// $Id$

/*
  Author : Aniruddha Gokhale
  Date: Spring 2020
  
  Developed for CS6381. Based on code developed several years back for CS3281 course.

  This is the client program.

 */

#include <iostream>
#include <string>
using namespace std;

#include <sys/types.h>      // for various data types
#include <sys/socket.h>     // for socket API
#include <netdb.h>            // for getaddrinfo
#include <netinet/in.h>      // for sockaddr_in
#include <arpa/inet.h>       // for inet_addr
#include <unistd.h>           // for getpid ()
#include <sys/time.h>        // for timing
#include <string.h>            // for memset
#include <stdlib.h>            // for atoi

// include our macros header
#include "macros.h"

/* 
   This is the factorial client. It asks the user for an input number
   whose factorial is to be computed. It then sends this request to
   the factorial server, which will return it the value.

   The client, very similar to the server, has to do some
   initialization in order to establish connection with server and do
   network I/O.
*/
// server main function
int main (int argc, char *argv[])
{ 
    // first declare the variables
    string  port_num;               // port number is unsigned short
    string  serv_ip_name;           // IP addr name of server
    CS6381_SOCK_HANDLE conn_sock;    // socket handle for connection
    addrinfo  *server_addr = 0;     // required for connect (See below)
    addrinfo  addr_hint;            // required for getaddrinfo (See below)
    long number;           // the number whose factorial is
                                    // to be found.
    unsigned long iters;           // number of iterations
    long result;           // factorial of "number"

    /**************** real program starts here **************/

    // we do some command line parsing
    // to find out what is the ip address of the server, open a shell
    // on the OS you are working on and type:
    // ipconfig /all     (this works on windows)
    //
    // or
    //
    // ifconfig or netstat -i or nslookup hostname        (this works on Linux)
    if (argc != 5) {
        cerr << "Usage: client <ip addr> <port> <number> <iterations>" << endl;
        return -1;
    }

    // retrieve all the parameters
    serv_ip_name = argv[1];
    port_num = argv[2];
    number = atoi (argv[3]);
    iters = atoi (argv[4]);

    cout << "Client connecting with host: " << serv_ip_name
         << " at port number: " << port_num 
         << " requesting factorial of: " << number
         << " and num iterations: " << iters << endl;
       
    /* Now let us initialize the client */

    //
    // STEP (1)
    // initialize the socket for the port we will use to connect to
    // server and do I/O
    conn_sock = socket (AF_INET,      // use IPv4 family
                        SOCK_STREAM,  // full duplex byte stream
                        0);           // protocol type (TCP)

    // error checking
    if (conn_sock == -1) {
        perror ("socket failed");
        cerr << "Client: socket call failed" << endl;
        return -1;
    }
                          
    // STEP (2)
    //
    // Now we must connect to the server. 
    // A client is considered to be the active entity because it
    // initiates a dialog with the server. On the other hand the
    // server is a passive entity
    //
    // (2a) first make sure we reset the structure. We do not want any
    // garbage values in this structure.
    memset (&addr_hint, 0, sizeof (addrinfo));

    // (2b) set the fields of the structure giving some hints to the OS on what
    // we are looking for.  We are going to use the new style of getting the
    // host address information.  Previous techniques used either gethostbyname
    // (if the host name was a fully qualified name) or inet_addr (if the host
    // was in dotted decimal form).  But these APIs will be deprecated in future
    // and hence we will use the new style.

    /* Here is how the addrinfo structure looks like:

       struct addrinfo {
           int ai_flags;
           int ai_family;
           int ai_socktype;
           int ai_protocol;
           size_t ai_addrlen;
           char* ai_canonname;
           struct sockaddr* ai_addr;
           struct addrinfo* ai_next;
        };

       Please see a nice description here:
       http://msdn2.microsoft.com/en-us/library/ms737530.aspx
    */

    addr_hint.ai_flags = 0;   // if we are a server, we would have used
                              // AI_PASSIVE to indicate we are passive listener
    addr_hint.ai_family = AF_INET;  // IPv4 family, use AF_INET6 for IPv6
    addr_hint.ai_socktype = SOCK_STREAM; // full duplex byte stream
    addr_hint.ai_protocol = IPPROTO_TCP;  // TCP protocol to be used

    // 2(c) call the new API
    int ret_status 
      = getaddrinfo (serv_ip_name.c_str (),  // node name we are looking up
                     port_num.c_str (),      // port number or service name like FTP
                     &addr_hint,    // hint you are passing to the OS
                     &server_addr);
    if (ret_status != 0){
      // something went wrong
      cerr << "getaddrinfo failed" << endl;
      // use a new API to print error message
      gai_strerror (ret_status);
    }

    // at this point we should have the server_addr structure filled up by the
    // getaddrinfo API. Moreover, if the host to whom we are planning to connect
    // to has many different names, we will actually get back a linked list.

    // 2(d) Now actively establish connection
    int conn_status;
    conn_status =
        connect (conn_sock,    // this was the connection socket handle we
                               // created earlier
                 // the second arg is supposed to be of type "sockaddr" which is
                 // a typedef declared in the OS headers to represent a generic
                 // network family. If we had used the older style of doing
                 // things, we would have used the sockaddr_in data
                 // structure. Therefore, now we would have required to  cast
                 // the sockaddr_in to sockaddr 
                 //
                 // Note we cannot use "static_cast" since the two types are
                 // different. Therefore, we ask the compiler to  reinterpret
                 // the type by using the C++ reinterpret_cast command. 
                 //
                 // No more of such things are needed anymore.
                 server_addr->ai_addr,
                 // indicate the size of the structure
                 server_addr->ai_addrlen);

    // error checking
    if (conn_status == -1 ) {
        perror ("connect failed:");
        cerr << "Server: connect failed" << endl;
        return -1;
    }

    // 2(e) since we got back the struct addrinfo link list, we need to free
    // it.  Call the API.
    freeaddrinfo (server_addr);

    cout << "Client: ESTABLISHED A CONNECTION" << endl;


    // The I/O with server starts here. We time the round trip delay
    cout << "Client is now sending data and receiving results" << endl;

    // for now we send the number. Remember to convert to network
    // format 
    long temp; // we are using this for network formatted number
    int send_status;   // return status of send/recv
    int recv_status;
    timeval start_time;   // used in timing measurements
    timeval end_time;

    for (int i = 0; i < iters; ++i) {
        /* TIME THE ROUND TRIP LATENCY */
        // on Linux we use the "gettimeofday" function that keeps
        // retrieves elapsed time since Jan 1, 1970
        //
        // the timeval structure has 2 fields defined as follows
        // struct timeval {
        //     long tv_sec;  // time in seconds
        //     long tv_usec; // time in microseconds
        // };
        if (gettimeofday (&start_time,  // timeval structure
                          0) == -1) {   // ignore timezone stuff
            perror ("gettimeofday");
            cerr << "Client: gettimeofday failed" << endl;
            return -1;
        }

        // convert our number to network format before sending. This is the
        // marshaling
        temp = htonl (number);
        
        // send the number
        send_status = 
            send (conn_sock, // I/O is done on this socket handle
                  // second parameter is the buffer you send
                  (void *) &temp,
                  // 3rd param is the length of the buffer
                  sizeof (long),
                  // we ignore the flags argument
                  0);
        
        // error checking
        if (send_status == -1) {
            perror ("send failed");
            cerr << "Client: sending number failed" << endl;
            return -1; // note we should really cleanup but we ignore it
        }

        // Now we expect the server to send us a reply. So we block until
        // we receive something
        recv_status =
            recv (conn_sock,  // I/O done with new sock
                                // handle
                                // second parameter is a buffer into
                                // which you receive data
                                // We have an understanding with the
                                // client that the first thing we will
                                // receive is the number whose
                                // factorial is to be computed
                                //
                                // Windows needs a (char *) buffer
                                // while Linux needs a (void *) buffer
                                // hence we have to do the following
                                (void *)&temp,
                                // third parameter is the size of the
                                // buffer
                                sizeof (long),
                                // last parameter is a flag that we
                                // will ignore.
                                0);

        // network I/O is tricky. Sometime you do not receive all the
        // bytes you have requested. I am not going to check for this
        // condition. On Linux you can force the kernel to not return
        // until all the requested bytes are read by using a special
        // flag that does not seem to be available on Windows.
        // The only error checking that we do is thus failed "recv"
        if (recv_status == -1) {
            perror ("recv failed");
            cerr << "Client: recv failed" << endl;
            return -1; // note we should really cleanup but we ignore it
        }

        // Get ending timing
        if (gettimeofday (&end_time,  // timeval structure
                          0) == -1) {   // ignore timezone stuff
            perror ("gettimeofday");
            cerr << "Client: gettimeofday failed" << endl;
            return -1;
        }


        // convert the received result to host format. This is unmarshaling.
        result = ntohl (temp);

        cout << "Client: Received result = " << result << endl;

        // print the roundtrip latency
        // convert everything to milliseconds
        cout << "Roundtrip Latency on Linux for iteration: " << i << " = "
               << ((end_time.tv_sec*1000.0 + end_time.tv_usec/1000.0) -
                       (start_time.tv_sec*1000.0 + start_time.tv_usec/1000.0))
               << " milliseconds " << endl;

    }

    // send a 0 to the server so it stops its activity with this client
    temp = 0;
    temp = htonl (temp);
    
    // send the number
    send_status = 
        send (conn_sock, // I/O is done on this socket handle
              // second parameter is the buffer you send
              (void *) &temp,
              // 3rd param is the length of the buffer
              sizeof (long),
              // we ignore the flags argument
              0);
        
    // error checking
    if (send_status == -1) {
        perror ("send failed");
        cerr << "Client: sending -1 failed" << endl;
        return -1; // note we should really cleanup but we ignore it
    }
    
    // STEP 6: close the handle because we are done
    cout << "Client: closing the connection" << endl;
    (void) close (conn_sock);

    return 0;
}

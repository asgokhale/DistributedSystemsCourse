// $Id$

/*
  Author : Aniruddha Gokhale
  Date: Spring 2020
  
  Developed for CS6381. Based on code developed several years back for CS3281 course.

  This is the server program.

 */

#include <iostream>
#include <string>
using namespace std;

#include <sys/types.h>       // for various data types
#include <sys/socket.h>     // for socket API
#include <netdb.h>            // for getaddrinfo
#include <netinet/in.h>      // for sockaddr_in
#include <arpa/inet.h>       // for inet_addr
#include <unistd.h>           // for getpid ()
#include <string.h>            // for memset
#include <limits.h>            // for system defined macros

// include our macros header
#include "macros.h"

/*
  Computes the factorial
 */
long factorial (long num)
{
    if (num == 1 || num == 2)
        return num;
    else
        return num * factorial (num - 1);
}

/* 
   The server we are implementing below is an iterative server wherein the
   client request is served iteratively in a loop one client at a time. In
   other words only one client will get served at a time.

   Making it concurrent is not a big deal. We simply need to serve every new
   incoming client in a separate thread or child process.

*/
// server main function
int main (int argc, char *argv[])
{ 
    // first declare the variables
    u_short temp_port;                           // port number is unsigned short
    char port_num[10];                           // string representation of port number
    char host[_POSIX_HOST_NAME_MAX];       // my host name on which the service will be running
    CS6381_SOCK_HANDLE listen_sock;   // socket handle for listening port
    CS6381_SOCK_HANDLE conn_sock;    // socket handle for accepted connection
    addrinfo  *server_addr = 0;               // required for bind (See below)
    addrinfo  addr_hint;                           // required for getaddrinfo (See below)
    long number, result;            // input and output values

    /**************** real program starts here **************/

    cout << "***************************************************" << endl;
    cout << "Welcome to the Iterative Factorial Server" << endl;
    cout << "\tServer will serve one client at a time. It expects the" << endl;
    cout <<"\tclient to send it a number whose factorial is to be found." <<
    endl;
    cout << "\tIt will keep computing this factorial until the client sends "
    << endl;
    cout << "\ta terminating token" << endl;
    cout << "***************************************************" << endl;

    /* Now let us initialize the server */

    // in order to ensure that there is no conflict on the listen
    // port, I am going to use the process ID, which is unique on the
    // OS, and add 10000 to it.
    temp_port = 10000 + (u_short)CS6381_GETPID ();
    sprintf (port_num, "%d", temp_port);                   // we need to convert it to string
    cout << "Initializing the server on port = " << port_num << endl;

    // get our host name  (this step is only for demonstration purpose)
    if (gethostname (host, _POSIX_HOST_NAME_MAX) == -1) {
      cerr << "gethostname failed" << endl;
      return -1;
    }

    cout << "Initializing service on " << host << " on port number " << port_num
         << endl;

    // STEP (1)
    // initialize the socket for the port we will listen on
    // A socket is a handle created by the operating system that
    // serves as the "end-point" through which network I/O can be
    // performed. Note, however, that simply creating a socket handle
    // does not immediately allow the server to start receiving client
    // requests. As shown in the different steps below, the socket
    // handle must first be associated with the network interface of
    // the machine. Only then can you start listening for incoming
    // requests. When a client sends a "connection establish" request,
    // the server will accept is using the "accept" command shown
    // below. Therefter the client and server exchange messages until
    // the session is over in which case both parties close the socket
    // handles.
    listen_sock = socket (AF_INET,      // use IPv4 family
                                     SOCK_STREAM,  // full duplex byte stream
                                     0);           // protocol type (TCP)

    // error checking
    if (listen_sock == -1) {
        perror ("socket failed");
        cerr << "Server: socket call failed" << endl;
        return -1;
    }
                          
    // STEP (2)
    // now we need to bind the socket handle to the network interface
    // over which we intend to receive incoming requests. In the older
    // approach we always used INADDR_ANY to indicates that we will 
    // receive request over any network interface that this machine has.
    // To do this we must first initialize a structure whose type is
    // "struct sockaddr_in"
    //
    // In the new approach using the addrinfo data structure, we no longer
    // need to do this. We must however create a "hints" data structure
    // to tell the OS what we are interested in.
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

    addr_hint.ai_flags = AI_PASSIVE;   // if we are a server, we need to use
                                       // AI_PASSIVE to indicate we are passive
                                       // listener 
    addr_hint.ai_family = AF_INET;     // IPv4 family, use AF_INET6 for IPv6
    addr_hint.ai_socktype = SOCK_STREAM;  // full duplex byte stream
    addr_hint.ai_protocol = IPPROTO_TCP;  // TCP protocol to be used

    // 2(c) call the new API
    int ret_status 
      = getaddrinfo (0,             // either pass the host name to indicate the
                                              // interface it will listen on else pass a 0
                                              // to indicate any interface - does the same
                                               // thing as INADDR_ANY
                     port_num,      // port number or service name like FTP
                     &addr_hint,    // hint you are passing to the OS
                     &server_addr); // the list of addresses allocated returned
                                    // to you by the OS (you need to free it)
    if (ret_status != 0){
      // something went wrong
      cerr << "getaddrinfo failed" << endl;
      // use a new API to print error message
      gai_strerror (ret_status);
    }
    
    // (2d) Now actually make the association via the "bind" call
    int bind_status;
    bind_status =
        bind (listen_sock,    // this was the listen socket handle we
                              // created earlier
              // the second arg is supposed to be of type "sockaddr"
              // which is a typedef declared in the OS headers to 
              // represent a generic network family. However, in the older 
              // style we used the IPv4 family and hence had initialized
              // the "sockaddr_in" structure. Therefore, now we must
              // cast the sockaddr_in to sockaddr
              //
              // Note we cannot use "static_cast" since the two types
              // are different. Therefore, we ask the compiler to 
              // reinterpret the type by using the C++
              // reinterpret_cast command
              // 
              // reinterpret_cast<sockaddr*> (&server_addr),
              // no more of such a thing is necessary with the newer API
              server_addr->ai_addr,
              // indicate the size of the structure
              server_addr->ai_addrlen);

    // error checking
    if (bind_status == -1 ) {
        perror ("bind failed");
        cerr << "Server: bind failed" << endl;
        return -1;
    }

    // 2(e) since we got back the struct addrinfo link list, we need to free
    // it.  Call the API.
    freeaddrinfo (server_addr);

    cout << "Server: Address is bound" << endl;

    // STEP 3: Now indicate to the OS that the server is ready to
    // start listening for incoming connection establishment requests
    // from some client.
    int listen_status;
    listen_status = listen (listen_sock, // our listen sockethandle
                                       5);              // backlog parameter (don't worry)

    // error checking
    if (listen_status == -1) {
        perror ("listen failed");
        cerr << "Server: listen failed" << endl;
        return -1;
    }

    // STEP 4: Now accept any incoming connection. Note that we are a
    // server and hence we are supposed to accept connections
    // forever. Therefore, we do the following logic inside an
    // infinite loop

    for (;;) {

        cout << "Server: WAITING TO ACCEPT A NEW CONNECTION" << endl;

        // the accept command shown below actually does the job of
        // the TCP/IP 3-way handshaking protocol when a client
        // requests a connection establishment.
        //
        // Note that the accept command creates a new socket handle as
        // the return value of "accept". Understand that this is
        // necessary because in order to serv several clients
        // simultaneously, the server needs to distinguish between
        // the handle it uses to listen for new connections requests
        // and the handle it uses to perform network I/O with the
        // client. Thus, the newly created socket handle is used to do
        // the network I/O whereas the older socket handle continues
        // to be used for listening purposes.
        conn_sock = accept (listen_sock, // our listen sock handle
                            0,  // we don't care about details of client
                            0); // hence length = 0

        // error checking
        if (listen_status == -1) {
            perror ("accept failed");
            cerr << "Server: accept failed" << endl;
            return -1;
        }

        cout << "Server: ACCEPTED A NEW CONNECTION" << endl;

        // Our protocol is that if the client sends a 0, we stop serving that client
        while (1) {
            // The I/O with client starts here. However, if we do it here,
            // then the server will be blocked until this client is
            // done. We cannot get concurrency doing I/O with client
            // here. The way out is to delegate the I/O to a thread or process
            // (depending on the strategy we use) 

            long temp;
            
            // receive some information from the client
            int recv_status = recv (conn_sock,  // I/O done with new sock
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
                cerr << "Server: recv failed" << endl;
                return -1; // note we should really cleanup but we ignore it
            }

            // convert the number to host format (network uses bi-canonical
            // form). This is called unmarshalling
            number = ntohl (temp);

            if (number == 0) {
                cout << "Server received 0 from client" << endl;
                break;
            } else
                cout << "Server is computing factorial of " << number << endl;

            // compute the factorial
            result = factorial (number);

            cout << "Server: Sending result = " << result << endl;

            // marshal the result
            temp = htonl (result);
            
            int send_status = 
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
                cerr << "Server: send failed" << endl;
                return -1; // note we should really cleanup but we ignore it
            }
        }

        // STEP 6: close the new handle because we are done with the client
        (void) close (conn_sock);

    } // end of for loop


    // cleanup the listening endpoint because we ended up here
    (void) close (listen_sock);

    return 0;
}

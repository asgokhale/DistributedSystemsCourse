
#include <time.h>
#include <iostream>
using namespace std;

int main (int argc, char *argv[])
{
    cout << "This code will print the current time" << endl;

    timespec ts;

    cout << "sizeof timespec = " << sizeof (timespec) << endl;
    cout << "sizeof time_t = " << sizeof (time_t) << endl;
    cout << "sizeof long = " << sizeof (long) << endl;
    
    if (clock_gettime (CLOCK_REALTIME, &ts) == -1) {
        cerr << "clock_gettime failed" << endl;
        return 0;
    }

    cout << "Current time: sec = " << ts.tv_sec << ", nanosec = " << ts.tv_nsec
         << endl;
    double time_now = ts.tv_sec + ts.tv_nsec/1e9;
    cout << "time in double = " << time_now << endl;

    return 0;
    
}

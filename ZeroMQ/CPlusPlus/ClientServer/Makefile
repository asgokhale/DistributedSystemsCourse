# Sample code for CS6381
# Vanderbilt University
# Instructor: Aniruddha Gokhale
#
# Makefile to compile the zmq-based code
#

CXX	= g++
CXXFLAGS	+= -c -I /usr/local/include
LDFLAGS	+=  -L /usr/local/lib
LIBS				+= -lczmq -lzmq

BINS		= server	\
					client

SRCS		=	$(addsuffix .cpp, $(BINS))
HDRS	=
OBJS	=	$(addsuffix .o, $(BINS))

all:	$(BINS)

$(BINS):	%: %.o
	$(CXX) $(LDFLAGS)	$^ -o $@ $(LIBS)

$(OBJS):  %.o: %.cpp $(HDRS)
	$(CXX) $(CXXFLAGS)	$< -o $@

clean:
	rm -fr $(BINS) $(OBJS)




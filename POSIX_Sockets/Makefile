#----------------------------------------------------------------------------
#       $Id$
#
#----------------------------------------------------------------------------

#----------------------------------------------------------------------------
#       Local macros
#----------------------------------------------------------------------------

BIN1		= iterative_server
BIN2		= concurrent_server
BIN3		= client

FILES1	= iterative_server 
FILES2	= concurrent_server
FILES3	= client

SRC1    	= $(addsuffix .cpp,$(FILES1))
OBJS1			= $(addsuffix .o,$(FILES1))

SRC2    	= $(addsuffix .cpp,$(FILES2))
OBJS2			= $(addsuffix .o,$(FILES2))

SRC3    	= $(addsuffix .cpp,$(FILES3))
OBJS3			= $(addsuffix .o,$(FILES3))

CXXFLAGS	= -g
LDFLAGS		= -lpthread

#----------------------------------------------------------------------------
#       Local targets
#----------------------------------------------------------------------------

all:	$(BIN1) $(BIN2) $(BIN3)

$(BIN1) : $(OBJS1)
		$(CXX) -o $@ $^ $(LDFLAGS)

$(BIN2) : $(OBJS2)
		$(CXX) -o $@ $^ $(LDFLAGS)

$(BIN3) : $(OBJS3)
		$(CXX) -o $@ $^ $(LDFLAGS)

#%.o: %.cpp
#		$(CXX) -c $(CXXFLAGS) $^ -o $@

$(OBJS1):	$(SRC1)
		$(CXX) -c $(CXXFLAGS) $^ -o $@

$(OBJS2):	$(SRC2)
		$(CXX) -c $(CXXFLAGS) $^ -o $@

$(OBJS3):	$(SRC3)
		$(CXX) -c $(CXXFLAGS) $^ -o $@

clean:
	rm -fr *.o *.exe $(BIN1) $(BIN2) $(BIN3)

#----------------------------------------------------------------------------
#       Dependencies
#----------------------------------------------------------------------------



# ---------------------------------------------------------------------------
#
#	Makefile for HydroPlayground 
#
#	Devon Powell 
#	December 2016
#
#	usage: make
#
# ---------------------------------------------------------------------------


# Source files
SOURCES = blackjack.c 
COMMON = 
LIBOUT = blackjack.so 

# compiler options
CC = gcc
CFLAGS = -shared -fPIC -O3 -Wall
INC = -I.
OBJ = $(SOURCES:.c=.o)
LDFLAGS += -lm


# Makefile rules!
all: $(LIBOUT)

$(LIBOUT): $(COMMON) $(OBJ)
	$(CC) $(OBJ) -o $@ $(LDFLAGS) $(CFLAGS)

.c.o: $(COMMON)
	$(CC) -c -o $@ $(INC) $(CFLAGS) $<

clean:
	rm -rf *.o $(LIBOUT) *~ core

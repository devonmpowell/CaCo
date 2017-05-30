# ---------------------------------------------------------------------------
#
#	Makefile for CoCa 
#
#	Devon Powell
#
#	usage: make
#
# ---------------------------------------------------------------------------


# Source files
SOURCES = cocalib.c 
COMMON = 
LIBOUT = cocalib.so 

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

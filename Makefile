DEBUG   = -O3
CC      = gcc
INCLUDE = -I/usr/local/include
CFLAGS  = $(DEBUG) -Wall $(INCLUDE) -Winline -pipe

LDFLAGS = -L/usr/local/lib
LDLIBS    = -lwiringPi -lwiringPiDev -lpthread -lm -lsqlite3

rht:  rht.o
	@echo [link]
	@$(CC) -o $@ rht.o $(LDFLAGS) $(LDLIBS)


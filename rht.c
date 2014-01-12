/* Created by Jason Seymour
 * Patterned on code from wiringPi
*/

#include <stdio.h>
#include <stdlib.h>
#include <wiringPi.h>
#include <sqlite3.h>
#include <time.h>

#define RHT03_PIN       7

#ifndef TRUE
#  define       TRUE    (1==1)
#  define       FALSE   (1==2)
#endif

/* A callback function for the db */
static int callback(void *NotUsed, int argc, char **argv, char **azColName){
  return 0;
}

/*
 * maxDetectLowHighWait:
 *      Wait for a transition from high to low on the bus
 *********************************************************************************
 */

static void maxDetectLowHighWait (const int pin)
{
  unsigned int timeOut = millis () + 2000 ;

  while (digitalRead (pin) == HIGH)
    if (millis () > timeOut)
      return ;

  while (digitalRead (pin) == LOW)
    if (millis () > timeOut)
      return ;
}

/*
 * maxDetectClockByte:
 *      Read in a single byte from the MaxDetect bus
 *********************************************************************************
 */

static unsigned int maxDetectClockByte (const int pin)
{
  unsigned int byte = 0 ;
  int bit ;

  for (bit = 0 ; bit < 8 ; ++bit)
  {
    maxDetectLowHighWait (pin) ;

// bit starting now - we need to time it.

    delayMicroseconds (30) ;
    byte <<= 1 ;
    if (digitalRead (pin) == HIGH)      // It's a 1
      byte |= 1 ;
  }

  return byte ;
}


/*
 * maxDetectRead:
 *      Read in and return the 4 data bytes from the MaxDetect sensor.
 *      Return TRUE/FALSE depending on the checksum validity
 *********************************************************************************
 */

int maxDetectRead (const int pin, unsigned char buffer [4])
{
  int i ;
  unsigned int checksum ;
  unsigned char localBuf [5] ;

// Wake up the RHT03 by pulling the data line low, then high
//      Low for 10mS, high for 40uS.

  pinMode      (pin, OUTPUT) ;
  digitalWrite (pin, 0) ; delay             (10) ;
  digitalWrite (pin, 1) ; delayMicroseconds (40) ;
  pinMode      (pin, INPUT) ;

// Now wait for sensor to pull pin low

  maxDetectLowHighWait (pin) ;

// and read in 5 bytes (40 bits)

  for (i = 0 ; i < 5 ; ++i)
    localBuf [i] = maxDetectClockByte (pin) ;

  checksum = 0 ;
  for (i = 0 ; i < 4 ; ++i)
  {
    buffer [i] = localBuf [i] ;
    checksum += localBuf [i] ;
  }
  checksum &= 0xFF ;

  return checksum == localBuf [4] ;
}

/*
 * readRHT03:
 *      Read the Temperature & Humidity from an RHT03 sensor
 *********************************************************************************
 */

int readRHT03 (const int pin, int *temp, int *rh)
{
  static unsigned int nextTime   = 0 ;
  static          int lastTemp   = 0 ;
  static          int lastRh     = 0 ;
  static          int lastResult = TRUE ;

  unsigned char buffer [4] ;

// Don't read more than once a second

  if (millis () < nextTime)
  {
    *temp = lastTemp ;
    *rh   = lastRh ;
    return lastResult ;
  }

  lastResult = maxDetectRead (pin, buffer) ;

  if (lastResult)
  {
//    *temp      = lastTemp   = (buffer [2] * 256 + buffer [3]) ;
    lastTemp = buffer [2] & 0x7F;
    lastTemp *= 256;
    lastTemp += buffer [3];
//     lastTemp /= 10;
    if (buffer [2] & 0x80)
    {
	lastTemp *= -1;
    }
    *temp = lastTemp;
    *rh        = lastRh     = (buffer [0] * 256 + buffer [1]) ;
    nextTime   = millis () + 2000 ;
    return TRUE ;
  }
  else
  {
    return FALSE ;
  }
}


/*
 ***********************************************************************
 * The main program
 ***********************************************************************
 */

int main (void)
{
  int temp, rh ;
  int newTemp, newRh ;
  float tempF = 0.0;
  char TimeString[64];
  time_t rawtime;
  struct tm * timeinfo;
  sqlite3 *db;
  char *zErrMsg = 0;
  int rc;
  char SQLstring[2048];

  temp = rh = newTemp = newRh = 0 ;

  wiringPiSetup () ;
  piHiPri       (55) ;

  /* Open database */
  rc = sqlite3_open("/var/rht/db/rht.db", &db);
  if ( rc )
  {
        fprintf(stderr, "Can't open database: %s\n", sqlite3_errmsg(db));
        exit(0);
  }


  for (;;)
  {
    delay (5000) ;

    if (!readRHT03 (RHT03_PIN, &newTemp, &newRh))
      continue ;

    if ((temp != newTemp) || (rh != newRh))
    {
      temp = newTemp ;
      tempF = temp / 10.0;
      tempF *= 9;
      tempF /= 5;
      tempF += 32;
      rh   = newRh ;
//      printf ("Temp (F): %5.1f, RH: %5.1f%%\n", tempF , rh / 10.0) ;

      time(&rawtime);
      timeinfo = localtime(&rawtime);
      strftime (TimeString,64,"%F %T",timeinfo);

      /* Insert record into the database */
      sprintf(SQLstring,"INSERT INTO rht VALUES (%u,%5.1f,%5.1f)",(unsigned)time(NULL),tempF,(rh / 10.0));
      rc = sqlite3_exec(db, SQLstring, callback, 0, &zErrMsg);
      if( rc != SQLITE_OK )
      {
        fprintf(stderr, "SQL error: %s\n", zErrMsg);
        sqlite3_free(zErrMsg);
      }

    }
  }

  sqlite3_close(db);
  return 0 ;
}




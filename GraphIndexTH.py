#
# pull data from sql, plot using matplotlib
# see http://stackoverflow.com/questions/18663746/matplotlib-multiple-lines-with-common-date-on-x-axis-solved
#
# rev 1.0 12/02/2013 WPNS built from GraphAirmuxSD.py V1.1
# rev 1.1 12/02/2013 WPNS remove large delta values
# rev 1.2 12/02/2013 WPNS remove -0.1 values (failed to read)
# rev 1.3 12/02/2013 WPNS show count of anomalies
# rev 1.4 12/03/2013 WPNS cleanup, release
# rev 1.5 12/03/2013 WPNS better label
# rev 1.6 12/03/2013 WPNS bugfix, release
# rev 1.69 12/04/2013 WPNS release to Instructables
# rev 2.0-JAS 1/11/2014 JAS adjusted graph ranges for current conditions and to use SQLite3 instead of MySQL

import sys
import os
import time
import math
import datetime
import numpy
import sqlite3 as lite

# so matplotlib has to have some of the setup parameters _before_ pyplot
import matplotlib
matplotlib.use('agg')

#matplotlib.rcParams['figure.dpi'] = 100
#matplotlib.rcParams['figure.figsize'] = [10.24, 7.68]
matplotlib.rcParams['lines.linewidth'] = 1
matplotlib.rcParams['axes.color_cycle'] = ['r','g','b','k']
matplotlib.rcParams['axes.labelsize'] = 'large'
matplotlib.rcParams['font.size'] = 8
matplotlib.rcParams['grid.linestyle']='-'

import matplotlib.pyplot as plt

anomalies = 0

print "GraphTH.py V1.69 12/04/2013 WPNS",time.asctime(),
print "GraphTH.py V1.0-JAS 12/22/2013 JAS"

# open the database connection, read the last <many> seconds of data, put them in a Numpy array called Raw
DBconn = lite.connect('/var/rht/db/rht.db')
cursor = DBconn.cursor()
sql = "select ComputerTime,TempF,Humidity from rht where ComputerTime >= (strftime('%s','now')-(60*60*24))"
cursor.execute(sql)

cursor2 = DBconn.cursor()
sql2 = "SELECT datetime(ComputerTime,'unixepoch','localtime'),TempF,Humidity FROM rht WHERE ComputerTime = (select max(ComputerTime) from rht)"
cursor2.execute(sql2)
lastRow = cursor2.fetchone()


Raw = numpy.fromiter(cursor.fetchall(), count=-1, dtype=[('', numpy.float)]*3)
Raw = Raw.view(numpy.float).reshape(-1, 3)
(samples,ports)=Raw.shape
print 'Samples: {}, DataPoints: {}'.format(samples,ports),
plotme=numpy.zeros((samples,ports-1)) # make an array the same shape minus the epoch numbers

for y in range(ports-1):
#    print y
    for x in range(samples-1):  # can't do last one, there's no (time) delta from previous sample
        seconds = Raw[x+1,0]-Raw[x,0]
        # if the number didn't overflow the counter
        plotme[x,y] = Raw[x,y+1]

    plotme[samples-1,y] = None # set last sample to "do not plot"

    for x in range(samples-1):                   # go thru the dataset again
        if (Raw[x+1,1] == -0.1):                 # if values are "reading failed" flag
            plotme[x+1,0] = plotme[x,0]          # copy current sample over it
            plotme[x+1,1] = plotme[x,1]          # for temperature and humidity both
            anomalies += 1

        if (abs(Raw[x+1,1]-Raw[x,1]) > 10):      # if temperature jumps more than 10 degrees in a minute
            plotme[x+1,0] = plotme[x,0]          # copy current sample over it
            plotme[x+1,1] = plotme[x,1]          # for temperature and humidity both
            anomalies += 1

print "Anomalies: ",anomalies,

#print plotme

# get an array of adatetime objects (askewchan from stackoverflow, above)
dts = map(datetime.datetime.fromtimestamp, Raw[:,0])

# set up the plot details we want
plt.grid(True)
plt.ylabel('Temp F, RH %%')
plt.axis(ymax=100,ymin=10)
plt.xlabel(time.asctime())
plt.title("Outdoor: Temperature (Red), Humidity (Green)")
plt.hold(True)

# and some fiddly bits around formatting the X (date) axis
plt.gca().xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%m/%d %H:%M'))
plt.gca().xaxis.set_major_locator(matplotlib.dates.HourLocator())
lines = plt.plot(dts,plotme)
plt.gcf().autofmt_xdate()

FileName = '/var/rht/images/TH.png'
plt.savefig(FileName)

web = open('/var/www/index.html', 'w')
web.write('<HTML>\n')
web.write('<HEAD>\n')
web.write('<meta http-equiv=\"refresh\" content=\"60\">\n')
web.write('<TITLE>Raspberry Pi Temperature and Humidity Readings</TITLE>\n')
web.write('</HEAD>\n')
web.write('\n')
web.write('<BODY BGCOLOR="#FFFFFF">\n')
web.write('<CENTER>\n')
web.write('<IMG SRC="/images/TH.png">\n')
web.write('<BR><BR>\n')
web.write('<FONT COLOR=\"#FF0000\" SIZE=+2>Temp: ' + str(lastRow[1]) + 'F </FONT> &nbsp; &nbsp; &nbsp; <FONT COLOR=\"#00FF00\" SIZE=+2>Humidity: ' + str(lastRow[2]) + '% </FONT><BR>\n')
web.write('<FONT SIZE=+2>Time: ' + str(lastRow[0]) + '</FONT><BR>\n')
web.write('</CENTER>\n')
web.write('</BODY>\n')
web.write('\n')
web.write('</HTML\n')


print 'Done at',time.asctime()


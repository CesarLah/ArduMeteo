#!/usr/bin/env python3

# Fist of all a socket is created in the port indicated and waits for the 
# host call (Arduino in this case). When the strings (data) from the host are 
# received, the connection is closed. The strings are splitted and stored in a
# database built with sqlite3 module and finally the graphs with the data are 
# drawn in the selected folder.

# For a correct script running is necessary to create first a folder named
# "Estaci999001" in the same directory the script is in. Inside "Estaci999001"
# is neccesary to create next folders: "DB" (for databases), "Text" and "Plots

# -*- coding: utf-8 -*-
import random
import string
import datetime
import socket
import sqlite3
import matplotlib.pyplot as pp
import matplotlib.patches as mpatches
import numpy as np

#FUNCTIONS --------------------------------------------
def randomKey():
    """Generate a random string"""
    i = 0;
    f = []
    while i <= 5:
        g = random.choice(string.ascii_lowercase)
        f.append(g)
        i = i + 1
    key = ''.join(f)
    return key


def setTime():
    now = datetime.datetime.now()
    print (now)
    init_hour = now.hour
    init_minute = now.minute
    init_second = now.second
    init_day = now.day
    init_month = now.month
    init_year = now.year
    return init_hour, init_minute, init_second, init_day, init_month, init_year

def stringSplit(j):
    """Separate the strings' data"""
    global LH01_STD_str, error, pos1
    data1 = data[j].split(";")
    # header=data1[0]   # i999001
    hour_str.append(data1[1])
    minutes_str.append(data1[2])
    seconds_str.append(data1[3])
    day_str.append(data1[4])
    month_str.append(data1[5])
    year_str.append(data1[6])
    TA01_AVG_str.append(data1[7])
    TA01_MAX_str.append(data1[8])
    TA01_MIN_str.append(data1[9])
    TA01_STD_str.append(data1[10])
    WV01_AVG_str.append(data1[11])
    WV01_MAX_str.append(data1[12])
    WV01_MIN_str.append(data1[13])
    WV01_STD_str.append(data1[14])
    WD01_DIR_str.append(data1[15])
    WD01_MOD_str.append(data1[16])
    WD01_UAVG_str.append(data1[17])
    WD01_UMAX_str.append(data1[18])
    WD01_UMIN_str.append(data1[19])
    WD01_USTD_str.append(data1[20])
    WD01_VAVG_str.append(data1[21])
    WD01_VMAX_str.append(data1[22])
    WD01_VMIN_str.append(data1[23])
    WD01_VSTD_str.append(data1[24])
    RA01_AVG_str.append(data1[25])
    RA01_MAX_str.append(data1[26])
    RA01_MIN_str.append(data1[27])
    RA01_STD_str.append(data1[28])
    RA01_TTL_str.append(data1[29])
    LH01_AVG_str.append(data1[30])
    LH01_MAX_str.append(data1[31])
    LH01_MIN_str.append(data1[32])
    LH01_STD_str_bug.append(data1[33])
    date_string.append([day_str[j], month_str[j], year_str[j]])
    adjust = LH01_STD_str_bug[j].split('.')
    # to check if the string's end has been received correctly
    if adjust[1].isdigit(): 	
        LH01_STD_str.append( LH01_STD_str_bug[j] )
    elif (adjust[1].find('i') != -1) and (adjust[1].find('q') == -1):  # if i999001 is included in last position (and not quit)
            pos1 = adjust[1].find('i')
            LH01_STD_str_bug[j] = adjust[0] + '.' + adjust[1][0: pos1]
            error = True
            LH01_STD_str.append(LH01_STD_str_bug[j])
    z = 35    # 34, number of different data received
    if len(data1) >= z:		# To check if data string length is longer and insert this values in next string 
        s = (len(data1)+1) - z
        lost_values.append(data1[(z - 1): len(data1)])    
        for p in range (0, s):
            new_string.append(lost_values[0][p])
            if new_string [len(new_string)-1] == "":
                new_string [0: len(new_string)-2] = new_string
        for z in range (s - 1, -1, -1):
             data[j+1] = new_string[z] + ";" + data[j+1]
        if error:
             data[j+1] = adjust[1] [pos1: len(adjust[1])] + ";" + data[j+1]
        pos3 = data[j+1].find(";;")
        data[j+1] = data[j+1][0:pos3] + data[j+1][(pos3+1): (len(data[j+1]))]
    else:
        if adjust[1].find('q') != -1:           # To check if "quit" is included in string's last position
            pos2 = adjust[1].find('q')
            LH01_STD_str_bug[j] = adjust[0] + '.' + adjust[1][0: pos2]
            LH01_STD_str.append(LH01_STD_str_bug[j])
        elif not adjust[1].isdigit():
            LH01_STD_str_bug[j] = adjust[0] + '.' + adjust[1][0: 2]
            LH01_STD_str.append(LH01_STD_str_bug[j])

def createTxt():

    txt = open ('Estaci999001/Text/%s' % file_name, 'w')  
    txt.close()


def saveTxt():      
    """Save strings' data received in a text file"""
    txt = open ('Estaci999001/Text/%s' % file_name, 'a')
    i = 0
    while i <= (measures - 1):
        txt.write (data[i])
        txt.write ('\n')
        i = i + 1
    txt.close()
    print ("Saved data in file  %s included in Text folder" % file_name)


def createDatabase():
    connection = sqlite3.connect("Estaci999001/DB/%s.sqlite3" % db)     # folder and database name
    query = connection.cursor()             #Cursor selection to make the query  

    sql = ("""
    CREATE TABLE IF NOT EXISTS %s(			    
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    T_AVG FLOAT NOT NULL,
    T_MAX FLOAT NOT NULL,
    T_MIN FLOAT NOT NULL,
    T_STD FLOAT NOT NULL,
    WV_AVG FLOAT NOT NULL,
    WV_MAX FLOAT NOT NULL,
    WV_MIN FLOAT NOT NULL,
    WV_STD FLOAT NOT NULL,
    WD_DIR FLOAT NOT NULL,
    WD_MOD FLOAT NOT NULL,
    WDU_AVG FLOAT NOT NULL,
    WDU_MAX FLOAT NOT NULL,
    WDU_MIN FLOAT NOT NULL,
    WDU_STD FLOAT NOT NULL,
    WDV_AVG FLOAT NOT NULL,
    WDV_MAX FLOAT NOT NULL,
    WDV_MIN FLOAT NOT NULL,
    WDV_STD FLOAT NOT NULL,
    L_AVG FLOAT NOT NULL,
    L_MAX FLOAT NOT NULL,
    L_MIN FLOAT NOT NULL,
    L_STD FLOAT NOT NULL,
    R_AVG FLOAT NOT NULL,
    R_MAX FLOAT NOT NULL,
    R_MIN FLOAT NOT NULL,
    R_STD FLOAT NOT NULL,
    R_TTL INTEGER NOT NULL,
    hour INTEGER NOT NULL,
    minute INTEGER NOT NULL,
    seconds INTEGER NOT NULL,
    date DATE NOT NULL)""" % db)	# 32 columns

    if query.execute(sql): print ("Database created  succesfully")
    else: print ("Error creating the table") 

    query.close()

    connection.commit()     # To save changes in the database

    connection.close()


def insertData(i):
    """Insert data in the database"""
    connection = sqlite3.connect("Estaci999001/DB/%s.sqlite3" % db )

    query = connection.cursor()

    T_AVG = float(TA01_AVG_str[i])
    T_MAX = float(TA01_MAX_str[i])
    T_MIN = float(TA01_MIN_str[i])
    T_STD = float(TA01_STD_str[i])
    WV_AVG = float(WV01_AVG_str[i])
    WV_MAX = float(WV01_MAX_str[i])
    WV_MIN = float(WV01_MIN_str[i])
    WV_STD = float(WV01_STD_str[i])
    WD_DIR = float(WD01_DIR_str[i])
    WD_MOD = float(WD01_MOD_str[i])
    WDU_AVG = float(WD01_UAVG_str[i])
    WDU_MAX = float(WD01_UMAX_str[i])
    WDU_MIN = float(WD01_UMIN_str[i])
    WDU_STD = float(WD01_USTD_str[i])
    WDV_AVG = float(WD01_VAVG_str[i])
    WDV_MAX = float(WD01_VMAX_str[i])
    WDV_MIN = float(WD01_VMIN_str[i])
    WDV_STD = float(WD01_VSTD_str[i])
    L_AVG = float(LH01_AVG_str[i])
    L_MAX = float(LH01_MAX_str[i])
    L_MIN = float(LH01_MIN_str[i])
    L_STD = float(LH01_STD_str[i])
    R_AVG = float(RA01_AVG_str[i])
    R_MAX = float(RA01_MAX_str[i])
    R_MIN = float(RA01_MIN_str[i])
    R_STD = float(RA01_STD_str[i])
    R_TTL = float(RA01_STD_str[i])
    hour1 = int(hour_str[i])
    minute1 = int(minutes_str[i])
    seconds1 = int(seconds_str[i])
    arguments = (T_AVG, T_MAX, T_MIN, T_STD, WV_AVG, WV_MAX, WV_MIN, WV_STD,
    WD_DIR, WD_MOD, WDU_AVG, WDU_MAX, WDU_MIN, WDU_STD, WDV_AVG, WDV_MAX,
    WDV_MIN, WDV_STD, L_AVG,L_MAX,L_MIN,L_STD, R_AVG,R_MAX, R_MIN,R_STD, R_TTL,
    hour1, minute1, seconds1, datetime.date.today())

    sql = ("""INSERT INTO %s(T_AVG, T_MAX, T_MIN, T_STD, WV_AVG, WV_MAX,
    WV_MIN, WV_STD, WD_DIR, WD_MOD, WDU_AVG, WDU_MAX, WDU_MIN, WDU_STD,
    WDV_AVG, WDV_MAX, WDV_MIN, WDV_STD, L_AVG, L_MAX, L_MIN, L_STD, R_AVG,
    R_MAX, R_MIN, R_STD, R_TTL, hour, minute, seconds, date) VALUES (?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ? , ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
    ? ,? ,? ,?)""" % db)				  # 31 arguments, no id

    query.execute(sql, arguments)

    query.close()

    connection.commit()

    connection.close()


def extractData(pos):
    connection=sqlite3.connect("Estaci999001/DB/%s.sqlite3" % db )    

    query = connection.cursor()

    selection = query.execute('SELECT * from %s' % db )
    all_data = selection.fetchall()

    for i in range(pos,p):
        num.append(all_data[i][0])
        tavg.append(all_data[i][1])
        tmax.append(all_data[i][2])
        tmin.append(all_data[i][3])
        tstd.append(all_data[i][4])
        vavg.append(all_data[i][5])
        vmax.append(all_data[i][6])
        vmin.append(all_data[i][7])
        vstd.append(all_data[i][8])
        vdir.append(all_data[i][9])
        vmod.append(all_data[i][10])
        w_uavg.append(all_data[i][11])
        w_umax.append(all_data[i][12])
        w_umin.append(all_data[i][13])
        w_ustd.append(all_data[i][14])
        w_vavg.append(all_data[i][15])
        w_vmax.append(all_data[i][16])
        w_vmin.append(all_data[i][17])
        w_vstd.append(all_data[i][18])
        lavg.append(all_data[i][19])
        lmax.append(all_data[i][20])
        lmin.append(all_data[i][21])
        lstd.append(all_data[i][22])
        ravg.append(all_data[i][23])
        rmax.append(all_data[i][24])
        rmin.append(all_data[i][25])
        rstd.append(all_data[i][26])
        rttl.append(all_data[i][27])
        hour.append(all_data[i][28])
        hour_plot.append(repr(all_data[i][28]))     # To obtain hour & minutes for graphs in str type
        minute_plot.append(repr(all_data[i][29]))
        minute.append(all_data[i][29])
        second.append(all_data[i][30])
        date.append(all_data[i][31])


def combHour():
    """Combine hour & minutes for each measure for plotting""" 
    v = len(hour_plot)
    z = 0
    while (z <= (v - 1)):
        if len(minute_plot[z]) == 1:
            hour_comb.append(hour_plot[z] + ":" + "0" + minute_plot[z])
            z = z + 1
        else:
            hour_comb.append(hour_plot[z] + ":" + minute_plot[z])
            z = z + 1


def reduction():
    """Number of ticks in x label for daily plot"""
    j = int(len(num) / 12)
    for i in range (0, len(num), j):
        daily_hour.append(hour_comb[i])
    return j


def plotDir():
    """Wind Direction plot"""
    left  = 0.1    # the left side of the subplots of the figure   
    right = 0.9    # the right side of the subplots of the figure
    bottom = 0.15  # the bottom of the subplots of the figure
    top = 0.75     # the top of the subplots of the figure
    wspace = 0.2   # the amount of width reserved for blank space between subplots
    hspace = 0.85  # the amount of height reserved for white space between subplots
    pp.close('all')

    nombresect = ['N','NW','W','SW','S','SE','E','NE']

    fig=pp.figure()
    fig.suptitle('i99001. From %s to %s. %s\nWIND DIRECTION' % (hour_comb[0],
    hour_comb[len(hour_comb)-1], date[len(date)-1]) , fontsize=12,
    fontweight='bold')
    fig.subplots_adjust(left, bottom, right, top, wspace, hspace)
    sp1 = fig.add_subplot(231, projection='polar')
    sp1.set_title("%s\n" % hour_comb[len(hour_comb) - 6])
    sp1.plot ([0, vdir[len(vdir) - 6]], [0,vmod[len(vmod) - 6]])
    sp1.set_theta_zero_location("N")
    pp.thetagrids(np.arange(0, 360, 45), nombresect, frac=1.3)
    sp2=fig.add_subplot(232,projection='polar')
    sp2.set_title("%s\n" % hour_comb[len(hour_comb) - 5])
    sp2.plot ([0, vdir[len(vdir) - 5]], [0, vmod[len(vmod) - 5]])
    sp2.set_theta_zero_location("N")
    pp.thetagrids(np.arange(0, 360, 45), nombresect, frac=1.3)
    sp3 = fig.add_subplot(233, projection='polar')
    sp3.set_title("%s\n" % hour_comb[len(hour_comb) - 4])
    sp3.plot ([0, vdir[len(vdir) - 4]], [0,vmod[len(vmod) - 4]])
    sp3.set_theta_zero_location("N")
    pp.thetagrids(np.arange(0, 360, 45), nombresect, frac=1.3)
    sp4=fig.add_subplot(234, projection = 'polar')
    sp4.set_title("%s\n" % hour_comb[len(hour_comb) - 3])
    sp4.plot ([0, vdir[len(vdir) - 3]], [0,vmod[len(vmod) - 3]])
    sp4.set_theta_zero_location("N")
    pp.thetagrids(np.arange(0, 360, 45), nombresect, frac=1.3)
    sp5=fig.add_subplot(235, projection='polar')
    sp5.set_title("%s\n" % hour_comb[len(hour_comb) - 2])
    sp5.plot ([0, vdir[len(vdir) - 2]], [0, vmod[len(vmod) - 2]])
    sp5.set_theta_zero_location("N")
    pp.thetagrids(np.arange(0, 360, 45), nombresect, frac=1.3)
    sp6=fig.add_subplot(236, projection='polar')
    sp6.set_title("%s\n" % hour_comb[len(hour_comb) - 1])  
    sp6.plot ([0,vdir[len(vdir)-1]],[0,vmod[len(vmod)-1]])
    sp6.set_theta_zero_location("N")
    pp.thetagrids(np.arange(0, 360, 45), nombresect, frac=1.3)

    imag = pp.gcf()
    imag.savefig('Estaci999001/Plots/i999001_%sh %smin_wDIRECTION@%s-%s-%s-%s.png'
    % (hour_str[len(hour_str) - 1], minutes_str[len(hour_str) - 1],
    day_str[len(hour_str) - 1], month_str[len(hour_str) - 1],
    year_str[len(hour_str) - 1], key), dpi=400)


def mainPlot():
    """Temperature, wind speed, rain and luminosity graphs for every hour"""
    left  = 0.08    # the left side of the subplots of the figure
    right = 0.94    # the right side of the subplots of the figure
    bottom = 0.08   # the bottom of the subplots of the figure
    top = 0.90      # the top of the subplots of the figure
    wspace = 0.30   # the amount of width reserved for blank space between subplots
    hspace = 0.07   # the amount of height reserved for white space between subplots

    pp.close('all')
    fig1 = pp.figure()

    fig1.suptitle('i999001.From %s to %s. %s' % (hour_comb[0],
    hour_comb[len(hour_comb) - 1], date[len(date) - 1]), fontsize=9,
    fontweight='bold')
    fig1.subplots_adjust(left, bottom, right, top, wspace, hspace)
    line1 = mpatches.Patch(color='red', hatch='-', linewidth=0.05,
    label="maximun values")
    line2 = mpatches.Patch(color='green', hatch='-', linewidth=0.1,
    label="average")
    line3 = mpatches.Patch(color='blue', hatch='-', linewidth=0.1,
    label="minumun values")
    line4 = mpatches.Patch(color='magenta', hatch='-', linewidth=0.1,
    label = "standard deviation")
    pp.figlegend((line1,line2,line3,line4), ('Maximun','Average','Minimun',
    'Standard deviation'),  loc=1, borderaxespad=0., prop={'size': 6} )

    ax1 = fig1.add_subplot(221)
    ax1.set_ylabel('TEMPERATURE (Celsius)',fontsize=7)

    ax1.plot(np.arange(len(num)),tavg, 'g-+', label='Avg')
    ax1.plot(np.arange(len(num)),tmax, 'r--', label='Max')
    ax1.plot(np.arange(len(num)),tmin, 'b--', label='Min')
    ax1.grid()
    ax11 = ax1.twinx()
    ax11.set_ylabel("deviation (Celsius)", fontsize=6)
    ax11.plot(np.arange(len(num)), tstd, 'mx')    
    pp.setp(ax11.get_xticklabels(), visible=False)
    pp.rc('font', size=8)
    pp.xticks(np.arange(len(num)), hour_comb, size='small', rotation=45)

    ax2=fig1.add_subplot(222)
    ax2.set_ylabel("WIND SPEED (kmh)",fontsize=7)
    ax2.plot(np.arange(len(num)), vavg, 'g-+')
    ax2.plot(np.arange(len(num)), vmax, 'r--')
    ax2.plot(np.arange(len(num)), vmin, 'b--')
    ax2.grid()
    ax21 = ax2.twinx()
    ax21.set_ylabel("desviacion (kmh)", fontsize=6)
    ax21.plot(np.arange(len(num)), vstd, 'mx')
    pp.setp(ax21.get_xticklabels(), visible=False)
    pp.rc('font', size=8)
    pp.xticks(np.arange(len(num)), hour_comb, size='small', rotation=45)

    ax3=fig1.add_subplot(223)
    ax3.set_xlabel('Hour : minutes', fontsize=7)
    ax3.set_ylabel("RAIN (mm)",fontsize=7)
    ax3.plot(np.arange(len(num)), ravg, 'g-+')
    ax3.plot(np.arange(len(num)), rmax, 'r--')
    ax3.plot(np.arange(len(num)), rmin, 'b--')
    ax3.grid()
    ax31 = ax3.twinx()
    ax31.set_ylabel("deviation (mm)", fontsize=6)
    ax31.plot(np.arange(len(num)), rstd, 'mx')
    pp.setp(ax31.get_xticklabels(), visible=False)
    pp.rc('font', size=8)
    pp.xticks(np.arange(len(num)), hour_comb, size='small', rotation=45)

    ax4 = fig1.add_subplot(224)
    ax4.set_xlabel('Hour : minutes', fontsize=7)
    ax4.set_ylabel("IRRADIANCE LEVEL (0-1024)", fontsize=7)
    ax4.plot(np.arange(len(num)), lavg, 'g-+')
    ax4.plot(np.arange(len(num)), lmax, 'r--')
    ax4.plot(np.arange(len(num)), lmin, 'b--')
    ax4.grid()
    ax41=ax4.twinx()
    ax41.set_ylabel("deviation",  fontsize=6)
    ax41.plot(np.arange(len(num)), lstd, 'mx')
    pp.setp(ax41.get_xticklabels(), visible=False)
    pp.rc('font', size=5)
    pp.xticks(np.arange(len(num)), hour_comb, size='small', rotation=45)

    imag = pp.gcf()
    imag.savefig('Estaci999001/Plots/%s.png' % file_name, dpi=400)


def plotComp():
    """Wind 'u' and 'v' components"""
    left  = 0.2     # the left side of the subplots of the figure
    right = 0.8     # the right side of the subplots of the figure
    bottom = 0.12   # the bottom of the subplots of the figure
    top = 0.88      # the top of the subplots of the figure
    wspace = 0.75   # the amount of width reserved for blank space between subplots
    hspace = 0.12   # the amount of height reserved for white space between subplots

    pp.close('all')
    fig1 = pp.figure()

    fig1.suptitle('i999001.From %s to %s. %s' % (hour_comb[0],
    hour_comb[len(hour_comb) - 1], date[len(date) - 1]) , fontsize=9,
    fontweight='bold')
    fig1.subplots_adjust(left, bottom, right, top, wspace, hspace)
    line1=mpatches.Patch(color='red')
    line2=mpatches.Patch(color='green')
    line3=mpatches.Patch(color='blue')
    line4=mpatches.Patch(color='magenta')
    pp.figlegend((line1,line2,line3,line4), ('Maximun','Average','Minimun', 
    'Standard deviation'), loc=1, borderaxespad=0., prop={'size': 7} )

    ax1 = fig1.add_subplot(211)
    ax1.set_ylabel('U WIND COMPONENT (radians)', fontsize=7)

    ax1.plot(np.arange(len(num)), w_uavg, 'g-+')
    ax1.plot(np.arange(len(num)), w_umax, 'r--')
    ax1.plot(np.arange(len(num)), w_umin, 'b--')
    ax1.grid()
    ax11 = ax1.twinx()
    ax11.set_ylabel("deviation (radians)", fontsize=6)
    ax11.plot(np.arange(len(num)), w_ustd, 'mx')
    pp.setp(ax11.get_xticklabels(), visible=False)
    pp.rc('font', size=5)
    pp.xticks(np.arange(len(num)), hour_comb, size='small', rotation=45)

    ax2 = fig1.add_subplot(212)

    ax2.set_ylabel("V WIND COMPONENT (radians)", fontsize=7)
    ax2.set_xlabel('Hour : minutes', fontsize=7)
    ax2.grid()
    ax2.plot(np.arange(len(num)), w_vavg, 'g-+')
    ax2.plot(np.arange(len(num)), w_vmax, 'r--')
    ax2.plot(np.arange(len(num)), w_vmin, 'b--')
    ax21 = ax2.twinx()
    ax21.set_ylabel("deviation (radians)", fontsize=6)
    ax21.plot(np.arange(len(num)), w_vstd, 'mx')
    pp.setp(ax21.get_xticklabels(), visible=False)
    pp.rc('font', size=5)
    pp.xticks(np.arange(len(num)), hour_comb, size='small', rotation=45)

    imag = pp.gcf()
    imag.savefig('Estaci999001/Plots/i999001_%sh %smin_WIND_COMPONENTS@\
    %s-%s-%s-%s.png' % (hour_str[len(day_str)-1], minutes_str[len(month_str)-1],
    day_str[len(day_str)-1], month_str[len(month_str)-1], 
    year_str[len(year_str)-1], key), dpi = 400)


def dailyPlot():
    """Plots data acquired in a whole day"""
    f = reduction()
    dailyPlot1(f)
    dailyPlot2(f)           
    dailyComp(f)

def dailyPlot1(f):
    """Temperature and Wind Speed plots for an entire day"""
    left  = 0.1     # the left side of the subplots of the figure
    right = 0.9     # the right side of the subplots of the figure
    bottom = 0.08   # the bottom of the subplots of the figure
    top = 0.90      # the top of the subplots of the figure
    wspace = 0.75   # the amount of width reserved for blank space between subplots
    hspace = 0.25   # the amount of height reserved for white space between subplots

    pp.close('all')
    fig1 = pp.figure()

    fig1.suptitle('i99001. From %s to %s. %s' % (hour_comb[0],
    hour_comb[len(hour_comb) - 1], date[len(date) - 1]), fontsize=12,
    fontweight='bold') 
    fig1.subplots_adjust(left, bottom, right, top, wspace, hspace)
    line1 = mpatches.Patch(color='red')
    line2 = mpatches.Patch(color='green')
    line3 = mpatches.Patch(color='blue')
    line4 = mpatches.Patch(color='magenta')
    pp.figlegend((line1,line2,line3,line4), ('Maximun','Average','Minimun',
    'Standard Deviation'), loc=1, borderaxespad=0., prop={'size': 6} )

    ax1 = fig1.add_subplot(211)
    ax1.set_ylabel('TEMPERATURE (Celsius)', fontsize=7)
    pp.setp(ax1.get_xticklabels(minor=True), visible=True, size='x-small')
    ax1.plot(np.arange(len(num)), tavg, 'g-+')
    ax1.plot(np.arange(len(num)), tmax, 'r--')
    ax1.plot(np.arange(len(num)), tmin, 'b--')
    ax1.grid()
    ax1.set_xlabel('Hour : minutes', fontsize=6)
    ax11=ax1.twinx()
    ax11.set_ylabel("deviation (Celsius)", fontsize=6)
    ax11.plot(np.arange(len(num)), tstd, 'mx') 
    pp.setp(ax11.get_xticklabels(), visible=False)
    pp.xticks(np.arange(0, len(hour_comb), f),daily_hour, size='x-small',
    rotation=45)
    pp.axis('tight')

    ax2 = fig1.add_subplot(212)
    ax2.set_ylabel("WIND SPEED (km/h)", fontsize=7)
    ax2.set_xlabel('Hour : minutes', fontsize=6)
    ax2.grid()
    ax2.plot(np.arange(len(num)), vavg, 'g-+')
    ax2.plot(np.arange(len(num)), vmax, 'r--')
    ax2.plot(np.arange(len(num)), vmin, 'b--')
    ax21=ax2.twinx()
    ax21.set_ylabel("deviation", fontsize=6)
    ax21.plot(np.arange(len(num)), vstd, 'mx')
    pp.setp(ax21.get_xticklabels(), visible=False)
    pp.xticks(np.arange(0, len(hour_comb), f), daily_hour, size='x-small',
    rotation=45)
    pp.axis('tight')
    for tick in ax21.xaxis.get_major_ticks():
        tick.label.set_fontsize(4)

    imag=pp.gcf()
    imag.savefig('Estaci999001/Plots/i999001_%sh %s\' %s\'\'DAILY_TEMPERATURE\
    _&_WIND SPEED@%s_%s.png' % (hour[len(hour) - 1], minute[len(minute) - 1],
    second[len(second) - 1], date[len(date) - 1], key), dpi=400)


def dailyPlot2(f):
    """Luminosity and Rain plots for a whole day"""
    left  = 0.1     # the left side of the subplots of the figure
    right = 0.9     # the right side of the subplots of the figure
    bottom = 0.08   # the bottom of the subplots of the figure
    top = 0.90      # the top of the subplots of the figure
    wspace = 0.75   # the amount of width reserved for blank space between subplots
    hspace = 0.25   # the amount of height reserved for white space between subplots

    pp.close('all')
    fig1 = pp.figure()

    fig1.suptitle('i99001. From %s to %s. %s' % (hour_comb[0],
    hour_comb[len(hour_comb) - 1], date[len(date) - 1]) , fontsize=12,
    fontweight='bold') 
    fig1.subplots_adjust(left, bottom, right, top, wspace, hspace)
    line1 = mpatches.Patch(color='red')
    line2 = mpatches.Patch(color='green')
    line3 = mpatches.Patch(color='blue')
    line4 = mpatches.Patch(color='magenta')
    pp.figlegend((line1,line2,line3,line4), ('Maximun','Average','Minimun',
    'Standard Deviation'), loc=1, borderaxespad=0., prop={'size': 6} )

    ax1 = fig1.add_subplot(211)
    ax1.set_ylabel('LUMINOSITY (0-1024)', fontsize=7)
    pp.setp(ax1.get_xticklabels(minor=True), visible=True, size='x-small')
    ax1.plot(np.arange(len(num)), lavg, 'g-+')
    ax1.plot(np.arange(len(num)), lmax, 'r--')
    ax1.plot(np.arange(len(num)), lmin, 'b--')
    ax1.grid()
    ax1.set_xlabel('Measure hour', fontsize=6)
    ax11=ax1.twinx()
    ax11.set_ylabel("deviation", fontsize=6)
    ax11.plot(np.arange(len(num)), lstd, 'mx')    
    pp.setp(ax11.get_xticklabels(), visible=False)
    pp.xticks(np.arange(0, len(hour_comb), f),daily_hour, size='x-small',
    rotation=45)
    pp.axis('tight')

    ax2=fig1.add_subplot(212)
    ax2.set_ylabel("RAIN (mm)", fontsize=7)
    ax2.set_xlabel('Measure hour', fontsize=6)
    ax2.grid()
    ax2.plot(np.arange(len(num)), ravg, 'g-+')
    ax2.plot(np.arange(len(num)), rmax, 'r--')
    ax2.plot(np.arange(len(num)), rmin, 'b--')
    ax21 = ax2.twinx()
    ax21.set_ylabel("deviation (mm)", fontsize=6)
    ax21.plot(np.arange(len(num)), rstd, 'mx')
    pp.setp(ax21.get_xticklabels(), visible=False)
    pp.xticks(np.arange(0, len(hour_comb), f), daily_hour, size='x-small',
    rotation=45)
    pp.axis('tight')
    for tick in ax21.xaxis.get_major_ticks():
        tick.label.set_fontsize(4)

    imag=pp.gcf()
    imag.savefig('Estaci999001/Plots/i999001_%sh %s\' %s\'\'DAILY_RAIN &\
    LUMINOSITY@%s_%s.png' % (hour[len(hour) - 1], minute[len(minute) - 1],
    second[len(second) -1 ], date[len(date) - 1], key), dpi=400)


def dailyComp(f):
    """Daily wind 'u' and 'v' components"""
    left  = 0.1     # the left side of the subplots of the figure
    right = 0.9     # the right side of the subplots of the figure
    bottom = 0.12   # the bottom of the subplots of the figure
    top = 0.88      # the top of the subplots of the figure
    wspace = 0.75   # the amount of width reserved for blank space between subplots
    hspace = 0.12   # the amount of height reserved for white space between subplots

    pp.close('all')
    fig1 = pp.figure()

    fig1.suptitle('i999001.From %s to %s. %s' % (hour_comb[0],
    hour_comb[len(hour_comb) - 1], date[len(date) - 1]) , fontsize=9,
    fontweight='bold')
    fig1.subplots_adjust(left, bottom, right, top, wspace, hspace)
    line1=mpatches.Patch(color='red')
    line2=mpatches.Patch(color='green')
    line3=mpatches.Patch(color='blue')
    line4=mpatches.Patch(color='magenta')
    pp.figlegend((line1,line2,line3,line4), ('Maximun','Average','Minimun', 
    'Standard deviation'), loc=1, borderaxespad=0., prop={'size': 7} )

    ax1 = fig1.add_subplot(211)
    ax1.set_ylabel('U WIND COMPONENT (radians)', fontsize=7)

    ax1.plot(np.arange(len(num)), w_uavg, 'g-+')
    ax1.plot(np.arange(len(num)), w_umax, 'r--')
    ax1.plot(np.arange(len(num)), w_umin, 'b--')
    ax1.grid()
    ax11 = ax1.twinx()
    ax11.set_ylabel("deviation (radians)", fontsize=6)
    ax11.plot(np.arange(len(num)), w_ustd, 'mx')
    pp.setp(ax11.get_xticklabels(), visible=False)
    pp.rc('font', size=5)
    pp.xticks(np.arange(0, len(hour_comb), f), daily_hour, size='small',
    rotation=45)
    pp.axis('tight')

    ax2 = fig1.add_subplot(212)

    ax2.set_ylabel("V WIND COMPONENT (radians)", fontsize=7)
    ax2.set_xlabel('Hour : minutes', fontsize=7)
    ax2.grid()
    ax2.plot(np.arange(len(num)), w_vavg, 'g-+')
    ax2.plot(np.arange(len(num)), w_vmax, 'r--')
    ax2.plot(np.arange(len(num)), w_vmin, 'b--')
    ax21 = ax2.twinx()
    ax21.set_ylabel("deviation (radians)", fontsize=6)
    ax21.plot(np.arange(len(num)), w_vstd, 'mx')
    pp.setp(ax21.get_xticklabels(), visible=False)
    pp.rc('font', size=5)
    pp.xticks(np.arange(0, len(hour_comb), f), daily_hour, size='small',
    rotation=45)
    pp.axis('tight')

    imag = pp.gcf()
    imag.savefig('Estaci999001/Plots/i999001_%sh %smin_DAILY_WIND_COMPONENTS@\
    %s-%s-%s-%s.png' % (hour_str[len(day_str)-1], minutes_str[len(month_str)-1],
    day_str[len(day_str)-1], month_str[len(month_str)-1], 
    year_str[len(year_str)-1], key), dpi = 400)


def initVar():
    global num, tavg, tmax, tmin, tstd, vavg, vmax, vmin, vstd, vdir, vmod 
    global w_uavg, w_umax, w_umin, w_ustd, w_vavg, w_vmax, w_vmin, w_vstd
    global ravg, rmax, rmin, rstd, rttl, lavg, lmax, lmin, lstd, hour, minute,\
    second, minute_plot, hour_comb , hour_plot
    num = []
    tavg = []
    tmax = []
    tmin = []
    tstd = []
    vmax = []
    vmin = []
    vavg = []
    vstd = []
    vdir = []
    vmod = []
    w_uavg = []
    w_umax = []
    w_umin = []
    w_ustd = []
    w_vavg = []
    w_vmax = []
    w_vmin = []
    w_vstd = []
    ravg = []      # rain
    rmin = []
    rmax = []
    rstd = []
    rttl = []
    lavg = []      # light
    lmax = []
    lmin = []
    lstd = []
    hour = []
    minute = []
    second = []
    date = []
    hour_plot = []
    minute_plot = []
    hour_comb = []


#--------------------SCRIPT-----------------------------------------------
error = False
pos1 = 0
measures = 6   # number of strings to receive in each connection
p = 0          # database id position
init_time = setTime()
db = ("DB_%ih%imin_day_%i_%i" % (init_time[0], init_time[1], init_time[3],
				 init_time[4]))

s=socket.socket()
s.bind(('',769))
s.listen(1)         # only accepts one connection at the same time
for j in range(0,50000):    # 50 000 hours
    print ("Waiting for a connection entrance")

    key = randomKey()    # identifies each measure received
    # initializes variables for the string splitting
    TA01_AVG_str = []
    TA01_MAX_str = []
    TA01_MIN_str = []
    TA01_STD_str = []
    WV01_AVG_str = []
    WV01_MAX_str = []
    WV01_MIN_str = []
    WV01_STD_str = []
    WD01_DIR_str = []
    WD01_MOD_str = []
    WD01_UAVG_str = []
    WD01_UMAX_str = []
    WD01_UMIN_str = []
    WD01_USTD_str = []
    WD01_VAVG_str = []
    WD01_VMAX_str = []
    WD01_VMIN_str = []
    WD01_VSTD_str = []
    LH01_AVG_str = []
    LH01_MAX_str = []
    LH01_MIN_str = []
    LH01_STD_str = []
    LH01_STD_str_bug = []
    RA01_AVG_str = []
    RA01_MAX_str = []
    RA01_MIN_str = []
    RA01_STD_str = []
    RA01_TTL_str = []
    day_str = []
    month_str = []
    year_str = []
    hour_str = []
    minutes_str = []
    seconds_str = []
    date = []
    date_string = []
    lost_values = []
    new_string = []

    # values obtained from database

    initVar()
    daily_hour = []

    # Server--------------------------------------------------------------------

    data = []
    sc, addr = s.accept()              # socket connection, address
    print("Connection made")

    i = 0
    while i <= measures:                        # 6 measures + 'quit'
        received = sc.recv(200)           # Maximun 200 bytes accepted

        if received == "quit":
            print ("QUIT")
            break
        else:
            data.append(received.decode('utf-8'))

        print ("Received: ", received)        
        print ("String number: %d" % i)
        print ("String size (bytes): %d" % len(received))
        i = i + 1
    sc.close()
    print ("Connection closed")

    # Data treatment----------------
    createDatabase()
    f = 0
    while f <= measures - 1:
        stringSplit(f)
        insertData(f)
        f = f + 1
        p = p + 1
    print ("%d Strings separated correctly and inserted the corresponding\
 values in the database %s (last position: %d)" % (f, db, p))
    file_name = 'i999001_%sh%smin@%s-%s-%s-%s.txt' % (hour_str[len(day_str)-1],
    minutes_str[len(month_str)-1], day_str[len(day_str)-1],
    month_str[len(month_str)-1], year_str[len(year_str)-1], key)
    createTxt()
    saveTxt()

    # Graphing ---------------------
    pos = p - (measures + 1)    
    if pos < 0: pos = 0
    extractData(pos)
    print ("Values obtained from database %s to print plots" % db)
    combHour()
    mainPlot()
    plotDir()
    plotComp()
    if p % 144 == 0 :
        pos1 = p - 144
        initVar()
        extractData(pos1)
        combHour()
        dailyPlot()
        print ("Daily plots drawn")
    print ("Graphs plotted")
    print ("Connection Processed number: ", j)
s.close()






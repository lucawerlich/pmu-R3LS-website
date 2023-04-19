from get_data import get_data_from_api
#from datetime import datetime
from scipy import signal
import numpy as np
import Preprocessing_V1 as dpp
from sys import argv
from json import dumps
import math
from matplotlib import pyplot as plt
import time
import datetime as dt
import matplotlib.dates as mdates


#from scipy.io import savemat
import os
import streamlit as st





#######################################################################################################
## FirstWindow

def FirstWindow(pmuSelect, windowWidth, slidingTime, safetyDelay, 
    ServerSampleRate, subSampleRateRatio, lower_filter, higher_filter, outlier_constant):
    
    
    os.system('cls')

    #######################################################################
    # Time format and units from DateTime module
    # Unix format: [number of milliseconds since (1970,jan,01,0,0,0,0)]
    # Date format: [year, month, day, hour, min, sec, microsec]
    # DateTime64 format : [year, month, day, hour, min, sec, millisec]

    # Time format and units from Time module
    # https://docs.python.org/3/library/time.html#time.gmtime
    # Time format: [number of secondes since epoch
    # standard epoch: January 1, 1970, 00:00:00 (UTC)
    # struct_time: 
    # functions: 
    # localtime(): from seconds since the epoch to struct_time in local time
    # mktime(): struct_time in local time to seconds since the epoch
    # ctime(): from time expressed in seconds since the epoch 
    #      to a string of a form: 'Sun Jun 20 23:21:05 1993'
    # strftime(format[, t]) Convert a tuple or struct_time representing a time as returned 
    #       by gmtime() or localtime(); format strftime(“%y-%m-%d-%H-%M”)
    # to a string as specified by the format argument
    # sleep(secs): Suspend execution
    #######################################################################

    

    #######################################################################
    # Geração da primeira janela

    iter = 1
    itermax = 10
    #######################################################################
    # gets current time and sets as beginProcessing time of first iteration
    timeNow = time.time()
    beginProcessing = timeNow

    #timeNow = 1678364362.297754


    #######################################################################
    # Sets startTime and endTime for first window
    # sets a previous time regarding current time considering a safetyDelay 
    endTime = math.floor(timeNow) - safetyDelay*60
    # defines startTime
    startTime = endTime - (windowWidth * 60)
    # sets endTime and startTime in [ms]
    endTimeUnix = endTime*1000
    startTimeUnix = startTime*1000

    # to be exclude
    timeNowSrt = time.strftime("%d/%b-%H:%M:%S", time.localtime(timeNow))
    endTimeStr = time.strftime("%d/%b-%H:%M:%S", time.localtime(endTime))
    startTimeStr = time.strftime("%d/%b-%H:%M:%S", time.localtime(startTime))


    #######################################################################
    # aquires data from server for first window
    apiData = np.array([get_data_from_api(
        startTimeUnix,
        endTimeUnix,
        feed_id=pmuSelect,
        interval= ServerSampleRate,
        interval_type=1,
        skip_missing=0
    )])
    # returns:
    # apiData[0][0] : time Unix format
    # apiData[0][1] : line frequência [Hz]

    #######################################################################
    # Splits data into time and frequency values and removes missing data
    RawTimeUnix = np.array([i[0] for i in apiData[0]])
    RawFreq = np.array([i[1] for i in apiData[0]], dtype=np.float64)

    # excludes last 2 points, so last RawTimeUnix is immediatly before endTimeUnix
    # it allows next startTimeUnix to be current endTimeUnix
    indexLastTwo = range(len(RawTimeUnix)-2,len(RawTimeUnix))
    RawTimeUnix = np.delete(RawTimeUnix, indexLastTwo , axis = 0)
    RawFreq = np.delete(RawFreq, indexLastTwo , axis = 0)


    # to be exclude - for evaluation purpouse
    """ RawFreq[0] = np.nan
    RawFreq[100] = np.nan
    RawFreq[1000] = np.nan
    RawFreq[5000] = np.nan
 """


    #######################################################################
    # processes data
    # ProcTimeUnix is necessary due to downsampling
    F = RawFreq.copy()
    T = RawTimeUnix.copy()
    ProcFreq, ProcTimeUnix, NanFreq, NanTimeUnix, OutlierFreq, OutlierTimeUnix, FMean, lowerLimit, higherLimit = dpp.preprocessamento(
        F, 
        T,
        ServerSampleRate,  
        subSampleRateRatio,
        lower_filter, 
        higher_filter, 
        outlier_constant
    )

    #######################################################################
    # Converts Time from Unix to DateTime64 and corrects time zone
    RawTimeDate64 = np.array(
        [np.datetime64(int(i - (3 * 3600000)), 'ms') for i in RawTimeUnix])
    ProcTimeDate64 = np.array(
        [np.datetime64(int(i - (3 * 3600000)), 'ms') for i in ProcTimeUnix])
    NanTimeDate64 = np.array(
        [np.datetime64(int(i - (3 * 3600000)), 'ms') for i in NanTimeUnix])
    OutlierTimeDate64 = np.array(
        [np.datetime64(int(i - (3 * 3600000)), 'ms') for i in OutlierTimeUnix])

    RawTimeDate64 = RawTimeDate64.astype(dt.datetime)

    #np.savetxt('RawTimeUnix.csv', RawTimeUnix, delimiter=',')
    #np.savetxt('RawFreq.csv', RawFreq, delimiter=',')


    #######################################################################
    YYRaw = [lowerLimit, higherLimit]
    XX = [RawTimeDate64[0], RawTimeDate64[0]]
    ZZ = [RawTimeDate64[-1], RawTimeDate64[-1]]
    timeaxis = [RawTimeDate64[0], RawTimeDate64[-1]]
    LL = [lowerLimit, lowerLimit]
    HL = [higherLimit, higherLimit]



    fig1, (ax1, ax2) = plt.subplots(2, 1, sharex = True)
    ax2.set_xlabel("Date", fontsize = 8)
    ax2.tick_params(axis='x', labelsize=6)
    ax1.set_title("Raw Frequency")
    ax2.set_title("Processed Frequency")
    ax1.set_ylabel('Freq [Hz]')
    ax2.set_ylabel('Freq [Hz]')

    ax1.plot(RawTimeDate64, RawFreq, 'b.', markersize=1)
    xfmt = mdates.DateFormatter("%b/%d-%H:%M:%S")
    ax2.xaxis.set_major_formatter(xfmt)
    ax1.plot(NanTimeDate64, NanFreq, 'r.', markersize=2)
    ax1.plot(OutlierTimeDate64, OutlierFreq, 'g.', markersize=2)

    ax1.plot(XX,YYRaw, color='green', linestyle='dashdot', linewidth=1)
    ax1.plot(ZZ,YYRaw, color='red', linestyle='dashdot', linewidth=1)

    ax1.plot(timeaxis, LL, color='yellow', linestyle='dashdot', linewidth=1)
    ax1.plot(timeaxis, HL, color='yellow', linestyle='dashdot', linewidth=1)


    YYProc = [min(ProcFreq), max(ProcFreq)]
    ax2.plot(ProcTimeDate64,ProcFreq,'.c')
    ax2.plot(XX,YYProc, color='green', linestyle='dashdot', linewidth=1)
    ax2.plot(ZZ,YYProc, color='red', linestyle='dashdot', linewidth=1)

    #plt.show(block=False)
    #plt.pause(1)



    with Graphs:
        Container01.pyplot(fig1)

    # sets indexFirstPoints if "slidingMode = Fixed" to be used on next iterations
    indexNewStartTime = (slidingTime * 60)* ServerSampleRate
    indexFirstPoints = range(0,int(indexNewStartTime))


    indexFirstPoints = range(0,int(indexNewStartTime))
    return [beginProcessing, endTimeUnix, RawTimeUnix, RawFreq, indexFirstPoints]
#######################################################################################################


#######################################################################################################
## NextWindows

def NextWindows(pmuSelect, windowWidth, slidingTime, safetyDelay, 
    ServerSampleRate, subSampleRateRatio, lower_filter, higher_filter, outlier_constant,
    beginProcessing, endTimeUnix, RawTimeUnix, RawFreq, indexFirstPoints):

    #######################################################################
    # gets current time and sets as finishProcessing of previous iteration 
    timeNow = time.time()
    finishProcessing = timeNow
    # calculates processingElapsedTime
    processingElapsedTime = finishProcessing - beginProcessing
    print('processing time: ', processingElapsedTime, sep = '')
    # suspend processing during timeToWait and then resumes
    timeToWait = slidingTime*60 - processingElapsedTime
    timeToWait = max(timeToWait,0)
    
    time.sleep(timeToWait)
    # gets current time and sets sets as beginProcessing time of current iteration 
    timeNow = time.time()
    beginProcessing = timeNow
    #######################################################################
    # Sets startTime and endTime for next data aquisition based on endTimeUnix of previous iteration
    startTimeUnix = endTimeUnix
    endTimeUnix = endTimeUnix + (slidingTime * 60 * 1000)
    
    
    ###########################################################
    # aquires data from server for new sliding window
    apiData = np.array([get_data_from_api(
        startTimeUnix,
        endTimeUnix,
        feed_id=pmuSelect,
        interval= ServerSampleRate,
        interval_type=1,
        skip_missing=0
    )])
    # returns:
    # apiData[0][0] : time Unix format
    # apiData[0][1] : line frequência [Hz]
    
    #######################################################################
    # Splits data into time and frequency values and exclude first two points
    #  and removes missing data
    RawTimeUnixSW = np.array([i[0] for i in apiData[0]])
    RawFreqSW = np.array([i[1] for i in apiData[0]], dtype=np.float64)

    # excludes last 2 points
    indexLastTwo = range(len(RawTimeUnixSW)-2,len(RawTimeUnixSW))
    RawTimeUnixSW = np.delete(RawTimeUnixSW, indexLastTwo , axis = 0)
    RawFreqSW = np.delete(RawFreqSW, indexLastTwo , axis = 0)

    #######################################################################
    # exclude first segment of RawTimeUnix and RawFreq corresponding to 
    # slidingwindow 
    # and includes new data acquired
    RawTime_ = []
    RawTime_ = np.delete(RawTimeUnix, indexFirstPoints , axis = 0)
    RawTimeUnix = []
    RawTimeUnix = np.append(RawTime_, RawTimeUnixSW)

    RawFreq_ = []    
    RawFreq_ = np.delete(RawFreq, indexFirstPoints , axis = 0)
    RawFreq = []
    RawFreq = np.append(RawFreq_, RawFreqSW)
    
    #######################################################################
    # excludes the entire processed data corresponding to previous window
    # ProcFreq FreqMean ProcTimeUnix
    ProcTimeUnix = []
    ProcFreq = []
    TimeProc = [] 
    FreqNan = [] 
    TimeNan = [] 
    FreqOutlier = [] 
    TimeOutlier = [] 

    # processes data corresponding to the entire new window
    #ProcTimeUnix is necessary due to downsampling

    #######################################################################
    # processes frequency
    #ProcTimeUnix is necessary due to downsampling
    F = RawFreq.copy()
    T = RawTimeUnix.copy()
    ProcFreq, ProcTimeUnix, NanFreq, NanTimeUnix, OutlierFreq, OutlierTimeUnix, FMean, lowerLimit, higherLimit = dpp.preprocessamento(
        F, 
        T,
        ServerSampleRate,  
        subSampleRateRatio,
        lower_filter, 
        higher_filter, 
        outlier_constant
    )

    #######################################################################
    # Converts Time from Unix to DateTime64 and corrects time zone
    RawTimeDate64 = []
    ProcTimeDate64 = []
    TimeNanDate64 = []
    TimeOutlierDate64 = []
    # Converts Time from Unix to DateTime64 and corrects time zone
    RawTimeDate64 = np.array(
        [np.datetime64(int(i - (3 * 3600000)), 'ms') for i in RawTimeUnix])
    ProcTimeDate64 = np.array(
        [np.datetime64(int(i - (3 * 3600000)), 'ms') for i in ProcTimeUnix])
    NanTimeDate64 = np.array(
        [np.datetime64(int(i - (3 * 3600000)), 'ms') for i in NanTimeUnix])
    OutlierTimeDate64 = np.array(
        [np.datetime64(int(i - (3 * 3600000)), 'ms') for i in OutlierTimeUnix])
    

    

    #######################################################################
    YYRaw = [lowerLimit, higherLimit]
    XX = [RawTimeDate64[0], RawTimeDate64[0]]
    ZZ = [RawTimeDate64[-1], RawTimeDate64[-1]]
    timeaxis = [RawTimeDate64[0], RawTimeDate64[-1]]
    LL = [lowerLimit, lowerLimit]
    HL = [higherLimit, higherLimit]


    #fig1.clear
    fig1, (ax1, ax2) = plt.subplots(2, 1, sharex = True)
    ax2.set_xlabel("Date", fontsize = 8)
    ax2.tick_params(axis='x', labelsize=6)
    ax1.set_title("Raw Frequency")
    ax2.set_title("Processed Frequency")
    ax1.set_ylabel('Freq [Hz]')
    ax2.set_ylabel('Freq [Hz]')


    YY = [lowerLimit, higherLimit]
    XX = [RawTimeDate64[0], RawTimeDate64[0]]
    ZZ = [RawTimeDate64[-1], RawTimeDate64[-1]]
    timeaxis = [RawTimeDate64[0], RawTimeDate64[-1]]
    LL = [lowerLimit, lowerLimit]
    HL = [higherLimit, higherLimit]

    

    ax1.plot(RawTimeDate64, RawFreq, 'b.', markersize=1)
    ax1.plot(NanTimeDate64, NanFreq, 'r.', markersize=2)
    ax1.plot(OutlierTimeDate64, OutlierFreq, 'g.', markersize=2)

    ax1.plot(XX,YYRaw, color='green', linestyle='dashdot', linewidth=1)
    ax1.plot(ZZ,YYRaw, color='red', linestyle='dashdot', linewidth=1)

    ax1.plot(timeaxis, LL, color='yellow', linestyle='dashdot', linewidth=1)
    ax1.plot(timeaxis, HL, color='yellow', linestyle='dashdot', linewidth=1)


    YYProc = [min(ProcFreq), max(ProcFreq)]
    ax2.plot(ProcTimeDate64,ProcFreq,'.c')
    ax2.plot(XX,YYProc, color='green', linestyle='dashdot', linewidth=1)
    ax2.plot(ZZ,YYProc, color='red', linestyle='dashdot', linewidth=1)

    #plt.show(block=False)
    #plt.pause(1)

    
    with Graphs:
        Container01.empty()
        Container01.pyplot(fig1)

    return [beginProcessing, endTimeUnix, RawTimeUnix, RawFreq, indexFirstPoints]



#######################################################################################################


#######################################################################################################
#st.set_page_config(page_title="Frequency Power Line Analisys", layout = "wide")


RunNextWindow = False
Data, Graphs = st.tabs(["Parameter specification", "Graph"])


with Data:
    st.header("Parameter specification for program execution")
with Graphs:
    st.header("Line frequency along time")
    Container01 = st.empty()

with Data:    
    DataForm = st.form("InputData")
    StopForm = st.form("StopButton")
    with DataForm:
        st.write("Specify the required data and press Start Processing")
        PMU = st.selectbox("Select a PMU to be analyzed", ('eficiencia','cabine', 'palotina', 'agrarias'), index = 1)
        if PMU == "eficiencia":
            pmuSelect = 506
        elif PMU == "cabine":
            pmuSelect = 515
        elif PMU == "palotina":
            pmuSelect = 524
        elif PMU == "agrarias":
            pmuSelect = 533

        windowWidth = st.number_input("Window Width [min]", min_value = 1.0, value = 30.0, step = 10.0)
        slidingTime = st.number_input("Sliding Time [min]", min_value = 0.1, value = 0.1, step = 1.0)
        safetyDelay = st.number_input("Safety Delay [min]", min_value = 0.0, value = 0.0, step = 5.0)
        ServerSampleRate = st.number_input("Server Sample Rate [samples/seconds] [a submultiple of 120: 1 2 3 4 6 12 30 60 120]", 
        min_value = 1, max_value = 120, value = 120, step = 1)
        subSampleRateRatio = st.number_input("sub Sample Rate Ratio", min_value = 1, max_value = 10, value = 1)
        lower_filter = st.number_input("Filter Low Cut-off Frequency [Hz]", min_value = 0.0, max_value = 60.0, value = 0.3, step = 0.1)
        higher_filter = st.number_input("Filter High Cut-off Frequency [Hz]", min_value = 0.0, max_value = 60.0,value = 7.0, step = 0.1)
        outlier_constant = st.number_input("Outlier Level [adm]", min_value = 1.0, max_value = 10.0, value = 3.0, step = 0.5)
        #Started = st.form_submit_button("Start Processing", on_click = RunSlidingWindow(pmuSelect, windowWidth, slidingTime, safetyDelay, ServerSampleRate, subSampleRateRatio, lower_filter, higher_filter, outlier_constant))
        Started = st.form_submit_button("Start Processing")

    with StopForm:
        ToStop = st.form_submit_button("Stop Current PMU analysis")


    if ToStop:
        Started = False
        RunNextWindow = False
        with Graphs:
            Container01.empty()
            Container01.write("PMU analysis stopped")
        
    if Started:
        [beginProcessing, endTimeUnix, RawTimeUnix, RawFreq, indexFirstPoints] = FirstWindow(pmuSelect, windowWidth, slidingTime, safetyDelay, 
            ServerSampleRate, subSampleRateRatio, lower_filter, higher_filter, outlier_constant)
        RunNextWindow = True

    while RunNextWindow:
        [beginProcessing, endTimeUnix, RawTimeUnix, RawFreq, indexFirstPoints] = NextWindows(pmuSelect, windowWidth, slidingTime, safetyDelay, 
            ServerSampleRate, subSampleRateRatio, lower_filter, higher_filter, outlier_constant,
            beginProcessing, endTimeUnix, RawTimeUnix, RawFreq, indexFirstPoints)

            
            



   

    
    
#######################################################################################################


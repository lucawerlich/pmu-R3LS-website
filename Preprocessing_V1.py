import math
from scipy import signal
import numpy as np
import matplotlib.pyplot as plt

# streamlit

def preprocessamento(Freq_, Time_, ServerSampleRate, subSampleRateRatio, filtLowpass, filtHighpass, k):
    # makes a safety copy of Time and Freq
    Time = Time_.copy()
    Freq = Freq_.copy()
    # remove NAN  and then performs Linear interpolation
    FWithoutNAN, nanIndex = linear_interpolation(Freq)
    # gets time where Freq equals Nan
    TimeNan = []
    FreqNan = []
    for i in nanIndex[0]:
        TimeNan = np.append(TimeNan, Time[i])
        FreqNan = np.append(FreqNan, 60)

    # Replaces Outlier with NAN
    FWithoutOutlier_, lowerLimit, higherLimit = mean_outlier_removal(FWithoutNAN, k=k)

    # removes NAN (previously an Outlier) and then performs Linear interpolation
    FWithoutOutlier, nanIndex = linear_interpolation(FWithoutOutlier_)
    # gets time where Freq equals Nan
    TimeOutlier = []
    FreqOutlier = []
    for i in nanIndex[0]:
        TimeOutlier = np.append(TimeOutlier, Time[i])
        FreqOutlier = np.append(FreqOutlier, Freq_[i])

    # Downsample
	# supondo que se deseja uma fs de 30 amostras por segundo
	# especifica-se fs de 120 hz para depois realizar o downsample para 30 amostras por segundo
	# a justificativa para isto é que, ao realizar a aquisição com fs de 30 amostras por segundo
	# é possível obter alguns valores de frequência nan ou outliers
	# realizando a aquisição com fs de 120 amostras por segundo
	# serão obtidos pontos adicionais no entorno (antes e depois) daqueles pontos obtidos com
	# fs de 30 amostras por segundo
	# desta forma o procedimento de realização da interpolação linear após 
	# excluir os nan e os outliers resultará em um valor mais consistente do que o 
	# obtido caso a fs já fosse de 30 amostras por segundo
    
    FDecimated = downsample(FWithoutOutlier, subSampleRateRatio)

    #FDecimated = FWithoutOutlier.copy()

    TimeProc = np.zeros(int(np.floor(len(Time)/ subSampleRateRatio)))
    #Apply decimation on the indexes of a vector (I attempted to use the decimate function but it changed values in DateTime/DateTime64 format)
    for i in range(0, len(TimeProc)):
        TimeProc[i] = Time[i*subSampleRateRatio]
    

    # Detrend
    FMean = np.nanmean(FDecimated)
    FZeroMean = FDecimated - np.nanmean(FDecimated)


    # HP filter
    FHighPassed = highpassFilter(FZeroMean, (ServerSampleRate/subSampleRateRatio), filtLowpass, 501)

    # LP filter
    FreqProc = lowpassFilter(FHighPassed, (ServerSampleRate/subSampleRateRatio), filtHighpass, 500)

    return FreqProc, TimeProc, FreqNan, TimeNan, FreqOutlier, TimeOutlier, FMean, lowerLimit, higherLimit


#################################################################

def linear_interpolation(Freq_):
    # makes a safety copy of Freq
    Freq = Freq_.copy()
    # Get location of nan and not nan values in array as True and False
    nanLocation = np.isnan(Freq)
    numberLocation = np.logical_not(nanLocation)
    nanIndex = np.where(nanLocation == True)
    
	# Linear interpolation at nan indexes
    Freq[nanLocation] = np.interp(nanLocation.nonzero()[0],
										numberLocation.nonzero()[0],
										Freq[~nanLocation])

    
    

    return Freq, nanIndex

#################################################################
def mean_outlier_removal(Freq_, k=3):
    # makes a safety copy of Freq
    Freq = Freq_.copy() 

	# Calculates mean and standard deviation
    freqMean = np.nanmean(Freq)
    freqStdLimit = np.nanstd(Freq) * k

	# Saves lower and higher filter limits
    lowerLimit = freqMean - freqStdLimit
    higherLimit = freqMean + freqStdLimit

	# Compares limits to data
    freqLowerMask = np.less_equal(Freq, lowerLimit)
    freqHigherMask = np.greater_equal(Freq, higherLimit)
    freqMask = np.logical_or(freqLowerMask, freqHigherMask)

	# Removes outliers if there's any
    if True in freqMask:
        outlierLocation = np.where(freqMask == True)
        for i in outlierLocation[0]:
            Freq[i] = np.nan

    return Freq, lowerLimit, higherLimit

#################################################################
def downsample(Freq_, subSampleRateRatio):
    # makes a safety copy of Freq
    Freq = Freq_.copy()
    signalDown = signal.decimate(Freq, subSampleRateRatio, zero_phase=True)
    return signalDown

#################################################################
def highpassFilter(x, fs, cutoff, order):
	# Calculates filter coefficients
	nyq = 0.5 * fs
	normal_cutoff = cutoff / nyq
	coef = signal.firwin(order, normal_cutoff, window='han', pass_zero="highpass")
	signalFilt = signal.lfilter(coef, 1, x)
	return signalFilt

#################################################################
def lowpassFilter(x, samplefreq, cutoff, order):
	# Calculates filter coefficients
	nyq = 0.5 * samplefreq
	normal_cutoff = cutoff / nyq
	coef = signal.firwin(order, normal_cutoff, window='han', pass_zero="lowpass", fs = samplefreq)
	signalFilt = signal.lfilter(coef, 1, x)
	return signalFilt

#################################################################

#################################################################

#################################################################


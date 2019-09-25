import numpy
import pylab
from operator import itemgetter
import scipy.signal as signal
import scipy.fftpack as fftpack
import random


class Wave:

    def __init__(self, data_x, data_y):
        self.waveData_x = data_x
        self.waveData_y = data_y
        self.filtered_wave_x = []
        self.filtered_wave_y = []
        self.method = {
            "median_filter" : 0,
            "lfilter" : 1,
            "fft_filter" : 2
        }

    def get_wave(self):
        return self.waveData_x, self.waveData_y

    def median_filtered(self):
        return signal.medfilt(self.waveData_y)

    def fft_filtered(self):
        length = len(self.waveData_y)
        spectrum = fftpack.fft(self.waveData_y)
        [low_cutoff, high_cutoff, f_sample] = [0.0, 60.0, 500.0]
        [low_point, high_point] = map(lambda F:F/f_sample * length/2, [low_cutoff, high_cutoff])
        filtered_spectrum = [spectrum[i] if i>=low_point and i<= high_point else 0.0 for i in xrange(length)]
        filtered_signal = fftpack.ifft(filtered_spectrum, n=length)
        return filtered_signal

    def filter(self, method_index=0):
        filters = [self.median_filtered, self.lfilter, self.fft_filtered]
        self.filtered_wave_x = self.waveData_x
        self.filtered_wave_y = filters[method_index]

    def find_peak(self, threshold, filtered=False):
        (working_wave_x, working_wave_y) = (self.filtered_wave_x, self.filtered_wave_y) if filtered else (self.waveData_x, self.waveData_y)
        step = 30
        division = []
        result = []
        for i in range(1, len(working_wave_y) - step - 1, step):
            if abs(working_wave_y[i] - working_wave_y[i+step]) >=threshold:
                division.append((i, i+step))

        for divide in division:
            start = divide[0]
            end = divide[1]
            min_index, element = min(enumerate(working_wave_y), key=itemgetter(1))
            minimum_y = min(working_wave_y[start:end])
            minimum_x = min_index ##should be start + min_index
            result.append((minimum_x, minimum_y)) 

        return result

    def find_minimum_point(self, filtered=False):
        if filtered:
            return self.filtered_wave_x[self.filtered_wave_y.argmin()], self.filtered_wave_y.min()
        else:
            return self.waveData_x[self.waveData_y.index(min(self.waveData_y))], min(self.waveData_y)

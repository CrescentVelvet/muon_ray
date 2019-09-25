from libs.oscilloscope.usb_devices import *
from pylab import *
from numpy import *
from ..utils.error import *
from libs.oscilloscope.wave import Wave
import time
import string


class ChannelParameters:
    def __init__(self, channel):
        self.channel = channel
        self.x_unit = 0
        self.x_inc = 0
        self.y_unit = 0
        self.y_mult = 0
        self.y_off = 0
        self.y_zero = 0


class TDS1012B:
    def __init__(self):
        self.visa = find_instrument()
        self.identity = 'TDS1012B'
        self.channel1 = ChannelParameters(1)
        self.channel2 = ChannelParameters(2)

    def query(self, content):
        try:
            q = self.visa.query(content)
        except:
            return -1
        return q

    def write(self, content):
        try:
            q = self.visa.write(content)
        except:
            return -1
        return q

    def read(self):
        try:
            q = self.visa.read()
        except:
            return -1
        return q

    def clear_queue(self):
        return self.query('*esr?')

    def set_channel(self, channel):
        if channel > 2 | channel < 1:
            e = Error("set_channel", "Incorrect channel parameter")
            return e

        self.write('data:source ch' + str(channel))
        return

    def get_scale_parameters(self, ch_parameter):

        if ch_parameter.channel > 2 | ch_parameter.channel < 1:
            e = Error("get_scale_parameters", "Incorrect channel parameter.")
            return e

        self.write('data:source ch' + str(ch_parameter.channel))

        ch_parameter.x_unit = self.query('wfmpre:xunit?').strip().strip('"')
        print(ch_parameter.x_unit)

        ch_parameter.x_inc = float(self.query('wfmpre:xinc?').strip())
        print(ch_parameter.x_inc)

        ch_parameter.y_unit = self.query('wfmpre:yunit?').strip().strip('"')
        print(ch_parameter.y_unit)

        ch_parameter.y_mult = float(self.query('wfmpre:ymult?').strip().strip('"'))
        print(ch_parameter.y_mult)

        ch_parameter.y_off = float(self.query('wfmpre:yoff?').strip().strip('"'))
        print(ch_parameter.y_off)

        ch_parameter.y_zero = float(self.query('wfmpre:yzero?').strip().strip('"'))
        print(ch_parameter.y_zero)

        return {}

    def get_wave_form(self, ch_parameter):
        e = {}
        if ch_parameter.channel > 2 | ch_parameter.channel < 1:
            e = Error("get_wave_form", "Incorrect channel parameter.")
            return e

        self.write('data:source ch'+str(ch_parameter.channel))
        self.write('data:encdg ascii')
        self.write('curve?')

        wave = self.read().split(',')
        x, y = self.scale_wave_form(wave, ch_parameter)
        self.wave = Wave(x,y)
        return e

    def scale_wave_form(self, wave, ch_parameter):
        y = []
        x = []
        x_pos = 0

        for data in wave:
            y.append((float(data)-ch_parameter.y_off)*ch_parameter.y_mult + ch_parameter.y_zero)
            x.append(x_pos)
            x_pos += ch_parameter.x_inc
        return x, y

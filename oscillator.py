from libs.oscilloscope.tek import TDS1012B
#import requests
class The_wave():
    def __init__(self,  directory):
        self.directory = directory
        
    def get_wave(self, vertical_scale, horizontal_scale, trig_value):
        self.device = TDS1012B()
        self.device.set_channel(1)
        isgood = self.device.write('hor:main:scale ' + str((int)(horizontal_scale)) + "e-6")
        if isgood == -1:
            return -1
        isgood = self.device.write('ch1:volts ' + str((int)(vertical_scale)))
        if isgood == -1:
            return -1
        isgood = self.device.write('trig:main:level '+ str(trig_value))
        if isgood == -1:
            return -1
        self.device.get_scale_parameters(self.device.channel1)
        isgood = self.device.write('acquire:stopafter sequence')
        if isgood == -1:
            return -1
        st = '0'
        isgood = st = self.device.query('acquire:state?').strip()
        if isgood == -1:
            return -1
        while(st != '0'):
        	st = self.device.query('acquire:state?').strip()
        e = self.device.get_wave_form(self.device.channel1)
        ax, ay = self.device.wave.get_wave()
        self.device.write('acquire:state on')
        return ax,  ay

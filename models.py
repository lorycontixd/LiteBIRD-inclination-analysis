import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

def fig_hist(data,ylabels, xvalues, title=''):
    figure, ax = plt.subplots()
    ax.hist(data)
    ax.set_xlabel("Angle")
    ax.set_ylabel("Counts")
    if title:
        plt.title(title)
    return figure,ax

def fig_plot(xdata,ydata,xlabels,ylabels,title=""):
    pass

class Planet():
    def __init__(self,name=None,temperature=None,radius=None):
        super().__init__()
        self.name = name
        self.temperature =temperature
        self.radius = radius

class Plot():
    def __init__(self,name="",figure=None):
        super().__init__()
        self.name = name
        self.figure = figure
    """
    @property
    def figure(self):
        return self.plot

    @figure.getter
    def figure(self):
        return self.figure
    
    @figure.setter
    def figure(self,f):
        self.figure = f
    
    @figure.deleter
    def figure(self):
        del self.figure
    """



class Information():
    def __init__(
            self,
            **kwargs
        ):
        valid_keys = [
            "planet",
            "frequency",
            "inclination",
            "runs",
            "fwhm",
            "fwhm_error",
            "ampl",
            "ampl_error",
            "ampl_point" #Save the point (angle, gamma) to be passed forward
        ]
        super().__init__()
        for vk in valid_keys:
            if vk in kwargs:
                setattr(self,vk,kwargs[vk])
            else:
                setattr(self,vk,None)
        self.plots = []
    
    """
    @property
    def planet(self):
        return self.planet

    @property
    def frequency(self):
        return self.frequency

    @property
    def inclination(self):
        return self.inclination

    @planet.setter
    def planet(self,p:Planet):
        self.planet = p
    
    @planet.getter
    def planet(self):
        return self.planet

    @frequency.setter
    def frequency(self,freq:str):
        accepted = ["low","mid","high"]
        if freq not in accepted:
            raise ValueError(f"Frequency Setter: invalid parameter {freq}")
        self.frequency = freq
    
    @frequency.getter
    def frequency(self):
        return self.frequency
    
    @inclination.setter
    def inclination(self,angle:float):
        self.inclination = angle
    
    @inclination.getter
    def inclination(self):
        return self.inclination
    """


class Data():
    def __init__(self,debug=False):
        self.debug = debug
        self.valid_freqs = ["low","mid","high"]
        self.valid_planets = ["jupiter","neptune","uranus"]
        self.debug = True
        self.data_jupiter = {
            "low" : [],
            "mid" : [],
            "high" : []
        }
        self.data_neptune = {
            "low" : [],
            "mid" : [],
            "high" : []
        }
        self.data_uranus = {
            "low" : [],
            "mid" : [],
            "high" : []
        }
    """
    def __setitem__(self,item,value):
        if self.debug:
            l.info(f"Set {item} to {value}")
    
    def __getitem__(self,item):
        if self.debug:
            l.info(f"Received key {item}")
    """
    
    def check_planet(self,planet):
        if not isinstance(planet,str):
            raise TypeError(f"(Data) Planet must be a string, not {type(planet)}")
        if planet not in self.valid_planets:
            raise ValueError(f"(Data) Planet cannot be {planet}")
    
    def check_frequency(self,freq):
        if not isinstance(freq,str):
            raise TypeError(f"(Data) Freqency must be a string, not {type(freq)}")
        if freq not in self.valid_freqs:
            raise ValueError(f"(Data) Frequency cannot be {freq}")

    def append_data(self,planet:str,freq:str,data):
        if not isinstance(data,tuple):
            raise TypeError(f"(Data) Invalid type for data {type(data)}. Must be a tuple with (angle,gamma_error).")
        self.check_planet(planet)
        self.check_frequency(freq)
        exec(f"self.data_{planet}['{freq}'].append({data})")

    def get_planet(self,planet:str):
        planet = planet.lower()
        self.check_planet(planet)
        return eval(f"self.data_{planet}") #Dict 

    def get_planet_frequency(self,planet:str,frequency:str):
        planet = planet.lower()
        self.check_planet(planet)
        self.check_frequency(frequency)
        return eval(f"self.data_{planet}['{frequency}']") #List
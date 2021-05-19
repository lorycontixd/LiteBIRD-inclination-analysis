import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from dataclasses import dataclass,field

def fig_hist(data,ylbl,xlbl, title=''):
    figure, ax = plt.subplots()
    ax.hist(data)
    ax.set_xlabel(xlbl)
    ax.set_ylabel(ylbl)
    if title:
        plt.title(title)
    return figure,ax

def fig_plot(xdata,ydata,xlabels,ylabels,title=""):
    pass

def create_table():
    pass

def rad2arcmin(x):
    if isinstance(x,(list,tuple)):
        t = type(x)
        return t([item*3437.75 for item in x])
    elif isinstance(x,(float,int)):
        return x*3437.75
    else:
        raise TypeError(f"Invalid type {type(x)} for rad2arcmin call.")

def arcmin2rad(x):
    if isinstance(x,(list,tuple)):
        t = type(x)
        return t([item/3437.75 for item in x])
    elif isinstance(x,(float,int)):
        return x/3437.75
    else:
        raise TypeError(f"Invalid type {type(x)} for rad2arcmin call.")

@dataclass(init=True, repr=True)
class Planet():
    """[Planet class]
Represents an instance of a planet, holding the following attributes:
- name (str): Name of the planet
- temperature (str): temperature of the planet (in Kelvin)
- radius (int): radius of the planet (in meters)
    """
    name: str = None
    temperature : str = None
    radius : int = None

class Plot():
    """[Plot class]
Holds information for a graph computed with matplotlib's PyPlot
- name (str): Name of the graph (used as ID)
- figure (graph): The figure holding the graph
    """
    def __init__(self,name="",figure=None):
        super().__init__()
        self.name = name
        self.figure = figure

@dataclass
class Information():
    """[Information class]
Holds various information that is passed on from the computational section of the code, where the MonteCarlo simulations are exectued, to the data analysis code.
This method is much more structured and easier to understand than other methods to pass on information through functions.

- planet (str): The planet used for the simulation
- frequency (str): The frequency used for the simulation
- inclination (float = 0.0): Inclination angle used for the simulation
- runs (int = 500): Number of MonteCarlo runs for the simulation
- fwhm (float = 0.0): Result for the FWHM from the simulation
- fwhm_error (float = 0.0): Result for the FWHM error from the simulation 
- angle (float = 0.0): Result for the inclination angle from the simulation
- angle_error (float = 0.0): Result for the inclination angle error from the simulation 
- ampl (float = 0.0): Result for the radiation amplitude/intensity from the simulation
- ampl_error (float = 0.0): Result for the radiation amplitude/intensity error from the simulation 
- ecc (float = 0.0): 
- ecc_error (float = 0.0):
- ampl_point (tuple = (0.0,0.0)): ?
- plots (list): list of plots from the outcome of the simulation
"""
    planet : str = None
    frequency : str = None
    inclination : float = 0.0
    runs : int = 500
    fwhm : float = 0.0
    fwhm_error : float = 0.0
    angle : float = 0.0
    angle_error : float = 0.0
    ampl : float = 0.0
    ampl_error : float = 0.0
    ampl_point : tuple = (0.0,0.0)
    ecc : float = 0.0
    ecc_error : float = 0.0
    maps : tuple = None
    hitmap : np.array = None
    plots : list = field(default_factory = lambda:[],repr = False, init = False)

    def __post_init__(self):
        if self.planet is None:
            raise ValueError("Planet must not be None.")
        else:
            valid = ["jupiter","neptune","uranus"]
            if self.planet.lower() not in valid:
                raise ValueError(f"Planet name not valid: {self.planet}")
        if self.frequency is None:
            raise ValueError("Frequency must not be None.")
    
    def __getitem__(self, key):
        return  self.__dict__[key]


class Data():
    """
        Container class for simulation data.
        - name: name of the data stored in the class
        - debug (bool): if true, prints to console operations done on the data
    """
    def __init__(self,name=None,debug=False):
        if name is None:
            raise ValueError("Name of Data object must be passed.")
        self.name = name
        self.valid_freqs = ["low","mid","high"]
        self.valid_planets = ["jupiter","neptune","uranus"]
        self.debug = debug
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
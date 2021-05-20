#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
import math
import models
import importlib
from tabulate import tabulate
from dataclasses import dataclass
import json
import time
import os,sys
from pathlib import Path
from shutil import copyfile
from typing import Dict, Any, List, Union
import subprocess as s
import markdown as md
from scipy.interpolate import UnivariateSpline
import timeit
import subprocess
import database
import settings


import logging
logging.basicConfig(
    level = logging.INFO,
    format = '[%(asctime)s] %(levelname)s: %(message)s',
    datefmt = '%m/%d/%Y %H:%M:%S'
)

from tqdm import tqdm

import litebird_sim as lbs

import healpy
import numpy as np
from scipy import optimize, interpolate, integrate

import matplotlib

matplotlib.use("Agg")
import matplotlib.pylab as plt
import matplotlib.pyplot as plot

PLANET_RADIUS = {
    "jupiter" : 7.1492e+07,
    "neptune" : 2.4622e+07,
    "uranus" : 2.5362e+07
}

TELESCOPES = {
    "low" : "LFT/L1-040",
    "mid" : "MFT/M2-166",
    "high" : "HFT/H3-402"
}

FREQUENCIES = {
    "low" : 40,
    "mid" : 166,
    "high" : 402
}

@dataclass
class Parameters:
    planet_name: str
    sed_file_name: str
    planet_radius_m: float
    scanning_simulation: Path
    detector: lbs.DetectorInfo
    num_of_mc_runs: int
    error_amplitude_map_file_name: str
    eccentricity: float
    inclination: float

    def __post_init__(self):
        self.sed_file_name = Path(self.sed_file_name)
        self.scanning_simulation = Path(self.scanning_simulation)

def end_fig():
    plt.close()

def get_radius(planet):
    return PLANET_RADIUS[planet]

def get_telescope(frequency):
    if frequency == "low":
        return "LFT/L1-040"
    elif frequency == "mid":
        return "MFT/M2-166"
    else:
        return "HFT/H3-402"

def check_planet(planet):
    planet = planet.lower()
    valid = ["jupiter","neptune","uranus"]
    if planet not in valid:
        raise ValueError(f"Invalid planet {planet}")
    radius = get_radius(planet)
    return (planet,radius)

def check_frequency(freq):
    freq = freq.lower()
    valid = ["low","mid","high"]
    if freq not in valid:
        raise ValueError(freq)
    telescope = get_telescope(freq)
    return (freq,telescope)

def create_toml(settings,planet,frequency,inclination):
    planet,radius = check_planet(planet)
    frequency,telescope = check_frequency(frequency)
    with open('tempfile.toml', 'w+') as file:
        content = f"""[simulation]
base_path = "./results/"
num_of_mc_runs = {settings.simulation_runs}

[planet]
planet_name = "{planet}"
sed_file_name = "sed_files/{planet}_hf3.csv"
planet_radius_m = {radius}
scanning_simulation = "./scanning_strategies/{planet}/"

[detector]
channel_obj = "/releases/v1.0/satellite/{telescope}/channel_info"
sampling_rate_hz = 1.0
eccentricity = {settings.simulation_eccentricity}
frequency = "{frequency}"
inclination = {inclination}
"""
        #print(content)
        file.write(content)

def parse_frequency(freq:str):
    return freq

def check_eccentricity(e):
    assert 0<=e<1,f"Invalid value of e {e}"

def read_detector(parameters: Dict[str, Any], imo: lbs.Imo):
    if "channel_obj" in parameters:
        detobj = lbs.FreqChannelInfo.from_imo(
            imo, parameters["channel_obj"]
        ).get_boresight_detector()

    elif "detector_obj" in parameters:
        detobj = lbs.DetectorInfo.from_imo(imo, parameters["detector_obj"])
    else:
        detobj = lbs.DetectorInfo()

    for param_name in (
        "name",
        "wafer",
        "pixel",
        "pixtype",
        "channel",
        "sampling_rate_hz",
        "fwhm_arcmin",
        "net_ukrts",
        "fknee_mhz",
        "fmin_hz",
        "alpha",
        "pol",
        "orient",
        "frequency"
        "eccentricity",
        "bandwidth_ghz",
        "bandcenter_ghz",
        "inclination"
    ):
        if param_name in parameters:
            setattr(detobj, param_name, parameters[param_name])

    return detobj


def load_parameters(sim: lbs.Simulation) -> Parameters:
    return Parameters(
        planet_name=sim.parameters["planet"]["planet_name"],
        sed_file_name=sim.parameters["planet"]["sed_file_name"],
        planet_radius_m=sim.parameters["planet"]["planet_radius_m"],
        scanning_simulation=sim.parameters["planet"]["scanning_simulation"],
        detector=read_detector(sim.parameters["detector"], sim.imo),
        eccentricity=sim.parameters["detector"]["eccentricity"],
        num_of_mc_runs=sim.parameters["simulation"].get("num_of_mc_runs", 20),
        error_amplitude_map_file_name=sim.parameters["simulation"].get(
            "error_amplitude_map_file_name", "error_map.fits"
        ),
        inclination=np.deg2rad(sim.parameters["detector"]["inclination"])
    )

#**************************************+   BEAM FUNCTIONS   **********************************************

def beamfunc(pixel_theta, fwhm_arcmin, amplitude=1.0):
    return amplitude * np.exp(
        -np.log(2) * ((pixel_theta / np.deg2rad(fwhm_arcmin / 60.0)) ** 2)
    )

def asymmetric_beam_good(mytuple,fwhm_arcmin,eccentricity,angle,amplitude=1.0):
    pixel_theta, pixel_phi = mytuple
    sin_theta = np.sin(pixel_theta) 
    x = sin_theta * np.cos(pixel_phi)
    y = sin_theta * np.sin(pixel_phi)
    #assert len(x) == len(y), "DimensionalError: theta and phi must have the same length"
    u = np.cos(angle)*x + np.sin(angle)*y
    v = -np.sin(angle)*x + np.cos(angle)*y
    a0 = fwhm_arcmin
    a2 = a0*(1-eccentricity)
    exponential = -np.log(2) * ( (u/np.deg2rad(a0 / 60.0))**2 + (v/np.deg2rad(a2/60.0))**2 )
    return amplitude * np.exp(exponential)


#********************************************************************************************************

def calc_beam_solid_angle(fwhm_arcmin,eccentricity,angle):
    return integrate.dblquad(
        lambda phi,theta: (
            np.sin(theta) * asymmetric_beam_good((theta,phi), fwhm_arcmin,eccentricity,angle)
        ), 0, np.pi,lambda theta: 0, lambda theta: np.pi
    )[0]             #CHANGED


def project_map_north_pole(pixels, width_deg, pixels_per_side=150):
    theta_max = np.deg2rad(width_deg)
    u = np.linspace(-np.sin(theta_max), +np.sin(theta_max), pixels_per_side)
    v = np.linspace(-np.sin(theta_max), +np.sin(theta_max), pixels_per_side)
    u_grid, v_grid = np.meshgrid(u, v)
    theta_grid = np.arcsin(np.sqrt(u_grid ** 2 + v_grid ** 2))
    phi_grid = np.arctan2(v_grid, u_grid)
    return (
        u_grid,
        v_grid,
        healpy.get_interp_val(pixels, theta_grid.flatten(), phi_grid.flatten()).reshape(
            pixels_per_side, -1
        ),
    )


def create_uv_plot(
    fig, ax, pixels, width_deg, contour_lines=True, smooth=False, fwhm_arcmin=None
):
    from scipy.ndimage.filters import gaussian_filter

    u_grid, v_grid, grid = project_map_north_pole(pixels, width_deg)

    if smooth:
        grid = gaussian_filter(grid, 0.7)

    cs = ax.contourf(u_grid, v_grid, grid, cmap=plt.cm.bone)

    if fwhm_arcmin:
        from matplotlib.patches import Circle

        ax.add_artist(
            Circle(
                (0, 0),
                np.sin(np.deg2rad(fwhm_arcmin / 60.0)),
                edgecolor="w",
                lw=5,
                facecolor="none",
                alpha=0.25,
            )
        )

    if contour_lines:
        cs2 = ax.contour(cs, levels=cs.levels[::2], colors="r")
        ax.clabel(cs2)

    ax.set_xlabel("U coordinate")
    ax.set_ylabel("V coordinate")
    ax.set_aspect("equal")

    cbar = fig.colorbar(cs)

    if contour_lines:
        cbar.add_lines(cs2)


def create_gamma_plots(gamma_map, gamma_error_map, fwhm_arcmin):
    plot_size_deg = 2 * fwhm_arcmin / 60.0

    gamma_fig, gamma_ax = plt.subplots()
    create_uv_plot(
        gamma_fig, gamma_ax, gamma_map, width_deg=plot_size_deg, fwhm_arcmin=None
    )

    gamma_error_fig, gamma_error_ax = plt.subplots()
    create_uv_plot(
        gamma_error_fig,
        gamma_error_ax,
        gamma_error_map,
        width_deg=plot_size_deg,
        contour_lines=False,
        fwhm_arcmin=fwhm_arcmin,
    )

    gamma_over_error_fig, gamma_over_error_ax = plt.subplots()
    create_uv_plot(
        gamma_over_error_fig,
        gamma_over_error_ax,
        gamma_map / gamma_error_map,
        width_deg=plot_size_deg,
        smooth=True,
        fwhm_arcmin=fwhm_arcmin,
    )

    return (plot_size_deg, gamma_fig, gamma_error_fig, gamma_over_error_fig)

def read_file(filename):
    lines = open(filename,"r+").readlines()
    mylist = []
    for line in lines[1:]:
        elems = line.split(",")
        mylist.append((elems[0],elems[4]))
    return mylist

def write_to_file(filename,ecc_true,n_of_runs,ecc_estimate,fwhm,fwhm_error):
    file = open(filename,"a+")
    #file.write(f"{n_of_runs},{fwhm},{fwhm_error}")
    if os.stat(filename).st_size == 0:
        file.write("eccenticity,n_runs,ecc_estimate,fwhm,fwhm_error")
        #print("eccenticity,n_runs,ecc_estimate,fwhm,fwhm_error")
    #print(f"{ecc_true},{n_of_runs},{ecc_estimate},{fwhm},{fwhm_error}")
   # file.write(f"{ecc_true},{n_of_runs},{ecc_estimate},{fwhm},{fwhm_error}")
   
def compute(i,tot,planet,data_path: Path,logger_debug:bool, data_debug:bool):
    angle_data= []
    ampl_data = []
    
    sim = lbs.Simulation(
        parameter_file=str(data_path),
        name="In-flight estimation of the beam properties",
        base_path="./results/",
        description="""
This report contains the result of a simulation of the reconstruction
of in-flight beam parameters, assuming a scanning strategy and some
noise/optical properties of a detector.
""",
    )
    params = load_parameters(sim)

    det = read_detector(sim.parameters["detector"], sim.imo)
    _frequency = parse_frequency(sim.parameters["detector"]["frequency"])

    # TODO: This should be done by the framework
    copyfile(
        src=params.sed_file_name, dst=sim.base_path / params.sed_file_name.name,
    )
    print(" ")
    if logger_debug:
        logging.info(f"Starting simulation {i} of {tot}")
        logging.info(f"Planet: {params.planet_name.capitalize()}")
        logging.info(f"Frequency: {str(_frequency).capitalize()}")
        logging.info(f"Inclination angle: {params.inclination} [rad] --> {np.rad2deg(params.inclination)} [deg]")
    info = models.Information(
        planet = params.planet_name,
        frequency = _frequency,
        inclination = params.inclination
    )
    
    # Calculate the brightness temperature of the planet over the band
    print("sed file: ",params.sed_file_name)
    sed_data = np.loadtxt(params.sed_file_name, delimiter=",")
    sed_fn = interpolate.interp1d(sed_data[:, 0], sed_data[:, 1],bounds_error=False,fill_value=1)
    print("sed_fn: ",sed_fn)
    planet_temperature_k = (
        integrate.quad(
            sed_fn,
            params.detector.bandcenter_ghz - params.detector.bandwidth_ghz / 2,
            params.detector.bandcenter_ghz + params.detector.bandwidth_ghz / 2,
        )[0]
        / params.detector.bandwidth_ghz
    )

    print("temp: ",planet_temperature_k)
    print("fwhm input: ",det.fwhm_arcmin)
    print("ecc input: ",params.eccentricity)

    beam_solid_angle = calc_beam_solid_angle(fwhm_arcmin=det.fwhm_arcmin,eccentricity=params.eccentricity,angle=params.inclination)
    sampling_time_s = 1.0 / params.detector.sampling_rate_hz

    input_map_file_name = params.scanning_simulation / "map.fits.gz"

    hit_map, time_map_s, dist_map_m2 = healpy.read_map(
        input_map_file_name, field=(0, 1, 2), verbose=False, dtype=np.float32
    )
    nside = healpy.npix2nside(len(dist_map_m2))
    pixel_theta, pixel_phi = healpy.pix2ang(nside, np.arange(len(hit_map)))

    gamma_map = asymmetric_beam_good(
        (pixel_theta, pixel_phi), params.detector.fwhm_arcmin, params.eccentricity, params.inclination, 1.0)                                                # CHANGED

    mask = (hit_map > 0.0) & (
        pixel_theta < np.deg2rad(3 * params.detector.fwhm_arcmin / 60.0)
    )
    assert hit_map[mask].size > 0, "no data available for the fit"

    error_amplitude_map = (
        beam_solid_angle
        * (params.detector.net_ukrts * 1e-6)
        / (
            np.pi
            * (params.planet_radius_m ** 2)
            * planet_temperature_k
            * np.sqrt(sampling_time_s)
        )
    ) * dist_map_m2

    if data_debug:
        print("\nPrinting sqrt terms:")
        print("Solid angle: ",beam_solid_angle)
        print("WN: ",params.detector.net_ukrts * 1e-6)
        print("Planet radius: ",params.planet_radius_m," ----> radius squared: ",params.planet_radius_m**2)
        print("Planet temperature: ",planet_temperature_k)
        print("Sqrt tau: ",np.sqrt(sampling_time_s))
        print("Bandcenter: ",params.detector.bandcenter_ghz,"\tBandwidth: ",params.detector.bandwidth_ghz)
        print(" ")
    #print(dist_map_m2)
    

    (
        plot_size_deg,
        gamma_fig,
        gamma_error_fig,
        gamma_over_error_fig,
    ) = create_gamma_plots(
        gamma_map, error_amplitude_map, fwhm_arcmin=params.detector.fwhm_arcmin,
    )

    
#(gamma_fig, "gamma.svg"),
#(gamma_error_fig, "gamma_error.svg"),
#(gamma_over_error_fig, "gamma_over_error.svg"),

    destfile = sim.base_path / params.error_amplitude_map_file_name
    healpy.write_map(
        destfile,
        [gamma_map, error_amplitude_map],
        coord="DETECTOR",
        column_names=["GAMMA", "ERR"],
        column_units=["", ""],
        dtype=[np.float32, np.float32, np.float32],
        overwrite=True,
    )
    
    fwhm_estimates_arcmin = np.empty(params.num_of_mc_runs)
    ampl_estimates = np.empty(len(fwhm_estimates_arcmin))
    eccentricity_estimates = np.empty(len(fwhm_estimates_arcmin))
    angle_estimates = np.empty(len(fwhm_estimates_arcmin))

    for i in tqdm(range(len(fwhm_estimates_arcmin))):
        noise_gamma_map = gamma_map + error_amplitude_map * np.random.randn(
            len(dist_map_m2)
        )
        # Run the fit
        best_fit,pcov = optimize.curve_fit(
            asymmetric_beam_good,
            (pixel_theta[mask],pixel_phi[mask]),
            noise_gamma_map[mask],
            p0=[params.detector.fwhm_arcmin, params.eccentricity, params.inclination, 1.0],
            maxfev=10000
        )
        fwhm_estimates_arcmin[i] = best_fit[0]
        eccentricity_estimates[i] = best_fit[1]
        angle_estimates[i] = best_fit[2]
        ampl_estimates[i] = best_fit[3]
    
    fwhm_fig,fwhm_ax = models.fig_hist(fwhm_estimates_arcmin,"Counts","FWHM [arcmin]","FWHM distribution")
    fwhm_plot = models.Plot("FWHM",fwhm_fig)
    end_fig()

    ampl_fig,ampl_ax = models.fig_hist(ampl_estimates,"Counts","AMPL [arcmin]","Amplitude distribution (Gamma)")
    ampl_plot = models.Plot("AMPL",ampl_fig)
    end_fig()

    ecc_fig,ecc_ax = models.fig_hist(eccentricity_estimates,"Counts","Eccentricity","Eccentricity distribution")
    ecc_plot = models.Plot("ECC",ecc_fig)
    end_fig()

    angle_fig,angle_ax = models.fig_hist(angle_estimates,"Counts","Inclination Angle","Inclination distribution")
    ang_plot = models.Plot("ANGLE",angle_fig)
    end_fig()
    
    planet_ = models.Planet(params.planet_name.capitalize(),"%.2f" % planet_temperature_k,params.planet_radius_m)
    info.planet = planet_
    info.frequency = _frequency
    info.inclination = float(params.inclination)
    info.runs = len(fwhm_estimates_arcmin)
    info.fwhm = np.mean(fwhm_estimates_arcmin)
    info.fwhm_error = np.std(fwhm_estimates_arcmin)
    info.angle = np.mean(angle_estimates)
    info.angle_error = np.std(angle_estimates)
    info.ampl = np.mean(ampl_estimates)
    info.ampl_error = np.std(ampl_estimates)
    info.ecc = np.mean(eccentricity_estimates)
    info.ecc_error = np.std(eccentricity_estimates)
    info.maps = (gamma_map,error_amplitude_map)
    info.hitmap = hit_map
    info.plots = [fwhm_plot,ampl_plot,ecc_plot,ang_plot]
    
    print("FWHM error: ",np.std(fwhm_estimates_arcmin)," - ",info.fwhm_error)
    print("Angle error: ",np.std(angle_estimates)," - ",info.angle_error)
    return info

def remove_temptoml(logger_debug:bool):
    if os.path.isfile('tempfile.toml'):
        subprocess.run(["rm","-rf","tempfile.toml"],shell=True)
        if (logger_debug):
            print("[MAIN] tempfile.toml file has been deleted")

def clear_map_files():
    subprocess.run(["chmod +x clean_maps.sh"],shell=True)
    subprocess.run(["./clean_maps.sh"])

def write_maps_to_file(i,planet,freq,angle,gamma_map=None,error_map=None,hit_map=None,logger_debug=True):
    """Saves maps to file:
    -- Gamma_map: map of the radiation pattern
    -- Error_map: map of the error of the radiation pattern
    """
    planet = planet.lower()
    base_dir = "results/maps/"
    planets = ["jupiter","neptune","uranus"]
    if planet not in planets:
        raise ValueError(f"Invalid planet {planet} for write_maps.")
    directories = [base_dir+str(p) for p in planets]
    for dir in directories:
        if not os.path.isdir(dir):
            subprocess.run(["mkdir",dir])
    angle = float("{:.2f}".format(angle))

    if gamma_map is not None:
        map_file = open(f"{base_dir}{planet}/gammamap_{freq}_{angle}.dat","w+")
        for x in gamma_map:
            map_file.write(str(x)+"\n")
        map_file.close()
    
    if error_map is not None:
        error_file = open(f"{base_dir}{planet}/errormap_{freq}_{angle}.dat","w+")
        for x in error_map:
            error_file.write(str(x)+"\n")
        error_file.close()
    
    if hit_map is not None:
        hitmap_file = open(f"{base_dir}{planet}/hitmap_{freq}_{angle}.dat","w+")
        for x in hit_map:
            hitmap_file.write(str(x)+"\n")
        hitmap_file.close()
    
    if (logger_debug):
        print("Pixel maps written to file")
    return


def main(filename:str):
    mysettings = settings.Settings(filename)
    sim2 = lbs.Simulation(
        base_path = "results/",
        name = mysettings.simulation_title,
        description= mysettings.simulation_description
    )
    if mysettings.settings_loggerdebug:
        print(mysettings)
    angle_data = models.Data(name="angles") #Store simulation results (or informations)
    fwhm_data = models.Data(name="fwhm")
    infos = []
    if mysettings.database_active:
        d = database.SimulationDatabase("db/"+mysettings.database_name)
        d.create_simulation()
    if mysettings.settings_clear_maps:
        clear_map_files()
    intro = """
# Base information
This report contains information about the dependency of the in-flight beam's inclination angle on planet and telescope frequency.
The document contains plots
    """
    sim2.append_to_report(intro)
    index = 0
    tot = len(mysettings.simulation_planets)*len(mysettings.simulation_frequencies)*len(mysettings.simulation_angles)
    for p in mysettings.simulation_planets:
        for f in mysettings.simulation_frequencies:
            for a in mysettings.simulation_angles:
                create_toml(mysettings,p,f,a) # Create a temporary TOML file with parameters
                info = compute(index+1,tot,p,"tempfile.toml",mysettings.settings_loggerdebug,mysettings.settings_datadebug) #extract data from the simulation by passing the temporary TOML file
                angle_data.append_data(p,f,(models.rad2arcmin(info.inclination),models.rad2arcmin(info.angle_error)))
                fwhm_data.append_data(p,f,(models.rad2arcmin(info.inclination),info.fwhm_error))
                if mysettings.settings_save_error_map:
                    write_maps_to_file(index,p,f,a,error_map = info.maps[1],logger_debug=mysettings.settings_loggerdebug)
                if mysettings.settings_save_hitmap:
                    write_maps_to_file(index,p,f,a,hit_map = info.hitmap,logger_debug=mysettings.settings_loggerdebug)
                if mysettings.database_active:
                    d.insert_run(info)
                sim2.append_to_report("""
### Results of the Monte Carlo simulation:  {{pname}} - {{freq}} - {{inc}}

Parameter  | Value
---------- | -----------------
# of runs  | {{ num_of_runs }}
FWHM       | {{"%.3f"|format(fwhm_arcmin)}} ± {{"%.3f"|format(fwhm_err)}} arcmin
γ0         | {{"%.3f"|format(ampl)}} ± {{"%.3f"|format(ampl_err)}} arcmin
e          | {{"%.3f"|format(ecc)}} ± {{"%.3f"|format(ecc_err)}} 
theta      | {{"%.3f"|format(angle)}} ± {{"%.3f"|format(angle_err)}} 

![](fwhm_distribution.svg)

![](ampl_distribution.svg)

![](ecc_distribution.svg)

![](angle_distribution.svg)
""",
                    figures=[
                        (info.plots[0].figure, "fwhm_distribution.svg"),
                        (info.plots[1].figure, "ampl_distribution.svg"),
                        (info.plots[2].figure, "ecc_distribution.svg"),
                        (info.plots[3].figure,"angle_distribution.svg")
                    ],
                    pname = info.planet.name,
                    freq = info.frequency,
                    inc = info.inclination,
                    num_of_runs=info.runs,
                    fwhm_arcmin=info.fwhm,
                    fwhm_err=info.fwhm_error,
                    ampl=info.ampl,
                    ampl_err=info.ampl_error,
                    ecc=info.ecc,
                    ecc_err = info.ecc_error,
                    angle=info.angle,
                    angle_err=info.angle_error
                )
                index +=1
        
    #Information was stored in a Data object instead of being iterated directly to make it visually easier to understand
    #At this point we have a Data object with 3 different planets each with 3 different frequencies and each is a list of tuples (angle,gamma_error)
    
    for p in mysettings.simulation_planets:
        fig, (ax1, ax2) = plt.subplots(nrows = 2, ncols = 1, sharex = True,figsize=(5, 5))
        ax1.set_xlabel("Inclination angle [arcmin]")
        ax1.get_xaxis().set_visible(False)
        ax2.set_xlabel("Inclination angle [arcmin]")
        ax1.set_ylabel("FWHM Error [arcmin]", labelpad = -2)
        ax2.set_ylabel("Inclination angle Error [arcmin] ",labelpad = -2)
        for f in mysettings.simulation_frequencies:
            ax1.scatter(
                [data[0] for data in fwhm_data.get_planet(p)[f]],
                [data[1] for data in fwhm_data.get_planet(p)[f]],
                s = 12
            )
            ax1.plot(
                [data[0] for data in fwhm_data.get_planet(p)[f]],
                [data[1] for data in fwhm_data.get_planet(p)[f]]
            )
            #s = UnivariateSpline(x, y, s=4)
            #sx1 = np.linspace( 0, len(fwhm_data.get_planet(p)[f]), 100)
            #sy1 = s(sx)
            #ßplt.plot(sx1, sy1)
            ax2.scatter(
                [data[0] for data in angle_data.get_planet(p)[f]],
                [data[1] for data in angle_data.get_planet(p)[f]],
                s = 12
            )
            ax2.plot(
                [data[0] for data in angle_data.get_planet(p)[f]],
                [data[1] for data in angle_data.get_planet(p)[f]],
                label = f"{f} frequency - {FREQUENCIES[f]}GHz"
            )
        plt.legend(prop={'size': 6})
        fig = plot.gcf()
            

        sim2.append_to_report(
            """
## {{planet}} plot

![]({{planet}}.png)
            """,
            figures = [
                (fig,f'{p}.png')
            ],
            planet = p.capitalize()
        )
        plot.close()
    remove_temptoml(mysettings.settings_loggerdebug)
    sim2.flush()
        

if __name__ == "__main__":
    assert len(sys.argv) == 2,f"Program requires parameter <TOML parameter_file>"
    start = time.time()
    main(str(sys.argv[1]))
    end = time.time()
    print(f"Simulation executed in {end-start} seconds.")
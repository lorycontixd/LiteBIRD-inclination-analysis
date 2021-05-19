
#  LiteBIRD's beam inclination analysis

  

This project aims to evaluate the dependance of the error of essential telescope parameters acquired through Monte Carlo simulations on the inclination of the beam function.

The telescopes mounted on LiteBIRD are far from ideal. The asymmetric structure of various lenses, together with the fact that a symmetric radiation would be obtained only from the center of the focal plane (which isn't the case for all detectors), leads to an asymmetric profile of the radiation pattern. In fact, the amount of acquired radiation follows a 3 dimensional asymmetric Gaussian. This can be observed by slicing the Gaussian at a value of z=1/2 for example, obtaining an ellipse as a cross-sectional profile.

This script aims then to visualize the impact of the angle of this asymmetry on the error of important parameters, such as the reconstruction of the FWHM, the intensity of the radiation and the angle of inclination itself.

  

##  Methodology

This code firstly cycles through all considered planets (Jupiter, Neptune & Uranus) and, for each planet, it cycles through all available frequencies on the telescope (low = 40GHz, mid = 166 GHz, high = 402GHz). For each planet and frequency, a set of angles is chosen to obtain the error on the radiation pattern and then visualized on eventual plots. Each parameter is passed on a configuration file, which should be a TOML format.

  

####  Parameters from TOML file

The parameters of the simulation are set in a TOML file, which is passed to the main script as a command-line argument. The TOML configuration file has different parameters for each section.

 - **``Simulation`` Section**:
 -- title (string): The title of the simulation
 -- description (string): The description of the simulation
 -- runs (int): Number of MonteCarlo steps for each simulation run
 -- planets (list): The planets to scan with the simulation (Jupiter, Neptune, Uranus)
 -- frequencies (list): The frequencies to scan in the simulation (Low, Mid, High)
 -- angles (list): Values for the angle of inclination of the beam function
 -- eccentricity (int): Value for the eccentricity of the beam function

- **``Simulation.info`` Section**
 -- author (string): The author of the simulation
 -- date (bool): Whether to include the date in the report or not.
 
 - **``Settings`` Section**
 -- loggerdebug (bool): Logger debug mode --> Prints out titles and console outputs
 -- datadebug (bool): Data debug mode --> Prints out important values
 -- save_error_map (bool): Save error_map pixels to file
 -- save_hitmap (bool): Save hitmap pixels to file
 -- clear_maps (bool): Clear previous maps saved 

- **``Database`` Section**
-- active (bool): Whether to store results in a SQL database
-- name (string): Database name. Ignored if active is false
 
##  Libraries

This simulation uses litebird_sim and dependants. Litebird_sim is a Python framework developed by colleagues to simulate the data acquired from LiteBIRD's telescopes during its 3-years flight around the L2 Sun-Earth Lagrangian point.

Other valuable libraries include scipy, numpy, matplotlib's pyplot and other self-developed libraries.

##  Code structure

The code is divided into a computational section and a data-elaboration section, the first one being executed inside the "compute" function and the second one in the "main" function.

The computed data is passed from one function to the other using classes inside the "models" module, where the results are stored after each simulation.

The main goal is to produce an HTML report with well-displayed data to easily spot the earlier-mentioned angle dependance, and finally to append three graphs (one per planet) with 3 scatter plots each (one per frequency). Each scatter plots contains 12 points of type (angle,radiation_error).

The reasons why this structure was chosen is firsly because of how easy it is to visualize what results are being passed to be elaborated, through the Informations model.

##  Contact

You can contact me through:

-  [My Github](https://github.com/lorycontixd)

- My university email: lorenzo.conti3@studenti.unimi.it
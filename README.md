# LiteBIRD's beam inclination analysis

This project aims to evaluate the dependance of the acquired radiation pattern's error on the LiteBIRD's beam inclination.
The telescopes mounted on LiteBIRD are far from ideal and the asymmetric structure of various lenses, together with the fact that a symmetric radiation would be obtained only from the center of the focal plane (which isn't the case for all detectors), allows the obtained radiation pattern's profile to be asymmetric.
This script aims then to visualize the impact of the angle of this asymmetry on the error of gathered radiation pattern.

## Methodology
The way I thought was best for executing what described in the above section, is to cycle through different parameters, apart from the inclination angle which is the main interest, to visualize what affects the error on received radiation the most.
This code firstly cycles through all considered planets (Jupiter, Neptune & Uranus) and, for each planet, it cycles through all available frequencies on the telescope (low = 40GHz, mid = 166 GHz, high = 402GHz). For each planet and frequency, a set of 12 angles is chosen to obtain the error on the radiation pattern and then visualized on eventual plots. 

## Libraries
This piece of code mostly uses litebird_sim and dependants. Litebird_sim is a Python framework developed by colleagues to simulate the data acquired from LiteBIRD's telescopes during its 3-years flight around the L2 Sun-Earth Lagrangian point.
Other valuable libraries include scipy, numpy, matplotlib's pyplot and other self-developed libraries.

## Code structure
The code is divided into a computational section and a data-elaboration section, the first one being executed inside the "compute" function and the second one in the "main" function.
The computed data is passed from one function to the other using classes inside the "models" module, where the results are stored after each simulation.
The main goal is to produce an HTML report with well-displayed data to easily spot the earlier-mentioned angle dependance, and finally to append three graphs (one per planet) with 3 scatter plots each (one per frequency). Each scatter plots contains 12 points of type (angle,radiation_error).

The reasons why this structure was chosen is firsly because of how easy it is to visualize what results are being passed to be elaborated, through the Informations model.

## Evaluations
Content in this section is constantly updated to keep track of current flaws and future updates.
#### Flaws
This code currently contains the following flaws:
- **Not very well optimized**
(Although the theoretical result of the code should be decently fast to run, the current code is not ideally optimized.)
- **Not enough comments**
(Readability and comprehensibility are key for a code snippet to be passed on and understanded)
- **Graphs not working**
As of now, the graphs are not right. :(

#### Next steps
These are the next steps to be taken on this piece of code:
- **Fix the graphs and the report output**
Both the content and the structure of the final report must be improved, because in the current state it is not very appealing and readable.
- **Optimize code**


## Contact 
You can contact me through:
- [My Github](https://github.com/lorycontixd)
- My university email: lorenzo.conti3@studenti.unimi.it

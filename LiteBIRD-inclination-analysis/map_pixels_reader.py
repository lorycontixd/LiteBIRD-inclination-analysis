import numpy as np
import tqdm
import argparse
from matplotlib import pyplot as plt


parser = argparse.ArgumentParser()
parser.add_argument(
    "--planet",
    nargs=1,
    default="jupiter"
)

parser.add_argument(
    "--frequency",
    nargs=1,
    default="low"
)

parser.add_argument(
    "--angle",
    nargs=1,
    default="0.0"
)
args = parser.parse_args()
freq = args.frequency
angle = args.angle

print("###########  READING FILES  ###########")
print("-- Reading gamma map file...")
#gammamap_filename = f"results/maps/{args.planet.lower()}/gammamap_{freq}_{angle}.dat"
#gamma = np.loadtxt(gammamap_filename,usecols=(0))

print("-- Reading error map file...")
errormap_filename = f"results/maps/{args.planet.lower()}/errormap_{freq}_{angle}.dat"
error = np.loadtxt(errormap_filename,usecols=(0))

print("###########  PLOTTING GRAPHS  ###########")
#print("-- Plotting gamma histogram")
#plt.hist(gamma,bins=100,range=(0,0.02))

print("-- Plotting error histogram")
plt.hist(error,bins=100,range=(0,max(error)))
print("")
print("-- Showing graphs")
plt.show()


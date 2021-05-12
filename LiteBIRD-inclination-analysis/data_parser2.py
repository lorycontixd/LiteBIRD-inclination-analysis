import database
import argparse
from matplotlib import pyplot as plt
import logging
import sys, os
from pprint import pprint
from statistics import mean
from dataclasses import dataclass

parser = argparse.ArgumentParser(
    prog="Data Analysis for LiteBIRD's inclination simulations",
    description="""The program reads data relative to MonteCarlo simulations saved in a SQL Database.
    It can produce outputs for quested observables.
    """,
    epilog= "https://github.com/lorycontixd/LiteBIRD-inclination-analysis"
)

parser.add_argument('--name',
    action='store',
    nargs=1,
    default="simulation0",
    help="Name of a specific simulation to be searched for"
)

parser.add_argument(
    '--order',
    action='store',
    nargs=1,
    default="planet",
    help = "Specific parameter to order data"
)

parser.add_argument(
    '--reverse',
    action = 'store_true',
    default=False,
    help="If true it fetches data in descending order of the parameter specified with 'order' flag, otherwise ascending"    
)

parser.add_argument(
    '--debug',
    action= 'store_true',
    default=False,
    help = "Prints out logging messages to the console"
)

parser.add_argument(
    '--select',
    action='store',
    nargs=2,
    help="Query parameters of type 'column' and 'value' for the data.\nIt will have options for multiple filters in the future."    
)

parser.add_argument(
    '--output',
    action='store',
    nargs = 1,
    default="fwhm_error",
    help="Instantly print out the queried data"
)

parser.add_argument(
    '--save',
    action="store_true",
    default=True,
    help="Save figures in a file"
)

#parser.add_argument(
#    "--columns",
#    action="store",
#    nargs="*",
#    help="Select specific columns from the database table"
#)

################### MACROS ###################

figsize = (14,6)
width = 8
xlbl = "Inclination angle"

FREQUENCIES = ["low","mid","high"]
PLANETS = ["Jupiter","Neptune","Uranus"]


################### CHECKS ###################

def check_output(output,validlist):
    if output not in validlist:
        raise ValueError(f"OUTPUT: Cannot show output graph for data {o}")
    #if "*" in outputlist and len(outputlist)>1:
    #p    raise ValueError("OUTPUT: * output value must be passed alone")

def check_order_key(key,validlist):
    if key not in validlist:
        raise ValueError(f"Invalid order key {key}")

##############################################

angles = [0,10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180]
def extract_data(data):
    @dataclass
    class InfoClass():
        data = {
            "Jupiter" : {
                "low" : [],
                "mid" : [],
                "high" : []
            },
            "Neptune" : {
                "low" : [],
                "mid" : [],
                "high" : []
            },
            "Uranus" : {
                "low" : [],
                "mid" : [],
                "high" : []
            }
        }
    info = InfoClass()

    i=0
    for d in data:
        info.data[ d[0] ][ d[1] ].append((d[3],d[4],d[5]))
    return info

def check_select(sel):
    if sel is not None:
        if sel[0] not in ["planet","frequency"]:
            raise ValueError(f"Invalid select key {sel[0]}.\nMust be planet or frequency.")


################### GET DATA ###################

args = parser.parse_args()
VALID_FILTERS = ["planet","frequency","angle","angle_error","ampl_error","fwhm_error"]
DATA_FILTERS = ["angle_error","ampl_error","fwhm_error"]
DATA_COLS_PRESENT = []

check_order_key(args.order,VALID_FILTERS)
check_output(args.output,DATA_FILTERS+["*"])
check_select(args.select)

if args.reverse:
    order_type = "DESC"
else:
    order_type = "ASC"
figs = []
if args.debug:
    print(f"------ LiteBIRD inclination Data Analyzing script ------")
    print(args)

dbname = "db/final_simulations"
mydb = database.SimulationDatabase(database_name=dbname,main_table=args.name[0])

if args.select is None:
    data = mydb.order(column=args.order,order_type=order_type)
else:
    data = mydb.query_run(filter=(args.select[0],args.select[1]))

#data is a list of tuples
if args.debug:pprint(data)

#!!!! FOR NOW ONLY WORK ON FWHM ERROR, EXTEND SCRIPT LATER
# this means:
# - output will have to be only bool for now

indices = {
    "inclination_error" : 0,
    "ampl_error" : 1,
    "fwhm_error" : 2
}

################### GRAPHS ###################

if not args.select:
    fig,ax = plt.subplots(1,3,figsize=figsize)
    for i,p in enumerate(PLANETS):
        for f in FREQUENCIES:
            if f == "low":
                zorder = 2
                color = "cyan"
            elif f == "mid":
                zorder = 10
                color = "magenta"
            elif f == "high":
                zorder = 5
                color = "red"
            else:
                raise ValueError("Invalid frequency key for zorder")
            y = [i[indices[args.output]] for i in extract_data(data).data[p][f]]
            ax[i].set_title(p)
            ax[i].set_xlabel(xlbl)
            ax[i].set_ylabel(args.output)
            ax[i].bar(angles,y,width=width,label=f,zorder=zorder)
            ymean = float("{:.2f}".format(mean(y)))
            ax[i].plot(angles,[mean(y) for i in y],color=color,zorder=20,label=f"mean {f}= {ymean}")
            ax[i].legend()
    plt.suptitle(f"{args.name[0]} - FWHM Error for all frequencies")

elif args.select[0] == "frequency":
    fig,ax = plt.subplots(1,3,figsize=figsize)

    for i,p in enumerate(PLANETS):
        ydata = [i[indices[args.output]] for i in extract_data(data).data[p][args.select[1]]]
        ax[i].set_title(p)
        ax[i].set_xlabel(xlbl)
        ax[i].set_ylabel(args.output)
        ax[i].bar(angles,ydata,width=width,label="Data")
        ymean = float("{:.2f}".format(mean(ydata)))
        ax[i].plot(angles,[mean(ydata) for i in ydata],color="orange",linewidth=3,label=f"Mean: {ymean}")
        ax[i].legend()

        plt.suptitle(f"{args.name[0]} - FWHM Error for frequency: {args.select[1]}")

#if args.selected[0] == "planet":
    
    
plt.show()




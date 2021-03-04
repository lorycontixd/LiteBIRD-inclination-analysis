#Module for reading data from local MySQL database with different options
import database
import argparse
from matplotlib import pyplot as plt
import logging
import sys
import os
from matplotlib import pyplot


def save_report(simulation,data,debug):
    if not isinstance(simulation,str):
        raise TypeError(f"Simulation name must be a string, not {type(simulation)}")
    if not isinstance(data,tuple):
        raise TypeError(f"Data must be a tuple, not {type(data)}")
    if not isinstance(debug,bool):
        raise TypeError(f"Debug setting must be a bool, not {type(debug)}")

    working_path = os.path.join(os.getcwd(),'results','analysis',simulation)
    if not os.path.exists(working_path):
        try:
            os.mkdir(working_path)
        except OSError:
            print ("Creation of the directory %s failed" % working_path)
    
    csv_file = open(working_path,'w+')
    for d in data:
        csv_file.write(d)
    



parser = argparse.ArgumentParser(
    prog = "Data analyzer",
    description='Process input settings for data analysis.',
    epilog= "https://github.com/lorycontixd/LiteBIRD-inclination-analysis"
)

parser.add_argument('--name',action='store',nargs=1)
parser.add_argument('--order',action='store',nargs=1)
parser.add_argument('--reverse',action = 'store_true')
parser.add_argument('--debug',action= 'store_true')
args = parser.parse_args()
if hasattr(args,'name') and args.name is not None:
    print(args.name)
    table = str(args.name[0])
else:
    table = "simulation1"
order_filter = args.order[0]
reverse = bool(args.reverse)
debug = bool(args.debug)

if debug:
    print(f'''Initial arguments:\n- Order: {order_filter}\n- Reverse: {reverse}\n- Debug: {debug}\n ''')

VALID_FILTERS = ["planet","frequency","angle","angle_error","fwhm_error"]
if str(order_filter) not in VALID_FILTERS:
    raise ValueError(f"Invalid filter error {order_filter}. Valid filters: {str(VALID_FILTERS)}")

mydatabase = database.SimulationDatabase(name=table)
_type = "ASC"
if reverse:
    _type = "DESC"
data = mydatabase.order(column=order_filter,order_type=_type)
print("data", "  ",data)

_planets = [item[0] for item in data]
_frequencies = [item[1] for item in data]
_angle = [item[2] for item in data]
_angle_error = [item[3] for item in data]
_ampl_error = [item[4] for item in data]
_fwhm_error= [item[5] for item in data]

if debug:
    print("Opening Plotly table..")



#fig.show()
#plt.show()
fig.write_image(f"./results/tables/{mydatabase.name}.png")
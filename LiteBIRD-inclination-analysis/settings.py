#Read simulation settings from parameter.toml
import toml
import pprint
import pandas as pd


def extract_nested_values(it):
    if isinstance(it, list):
        for sub_it in it:
            yield from extract_nested_values(sub_it)
    elif isinstance(it, dict):
        for value in it.values():
            yield from extract_nested_values(value)
    else:
        yield it

def normalize(mydict):
    df = pd.json_normalize(mydict, sep='_')
    return df.to_dict(orient='records')[0]


class Settings():
    """
    """

    def __init__(self,filename):
        super().__init__()
        self.filename = filename
        self.__validate_filename(self.filename)
        self.__settings = self.__read_file(self.filename)
        self.__normalized_dict = normalize(self.__settings)
        for item in self.__normalized_dict:
            setattr(self,item,self.__normalized_dict[item])
        self.__validate_inputs()
        
    def __repr__(self):
        info = """
The Settings class represents the parameters used for this simulation.
This message is visible because debug = True, you can disable it in your parameter file or from this class.

Current simulation settings:
"""
        for key in self.__normalized_dict:
            info+=f"- {key}: {self.__normalized_dict[key]} \n"
        return info

    def __validate_inputs(self):
        if "simulation_planets" not in self.__dict__:
            raise ValueError("Planets must be passed in parameters under simulation section.")
        if "simulation_frequencies" not in self.__dict__:
            raise ValueError("Frequnecies must be passed in parameters under simulation section.")
        if "simulation_angles" not in self.__dict__:
            raise ValueError("Angles must be passed in parameters under simulation section.")

    def __validate_filename(self,filename):
        if not isinstance(filename,str):
            raise TypeError("Settings argument must be <filename> of type str.")
        if not self.filename.endswith(".toml"):
            raise TypeError("Paramenter filename must be a TOML file.")

    def __validate_args(self,*args):
        pass

    def __validate_kwargs(self,**kwargs):
        pass

    def __read_file(self,filename):
        try:
            content = open(filename,"r+").read()
            mydict = toml.loads(content)
            return mydict
        except FileNotFoundError as e:
            print(f"File {filename} does not exist or is not found.")

    def get_first_setting(self,key):
        for k in self.__normalized_dict.keys():
            if key in k:
                return (k,self.normalized_dict[k])

    def get_named_settings(self,key):
        results = []
        for k in self.__normalized_dict.keys():
            if key in k:
                results.append((k,self.__normalized_dict[k]))
        return results
    
    def get_all_settings(self):
        return self.__normalized_dict

if __name__ == "__main__":
    s = Settings("parameters.toml")
    print(s)
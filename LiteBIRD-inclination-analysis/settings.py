#Read simulation settings from parameter.toml
import toml

class Settings():
    """
    Class for simulation settings.

    If filename is passed, it imports settings from file [from TOML]
    If filename is not passed, settings can be changed from script
    """
    def __init__(self,filename=None):
        self.filename = filename
        self.__settings = {}
    
    def parse_file(self):
        if self.filename is not None:
            self.__settings = toml.loads(self.filename)
        else:
            raise TypeError("Cannot parse null settings file.")
        
        print(self.__settings)


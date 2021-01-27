from datetime import datetime
import pytz

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'



class Logger():
    def __init__(self,**kwargs):
        """
        Timezone (str): the timezone you are in\n
        Default level (str): the default level of logging\n
        Colors (bool): if colors inside messages\n
        """
        self.accepted = ["timezone", "default_level", "colors"]
        for kw in kwargs:
            assert kw in self.accepted,f"Invalid kwarg passed {kw}. Allowed kwargs are <timezone>, <default_level> and <colors>"

        for a in self.accepted:
            if a in kwargs:
                setattr(self,kw,kwargs[kw])
            else:
                if a == "default_level":
                    setattr(self, a, "info")
                elif a == "colors":
                    setattr(self, a, True)
                elif a == "timezone":
                    setattr(self,a,"Europe/Rome")
                else:
                    setattr(self, a, None)
        self.c = Colors()
        self.levels = {
            "info" : self.c.OKBLUE,
            "header" : self.c.HEADER,
            "fail" : self.c.FAIL,
            "fatal" : self.c.BOLD +  self.c.FAIL,
            "warning" : self.c.WARNING,
            "success" : self.c.OKGREEN
        }
        self.tz = pytz.timezone(self.timezone)
    
    def __repr__(self):
        string = f"""Logger information:
- Timezone (str): {self.timezone}
- Default level (str): {self.default_level}
- Allow colors (bool): {self.colors}
"""
    def log_print(self,message,level=None):
        if level is None:
            level = self.default_level
        string = f"[{datetime.now(tz=self.tz).strftime('%d/%m/%Y, %H:%M:%S')}] - [{self.levels[level]}{level.upper()}{self.c.ENDC}] - {message}"
        print(string)
    
    def info(self,message):
        self.log_print(message, "info")

    def header(self,message):
        self.log_print(message, "header")

    def warn(self,message):
        self.log_print(message,"warning")
    
    def fail(self,message):
        self.log_print(message, "fail")
    
    def fatal(self,message):
        self.log_print(message, "fatal")
    
    def success(self,message):
        self.log_print(message, "success")

    def change_attr(self,attribute,value):
        assert attribute in self.accepted,f"Invalid attribute {attribute}. Allowed attributes are {str(self.accepted)}"
        setattr(self,attribute,value)
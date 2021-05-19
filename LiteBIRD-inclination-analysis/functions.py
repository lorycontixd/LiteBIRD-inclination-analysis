import sys,os
import time, timeit
import litebird_sim

class Decorators():
    @staticmethod
    def timer(function):
        def new_function():
            start_time = timeit.default_timer()
            function()
            elapsed = timeit.default_timer() - start_time
            print('Function "{name}" took {time} seconds to complete.'.format(name=function.__name__, time=elapsed))
        return new_function()

class Functions():
    pass

class Parsers():
    pass

class OSFunctions(Functions):
    pass

class SimulationFunctions():
    pass


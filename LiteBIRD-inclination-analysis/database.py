import sqlite3
import sys
import models

class Parser():
    def __init__(self):
        pass
    
    def _check_dict(self,mydict):
        if not isinstance(mydict,dict):
            return TypeError(f"Invalid type for sql_statement {type(mydict)} --> it must be a dict")

    def create_table(self,mydict):
        self._check_dict(mydict)
        sql_params = ""
        i = 0
        for col in mydict:
            if not isinstance(mydict[col],tuple):
                raise TypeError(f"Invalid type for sql_parameters {type(mydict[col])} --> it must be a tuple")
            sql_line = f"{col} "
            for param in mydict[col]:
                sql_line += param+" "
            if i!=len(mydict.keys())-1:
                sql_line += ","
            sql_params += sql_line
            i+=1
        return sql_params
    
    def insert_to_table(self,list):
        cols = tuple([item[0] for item in list])
        values = tuple([item[1] for item in list])
        sql_params = f"{str(cols)} VALUES {str(values)}"
        return sql_params
    
    def query_columns(self,columns:list):
        cols = ""
        i = 0
        for c in columns:
            cols += str(c)
            if i != len(columns)-1:
                cols +=","
        return cols


class Database():
    """
    Class for storing simulation results in a sqlite3 database
    (sqlite3 over mongo)
    """

    def __init__(self,name=None,max_tables = 10):
        if name is None:
            raise ValueError("Database name must not be None")
        self.name = name.lower()
        self.max_tables = max_tables
        self.conn = None
        self.c = None
        self._connect(self.name)
        self.parser = Parser()

    def _connect(self,db):
        if self.conn is None:
            self.conn = sqlite3.connect(f'{db}.db')
            self.c = self.conn.cursor()
    
    def _disconnect(self):
        self.conn.close()
    
    def _list_tables(self):
        self.c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables=(self.c.fetchall())
        return tables

    def create_table(self,name,columns):
        params = self.parser.create_table(columns)        
        command = f'''CREATE TABLE IF NOT EXISTS {name} ({params})'''
        self.c.execute(command)
        self.conn.commit()
        print(f"SQL: Created table with name {name} and {len(columns)} columns")

    def insert_to_table(self,table_name:str,params_list:list):
        #params list is a list of tuples --> (column,value)
        params = self.parser.insert_to_table(params_list)
        command = f'''INSERT INTO {table_name}{params};'''
        print(command)
        self.c.execute(command)
        self.conn.commit()
        print(f"SQL: Inserted row in table {table_name}")

    def query_data(self,table_name=None,columns=[],filter=()):
        if table_name is None:
            raise ValueError("Table name must not be none for db.query_data")
        column_string = ""
        if not columns:
            column_string = "*"
        else:
            column_string = self.parser.query_columns(columns)
        command = f'''SELECT {column_string} FROM {table_name}'''
        if filter:
            command = f"SELECT {column_string} FROM {table_name} WHERE {filter[0]}='{filter[1]}'"
        print(command)
        data = self.c.execute(command)
        rows = self.c.fetchall()
        return rows

class SimulationDatabase(Database):
    def __init__(self,name = None):
        super().__init__("simulations")
        if name is None:
            self.name = "simulation"+str(len(self._list_tables()))
        else:
            self.name = name
            if self.name not in [item[0] for item in self._list_tables()]:
                print(self.name,"  ",self._list_tables())
                print(f"Table {self.name} not found in the database. Setting to simulation{len(self._list_tables())-1}")
                self.name = "simulation"+str(len(self._list_tables())-1)
        self.keys = ["planet","frequency","inclination","angle_error","ampl_error","fwhm_error"]
    
    def create_simulation(self):
        cols = {
            "planet" : ("VARCHAR(255)","NOT NULL"),
            "frequency" : ("VARCHAR(255)","NOT NULL"),
            "inclination" : ("FLOAT","NOT NULL"),
            "angle_error" : ("FLOAT","NOT NULL"),
            "ampl_error" : ("FLOAT","NOT NULL"),
            "fwhm_error" : ("FLOAT","NOT NULL")
        }
        self.create_table(self.name,cols)
    
    def insert_run(self,info:models.Information,table_name=None):
        params = []
        for k in self.keys:
            if k != "planet":
                params.append( (k,info[k]) )
            else:
                params.append( (k,info[k].name) )
        if table_name is None:
            self.insert_to_table(self.name,params)
        else:
            self.insert_to_table(table_name,params)

    def query_all_runs(self,name=None):
        if name is None:
            data = self.query_data(self.name)
        else:
            data = self.query_data(name)
        return data

    def query_run(self,columns=[],filter=()):
        data = self.query_data(self.name,columns,filter)
        return data
    
    def order(self,column="planet",order_type="ASC"):
        if not isinstance(column,str):
            raise TypeError("Order key must be a string")
        if not isinstance(self.name,str):
            raise TypeError("Table name must be a string")
        if not isinstance(order_type,str):
            raise TypeError("Order type must be a string")
        order_type = order_type.upper()
        if order_type not in ["ASC","DESC"]:
            raise ValueError(f"Invalid order type {str(order_type)}. Must be ASC or DESC")

        sql_statement = f'''SELECT * FROM {self.name} ORDER BY {column} {order_type}'''
        data = self.c.execute(sql_statement)
        rows = self.c.fetchall()
        return rows
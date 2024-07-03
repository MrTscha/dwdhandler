# -*- coding: utf-8 -*-
"""
Created on Mon Jul 01 16:01:28 2024

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: Simple Postgres handling
"""

# import libraries
from dotenv import dotenv_values
from pathlib import Path
from configparser import ConfigParser
import psycopg2
from sqlalchemy import create_engine

necessary_config_keys = ['host', 'database', 'user', 'password', 'port']

class PostgresHandler():
    def __init__(self, dbschema, config=None, file_location=".env"):
        """
            Class which handles postgres connection
            config (Dict): Contains essential authorization credentials
            file_location (string): Contains name of configuration file, Default ".env"
                        If no config dict is given it is assumed that credentials are 
                        given in the configuration file
                        it is also possible to provide an .ini file, which is then parsed
                        by configparser (the .ini file must contain section postgresql)
                        necessary information is
                        host=
                        database=
                        user=
                        password=
        """

        self.dbschema = dbschema

        if(config is None):
            if(Path(file_location).suffix == ".ini" ):
                self.config = load_config(filename=file_location)
            else:
                self.config = dotenv_values(file_location)
        else:
            self.config = config

    def connect(self):
        """
            Connect to the PostgreSQL database
        """

        if(self.config is None):
            print("No Configuration loaded, return without connecting")
            return
        
        # check for keys
        if(not check_config_completeness(self.config)):
            return

        try:
            # connecting to PostgreSQL Server

            #with psycopg2.connect(**self.config) as con:
            #    print(f"Connection to {self.config['host']} established.")
            #    self.con = con

            connect_str = f"postgresql+psycopg2://{self.config['user']}:{self.config['password']}@{self.config['host']}:{self.config['port']}/{self.config['database']}"
            self.engine = create_engine(
                connect_str,
                connect_args={'options': '-csearch_path={}'.format(self.dbschema)}
            )

        #except (psycopg2.DatabaseError, Exception) as error:
        except ( Exception) as error:
            print(error)

    def close(self):
        """
            closes connection
        """

        try:
            self.engine.dispose()
        except Exception as error:
            print(error)
            print("Was connection established?")
            

def check_config_completeness(config):
    """
        checks config file
    """

    lall = all(key in config for key in necessary_config_keys)

    if(lall):
        return lall
    else:
        print(set(necessary_config_keys).difference(set(config)))
        print("are not in configuration file")
        return False


def load_config(filename='database.ini', section='postgresql'):
    """
        parses .ini file to load credentials
        filename (string): Name of the .ini file, default "database.ini"
        section (string): Name of the section to read, default "postgresql"
    """

    # Init parser
    parser = ConfigParser()
    parser.optionxform=str

    if(not Path(filename).exists):
        raise Exception(f"File {filename} does not exists!")
        return config

    # Read file
    parser.read(filename)

    # Get section entries
    config = {}

    # Parse section
    if(parser.has_section(section)):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception(f'Section [{section}] not found in {filename}')
    
    return config
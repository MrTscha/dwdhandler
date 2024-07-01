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

class PostgresHandler():
    def __init__(self, config=None, file_location=".env"):
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

        if(config is None):
            if(Path(file_location).suffix == ".ini" ):
                self.config = load_config(filename=file_location)
            else:
                self.config = dotenv_values(file_location)
        else:
            self.config = config

def load_config(filename='database.ini', section='postgresql'):
    """
        parses .ini file to load credentials
        filename (string): Name of the .ini file, default "database.ini"
        section (string): Name of the section to read, default "postgresql"
    """

    # Init parser
    parser = ConfigParser()
    parser.read_file(filename)

    # Get section entries
    config = {}

    if(not Path(filename).exists):
        raise Exception(f"File {filename} does not exists!")
        return config

    if(parser.has_section(section)):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception(f'Section [{section}] not found in {filename}')
    
    return config
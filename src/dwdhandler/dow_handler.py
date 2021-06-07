# -*- coding: utf-8 -*-
"""
Created on Thu Jun 08 17:45:40 2020

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: This module mainly handles downloading data from 
              DWD opendata homepage
"""

#import system modules
from sys import exit, stdout
import os
import pandas as pd

# local modules
from .constants.serverdata import SERVERPATH_CLIMATE_GERM, SERVERNAME
from .constants.filedata import (MAIN_FOLDER, TIME_RESOLUTION_MAP, 
                                METADATA_FOLDER, NAME_CONVERSATION_MAP)
from .helper.hfunctions import check_create_dir
from .helper.ftp import cftp

class dow_handler(dict):
    def __init__(self, 
                 dtype='station',
                 par='air_temperature',
                 resolution='hourly',
                 base_dir=MAIN_FOLDER,
                 period='recent',
                 local_time = False,
                 date_check = None,
                 debug = False
                ):
        """
        This class handles the download of data originating from opendata.dwd.de
        dtype: specify type of data --> station:Station Data, raster: Raster Data, nwp: Numerical Forecast
        period: Define period --> historical, recent, now 
        local_time: translate to local time if wanted, otherwise time is in UTC
        date_check: check list of station data has to be data to this given date, if not specified today is used
        """

        # store data
        self.dtype  = dtype
        self.par    = par
        self.period = period
        self.debug  = False
        self.local_time = local_time
        self.date_check = date_check
        self.resolution = resolution
        self.base_dir   = base_dir
        # store "Home" Directory
        self.home_dir   = os.getcwd() 

        self.prepare_download()

    def prepare_download(self):
        """ Prepare download data 
        """

        check_create_dir(self.base_dir)

        self.check_parameters()
        
        self.get_metadata()

    def check_parameters(self):
        """ Check if parameter combination is available
        """

        #check = TIME_RESOLUTION_MAP.get(self.resolution, ([], []))
        check = TIME_RESOLUTION_MAP[self.resolution]

        if(self.par not in check[0] or self.period not in check[1]):
            raise NameError(
                f"Wrong combination of resolution={self.resolution},par={self.par}"
                f"and period={self.period}."
                f"Please check again:"
                f"{TIME_RESOLUTION_MAP}" ### !!! >>TS TODO introduce better print function !!! <<TS###
            )

    def get_metadata(self):
        """ Gets Metadata of data """

        if(self.dtype == 'station'):
            self.get_station_metadata()
        elif(self.dtype == 'raster'):
            self.get_raster_metadata()
    
    def get_station_metadata(self):
        """ Get Station Metadata
        """

        # create local location to save data description
        pathlocal  = self.base_dir+METADATA_FOLDER+f'{self.resolution}_{self.par}/'
        # create path on remote server
        pathremote = SERVERPATH_CLIMATE_GERM+f'{self.resolution}/{self.par}/{self.period}/'
        # create meta data filename 
        filename = self.create_metaname()
        print(pathlocal)
        print(pathremote)
        print(pathremote+filename)

        # check if dir already exists
        check_create_dir(pathlocal)

        # Try to download Metadatafile
        metaftp = cftp(SERVERNAME)
        metaftp.open_ftp()
        metaftp.cwd_ftp(pathremote)
        os.chdir(pathlocal)

        if(self.debug):
            print(f"Retrieve {pathremote+filename}")

        metaftp.save_file(filename,filename)
        
        metaftp.close_ftp()

        os.chdir(self.home_dir)

        print("Station Metadata not yet fully implemented")

    def create_metaname(self):

        return f'{NAME_CONVERSATION_MAP[self.par]}_{NAME_CONVERSATION_MAP[self.resolution+f"_meta"]}{NAME_CONVERSATION_MAP["meta_file_stationen"]}'

    def get_raster_metadata(self):
        """ Get Raster Data Metadata
        """

        print("Raster Metadata not yet implemented")

    def get_obj_station(self,key,obj='name'):
        """ Get Metadata of Station Metadatafile """

        if(obj in ['von','bis']):
            return pd.to_datetime(self.df_station_list[self.df_station_list.index == key][obj].values[0])
        else:
            return self.df_station_list[self.df_station_list.index == key][obj].values[0]
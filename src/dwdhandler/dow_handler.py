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

# local modules
from .constants.serverdata import SERVERPATH_CLIMATE_GERM
from .constants.filedata import MAIN_FOLDER, TIME_RESOLUTION_MAP, METADATA_FOLDER
from .helper.hfunctions import check_create_dir

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
        filelocal  = '{self.par}_metadata_{self.period}.txt'
        # create path on remote server
        pathremote = SERVERPATH_CLIMATE_GERM+f'{self.resolution}/{self.par}/{self.period}/'
        print(pathlocal)
        print(pathremote)
        check_create_dir(pathlocal)
        print("Station Metadata not yet fully implemented")

    def get_raster_metadata(self):
        """ Get Raster Data Metadata
        """

        print("Raster Metadata not yet implemented")


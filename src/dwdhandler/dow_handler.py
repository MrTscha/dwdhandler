# -*- coding: utf-8 -*-
"""
Created on Thu Jun 08 17:45:40 2020

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: This module mainly handles downloading data from
              DWD opendata homepage
"""

#import system modules
from sys import exit, float_repr_style, stdout
import os
import pandas as pd
import datetime
import shutil
import sqlite3
import numpy as np

# local modules
from .constants.serverdata import SERVERPATH_CLIMATE_GERM, SERVERNAME, SERVERPATH_RASTER_GERM
from .constants.filedata import *
from .constants.constpar import FILLVALUE
from .helper.hfunctions import check_create_dir, list_files, read_station_list, unzip_file, update_progress
from .helper.ftp import cftp

class dow_handler(dict):
    def __init__(self,
                 dtype='station',
                 par='air_temperature' ,
                 resolution='hourly',
                 base_dir=os.getcwd()+'/'+MAIN_FOLDER,
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
        
        dtype raster has to be set with period recent! 
        """

        # store data
        self.dtype  = dtype
        self.par    = par
        self.period = period
        self.debug  = debug
        self.local_time = local_time
        self.date_check = date_check
        self.resolution = resolution
        self.base_dir   = base_dir
        # store "Home" Directory
        self.home_dir   = os.getcwd()  ### TODO: Das geht hier vlt nicht so einfach... beißt sich mit base_dir und dem wechseln in die Verzeichnisse
        self.tmp_dir    = 'tmp{}/'.format(datetime.datetime.now().strftime('%s'))

        self.prepare_download()

    def prepare_download(self):
        """ Prepare download data 
        """

        check_create_dir(self.base_dir)

        self.check_parameters()

        self.create_dirs()
        
        self.get_metadata()

    def check_parameters(self):
        """ Check if parameter combination is available
        """

        #check = TIME_RESOLUTION_MAP.get(self.resolution, ([], []))
        if(self.dtype == 'station'):
            time_check_map = TIME_RESOLUTION_MAP
        elif(self.dtype == 'raster'):
            time_check_map = TIME_RASTER_MAP

        check = time_check_map[self.resolution]

        if(self.par not in check[0] or self.period not in check[1]):
            raise NameError(
                f"Wrong combination of resolution={self.resolution}, par={self.par} "
                f"and period={self.period}.\n"
                f"Please check again:\n"
                f"{time_check_map}" ### !!! >>TS TODO introduce better print function !!! <<TS###
            )

    def create_dirs(self):
        """
        Create directories
        """

        if(self.dtype == 'station'):
            # create local location to save data description
            self.pathmlocal = self.base_dir+METADATA_FOLDER+f'{self.resolution}_{self.par}/'
            # create path on remote server of metadata and data
            self.pathremote = SERVERPATH_CLIMATE_GERM+f'{self.resolution}/{self.par}/{self.period}/'
            # create local data to save data
            self.pathdlocal = self.base_dir+STATION_FOLDER
            # create temp directory to avoid clashes of data streams
            self.pathdlocaltmp = self.base_dir+self.tmp_dir
        elif(self.dtype == 'raster'):
            # create local location to save data description
            self.pathmlocal = self.base_dir+METADATA_FOLDER+f'raster_{self.resolution}_{self.par}/'
            # create path on remote server of metadata and data
            self.pathremote = SERVERPATH_RASTER_GERM+f'{self.resolution}/{self.par}/'
            # create local data to save data
            self.pathdlocal = self.base_dir+RASTER_FOLDER+f'{self.par}/'
            # create temp directory to avoid clashes of data streams
            self.pathdlocaltmp = self.base_dir+self.tmp_dir

    def get_metadata(self):
        """ Gets Metadata of data """

        if(self.dtype == 'station'):
            self.get_station_metadata()
        elif(self.dtype == 'raster'):
            self.get_raster_metadata()
    
    def get_station_metadata(self):
        """ Get Station Metadata
        """

        # create meta data filename 
        filename = self.create_station_metaname()

        # check if dir already exists
        check_create_dir(self.pathmlocal)
        # Try to download Metadatafile
        metaftp = cftp(SERVERNAME)
        metaftp.open_ftp()
        metaftp.cwd_ftp(self.pathremote)
        os.chdir(self.pathmlocal)

        if(self.debug):
            print(f"Retrieve {self.pathremote+filename}")

        metaftp.save_file(filename,filename)
        
        metaftp.close_ftp()

        os.chdir(self.home_dir)

        self.df_station_list = read_station_list(self.pathmlocal,filename)

    def create_station_metaname(self):

        return f'{NAME_CONVERSATION_MAP[self.par]}_{NAME_CONVERSATION_MAP[self.resolution+f"_meta"]}{NAME_CONVERSATION_MAP["meta_file_stationen"]}'

    def create_raster_metaname(self):
        return f'DESCRIPTION_gridsgermany_{self.resolution}_{self.par}_en.pdf'

    def create_station_filename(self,key):
        """ Creates file location on ftp """

        if(self.period == 'recent'):
            return f'{NAME_CONVERSATION_MAP[self.resolution]}_{NAME_CONVERSATION_MAP[self.par]}_{key}_{NAME_CONVERSATION_MAP[self.period]}.zip'
        elif(self.period == 'now'):
            return f'{NAME_CONVERSATION_MAP[self.resolution]}_{NAME_CONVERSATION_MAP[self.par]}_{key}_{NAME_CONVERSATION_MAP[self.period]}.zip'
        else:
            cvon = self.get_obj_station(key,obj='von').strftime('%Y%m%d')
            tbis = self.get_obj_station(key,obj='bis')
            if(tbis.year == datetime.datetime.now().year):
                cbis = '{}1231'.format(tbis.year-1)
            else:
                cbis = self.get_obj_station(key,obj='bis').strftime('%Y%m%d')
            return f'{NAME_CONVERSATION_MAP[self.resolution]}_{NAME_CONVERSATION_MAP[self.par]}_{key}_{cvon}_{cbis}_{NAME_CONVERSATION_MAP[self.period]}.zip'

    def create_raster_filename(self,year,month):
        """ Creates file location on ftp for raster data """

        if(self.par in RASTERNCDICT):
            fil_ending = 'nc'
        else:
            fil_ending = 'asc.gz'

        if(self.par in RASTERMONTHSUB):
            return f'{RASTERMONTHDICT[month-1]}/grids_germany_{self.resolution}_{RASTER_CONVERSATION_MAP[self.par]}_{year}{month:02d}.asc.gz'
        else:
            return f'{self.par}'

    def get_raster_metadata(self):
        """ Get Raster Data Metadata
        """

        print("Raster Metadata not yet implemented")
    
    def retrieve_dwd_raster(self,year,month,to_netcdf=False):
        """ Retrieves DWD Raster data
            year:  can be a single year or a list with starting year and end year;
                   [2000,2010] means download data from 2000 to 2010
            month: can be a single month or a list with starting month and end month
                   [1,4] means download data from January to February
            to_netcdf: True/False; True save data to a netCDF File -- Not Yet implemented!! --
        """

        if(isinstance(year, list)):
            if(self.debug):
                print(f'Retrieve year {year[0]} - {year[1]}')
            year_arange = np.arange(year[0],year[1]+1)
        else:
            if(self.debug):
                print(f"Retrieve year {year}")
            year_arange = np.array([year])

        if(isinstance(month, list)):
            if(self.debug):
                print(f'and month {month[0]} - {month[1]}')
            month_arange = np.arange(month[0],month[1]+1)
        else:
            if(self.debug):
                print(f"and month {month}")
            month_arange = np.array([month])
        
        # Are the pathes there
        check_create_dir(self.pathdlocal)
        os.chdir(self.pathdlocal)

        if(to_netcdf):
            check_create_dir(self.pathdlocaltmp)
            os.chdir(self.pathdlocaltmp)

        metaftp = cftp(SERVERNAME)
        metaftp.open_ftp()
        metaftp.cwd_ftp(self.pathremote)

        ii = 0
        i_tot = len(year_arange)*len(month_arange)
        not_in_list = []

        for tyear in year_arange:
            for tmonth in month_arange:
                update_progress(ii/i_tot)
                ii = ii + 1
                filename = self.create_raster_filename(tyear,tmonth)
                print(filename)

                if(self.debug):
                    print(f"Retrieve: {self.pathremote+filename}")

                try:
                    if(self.par in RASTERMONTHSUB):
                        metaftp.save_file(filename,filename[7:])
                    else:
                        metaftp.save_file(filename,filename)
                except:
                    print(f"{self.pathremote+filename} not found")
                    not_in_list.append(self.pathremote+filename)
                try:
                    if(self.par in RASTERMONTHSUB):
                        os.system('gunzip -f '+filename[7:])
                    elif(self.par not in RASTERNCDICT): ### Files with nc ending are not needed to unzip
                        os.system('gunzip -f '+filename)
                except:
                    print(f'{filename} could not gunziped --> Is gunzip installed on local machine?')
                    print('Python intern gunzip not yet implemented!')

        # attach all files which are not found
        self.stations_not_found = not_in_list

        metaftp.close_ftp()

        os.chdir(self.home_dir)

        os.chdir(self.home_dir)

        if(to_netcdf):
            try:
                shutil.rmtree(self.pathdlocaltmp)
            except OSError as e:
                print(f"Error: {self.pathdlocaltmp} : {e.strerror}")


    def retrieve_dwd_station(self,key_arr,to_sqlite=True):
        """ Retrieves DWD Station data 
            key_arr:   IDs of stations to retrieve, 1D-Array
            to_sqlite: Saves data within SQLITE databank
        """

        # test types of input parameters
        assert isinstance(key_arr, list)

        check_create_dir(self.pathdlocal)
        check_create_dir(self.pathdlocaltmp)

        os.chdir(self.pathdlocaltmp)

        metaftp = cftp(SERVERNAME)
        metaftp.open_ftp()
        metaftp.cwd_ftp(self.pathremote)

        ii = 0
        i_tot = float(len(key_arr))
        not_in_list = []

        for key in key_arr:
            update_progress(ii/i_tot)
            ii = ii + 1
            filename = self.create_station_filename(key)
            check_create_dir(key)
            os.chdir(key)
            if(self.debug):
                print(f"Retrieve: {self.pathremote+filename}")

            try:
                metaftp.save_file(filename,filename)
                unzip_file(filename)
                df_tmp = self.get_station_df_csv(os.getcwd())
                self.to_sqlite(df_tmp, key) ## TODO, what if sqlite is not used?
            except:
                print(f"{self.pathremote+filename} not found")
                not_in_list.append(self.pathremote+filename)
            os.chdir('../')

        self.stations_not_found = not_in_list

        metaftp.close_ftp()

        os.chdir(self.home_dir)

        try:
            shutil.rmtree(self.pathdlocaltmp)
        except OSError as e:
            print(f"Error: {self.pathdlocaltmp} : {e.strerror}")

    def get_dwd_station_data(self,key,mask_FillVal=True):
        """ Get Data from sqlite database """

        filename = 'file:{}?cache=shared'.format(self.pathdlocal+SQLITEFILESTAT)

        con = sqlite3.connect(filename,uri=True)

        tabname = f"{self.par}_{self.resolution}"

        sqlexec = "SELECT * from {} WHERE STATIONS_ID = {}".format(tabname,key)

        if(self.debug):
            print("Get SQLITE data:")
            print(sqlexec)

        df_data = pd.read_sql_query(sqlexec, con)

        con.close()

        if(self.resolution == 'hourly'):
            strformat='%Y%m%d%H'
        elif(self.resolution == 'daily'):
            strformat='%Y%m%d'
        elif(self.resolution == 'monthly'):
            strformat='%Y%m'
        elif(self.resolution == 'yearly'):
            strformat='%Y'

        df_data.index = pd.to_datetime(df_data['MESS_DATUM'],format=strformat) ## TODO MESS_DATUM durch generisches filedata austauschen
        df_data.drop(columns=['MESS_DATUM'],inplace=True)

        columns = df_data.columns
        replace_col = {}
        for column in columns:
            replace_col[column] = column.replace(' ','')

        df_data.rename(columns=replace_col,inplace=True)

        if(mask_FillVal):
            df_data.mask(df_data == FILLVALUE,inplace=True)

        return df_data

    def get_data(self,sqlexec,mask_fillVal=True):
        """ Get data according to sqlexec"""

        filename = 'file:{}?cache=shared'.format(self.pathdlocal+SQLITEFILESTAT)

        con = sqlite3.connect(filename,uri=True)

        df_data = pd.read_sql_query(sqlexec, con)

        con.close()

        if(self.resolution == 'hourly'):
            strformat='%Y%m%d%H'
        elif(self.resolution == 'daily'):
            strformat='%Y%m%d'
        elif(self.resolution == 'monthly'):
            strformat='%Y%m'
        elif(self.resolution == 'yearly'):
            strformat='%Y'


        df_data.index = pd.to_datetime(df_data['MESS_DATUM'],format=strformat)
        df_data.drop(columns=['MESS_DATUM'],inplace=True)

        columns = df_data.columns
        replace_col = {}
        for column in columns:
            replace_col[column] = column.replace(' ','')

        df_data.rename(columns=replace_col,inplace=True)

        if(mask_fillVal):
            df_data.mask(df_data == FILLVALUE,inplace=True)

        return df_data


    def to_sqlite(self,df_in,key):
        """ Save data to sqlite
        """

        filename = 'file:{}?cache=shared'.format(self.pathdlocal+SQLITEFILESTAT)

        con = sqlite3.connect(filename,uri=True)

        tabname = f"{self.par}_{self.resolution}"

        lnew = True

        try:
            sqlexec = f"SELECT * from {tabname} WHERE STATIONS_ID = {key}"
            if(self.debug):
                print("Compare Sets")
                print(sqlexec)

            df_old = pd.read_sql_query(sqlexec,con)
            df_old.drop_duplicates(inplace=True)
            df_test = pd.concat([df_old,df_in]).drop_duplicates().reset_index(drop=True)
            df_test = df_test.merge(df_old,indicator=True,how='left').loc[lambda x : x['_merge']!='both']
            df_test.drop(columns='_merge',inplace=True)
            df_test.to_sql(tabname, con, if_exists="append", index=False)
            lnew = False

        except Exception as Excp:
            lnew = True  # if above fails, there seems to be no tab according to this name
            print(Excp)

        if(lnew):
            df_in.to_sql(tabname, con, index=False)

        con.close()


    def get_station_df_csv(self,dir_in):
        """
        """

        data_files = list_files(dir_in,ending='txt',only_files=True)
        for file in data_files:
            if('produkt' in file):
                df_tmp = pd.read_csv(file,delimiter=';')
                break

        # remove blanks from column names
        columns = df_tmp.columns
        replace_col = {}
        for column in columns:
            replace_col[column] = column.replace(' ','')

        df_tmp.rename(columns=replace_col,inplace=True)

        return df_tmp

    def get_obj_station(self,key,obj='name'):
        """ Get Metadata of Station Metadatafile """

        if(obj in ['von','bis']):
            return pd.to_datetime(self.df_station_list[self.df_station_list.index == key][obj].values[0])
        else:
            return self.df_station_list[self.df_station_list.index == key][obj].values[0]

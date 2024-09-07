# -*- coding: utf-8 -*-
"""
Created on Thu Jun 08 17:45:40 2020

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: This module mainly handles downloading data from
              DWD opendata homepage
"""

#import system modules
from sys import exit, float_repr_style, stdout, exc_info
import os
import pandas as pd
import datetime
import shutil
import numpy as np

from sqlalchemy import text

try:
    import pyproj
    from pyproj import Proj
    lproj = True
except:
    lproj = False
try:
    from pyproj import Transformer
    ltransform = True
except:
    ltransform = False

# local modules
from .constants.serverdata import SERVERPATH_CLIMATE_GERM, SERVERNAME, SERVERPATH_NWP, SERVERPATH_RASTER_GERM, SERVERPATH_REG_GERM
from .constants.filedata import *
from .constants.constpar import ASCIIRASCRS, FILLVALUE, RASTERFACTDICT, SQLITE_DRIVER, POSTGRES_DRIVER
from .helper.hfunctions import (check_create_dir, delete_sqlite_where, 
                                list_files, read_station_list, unzip_file, update_progress, 
                                write_sqlite, delete_sqlite_where, open_database, close_database,
                                check_for_table, create_table_res, create_table_regavg,
                                write_sqlite_data, check_drivers)
from .helper.ftp import cftp

class dow_handler(dict):
    def __init__(self,
                 dtype='station',
                 par='air_temperature' ,
                 resolution='hourly',
                 base_dir=os.getcwd()+'/'+MAIN_FOLDER,
                 period='recent',
                 nwpgrid='regular-lat-lon',
                 local_time = False,
                 date_check = None,
                 driver = 'SQLite',
                 dbconfigfile='.env',
                 config_dir=None,
                 dbschema='dwd',
                 debug = False
                ):
        """
        This class handles the download of data originating from opendata.dwd.de
        dtype: specify type of data --> station:Station Data, raster: Raster Data, nwp: Numerical Forecast
        par: Parameter to choose: kl, air_temperature, precipitation
        period: Define period --> historical, recent, now
        resolution: Define temporal resolution of data: hourly, daily, monthly, yearly
        base_dir: location of SQLite Database. Default is current directory
        nwpgrid: Grid of numerical forecast, default 'regular-lat-lon'
        local_time: translate to local time if wanted, otherwise time is in UTC
        date_check: check list of station data has to be data to this given date, if not specified today is used
        debug: True or False. Some more output
        
        dtype raster has to be set with period recent (which is default value)! 
        dtype regavg has to be set with period recent (which is default value)!
        """

        # very first check if dtype is available

        if(dtype not in DTYPEAVAIL):
            print(f'{dtype} is not available (at the moment)')
            print(f'Available dtypes:')
            for dtypeav in DTYPEAVAIL:
                print(f'{dtypeav}')
            return

        # store data
        self.dtype  = dtype
        self.par    = par
        self.period = period
        self.driver = driver
        self.dbconfigfile = dbconfigfile
        self.dbschema = dbschema
        self.debug  = debug
        self.local_time = local_time
        self.date_check = date_check
        self.resolution = resolution
        self.base_dir   = base_dir
        if(config_dir is None): # Assuming that configuration is stored in the same directory
            self.config_dir = base_dir
        else:
            self.config_dir = config_dir
        self.nwpgrid    = nwpgrid
        # store "Home" Directory
        self.home_dir   = os.getcwd()  ### TODO: Das geht hier vlt nicht so einfach... beißt sich mit base_dir und dem wechseln in die Verzeichnisse
        self.tmp_dir    = 'tmp{}/'.format(datetime.datetime.now().strftime('%s'))
        # create table name for sqlite database
        self.tabname = f"{self.par}_{self.resolution}"

        self.ldbsave = check_drivers(driver)

        icheck = self.prepare_download()

        if(icheck != 0):
            return

    def prepare_download(self):
        """ Prepare download data 
        """

        check_create_dir(self.base_dir)

        self.check_parameters()

        icheck = self.create_dirs()

        if(icheck != 0):
            return icheck 
        
        self.get_metadata()

    def check_parameters(self):
        """ Check if parameter combination is available
        """

        #check = TIME_RESOLUTION_MAP.get(self.resolution, ([], []))
        if(self.dtype == 'station'):
            time_check_map = TIME_RESOLUTION_MAP
        elif(self.dtype == 'raster'):
            time_check_map = TIME_RASTER_MAP
        elif(self.dtype == 'nwp'):
            time_check_map = NWP_DATA_MAP
        elif(self.dtype == 'regavg'):
            time_check_map = REG_AVG_MAP

        check = time_check_map[self.resolution]

        if(self.par not in check[0] or self.period not in check[1]):
            raise NameError(
                f"Wrong combination of resolution={self.resolution}, par={self.par} "
                f"and period={self.period}.\n"
                f"Please check again:\n"
                f"{time_check_map}" ### !!! >>TS TODO introduce better print function !!! <<TS###
            )

        if(self.dtype):
            if(self.nwpgrid not in NWPGRIDCHECK):
                raise NameError(
                    f'Wrong nwp grid! {self.nwpgrid} is not valid'
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
        elif(self.dtype == 'nwp'):
            # create local location to save data description
            self.pathmlocal = self.base_dir+METADATA_FOLDER+f'nwp_{self.resolution}_{self.par}/'
            # create path on remote server of metadata and data
            self.pathremote = SERVERPATH_NWP+f'{self.resolution}/grib/{self.period}/{self.par}/'
            # create local data to save data
            self.pathdlocal = self.base_dir+NWP_FOLDER+f'/{self.period}/{self.par}/'
            # create temp directory to avoid clashes of data streams
            self.pathdlocaltmp = self.base_dir+self.tmp_dir
        elif(self.dtype == 'regavg'):
            # create local location to save data description
            self.pathmlocal = self.base_dir+METADATA_FOLDER+f'regavg_{self.resolution}_{self.par}/'
            # create path on remote server of metadata and data
            self.pathremote = SERVERPATH_REG_GERM+f'{self.resolution}/{self.par}/'
            # create local data to save data
            self.pathdlocal = self.base_dir+REGAVG_FOLDER+f'/{self.resolution}/{self.par}/'
            self.pathregsql = self.base_dir+REGAVG_FOLDER+'/'
            # create temp directory to avoid clashes of data streams
            self.pathdlocaltmp = self.base_dir+self.tmp_dir
        else: # default
            print(f'{self.dtype} is not defined in create directories. Stop')
            return -1 
        
        return 0

    def get_metadata(self):
        """ Gets Metadata of data """

        if(self.dtype == 'station'):
            self.get_station_metadata()
        elif(self.dtype == 'raster'):
            self.get_raster_metadata()
        elif(self.dtype == 'nwp'):
            self.get_nwp_metadata()
        elif(self.dtype == 'regavg'):
            self.get_regavg_metadata()
        else:
            print(f'Metadata retrieval for {self.dtype} not found')
    
    def get_station_metadata(self):
        """ Get Station Metadata
        """

        # create meta data filename 
        filename = self.create_station_metaname()

        # check if dir already exists
        check_create_dir(self.pathmlocal)
        # Try to download Metadatafile
        try:
            metaftp = cftp(SERVERNAME)
            metaftp.open_ftp()
            metaftp.cwd_ftp(self.pathremote)
            os.chdir(self.pathmlocal)

            if(self.debug):
                print(f"Retrieve {self.pathremote+filename}")

            metaftp.save_file(filename,filename)
        
            metaftp.close_ftp()
        except Exception as Excp:
            print("Something went wrong during downloading Metadata")
            print(Excp)

        os.chdir(self.home_dir)

        try:
            self.df_station_list = read_station_list(self.pathmlocal,filename)
        except Exception as Excp:
            print("Something went wrong during reading Metadata")
            print(Excp)
            self.df_station_list = pd.DataFrame()

    def create_station_metaname(self):

        if(self.resolution == '10_minutes'):
            if(self.period == 'now'):
                if(self.par == 'solar'):
                    return f'zehn_{NAME_CONVERSATION_MAP[self.period]}_sd{NAME_CONVERSATION_MAP["meta_file_stationen"]}'
                elif(self.par == 'extreme_temperature'):
                    return f'zehn_{NAME_CONVERSATION_MAP[self.period]}_tx{NAME_CONVERSATION_MAP["meta_file_stationen"]}'
                else:
                    return f'zehn_{NAME_CONVERSATION_MAP[self.period]}_{NAME_CONVERSATION_MAP[self.par].lower()}{NAME_CONVERSATION_MAP["meta_file_stationen"]}'
            else:
                if(self.par == 'extreme_temperature'):
                    return f'zehn_min_tx{NAME_CONVERSATION_MAP["meta_file_stationen"]}' ## TODO The conversation maps should contain all of this
                else:
                    return f'zehn_min_{NAME_CONVERSATION_MAP[self.par].lower()}{NAME_CONVERSATION_MAP["meta_file_stationen"]}' 
        else:
            return f'{NAME_CONVERSATION_MAP[self.par]}_{NAME_CONVERSATION_MAP[self.resolution+f"_meta"]}{NAME_CONVERSATION_MAP["meta_file_stationen"]}'

    def create_raster_metaname(self):
        return f'DESCRIPTION_gridsgermany_{self.resolution}_{self.par}_en.pdf'

    def create_regavg_filename(self,time):
        """Create file name of regional averages
           str(time): defines time index --> month, seasonal or year;
                      example: month  time = '01' or time = '02' ...
                               seasonal time = 'autumn' or time = 'spring' ...
                               year   time = 'year'
        """

        return f'regional_averages_{REG_CONV_MAP[self.par]}_{time}.txt'

    def create_station_filename(self,key):
        """ Creates file location on ftp 
        TODO: adapt 
        """

        if(self.period == 'recent'):
            if(self.resolution == '10_minutes' and self.par == 'precipitation'):
                return f'{NAME_CONVERSATION_MAP[self.resolution]}_nieder_{key}_{NAME_CONVERSATION_MAP[self.period]}.zip'
            elif(self.resolution == '10_minutes' and self.par == 'extreme_wind'):
                return f'{NAME_CONVERSATION_MAP[self.resolution]}_extrema_wind_{key}_{NAME_CONVERSATION_MAP[self.period]}.zip'
            else:
                return f'{NAME_CONVERSATION_MAP[self.resolution]}_{NAME_CONVERSATION_MAP[self.par]}_{key}_{NAME_CONVERSATION_MAP[self.period]}.zip'
        elif(self.period == 'now'):
            if(self.par == 'precipitation'): ## may be the Name Conversation Map should be restructured! that it contains already the period and then self.par
                return f'{NAME_CONVERSATION_MAP[self.resolution]}_nieder_{key}_{NAME_CONVERSATION_MAP[self.period]}.zip'
            elif(self.resolution == '10_minutes' and self.par == 'extreme_wind'):
                return f'{NAME_CONVERSATION_MAP[self.resolution]}_extrema_wind_{key}_{NAME_CONVERSATION_MAP[self.period]}.zip'
            elif(self.par == 'wind'):
                return f'{NAME_CONVERSATION_MAP[self.resolution]}_wind_{key}_{NAME_CONVERSATION_MAP[self.period]}.zip'
            elif(self.par == 'solar'):
                return f'{NAME_CONVERSATION_MAP[self.resolution]}_SOLAR_{key}_{NAME_CONVERSATION_MAP[self.period]}.zip'
            else:
                return f'{NAME_CONVERSATION_MAP[self.resolution]}_{NAME_CONVERSATION_MAP[self.par]}_{key}_{NAME_CONVERSATION_MAP[self.period]}.zip'
        else:
            cvon = self.get_obj_station(key,obj='von').strftime('%Y%m%d')
            tbis = self.get_obj_station(key,obj='bis')
            if(tbis.year == datetime.datetime.now().year):
                year = (datetime.datetime.now() + datetime.timedelta(days=-500)).year
                cbis = '{}1231'.format(year)
            else:
                cbis = self.get_obj_station(key,obj='bis').strftime('%Y%m%d')
            if(self.resolution == '10_minutes' and self.par == 'extreme_wind'):
                return f'{NAME_CONVERSATION_MAP[self.resolution]}_nieder_{key}_{cvon}_{cbis}_{NAME_CONVERSATION_MAP[self.period]}.zip'
            elif(self.resolution == '10_minutes' and self.par == 'extreme_wind'):
                return f'{NAME_CONVERSATION_MAP[self.resolution]}_extrema_wind_{key}_{cvon}_{cbis}_{NAME_CONVERSATION_MAP[self.period]}.zip'
            else:
                return f'{NAME_CONVERSATION_MAP[self.resolution]}_{NAME_CONVERSATION_MAP[self.par]}_{key}_{cvon}_{cbis}_{NAME_CONVERSATION_MAP[self.period]}.zip'

    def create_nwp_filename(self,hour,mlayer=NWPMAXMOLEV,player=1000):
        """ Creates file location on ftp nwp data """

        date = datetime.datetime.now().strftime('%Y%m%d')
        date = f'{date}{self.period}'
        lvllayer = NWPNAMEDICT[self.par]
        if(lvllayer == 'single-level'):
            return f'{self.resolution}_{NWPNAMEDICT[self.resolution]}_{self.nwpgrid}_{lvllayer}_{date}_{hour:03d}_2d_{self.par}.grib2.bz2'
        elif(lvllayer == 'model-level'):
            return f'{self.resolution}_{NWPNAMEDICT[self.resolution]}_{self.nwpgrid}_{lvllayer}_{date}_{hour:03d}_{mlayer}_{self.par}.grib2.bz2'
        elif(lvllayer == 'pressure-level'):
            return f'{self.resolution}_{NWPNAMEDICT[self.resolution]}_{self.nwpgrid}_{lvllayer}_{date}_{hour:03d}_{player}_{self.par}.grib2.bz2'

    def create_raster_filename(self,year,month,readf=False,clim_mean=False):
        """ Creates file location on ftp for raster data """

        if(clim_mean):
            # create end year of climate normal period
            year_sec = year + 29

        if(self.par in RASTERNCDICT):
            file_ending = 'nc'
        elif(readf):
            file_ending = 'asc'
        else:
            file_ending = 'asc.gz'

        if(readf and not clim_mean):
            return f'grids_germany_{self.resolution}_{RASTER_CONVERSATION_MAP[self.par]}_{year}{month:02d}.{file_ending}'
        elif(readf and clim_mean):
            if((year > 1990) & (self.par == 'air_temperature_mean')): # This is problem on DWD server
                return f'grids_germany_multi_annual_{RASTER_CONVERSATION_MAP[self.par]}_{year}_{year_sec}_{month:02d}.{file_ending}'
            else:
                return f'grids_germany_multi_annual_{RASTER_CONVERSATION_MAP[self.par]}_{year}-{year_sec}_{month:02d}.{file_ending}'
        elif(clim_mean):
            if((year > 1990) & (self.par == 'air_temperature_mean')): # This is problem on DWD server
                return f'grids_germany_multi_annual_{RASTER_CONVERSATION_MAP[self.par]}_{year}_{year_sec}_{month:02d}.{file_ending}'
            else:
                return f'grids_germany_multi_annual_{RASTER_CONVERSATION_MAP[self.par]}_{year}-{year_sec}_{month:02d}.{file_ending}'
        elif(self.par in RASTERMONTHSUB):
            return f'{RASTERMONTHDICT[month-1]}/grids_germany_{self.resolution}_{RASTER_CONVERSATION_MAP[self.par]}_{year}{month:02d}.{file_ending}'
        else:
            return f'grids_germany_{self.resolution}_{RASTER_CONVERSATION_MAP[self.par]}_{year}{month:02d}.{file_ending}'

    def get_raster_metadata(self):
        """ Get Raster Data Metadata
        """

        print("Raster Metadata not yet implemented")

    def get_regavg_metadata(self):
        """ Get Regional Averages Data Metadata
        """

        if(self.debug == True):
            print("Regional Average Metadata not yet available on homepage")

    def get_nwp_metadata(self):
        """ Get NWP Metadata 
        """

        print("NWP Metadata not yet implemented")

    def retrieve_dwd_nwp(self,max_hour=48,**kwargs):
        """ Retrieves DWD NWP data
            max_hour: defines the maximum hour to get; default 48 hours
        """

        # Are the pathes there
        check_create_dir(self.pathdlocal)
        os.chdir(self.pathdlocal)

        metaftp = cftp(SERVERNAME)
        metaftp.open_ftp()
        metaftp.cwd_ftp(self.pathremote)

        ii = 0
        i_tot = max_hour
        not_in_list = []
        for i in range(max_hour):
                update_progress(i/i_tot)
                filename = self.create_nwp_filename(i,**kwargs)

                if(self.debug):
                    print(f"Retrieve: {self.pathremote+filename}")

                try:
                        metaftp.save_file(filename,filename)
                except:
                    print(f"{self.pathremote+filename} not found")
                    not_in_list.append(self.pathremote+filename)


        metaftp.close_ftp()

        os.chdir(self.home_dir)

    def retrieve_dwd_regavg(self):
        """Retrieves DWD regional average data
           Regional Averages are always retrieved als complete package!
           for example self.resolution = 'monthly' downloads 12 month
           for example self.resolution = 'seasonal' downloads 4 seasons ( no not the four seasons total Landscaping )
           for example self.resolution = 'annual' downloads yearly values
           The data is summed up in one file each at DWD. So yearly will deliver on pandas dataframe
        """

        filenlist = []
        if(self.resolution == 'monthly'):
            for month in REGAVGMONTHS:
                filenlist.append(self.create_regavg_filename(month))
        elif(self.resolution == 'seasonal'):
            for season in REGAVGSEASONS:
                filenlist.append(self.create_regavg_filename(season))
        elif(self.resolution == 'annual'):
            filenlist.append(self.create_regavg_filename('year'))

        # Are the pathes there
        #check_create_dir(self.pathdlocal)
        check_create_dir(self.pathregsql)
        check_create_dir(self.pathdlocaltmp)
        # Change into directory
        #os.chdir(self.pathdlocal)
        os.chdir(self.pathdlocaltmp)

        filenamesql = 'file:{}?cache=shared'.format(self.pathregsql+SQLITEREGAVG)

        con = open_database(filenamesql, self.ldbsave, self.driver, 
                            config_dir=self.config_dir,
                            postfile=self.dbconfigfile)

        if(check_for_table(con,self.tabname,self.driver)):
            print(f"Table {self.tabname} exists")
            lcreate=False
        else:
            print(f"Create Table {self.tabname}")
            lcreate=True

        # Log in to ftp server
        metaftp = cftp(SERVERNAME)
        metaftp.open_ftp()
        # change to remote directory
        metaftp.cwd_ftp(self.pathremote)

        # download files listed in filenlist
        for filename in filenlist:
            if(self.debug):
                print(f'Retrieve: {self.pathremote+filename}')
            metaftp.save_file(filename,filename)
            df_tmp = pd.read_csv(filename,delimiter=';',skiprows=[0])
            df_tmp.rename(columns={'winter':'season','spring':'season','summer':'season','autumn':'season'},inplace=True)
            df_tmp.drop(columns=df_tmp.columns[df_tmp.columns.str.contains('Unnamed')],inplace=True)
            df_tmp.drop(columns=df_tmp.columns[df_tmp.columns.str.contains('Jahr.1')],inplace=True)
            df_tmp.columns = df_tmp.columns.str.replace('-','_')
            df_tmp.columns = df_tmp.columns.str.replace('/','_')
            if(lcreate):
                create_table_regavg(con,resolution=self.resolution,par=self.par,keys=df_tmp.keys())
            write_sqlite_data(df_tmp, con, self.tabname, self.driver)

        # close ftp connection
        metaftp.close_ftp()

        close_database(con, self.driver)

        os.chdir(self.home_dir)

        try:
            shutil.rmtree(self.pathdlocaltmp)
        except OSError as e:
            print(f"Error: {self.pathdlocaltmp} : {e.strerror}")

    def retrieve_dwd_raster(self,year,month,to_netcdf=False,clim_mean=False):
        """ Retrieves DWD Raster data
            year:  can be a single year or a list with starting year and end year;
                   [2000,2010] means download data from 2000 to 2010
                   in case of clim_mean = True year can be either list or scalar value
                   But in case of list only first entry will be used, so the scalar value
                   or the first value of the list defines starting point of 30 year climate
                   normal period. Valid as beginning year 1961, 1971, 1981, 1991
            month: can be a single month or a list with starting month and end month
                   [1,4] means download data from January to February
            to_netcdf: True/False; True save data to a netCDF File -- Not Yet implemented!! --
        """

        if(clim_mean and not isinstance(year,list)):
            year_arange = [year]
        elif(clim_mean and isinstance(year,list)):
            year_arange = [year[0]]
        elif(isinstance(year, list)):
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

        if(clim_mean):
            # save temporarly remote file location
            pathremotetmp = self.pathremote
            # replace resolution part with multi_annual
            self.pathremote = self.pathremote.replace(f'{self.resolution}','multi_annual')

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
                filename = self.create_raster_filename(tyear,tmonth,clim_mean=clim_mean)

                if(self.debug):
                    print(f"Retrieve: {self.pathremote+filename}")

                try:
                    if(self.par in RASTERMONTHSUB and not clim_mean):
                        metaftp.save_file(filename,filename[7:])
                    else:
                        metaftp.save_file(filename,filename)
                except:
                    print(f"{self.pathremote+filename} not found")
                    not_in_list.append(self.pathremote+filename)

                try:
                    if(self.par in RASTERMONTHSUB and not clim_mean):
                        os.system('gunzip -f '+filename[7:])
                    elif(self.par not in RASTERNCDICT): ### Files with nc ending are not needed to unzip
                        os.system('gunzip -f '+filename)
                except:
                    print(f'{filename} could not gunziped --> Is gunzip installed on local machine?')
                    print('Python intern gunzip not yet implemented!')

        # attach all files which are not found
        self.stations_not_found = not_in_list
        if(clim_mean):
            # reset remote path again
            self.pathremote = pathremotetmp

        metaftp.close_ftp()

        os.chdir(self.home_dir)

        if(to_netcdf):
            try:
                shutil.rmtree(self.pathdlocaltmp)
            except OSError as e:
                print(f"Error: {self.pathdlocaltmp} : {e.strerror}")

    def read_dwd_regavg(self,cyears=1961,cyeare=1990):
        """ Reads DWD Raster data
            data is read as one pandas DataFrame
            cyears: Start year of climate normal period (default 1961)
            cyeare: End year of climate normal period (default 1990 )
        """

        filenamesql = 'file:{}?cache=shared'.format(self.pathregsql+SQLITEREGAVG)
        con = open_database(filenamesql, self.ldbsave, self.driver, 
                            config_dir=self.config_dir,
                            postfile=self.dbconfigfile)

        if(self.resolution == 'annual'):

            sqlexec = f"SELECT * from {self.tabname}"
            # create filename
            #filename = self.create_regavg_filename('year')
            # read data and skipping first line
            #df_out = pd.read_csv(self.pathdlocal+filename,delimiter=';',skiprows=[0])
            df_out = pd.read_sql_query(sqlexec,con=con)
            df_out.index = pd.to_datetime(df_out['Jahr'],format='%Y')
            df_out.index.name = 'Jahr'
            # Jahr are two columns in dataset, so drop the first one because it is an index
            # drop second one because it is obsolet
            df_out.drop(columns=['Jahr'],inplace=True)
            # create climate normal period 
            df_clim = df_out[(df_out.index.year >= cyears) & (df_out.index.year <= cyeare)].mean(axis=0)
            # calculate deviation
            for key in df_out.keys():
                df_out[f'{key}_dev'] = df_out[key] - df_clim[key]
        elif(self.resolution == 'seasonal'):
            sqlexec = f"SELECT * from {self.tabname}"
            df_compl = pd.read_sql_query(sqlexec,con=con)
            self.df_compl = df_compl
            for season in REGAVGSEASONS:
                # create filename
                #filename = self.create_regavg_filename(season)
                # read data and skipping first line
                #df_tmp = pd.read_csv(self.pathdlocal+filename,delimiter=';',skiprows=[0])
                #df_tmp = pd.read_sql_query(sqlexec,con=con)
                #df_tmp.rename(columns={season:'season'},inplace=True)
                df_tmp = df_compl.query(f"season == '{season}'")
                # create climate normal period 
                df_clim = df_tmp[(df_tmp['Jahr'] >= cyears) & (df_tmp['Jahr'] <= cyeare)].mean(axis=0,numeric_only=True)
                # calculate deviation
                for key in df_tmp.keys():
                    if(key not in ['season','Jahr']):
                        df_tmp[f'{key}_dev'] = df_tmp[key] - df_clim[key]    
                try:
                    df_out = pd.concat([df_out,df_tmp])
                except:
                    df_out = df_tmp.copy()
            df_out.index = pd.to_datetime(df_out['Jahr'],format='%Y')
            df_out.index.name = 'Jahr'
        elif(self.resolution == 'monthly'):
            sqlexec = f"SELECT * from {self.tabname}"
            df_compl = pd.read_sql_query(sqlexec,con=con)
            self.df_compl = df_compl
            for month in REGAVGMONTHS:
                month_int = int(month)
                #create filename
                #filename = self.create_regavg_filename(month)
                # read data and skipping first line
                #df_tmp = pd.read_csv(self.pathdlocal+filename,delimiter=';',skiprows=[0])
                df_tmp = df_compl.query(f"Monat == {month_int}")
                # create climate normal period 
                df_clim = df_tmp[(df_tmp['Jahr'] >= cyears) & (df_tmp['Jahr'] <= cyeare)].mean(axis=0)
                # calculate deviation
                for key in df_tmp.keys():
                    df_tmp[f'{key}_dev'] = df_tmp[key] - df_clim[key]    
                try:
                    df_out = pd.concat([df_out,df_tmp])
                except:
                    df_out = df_tmp.copy()
            df_out.index = pd.to_datetime(df_out.apply(lambda row: f'{int(row.Jahr)}-{int(row.Monat)}-01', axis=1))
            df_out.index.name = 'Datum'
            df_out.drop(columns=['Jahr','Monat'],inplace=True)
            df_out.sort_index(inplace=True)
        else:
            print(f'{self.resolution} is unknown. Not data to return')
            return


        # Last ; in data leads to this column, so try to drop it
        try:
            df_out.drop(columns=['Unnamed: 19','Unnamed: 19_dev'],inplace=True)
        except:
            pass

        close_database(con, self.driver)

        return df_out

    def read_dwd_raster(self,year,month,netcdf=False,calc_dev=False,clim_mean=False,clim_year_s=None):
        """ Read DWD Raster data
            year:  can be a single year or a list with starting year and end year;
                   [2000,2010] means download data from 2000 to 2010
            month: can be a single month or a list with starting month and end month
                   [1,4] means download data from January to February
            netcdf: True/False; read data from netCDF File -- Not Yet implemented!! --
            clim_mean: Reads climatic normal period --> first year of 30 year period must be given
            calc_dev: Calculates deviation --> first year of 30 year period must be given
        """

        if(isinstance(year, list)):
            if(self.debug):
                print(f'Read year {year[0]} - {year[-1]}')
            year_arange = np.arange(year[0],year[-1]+1)
        else:
            if(self.debug):
                print(f"Read year {year}")
            year_arange = np.array([year])

        if(isinstance(month, list)):
            if(self.debug):
                print(f'and month {month[0]} - {month[-1]}')
            month_arange = np.arange(month[0],month[-1]+1)
        else:
            if(self.debug):
                print(f"and month {month}")
            month_arange = np.array([month])

        data_clim = []
        if(clim_mean or calc_dev):
            if(clim_year_s is None):
                print(f"Please specify clim_year_s")
                return

            for tmonth in month_arange:
                filename = self.create_raster_filename(clim_year_s,tmonth,readf=True,clim_mean=clim_mean)
                # set climate normal years to class
                self.clim_y_s = clim_year_s
                self.clim_y_e = clim_year_s + 29
                data_clim.append(self.read_raster_ascii(self.pathdlocal+filename))
                #data_clim = self.read_raster_ascii(self.pathdlocal+filename)
            data_clim = np.asarray(data_clim,dtype=np.float64)
            data_clim = np.ma.masked_where(data_clim == self.missingval,data_clim)
            if(not calc_dev):
                if(self.par in RASTERFACTDICT.keys()):
                    data_clim *= RASTERFACTDICT[self.par]
                return data_clim

        data_r = []
        data_r_anom = [] # !! TODO! Add climate normal periods to calculate deviations
        i_tot = len(year_arange)*len(month_arange)
        lfirst = True ## needed to create multiarray in first place
        ii = 0
        for tyear in year_arange:
            imonth = 0
            for tmonth in month_arange:
                filename = self.create_raster_filename(tyear,tmonth,readf=True)
                if(netcdf):
                    pass
                else:
                    data_tmp = self.read_raster_ascii(self.pathdlocal+filename)
                    try:
                        #data_r.append(self.read_raster_ascii(self.pathdlocal+filename))
                        data_tmp = self.read_raster_ascii(self.pathdlocal+filename)
                    except:
                        #data_r.append(np.full((self.rnrows,self.rncols),self.missingval))
                        data_tmp = np.full((self.rncols,self.rnrows),self.missingval)

                data_tmp = np.ma.masked_where(data_tmp == self.missingval, data_tmp)

                if(lfirst):
                    data_r = np.full((i_tot,self.rncols,self.rnrows),self.missingval)
                    if(calc_dev):
                        data_r_anom = np.full((i_tot,self.rncols,self.rnrows),self.missingval)
                    lfirst = False
                data_r[ii] = data_tmp

                if(calc_dev):
                    data_r_anom[ii] = data_r[ii] - data_clim[imonth]

                imonth += 1
                ii += 1

        # mask data with Fill Value
        data_r_m = np.ma.masked_where(data_r==self.missingval,data_r)
        if(calc_dev):
            data_r_anom_m = np.ma.masked_where(data_r_anom==self.missingval,data_r_anom)

        # is it necessary to multiply data with a factor?
        if(self.par in RASTERFACTDICT.keys()):
            data_r_m *= RASTERFACTDICT[self.par]
            if(calc_dev):
                data_r_anom_m *= RASTERFACTDICT[self.par]

        if(calc_dev):
            return data_r_m, data_r_anom_m
        else:
            return data_r_m

    def set_raster_grid(self):
        """ Creates grid with lon lat for DWD ASCII Grid"""

        # Check first if data was read
        try:
            self.xllcorner
        except:
            print("First read raster data with:")
            print("dow_handler.read_dwd_raster()")
            return

        if(self.debug):
            print("Create Grid")
        self.create_grid()

    def create_grid(self):
        """ Returns four arrays with 1D x-y and 2D xx-yy coordinates
            uses projection of raster and project to lon lat
        """

        if(not lproj):
            print("pyproj seems not installed; Return")
            return

        inProj  = Proj({'init': f'{self.crs_in}'})
        outProj = Proj({'init': 'epsg:4326'})

        if(ltransform):
            transformer = Transformer.from_proj(inProj,outProj)

            transform = transformer.transform

        grid_x = np.zeros((self.rncols))
        grid_y = np.zeros((self.rnrows))

        for ii in range(self.rncols):
            grid_x[ii] = self.xllcorner + self.rcellsize * ii

        for ii in range(self.rnrows):
            grid_y[ii] = self.yllcorner + self.rcellsize * ii

        lons = np.zeros((self.rncols,self.rnrows))
        lats = np.zeros((self.rncols,self.rnrows))

        
        # Fill 2D lon lat arrays with values
        for ii in range(self.rncols):
            for jj in range(self.rnrows):
                #tmp_lon, tmp_lat = transform(grid_x[ii],grid_y[jj])
                if(ltransform):
                    lons[ii,jj], lats[ii,jj] = transform(grid_x[ii],grid_y[jj])
                else:
                    lons[ii,jj], lats[ii,jj] = pyproj.transform(inProj, outProj, grid_x[ii],grid_y[jj])


            update_progress(ii/self.rncols)

        self.gridx = grid_x 
        self.gridy = grid_y

        self.rlons = lons
        self.rlats = lats

    def read_raster_ascii(self,filename):
        """ Reads ASCII data from DWD Raster data
            Saves lower left and right corner to class
            Saves grid cell size to class
            number of rows and columns
        """

        if(self.debug):
            print(f'Read\n{filename}')

        with open(filename) as f:
            content = f.readlines()

        # safe number of columns and rows
        self.rncols = int(content[0].split()[1])
        self.rnrows = int(content[1].split()[1])

        # safe lower left and lower right corner
        self.xllcorner = float(content[2].split()[1])
        self.yllcorner = float(content[3].split()[1])

        # safe cell size 
        self.rcellsize = float(content[4].split()[1])

        # safe missing value
        self.missingval = float(content[5].split()[1])

        self.crs_in = ASCIIRASCRS

        # create data array
        data = []

        # parse each line, skip header
        for line in content[6:]: # skip header
            data.append(line.split())  # splits whitespace and appends row to data

        if(self.debug):
            print("File props")
            print(f"ncols: {self.rncols}")
            print(f"nrows: {self.rnrows}")
            print(f"xll: {self.xllcorner}")
            print(f"yll: {self.yllcorner}")
            print(f"cellsize: {self.rcellsize}")
            print(f"fillVal: {self.missingval}")

        # convert to float
        [[float(y) for y in x] for x in data]

        # convert data to numpy arr
        new_data = [[float(string) for string in inner] for inner in data]
        np_data = np.asarray(new_data)

        # data is upside down --> flip it and transpose
        np_data = np_data[::-1,:].T

        return np_data

    def retrieve_dwd_station(self,key_arr,to_sqlite=True,**kwargs):
        """ Retrieves DWD Station data 
            key_arr:   IDs of stations to retrieve, 1D-Array
            to_sqlite: Saves data within SQLITE databank
        """

        # test types of input parameters
        assert isinstance(key_arr, list)

        print(f"Len key_arr {len(key_arr)}")

        check_create_dir(self.pathdlocal)
        check_create_dir(self.pathdlocaltmp)

        os.chdir(self.pathdlocaltmp)

        metaftp = cftp(SERVERNAME)
        metaftp.open_ftp()
        metaftp.cwd_ftp(self.pathremote)

        ii = 0
        i_tot = float(len(key_arr))
        not_in_list = []

        filenamesql = 'file:{}?cache=shared'.format(self.pathdlocal+SQLITEFILESTAT)

        con = open_database(filenamesql, self.ldbsave, 
                            self.driver, 
                            dbschema=self.dbschema,
                            debug=self.debug,
                            config_dir=self.config_dir,
                            postfile=self.dbconfigfile)

        if(check_for_table(con,self.tabname,self.driver)):
            print(f"Table {self.tabname} exists")
            lcreate=False
        else:
            print(f"Create Table {self.tabname}")
            lcreate=True

        if(lcreate):
            if(not create_table_res(con,self.resolution, self.par,self.driver, schema=self.dbschema)):
                return

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
                # prepare date to split into year month day ...
                self.df_tmp = df_tmp
                write_sqlite_data(df_tmp, con, self.tabname, self.driver)
            except Exception as Excp:
                print(Excp)
                print(f"{self.pathremote+filename} not found\n")
                not_in_list.append(self.pathremote+filename)
            os.chdir('../')

        self.stations_not_found = not_in_list

        metaftp.close_ftp()

        close_database(con, self.driver)

        os.chdir(self.home_dir)

        try:
            shutil.rmtree(self.pathdlocaltmp)
        except OSError as e:
            print(f"Error: {self.pathdlocaltmp} : {e.strerror}")


    def get_dwd_station_data(self,key,mask_FillVal=True):
        """ Get Data from sqlite database """

        filename = 'file:{}?cache=shared'.format(self.pathdlocal+SQLITEFILESTAT)

        con = open_database(filename, self.ldbsave, self.driver,debug=self.debug,
                            config_dir=self.config_dir,
                            postfile=self.dbconfigfile)

        if(self.driver in [POSTGRES_DRIVER]):
            tabname = f"{self.dbschema}.{self.par}_{self.resolution}"
        else:
            tabname = f"{self.par}_{self.resolution}"

        sqlexec = "SELECT * from {} WHERE STATIONS_ID = {}".format(tabname,key)
        if(self.driver in [POSTGRES_DRIVER]):
            sqlexec = text(sqlexec)

        if(self.debug):
            print("Get data:")
            print(sqlexec)

        df_data = pd.read_sql_query(sqlexec, con)

        close_database(con, self.driver)

        if(self.resolution == 'hourly'):
            strformat='%Y%m%d%H'
        if(self.resolution == '10_minutes'):
            strformat='%Y%m%d%H%M'
        elif(self.resolution == 'daily'):
            strformat='%Y%m%d'
        elif(self.resolution == 'monthly'):
            strformat='%Y%m'
        elif(self.resolution == 'yearly'):
            strformat='%Y'

        if(self.driver in [POSTGRES_DRIVER]):
            date_string = 'mess_datum'
        else:
            date_string = 'MESS_DATUM'

        df_data.index = pd.to_datetime(df_data[date_string],format=strformat) ## TODO MESS_DATUM durch generisches filedata austauschen
        df_data.drop(columns=[date_string],inplace=True)

        columns = df_data.columns
        replace_col = {}
        for column in columns:
            replace_col[column] = column.replace(' ','')

        df_data.rename(columns=replace_col,inplace=True)

        if(mask_FillVal):
            df_data.mask(df_data == FILLVALUE,inplace=True)

        return df_data

    def get_data(self,sqlexec,
                 ldateindex=True,
                 mask_fillVal=True):
        """ Get data according to sqlexec
        Arguments:
            sqlexec:      SQLite Query
            ldateindex:   Date ("MESS_DATUM") as index (True/False --> Default True)
            mask_fillVal: mask FillValue (True/False --> Default True)
        """

        filename = 'file:{}?cache=shared'.format(self.pathdlocal+SQLITEFILESTAT)

        con = open_database(filename, self.ldbsave, self.driver,debug=self.debug,
                            config_dir=self.config_dir,
                            postfile=self.dbconfigfile)

        df_data = pd.read_sql_query(sqlexec, con)

        close_database(con, self.driver)

        if(ldateindex):
            if(self.resolution == 'hourly'):
                strformat='%Y%m%d%H'
            elif(self.resolution == '10_minutes'):
                strformat='%Y%m%d%H%M'
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


    def clean_database(self):
        """ Cleans Database --> could be possible if multiple times data was added
            Keeps the last entry
        """

        filename = 'file:{}?cache=shared'.format(self.pathdlocal+SQLITEFILESTAT)

        con = open_database(filename, ldbsave=self.ldbsave, driver=self.driver,debug=self.debug,
                            config_dir=self.config_dir,
                            postfile=self.dbconfigfile)

        tabname = f"{self.par}_{self.resolution}"

        sqlexc = f"DELETE FROM {tabname} "\
                  "WHERE rowid NOT IN "\
                  "(" \
                  "SELECT max(rowid) "\
                 f"FROM {tabname} "\
                  "GROUP BY STATIONS_ID, MESS_DATUM )"

        if(self.debug):
            print(sqlexc)
            print("Clear database")

        con.execute(sqlexc)
        con.commit()

        close_database(con, self.driver)

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

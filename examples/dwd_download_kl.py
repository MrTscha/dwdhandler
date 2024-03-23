"""
Example script to download daily data from DWD stations
"""

import dwdhandler

# which parameter to download
# here climate stations of DWD
par = 'kl'
# which period to consider. 'recent' or 'historical'
# 'historical' would be complete dataset
period = 'recent'
# daily resolution of data
resolution = 'daily'
# location of SQLite Database, which will be created
base_dir = '/home/tobias/workspace/DATA/DWD/'
# key corresponds to station ID
key = None

dow_handler = dwdhandler.dow_handler(par=par,
                                     period=period,
                                     resolution=resolution,
                                     base_dir=base_dir)

if(key is None): # if None download all station data
    dow_handler.retrieve_dwd_station(list(dow_handler.df_station_list.index))
else: # otherwise only specific station data
    dow_handler.retrieve_dwd_station([key]) 
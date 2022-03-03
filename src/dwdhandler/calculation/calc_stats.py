# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 17:45:00 2022

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: This module computes simple statistics of meteorological data 
"""

#import system modules
import os
import numpy as np
import pandas as pd

#local modules
from ..constants.filedata import *

# create class for station data
class station_data_handler():
    def __init__(self,df_tot,
                 tabname=None,
                 var_sum=False,
                 var_perc=False,
                 var_max=False,
                 base_dir=os.getcwd()+'/'+MAIN_FOLDER,
                 year_spec=None,
                 ldebug=False):
        """ 
        Init station data handler.
        df_tot   : Pandas dataframe which contains data --> for example on daily basis
        tabname  : This is the table name from dow_handler which is now modified --> use dow_handler.tabname to get it
        var_sum  : Is it a variable which needs monthly sum (for example precipitation) 
        var_perc : Is it a variable which deviation should be calculated in percent (for example precipitation)
        var_max  : Only calculate the maximum in resampled space
        base_dir : Should be the same directory like sqlite data is stored to use one database
        year_spec: Is a special year wanted
        ldebug   : Some additional output
        """

        if(tabname is None):
            print("Name of table not specified!")
            print("Please get it from dow_handler.tabname")
            return

        self.tabname   = tabname
        self.var_sum   = var_sum
        self.var_perc  = var_perc
        self.var_max   = var_max
        self.base_dir  = base_dir
        if(year_spec is None):
            self.year_spec = year_spec
        else:
            self.year_spec = df_tot.index.year[-1]  # should be a sorted index
        self.ldebug    = ldebug

        self.FillValue = -999.

        self.df_tot    = df_tot.mask(df_tot == self.FillValue)
        self.df_tot.dropna(inplace=True)

        if(self.ldebug):
            print("init complete")

        if(df_tot.empty):
            self.lcalc = False
            print("No data in DataFrame")
            return
        else:
            self.lcalc = True

    def calc_vals(self):
        """Resample values"""

        if(self.lcalc):
            self.calc_daily_vals()
            self.calc_monthly_vals()
            self.calc_yearly_vals()

    def calc_daily_vals(self):
        """Calculates daily values --> resamples df_tot"""
        self.df_daily = self.resample_df(self.df_tot,'D')

    def calc_monthly_vals(self):
        """Calculates monthly values --> resamples df_tot"""
        self.df_monthly = self.resample_df(self.df_tot,'M')

    def calc_yearly_vals(self):
        """Calculates yearly values --> resamples df_tot"""
        self.df_yearly = self.resample_df(self.df_tot,'Y')
    
    def resample_df(self,df_in,type_resample):
        """Resample DataFrame
        df_in:         pandas DataFrame with datetime as index
        type_resample: string --> Type of resampmling (D daily, M monthly, Y yearly, and so on)
        
        Resampling also takes into account self.var_sum. If True the sum will be resampled otherwise mean
        """

        if(self.var_sum):
            df_out = df_in.resample(type_resample).sum()
            df_out.mask(df_out == 0, inplace=True)
        elif(self.var_max):
            df_out = df_in.resample(type_resample).max()
        else:
            df_out = df_in.resample(type_resample).mean()
        return df_out.dropna()
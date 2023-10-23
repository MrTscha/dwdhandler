# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 17:45:00 2022

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: This module computes simple statistics of meteorological data 
"""

#import system modules
from distutils.log import debug
from enum import unique
import os
import numpy as np
import pandas as pd

#local modules
from ..constants.filedata import *
from ..helper.hfunctions import (write_sqlite, write_exc_info, write_sqlite_data,
                                 drop_table, open_database, 
                                 check_for_table, create_table_res_climstats)

# create class for station data
class station_data_handler(dict):
    def __init__(self,df_tot,
                 key,
                 tabname=None,
                 var_sum=False,
                 var_perc=False,
                 var_max=False,
                 resolution=None,
                 par=None,
                 base_dir=os.getcwd()+'/'+MAIN_FOLDER,
                 year_spec=None,
                 ldebug=False):
        """
        Init station data handler.
        df_tot   : Pandas dataframe which contains data --> for example on daily basis
        key      : Station ID
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
        self.tabname_c = f'{tabname}_clim'
        self.tabname_d = f'{tabname}_dev'
        self.var_sum   = var_sum
        self.var_perc  = var_perc
        self.var_max   = var_max
        self.base_dir  = base_dir
        self.key       = key

        self.resolution = resolution
        self.par        = par

        if(year_spec is None):
            self.year_spec = year_spec
        else:
            self.year_spec = df_tot.index.year[-1]  # should be a sorted index
        self.ldebug    = ldebug

        self.FillValue = -999.

        self.df_tot    = df_tot.mask(df_tot == self.FillValue)
#        self.df_tot.dropna(inplace=True)

        # create a dummy non-leap year --> we only need day and month for daily calculation
        self.nonleap_range = pd.date_range('2001-01-01','2001-12-31')

        self.default_clim_norms = [1961,1971,1981,1991]

        self.lsqlite_prep = False # Triggers warning in case of writing to sqlite

        if(self.ldebug):
            print("init complete")

        if(df_tot.empty):
            self.lcalc = False
            print("No data in DataFrame")
            return
        else:
            self.lcalc = True

    def __getattr__(self, item):
        return self[item]

    def __dir__(self):
        return super().__dir__() + [str(k) for k in self.keys()]

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
            #df_out.mask(df_out == 0, inplace=True)
        elif(self.var_max):
            df_out = df_in.resample(type_resample).max()
        else:
            df_out = df_in.resample(type_resample).mean()
        #return df_out.dropna()
        return df_out

    def calc_clim_mean(self,years=1961,yeare=1991):
        """Calculate the climatolocigal mean of data
        This routine calculates the mean of each DataFrame of this class
        meanging df_daily, df_monthly and df_yearly
        years: First year to taken into account for calculation (default 1961)
        yeare: Last year to taken into account for calculation (default 1991)
        do_min_max: Additionally calculate min/max (default False)
        percentile: list of two values of percentiles, if given percentiles are also calculated (default None)
        """

        df_clim = self.extract_subdata_year(self.df_daily,years,yeare)
        sdf_name = f'df_daily_c_{years}'
        #df_clim = df_clim[~((df_clim.index.month == 2) & (df_clim.index.day==29))] # remove leap year from data
        # But this brings the leap year back on table... So mean is for 366 days...
        #self[sdf_name] = df_clim.groupby(df_clim.index.dayofyear).mean()
        self[sdf_name] = self.calc_daily_clim(df_clim) 

        df_clim = self.extract_subdata_year(self.df_monthly,years,yeare)
        sdf_name = f'df_monthly_c_{years}'
        self[sdf_name] = df_clim.groupby(df_clim.index.month).mean(numeric_only=True)

        df_clim = self.extract_subdata_year(self.df_yearly,years,yeare)
        sdf_name = f'df_yearly_c_{years}'
        self[sdf_name] = df_clim.mean().to_frame().T

        ## Add here min/max/percentiles

    def calc_clim_stats(self,percentiles=[0.1,0.9]):
        """Calculate the occuring minimum and maximum and percentile of data
        This routine calculates the minimum and maximum occuring in the data
        It creates a DataFrame attached to the class with suffixes _min _max _perc_low _perc_high,
        where _perc_low and _perc_high are the values given percentiles (e.q. _10 and _90 for 10th and 90th percentile) 
        Arguments:
        --------------
            percentile: list with percentiles (default: [10,90])
        """

        # monthly

        ## yearly
        #df_stats = self.df_yearly.min().to_frame().T.add_suffix('_Min')
        #df_stats = df_stats.merge(self.df_yearly.idxmin().to_frame().T.add_suffix('_Min_Datum'),left_index=True,right_index=True)
        #df_stats = self.df_yearly.max().to_frame().T.add_suffix('_Max')
        #df_stats = df_stats.merge(self.df_yearly.idxmax().to_frame().T.add_suffix('_Max_Datum'),left_index=True,right_index=True)
        ##df_maxval.T.merge(df_maxidx.T.add_suffix('_Datum'),left_index=True,right_index=True)
        #self['df_yearly_stats'] = df_stats

        if(self.lcalc):
            # daily
            self['df_daily_clim_stats'] = self.calc_daily_clim_stats(self.df_daily,percentiles=percentiles)

        if(self.lcalc):
            # monthly
            self['df_monthly_clim_stats'] = self.calc_monthly_clim_stats(self.df_monthly,percentiles=percentiles)

    def calc_daily_indicators(self,df_in, col_max_temp, col_min_temp, col_precip):
        """
            Calculates days within month which are over a certain threshold
            ice days, frost days, summer day, hot day, rainy day

        Arguments:
            df_in: DataFrame with the data (index must be date on daily basis)
        """

        # daily sum up

        self['df_daily_clim_stats'] = None


    def calc_daily_clim_stats(self,df_in,percentiles=None):
        """This routine calculates climatolocal percentiles and maximum each day of the year
           It discard Feb 29. So the return is 365 days. It does a loop over the days
           because groupby takes leap years into account and therefore leads to 366 days
           This approach may take more time than for example regroup
        Arguments:
        -------------------
            df_in:  DataFrame with data (index must be date)
            percentiles: quantile values between 0 and 1. Default is None, so no quantiles calculated
        """

        i = 1
        for date in self.nonleap_range:
            cond = (df_in.index.month == date.month) & (df_in.index.day == date.day)
            df_minmax = df_in[cond].agg(['max','min'])
            df_minmax['DOY'] = np.full(2,i)
            try:
                #df_out = df_out.append(df_minmax,ignore_index=True)
                #df_out = df_out.append(df_minmax)
                df_out = pd.concat([df_out,df_minmax])
            except: # create the DataFrame
                df_out = df_minmax.copy()

            # as DataFrame should be created already just append percentiles
            if(percentiles is not None):
                df_percentiles = df_in[cond].quantile(percentiles,numeric_only=True)
                df_percentiles['DOY'] = np.full(len(percentiles),i)
                #df_out = df_out.append(df_percentiles,ignore_index=True)
                #df_out = df_out.append(df_percentiles)
                df_out = pd.concat([df_out,df_percentiles])
            i += 1

        df_out.reset_index(inplace=True)
        df_out.rename(columns={'index':'stat'},inplace=True)
        return df_out

    def calc_monthly_clim_stats(self,df_in,percentiles=None):
        """This routine calculates climatolocal percentiles and maximum each month in year 
           It does a loop over the month
        Arguments:
        -------------------
            df_in:  DataFrame with data (index must be date)
            percentiles: quantile values between 0 and 1. Default is None, so no quantiles calculated
        """

        i = 1
        self.df_test = df_in
        for month in df_in.index.month.unique():
            cond = (df_in.index.month == month)
            df_minmax = df_in[cond].agg(['max','min'])
            df_minmax['Monat'] = np.full(2,i)
            try:
                #df_out = df_out.append(df_minmax)
                df_out = pd.concat([df_out,df_minmax])
            except:
                df_out = df_minmax.copy()
            
            # as DataFrame should be created already just append percentiles
            if(percentiles is not None):
                df_percentiles = df_in[cond].quantile(percentiles)
                df_percentiles['Monat'] = np.full(len(percentiles),i)
                #df_out = df_out.append(df_percentiles)
                df_out = pd.concat([df_out,df_percentiles])
            i += 1 

        df_out.reset_index(inplace=True)
        df_out.rename(columns={'index':'stat'},inplace=True)
        return df_out

    def calc_daily_clim(self,df_in):
        """This routine calculates the climatolocial mean on each day of the year
           It discard Feb 29. So the return is 365 days. It does a loop over the days
           because groupby takes leap years into account and therefore leads to 366 days
           This approach may take more time than for example regroup
        Arguments:
        -------------------
            df_in:  DataFrame with data (for example subdata with 30 years of data)
        """

        lfirst = True
        for date in self.nonleap_range:
            cond = (df_in.index.month == date.month) & (df_in.index.day == date.day)
            if(lfirst):
                df_out = df_in[cond].mean().to_frame().T
                lfirst = False
                self.df_out = df_out
            else:
                df_tmp = df_in[cond].mean().to_frame().T
                df_out = pd.concat([df_out,df_tmp],ignore_index=True)

        df_out.index      = self.nonleap_range.dayofyear
        df_out.index.name = 'DOY'
        return df_out


    def add_df_statid(self,df_in):
        """Adds Station ID to DataFrame"""
        df_in.insert(0,'STATIONS_ID',np.full((len(df_in)),int(self.key)))
        return df_in

    def add_df_ind_col(self,df_in,pos=1,colname=None):
        """Add index to colum
        df_in:   DataFrame
        pos:     position to insert index (default 1)
        colname: If the columname should differ from index name
        """
        if(colname is None):
            colname = df_in.index.name
        df_in.insert(pos,colname,df_in.index.values)
        return df_in

    def extract_subdata_year(self,df_in,years,yeare):
        """Extract subdata in given DataFrame only year is taken into account
           df_in:  DataFrame to extract subdata
           years:  First year which should be taken into account
           yeare:  Last year which should be taken into account
           returns DataFrame
        """

        # Check if yeare is greater than years
        # if not swap them
        if(yeare < years):
            years, yeare = yeare, years

        return df_in[(df_in.index.year >= years) & (df_in.index.year <= yeare)]

    def calculate_climatic_normals(self,
                                   clim_norms=None):
        """Loops over different climatic normal periods
           clim_norms: List which defines always defines the first year of climatic normal period
                       So if a list of [1961,1991] is given it calculates two 30 year normal periods
                       --> 1961 - 1990 and 1991 - 2020
                       Default is following list [1961,1971,1981,1991]
        """

        if(self.lcalc):
            if(clim_norms is None):
                clim_norms = self.default_clim_norms

            for years in clim_norms:
                yeare = years + 29 #
                if(self.ldebug):
                    print(f'Calculate normal period: {years} - {yeare}')
                self.calc_clim_mean(years,yeare)

    def prepare_to_sqlite(self,
                          clim_norms=None):
        """Prepare Dataframe to write to sqlite database"""

        if(clim_norms is None):
            clim_norms = self.default_clim_norms

        for years in clim_norms:
            # daily
            sdf_name = f'df_daily_c_{years}'
            self[sdf_name].index.name = 'Tag'
            self[sdf_name].reset_index(inplace=True)
            self[sdf_name] = self.add_df_statid(self[sdf_name])

            #monthly
            sdf_name = f'df_monthly_c_{years}'
            self[sdf_name].index.name = 'Monat'
            self[sdf_name].reset_index(inplace=True)
            self[sdf_name] = self.add_df_statid(self[sdf_name])
            
            #yearly
            sdf_name = f'df_yearly_c_{years}'
            self[sdf_name].index.name = 'Jahr'
            self[sdf_name].reset_index(inplace=True)
            self[sdf_name] = self.add_df_statid(self[sdf_name])
            self[sdf_name]['Jahr'] = years
            #self[sdf_name].drop(columns=['index'],inplace=True)

        self.df_daily.reset_index(inplace=True)
        self.df_daily = self.add_df_statid(self.df_daily)
        self.df_monthly.reset_index(inplace=True)
        self.df_monthly = self.add_df_statid(self.df_monthly)
        self.df_yearly.reset_index(inplace=True)
        self.df_yearly = self.add_df_statid(self.df_yearly)

        try:
            self.df_daily_clim_stats = self.add_df_statid(self.df_daily_clim_stats)
        except:
            write_exc_info()

        try:
            self.df_monthly_clim_stats = self.add_df_statid(self.df_monthly_clim_stats)
        except:
            write_exc_info()

        self.lsqlite_prep = True

    def write_all_df_sqlite(self,key,aggregation=['monthly','yearly'],force=False):
        """Loop over DataFrames containing aggregated data
        Arguments:
        -------------------------------------
            key (int): Station ID
            aggregation (list): List of aggregation types to write (default ['monthly', 'yearly'])
            force (bool): Force to write data without using prepare_to_sqlite
        """

        if(not self.lsqlite_prep and not force):
            print("execute prepare_to_sqlite first or use force=True")
            return

    def delete_clim_sqlite(self,clim_norms=None):
        """Loop over all tables containing climate data and delete them
        Arguments:
        -------------------------------------
            clim_norms: Specify special normal periods as desired --> starting year as list
        """

        if(clim_norms is None):
            clim_norms = self.default_clim_norms

        filename = self.base_dir+STATION_FOLDER+SQLITEFILESTAT
        
        for years in clim_norms:
            #delete daily vals
            if(self.ldebug):
                print("Delete daily clim vals")
            try:
                tabname  = f'{self.tabname_c}_daily_{years}'
                drop_table(tabname,filename)
            except:
                write_exc_info()

            # delete monthly vals
            if(self.ldebug):
                print("Delete monthly clim vals")
            try:
                tabname  = f'{self.tabname_c}_monthly_{years}'
                drop_table(tabname,filename)
            except:
                write_exc_info()

            #delete yearly vals
            if(self.ldebug):
                print("Write yearly clim vals")
            try:
                tabname  = f'{self.tabname_c}_yearly_{years}'
                drop_table(tabname,filename)
            except:
                write_exc_info()

        try:
            tabname  = f'{self.tabname_c}_daily_climstats'
            drop_table(tabname,filename)
        except:
            write_exc_info()

        try:
            tabname  = f'{self.tabname_c}_monthly_climstats'
            drop_table(tabname,filename)
        except:
            write_exc_info()

    def write_all_clim_sqlite(self,key,clim_norms=None,force=False):
        """Loop over DataFrames containing climatic normal periods
        Attention prepare_to_sqlite should be performed prior!
        clim_norms: Specify special normal periods as desired --> starting year as list
        """

        if(not self.lsqlite_prep and not force):
            print("execute prepare_to_sqlite first or use force=True")
            return
        
        if(clim_norms is None):
            clim_norms = self.default_clim_norms

        for years in clim_norms:
            #write daily vals
            if(self.ldebug):
                print("Write daily clim vals")
            sdf_name = f'df_daily_c_{years}'
            tabname  = f'{self.tabname_c}_daily_{years}'
            self.write_clim_to_sqlite(self[sdf_name],key,tabname,'norm')

            #write monthly vals
            if(self.ldebug):
                print("Write monthly clim vals")
            sdf_name = f'df_monthly_c_{years}'
            tabname  = f'{self.tabname_c}_monthly_{years}'
            self.write_clim_to_sqlite(self[sdf_name],key,tabname,'norm')

            #write yearly vals
            if(self.ldebug):
                print("Write yearly clim vals")
            sdf_name = f'df_yearly_c_{years}'
            tabname  = f'{self.tabname_c}_yearly_{years}'
            self.write_clim_to_sqlite(self[sdf_name],key,tabname,'norm')

        try:
            if(self.ldebug):
                print("Write daily clim stats")
            sdf_name = 'df_daily_clim_stats'
            tabname  = f'{self.tabname_c}_daily_climstats'
            self.write_clim_to_sqlite(self[sdf_name],key,tabname,'climstats')
        except:
            write_exc_info()
        try:
            if(self.ldebug):
                print("Write monthly clim stats")
            sdf_name = 'df_monthly_clim_stats'
            tabname  = f'{self.tabname_c}_monthly_climstats'
            self.write_clim_to_sqlite(self[sdf_name],key,tabname,'climstats')
        except:
            write_exc_info()


    def write_clim_to_sqlite(self,df_in,key,
                             tablename,ctype=None):
        """Write sqlite data to 
        df_in: prepared DataFrame --> prepare_to_sqlite should be performed before
        key: Station ID
        tablename: Table name to write
        """

        # construct filename
        filename = self.base_dir+STATION_FOLDER+SQLITEFILESTAT

        con = open_database(filename)

        if(check_for_table(con,tablename)):
            lcreate=False
        else:
            lcreate=True

        if(lcreate):
            create_table_res_climstats(con,self.resolution,self.par,tablename,ctype=ctype)

        write_sqlite_data(df_in, con, tablename,debug=self.ldebug)

        con.close()
    
    def combine_df_clim_class(self,station_data_class,clim_norms=None):
        """This combines climate normal Dataframes from another instance
        station_data_class: This class
        """

        if(clim_norms is None):
            clim_norms = self.default_clim_norms

        for years in clim_norms:
            #combine daily vals
            if(self.ldebug):
                print("combine daily clim vals")
            sdf_name = f'df_daily_c_{years}'
            tabname  = f'{self.tabname_c}_daily_{years}'
            self[sdf_name] = self[sdf_name].merge(station_data_class[sdf_name],left_index=True,right_index=True)

            #combine monthly vals
            if(self.ldebug):
                print("combine monthly clim vals")
            sdf_name = f'df_monthly_c_{years}'
            tabname  = f'{self.tabname_c}_monthly_{years}'
            self[sdf_name] = self[sdf_name].merge(station_data_class[sdf_name],left_index=True,right_index=True)

            #combine yearly vals
            if(self.ldebug):
                print("combine yearly clim vals")
            sdf_name = f'df_yearly_c_{years}'
            tabname  = f'{self.tabname_c}_yearly_{years}'
            self[sdf_name] = self[sdf_name].merge(station_data_class[sdf_name],left_index=True,right_index=True)

    def combine_df_clim_stats(self,station_data_class):
        """Combines climate daily statistics from another class instance
        Arguments:
        ----------------------------
            station_data_class: This class with calculated df_daily_clim_stats
        """

        sdf_name = 'df_daily_clim_stats'
        self[sdf_name] = self[sdf_name].merge(station_data_class[sdf_name],left_index=True,right_index=True)
        # drop _y entries
        try:
            self[sdf_name].drop(list(self[sdf_name].filter(regex='_y')),axis=1,inplace=True)
        except:
            pass
        # strip _x suffixes
        try:
            self[sdf_name].columns = self[sdf_name].columns.str.rstrip("_x")
        except:
            pass

# -*- coding: utf-8 -*-
"""
Created on Sat Jun 06 17:32:40 2021

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: some helper functions """

from os import makedirs, system, popen, getcwd, listdir, chdir
from os.path import exists, isfile, join, split
import glob
from sys import stdout, exc_info
import pandas as pd
import numpy as np
import datetime
import zipfile
import sqlite3
import sqlalchemy as sa
from dotenv import dotenv_values
from ..helper.postgres import PostgresHandler
from ..constants.constpar import (STATION_VAR_DICT, STATION_INT_VARS, 
                                  STATION_BIGINT_VARS,
                                  STATION_TEXT_VARS, STATION_PRIMARY_KEYS,
                                  STATION_NOT_NULL, STATION_DATE_END_VARS,
                                  REGAVG_PRIMARY_KEYS,
                                  DATENAMESTAT,DATENAMESTATEND,
                                  ALLOWED_DRIVERS, POSTGRES_DRIVER, SQLITE_DRIVER)

def check_create_dir(dir_in):
    """ Simple check if dir exists, if not create it """

    if not exists(dir_in):
        makedirs(dir_in)

def read_station_list(dir_in,file_in,debug=False):
    """ Reads DWD station list metadata """

    if(debug):
        print("Open file {} and read station list".format(dir_in+file_in))

    check_file_encoding(dir_in,file_in)

    # First Line and Line with ------ ----- are skipped
    df_out = pd.read_fwf(dir_in+file_in,skiprows=[0,1],
                          names=['Stations_id', 'von', 'bis', 'hoehe','lat','lon','name','bundesland','abgabe']) 
    df_out['Stations_id'] = df_out['Stations_id'].apply(lambda x: '{0:0>5}'.format(x))
    df_out['von'] = pd.to_datetime(df_out['von'],format="%Y%m%d")
    df_out['bis'] = pd.to_datetime(df_out['bis'],format="%Y%m%d")
    df_out.set_index('Stations_id', inplace=True)


    if(debug):
        print("{} stations read".format(df_out.shape[0]))

    return df_out

def extract_yyyymmdd(date,sep=''):                                                                                                                                                                                                           
    """ extracts hour day month year from string of yyyymmddhh or with seperator                                      
    and returns it as string. 
    if the date is seperated specify the seperator:                                                                   
        for exammple: sep='.' in case of a dot as seperator                                                           
    """         
                
    if(sep != ''):
        date = date.replace(sep,"") # remove seperator
                                         
    year  = date[0:4]                    
    month = date[4:6]                                                                                                 
    day   = date[6:8]
        
    return year, month, day

def extract_yyyymmddhh(date,sep='',l_minutes=False):
    """ extracts hour day month year from string of yyyymmddhh or with seperator
    and returns it as string.
    if the date is seperated specify the seperator:
        for exammple: sep='.' in case of a dot as seperator
    """

    if(sep != ''):
        date = date.replace(sep,"") # remove seperator

    year  = date[0:4]
    month = date[4:6]
    day   = date[6:8]
    hour  = date[8:10]
    minutes = date[10:12]

    if(l_minutes):
        return year, month, day, hour, minutes
    else:
        return year, month, day, hour

def check_file_encoding(dir_in,fil_in,return_enc=False,debug=False):
    """ Checks file encoding and change it """

    if(debug):
        print("Check File Encoding")
        print(dir_in)
        print(fil_in)

    fil_open = dir_in+fil_in
    f = popen('file -i {}'.format(fil_open))
    output = f.read()
    #print(output)
    #f_index = encoding.index('charset')
    s_index = output.index('=') # find encoding
    encoding = output[s_index+1:].strip()
    encoding.replace(" ","")

    if(not return_enc):
        fil_temp = dir_in+'tmp'
        system('iconv -f {} -t utf-8 {} > {}'.format(encoding,fil_open,fil_temp))
        system('mv {} {}'.format(fil_temp,fil_open))
    #print(encoding)

    if(return_enc):
        return encoding

def update_progress(progress):
    """ Display simple progress bar 
    """
    barLength = 10  # modify this to change length of the progress bar

    status = ""
    if(isinstance(progress, int)):
        progress = float(progress)
    if(not isinstance(progress, float)):
        progress = 0
        status = "error: progress var must be float\r\n"                             
    if progress < 0:                                                            
        progress = 0
        status = "Halt...\r\n"                                                      
    if progress >= 1:                                                                                     
        progress = 1
        status = "Done...\r\n"
    block = int(round(barLength*progress))
    text = "\rPercent: [{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), round(progress*100), status)
    stdout.write(text)        
    stdout.flush()    

def unzip_file(fil_in,dir_in='',dir_to=''):
    """ Unzips file """

    if(dir_to == ''):
        dir_to = dir_in

    if(dir_in == '' and dir_to == ''): #expecting absolute path
        zip_ref = zipfile.ZipFile(fil_in,'r')
        zip_ref.extractall()
        zip_ref.close()
    elif(dir_in == '' and dir_to != ''):
        try:
            zip_ref = zipfile.ZipFile(fil_in, 'r')
            zip_ref.extractall(dir_to)
            zip_ref.close()
        except:
            print("File is not readible")
    elif(dir_in != '' and dir_to == ''):
        zip_ref = zipfile.ZipFile(dir_in+'/'+fil_in, 'r')
        zip_ref.extractall()
        zip_ref.close()
    else:
        zip_ref = zipfile.ZipFile(dir_in+'/'+fil_in, 'r')
        zip_ref.extractall(dir_to)
        zip_ref.close()

def list_files(dir_in, ending='',only_files=False):
    """ List files in directory 
        ending: if specified only files with this ending are returned
    """

    if(ending != ''):
        if(ending[0:1] != '*.'):
                ending = '*.'+ending

        if(only_files):
            dir_pwd = getcwd()
            check_create_dir(dir_in)
            chdir(dir_in)
            r_files = glob.glob(ending)
            chdir(dir_pwd)
        else:
            r_files = glob.glob(dir_in+'/'+ending)
    else:
        r_files = [f for f in listdir(dir_in) if isfile(join(dir_in, f))]

    return r_files


# math related
def moving_average(x, w):
    return np.ma.convolve(x, np.ma.ones(w), 'valid') / w

def open_database(filename=None,
                  ldbsave=False,
                  driver=SQLITE_DRIVER,
                  dbschema=None,
                  postgconfig=None,
                  config_dir=None,
                  postfile=".env",
                  return_engine=False,
                  debug=False):
    """Open Database
    Arguments:
    ------------------------------------
        filename: File Name of SQLITE Database (Default None and and if None it returns without doing anything)
        ldbsave:  Bool if DB can be savely used, if not do nothing
        driver:   Driver to use 
        dbschema: Schema to use
        postgconfig: Configuration Dictionary for postgres 
        config_dir: Directory where config file is stored
        postfile: location of .env File or database.ini File
        debug:    Some additional output
    returns
        con:      Sqlite connection
    """

    if(not ldbsave):
        if(debug):
            print("db seems not save to use return")
        return 
    
    if(driver in [SQLITE_DRIVER]):
        con = sqlite3.connect(filename,uri=True)

        con.execute('''PRAGMA synchronous = EXTRA''')
        con.execute('''PRAGMA journal_mode = WAL''')
        con.commit()
    elif(driver in ['PostgreSQL']):
        if(postgconfig is None):
            if(debug):
                print("PostgreSQL. Using following configfile: ")
                print(config_dir, postfile)
            if(config_dir is None):
                postgres = PostgresHandler(file_location=postfile,dbschema=dbschema)
            else:
                postgres = PostgresHandler(file_location=config_dir+postfile,dbschema=dbschema)
        else:
            postgres = PostgresHandler(config=postgconfig,dbschema=dbschema)

        postgres.connect()
        if(return_engine):
            return postgres.engine
        con = postgres.engine.connect()
    else:
        return {}

    return con

def close_database(con,
                   driver=SQLITE_DRIVER,
                   debug=False):
    """
        Closes connection of database
        con:  Connection stream
        driver:   Driver to use 
        debug:    Some additional output
    """

    if(debug):
        print("Close Connection for " + driver)

    if(driver in [SQLITE_DRIVER]):
        con.close()
    elif(driver in ['PostgreSQL']):
        try:
            con.dispose()
        except:
            con.close()

def check_drivers(driver):
    """
        Checks if driver is ok to use
    """

    lallowed = driver in ALLOWED_DRIVERS

    if(not lallowed):
        print(f"{driver} is not implemented at the moment. Use Following:")
        print(ALLOWED_DRIVERS)

    return lallowed

def create_table_regavg(con,
                        resolution=None,
                        par=None,
                        keys=None,
                        debug=False):
    """
        Create table according to given resolution and parameter
        regional average
    Arguments:
    ------------------------------------
        con: connection to database
        resolution: string --> defines resolution (e.g. 10_minutes, hourly, daily...)
        par: string --> parameter (e.g. air_temperature, precipitation, etc)
        keys: list --> contains column names from table
        debug: bool --> some extra output for debugging
    """

    if(resolution is None):
        print("No resolution given, return")
        return

    if(par is None):
        print("No parameter given, return")
        return

    if(keys is None):
        print("No columns given, return")
        return
    
    create_stmt = create_statement(resolution,par,keys)
    print(create_stmt)

    con.execute(create_stmt)
    con.commit()

def create_table_res(con,
                 resolution=None,
                 par=None,
                 driver=SQLITE_DRIVER,
                 schema=None,
                 debug=False):
    """
        Create table according to given resolution and parameter
    Arguments:
    ------------------------------------
        con: connection to database
        resolution: string --> defines resolution (e.g. 10_minutes, hourly, daily...)
        par: string --> parameter (e.g. air_temperature, precipitation, etc)
        debug: bool --> some extra output for debugging
    """

    if(resolution is None):
        print("No resolution given, return")
        return False

    if(par is None):
        print("No parameter given, return")
        return False

    lwrite_generated = True

    if(driver in [POSTGRES_DRIVER]):
        # get version
        result = con.execute(sa.text("select version()"))
        for data in result:
            pg_version_nr = data[0].split(" ")[1]

        # below version 12 generated columns are not possible, don't write them 
        lwrite_generated = pg_version_nr > '12'

    create_stmt = create_statement(resolution,par, driver=driver, lwrite_generated=lwrite_generated)

    if(driver in [SQLITE_DRIVER]):
        con.execute(create_stmt)
    else:
        con.execute(sa.text(create_stmt))
    con.commit()
    return True

def create_table_res_climstats(con,
                               resolution,
                               par,
                               tablename,
                               ctype=None,
                               debug=False):
    """
        Create table of climstats according given resolution and parameter
    Arguments:
        con: connection to database
        tablename: str --> tablename to be created
        debug: bool --> some extra output for debugging
    """

    create_stmt = create_statement(resolution=resolution,par=par,
                                   tabname=tablename,lclimstat=True,ctype=ctype)
    print(tablename)
    print(create_stmt)
    con.execute(create_stmt)
    con.commit()

def drop_table(tabname=None,
               filename=None,
               debug=False):
    """Drop table with given tabname
    Arguments:
    ------------------------------------
        tabname: Table to delete (Default None and if None it returns without doing anything)
        filename: File Name of SQLITE Database (Default None and and if None it returns without doing anything)
        debug:    Some additional output
    """
    if(filename is None):
        print("No filename given")
        return

    if(tabname is None):
        print("No tablename given")
        return

    if(debug):
        print(f"Try to open: {filename}")

    con = open_database(filename,debug=debug) 
    sqlexec = f"DROP TABLE {tabname}"
    con.execute(sqlexec)
    con.commit()
    con.close()

def delete_sqlite_where(tabname=None,
                        filename=None,
                        col=None,
                        value=None,
                        cond=None,
                        debug=False):
    """ Delete data with where condition
    tabname: Table to write to (Default None and if None it returns without doing anything)
    filename: File Name of SQLITE Database (Default None and and if None it returns without doing anything)
    col:      Column Name
    cond:     Condition where data is deleted
    debug:    Some additional output
    """

    if(filename is None):
        #filename = 'file:{}?cache=shared'.format(self.pathdlocal+SQLITEFILESTAT)
        print("No filename given")
        return

    if(tabname is None):
        print("No tablename given")
        return

    if(debug):
        print(f"Try to open: {filename}")

    con = open_database(filename,debug=debug) 
    sqlexec = f"DELETE from {tabname} WHERE {col} {cond} {value}"

    if(debug):
        print(f"Execute: {sqlexec}")

    con.execute(sqlexec)
    con.commit()

    con.close()

def write_sqlite_data(data,con, table, driver,
                      debug=False):
    """
        Write data to sqlite
    Arguments:
        data: dataframe
        con:  Connection
        driver: to use
        table: tablename
    """

    if(debug):
        print("Write data direct")

    if(driver in [SQLITE_DRIVER]):
        cur = con.cursor()

        insert_stmt = f"INSERT OR REPLACE INTO {table} ("
    else:
        insert_stmt = f"INSERT INTO {table} ("
    
    insert_stmt_t = "VALUES ("

    for col in data:
        insert_stmt   += f"{col}, "
        if(driver in [SQLITE_DRIVER]):
            insert_stmt_t += "?, " # TODO change if all is transfered to sqlalchemy
        else:
            insert_stmt_t += f":{col}, "
    
    # remove trailing comma
    insert_stmt  = insert_stmt[:-2]
    insert_stmt_t = insert_stmt_t[:-2]
    insert_stmt   += ") "
    insert_stmt_t += ");"
    insert_stmt += insert_stmt_t

    if(driver in [POSTGRES_DRIVER]):
        insert_stmt = insert_stmt[:-1]
        inspector = sa.Inspector(con)
        pk_keys = inspector.get_pk_constraint(table_name=table)['constrained_columns']
        insert_stmt += f" ON CONFLICT {tuple(pk_keys)} ".replace('\'','')
        insert_stmt += f" DO UPDATE SET "
        for col in data:
            insert_stmt += f"{col} = EXCLUDED.{col}, "
        insert_stmt = insert_stmt[:-2]
        insert_stmt += ";"

    if(driver in ['SQLite']):
        cur.executemany(insert_stmt,data.values.tolist())
        con.commit()
    else:
        con.execute(sa.text(insert_stmt), data.to_dict(orient='records'))
        con.commit()
            

def create_statement(resolution=None,par=None,
                     lclimstat=False,keys=None,
                     ctype=None,tabname=None,
                     lwrite_generated=True,
                     driver='SQLite'):
    """
    Creates Create Statement of table
    Arguments:
        resolution: string --> defines resolution (10_minutes, hourly etc)
        par: string --> defines parameter (air_temperature, precipitation etc)
        climstat: bool --> indicate that climstats table is to be created
        keys: stringlist --> keys which are used for regional average; default None 
        ctype: string --> is used to determine if climstats or norm should be created
    """

    if(resolution is None and par is not None):
        print("Create Statement, no resolution specified, return")
        return -1

    if(par is None and resolution is not None):
        print("Create Statement, no par specified, return")
        return -1
    
    if(par is None and resolution is None and tabname is None):
        print("Not even a table name (tabname) is specified, return")
        return -1
    
    # init create statement
    stmt = 'CREATE TABLE IF NOT EXISTS ' 
    if(tabname is None):
        stmt += f'{par}_{resolution} ('
    else:
        stmt += f'{tabname} ('

    # vars which are primary key are temporary stored here and later added
    # this is necessary in case of multiple keys
    prim_keys = []
    if(keys is None):
        if(lclimstat):
            if(ctype == 'climstats'):
                stmt += 'stat TEXT, '
                if('monthly' in tabname):
                    stmt += 'Monat INT, '
                elif('yearly' in tabname):
                    stmt += 'Jahr INT, '
                else:
                    stmt += 'DOY INT, '
            elif(ctype == 'norm'):
                if('monthly' in tabname):
                    stmt += 'Monat INT, '
                elif('yearly' in tabname):
                    stmt += 'Jahr INT, '
                else:
                    stmt += 'Tag INT, '

        # loop over variables ## TODO Verhindere das MESS_DATUM bei norm und climstats im CREATE STATEMENT auftaucht
        for var in STATION_VAR_DICT[resolution][par]:
            loverwrite_not_null = False

            #print(var, lclimstat)
            if(lclimstat):
                luse_int_var = not (var in [DATENAMESTAT, DATENAMESTATEND])
            else:
                luse_int_var = True

            loverwrite_not_null = True

            if(var in STATION_INT_VARS):
                # avoid that MESS_DATUM is used in case of climstats
                if(luse_int_var):
                    if(driver in [SQLITE_DRIVER]):
                        stmt += f'{var} INT'
                    else:
                        if(var in STATION_BIGINT_VARS):
                            stmt += f'{var} BIGINT'
                        else:
                            stmt += f'{var} INT'

                #stmt += f'{var} INT'
                loverwrite_not_null = luse_int_var
            elif(var in STATION_TEXT_VARS):
                stmt += f'{var} TEXT'
            else:
                stmt += f'{var} REAL'

            if(var in STATION_NOT_NULL and loverwrite_not_null):
                stmt += ' NOT NULL'

            if(var in STATION_PRIMARY_KEYS):
                prim_keys.append(var)

            if(loverwrite_not_null):
                stmt += ', '

        if(lclimstat):
            prim_keys.remove(DATENAMESTAT)
            if(ctype == 'climstats'):
                prim_keys.append('stat')
                if('monthly' in tabname):
                    prim_keys.append('Monat')
                elif('yearly' in tabname):
                    prim_keys.append('Jahr')
                else:
                    prim_keys.append('DOY')
            elif(ctype == 'norm'):
                if('monthly' in tabname):
                    prim_keys.append('Monat')
                elif('yearly' in tabname):
                    prim_keys.append('Jahr')
                else:
                    prim_keys.append('Tag')

        # add GENERATED COLUMNS 
        # we also have to add the correct name of date column
        if(not lclimstat and lwrite_generated):
            if(par in STATION_DATE_END_VARS):
                DATE_USE_NAME = DATENAMESTATEND
            else:
                DATE_USE_NAME = DATENAMESTAT

            # Year
            if(driver in [SQLITE_DRIVER]):
                stmt += f'Jahr INT GENERATED ALWAYS AS (substr({DATE_USE_NAME},1,4)) STORED, '
            else:
                #stmt += f'Jahr INT GENERATED ALWAYS AS (substring({DATE_USE_NAME} FROM 11 FOR 2)) STORED, '
                if(resolution in ['10_minutes']):
                    factor = 10000000000
                elif(resolution in ['daily']):
                    factor = 1000000

                stmt += f'Jahr INT GENERATED ALWAYS AS (MESS_DATUM / {factor}) STORED, '
            # Month
            if(driver in [SQLITE_DRIVER]):
                stmt += f'Monat INT GENERATED ALWAYS AS (substr({DATE_USE_NAME},5,2)) STORED, '
            else:
                #stmt += f'Monat INT GENERATED ALWAYS AS (substring({DATE_USE_NAME} FROM 5 FOR 2)) STORED, '
                if(resolution in ['10_minutes']):
                    factor = 100000000
                elif(resolution in ['hourly']):
                    factor = 10000
                elif(resolution in ['daily']):
                    factor = 100
                stmt += f'Monat INT GENERATED ALWAYS AS ((MESS_DATUM / {factor}) % 100) STORED, '
            # Day
            if(driver in [SQLITE_DRIVER]):
                stmt += f'Tag INT GENERATED ALWAYS AS (substr({DATE_USE_NAME},7,2)) STORED, '
            else:
                #stmt += f'Tag INT GENERATED ALWAYS AS (substring({DATE_USE_NAME} FROM 7 FOR 2)) STORED, '
                if(resolution in ['10_minutes']):
                    factor = 1000000
                elif(resolution in ['hourly']):
                    factor = 10000
                elif(resolution in ['daily']):
                    factor = None

                if(factor is None):
                    stmt += f'Tag INT GENERATED ALWAYS AS (MESS_DATUM % 100) STORED, '
                else:
                    stmt += f'Tag INT GENERATED ALWAYS AS ((MESS_DATUM / {factor}) % 100) STORED, '

            if(resolution in ['hourly','10_minutes']):
                # Hour
                if(driver in [SQLITE_DRIVER]):
                    stmt += f'Stunde INT GENERATED ALWAYS AS (substr({DATE_USE_NAME},9,2)) STORED, '
                else:
                    if(resolution in ['10_minutes']):
                        factor = 10000
                    elif(resolution in ['hourly']):
                        factor = None
                    #stmt += f'Stunde INT GENERATED ALWAYS AS (substring({DATE_USE_NAME} FROM 9 FOR 2)) STORED, '
                    if(factor is None):
                        stmt += f'Stunde INT GENERATED ALWAYS AS (MESS_DATUM % 100) STORED, '
                    else:
                        stmt += f'Stunde INT GENERATED ALWAYS AS ((MESS_DATUM / {factor}) % 100) STORED, '
            if(resolution in ['10_minutes']):
                # Minutes
                if(driver in [SQLITE_DRIVER]):
                    stmt += f'Minuten INT GENERATED ALWAYS AS (substr({DATE_USE_NAME},11,2)) STORED, '
                else:
                    factor = 100
                    stmt += f'Minuten INT GENERATED ALWAYS AS ((MESS_DATUM / {factor}) % 100) STORED, '
                #    stmt += f'Minuten INT GENERATED ALWAYS AS (substring({DATE_USE_NAME} FROM 11 FOR 2)) STORED, '
    else:
        for key in keys:
            if(key in ['autumn','spring','winter','summer','season']):
                stmt += 'season TEXT'
            elif(key in ['Jahr','Monat']):
                stmt += f'{key} INT'
            else:
                stmt += f'{key} REAL'

            stmt += ', '
            if(key in REGAVG_PRIMARY_KEYS):
                prim_keys.append(key)

    if(par in ['regavg']): # do not in station data!
        stmt = stmt.replace('/','_') 
    stmt = stmt.replace('-','_')

    # are there primary keys? if so add them
    if(len(prim_keys) > 0):
        stmt += 'PRIMARY KEY('
        for var in prim_keys:
            stmt += f'{var}, '
        
        stmt = stmt[:-2]
        stmt += ')'
    else:
        # otherwise only remove last trailing comma
        stmt = stmt[:-2]

    # add bracket
    stmt += ')'

    return stmt

def write_sqlite(df_in,key,
              tabname=None,
              filename=None,
              linsertrepl=False,
              debug=False):
    """ Save data to sqlite
    df_in:   DataFrame 
    key:     key of Station
    tabname: Table to write to (Default None and if None it returns without doing anything)
    filename: File Name of SQLITE Database (Default None and and if None it returns without doing anything)
    linsertrepl: Replaces old data if data is in the table
    debug:    Some additional output
    """

    if(filename is None):
        #filename = 'file:{}?cache=shared'.format(self.pathdlocal+SQLITEFILESTAT)
        print("No filename given")
        return

    if(tabname is None):
        print("No tablename given")
        return

    if(debug):
        print(f"Try to open: {filename}")

    con = open_database(filename)

    if(linsertrepl):
        # This drops data if table already exists and replaces the data
        df_in.to_sql(tabname, con, index=False, chunksize=1000, method='multi', if_exists='replace')
    else:
        # Data is just appended, if data exists
        df_in.to_sql(tabname, con, index=False, chunksize=1000, method='multi', if_exists='append')

    con.close()

def check_for_table(con,table, driver):
    """
        Checks connection if table exists and returns true if so, otherweise false
    Arguments:
        con: Connection
        table: string --> tablename
        driver: string --> driver which is used
    """

    if(driver in ['SQLite']):
        # create cursor object
        cur = con.cursor()

        # fetch table name
        listOfTable = cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name = '{table}'").fetchall()

        if(listOfTable == []):
            # no table present
            return False
        else:
            return True
    else:
        inspector = sa.Inspector(con)
        return table in inspector.get_table_names()

def write_exc_info():
    exc_type, exc_obj, exc_tb = exc_info()
    fname = split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)

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

def check_create_dir(dir_in):
    """ Simple check if dir exists, if not create it """

    if not exists(dir_in):
        makedirs(dir_in)

def read_station_list(dir_in,file_in,debug=False):
    """ Reads DWD station list metadata """

    if(debug):
        print("Open file {} and read station list".format(dir_in+file_in))                                

    check_file_encoding(dir_in,file_in)                                                        

    input_file = open(dir_in+file_in,"r")                                                           

    lines = input_file.readlines()                                                                                

    i = 0

    station_list = {}

    for line in lines:                                                                                            
        if(i == 0):
            header = line.split()                                                                                 
        elif(i > 1): # skip second line...                                                                        
            station_key = line[0:5]
            year, month, day = extract_yyyymmdd(line[6:14])                                                       
            b_date      = datetime.datetime(int(year), int(month), int(day))                                      
            year, month, day = extract_yyyymmdd(line[15:23])
            e_date      = datetime.datetime(int(year), int(month), int(day))                                      
            height      = line[34:38].replace(" ","")
            height      = np.float(height)                                                                        
            lat         = float(line[43:50])                                                                      
            lon         = float(line[53:60])                                                                      
            name        = line[61:101].rstrip()                                                                   
            state       = line[102:126].rstrip()                                                                  
            station_list[station_key] = {'von':b_date,'bis':e_date,                                               
                                     'hoehe':height,'lat':lat,'lon':lon,                                          
                                     'name':name,'bundesland':state}                                              
        i += 1                                                                                                    

    if(debug):
        print("{} stations read".format(i-2))                                                                     
        #print(station_list)                                                                                      

    return pd.DataFrame(station_list).T 

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

def write_sqlite(df_in,key,
              tabname=None,
              filename=None,
              debug=False):
    """ Save data to sqlite
    df_in:   DataFrame 
    key:     key of Station
    tabname: Table to write to (Default None and if None it returns without doing anything)
    filename: File Name of SQLITE Database (Default None and and if None it returns without doing anything)
    debug:    Some additional output
    """

    if(filename is None):
        #filename = 'file:{}?cache=shared'.format(self.pathdlocal+SQLITEFILESTAT)
        print("No filename given")
        return

    con = sqlite3.connect(filename,uri=True)

    if(tabname is None):
        print("No table name given")
        return

    lnew = True

    try:
        sqlexec = f"SELECT * from {tabname} WHERE STATIONS_ID = {key}"
        if(debug):
            print("Compare Sets")
            print(sqlexec)

        df_old = pd.read_sql_query(sqlexec,con)
        df_old.drop_duplicates(inplace=True)
        df_test = pd.concat([df_old,df_in]).drop_duplicates().reset_index(drop=True)
        df_test = df_test.merge(df_old,indicator=True,how='left').loc[lambda x : x['_merge']!='both']
        df_test.drop(columns='_merge',inplace=True)
        df_test.to_sql(tabname, con, if_exists="append", index=False,chunksize=1000,method='multi')
        lnew = False

    except Exception as Excp:
        lnew = True  # if above fails, there seems to be no tab according to this name
        if(debug):
            print(Excp)

    if(lnew):
        df_in.to_sql(tabname, con, index=False, chunksize=1000, method='multi')

    con.close()

def write_exc_info():
    exc_type, exc_obj, exc_tb = exc_info()
    fname = split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
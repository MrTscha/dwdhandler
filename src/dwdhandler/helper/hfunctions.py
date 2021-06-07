# -*- coding: utf-8 -*-
"""
Created on Sat Jun 06 17:32:40 2021

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: some helper functions """

from os import makedirs
from os.path import exists
import pandas as pd
import datetime

def check_create_dir(dir_in):
    """ Simple check if dir exists, if not create it """

    if not exists(dir_in):
        makedirs(dir_in)

def read_station_list(filelocation,debug=False):
    """ Reads DWD station list metadata """

    if(debug):
        print("Open file {} and read station list".format(filelocation))                                

    #self.check_file_encoding(dir_dwd_station,station_file)                                                        

    input_file = open(filelocation,"r")                                                           

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
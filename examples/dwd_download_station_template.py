#!/usr/bin/env python                                                                                                                                                                                                

import time
import sys
import getopt
import dwdhandler

def main(argv):

    # Some default values
    par = 'kl'
    period = 'now'
    resolution = 'daily'
    base_dir = '/home/tobias/workspace/DATA/DWD/'
    key = None

    try:
        opts, args = getopt.getopt(argv, "hp:r:d:v:k:", ["help","period=","resolution=","dir=","var=","key="])
    except getopt.GetoptError as err:
        usage()
        print(err)
        sys.exit(1)

    for opt, arg in opts:
        if(opt in ['-h','--help']):
            usage()
            sys.exit()
        elif(opt in ['-p','--period']):
            period = str(arg)
        elif(opt in ['-r','--resolution']):
            resolution = str(arg)
        elif(opt in ['-d','--directory']):
            base_dir = str(arg)
        elif(opt in ['-v','--var']):
            par = str(arg)
        elif(opt in ['-k','--key']):
            key = arg

    # start time 
    ts = time.time()

    dow_handler = dwdhandler.dow_handler(par=par,period=period,resolution=resolution,base_dir=base_dir)

    if(key is None):
        dow_handler.retrieve_dwd_station(list(dow_handler.df_station_list.index))
    else:
        dow_handler.retrieve_dwd_station([key])

    # end time
    te = time.time()

    print(f"Total: {round((te-ts)/60,1)} minutes")

def usage():
    """
        Some help information
    """

    print("-h print this help message \n")
    print("-p (--period) PERIOD; means 'now', 'recent' or 'historical'")
    print("-r (--resolution) resolution; Temporal resolution of dataset: '10_minutes', 'hourly', 'daily'")
    print("-d (--directory) directory; Define main directory of dwdhandler data")
    print("-v (--var) variable; Define variable to download; 'kl', 'precipitation', 'air_temperature', 'extreme_temperature'")
    print("-k (--key) station_id; Define the station id to be downloaded")

if __name__ == '__main__':
    main(sys.argv[1:])                   
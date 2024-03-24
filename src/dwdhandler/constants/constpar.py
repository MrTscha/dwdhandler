# -*- coding: utf-8 -*-
"""
Created on Sat Jun 06 17:32:40 2021

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: module containing some constants """

FILLVALUE = -999
ASCIIRASCRS = 'epsg:31467'
STATIONNAMEID = 'STATIONS_ID'
DATENAMESTAT = 'MESS_DATUM' # Name of time variable of station data
DATENAMESTATEND = 'MESS_DATUM_ENDE'
STATIONNAMEQUAL = 'QN'

RADIUSEARTH = 6371000

RASTERFACTDICT = {
    'air_temperature_max':0.1,
    'air_temperature_mean':0.1,
    'air_temperature_min':0.1,
    'evapo_p':0.1,
    'evapo_r':0.1
}

# Create dictionary

STATION_VAR_DICT = {
    '10_minutes':
    {'air_temperature':[STATIONNAMEID,DATENAMESTAT,'QN','PP_10','TT_10','TM5_10','RF_10','TD_10','eor'],
     'extreme_temperature':[STATIONNAMEID,DATENAMESTAT,'QN','TX_10','TX5_10','TN_10','TN5_10','eor'],
     'extreme_wind':[STATIONNAMEID,DATENAMESTAT,'QN','FX_10','FNX_10','FMX_10','DX_10','eor'], # DATENAMESTAT in this context is end of measurement
     'precipitation':[STATIONNAMEID,DATENAMESTAT,'QN','RWS_DAU_10','RWS_10','RWS_IND_10','eor'],
     'solar':[STATIONNAMEID,DATENAMESTAT,'QN','DS_10','GS_10','SD_10','LS_10','eor'],
     'wind':[STATIONNAMEID,DATENAMESTAT,'QN','FF_10','DD_10','eor']
    },
    'daily':
    {
        'kl':[STATIONNAMEID,DATENAMESTAT,'QN_3','FX','FM','QN_4','RSK','RSKF','SDK','SHK_TAG','NM','VPM','PM','TMK','UPM','TXK','TNK','TGK','eor']
    }
}

STATION_INT_VARS = [STATIONNAMEID,DATENAMESTAT,DATENAMESTATEND,STATIONNAMEQUAL,'QN_3','QN_4','RSKF']
STATION_TEXT_VARS = ['eor']
STATION_PRIMARY_KEYS = [STATIONNAMEID, DATENAMESTAT, DATENAMESTATEND]
STATION_NOT_NULL = [STATIONNAMEID, DATENAMESTAT, DATENAMESTATEND]
STATION_DATE_END_VARS = []


REGAVG_PRIMARY_KEYS = ['Jahr','season','Monat']
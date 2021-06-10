# -*- coding: utf-8 -*-
"""
Created on Sat Jun 06 17:32:40 2021

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: Local file data constants """

MAIN_FOLDER     = 'dwd_data/'
METADATA_FOLDER = 'metadata/'
STATION_FOLDER  = 'station_data/'
RASTER_FOLDER   = 'raster_data/'
SQLITEFILESTAT  = 'DWD_STATION.sqlite'

TIME_RESOLUTION_MAP = {
    'hourly': [['air_temperature',
                'cloud_type',
                'cloudiness',
                'dew_point',
                'extreme_wind',
                'moisture',
                'precipitation',
                'pressure',
                'soil_temperature',
                'solar',
                'sun',
                'visibility',
                'weather_phenomena',
                'wind',
                'wind_synop'
               ],
               ['historical',
               'recent']
               ],
    'daily':   [['kl',
                 'more_precip',
                 'soil_temperature',
                 'solar',
                 'water_equiv',
                 'weather_phenomena'
                ],
                ['historical',
                 'recent'
                ]
               ],
    'monthly': [['kl',
                 'more_precip',
                 'weather_phenomena'
                ],
                ['historical',
                 'recent'
                ]
               ]
}

NAME_CONVERSATION_MAP = {
    'air_temperature':'TU',
    'cloud_type':'CS',
    'cloudiness':'N',
    'dewpoint':'TD',
    'extreme_wind':'FX',
    'moisture':'TF',
    'precipitation':'RR',
    'pressure':'P0',
    'soil_temp':'EB',
    'soil_temperature':'EB',
    'solar':'ST',  
    'sun':'SD',
    'visibility':'VV',
    'weather_phenomena':'WW',
    'wind':'FF',
    'wind_synop':'F',
    'more_precip':'RR',
    'kl':'KL',
    '10_minutes':'10minutenwerte',
    '10_minutes_meta':'zehn_min',
    'hourly':'stundenwerte',
    'hourly_meta':'Stundenwerte',
    'daily':'tageswerte',
    'daily_meta':'Tageswerte',
    'monthly':'monatswerte',
    'monthly_meta':'Monatswerte',
    'meta_file_stationen':'_Beschreibung_Stationen.txt',
    'recent':'akt',
    'historical':'hist'
}
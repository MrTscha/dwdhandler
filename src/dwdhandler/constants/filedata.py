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

# This is needed for raster data, which is in month subdirectories
RASTERMONTHSUB = ['air_temperature_max','air_temperature_mean',
                  'air_temperature_min','precipitation','sunshine_duration']

# Raster is saved in netCDF File at DWD?
RASTERNCDICT   = ['Project_TRY','hyras_de']

RASTERMONTHDICT = ['01_Jan','02_Feb','03_Mar','04_Apr','05_May','06_Jun',
                   '07_Jul','08_Aug','09_Sep','10_Oct','11_Nov','12_Dec']

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

TIME_RASTER_MAP = {
    'monthly':[['air_temperature_max',
               'air_temperature_mean',
               'air_temperature_min',
               'drougt_index',
               'evapo_p',
               'evapo_r',
               'frost_depth',
               'hyras_de',
               'precipitation',
               'radiation_diffuse',
               'radiation_direct',
               'radiation_global',
               'regnie',
               'soil_moist',
               'soil_temperature_5cm',
               'sunshine_duration'
               ],
               ['recent']
              ]
}

RASTER_CONVERSATION_MAP ={
    'air_temperature_max':'air_temp_max',
    'air_temperature_min':'air_temp_min',
    'air_temperature_mean':'air_temp_mean',
    'precipitation':'precipitation'
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

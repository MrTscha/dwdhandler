# -*- coding: utf-8 -*-
"""
Created on Sat Jun 06 17:32:40 2021

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: Local file data constants """

MAIN_FOLDER     = './dwd_data/'
METADATA_FOLDER = 'metadata/'
STATION_FOLDER  = 'station_data/'
RASTER_FOLDER   = 'raster_data/'

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
               ]
}
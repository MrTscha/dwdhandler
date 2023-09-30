# -*- coding: utf-8 -*-
"""
Created on Sat Jun 06 17:32:40 2021

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: Local file data constants. It also includes som basic constant regarding variables
"""

MAIN_FOLDER     = 'dwd_data/'
METADATA_FOLDER = 'metadata/'
STATION_FOLDER  = 'station_data/'
RASTER_FOLDER   = 'raster_data/'
REGAVG_FOLDER   = 'regavg/'
NWP_FOLDER      = 'nwp_data/'
SQLITEFILESTAT  = 'DWD_STATION.sqlite'
SQLITEREGAVG    = 'DWD_regavg.sqlite'

# Available dtypes
DTYPEAVAIL = ['station','raster','regavg','nwp']

# This is needed for raster data, which is in month subdirectories
RASTERMONTHSUB = ['air_temperature_max','air_temperature_mean',
                  'air_temperature_min','precipitation','sunshine_duration','drought_index']

# Raster is saved in netCDF File at DWD?
RASTERNCDICT   = ['Project_TRY','hyras_de']

RASTERMONTHDICT = ['01_Jan','02_Feb','03_Mar','04_Apr','05_May','06_Jun',
                   '07_Jul','08_Aug','09_Sep','10_Oct','11_Nov','12_Dec']

# Regional Averages month vals
REGAVGMONTHS  = [str(x).zfill(2) for x in range(1,13)]
REGAVGSEASONS = ['winter','spring','summer','autumn']

# NWP name dict
NWPNAMEDICT = {'icon':'global',
               'icon-d2':'germany',
               'tot_prec':'single-level',
               'qv':'model-level',
               'omega':'pressure-level'
              }

NWPGRIDCHECK = ['regular-lat-lon','icosahedral']

# maximum levels
NWPMAXMOLEV = 65

# pressure levels
NWPPRESLEV = [1000,975,950,850,700,600,500,400,300,250,200]

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
    '10_minutes':[['air_temperature',
                   'extreme_temperature',
                   'extreme_wind',
                   'precipitation',
                   'solar',
                   'wind',
                   'wind_test' 
                  ],
                  [
                    'historical',
                    'now',
                    'recent'
                  ]
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

REG_AVG_MAP = {
    'annual':[[
        'air_temperature_mean',
        'frost_days',
        'hot_days',
        'ice_days',
        'precipGE10mm_days',
        'precipGE20mm_days',
        'precipitation',
        'summer_days',
        'sunshine_duration',
        'tropical_nights_tminGE20'
    ], ['recent']
    ],
    'monthly': [[
        'air_temperature_mean',
        'precipitation',
        'sunshine_duration'
    ],['recent']],
    'seasonal': [[
        'air_temperature_mean',
        'precipitation',
        'sunshine_duration'
    ],['recent']]
}

TIME_RASTER_MAP = {
    'monthly':[['air_temperature_max',
               'air_temperature_mean',
               'air_temperature_min',
               'drought_index',
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

NWP_DATA_MAP = {
    'icon':[['tot_prec','omega','qv'],
            ['00']
           ],
    'icon-d2':[['tot_prec','omega','qv'],
           ['00']]

}

RASTER_CONVERSATION_MAP ={
    'air_temperature_max':'air_temp_max',
    'air_temperature_min':'air_temp_min',
    'air_temperature_mean':'air_temp_mean',
    'precipitation':'precipitation',
    'evapo_p':'evapo_p',
    'evapo_r':'evapo_r',
    'soil_moist':'soil_moist',
    'frost_depth':'frost_depth',
    'drought_index':'drought_index',
    'sunshine_duration':'sunshine_duration'
}

NAME_CONVERSATION_MAP = {
    'air_temperature':'TU',
    'cloud_type':'CS',
    'cloudiness':'N',
    'dew_point':'TD',
    'extreme_wind':'FX',
    'extreme_temperature':'extrema_temp',
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
    'historical':'hist',
    'now':'now'
}
PLOT_NAME_CONV = {
    'TT':'Temperatur',
    'RF':'Luftfeuchtigkeit',
    'TT_TU':'Temperatur',
    'RF_TU':'Luftfeuchtigkeit',
    'TD':'Taupunkt',
    'R1':'Niederschlag'
}
REG_CONV_MAP = {
    'air_temperature_mean':'tm',
    'precipitation':'rr',
    'sunshine_duration':'sd',
    'frost_days':'tnas',
    'hot_days':'txbs',
    'ice_days':'txcs',
    'precipGE10mm_days':'rrsfs',
    'precipGE20mm_days':'rrsgs',
    'summer_days':'txas',
    'tropical_nights_tminGE20':'tnes'
}
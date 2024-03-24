# -*- coding: utf-8 -*-
"""
Created on Sun Mar 24 18:21:00 2024

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: Some simple calculations for geographical features like distances from stations
"""

from ..constants.constpar import RADIUSEARTH

import numpy as np

def nearest_station(lon, lat, df_station_list):
    """
        Calculate the distances from given lon/lat pair to given station list
        Uses Haversine function

    Arguments:
        lon (float): longitude of given location
        lat (float): latitude of given location
        df_station_list (Pandas Dataframe): Station list which contains station name or ID and coordinates

    """

    distance = None

    print(distance)


def haversine_function(p1, p2):
    """
        Haversine function
    
    Arguments:
        p1 (tuple): Coordinates of first point (lon, lat)
        p2 (tuple): Coordinates of second point (lon, lat)
    """ 

    lon_p1, lat_p1 = p1
    lon_p2, lat_p2 = p2

    dist_lon = np.radians(lon_p2 - lon_p1)
    dist_lat = np.radians(lat_p2 - lat_p1)

    dist_lat_2 = dist_lat / 2.0
    dist_lon_2 = dist_lon / 2.0

    a  = np.sin(dist_lat_2) * np.sin(dist_lat_2) 
    a += np.cos( np.radians(lat_p1) ) * np.cos( np.radians(lat_p2) ) * np.sin( dist_lon_2 ) * np.sin( dist_lon_2 )
    c  = 2.0 * np.arctan2(np.sqrt(a), np.sqrt( 1.0 - a))
    dist = c * RADIUSEARTH

    return dist
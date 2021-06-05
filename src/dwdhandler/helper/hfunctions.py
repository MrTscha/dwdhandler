# -*- coding: utf-8 -*-
"""
Created on Sat Jun 06 17:32:40 2021

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: some helper functions """

from os import makedirs
from os.path import exists

def check_create_dir(dir_in):
    """ Simple check if dir exists, if not create it """

    if not exists(dir_in):
        makedirs(dir_in)

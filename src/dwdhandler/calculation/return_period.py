# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 16:21:00 2023

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: This module computes return periods of given data
              Preferable precipitation data
"""

# import system modules
import os
import numpy as np
import pandas as pd
import scipy.stats as stats

functionListAvail = ['gev','norm','lognorm','gamma','pearson3','gumbel_r','dweibull','chi2']

def setFunctionType(class_in,ftype):
    """
        Sets and checks function type
    """

    if(ftype in functionListAvail):
        class_in.ftype = ftype
    else:
        print(35*'!')
        print(f"Function '{ftype}' is not available")
        print("Use function listAvailableFunctions of class calc_return_period to list available")
        print(35*'!')

    if(ftype == 'gev'):
        setFctc(class_in=class_in,fct=stats.genextreme)
    elif(ftype == 'norm'):
        setFctc(class_in=class_in,fct=stats.norm)
    elif(ftype == 'lognorm'):
        setFctc(class_in=class_in,fct=stats.lognorm)
    elif(ftype == 'gamma'):
        setFctc(class_in=class_in,fct=stats.gamma)
    elif(ftype == 'pearson3'):
        setFctc(class_in=class_in,fct=stats.pearson3)
    elif(ftype == 'gumbel_r'):
        setFctc(class_in=class_in,fct=stats.gumbel_r)
    elif(ftype == 'dweibull'):
        setFctc(class_in=class_in,fct=stats.dweibull)
    elif(ftype == 'chi2'):
        setFctc(class_in=class_in,fct=stats.chi2)

def setFctc(class_in,fct):
    class_in.fctc = fct

class calc_return_period:
    def __init__(self, data, ftype='gev'):
        """
            Init of class calc_return_period.
        Arguments:
            data 1d-array: Array which contains the data
            ftype str: type of function to describe probability density function
                       e.g. 'gev', 'norm', 'lognorm'
        """

        self.data = data
        self.functionType = None # will be set in setFunctionType
        self.fctc = None # will be set in setFunctionType
        self.twoParamFcts = ['norm','gumbel_r']

        setFunctionType(self,ftype)

    def listAvailableFunctions(self):
        """
            Prints all available functions to describe probability density function of given data
        """

        print(30*'*')
        print('available functions')
        print('which are also available in scipy.stats')
        for fct in functionListAvail:
            print(fct)
        print(30*'*')

    def calc_period(self,
                    end_period=151,
                    beg_range = 1.0,
                    end_range = 101.0,
                    beg_bins  = 0,
                    end_bins  = 101):
        """
            calculate the return period 
            TODO: Describe Arguments,
        """

        self.bins = np.arange(beg_bins, end_bins)

        if(self.functionType in self.twoParamFcts):
            self.shape, self.loc = self.fctc.fit(self.data)
        else:
            self.shape, self.loc, self.scale = self.fctc.fit(self.data)

        self.return_periods = np.arange(1, end_period)
        self.x_range = np.arange(beg_range, end_range)

        self.prop_levels = np.arange(0.0, 1.001, 0.001)

        #if(self.functionType in self.twoParamFcts):
        #    self.return_levels = self.fctc.ppf(self.prop_levels, self.shape, self.loc)
        #else:
        #    self.return_levels = self.fctc.ppf(self.prop_levels, self.shape, self.loc, self.scale)
        self.return_levels = self.calc_return_level(self.prop_levels)

        self.return_period = 1. / (1. - self.prop_levels)

        self.prop = self.calc_prop(self.x_range)

        self.hist, self.bins = np.histogram(self.data, bins=self.bins, density=True)

    def calc_return_level(self,prop):
        """
        Arguments:
            prop scalar or array: probability
        """

        if(self.functionType in self.twoParamFcts):
            return_level = self.fctc.ppf(prop, self.shape, self.loc)
        else:
            return_level = self.fctc.ppf(prop, self.shape, self.loc, self.scale)

        return return_level

    def calc_prop(self,value):
        """
            Caclulate probability by using the propability density function of fitted function
        Arguments:
            value scalar or array: Value to calculate the probabilty 
        returns: scalar or array probability
        """

        if(self.functionType in self.twoParamFcts):
            prop = self.fctc.pdf(value, self.shape, self.loc)
        else:
            prop = self.fctc.pdf(value, self.shape, self.loc, self.scale)

        return prop
    
    def calc_ret_period(self,value):
        """
            Calculate Return Period
        Arguments:
            value: Values which return period is calculated
        returns float
        """

        if(self.functionType in self.twoParamFcts):
            return 1. / (1. - self.fctc.cdf(value,self.shape,self.loc))
        else:
            return 1. / (1. - self.fctc.cdf(value,self.shape,self.loc,self.scale))
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 05 11:40:40 2021

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: This module creates plots
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mc
import matplotlib.gridspec as gridspec
import matplotlib as mpl
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
from matplotlib.ticker import MaxNLocator
import numpy as np
import seaborn as sns

from datetime import datetime

import json

# try to import folium
try:
    import folium
    from folium import DivIcon, plugins
    from folium import IFrame
    lfolium = True
except:
    lfolium = False

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import cartopy.io.shapereader as shpreader
    lcartopy = True
except:
    lcartopy = False

# import plotly
from plotly.utils import PlotlyJSONEncoder
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..helper.hfunctions import moving_average, write_exc_info
from ..constants.filedata import PLOT_NAME_CONV

# activate seaborn plotting settings
sns.set('talk')
sns.set_style("whitegrid", {'axes.grid': False,'axes.edgecolor':'1.0'})
#sns.set_style("whitegrid", {'axes.grid': False})
#sns.set_context('talk')

# Some helper functions

def normalize_colormap(cmap,value,vmin=-1.0,vmax=1.0,return_norm=False,ret_hex=False):
    """
    returns rgba value of given cmap and value
    Arguments:
        cmap:   Colormap
        value:  Value to normalize
        vmin:   Minimum Range (default -1)
        vmax:   Maximum Range (default  1)
        return_norm: Return norm function to use it outside of this function
        return_hex:  Return hex value instead of rgba 
    """

    norm = mc.Normalize(vmin,vmax)
    if(return_norm):
        return norm

    # check if cmap is string otherwise asume it is already colormap
    if(isinstance(cmap,str)):
        cmap = cm.get_cmap(cmap)

    # get colormap rgba
    if(ret_hex):
        return mc.rgb2hex(cmap(norm(value)))
    else:
        return cmap(norm(value))


# Class
class plot_handler(dict):
    def __init__(self,
                 plot_dir,
                 shape_dir=None,
                 shape_fil=None,
                 debug=False,
                 creator=None,
                 source=None,
                 figsize=None,
                 **kwargs):
        # safe init settings
        self.plot_dir = plot_dir
        self.shape_dir = shape_dir
        self.shape_fil = shape_fil
        self.debug     = debug
        self.creator   = creator
        self.source    = source
        if(figsize is None):
            self.figsize = (12,8)

        #
        self.shape_zorder = kwargs.get("shape_zorder")
        if(self.shape_zorder is None):
            self.shape_zorder = 2

        # Create month array
        self.ymonth_arr = [f'{x:02d}' for x in range(1,13)]

        # Create dictionary to convert month to title string
        self.month_title_dict = {
                                 '01':'Januar',
                                 '02':'Februar',
                                 '03':u'März',
                                 '04':'April',
                                 '05':'Mai',
                                 '06':'Juni',
                                 '07':'Juli',
                                 '08':'August',
                                 '09':'September',
                                 '10':'Oktober',
                                 '11':'November',
                                 '12':'Dezember'
                                 }

        # create dictionaries for plotting routines
        # unit
        self.unit_dict = {
            'air_temperature_max':r'$\degree$C',
            'air_temperature_mean':r'$\degree$C',
            'air_temperature':r'$\degree$C',
            'dew_point':r'$\degree$C',
            'air_temperature_min':r'$\degree$C',
            'pressure':'hPa',
            'humidity':'%',
            'windvel':'km/h',
            'winddir':r'$\circ$',
            'cloud_type':' ',
            'cloud_amount':' ',
            'radiation':'Jcm$^2$',
            'radiation_glob':'Jcm$^2$',
            'radiation_diffus':'Jcm$^2$',
            'radiation_atmo':'Jcm$^2$',
            'sundur_hour':'h',
            'sunshine_duration':'h',
            'sundur_hour_p':'%',
            'sundur_min':'min',
            'precipitation':'mm',
            'precipitation_p':'%',
            'evapo_p':'mm',
            'evapo_r':'mm',
            'cwb':'mm'
        }
        self.color_dict = {
            'air_temperature':'red',
            'dew_point':'blue',
            'humidity':'green',
            'precipitation':'blue',
            'radiation':'red',
            'windvel':'red',
            'winddir':'black',
            'radiation_glob':'red',
            'radiation_diffus':'black',
            'radiation_atmo':'blue',
            'sundur_hour':'goldenrod',
            'sundur_min':'goldenrod',
            'cloud_type':'blue',
            'cloud_amount':'blue',
            'pressure':'black'
        }
        #cmap
        self.cmap_dict = {
            'air_temperature_max' :{'abs':cm.seismic,
                                    'clim':cm.seismic,
                                   'dev':cm.seismic},
            'air_temperature_mean':{'abs':cm.seismic,
                                    'clim':cm.seismic,
                                   'dev':cm.seismic},
            'air_temperature_min' :{'abs':cm.seismic,
                                    'clim':cm.seismic,
                                   'dev':cm.seismic},
            'precipitation':{'abs':cm.viridis_r,
                             'clim':cm.viridis_r,
                             'per':cm.PuOr,
                             'dev':cm.PuOr},
            'precipitation_p':{'abs':cm.viridis_r,
                               'clim':cm.viridis_r,
                               'per':cm.PuOr,
                               'dev':cm.PuOr},
            'sunshine_duration':{'abs':cm.cividis,
                                 'clim':cm.cividis,
                             'per':cm.cividis,
                             'dev':cm.cividis},
            'sundur_hour'  :{'abs':cm.viridis_r,
                             'clim':cm.viridis_r,
                             'per':cm.cividis,
                             'dev':cm.PuOr},
            'sundur_hour_p':{'abs':cm.viridis_r,
                             'clim':cm.viridis_r,
                             'per':cm.cividis,
                             'dev':cm.PuOr},
            'evapo_r'      :{'abs':cm.viridis_r,
                             'clim':cm.viridis_r,
                             'dev':cm.PuOr},
            'evapo_p'      :{'abs':cm.viridis_r,
                             'clim':cm.viridis_r,
                             'dev':cm.PuOr},
            'cwb'          :{'abs':cm.PuOr,
                             'clim':cm.PuOr,
                             'dev':cm.PuOr}
        }
        #level dict
        self.vminmax_dict = {
            'air_temperature_max' :{'abs':
                                          {'vmax':35.0,'vmin':-35.0,'vdd':0.5},
                                    'clim':
                                          {'vmax':25.0,'vmin':-25.0,'vdd':0.5},
                                    'dev':
                                          {'vmax':5.0, 'vmin':-5.0, 'vdd':0.1},
                                          },
            'air_temperature_mean':{'abs':
                                          {'vmax':25.0,'vmin':-25.0,'vdd':0.5},
                                    'clim':
                                          {'vmax':15.0,'vmin':-15.0,'vdd':0.5},
                                    'dev':
                                          {'vmax':5.0, 'vmin':-5.0, 'vdd':0.1},
                                          },
            'air_temperature_min' :{'abs':
                                          {'vmax':25.0,'vmin':-25.0,'vdd':0.5},
                                    'clim':
                                          {'vmax':10.0,'vmin':-10.0,'vdd':0.5},
                                    'dev':
                                          {'vmax':5.0, 'vmin':-5.0, 'vdd':0.1},
                                          },
            'precipitation'       :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'clim':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                    'per':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          },
            'sunshine_duration'   :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'clim':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                    'per':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          },
            'precipitation_p'     :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'clim':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                    'per':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          },
            'evapo_p'             :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'clim':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          },
            'evapo_r'             :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'clim':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          },
            'cwb'                 :{'abs':
                                          {'vmax':200.0,'vmin':-200.0,'vdd':20},
                                    'clim':
                                          {'vmax':200.0,'vmin':-200.0,'vdd':20},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          }
        }

        self.vminmax_dict_station_map = {
            'air_temperature_mean':{'abs':
                                          {'vmax':20.0,'vmin':-20.0,'vdd':0.5},
                                    'dev':
                                          {'vmax':3.0, 'vmin':-3.0, 'vdd':0.1},
                                          },
            'air_temperature_max':{'abs':
                                          {'vmax':30.0,'vmin':-30.0,'vdd':0.5},
                                    'dev':
                                          {'vmax':3.0, 'vmin':-3.0, 'vdd':0.1},
                                          },
            'air_temperature_min':{'abs':
                                          {'vmax':30.0,'vmin':-30.0,'vdd':0.5},
                                    'dev':
                                          {'vmax':3.0, 'vmin':-3.0, 'vdd':0.1},
                                          },
            'precipitation'       :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'per': 
                                          {'vmax':125.0,'vmin':75.0,'vdd':1},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          },
            'precipitation_p'     :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'per': 
                                          {'vmax':125.0,'vmin':75.0,'vdd':1},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          },
            'sunshine_duration'   :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'per': 
                                          {'vmax':125.0,'vmin':75.0,'vdd':1},
                                    'dev':
                                          {'vmax':150.0, 'vmin':-150.0, 'vdd':5},
                                          },
            'sundur_hour'         :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'per': 
                                          {'vmax':125.0,'vmin':75.0,'vdd':1},
                                    'dev':
                                          {'vmax':150.0, 'vmin':-150.0, 'vdd':5},
                                          },
            'sundur_hour_p'       :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'per': 
                                          {'vmax':125.0,'vmin':75.0,'vdd':1},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          },
            'evapo_p'             :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          },
            'evapo_r'             :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          },
            'cwb'                 :{'abs':
                                          {'vmax':300.0,'vmin':-300.0,'vdd':20},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          }
        }

        self.vminmax_dict_regavgyear = {
            'air_temperature_mean':{'abs':
                                          {'vmax':20.0,'vmin':-20.0,'vdd':0.5},
                                    'dev':
                                          {'vmax':3.0, 'vmin':-3.0, 'vdd':0.1},
                                          },
            'precipitation'       :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'per': 
                                          {'vmax':125.0,'vmin':75.0,'vdd':1},
                                    'dev':
                                          {'vmax':150.0, 'vmin':-150.0, 'vdd':5},
                                          },
            'precipitation_p'     :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'per': 
                                          {'vmax':125.0,'vmin':75.0,'vdd':1},
                                    'dev':
                                          {'vmax':150.0, 'vmin':-150.0, 'vdd':5},
                                          },
            'sunshine_duration'   :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'per': 
                                          {'vmax':125.0,'vmin':75.0,'vdd':1},
                                    'dev':
                                          {'vmax':150.0, 'vmin':-150.0, 'vdd':5},
                                          },
            'evapo_p'             :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          },
            'evapo_r'             :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          },
            'cwb'                 :{'abs':
                                          {'vmax':300.0,'vmin':-300.0,'vdd':20},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          }
        }
        # title
        self.var_title_dict = {
            'air_temperature_max' :{'long' :'Maximale Temperatur [{}]'.format(self.unit_dict['air_temperature_max']),
                                    'abs'  :r'$\overline{T_{max}}$',
                                    'clim' :r'$\overline{T_{max}}$',
                                    'dev'  :'$T_{max}$',
                                    'short':'Maximaltemperatur'},
            'air_temperature_mean':{'long' :'Mittlere Temperatur [{}]'.format(self.unit_dict['air_temperature_mean']),
                                    'abs'  :r'$\overline{T_{mean}}$',
                                    'clim' :r'$\overline{T_{max}}$',
                                    'dev'  :'$T_{mean}$',
                                    'short':'Mitteltemperatur'},
            'air_temperature_min' :{'long' :'Minimale Temperatur [{}]'.format(self.unit_dict['air_temperature_min']),
                                    'abs'  :r'$\overline{T_{min}}$',
                                    'clim' :r'$\overline{T_{max}}$',
                                    'dev'  :'$T_{min}$',
                                    'short':'Minimaltemperatur'},
            'precipitation'       :{'long' :'Niederschlagssumme [{}]'.format(self.unit_dict['precipitation']),
                                    'abs'  :'$P_{mean}$',
                                    'clim' :'$P_{mean}$',
                                    'dev'  :'$P_{mean}$',
                                    'per'  :'$P_{mean}$',
                                    'short':'Niederschlagssumme'},
            'precipitation_p'     :{'long' :'Niederschlagssumme [{}]'.format(self.unit_dict['precipitation_p']),
                                    'abs'  :'$P_{mean}$',
                                    'clim' :'$P_{mean}$',
                                    'dev'  :'$P_{mean}$',
                                    'per'  :'$P_{mean}$',
                                    'short':'Niederschlagssumme'},
            'sunshine_duration'   :{'long' :'Sonnenscheindauer [{}]'.format(self.unit_dict['sunshine_duration']),
                                    'abs'  :'$SD_{mean}$',
                                    'clim' :'$SD_{mean}$',
                                    'dev'  :'$SD_{mean}$',
                                    'per'  :'$SD_{mean}$',
                                    'short':'Sonnenscheindauer'},
            'evapo_p'             :{'long' :'Potentielle Verdunstung [{}]'.format(self.unit_dict['evapo_p']),
                                    'abs'  :'$evap_{mean}$',
                                    'clim' :'$evap_{mean}$',
                                    'dev'  :'$evap_{mean}$',
                                    'per'  :'$evap_{mean}$',
                                    'short':'Pot. Verdunstung'},
            'evapo_r'             :{'long' :'Reale Verdunstung [{}]'.format(self.unit_dict['evapo_r']),
                                    'abs'  :'$evar_{mean}$',
                                    'clim' :'$evar_{mean}$',
                                    'dev'  :'$evar_{mean}$',
                                    'per'  :'$evar_{mean}$',
                                    'short':'Reale Verdunstung'},
            'cwb'                 :{'long' :'Klimatische Wasserbilanz [{}]'.format(self.unit_dict['cwb']),
                                    'abs'  :'$KWB_{mean}$',
                                    'clim' :'$KWB_{mean}$',
                                    'dev'  :'$KWB_{mean}$',
                                    'per'  :'$KWB_{mean}$',
                                    'short':'Klimatische Wasserbilanz'},
        }


        # position in case mean value is desired 
        # according to coordinaters used (epsg) it should be right under the month plot
        self.x_txt_mean = 0.20
        self.y_txt_mean = -0.15



    def load_shape_file(self):
        """
            function which loads shapefile. 
        """
        try:
            return list(shpreader.Reader(self.shape_dir+self.shape_fil).geometries())
        except:
            if(self.debug):
                if(self.shape_fil is None):
                    print(f"No Shapefile given")
                else:
                    print(f"Could not read shape file {self.shape_dir+self.shape_fil}")
            return

    def plot_single_raster_data(self,lons,lats,data,varp,
                        ptype='abs',
                        ryear=None,
                        title=None,
                        dmean=False,
                        dsource=True,
                        pcmap=None,
                        pextend=None,
                        plevel=None,
                        save_pref=None,
                        **kwargs):
        """Plots only a single raster map"""

        fig, ax = plt.subplots(1,1, figsize=self.figsize,
                                subplot_kw={'projection':ccrs.PlateCarree()})

        if(pcmap is None):
            pcmap = self.cmap_dict[varp][ptype]

        if(pextend is None):
            pextend = 'both'

        if(plevel is None):
            plevel = np.arange(self.vminmax_dict[varp][ptype]['vmin'],
                               self.vminmax_dict[varp][ptype]['vmax']+self.vminmax_dict[varp][ptype]['vdd'],
                               self.vminmax_dict[varp][ptype]['vdd'])
        
        im = self.plot_raster_data(lons, lats, data,
                                   varp=varp,ptype=ptype,
                                   ax=ax,title=title,
                                   dmean=dmean, cmap=pcmap,
                                   extend=pextend,levels=plevel,
                                   **kwargs)

        ax.axis('off')
        cax = plt.axes([0.85,0.25,0.01,0.35])
        cb  = plt.colorbar(im,cax=cax)
        cb.set_label(self.unit_dict[varp])

        if(dsource):
            #sax = plt.axes([0.93,0.20,0.01,0.5])
            #plt.text(0.45,-0.1,'Datengrundlage:DWD',fontsize=10,transform=cax.transAxes)
            plt.text(0.95,0.15,'Datengrundlage: DWD',fontsize=10,transform=ax.transAxes)
        plt.text(0.95,0.1,f'Visualisierung: {self.creator}',fontsize=10,transform=ax.transAxes)

        if(save_pref is None):
            save_pref = 'single'

        filename = f"{self.plot_dir}{save_pref}_{varp}_year_{ryear}_{ptype}.png"

        if(self.debug):
            print(f"Save to: {filename}")
        plt.savefig(filename,bbox_inches='tight',pad_inches=0)
        #plt.show()
        # After all close figure
        plt.close(fig) 

    def plot_raster_data(self,lons,lats,data,varp,
                         ptype='abs',
                         ax=None,
                         title=None,
                         dmean=False,
                         **kwargs):
        """ Simple contour plot """

        if(not lcartopy):
            print("Cartopy is not installed!\nThis function will not work")
            return
        
        adm1_shapes = self.load_shape_file()

        if(ax is None):
            fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})

        try:
            ax.add_geometries(adm1_shapes, ccrs.PlateCarree(),
                              edgecolor='k', facecolor='none', alpha=0.6,zorder=self.shape_zorder,linewidth=0.5)    
        except Exception as Excp:
            if(self.debug):
                print("Could not plot shape geometries")
                print(Excp)
            pass

        im = ax.contourf(lons,lats,data,**kwargs)

        # if mean value is wanted
        if(dmean):
            mean = np.around(data.mean(),decimals=2)
            plt.text(self.x_txt_mean,self.y_txt_mean,
                     f"{self.var_title_dict[varp][ptype]}: {mean}",
                     fontsize=16,
                     transform=ax.transAxes)

        if(title is not None):
            ax.set_title(title)

        return im

    def plot_raster_year_array(self,lons,lats,data_in,year_arr,varp,
                               columns=5,
                               ptype='abs',
                               dmean=False,
                               pcmap=None,
                               pextend=None,
                               psubtitle=None,
                               plevel=None,
                               dsource=True,
                               save_pref=None,
                               **kwargs):
        """Plots for each year, where columns are specified and rows are calculated automatically 
           data_in: 3D array of data;
           year: Year which is plotted
           varp: Variable which is plotted --> same name as retrieved from DWD
           ptype: ['abs' or 'dev'] denotes type of data absolute or deviation. Deviation must contain 
                  Devation in data_in. This only handels cmap title and so on
           dmean: display mean value of each month within plot
        """

        # calculate columns
        total_years = len(year_arr)

        if(total_years != data_in.shape[0]):
            print("first index of data has not the same length as year array")
            return

        rows = int(total_years / columns) 
        # add one row if there is a rest in division
        if(total_years % columns != 0):
            rows += 1

        # total count of subplots 
        tot_count = rows*columns

        if(self.debug):
            print(f'Total years: {total_years}, columns: {columns}, rows: {rows}')

        fig, axs = plt.subplots(rows,columns, figsize=(columns*2,rows*2),
                                subplot_kw={'projection':ccrs.PlateCarree()})
        #fig, axs = plt.subplots(rows,columns, figsize=(10,8),

        k = 0
        i = 0
        j = 0
        if(pcmap is None):
            pcmap = self.cmap_dict[varp][ptype]

        if(pextend is None):
            pextend = 'both'

        if(plevel is None):
            plevel = np.arange(self.vminmax_dict[varp][ptype]['vmin'],
                               self.vminmax_dict[varp][ptype]['vmax']+self.vminmax_dict[varp][ptype]['vdd'],
                               self.vminmax_dict[varp][ptype]['vdd'])

        #for year in year_arr:
        for j in range(tot_count):
            ax = axs[i,k]

            k += 1
            if(k==columns):
                k = 0
                i += 1
            
            try:
                titlestr = year_arr[j]
                alpha = 1.0
                im = self.plot_raster_data(lons, lats, data_in[j],
                                           varp=varp, ptype=ptype,
                                           ax=ax,title=titlestr,
                                           dmean=dmean,cmap=pcmap,
                                           extend=pextend,levels=plevel,
                                           alpha=alpha,
                                           **kwargs)
                ax.axis('off')
            except Exception as excp:
                print(excp)
                #data_tmp = np.full_like(data_in[0],-999.)
                #alpha = 0.0
                ## nasty bug in matplotlib as all masked values is not possible to plot --> blend out with alpha = 0.0
                #self.plot_raster_data(lons,lats, data_tmp,
                #                      varp=varp, ptype=ptype,
                #                      ax=ax, title=titlestr,
                #                      cmap=pcmap,extend=pextend,
                #                      dmean=False,  # overwrite it anyway
                #                      alpha=alpha,
                #                      **kwargs)
                ax.axis('off')

            #j += 1
        cax = plt.axes([0.93,0.25,0.01,0.35])
        cb  = plt.colorbar(im,cax=cax)
        cb.set_label(self.unit_dict[varp])

        if(psubtitle is not None):
            plt.suptitle(psubtitle)

        # add dwd as source
        if(dsource):
            #sax = plt.axes([0.93,0.20,0.01,0.5])
            plt.text(0.45,-0.1,'Datengrundlage:DWD',fontsize=10,transform=cax.transAxes)
        plt.text(1.048,0.1,f'Visualisierung: {self.creator}',fontsize=10,transform=ax.transAxes)

        if(save_pref is None):
            save_pref = 'array'
        #plt.tight_layout()
        fig.subplots_adjust(wspace=0.0,bottom=0.0,top=0.92)
        filename = f"{self.plot_dir}{save_pref}_year_{varp}_{year_arr[0]}_{year_arr[-1]}_{ptype}.png"

        if(self.debug):
            print(f"Save to: {filename}")
        plt.savefig(filename,bbox_inches='tight',pad_inches=0)
        #plt.show()
        # After all close figure
        plt.close(fig) 

    def plot_raster_year_tot(self,lons,lats,data_in,year,varp,
                             ptype='abs',
                             dmean=False,
                             pcmap=None,
                             pextend=None,
                             psubtitle=None,
                             plevel=None,
                             dsource=True,
                             **kwargs):
        """Plots total year of raster data 
           data is plotted in two rows
           data_in: 3D array of data; First index denotes month and can be less than 12 but not greater than 12
           year: Year which is plottet
           varp: Variable which is plottet --> same name as retrieved from DWD
           ptype: ['abs' or 'dev' or 'clim'] denotes type of data absolute or deviation or climate mean values. Deviation must contain 
                  Devation in data_in. This only handels cmap title and so on
           dmean: display mean value of each month within plot
        """

        fig, axs = plt.subplots(2,6, figsize=(20,7),
                                subplot_kw={'projection':ccrs.PlateCarree()})

        k = 0
        i = 0
        j = 0
        if(pcmap is None):
            pcmap = self.cmap_dict[varp][ptype]

        if(pextend is None):
            pextend = 'both'

        if(plevel is None):
            plevel = np.arange(self.vminmax_dict[varp][ptype]['vmin'],
                               self.vminmax_dict[varp][ptype]['vmax']+self.vminmax_dict[varp][ptype]['vdd'],
                               self.vminmax_dict[varp][ptype]['vdd'])

        for month in self.ymonth_arr:
            ax = axs[i,k]

            k += 1
            if(k==6):
                k = 0
                i = 1
            
            titlestr = self.month_title_dict[month]
            try:
                alpha = 1.0
                im = self.plot_raster_data(lons, lats, data_in[j],
                                           varp=varp, ptype=ptype,
                                           ax=ax,title=titlestr,
                                           dmean=dmean,cmap=pcmap,
                                           extend=pextend,levels=plevel,
                                           alpha=alpha,
                                           **kwargs)
            except Exception as excp:
                print(excp)
                data_tmp = np.full_like(data_in[0],-999.)
                alpha = 0.0
                # nasty feature in matplotlib as all masked values is not possible to plot --> blend out with alpha = 0.0
                # Also we don't want im here, since it is then used for the colorbar, which gives unwanted results
                self.plot_raster_data(lons,lats, data_tmp,
                                      varp=varp, ptype=ptype,
                                      ax=ax, title=titlestr,
                                      cmap=pcmap,extend=pextend,
                                      dmean=False,  # overwrite it anyway
                                      alpha=alpha,
                                      **kwargs)

            j += 1

        cax = plt.axes([0.93,0.25,0.01,0.5])
        cb  = plt.colorbar(im,cax=cax)
        cb.set_label(self.unit_dict[varp])
        if(psubtitle is None):
            psubtitle = f"{self.var_title_dict[varp]['short']}\nJahr {year}"

        plt.suptitle(psubtitle)

        # add dwd as source
        if(dsource):
            plt.text(1.05,0.2,'Datengrundlage:DWD',fontsize=10,transform=ax.transAxes)
        plt.text(1.048,0.1,f'Visualisierung: {self.creator}',fontsize=10,transform=ax.transAxes)

        filename = f"{self.plot_dir}{varp}_{year}_{ptype}.png"

        if(self.debug):
            print(f"Save to: {filename}")
        plt.savefig(filename,bbox_inches='tight')
        # After all close figure
        plt.close(fig) 

    def plot_map_station_val(self,
                             data_in,
                             var_plot,
                             date_in,
                             lats=None,
                             lons=None,
                             ax=None,
                             ptype='abs',
                             title=None,
                             dsource=True,
                             dcreator=False,
                             filename=None):
        """
        Plots map with station distribution of given values
        Arguments:
            df_in:    DataFrame with data
            var_plot: Variable to plot
            date_in:  date 
            lats:     list of latitude coordinate (must fit to station location)
            lons:     list of longitude coordinate (must fit to station location)
            ax:       Axis to plot to (default None --> axis is created)
            ptype:    type of potting ('abs' or 'dev')  default 'abs'
            title:    Title (default None)
            dsource:  print source on plot
            dcreator: print creator, defined by init (default False)
            filename: Other filename than automatic created (default None --> creates automated one)
        """

        if(not lcartopy):
            print("Cartopy is not installed!\nThis function will not work")
            return

        if(lats is None and lons is None):
            print("Please provide lon and lat coordinate")
            print("No data plotted")
            return

        adm1_shapes = self.load_shape_file()

        if(ax is None):
            fig, ax = plt.subplots(figsize=self.figsize,subplot_kw={'projection': ccrs.PlateCarree()})
        
        try:
            ax.add_geometries(adm1_shapes, ccrs.PlateCarree(),
                              edgecolor='k', facecolor='none', alpha=0.6,zorder=self.shape_zorder,linewidth=0.5)    
        except Exception as Excp:
            if(self.debug):
                print("Could not plot shape geometries")
                print(Excp)
            pass

        norm_size = [self.vminmax_dict_station_map[var_plot][ptype]['vmin'],self.vminmax_dict_station_map[var_plot][ptype]['vmax']]

        im = ax.scatter(
            lons, lats,
            c=data_in,
            s=54,
            edgecolors='k',
            cmap=self.cmap_dict[var_plot][ptype],
            norm=plt.Normalize(norm_size[0],norm_size[-1]),
            transform=ccrs.PlateCarree()
        )

        if(title is None):
            title = self.var_title_dict[var_plot] 
        ax.set_title(title)
        ax.set_extent([5.3, 15.3, 47.0, 55.5], crs=ccrs.PlateCarree())

        cax = plt.axes([0.85, 0.25, 0.01, 0.5])
        cbar = plt.colorbar(im,cax=cax,extend='both')
        cbar.set_label(self.unit_dict[var_plot])
        if(dsource):
            ax.text(1.02,0.1,self.source,fontsize=10,transform=ax.transAxes)
        if(dcreator):
            ax.text(1.02,0.06,f'Visualisierung u. Berechnung: {self.creator}',fontsize=8,transform=ax.transAxes)

        if(filename is None):
            filename = f"{self.plot_dir}{var_plot}_{date_in.year}_{date_in.month:02d}_{ptype}.png"

        if(self.debug):
            print(f"Save to: {filename}")

        plt.savefig(filename,bbox_inches='tight')
        # After all close figure
        plt.close(fig)

    def plot_data_histo(self,
                        data_in,
                        var_plot,
                        date_in,
                        bin_arr=None,
                        ax=None,
                        ptype='abs',
                        title=None,
                        dsource=True,
                        dcreator=False,
                        filename=None
                       ):
        """
        Plots histogram of given data and uses cmap of plotconstr, 
        which is according to the given variable
        Arguments:
            df_in:   DataFrame with data
            date_in: date 
            bin_arr: Bins to use (default None --> calculated from vminmax_dict_station_map)
            ax:      Axis to plot to (default None --> axis is created)
            ptype:   type of potting ('abs' or 'dev')  default 'abs'
            title:   Title (default None)
            dsource: print source on plot
            dcreator: print creator, defined by init (default False)
            filename: Other filename than automatic created (default None --> creates automated one)
        """

        sns.set_theme(style='dark')

        # if no bin_arr given, create one
        if(bin_arr is None):
            bin_arr =  np.arange(self.vminmax_dict_station_map[var_plot][ptype]['vmin'],
                               self.vminmax_dict_station_map[var_plot][ptype]['vmax']+self.vminmax_dict_station_map[var_plot][ptype]['vdd'],
                               self.vminmax_dict_station_map[var_plot][ptype]['vdd'])

        # calculate histogram
        counts, bins = np.histogram(data_in,bins=bin_arr)

        # create figure if no axis is given
        if(ax is None):
            fig, ax = plt.subplots(figsize=self.figsize)

        cm = self.cmap_dict[var_plot][ptype]
        #plt.cm.get_cmap(plot_class.var_dict[svardict]['cm'])
        x_span = bins.max() - bins.min()
        col = [cm(((x-bins.min())/x_span)) for x in bins]
        ax.bar(bins[:-1],counts,color=col,width=bins[1]-bins[0])
        ax.set_xlabel(self.unit_dict[var_plot])

        if(title is None):
            title = self.var_title_dict[var_plot]
        
        ax.set_title(title)

        if(filename is None):
            filename = f"{self.plot_dir}{var_plot}_{date_in.year}_{date_in.month:02d}_{ptype}.png"

        if(self.debug):
            print(f"Save to: {filename}")

        plt.savefig(filename,bbox_inches='tight')
        # After all close figure
        plt.close(fig)

    def plot_station_meteo(self,df_in,
                           var_plot=['TT_TU'],
                           var_cat=['air_temperature'],
                           ax_arr=None,
                           title=None,
                           lday=True):
        """Plots simple station meteogramm
        Arguments:

        """

        assert(len(var_cat) == len(var_plot))

        if(ax_arr is None):
            tot_len = len(var_plot)
        else:
            assert(len(ax_arr) == len(var_plot))
            tot_len = np.max(ax_arr)+1

        sns.set_style("whitegrid", {'axes.grid': False,'axes.edgecolor':'0.5'})
        #fig, ax = plt.subplots(tot_len,1,figsize=(10,6))
        fig, ax = plt.subplots(tot_len,1,figsize=(10,2.0*tot_len))

        if(title is not None):
            plt.suptitle(title)

        i = 0

        if(ax_arr is None):
            for var, varc in zip(var_plot,var_cat):
                if(tot_len != 1):
                    ax_d = ax[i]
                else:
                    ax_d = ax

                if(varc in ['precipitation']):
                    self.plot_timeseries_meteogram(df_in,var,varc,ax_d,plot_bar=True,lday=lday)
                else:
                    self.plot_timeseries_meteogram(df_in,var,varc,ax_d,lday=lday)
                if(i < tot_len-1 and tot_len != 1):
                #    #ax_d.axes.get_xaxis().set_visible(False)
                    ax_d.set_xticklabels([])
                i += 1
        else:
            for var, varc, i in zip(var_plot,var_cat,ax_arr):
                if(varc in ['precipitation']):
                    self.plot_timeseries_meteogram(df_in,var,varc,ax[i],plot_bar=True,lday=lday)
                else:
                    self.plot_timeseries_meteogram(df_in,var,varc,ax[i],lday=lday)

                if(i < tot_len-1 and tot_len != 1):
                #    #ax[i].axes.get_xaxis().set_visible(False)
                    ax[i].set_xticklabels([])

        fig.autofmt_xdate(rotation=45)
        fig.subplots_adjust(left=0.1,right=0.87,hspace=0.2)

        plt.show()

    def plot_timeseries_meteogram(self,df_in,var_in,var_cat,ax,plot_bar=False,lday=True):
        """Plots Meteogram according to given Variable and DataFrame
        
        Arguments:
            df_in:   DataFrame with data
            var_in:  Variable of Dataframe to plot
            var_cat: Variable categorie --> temperature, precipitation...
            ax:      plot axis
            plot_bar: Plots additional to bar plot for precipitation cumulative sum of precip (default False)
            lday:    Data is only one day (default True), manages date formatter
        """

        try:
            color = self.color_dict[var_cat]
        except:
            color = 'black'

        if(var_cat in ['precipitation']):
            ax.bar(df_in.index.values,
                   df_in[var_in],
                   color=color,
                   edgecolor=color,
                   label=f'{var_in}',
                   width=1.0/len(df_in.index.values)
                   )
            if(plot_bar):
                ax2 = ax.twinx()
                ax2.plot(df_in.index.values,
                        df_in[var_in].cumsum(),
                        color=color,
                        label=f'{var_in}-kum',
                       )
                ax2.set_ylabel(self.unit_dict[var_cat])
                ax2.set_ylim(0,df_in[var_in].cumsum().max()+30)
                ax2.legend(loc='upper right',fontsize=8,shadow=True,ncol=4)
        elif(var_cat == 'cloud_amount'):
            ax.bar(df_in.index.values,
                    df_in[var_in],
                    color=color,
                    edgecolor=color,
                    label=f'{var_in}',
                    width=1.0/len(df_in.index.values)
                   )
        elif(var_cat in ['sundur','sundur_min','sundur_hour']):
            ax.bar(df_in.index.values,
                    df_in[var_in],
                    color=color,
                    edgecolor=color,
                    label=f'{var_in}',
                    width=1.0/len(df_in.index.values)
            )
        elif(var_cat in ['winddir']):
            ax2 = ax.twinx()
            ax2.plot(df_in.index.values,
                    df_in[var_in],
                    color=color,
                    label=f'{var_in}'
                   )
            ax2.legend(loc='upper right',fontsize=8,shadow=True,ncol=4)
        else:
            ax.plot(df_in.index.values,
                    df_in[var_in],
                    color=color,
                    label=f'{var_in}'
                   )

        if(var_cat == 'humidity'):
            ax.set_ylim(0,100)
        if(var_cat == 'cloud_amount'):
            ax.set_ylim(0,8)
        if(var_cat == 'air_temperature'):
            ax.set_ylim(round(df_in[var_in].min(),-1)-10,round(df_in[var_in].max()+10,-1))
        if(var_cat == 'dew_point'):
            ax.set_ylim(bottom=round(df_in[var_in].min()-10,-1))
        #if(var_cat == 'sundur'):
        #    ax.set_ylim(0,1)

        if(var_cat in ['air_temperature','dew_point']):
            ax.axhline(0,linestyle='--',color='black')

        if(lday):
            date_form = DateFormatter("%Y-%m-%d-%H")
        else:
            date_form = DateFormatter("%Y-%m-%d")
        ax.xaxis.set_major_formatter(date_form)
        ax.set_xlim(df_in.index[0],df_in.index[-1])

        #ax.legend(bbox_to_anchor=(0.5,1.3), loc="upper center",fontsize=8,shadow=True,ncol=4)
        if(var_cat in ['winddir']):
            ax2.set_ylabel(self.unit_dict[var_cat])
            ax2.set_ylim(0,420)

        if(var_cat in ['precipitation']):
            ax.legend(loc='upper left',fontsize=8,shadow=True,ncol=4)
        elif(var_cat in ['winddir']):
            ax.legend(loc='upper left',fontsize=8,shadow=True,ncol=4,bbox_to_anchor=(0.0,1.2)).set_zorder(10)
            ax2.legend(loc='upper right',fontsize=8,shadow=True,ncol=4,bbox_to_anchor=(1.0,1.2)).set_zorder(10)
        else:
            ax.legend(fontsize=8,shadow=True,ncol=4)

        try:
            ax2
        except:
            ax.set_ylabel(self.unit_dict[var_cat])
        
        ax.grid(axis='x',which='both',zorder=0)
        ax.grid(axis='y',zorder=0,linestyle='--')

    def plot_regavg_thermopluvio(self,date_arr,temp_dev,prec_dev,
                                 stepwise=None,
                                 title=None,
                                 xlim=None,
                                 ylim=None,
                                 pdiff=False,
                                 ldraw_ell=False,
                                 file_suffix=None):
        """
           Plots Thermopluviogram of DWD regional average 
           date_arr:  Date Array
           temp_dev:  Temperature array containing deviation
           prec_dev:  Precipitation array containing deviation
           stepwise:  step to combine years using the same --> for example 10 will do a 10 years step before changing color
           title:     Title (default: None)
           xlim:      setting xlim (default: None --> -2.5,2.5)
           ylim:      setting ylim (default: None --> -250,250)
           pdiff:     if precipitation deviation is in percent
           ldraw_ell: Draw ellipse around data points (default: False)
           file_suffix: if a suffix has to be appended to standard filename regavg_thermopluviogram_{file_suffix}.png (default: None)
        """

        fig, ax = plt.subplots(figsize=(10,8))

        fsyl_size = 14
        fs_cbar   = 12
        fs_legend = 8
        axlc      = 'k'
        axla      = 0.7
        axls      = '--'

        # is a step given?
        if(stepwise is not None):
            steps = np.arange(round(date_arr.year[0],-1),round(date_arr.year[-2],-1)+stepwise,stepwise)
            # create colors from cmap
            color_names = self.make_colors_norm(norm_size=[0,len(steps)],cmap=cm.plasma,data_in=np.arange(0,len(steps)+1))
            for i in range(len(steps)-1):
                if(steps[i+1] > date_arr.year[-2]):
                    cond = np.isin(date_arr.year,np.arange(steps[i],date_arr.year[-1]))
                    label = f'{steps[i]} - {date_arr.year[-2]}'
                else:
                    cond = np.isin(date_arr.year,np.arange(steps[i],steps[i+1]))
                    label = f'{steps[i]} - {steps[i+1]-1}'
                ax.scatter(temp_dev[cond],prec_dev[cond],label=label,color=color_names[i])
                if(ldraw_ell):
                    self.confidence_ellipse(temp_dev[cond],prec_dev[cond],ax,n_std=1.5,edgecolor=color_names[i])

                if(self.debug):
                    print(steps[i],steps[i+1])
        # no step given --> plot only last one with different colored marker
        else:
            ax.scatter(temp_dev[:len(temp_dev)-1],prec_dev[:len(temp_dev)-1],label=f'{date_arr[0].year} - {date_arr[len(date_arr)-2].year}')
            if(ldraw_ell):
                self.confidence_ellipse(temp_dev[:len(temp_dev)-1],prec_dev[:len(temp_dev)-1],ax,n_std=1.5,edgecolor='k')
        ax.scatter(temp_dev[-1],prec_dev[-1],color='black',marker='*',label=f'{date_arr[-1].year}',s=200)

        ax.axvline(0,color=axlc,zorder=0,alpha=axla,linestyle=axls)

        if(xlim is None):
            xlim = self.even_lim_data(temp_dev)
        ax.set_xlim(xlim[0],xlim[-1])

        if(ylim is None):
            ylim = self.even_lim_data(prec_dev)
            if(pdiff):
                ylim[0] = 0
        ax.set_ylim(ylim[0],ylim[1])

        ax.set_xlabel(self.unit_dict['air_temperature_mean'])
        if(pdiff):
            ax.set_ylabel(self.unit_dict['precipitation_p'])
            ax.axhline(100,color=axlc,zorder=0,alpha=axla,linestyle=axls)
        else:
            ax.set_ylabel(self.unit_dict['precipitation'])
            ax.axhline(0,color=axlc,zorder=0,alpha=axla,linestyle=axls)

        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels,loc='upper left',fontsize=fs_legend)

        if(title is not None):
            fig.suptitle(title,fontsize=18)

        # final adjustments
        #plt.subplots_adjust(left=0.1, bottom=0.1, right=0.89, top=0.88, wspace=0.05, hspace=0.15) 

        if(file_suffix is None):
            filename = f"{self.plot_dir}/regyear_thermopluviogramm.png"
        else:
            filename = f"{self.plot_dir}/regyear_thermopluviogramm_{file_suffix}.png"

        if(self.debug):
            print(f"Save to: {filename}")

        plt.savefig(filename,bbox_inches='tight')
        # close figure at the end
        plt.close(fig)

    def plot_regavg_year_tps(self,date_arr,temp,prec,sd,
                             temp_dev,prec_dev,sd_dev,
                             title=None,**kwargs):
        """Plots DWD regional average evoluation
           of given temperature, precipitation and sunduration array
           and stripes (deviation), for precipitation and sun duration it will be calculated to percental deviation
           date_arr: Date
           temp:     temperature with same dimensionality as date_arr
           prec:     precipitation with same dimensionality as date_arr
           sd:       sun duration with same dimensionalty as date_arr
           temp_dev: temperature deviation with same dimensionality as date_arr
           prec_dev: precipitation deviation with same dimensionality as date_arr
           sd_dev:   sun duration deviation with same dimensionalty as date_arr
        """

        move_avg = kwargs.get('move_avg',5)
        file_suffix = kwargs.get('file_suffix')

        fig, axs = plt.subplots(3,2,figsize=(14,10))

        fsyl_size = 14
        fs_cbar   = 12
        fs_legend = 8

        # plot temperature
        ax = axs[0,0]
        ax.plot_date(date_arr,temp,'.',color='k',label='Mitteltemperatur')
        tmp_arr = np.full_like(temp,-999.)
        #tmp_arr[4:] = moving_average(temp,5)
        tmp_arr[move_avg-1:] = moving_average(temp,move_avg)
        tmp_arr = np.ma.masked_where(tmp_arr == -999.,tmp_arr)
        ax.plot_date(date_arr,tmp_arr,'-',color='tomato',label=f'Gleitendes Mittel ({move_avg}j)')
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels,loc='upper left',fontsize=fs_legend)
        ax.set_xticks([])
        year_diff = 2
        xstart = datetime(date_arr[0].year-year_diff,date_arr[0].month, date_arr[0].day)
        xend   = datetime(date_arr[-1].year+year_diff,date_arr[-1].month, date_arr[-1].day)
        #ax.set_xlim(date_arr[0],date_arr[-1])
        ax.set_xlim(xstart, xend)
        ax.set_ylabel(r'[$^\circ C$]',fontsize=fsyl_size)
        ax = axs[0,1]
        var_t = 'air_temperature_mean'
        ptypet = 'dev'
        cmap = self.cmap_dict[var_t][ptypet]
        norm_size = [self.vminmax_dict_regavgyear[var_t][ptypet]['vmin'],self.vminmax_dict_regavgyear[var_t][ptypet]['vmax']]
        normalize = self.make_stripe_plot(date_arr,temp_dev,ax,cmap,norm_size,lretnorm=True)
        ax.set_xticks([])
        #ax.set_xlim(date_arr[0],date_arr[-1])
        ax.set_xlim(xstart, xend)

        cax, _ = mpl.colorbar.make_axes(ax,shrink=0.65,fraction=0.03,pad=0.04,anchor=(2.0,0.5))
        cbar   = mpl.colorbar.ColorbarBase(cax,cmap=cmap,norm=normalize,extend='both')
        cbar.set_label(self.unit_dict[var_t],fontsize=fs_cbar)

        # plot precipitation
        ax = axs[1,0]
        ax.plot_date(date_arr,prec,'.',color='k',label='Niederschlagssumme')
        tmp_arr = np.full_like(temp,-999.)
        #tmp_arr[4:] = moving_average(prec,5)
        tmp_arr[move_avg-1:] = moving_average(prec,move_avg)
        tmp_arr = np.ma.masked_where(tmp_arr == -999.,tmp_arr)
        ax.plot_date(date_arr,tmp_arr,'-',color='royalblue',label=f'Gleitendes Mittel ({move_avg}j)')
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels,loc='upper left',fontsize=fs_legend)
        ax.set_xticks([])
        #ax.set_xlim(date_arr[0],date_arr[-1])
        ax.set_xlim(xstart, xend)
        ax.set_ylabel('[mm]',fontsize=fsyl_size)
        ax = axs[1,1]
        var_t = 'precipitation'
        ptypet = 'per'
        cmap = self.cmap_dict[var_t][ptypet]
        norm_size = [self.vminmax_dict_regavgyear[var_t][ptypet]['vmin'],self.vminmax_dict_regavgyear[var_t][ptypet]['vmax']]
        # calculate percental deviation
        prec_perc = (1.0 + (prec_dev/prec))*100.0
        normalize = self.make_stripe_plot(date_arr,prec_perc,ax,cmap,norm_size,lretnorm=True)
        ax.set_xticks([])
        #ax.set_xlim(date_arr[0],date_arr[-1])
        ax.set_xlim(xstart, xend)

        cax, _ = mpl.colorbar.make_axes(ax,shrink=0.65,fraction=0.03,pad=0.04,anchor=(2.0,0.5))
        cbar   = mpl.colorbar.ColorbarBase(cax,cmap=cmap,norm=normalize,extend='both')
        cbar.set_label('%',fontsize=fs_cbar)

        # plot sunshine duration
        ax = axs[2,0]
        ax.plot_date(date_arr,sd,'.',color='k',label='Sonnenscheindauer')
        tmp_arr = np.full_like(sd,-999.)
        #tmp_arr[4:] = moving_average(sd,5)
        tmp_arr[move_avg-1:] = moving_average(sd,move_avg)
        #print(sd)
        tmp_arr = np.ma.masked_where(tmp_arr == -999.,tmp_arr)
        # to avoid error message replace mask with nan
        tmp_arr = tmp_arr.filled(np.nan)
        ax.plot_date(date_arr,tmp_arr,'-',color='orange',label=f'Gleitendes Mittel ({move_avg}j)')
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels,loc='upper left',fontsize=fs_legend)
        #ax.set_xlim(date_arr[0],date_arr[-1])
        ax.set_xlim(xstart, xend)
        ax.tick_params(axis='x', labelrotation=45)
        ax.set_ylabel('[h]',fontsize=fsyl_size)

        ax = axs[2,1]
        var_t = 'sunshine_duration'
        ptypet = 'per'
        cmap = self.cmap_dict[var_t][ptypet]
        hex_list = ['#535353','#fcff59']
        cmap = self.get_continuous_cmap(hex_list)
        norm_size = [self.vminmax_dict_regavgyear[var_t][ptypet]['vmin'],self.vminmax_dict_regavgyear[var_t][ptypet]['vmax']]
        # calculate percental deviation
        sd_perc = (1.0 + (sd_dev/sd))*100.0
        # to avoid error message replace mask with nan
        sd_perc = sd_perc.filled(np.nan)
        normalize = self.make_stripe_plot(date_arr,sd_perc,ax,cmap,norm_size,lretnorm=True)
        #ax.set_xlim(date_arr[0],date_arr[-1])
        ax.set_xlim(xstart, xend)
        ax.tick_params(axis='x', labelrotation=45)

        cax, _ = mpl.colorbar.make_axes(ax,shrink=0.65,fraction=0.03,pad=0.04,anchor=(2.0,0.5))
        cbar   = mpl.colorbar.ColorbarBase(cax,cmap=cmap,norm=normalize,extend='both')
        cbar.set_label('%',fontsize=fs_cbar)

        if(title is not None):
            fig.suptitle(title,fontsize=18)

        # final adjustments
        plt.subplots_adjust(left=0.1, bottom=0.1, right=0.89, top=0.88, wspace=0.05, hspace=0.15) 

        if(file_suffix is None):
            filename = f"{self.plot_dir}/regyear_temp_prec_sd.png"
        else:
            filename = f"{self.plot_dir}/regyear_temp_prec_sd_{file_suffix}.png"

        if(self.debug):
            print(f"Save to: {filename}")

        plt.savefig(filename,bbox_inches='tight',pad_inches=0)
        # close figure at the end
        plt.close(fig)

    def plot_regavg_year(self,date_arr,data_arr,var_in,
                         ptype='abs',pbar=False,pstripes=False,
                         title=None,norm_size=None,file_prefix=None):
        """ Plots DWD regional average on a yearly resolution
            date_arr: Date array (mostly only the year)
            data_arr: Data array
            ptype:    Type of Plot --> 'abs' (default) absolut values, 'dev' devation --> Data must be absolute values or deviation and is not calculated here!
            pbar:     Plot data as bar plot (default False)
            pstripes: Plot data as stripes (Ed Hawking stripes) plot (default False)
            title:    Give the plot a title (default is None and therefore a string is generated from self.var_title_dict)
            norm_size: Give the ylim of plot and normalization values for coloring e.g.[-5,5]
            file_prefix: apply some prefix to file outpug
        """

        fig, ax = plt.subplots(1,1,figsize=(12,6)) 

        if(norm_size is None):
            norm_size = [self.vminmax_dict_regavgyear[var_in][ptype]['vmin'],self.vminmax_dict_regavgyear[var_in][ptype]['vmax']]
        cmap = self.cmap_dict[var_in][ptype]
        fs_cbar = 12
        datemin = pd.Timestamp(f'{date_arr.year[0]  - 1}-01-01')
        datemax = pd.Timestamp(f'{date_arr.year[-1] + 1}-01-01')
        if(pbar):
            bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
            #normalize = self.make_bar_plot(date_arr,data_arr,ax,norm_size,cmap,lretnorm=True,bbox=bbox)
            normalize = self.make_bar_plot(date_arr,data_arr,ax,norm_size,cmap,lretnorm=True)
            cax, _ = mpl.colorbar.make_axes(ax,shrink=0.65,fraction=0.03,pad=0.04,anchor=(1.0,0.5))
            cbar   = mpl.colorbar.ColorbarBase(cax,cmap=cmap,norm=normalize,extend='both')
            cbar.set_label(self.unit_dict[var_in],fontsize=fs_cbar)
            ax.grid(False)
            ax.grid(True,linestyle='--',which='major',axis='y',linewidth=2,color='black',alpha=0.5)
            ax.set_xlim(datemin, datemax)
            labellingFormat=mpl.dates.DateFormatter("%Y")#b refers to month,y refers to year
            ax.xaxis.set_major_formatter(labellingFormat)
            majorTicks=mpl.dates.YearLocator(5) #every 4th year, 1st month, 1st day
            ax.xaxis.set_major_locator(majorTicks)
            for label in ax.get_xticklabels():
                label.set_rotation(45)

            ax.text(1.01,0.125,'Daten: DWD',fontsize=8,transform=ax.transAxes)
            ax.text(1.01,0.1,f'Visualisierung: {self.creator}',fontsize=8,transform=ax.transAxes)
        elif(pstripes):
            self.make_stripe_plot(date_arr,data_arr,ax,cmap,norm_size)
            ax.set_xlim(datemin, datemax)

            ax.text(1.01,0.125,'Daten: \nDWD',fontsize=8,transform=ax.transAxes)
            ax.text(1.01,0.05,f'Visualisierung: \n{self.creator}',fontsize=8,transform=ax.transAxes)
        else:
            ax.axhline(0.0,color='grey',linestyle='--',alpha=0.7)
            ax.plot_date(date_arr,data_arr,'-',color='k')
            ax.set_ylabel(self.unit_dict[var_in]) 

            ax.text(1.03,0.125,'Daten: \nDWD',fontsize=8,transform=ax.transAxes)
            ax.text(1.03,0.05,f'Visualisierung: \n{self.creator}',fontsize=8,transform=ax.transAxes)

        if(title is None):
            title = self.var_title_dict[var_in]['long']

        ax.set_title(title)
        ax.set_xlabel('Jahr')

        if(file_prefix is None):
            filename = f"{self.plot_dir}{var_in}_{date_arr[0].year}_{date_arr[-1].year}_{ptype}.png"
        else:
            filename = f"{self.plot_dir}{file_prefix}_{var_in}_{date_arr[0].year}_{date_arr[-1].year}_{ptype}.png"
        if(self.debug):
            print(f"Save to: {filename}")
        plt.savefig(filename,bbox_inches='tight',pad_inches=0)
        #plt.show()
        # After all close figure
        plt.close(fig) 
    
    def make_bar_plot(self,date_in,data_in,ax_in,norm_size,cmap,lretnorm=False,bbox=None):
        """ Makes bar plot with given input data
        """

        if(lretnorm):
            colors,normalize = self.make_colors_norm(norm_size,cmap,data_in,lretnorm=lretnorm)
        else:
            colors = self.make_colors_norm(norm_size,cmap,data_in,lretnorm=lretnorm)
        #barplot = ax_in.bar(date_in,data_in,width=200.0,edgecolor='k')
        if(bbox is not None):
            width = len(data_in) / bbox.width
            print(width)
            barplot = ax_in.bar(date_in,data_in,width=width,edgecolor='k')
        else:
            barplot = ax_in.bar(date_in,data_in,edgecolor='k')

        for i in range(len(colors)):
            barplot[i].set_color(colors[i])
        ax_in.set_ylim(norm_size)
        if(lretnorm):
            return normalize

    def make_stripe_plot(self,xval,yval,ax_in,cmap,norm_size,lretnorm=False):
        """makes a stripe plot similar to Ed Hawkings warming stripes"""

        if(lretnorm):
            colors,normalize = self.make_colors_norm(norm_size,cmap,yval,lretnorm=lretnorm)
        else:
            colors = self.make_colors_norm(norm_size,cmap,yval,lretnorm=lretnorm)
        for i in range(len(colors)):
            ax_in.axvline(x=xval[i],color=colors[i],linewidth=5.0) # linewidth should be adabtable
        # remove yticks
        ax_in.set_yticks([])
        ax_in.tick_params(axis='y',labelbottom=False) # turn off label
        ax_in.grid(False)
        if(lretnorm):
            return normalize
    
    def even_lim_data(self,data_in):
        """ Makes even spaced limits for plotting
        It searches for min/max value and then returns the negative and positive
        value of the maximum absolut value
        --> max 3.4 and min - 1.2 --> returns [-4,4]
        data_in:      1D data array
        """

        min = np.floor(data_in.min())
        max = np.ceil(data_in.max())

        max = np.maximum(np.abs(min),np.abs(max))
        max = np.ceil(max + data_in.std()*0.5)

        return [-1 * max, max]

    def confidence_ellipse(self,x, y, ax, n_std=3.0, facecolor='none', **kwargs):
        """
        Create a plot of the covariance confidence ellipse of *x* and *y*.

        Parameters
        ----------
        x, y : array-like, shape (n, )
            Input data.

        ax : matplotlib.axes.Axes
            The axes object to draw the ellipse into.

        n_std : float
            The number of standard deviations to determine the ellipse's radiuses.

        **kwargs
            Forwarded to `~matplotlib.patches.Ellipse`

        Returns
        -------
        matplotlib.patches.Ellipse
        """
        if(x.size != y.size):
            raise ValueError("x and y must be the same size")

        cov = np.cov(x, y)
        pearson = cov[0, 1]/np.sqrt(cov[0, 0] * cov[1, 1])
        # Using a special case to obtain the eigenvalues of this
        # two-dimensionl dataset.
        ell_radius_x = np.sqrt(1 + pearson)
        ell_radius_y = np.sqrt(1 - pearson)
        ellipse = Ellipse((0, 0), width=ell_radius_x * 2, height=ell_radius_y * 2,
                          facecolor=facecolor, **kwargs)

        # Calculating the stdandard deviation of x from
        # the squareroot of the variance and multiplying
        # with the given number of standard deviations.
        scale_x = np.sqrt(cov[0, 0]) * n_std
        mean_x = np.mean(x)

        # calculating the stdandard deviation of y ...
        scale_y = np.sqrt(cov[1, 1]) * n_std
        mean_y = np.mean(y)

        transf = transforms.Affine2D() \
            .rotate_deg(45) \
            .scale(scale_x, scale_y) \
            .translate(mean_x, mean_y)

        ellipse.set_transform(transf + ax.transData)
        return ax.add_patch(ellipse)


    def make_colors_norm(self,norm_size,cmap,data_in,lretnorm=False):
        """Creates color array according to given cmap and normalization range
           norm_size: list with two values (min, max)
           cmap:      colormap
           data_in:   data
           returns list of colors
        """

        colors = []
        normalize = mc.Normalize(norm_size[0],norm_size[1])
        colors = [cmap(normalize(val)) for val in data_in]
        if(lretnorm):
            return colors, normalize
        else:
            return colors

    def get_continuous_cmap(self, hex_list, float_list=None):
        ''' creates and returns a color map that can be used in heat map figures.
        If float_list is not provided, colour map graduates linearly between each color in hex_list.
        If float_list is provided, each color in hex_list is mapped to the respective location in float_list. 
        
        Parameters
        ----------
        hex_list: list of hex code strings
        float_list: list of floats between 0 and 1, same length as hex_list. Must start with 0 and end with 1.
        
        Returns
        ----------
        colour map'''
        rgb_list = [self.rgb_to_dec(self.hex_to_rgb(i)) for i in hex_list]
        if float_list:
            pass
        else:
            float_list = list(np.linspace(0,1,len(rgb_list)))

        cdict = dict()
        for num, col in enumerate(['red', 'green', 'blue']):
            col_list = [[float_list[i], rgb_list[i][num], rgb_list[i][num]] for i in range(len(float_list))]
            cdict[col] = col_list
        #cmp = mcolors.LinearSegmentedColormap('my_cmp', segmentdata=cdict, N=256)
        cmp = mc.LinearSegmentedColormap('my_cmp', segmentdata=cdict, N=256)
        return cmp
    
    def hex_to_rgb(self,value):
        '''
        Converts hex to rgb colours
        value: string of 6 characters representing a hex colour.
        Returns: list length 3 of RGB values'''
        value = value.strip("#") # removes hash symbol if present
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


    def rgb_to_dec(self,value):
        '''
        Converts rgb to decimal colours (i.e. divides each value by 256)
        value: list (length 3) of RGB values
        Returns: list (length 3) of decimal values'''
        return [v/256 for v in value]


# class to display return period

class plot_return_period:
    def __init__(self,return_period_class,source=None,creator=None):

        self.returnp_class = return_period_class
        self.source = source
        self.creator = creator

    def plot_return_period(self,save_info,
                           single_plot=True,
                           var_display='tägl. Niederschlagsmenge',
                           return_per_plot=200.,
                           ret_ax=False,
                           act_val=None,
                           **kwargs
                           ):
        
        """
        Arguments:
            save_info str: additional info which is used for saving the file
            single_plot bool: Put everythin in a single plot (return period, PDF and Histogram of data)
            var_display str: String which is added to Plot to describe Variable 
            return_per_plot scalar: maximum return period value
            ret_ax bool: return ax of pyplot
            act_val scalar: Value which is displayed as a red dot in return period diagram
            **kwargs
        """

        figsize = kwargs.get('figsize')

        if(figsize is None):
            if(single_plot):
                figsize = (11,12)
            else:
                figsize = (11,6)

        if(single_plot):
            fig, ax = plt.subplots(2, 1, figsize=figsize)

        iax = 0

        bins = self.returnp_class.bins
        hist = self.returnp_class.hist
        x_range = self.returnp_class.x_range
        prop = self.returnp_class.prop

        edgecolor = kwargs.get('edgecolor','#4aaaaa')

        if(not single_plot):
            fig, pax = plt.subplots(figsize=figsize)

            pax.bar(bins[:-1],hist, align='edge', color='blue', edgecolor=edgecolor)

            pax.set_xlabel(var_display)
            pax.set_ylabel("Häufigkeit")
            pax.set_title(f"Häufigkeit {var_display}")
            pax.set_yscale("log")

            plt.savefig(f"Häufigkeit_{save_info}_{self.returnp_class.ftype}.png",bbox_inches='tight')
            plt.close(fig)

        if(single_plot):
            pax = ax[0]
        else:
            fig, pax = plt.subplots(figsize=figsize)

        pax.bar(bins[:-1], hist, align='edge', color='blue', edgecolor=edgecolor)
        print(x_range)
        print(prop)
        pax.plot(x_range,prop,color='purple',label='PDF',linestyle='--',linewidth=4)
        pax.grid(True)

        pax.legend(frameon=False)

        pax.set_xlabel(var_display)
        pax.set_ylabel("Wahrscheinlichkeit")
        pax.set_title(f"Wahrscheinlichkeit {var_display}")

        if(not single_plot):
            plt.savefig(f"Wahrscheinlichkeit_{save_info}_{self.returnp_class.ftype}.png",bbox_inches='tight')

            plt.close(fig)

        # return period
        if(single_plot):
            pax = ax[1]
        else:
            fig, pax = plt.subplots(figsize=figsize)

        return_period = self.returnp_class.return_period
        return_levels = self.returnp_class.return_levels

        pax.plot(return_period, return_levels,linewidth=4,color='#4B4C4E')

        if(act_val is not None):
            return_per = self.returnp_class.calc_ret_period(act_val)
            print(f"{act_val}mm; ret per: {return_per}")
            pax.scatter(return_per,act_val,color='red',zorder=2,s=140)
        else:
            return_per = 0.0
        pax.grid(True)

        #pax.legend(frameon=False)

        pax.set_xlabel("Wiederkehrzeit")
        pax.set_ylabel(var_display)

        if(not single_plot):
            pax.set_title(f"Wiederkehrzeit {var_display}")

        pax.set_xlim(0,np.maximum(return_per_plot,np.floor(return_per+40.0)))
        ymax = np.ceil(self.returnp_class.calc_return_level(1. - (1./return_per_plot)))

        if(act_val is not None):
            pax.set_ylim(kwargs.get('return_period_ylim0',0),np.maximum(ymax,np.floor(act_val+40.0)))

        if(not single_plot):
            plt.savefig(f"Wiederkehrzeit_{save_info}_{self.returnp_class.ftype}.png",bbox_inches='tight')

            plt.close(fig)

        if(single_plot):
            # adjust subplot
            plt.subplots_adjust(left=0.1,
                                bottom=0.1,
                                right=0.9,
                                top=0.9,
                                wspace=0.4,
                                hspace=0.4)
            # save single plot
            plt.savefig(f"Hauf_Wahr_Wieder_{save_info}_{self.returnp_class.ftype}.png",bbox_inches='tight')

        plt.close(fig) # Schließe am Ende alles

class plotly_class:
    def __init__(self,source=None,creator=None):

        self.source = source
        self.creator = creator
        self.plot_unit_dict = {
                    'RSK':'mm',
                    'RWS_10':'mm',
                    'RWS_10c':'mm',
                    'PP_10':'hPa',
                    'SDK':'h',
                    'TD_10':'\u00B0C',
                    'TT_10':'\u00B0C',
                    'TX_10':'\u00B0C',
                    'TN_10':'\u00B0C',
                    'RF_10':'%',
                    'TM5_10':'\u00B0C',
                    'TX5_10':'\u00B0C',
                    'TN5_10':'\u00B0C',
                    'TMK':'\u00B0C',
                    'TNK':'\u00B0C',
                    'TXK':'\u00B0C'
                    }

        self.plot_line_color = {
                    'TT_10':'#ff0000',
                    'TX_10':'#ff0000',
                    'TN_10':'#ff0000',
                    'TD_10':'#4287f5',
                    'TM5_10':'#820000',
                    'TX5_10':'#820000',
                    'TN5_10':'#4287f5'
        }

        self.plot_dash = {
                    'TT_10':None,
                    'TX_10':'dot',
                    'TN_10':'dot',
                    'TD_10':None,
                    'TM5_10':None,
                    'TX5_10':'dot',
                    'TN5_10':'dot'
        }

        self.plot_title_dict={
                    'RSK':'Niederschlag',
                    'SDK':'Sonnenscheindauer',
                    'RSKc':'kum. Niederschlag (M)',
                    'RSKcy':'kum. Niederschlag (J)',
                    'TMK':'Tagesmitteltemperatur',
                    'TNK':'Tagesminimumtemperatur',
                    'TXK':'Tageshöchstemperatur',
                    'PP_10':'Luftdruck',
                    'TT_10':'10min Mittel Temperatur (2m)',
                    'TX_10':'10min Max Temperatur (2m)',
                    'TN_10':'10min Min Temperatur (2m)',
                    'TD_10':'Taupunkt (2m)',
                    'RF_10':'Luftfeuchtigkeit',
                    'TM5_10':'10min Mittel Temperatur (5cm)',
                    'TX5_10':'10min Max Temperatur (5cm)',
                    'TN5_10':'10min Min Temperatur (5cm)',
                    'RWS_10c':'kum. Niederschlag',
                    'RWS_10':'Niederschlag'
                    }
        


    def plot_act_year_ts_sumvar(self,df_in,
                        var_plot,
                        df_clim_daily,
                        clim_period,
                        df_climstats=None,
                        date_index=None,
                        year_in=None,
                        title=None,
                        filename=None,
                        returnJson=False,
                        **kwargs
                        ):
        """Plots timeseries of actual year
        with given min/max and percentiles for sum variables
        Arguments:
            df_in: DataFrame with timeseries data
            var_plot: Variable to plot
            clim_period: string --> climatic period e.g. "1991 - 2020"
            df_clim_daily: Daily mean values
            df_climstats: Give some climstats min/max percentiles; default None
            date_index: Give date index Default None --> will be created
            year_in:  Year which is to be plotted
            title:  Give a specific title
            filename: Give an filename
        """

        if(year_in is None):
            year_in = df_in.index.year[-1]

        if(date_index is None):
            date_range = pd.date_range(f'{year_in}-01-01',f'{year_in}-12-31')

        values = np.full(len(date_range),np.nan)
        # fill values with year values
        ## TODO take leap year into account
        date_mask = df_in.index.year == year_in
        values[0:len(df_in[date_mask])] = df_in[date_mask][var_plot].values
        # prepare monthly cumsum
        values_cumsm = np.full(len(date_range),np.nan)
        values_cumsm[0:len(df_in[date_mask])] = df_in[date_mask][var_plot].groupby(df_in[date_mask].index.month).cumsum().values
        # prepare yearly cumsum
        values_cumsy = np.full(len(date_range),np.nan)
        values_cumsy[0:len(df_in[date_mask])] = df_in[date_mask][var_plot].cumsum()

        if(title is None):
            title = self.plot_title_dict[var_plot]

        fig = go.Figure()

        # plot values
        fig.add_trace(go.Bar(
            x=date_range,
            y=values,
            name='Tagessumme',
            marker_color='blue'
        ))

        fig.add_trace(go.Scatter(
            x=date_range,
            y=values_cumsm,
            name='kum. Monatssumme',
            line_shape='spline',
            line=dict(color='Coral')
        ))

        fig.add_trace(go.Scatter(
            x=date_range,
            y=values_cumsy,
            name='kum. Jahressumme',
            line_shape='spline',
            line=dict(color='indigo')
        ))

        if(df_clim_daily is not None or not df_climstats.empty()):
            # add clim_cumsum
            if(date_range.is_leap_year[0]):
                row_number = 60
                df1 = df_clim_daily[0:row_number]
                df2 = df_clim_daily[row_number:]
                df1.loc[row_number] = df_clim_daily.loc[row_number]
                df_clim_daily = pd.concat([df1,df2])
                df_clim_daily.index = [*range(df_clim_daily.shape[0])]
            fig.add_trace(go.Scatter(
                x=date_range,
                y=df_clim_daily[var_plot].groupby(date_range.month).cumsum().values,
                mode='lines',
                line_color='SlateBlue',
                line_shape='spline',
                name=f'Monatssumme {clim_period}'
            ))

            fig.add_trace(go.Scatter(
                x=date_range,
                y=df_clim_daily[var_plot].cumsum().values,
                mode='lines',
                line_color='SteelBlue',
                line_shape='spline',
                name=f'Jahressumme {clim_period}'
            ))

        fig.update_layout(
            title=title,
            yaxis_title=self.plot_unit_dict[var_plot],
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(
                            count=1,
                            label='1m',
                            step='month',
                            stepmode='backward'
                        ),
                        dict(
                            count=2,
                            label='2m',
                            step='month',
                            stepmode='backward'
                        ),
                        dict(
                            count=3,
                            label='3m',
                            step='month',
                            stepmode='backward'
                        ),
                        dict(
                            count=6,
                            label='6m',
                            step='month',
                            stepmode='backward'
                        ),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=False
            ),
                type='date'
            )
        )

        if(returnJson):
            return json.dumps(fig,cls=PlotlyJSONEncoder)

        # create filename if none is given
        if(filename is None):
            filename = f"{var_plot}.html"
    
        # write to html
        fig.write_html(filename,config={'displaylogo':False})

    def plot_act_year_ts(self,df_in,
                         var_plot,
                         df_clim_daily,
                         clim_period,
                         df_climstats=None,
                         date_index=None,
                         year_in=None,
                         title=None,
                         returnJson=True,
                         filename=None
                        ):
        """Plots timeseries of actual year
           with given min/max and percentiles
        Arguments:
            df_in: DataFrame with timeseries data
            var_plot: Variable to plot
            clim_period: string --> climatic period e.g. "1991 - 2020"
            df_clim_daily: Daily mean values
            df_climstats: Give some climstats min/max percentiles; default None
            date_index: Give date index Default None --> will be created
            year_in:  Year which is to be plotted
            title:  Give a specific title
            filename: Give an filename
        """

        if(year_in is None):
            year_in = df_in.index.year[-1]

        if(date_index is None):
            date_range = pd.date_range(f'{year_in}-01-01',f'{year_in}-12-31')

        values = np.full(len(date_range),np.nan)
        # fill values with year values
        ## TODO take leap year into account
        values[0:len(df_in[df_in.index.year == year_in])] = df_in[df_in.index.year == year_in][var_plot].values

        # get min max year of data
        year_b = df_in.index.year[0]
        #year_e = df_in.index.year[-2]
        year_b = np.min(df_in.index.year)
        year_e = np.max(df_in.index.year) - 1

        if(title is None):
            title = self.plot_title_dict[var_plot]

        fig = go.Figure()

        if(df_climstats is not None):
            minmax_col = 'indigo'
            # Plot min/max
            fig.add_trace(go.Scatter(
                x=date_range,
                y=df_climstats.query('stat == "min"')[var_plot].values,
                #fill='tonexty',
                name=f'min {year_b}-{year_e}',
                line=dict(color=minmax_col),
                line_shape='spline',
                opacity=0.6
            ))

            fig.add_trace(go.Scatter(
                x=date_range,
                y=df_climstats.query('stat == "max"')[var_plot].values,
                fill='tonexty',
                name=f'max {year_b}-{year_e}',
                mode='lines',
                line_color=minmax_col,
                line_shape='spline',
                opacity=0.6
            ))

            perz_color = 'burlywood'
            fig.add_trace(go.Scatter(
                x=date_range,
                y=df_climstats.query('stat == "0.1"')[var_plot].values,
                #fill='tonexty',
                name=f'10. Perz.',
                mode='lines',
                line_shape='spline',
                line_color=perz_color,
                opacity=0.75
            ))

            fig.add_trace(go.Scatter(
                x=date_range,
                y=df_climstats.query('stat == "0.9"')[var_plot].values,
                fill='tonexty',
                name=f'90. Perz.',
                mode='lines',
                line_shape='spline',
                line_color=perz_color,
                opacity=0.75
            ))


        # plot mean
        fig.add_trace(go.Scatter(
            x=date_range,
            y=values,
            mode='markers',
            name=f'{year_in}',
            marker=dict(color='crimson') 
        ))

        fig.add_trace(go.Scatter(
            x=date_range,
            y=df_clim_daily[var_plot].values,
            name=f'{clim_period}',
            mode='lines',
            line_color='black',
            line_shape='spline',
            opacity=0.95
        ))

        fig.update_layout(
            legend_itemclick=False,
            legend_itemdoubleclick=False,
            title=title,
            yaxis_title=self.plot_unit_dict[var_plot]
        )

        if(returnJson):
            return json.dumps(fig,cls=PlotlyJSONEncoder)

        # create filename if none is given
        if(filename is None):
            filename = f"{var_plot}_ts.html"

        # write to html
        fig.write_html(filename,config={'displaylogo':False})

    def plot_timeseries_temp_daily_pltly(self,df_in,
                                   var_plot,
                                   df_dev=None,
                                   df_clim=None,
                                   title=None,
                                   filename=None):
        """Plots timeseries
        Arguments:
            df_in: DataFrame with timeseries data
            var_plot: Variable to plot
            df_dev: Deviation DataFrame (may be None)
            title:  If there is a specific title
            filename: Give an filename
        """

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_in.index,
            y=df_in['TXK'].values,
            name=self.plot_title_dict['TXK'],
            line=dict(color='red',width=4)
        ))

        fig.add_trace(go.Scatter(
            x=df_in.index,
            y=df_in['TMK'].values,
            name=self.plot_title_dict['TMK'],
            line=dict(color='green',width=4)
        ))

        fig.add_trace(go.Scatter(
            x=df_in.index,
            y=df_in['TNK'].values,
            name=self.plot_title_dict['TNK'],
            line=dict(color='blue',width=4)
        ))

        fig.update_layout(
            title=title,
            yaxis_title=self.plot_unit_dict['TMK'],
            legend=dict(
                orientation='h',
                x=0.01,
                y=0.97,
                traceorder='normal',
                font=dict(
                    size=12,
                )
            ),
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(
                            count=1,
                            label='1m',
                            step='month',
                            stepmode='backward'
                        ),
                        dict(
                            count=2,
                            label='2m',
                            step='month',
                            stepmode='backward'
                        ),
                        dict(
                            count=6,
                            label='6m',
                            step='month',
                            stepmode='backward'
                        ),
                        dict(
                            count=1,
                            label='1 Jahr',
                            step='year',
                            stepmode='backward'
                        ),
                        dict(
                            count=1,
                            label='Akt Jahr',
                            step='year',
                            stepmode='todate'
                        ),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=False
                ),
                type='date'
            )
        )

        # set initial date
        try:
            fig.update_xaxes(
                range=[df_in.index[-62],df_in.index[-1]],
                type='date'
            )
        except:
            fig.update_xaxes(
                range=[df_in.index[-1*(len(df_in.index)-1)],df_in.index[-1]],
                type='date'
            )

        fig.update_yaxes(
            range=[df_in[var_plot].min()-1.0,df_in[var_plot].max()+1.0]
        )

        # create filename if none is given
        if(filename is None):
            filename = f"{var_plot}.html"

        # write to html
        fig.write_html(filename,config={'displaylogo':False})

    def plot_date_timeseries_pltly(self,df_in,
                                   var_plot,
                                   df_dev=None,
                                   df_clim=None,
                                   title=None,
                                   filename=None):
        """Plots timeseries
        Arguments:
            df_in: DataFrame with timeseries data
            var_plot: Variable to plot
            df_dev: Deviation DataFrame (may be None)
            title:  If there is a specific title
            filename: Give an filename
        """

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_in.index,
            y=df_in[var_plot].values,
            name=self.plot_title_dict[var_plot],
            line=dict(color='red',width=4)
        ))

        fig.update_layout(
            title=title,
            yaxis_title=self.plot_unit_dict[var_plot],
            legend=dict(
                orientation='h',
                x=0.01,
                y=0.97,
                traceorder='normal',
                font=dict(
                    size=12,
                )
            ),
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(
                            count=1,
                            label='1m',
                            step='month',
                            stepmode='backward'
                        ),
                        dict(
                            count=2,
                            label='2m',
                            step='month',
                            stepmode='backward'
                        ),
                        dict(
                            count=6,
                            label='6m',
                            step='month',
                            stepmode='backward'
                        ),
                        dict(
                            count=1,
                            label='1 Jahr',
                            step='year',
                            stepmode='backward'
                        ),
                        dict(
                            count=1,
                            label='Akt Jahr',
                            step='year',
                            stepmode='todate'
                        ),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=False
                ),
                type='date'
            )
        )

        # set initial date
        fig.update_xaxes(
            range=[df_in.index[-62],df_in.index[-1]],
            type='date'
        )

        fig.update_yaxes(
            range=[df_in[var_plot].min()-1.0,df_in[var_plot].max()+1.0]
        )

        # create filename if none is given
        if(filename is None):
            filename = f"{var_plot}.html"

        # write to html
        fig.write_html(filename,config={'displaylogo':False})

    def plot_date_bar_pltly(self,df_in,
                            var_plot,
                            df_dev=None,
                            df_clim=None,
                            title=None,
                            filename=None
                            ):
        """Plots bar chart with plotly bar
        Arguments:
            df_in: DataFrame with timeseries data
            var_plot: Variable to plot
            df_dev: Deviation DataFrame (may be None)
            title:  If there is a specific title
            filename: Give an filename
        """

        len_data = len(df_in[var_plot].values)
        if(var_plot in ['RSK']):
            cumsum = df_in[f'{var_plot}c'].values
            cumsumy = df_in[f'{var_plot}cy'].values
        if(title is None):
            title = self.plot_title_dict[var_plot]

        cunit = self.plot_unit_dict[var_plot]

        #if(df_dev is not None):
        #    if(var_plot in ['RSK']):
        #        perc = df_dev[f'{var_plot}p'].round(1).values[0]
        #        title = f'{title}<br>Kl. Monatsumme: {df_clim[var_plot].round(1).values[0]} Abweichung: {df_dev[f"{var_plot}_dev"].round(1).values[0]} ({perc}%)'
        #    else:
        #        dev = df_dev[f'{var_plot}_dev'].round(2).values
        #        title = f'{title}<br>Kl. Monatmittel: {df_dev[var_plot].values} ({dev})'

        fig = go.Figure()


        fig.add_trace(go.Bar(
            x=df_in.index,
            y=df_in[var_plot].values,
            name=self.plot_title_dict[var_plot],
            marker_color='blue'  # may set via dict
        ))

        if(var_plot in ['RSK']):
            fig.add_trace(go.Scatter(
                x=df_in.index,
                y=cumsum,
                name=self.plot_title_dict[f'{var_plot}c'],
                line=dict(
                    width=2
                )
            ))
            fig.add_trace(go.Scatter(
                x=df_in.index,
                y=cumsumy,
                name=self.plot_title_dict[f'{var_plot}cy'],
                line=dict(
                    width=2
                )
            ))

        fig.update_layout(
            xaxis_tickangle=-45,
            hovermode="x",
            dragmode="zoom",
            title=title,
            yaxis_title=self.plot_unit_dict[var_plot],
            xaxis_title="Datum",
            height=490,
            #template="plotly_white",
            #template="plotly_dark",
            template="seaborn",
            legend=dict(
                orientation='h',
                x=0.01,
                y=0.97,
                traceorder='normal',
                font=dict(
                    size=12,
                )
            ),
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(
                            count=1,
                            label='1m',
                            step='month',
                            stepmode='backward'
                        ),
                        dict(
                            count=2,
                            label='2m',
                            step='month',
                            stepmode='backward'
                        ),
                        dict(
                            count=6,
                            label='6m',
                            step='month',
                            stepmode='backward'
                        ),
                        dict(
                            count=1,
                            label='1 Jahr',
                            step='year',
                            stepmode='backward'
                        ),
                        dict(
                            count=1,
                            label='Akt Jahr',
                            step='year',
                            stepmode='todate'
                        ),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=False
                ),
                type='date'
            )
        )

        # set initial date
        try:
            fig.update_xaxes(
                range=[df_in.index[-62],df_in.index[-1]],
                type='date'
            )
        except:
            fig.update_xaxes(
                range=[df_in.index[-1*(len(df_in.index)-1)],df_in.index[-1]],
                type='date'
            )

        # set initial y limits
        if(var_plot in ['RSK']):
            try:
                fig.update_yaxes(
                    range=[df_in[var_plot].min(),cumsum[-62:-1].max()+10.]
                )
            except:
                fig.update_yaxes(
                    range=[df_in[var_plot].min(),cumsum[-2:-1].max()+10.]
                )
        else:
            fig.update_yaxes(
                range=[df_in[var_plot].min()-1.0,df_in[var_plot].max()+1.0]
            )

        # create filename if none is given
        if(filename is None):
            filename = f"{var_plot}.html"

        # write to html
        fig.write_html(filename,config={'displaylogo':False})

    def plot_10m_timeseries_pltly(self,df_in,
                                   var_plot,
                                   title=None,
                                   filename=None,
                                   returnJson=False):
        """Plots timeseries
        Arguments:
            df_in: DataFrame with timeseries data
            var_plot: Variable to plot
            title:  If there is a specific title
            filename: Give an filename
            returnJson (bool): Default False, return json plty as json
        """

        fig = go.Figure()

        if(var_plot == 'RWS_10'):
            fig.add_trace(go.Bar(
                x=df_in.index,
                y=df_in[var_plot].values,
                name=self.plot_title_dict[var_plot],
                marker_color='blue'
            ))
            rws_cumsum = df_in[var_plot].groupby(df_in.index.day).cumsum().values
            fig.add_trace(go.Scatter(
                x=df_in.index,
                y=df_in[f'{var_plot}c'].values,
                name=self.plot_title_dict[f'{var_plot}c'],
                line_shape='spline',
                line=dict(color='red',width=4)
            ))

            # update init y axis limits
            fig.update_yaxes(
                range=[0.0,df_in[f'{var_plot}c'].max()+6.]
            )
        elif(isinstance(var_plot,list)):

            for var in var_plot:
                try:
                    fig.add_trace(go.Scatter(
                        x=df_in.index,
                        y=df_in[var].values,
                        name=self.plot_title_dict[var],
                        line_shape='spline',
                        line=dict(color=self.plot_line_color[var],dash=self.plot_dash[var],width=4)
                    ))
                except:
                    write_exc_info()

            # update init y axis limits
            fig.update_yaxes(
                range=[df_in[var_plot].min()-1.0,df_in[var_plot].max()+3.0]
            )
        else:
            fig.add_trace(go.Scatter(
                x=df_in.index,
                y=df_in[var_plot].values,
                name=self.plot_title_dict[var_plot],
                line=dict(color='red',width=4)
            ))

            # update init y axis limits
            fig.update_yaxes(
                range=[df_in[var_plot].min()-1.0,df_in[var_plot].max()+3.0]
            )

        if(isinstance(var_plot,list)):
            var = var_plot[0]
        else:
            var = var_plot

        fig.update_layout(
            title=title,
            yaxis_title=self.plot_unit_dict[var],
            legend=dict(
                orientation='h',
                x=0.01,
                y=0.97,
                traceorder='normal',
                font=dict(
                    size=12,
                )
            ),
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(
                            count=1,
                            label='1h',
                            step='hour',
                            stepmode='backward'
                        ),
                        dict(
                            count=2,
                            label='2h',
                            step='hour',
                            stepmode='backward'
                        ),
                        dict(
                            count=4,
                            label='4h',
                            step='hour',
                            stepmode='backward'
                        ),
                        dict(
                            count=6,
                            label='6h',
                            step='hour',
                            stepmode='backward'
                        ),
                        dict(
                            count=1,
                            label='1d',
                            step='day',
                            stepmode='backward'
                        ),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=False
                ),
                type='date'
            )
        )

        #fig.update_xaxes(
        #    range=[df_in.index[-62],df_in.index[-1]],
        #    type='date'
        #)

        if(returnJson):
            return json.dumps(fig,cls=PlotlyJSONEncoder)

        # create filename if none is given
        if(filename is None):
            filename = f"{var_plot}.html"

        # write to html
        fig.write_html(filename,config={'displaylogo':False})

class fol_map:
    def __init__(self, 
                 start_coords=(51.0,10.0),
                 z_start=6.9,
                 map_tile = 'OpenStreetMap',
                 debug = False
                ):
        """Class with folium map 
        Arguments:
            start_coords:  Start coordinates of folium map; default: (51.0,10.0)
            z_start:       Zoom Start; default: 6.9
            map_tile:      Map Tile of Folium map; default: 'OpenStreetMap'
            debug:         Prints some extra output
        """
        self.start_coords = start_coords
        self.z_start      = z_start
        self.map_tile     = map_tile
        self.debug        = debug

    def create_map(self,**kwargs):
        """Creates map instance"""
        start_coords = kwargs.get('start_coords')
        if(start_coords is None):
            start_coords = self.start_coords
        zoom_start = kwargs.get('zoom_start')
        if(zoom_start is None):
            zoom_start = self.z_start
        map_tile = kwargs.get('map_tile')
        if(map_tile is None):
            map_tile = self.map_tile
        control_scale = kwargs.get('control_scale')
        if(control_scale is None):
            control_scale = True

        if(self.debug):
            print("Create Folium Map")
            print("Start Coords ", start_coords)
            print("Zoom ",zoom_start," Map tile: ", map_tile," Contrl Scale ",control_scale)

        self.m = folium.Map(start_coords,zoom_start=zoom_start,tiles=map_tile,control_scale=control_scale)
        if(map_tile != 'OpenStreetMap'):
            folium.TileLayer('OpenStreetMap').add_to(self.m)

    def finalize_map_controls(self):
        """Add controlls at final step"""

        plugins.Fullscreen(
            position='topright',
            title='Expand me',
            title_cancel='Exit me',
            force_separate_button=True
        ).add_to(self.m)

        folium.LayerControl(collapsed=True).add_to(self.m)


    def map_cluster(self,markergroup,**kwargs):
        """
        prepares map for marker cluster
        Arguments:
            markergroup: Groups of markers
        """

        try:
            self.m
        except:
            self.create_map()
        
        control = kwargs.get('control')
        if(control is None):
            control = False

        self.mcg = folium.plugins.MarkerCluster(control=control)
        self.m.add_child(self.mcg)

        # save markergroup for later purpose
        self.markergroup = markergroup

        self.subcluster =  []
        for i, marker in enumerate(markergroup):
            self.subcluster.append(folium.plugins.FeatureGroupSubGroup(self.mcg, marker))
            self.m.add_child(self.subcluster[i])

    def add_val_marker(self,loc,value,cname=None,popup_key=None,i=None,icon_col=None,tooltip=None):
        """
        Add maker with value as marker
        Arguments: 
            loc:    Location of Marker [lat,lon]
            cname:  Name of Cluster, default None --> if None i has to be given
            popup_key: popup text (also html possible like iframe)
            i    : ith - place in markergroup which was given for map_cluster
                   default None --> Item is searched each time
            icon_col: icon color
        """

        if(icon_col is None):
            icon_col = 'blue'

        # Create circle
        html_circ = f"""
            <div style="font-size: 12pt; color: {icon_col};">
                {value}
            </div>"""
        icon = folium.DivIcon(html=html_circ)

        if(tooltip is None):
            folium.Marker(location=loc,popup=popup_key,icon=icon).add_to(self.m)
        else:
            folium.Marker(location=loc,popup=popup_key,icon=icon,tooltip=tooltip).add_to(self.m)
        #folium.Circle(location=loc,popup=popup_key,radius=4000,color=icon_col,fill_color=icon_col).add_to(self.m)

    def add_val_cluster(self,loc,cname=None,popup_key=None,i=None,icon=None,icon_col=None):
        """
        Add a value to a cluster
        Arguments:
            loc  : Location of Marker [lat,lon]
            cname: Name of Cluster, default None --> if None i has to be given
            popup_key: popup text (also html possible like iframe)
            i    : ith - place in markergroup which was given for map_cluster
                   default None --> Item is searched each time
            icon: Displayed icon on folium map
            icon_col: icon color
        """

        if(i is None and cname is None):
            print("Please specify at least the name of markergroup")
            return

        if(i is None):
            i = self.markergroup.index(cname)

        if(icon_col is None):
            icon_col = 'blue'

        if(icon is None):
            icon = folium.Icon(color=icon_col)

        if(self.debug):
            print("icon")
            print("i ", i)
            print("icon_col ", icon_col)
            print("loc ", loc)
            print("popup ",popup_key)
        folium.Marker(location=loc,popup=popup_key,icon=icon).add_to(self.subcluster[i])

    def save_map(self,filename):
        """
        Saves map to given destiny
        Arguments:
            filename:  file destination 
        """

        if(self.debug):
            print(f"Save Map to {filename}")
        self.m.save(filename)

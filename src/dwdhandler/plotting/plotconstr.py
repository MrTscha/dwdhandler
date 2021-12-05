# -*- coding: utf-8 -*-
"""
Created on Thu Dec 05 11:40:40 2021

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: This module creates plots
"""

#import system modules
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import seaborn as sns

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader

# activate seaborn plotting settings
sns.set()
sns.set_style("whitegrid", {'axes.grid': False})
sns.set_context('talk')

class plot_handler(dict):
    def __init__(self,
                 plot_dir,
                 shape_dir=None,
                 shape_fil=None,
                 debug=False):
        # safe init settings
        self.plot_dir = plot_dir
        self.shape_dir = shape_dir
        self.shape_fil = shape_fil
        self.debug     = debug


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
            'air_temperature_max':'$\degree$C',
            'air_temperature_mean':'$\degree$C',
            'air_temperature_min':'$\degree$C',
            'precipitation':'mm',
            'evapo_p':'mm',
            'evapo_r':'mm',
            'cwb':'mm'
        }
        #cmap
        self.cmap_dict = {
            'air_temperature_max' :{'abs':cm.seismic,
                                   'dev':cm.seismic},
            'air_temperature_mean':{'abs':cm.seismic,
                                   'dev':cm.seismic},
            'air_temperature_min' :{'abs':cm.seismic,
                                   'dev':cm.seismic},
            'precipitation':{'abs':cm.viridis_r,
                             'dev':cm.PuOr},
            'evapo_r'      :{'abs':cm.viridis_r,
                             'dev':cm.PuOr},
            'evapo_p'      :{'abs':cm.viridis_r,
                             'dev':cm.PuOr},
            'cwb'          :{'abs':cm.PuOr,
                             'dev':cm.PuOr}
        }
        #level dict
        self.vminmax_dict = {
            'air_temperature_max' :{'abs':
                                          {'vmax':35.0,'vmin':-35.0,'vdd':0.5},
                                    'dev':
                                          {'vmax':5.0, 'vmin':-5.0, 'vdd':0.1},
                                          },
            'air_temperature_mean':{'abs':
                                          {'vmax':25.0,'vmin':-25.0,'vdd':0.5},
                                    'dev':
                                          {'vmax':5.0, 'vmin':-5.0, 'vdd':0.1},
                                          },
            'air_temperature_min' :{'abs':
                                          {'vmax':25.0,'vmin':-25.0,'vdd':0.5},
                                    'dev':
                                          {'vmax':5.0, 'vmin':-5.0, 'vdd':0.1},
                                          },
            'precipitation'       :{'abs':
                                          {'vmax':200.0,'vmin':0.0,'vdd':5},
                                    'dev':
                                          {'vmax':100.0, 'vmin':-100.0, 'vdd':5},
                                          }
        }
        # title
        self.var_title_dict = {
            'air_temperature_max' :{'long' :'Maximale Temperatur [{}]'.format(self.unit_dict['air_temperature_max']),
                                    'abs'  :'$\overline{T_{max}}$',
                                    'dev'  :'$T_{max}$',
                                    'short':'Maximaltemperatur'},
            'air_temperature_mean':{'long' :'Mittlere Temperatur [{}]'.format(self.unit_dict['air_temperature_mean']),
                                    'abs'  :'$\overline{T_{mean}}$',
                                    'dev'  :'$T_{mean}$',
                                    'short':'Mitteltemperatur'},
            'air_temperature_min' :{'long' :'Minimale Temperatur [{}]'.format(self.unit_dict['air_temperature_min']),
                                    'abs'  :'$\overline{T_{min}}$',
                                    'dev'  :'$T_{min}$',
                                    'short':'Minimaltemperatur'},
            'precipitation'       :{'long' :'Niederschlagssumme [{}]'.format(self.unit_dict['precipitation']),
                                    'abs'  :'$P_{mean}$',
                                    'dev'  :'$P_{mean}$',
                                    'short':'Niederschlagssumme'},
        }


        # position in case mean value is desired 
        # according to coordinaters used (epsg) it should be right under the month plot
        self.x_txt_mean = 0.20
        self.y_txt_mean = -0.15
        

    def plot_raster_data(self,lons,lats,data,varp,
                         ptype='abs',
                         ax=None,
                         title=None,
                         dmean=False,
                         **kwargs):
        """ Simple contour plot """

        try:
            adm1_shapes = list(shpreader.Reader(self.shape_dir+self.shape_fil).geometries())
        except:
            if(self.debug):
                print(f"Could not read shape file {self.shape_dir+self.shape_fil}")
            pass

        if(ax is None):
            fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})

        try:
            ax.add_geometries(adm1_shapes, ccrs.PlateCarree(),
                              edgecolor='k', facecolor='none', alpha=0.6,zorder=1,linewidth=0.5)    
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
           data_in: 3D array of data; First index denotes month and can be less than 12
           year: Year which is plottet
           varp: Variable which is plottet --> same name as retrieved
           ptype: ['abs' or 'dev'] denotes type of data absolute or deviation. Deviation must contain 
                  Devation in its data. This only handels cmap title and so on
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
                # nasty bug in matplotlib as all masked values is not possible to plot --> blend out with alpha = 0.0
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

        filename = f"{self.plot_dir}{varp}_{year}_{ptype}.png"

        if(self.debug):
            print(f"Save to: {filename}")
        plt.savefig(filename,bbox_inches='tight')
        # After all close figure
        plt.close(fig) 
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 05 11:40:40 2021

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: This module creates plots
"""

#import system modules
from sqlite3 import Timestamp
from turtle import color
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mc
import matplotlib.gridspec as gridspec
import matplotlib as mpl
import numpy as np
import seaborn as sns

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader

from ..helper.hfunctions import moving_average

# activate seaborn plotting settings
sns.set('talk')
#sns.set_style("whitegrid", {'axes.grid': False,'axes.edgecolor':'1.0'})
sns.set_style("whitegrid", {'axes.grid': False})
#sns.set_context('talk')

class plot_handler(dict):
    def __init__(self,
                 plot_dir,
                 shape_dir=None,
                 shape_fil=None,
                 debug=False,
                 creator=None):
        # safe init settings
        self.plot_dir = plot_dir
        self.shape_dir = shape_dir
        self.shape_fil = shape_fil
        self.debug     = debug
        self.creator   = creator


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
            'air_temperature':'$\degree$C',
            'air_temperature_min':'$\degree$C',
            'pressure':'hPa',
            'humidity':'%',
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
                             'per':cm.PuOr,
                             'dev':cm.PuOr},
            'sunshine_duration':{'abs':cm.viridis_r,
                             'per':cm.cividis,
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
            'evapo_p'             :{'long' :'Potentielle Verdunstung [{}]'.format(self.unit_dict['evapo_p']),
                                    'abs'  :'$evap_{mean}$',
                                    'dev'  :'$evap_{mean}$',
                                    'short':'Pot. Verdunstung'},
            'evapo_r'             :{'long' :'Reale Verdunstung [{}]'.format(self.unit_dict['evapo_r']),
                                    'abs'  :'$evar_{mean}$',
                                    'dev'  :'$evar_{mean}$',
                                    'short':'Reale Verdunstung'},
            'cwb'                 :{'long' :'Klimatische Wasserbilanz [{}]'.format(self.unit_dict['cwb']),
                                    'abs'  :'$KWB_{mean}$',
                                    'dev'  :'$KWB_{mean}$',
                                    'short':'Klimatische Wasserbilanz'},
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
        #fig, axs = plt.subplots(rows,columns, figsize=(10,8),
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
            plt.text(0.5,-0.1,'Datengrundlage:DWD',fontsize=10,transform=cax.transAxes)

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
           ptype: ['abs' or 'dev'] denotes type of data absolute or deviation. Deviation must contain 
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
        plt.text(1.048,0.2,f'Visualisierung: {self.creator}',fontsize=10,transform=ax.transAxes)

        filename = f"{self.plot_dir}{varp}_{year}_{ptype}.png"

        if(self.debug):
            print(f"Save to: {filename}")
        plt.savefig(filename,bbox_inches='tight')
        # After all close figure
        plt.close(fig) 

    def plot_station_meteo(self,df_in,var_plot=['TT_10'],var_cat=['air_temperature']):
        """Plots simple station meteogramm"""

        tot_len = len(var_plot)
        fig, ax = plt.subplots(tot_len,1,figsize=(10,6))

        i = 0
        for var, varc in zip(var_plot,var_cat):
            df_in[var].plot(ax=ax[i])
            ax[i].set_ylabel(self.unit_dict[varc])
            if(i < tot_len-1):
                ax[i].axes.get_xaxis().set_visible(False)
            i += 1

        plt.show()

    def plot_regavg_thermopluvio(self,date_arr,temp_dev,prec_dev,
                                 stepwise=None,
                                 title=None,
                                 xlim=None,
                                 ylim=None):
        """
           Plots Thermopluviogram of DWD regional average 
           date_arr:  Date Array
           temp_dev:  Temperature array containing deviation
           prec_dev:  Precipitation array containing deviation
           stepwise:  step to combine years using the same --> for example 10 will do a 10 years step before changing color
           title:     Title (default: None)
           xlim:      setting xlim (default: None --> -2.5,2.5)
           ylim:      setting ylim (default: None --> -250,250)
        """

        fig, ax = plt.subplots(figsize=(10,8))

        fsyl_size = 14
        fs_cbar   = 12
        fs_legend = 8
        axlc      = 'k'
        axla      = 0.7
        axls      = '--'
        color_names = ['green', 'blue', 'cyan','lime','darkgreen','navy','red', 'plum', 'olivedrab', 'orangered', 'firebrick', 'saddlebrown', 'darkorange', 
                       'gold','ligthcoral','purple']

        # is a step given?
        if(stepwise is not None):
            steps = np.arange(round(date_arr.year[0],-1),round(date_arr.year[-2],-1)+stepwise,stepwise)
            color_names = self.make_colors_norm(norm_size=[0,len(steps)],cmap=cm.plasma,data_in=np.arange(0,len(steps)+1))
            for i in range(len(steps)-1):
                cond = np.isin(date_arr.year,np.arange(steps[i],steps[i+1]))
                if(steps[i+1] > date_arr.year[-2]):
                    label = f'{steps[i]} - {date_arr.year[-2]}'
                else:
                    label = f'{steps[i]} - {steps[i+1]}'
                ax.scatter(temp_dev[cond],prec_dev[cond],label=label,color=color_names[i])
                print(steps[i],steps[i+1])
        # no step given --> plot only last one with different colored marker
        else:
            ax.scatter(temp_dev[:len(temp_dev)-1],prec_dev[:len(temp_dev)-1],label=f'{date_arr[0].year} - {date_arr[len(date_arr)-2].year}')
        ax.scatter(temp_dev[-1],prec_dev[-1],color='red',marker='v',label=f'{date_arr[-1].year}')

        ax.axhline(0,color=axlc,zorder=0,alpha=axla,linestyle=axls)
        ax.axvline(0,color=axlc,zorder=0,alpha=axla,linestyle=axls)

        ax.set_xlim(-2.5,2.5)
        ax.set_ylim(-250,250)

        ax.set_xlabel(self.unit_dict['air_temperature_mean'])
        ax.set_ylabel(self.unit_dict['precipitation'])

        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels,loc='upper left',fontsize=fs_legend)

        plt.show()

    def plot_regavg_year_tps(self,date_arr,temp,prec,sd,
                             temp_dev,prec_dev,sd_dev,
                             title=None):
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

        fig, axs = plt.subplots(3,2,figsize=(14,10))

        fsyl_size = 14
        fs_cbar   = 12
        fs_legend = 8

        # plot temperature
        ax = axs[0,0]
        ax.plot_date(date_arr,temp,'.',color='k',label='Mitteltemperatur')
        tmp_arr = np.full_like(temp,-999.)
        tmp_arr[4:] = moving_average(temp,5)
        tmp_arr = np.ma.masked_where(tmp_arr == -999.,tmp_arr)
        ax.plot_date(date_arr,tmp_arr,'-',color='tomato',label='Gleitendes Mittel (5j)')
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels,loc='upper left',fontsize=fs_legend)
        ax.set_xticks([])
        ax.set_xlim(date_arr[0],date_arr[-1])
        ax.set_ylabel('[$^\circ C$]',fontsize=fsyl_size)
        ax = axs[0,1]
        var_t = 'air_temperature_mean'
        ptypet = 'dev'
        cmap = self.cmap_dict[var_t][ptypet]
        norm_size = [self.vminmax_dict_regavgyear[var_t][ptypet]['vmin'],self.vminmax_dict_regavgyear[var_t][ptypet]['vmax']]
        normalize = self.make_stripe_plot(date_arr,temp_dev,ax,cmap,norm_size,lretnorm=True)
        ax.set_xticks([])
        ax.set_xlim(date_arr[0],date_arr[-1])

        cax, _ = mpl.colorbar.make_axes(ax,shrink=0.65,fraction=0.03,pad=0.04,anchor=(2.0,0.5))
        cbar   = mpl.colorbar.ColorbarBase(cax,cmap=cmap,norm=normalize,extend='both')
        cbar.set_label(self.unit_dict[var_t],fontsize=fs_cbar)

        # plot precipitation
        ax = axs[1,0]
        ax.plot_date(date_arr,prec,'.',color='k',label='Niederschlagssumme')
        tmp_arr = np.full_like(temp,-999.)
        tmp_arr[4:] = moving_average(prec,5)
        tmp_arr = np.ma.masked_where(tmp_arr == -999.,tmp_arr)
        ax.plot_date(date_arr,tmp_arr,'-',color='royalblue',label='Gleitendes Mittel (5j)')
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels,loc='upper left',fontsize=fs_legend)
        ax.set_xticks([])
        ax.set_xlim(date_arr[0],date_arr[-1])
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
        ax.set_xlim(date_arr[0],date_arr[-1])

        cax, _ = mpl.colorbar.make_axes(ax,shrink=0.65,fraction=0.03,pad=0.04,anchor=(2.0,0.5))
        cbar   = mpl.colorbar.ColorbarBase(cax,cmap=cmap,norm=normalize,extend='both')
        cbar.set_label('%',fontsize=fs_cbar)

        # plot sunshine duration
        ax = axs[2,0]
        ax.plot_date(date_arr,sd,'.',color='k',label='Sonnenscheindauer')
        tmp_arr = np.full_like(sd,-999.)
        tmp_arr[4:] = moving_average(sd,5)
        #print(sd)
        tmp_arr = np.ma.masked_where(tmp_arr == -999.,tmp_arr)
        # to avoid error message replace mask with nan
        tmp_arr = tmp_arr.filled(np.nan)
        ax.plot_date(date_arr,tmp_arr,'-',color='orange',label='Gleitendes Mittel (5j)')
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels,loc='upper left',fontsize=fs_legend)
        ax.set_xlim(date_arr[0],date_arr[-1])
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
        ax.set_xlim(date_arr[0],date_arr[-1])
        ax.tick_params(axis='x', labelrotation=45)

        cax, _ = mpl.colorbar.make_axes(ax,shrink=0.65,fraction=0.03,pad=0.04,anchor=(2.0,0.5))
        cbar   = mpl.colorbar.ColorbarBase(cax,cmap=cmap,norm=normalize,extend='both')
        cbar.set_label('%',fontsize=fs_cbar)

        if(title is not None):
            fig.suptitle(title,fontsize=18)

        # final adjustments
        plt.subplots_adjust(left=0.1, bottom=0.1, right=0.89, top=0.88, wspace=0.05, hspace=0.15) 

        filename = f"{self.plot_dir}/regyear_temp_prec_sd.png"

        if(self.debug):
            print(f"Save to: {filename}")

        plt.savefig(filename,bbox_inches='tight',pad_inches=0)
        # close figure at the end
        plt.close(fig)

    def plot_regavg_year(self,date_arr,data_arr,var_in,
                         ptype='abs',pbar=False,pstripes=False,
                         title=None):
        """ Plots DWD regional average on a yearly resolution
            date_arr: Date array (mostly only the year)
            data_arr: Data array
            ptype:    Type of Plot --> 'abs' (default) absolut values, 'dev' devation --> Data must be absolute values or deviation and is not calculated here!
            pbar:     Plot data as bar plot (default False)
            pstripes: Plot data as stripes (Ed Hawking stripes) plot (default False)
            title:    Give the plot a title (default is None and therefore a string is generated from self.var_title_dict)
        """

        fig, ax = plt.subplots(1,1,figsize=(12,6)) 

        norm_size = [self.vminmax_dict_regavgyear[var_in][ptype]['vmin'],self.vminmax_dict_regavgyear[var_in][ptype]['vmax']]
        cmap = self.cmap_dict[var_in][ptype]
        fs_cbar = 12
        datemin = pd.Timestamp(f'{date_arr.year[0]  - 1}-01-01')
        datemax = pd.Timestamp(f'{date_arr.year[-1] + 1}-01-01')
        if(pbar):
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

            ax.text(1.03,0.125,'Daten: DWD',fontsize=8,transform=ax.transAxes)
            ax.text(1.03,0.1,f'Visualisierung: {self.creator}',fontsize=8,transform=ax.transAxes)
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

        filename = f"{self.plot_dir}{varp}_{year}_{ptype}.png"
        if(self.debug):
            print(f"Save to: {filename}")
        plt.savefig(filename,bbox_inches='tight',pad_inches=0)
        #plt.show()
        # After all close figure
        plt.close(fig) 
    
    def make_bar_plot(self,date_in,data_in,ax_in,norm_size,cmap,lretnorm=False):
        """ Makes bar plot with given input data
        """

        if(lretnorm):
            colors,normalize = self.make_colors_norm(norm_size,cmap,data_in,lretnorm=lretnorm)
        else:
            colors = self.make_colors_norm(norm_size,cmap,data_in,lretnorm=lretnorm)
        barplot = ax_in.bar(date_in,data_in,width=200.0,edgecolor='k')
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
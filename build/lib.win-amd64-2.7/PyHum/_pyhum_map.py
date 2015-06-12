## PyHum (Python program for Humminbird(R) data processing) 
## has been developed at the Grand Canyon Monitoring & Research Center,
## U.S. Geological Survey
##
## Author: Daniel Buscombe
## Project homepage: <https://github.com/dbuscombe-usgs/PyHum>
##
##This software is in the public domain because it contains materials that originally came from 
##the United States Geological Survey, an agency of the United States Department of Interior. 
##For more information, see the official USGS copyright policy at 
##http://www.usgs.gov/visual-id/credit_usgs.html#copyright
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
## See the GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/>.

#"""
# ____        _   _                         
#|  _ \ _   _| | | |_   _ _ __ ___    _   _ 
#| |_) | | | | |_| | | | | '_ ` _ \  (_) (_)
#|  __/| |_| |  _  | |_| | | | | | |  _   _ 
#|_|    \__, |_| |_|\__,_|_| |_| |_| (_) (_)
#       |___/                               
#
#                        
#   ____ ___  ____ _____ 
#  / __ `__ \/ __ `/ __ \
# / / / / / / /_/ / /_/ /
#/_/ /_/ /_/\__,_/ .___/ 
#               /_/      
#
##+-+-+ +-+-+-+-+-+-+ +-+-+-+-+-+-+-+-+
#|b|y| |D|a|n|i|e|l| |B|u|s|c|o|m|b|e|
#+-+-+ +-+-+-+-+-+-+ +-+-+-+-+-+-+-+-+
#+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#|d|b|u|s|c|o|m|b|e|@|u|s|g|s|.|g|o|v|
#+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#+-+-+-+-+ +-+-+-+-+-+-+-+-+-+-+ +-+-+-+-+-+-+
#|U|.|S|.| |G|e|o|l|o|g|i|c|a|l| |S|u|r|v|e|y|
#+-+-+-+-+ +-+-+-+-+-+-+-+-+-+-+ +-+-+-+-+-+-+

#"""

# =========================================================
# ====================== libraries ======================
# =========================================================

# operational
from __future__ import division
from scipy.io import loadmat
import os, time, sys, getopt
try:
   from Tkinter import Tk
   from tkFileDialog import askopenfilename, askdirectory
except:
   pass
from joblib import Parallel, delayed, cpu_count
import pyproj

# numerical
import numpy as np
import pyproj
import PyHum.utils as humutils
from scipy.interpolate import griddata
from scipy.spatial import cKDTree as KDTree
from scipy.ndimage.filters import median_filter

# plotting
import matplotlib.pyplot as plt
try:
   from mpl_toolkits.basemap import Basemap
except:
   print "Error: Basemap could not be imported"
   pass
import simplekml

# suppress divide and invalid warnings
np.seterr(divide='ignore')
np.seterr(invalid='ignore')

__all__ = [
    'map',
    'custom_save',
    'custom_save2',    
    'bearingBetweenPoints',
    'calc_beam_pos',
    ]

#################################################
def map(humfile, sonpath, cs2cs_args, dogrid, calc_bearing, filt_bearing, res, cog):
         
    '''
    Create plots of the spatially referenced sidescan echograms
    using the algorithm detailed by Buscombe et al. (forthcoming)

    Syntax
    ----------
    [] = PyHum.map(humfile, sonpath, cs2cs_args, dogrid, calc_bearing, filt_bearing, res, cog)

    Parameters
    ----------
    humfile : str
       path to the .DAT file
    sonpath : str
       path where the *.SON files are
    cs2cs_args : int, *optional* [Default="epsg:26949"]
       arguments to create coordinates in a projected coordinate system
       this argument gets given to pyproj to turn wgs84 (lat/lon) coordinates
       into any projection supported by the proj.4 libraries
    dogrid : float, *optional* [Default=1]
       if 1, textures will be gridded with resolution 'res'. 
       Otherwise, point cloud will be plotted
    calc_bearing : float, *optional* [Default=0]
       if 1, bearing will be calculated from coordinates
    filt_bearing : float, *optional* [Default=0]
       if 1, bearing will be filtered
    res : float, *optional* [Default=0.1]
       grid resolution of output gridded texture map
    cog : int, *optional* [Default=1]
       if 1, heading calculated assuming GPS course-over-ground rather than
       using a compass

    Returns
    -------
    sonpath+'x_y_ss_raw'+str(p)+'.asc'  : text file
        contains the point cloud of easting, northing, and sidescan intensity
        of the pth chunk

    sonpath+'GroundOverlay'+str(p)+'.kml': kml file
        contains gridded (or point cloud) sidescan intensity map for importing into google earth
        of the pth chunk

    sonpath+'map'+str(p)+'.png' : 
        image overlay associated with the kml file

    '''

    # prompt user to supply file if no input file given
    if not humfile:
       print 'An input file is required!!!!!!'
       Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
       inputfile = askopenfilename(filetypes=[("DAT files","*.DAT")]) 

    # prompt user to supply directory if no input sonpath is given
    if not sonpath:
       print 'A *.SON directory is required!!!!!!'
       Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
       sonpath = askdirectory() 

    # print given arguments to screen and convert data type where necessary
    if humfile:
       print 'Input file is %s' % (humfile)

    if sonpath:
       print 'Sonar file path is %s' % (sonpath)

    if cs2cs_args:
       print 'cs2cs arguments are %s' % (cs2cs_args)

    if dogrid:
       dogrid = int(dogrid)
       if dogrid==1:
          print "Data will be gridded"      

    if calc_bearing:
       calc_bearing = int(calc_bearing)
       if calc_bearing==1:
          print "Bearing will be calculated from coordinates"     
 
    if filt_bearing:
       filt_bearing = int(filt_bearing)
       if filt_bearing==1:
          print "Bearing will be filtered"      

    if res:
       res = np.asarray(res,float)
       print 'Gridding resolution: %s' % (str(res))      

    if cog:
       cog = int(cog)
       if cog==1:
          print "Heading based on course-over-ground" 

    if not cs2cs_args:
       # arguments to pass to cs2cs for coordinate transforms
       cs2cs_args = "epsg:26949"
       print '[Default] cs2cs arguments are %s' % (cs2cs_args)

    if not dogrid:
       if dogrid != 0:
          dogrid = 1
          print "[Default] Data will be gridded"

    if not calc_bearing:
       if calc_bearing != 1:
          calc_bearing = 0
          print "[Default] Heading recorded by instrument will be used"

    if not filt_bearing:
       if filt_bearing != 1:
          filt_bearing = 0
          print "[Default] Heading will not be filtered"

    if not res:
       res = 0.05
       print '[Default] Grid resolution is %s m' % (str(res))

    if not cog:
       if cog != 0:
          cog = 1
          print "[Default] Heading based on course-over-ground"

    trans =  pyproj.Proj(init=cs2cs_args)

    # if son path name supplied has no separator at end, put one on
    if sonpath[-1]!=os.sep:
       sonpath = sonpath + os.sep

    base = humfile.split('.DAT') # get base of file name for output
    base = base[0].split(os.sep)[-1]

    esi = np.squeeze(loadmat(sonpath+base+'meta.mat')['e'])
    nsi = np.squeeze(loadmat(sonpath+base+'meta.mat')['n']) 

    pix_m = np.squeeze(loadmat(sonpath+base+'meta.mat')['pix_m'])
    dep_m = np.squeeze(loadmat(sonpath+base+'meta.mat')['dep_m'])
    c = np.squeeze(loadmat(sonpath+base+'meta.mat')['c'])

    # over-ride measured bearing and calc from positions
    if calc_bearing==1:
       lat = np.squeeze(loadmat(sonpath+base+'meta.mat')['lat'])
       lon = np.squeeze(loadmat(sonpath+base+'meta.mat')['lon']) 

       #point-to-point bearing
       bearing = np.zeros(len(lat))
       for k in xrange(len(lat)-1):
          bearing[k] = bearingBetweenPoints(lat[k], lat[k+1], lon[k], lon[k+1])
       del lat, lon

    else:
       # reported bearing by instrument (Kalman filtered?)
       bearing = np.squeeze(loadmat(sonpath+base+'meta.mat')['heading'])

    ## bearing can only be observed modulo 2*pi, therefore phase unwrap
    #bearing = np.unwrap(bearing)

    # if stdev in heading is large, there's probably noise that needs to be filtered out
    if np.std(bearing)>180:
       print "WARNING: large heading stdev - attempting filtering"
       from sklearn.cluster import MiniBatchKMeans
       # can have two modes
       data = np.column_stack([bearing, bearing])
       k_means = MiniBatchKMeans(2)
       # fit the model
       k_means.fit(data) 
       values = k_means.cluster_centers_.squeeze()
       labels = k_means.labels_

       if np.sum(labels==0) > np.sum(labels==1):
          bearing[labels==1] = np.nan
       else:
          bearing[labels==0] = np.nan

       nans, y= humutils.nan_helper(bearing)
       bearing[nans]= np.interp(y(nans), y(~nans), bearing[~nans])

       # save this filtered version to file
       meta = loadmat(sonpath+base+'meta.mat')
       meta['heading_filt'] = bearing
       savemat(sonpath+base+'meta.mat', meta ,oned_as='row')
       del meta   

    if filt_bearing ==1:
       bearing = humutils.runningMeanFast(bearing, len(bearing)/100)

    theta = np.asarray(bearing, 'float')/(180/np.pi)

    if cog==1:
       #course over ground is given as a compass heading (ENU) from True north, or Magnetic north.
       #To get this into NED (North-East-Down) coordinates, you need to rotate the ENU 
       # (East-North-Up) coordinate frame. 
       #Subtract pi/2 from your heading
       theta = theta - np.pi/2
       # (re-wrap to Pi to -Pi)
       theta = np.unwrap(-theta)

    # load memory mapped scans
    shape_port = np.squeeze(loadmat(sonpath+base+'meta.mat')['shape_port'])
    if shape_port!='':
       port_fp = np.memmap(sonpath+base+'_data_port_l.dat', dtype='float32', mode='r', shape=tuple(shape_port))

    shape_star = np.squeeze(loadmat(sonpath+base+'meta.mat')['shape_star'])
    if shape_star!='':
       star_fp = np.memmap(sonpath+base+'_data_star_l.dat', dtype='float32', mode='r', shape=tuple(shape_star))

    # time varying gain
    tvg = ((8.5*10**-5)+(3/76923)+((8.5*10**-5)/4))*c
        
    # depth correction
    dist_tvg = ((np.tan(np.radians(25)))*dep_m)-(tvg)

    for p in xrange(len(star_fp)):
       make_map(esi[shape_port[-1]*p:shape_port[-1]*(p+1)], nsi[shape_port[-1]*p:shape_port[-1]*(p+1)], theta[shape_port[-1]*p:shape_port[-1]*(p+1)], dist_tvg[shape_port[-1]*p:shape_port[-1]*(p+1)], port_fp[p], star_fp[p], pix_m, res, cs2cs_args, sonpath, p, dogrid)


# =========================================================
def custom_save(figdirec,root):
    plt.savefig(figdirec+root,bbox_inches='tight',dpi=400,transparent=True)

# =========================================================
def calc_beam_pos(dist, bearing, x, y):

   dist_x, dist_y = (dist*np.sin(bearing), dist*np.cos(bearing))
   xfinal, yfinal = (x + dist_x, y + dist_y)
   return (xfinal, yfinal)

# =========================================================
def bearingBetweenPoints(pos1_lat, pos2_lat, pos1_lon, pos2_lon):
   lat1 = np.deg2rad(pos1_lat)
   lon1 = np.deg2rad(pos1_lon)
   lat2 = np.deg2rad(pos2_lat)
   lon2 = np.deg2rad(pos2_lon)

   bearing = np.arctan2(np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(lon2 - lon1), np.sin(lon2 - lon1) * np.cos(lat2))

   db = np.rad2deg(bearing)
   return (90.0 - db + 360.0) % 360.0

# =========================================================
def make_map(e, n, t, d, dat_port, dat_star, pix_m, res, cs2cs_args, sonpath, p, dogrid):
   
   trans =  pyproj.Proj(init=cs2cs_args)   
   
   merge = np.vstack((dat_port,dat_star))
   #merge = np.vstack((np.flipud(port_fp[p]),star_fp[p]))
   
   merge[np.isnan(merge)] = 0

   merge = merge[:,:len(n)]

   # get number pixels in scan line
   extent = int(np.shape(merge)[0]/2)

   yvec = np.linspace(pix_m,extent*pix_m,extent)

   print "getting point cloud ..."
   # get the points by rotating the [x,y] vector so it lines up with boat heading, assumed to be the same as the curvature of the [e,n] trace
   X=[]; Y=[];
   for k in range(len(n)): 
      x = np.concatenate((np.tile(e[k],extent) , np.tile(e[k],extent)))
      #y = np.concatenate((n[k]+yvec, n[k]-yvec))
      rangedist = np.sqrt(np.power(yvec, 2.0) - np.power(d[k], 2.0))
      y = np.concatenate((n[k]+rangedist, n[k]-rangedist))
      # Rotate line around center point
      xx = e[k] - ((x - e[k]) * np.cos(t[k])) - ((y - n[k]) * np.sin(t[k]))
      yy = n[k] - ((x - e[k]) * np.sin(t[k])) + ((y - n[k]) * np.cos(t[k]))
      xx, yy = calc_beam_pos(d[k], t[k], xx, yy)
      X.append(xx)
      Y.append(yy) 

   del e, n, t, x, y #, X, Y

   # merge flatten and stack
   X = np.asarray(X,'float').T
   X = X.flatten()

   # merge flatten and stack
   Y = np.asarray(Y,'float').T
   Y = Y.flatten()

   X = X[np.where(np.logical_not(np.isnan(Y)))]
   merge = merge.flatten()[np.where(np.logical_not(np.isnan(Y)))]
   Y = Y[np.where(np.logical_not(np.isnan(Y)))]

   Y = Y[np.where(np.logical_not(np.isnan(X)))]
   merge = merge.flatten()[np.where(np.logical_not(np.isnan(X)))]
   X = X[np.where(np.logical_not(np.isnan(X)))]


   X = X[np.where(np.logical_not(np.isnan(merge)))]
   Y = Y[np.where(np.logical_not(np.isnan(merge)))]
   merge = merge[np.where(np.logical_not(np.isnan(merge)))]

   # write raw bs to file
   outfile = sonpath+'x_y_ss_raw'+str(p)+'.asc' 
   with open(outfile, 'w') as f:
      np.savetxt(f, np.hstack((humutils.ascol(X.flatten()),humutils.ascol(Y.flatten()), humutils.ascol(merge.flatten()))), delimiter=' ', fmt="%8.6f %8.6f %8.6f")

   humlon, humlat = trans(X, Y, inverse=True)

   if dogrid==1:
      grid_x, grid_y = np.meshgrid( np.arange(np.min(X), np.max(X), res), np.arange(np.min(Y), np.max(Y), res) )  

      dat = griddata(np.c_[X.flatten(),Y.flatten()], merge.flatten(), (grid_x, grid_y), method='nearest') 

      ## create mask for where the data is not
      tree = KDTree(np.c_[X.flatten(),Y.flatten()])
      dist, _ = tree.query(np.c_[grid_x.ravel(), grid_y.ravel()], k=1)
      dist = dist.reshape(grid_x.shape)

   del X, Y #, bearing #, pix_m, yvec

   if dogrid==1:
      ## mask
      dat[dist> np.floor(np.sqrt(1/res))-1 ] = np.nan #np.floor(np.sqrt(1/res))-1 ] = np.nan
      del dist, tree

      dat[dat==0] = np.nan
      dat[np.isinf(dat)] = np.nan
      datm = np.ma.masked_invalid(dat)

      glon, glat = trans(grid_x, grid_y, inverse=True)
      del grid_x, grid_y

   try:
      print "drawing and printing map ..."
      fig = plt.figure(frameon=False)
      map = Basemap(projection='merc', epsg=cs2cs_args.split(':')[1], #26949,
       resolution = 'i', #h #f
       llcrnrlon=np.min(humlon)-0.001, llcrnrlat=np.min(humlat)-0.001,
       urcrnrlon=np.max(humlon)+0.001, urcrnrlat=np.max(humlat)+0.001)

      if dogrid==1:
         gx,gy = map.projtran(glon, glat)

      ax = plt.Axes(fig, [0., 0., 1., 1.], )
      ax.set_axis_off()
      fig.add_axes(ax)

      if dogrid==1:
         map.pcolormesh(gx, gy, datm, cmap='gray', vmin=np.nanmin(dat), vmax=np.nanmax(dat))
         del datm, dat
      else: 
         ## draw point cloud
         x,y = map.projtran(humlon, humlat)
         map.scatter(x.flatten(), y.flatten(), 0.5, merge.flatten(), cmap='gray', linewidth = '0')

      custom_save(sonpath,'map'+str(p))
      del fig 

   except:
      print "error: map could not be created..."

   kml = simplekml.Kml()
   ground = kml.newgroundoverlay(name='GroundOverlay')
   ground.icon.href = 'map'+str(p)+'.png'
   ground.latlonbox.north = np.min(humlat)-0.001
   ground.latlonbox.south = np.max(humlat)+0.001
   ground.latlonbox.east =  np.max(humlon)+0.001
   ground.latlonbox.west =  np.min(humlon)-0.001
   ground.latlonbox.rotation = 0

   kml.save(sonpath+'GroundOverlay'+str(p)+'.kml')

   del humlat, humlon


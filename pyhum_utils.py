'''
pyhum_utils.py
Part of PyHum software 

INFO:
helper functions and utilities

Author:    Daniel Buscombe
           Grand Canyon Monitoring and Research Center
           United States Geological Survey
           Flagstaff, AZ 86001
           dbuscombe@usgs.gov
Version: 1.0      Revision: June, 2014

For latest code version please visit:
https://github.com/dbuscombe-usgs

This function is part of 'PyHum' software
This software is in the public domain because it contains materials that originally came from the United States Geological Survey, an agency of the United States Department of Interior. 
For more information, see the official USGS copyright policy at 
http://www.usgs.gov/visual-id/credit_usgs.html#copyright

Any use of trade, product, or firm names is for descriptive purposes only and does not imply endorsement by the U.S. government.

This software has been tested with Python 2.7 on Linux Fedora 16 & 20, Ubuntu 12.4 & 13.4, and Windows 7.
This software has (so far) been used only with Humminbird 998 series instruments. 

Installation:

PYTHON LIBRARIES YOU MAY NEED TO INSTALL TO USE PyHum:
1) Joblib: http://pythonhosted.org/joblib/
2) Pyproj: http://code.google.com/p/pyproj/
3) SciPy: http://www.scipy.org/scipylib/download.html
4) Numpy: http://www.scipy.org/scipylib/download.html
5) Matplotlib: http://matplotlib.org/downloads.html
6) Scikit-learn: http://scikit-learn.org/stable/
7) Python Image LIbrary (PIL) http://www.pythonware.com/products/pil/

All of the above are available through pip (https://pypi.python.org/pypi/pip) and easy_install (https://pythonhosted.org/setuptools/easy_install.html)

OTHER LIBRARIES (CYTHON) NEED TO BE COMPILED FOR SPEED:
1) pyread.pyx
2) cwt.pyx
3) replace_nans.pyx
- use the shell script "compile_pyhum.sh" on linux/mac

'''

from numpy.lib.stride_tricks import as_strided as ast
from numpy import array, product, isnan, min, max, convolve, isnan, ones, mean, std, argmax, where, interp, shape, zeros, hstack, vstack, argmin, squeeze, choose, linspace, r_, cumsum, histogram, any, seterr

from numpy import nan as npnan
from numpy.matlib import repmat

from sklearn.cluster import KMeans
from scipy.interpolate import RectBivariateSpline

# suppress divide and invalid warnings
seterr(divide='ignore')
seterr(invalid='ignore')

# =========================================================
def ascol( arr ):
    '''
    reshapes row matrix to be a column matrix (N,1).
    '''
    if len( arr.shape ) == 1: arr = arr.reshape( ( arr.shape[0], 1 ) )
    return arr 

# =========================================================
def rm_spikes(dat,numstds):
    """
    remove spikes in dat
    """
    ht = mean(dat) + numstds*std(dat)
    lt = argmax(mean(dat) - numstds*std(dat),0)

    index = where(dat>ht); 
    if index:
      dat[index] = npnan

    index = where(dat<lt); 
    if index: 
      dat[index] = npnan

    # fill nans using linear interpolation
    nans, y= nan_helper(dat)
    dat[nans]= interp(y(nans), y(~nans), dat[~nans])

    return dat

# =========================================================
def rescale(dat,mn,mx):
    """
    rescales an input dat between mn and mx
    """
    m = min(dat.flatten())
    M = max(dat.flatten())
    return (mx-mn)*(dat-m)/(M-m)+mn

# =========================================================
def runningMeanFast(x, N):
    '''
    flawed but fast running mean
    '''
    x = convolve(x, ones((N,))/N)[(N-1):]
    # the last N values will be crap, so they're set to the global mean
    x[-N:] = x[-N]
    return x

# =========================================================
def nan_helper(y):
   '''
   function to help manage indices of nans
   '''
   return isnan(y), lambda z: z.nonzero()[0]

# =========================================================
def norm_shape(shap):
    '''
    Normalize numpy array shapes so they're always expressed as a tuple, 
    even for one-dimensional shapes.
    '''
    try:
        i = int(shap)
        return (i,)
    except TypeError:
        # shape was not a number
        pass
 
    try:
        t = tuple(shap)
        return t
    except TypeError:
        # shape was not iterable
        pass
     
    raise TypeError('shape must be an int, or a tuple of ints')

# =========================================================
# Return a sliding window over a in any number of dimensions
def sliding_window(a,ws,ss = None,flatten = True):
    '''
    Return a sliding window over a in any number of dimensions
    '''
    if None is ss:
        # ss was not provided. the windows will not overlap in any direction.
        ss = ws
    ws = norm_shape(ws)
    ss = norm_shape(ss)
    # convert ws, ss, and a.shape to numpy arrays
    ws = array(ws)
    ss = array(ss)
    shap = array(a.shape)
    # ensure that ws, ss, and a.shape all have the same number of dimensions
    ls = [len(shap),len(ws),len(ss)]
    if 1 != len(set(ls)):
        raise ValueError(\
        'a.shape, ws and ss must all have the same length. They were %s' % str(ls))
     
    # ensure that ws is smaller than a in every dimension
    if any(ws > shap):
        raise ValueError(\
        'ws cannot be larger than a in any dimension.\
 a.shape was %s and ws was %s' % (str(a.shape),str(ws)))
    # how many slices will there be in each dimension?
    newshape = norm_shape(((shap - ws) // ss) + 1)
    # the shape of the strided array will be the number of slices in each dimension
    # plus the shape of the window (tuple addition)
    newshape += norm_shape(ws)
    # the strides tuple will be the array's strides multiplied by step size, plus
    # the array's strides (tuple addition)
    newstrides = norm_shape(array(a.strides) * ss) + a.strides
    a = ast(a,shape = newshape,strides = newstrides)
    if not flatten:
        return a
    # Collapse strided so that it has one more dimension than the window.  I.e.,
    # the new array is a flat list of slices.
    meat = len(ws) if ws.shape else 0
    firstdim = (product(newshape[:-meat]),) if ws.shape else ()
    dim = firstdim + (newshape[-meat:])
    # remove any dimensions with size 1
    dim = filter(lambda i : i != 1,dim) 
    
    return a.reshape(dim), newshape

# =========================================================
def dpboundary(imu):
   '''
   dynamic boundary tracing in an image 
   (translated from matlab: CMP Vision Algorithms http://visionbook.felk.cvut.cz)
   '''
   m,n = shape(imu)  
   c = zeros((m,n))
   p = zeros((m,n))
   c[0,:] = imu[0,:]  
   
   for i in xrange(1,m):
      c0 = c[i-1,:]
      tmp1 = squeeze(ascol(hstack((c0[1:],c0[-1]))))  
      tmp2 = squeeze(ascol(hstack((c0[0], c0[0:len(c0)-1]))))
      d = repmat( imu[i,:], 3, 1 ) + vstack( (c0,tmp1,tmp2) )
      del tmp1, tmp2
      p[i,:] =  argmin(d,axis=0)
      c[i,:] =  min(d,axis=0)

   p[p==0] = -1
   p = p+1

   x = zeros((m,1))
   cost = min(c[-1,:])
   xpos = argmin( c[-1,:] )
   for i in reversed(range(1,m)):
      x[i] = xpos
      if p[i,xpos]==2 and xpos<n:
        xpos = xpos+1
      elif p[i,xpos]==3 and xpos>1:
        xpos = xpos-1
   x[0] = xpos
   return x

## =========================================================
def cut_kmeans(w,numclusters): 
   '''
   perform a k-means segmentation of image
   '''
   wc = w.reshape((-1, 1)) # We need an (n_sample, n_feature) array
   k_means = KMeans(numclusters)
   # fit the model
   k_means.fit(wc) 
   values = k_means.cluster_centers_.squeeze()
   labels = k_means.labels_
   # make the cut and reshape
   wc = choose(labels, values)
   wc.shape = w.shape
   return wc, values

# =========================================================
def im_resize(im,Nx,Ny):
   '''
   resize array by bivariate spline interpolation
   '''
   ny, nx = shape(im)
   xx = linspace(0,nx,Nx)
   yy = linspace(0,ny,Ny)
   newKernel = RectBivariateSpline(r_[:ny],r_[:nx],im) 
   return newKernel(yy,xx)

# =========================================================
def histeq(im,nbr_bins=256):

   im[isnan(im)] = 0
   #get image histogram
   imhist,bins = histogram(im.flatten(),nbr_bins,normed=True)
   cdf = imhist.cumsum() #cumulative distribution function
   cdf = 255 * cdf / cdf[-1] #normalize

   #use linear interpolation of cdf to find new pixel values
   im2 = interp(im.flatten(),bins[:-1],cdf)

   return im2.reshape(im.shape), cdf


## =========================================================
#def spec_noise(im,factor=1.25):
#   cols, rows = np.shape(im)
#   imfft = fftshift(fft2(np.random.randn(cols,rows)))
#   mag = abs(imfft)  
#   phase = imfft/mag  
#   xi, yi = np.meshgrid(np.r_[:rows],np.r_[:cols])  
#   radius = np.sqrt(xi**2 + yi**2)
#   radius[cols/2 + 1, rows/2 + 1] = 1
#   radius[radius==0] = 1
#   filter = np.divide(1,(radius**factor))
#   noise = real(ifft2(fftshift(np.multiply(filter,phase)))) 
#   noise = noise/noise.sum() 
#   return rescale(im_resize(noise[::2,::2],cols,rows),np.nanmin(im),np.nanmax(im))






'''
ppdrc.pyx
Part of PyHum software 

INFO:
Cython script to tone map data using a phase preserving technique

Author:    Daniel Buscombe
           Grand Canyon Monitoring and Research Center
           United States Geological Survey
           Flagstaff, AZ 86001
           dbuscombe@usgs.gov
Version: 1.0      Revision: July, 2014

For latest code version please visit:
https://github.com/dbuscombe-usgs

This function is part of 'PyHum' software
This software is in the public domain because it contains materials that originally came from the United States Geological Survey, an agency of the United States Department of Interior. 
For more information, see the official USGS copyright policy at 
http://www.usgs.gov/visual-id/credit_usgs.html#copyright

Any use of trade, product, or firm names is for descriptive purposes only and does not imply endorsement by the U.S. government.
'''

from __future__ import division
import numpy as np
cimport numpy as np

DTYPEf = np.float64
ctypedef np.float64_t DTYPEf_t

DTYPEc = np.complex128
ctypedef np.complex128_t DTYPEc_t


# =========================================================
cdef class ppdrc:

   cdef object res

   # =========================================================
   def __init__(self, np.ndarray im, int wavelength=768, int n=2):


      # Reference:
      # Peter Kovesi, "Phase Preserving Tone Mapping of Non-Photographic High Dynamic 
      # Range Images".  Proceedings: Digital Image Computing: Techniques and
      # Applications 2012 (DICTA 2012). Available via IEEE Xplore

      # translated from matlab code posted on:
      # http://www.csse.uwa.edu.au/~pk/research/matlabfns/PhaseCongruency/
      cdef int cols
      cdef int rows
      cdef float eps = 2.2204e-16

      rows,cols = np.shape(im)    

      cdef np.ndarray E = np.empty( [rows, cols], dtype=DTYPEf)
      cdef np.ndarray H = np.empty( [rows, cols], dtype=DTYPEf)
      cdef np.ndarray res = np.empty( [rows, cols], dtype=DTYPEf)
      cdef np.ndarray radius = np.empty( [rows, cols], dtype=DTYPEf)
      cdef np.ndarray u1 = np.empty( [rows, cols], dtype=DTYPEf)
      cdef np.ndarray u2 = np.empty( [rows, cols], dtype=DTYPEf)
      cdef np.ndarray ph = np.empty( [rows, cols], dtype=DTYPEf)
      cdef np.ndarray h1f = np.empty( [rows, cols], dtype=DTYPEf)
      cdef np.ndarray h2f = np.empty( [rows, cols], dtype=DTYPEf)
      cdef np.ndarray f = np.empty( [rows, cols], dtype=DTYPEf)

      cdef np.ndarray IM = np.empty( [rows, cols], dtype=DTYPEc)
      cdef np.ndarray H1 = np.empty( [rows, cols], dtype=DTYPEc)
      cdef np.ndarray H2 = np.empty( [rows, cols], dtype=DTYPEc)

      IM = np.fft.fft2(im)

      # Generate horizontal and vertical frequency grids that vary from
      # -0.5 to 0.5 
      u1, u2 = np.meshgrid((np.r_[0:cols]-(np.fix(cols/2)+1))/(cols-np.mod(cols,2)),(np.r_[0:rows]-(np.fix(rows/2)+1))/(rows-np.mod(rows,2)))

      u1 = np.fft.ifftshift(u1)   # Quadrant shift to put 0 frequency at the corners
      u2 = np.fft.ifftshift(u2)
    
      radius = np.sqrt(u1**2 + u2**2)
      # Matrix values contain frequency values as a radius from centre (but quadrant shifted)
    
      # Get rid of the 0 radius value in the middle (at top left corner after
      # fftshifting) so that dividing by the radius, will not cause trouble.
      radius[1,1] = 1
    
      H1 = 1j*u1/radius   # The two monogenic filters in the frequency domain
      H2 = 1j*u2/radius
      H1[1,1] = 0
      H2[1,1] = 0
      radius[1,1] = 0  # undo fudge
 
      # High pass Butterworth filter
      H =  1.0 - 1.0 / (1.0 + (radius * wavelength)**(2*n))       
         
      f = np.real(np.fft.ifft2(H*IM))
      h1f = np.real(np.fft.ifft2(H*H1*IM))
      h2f = np.real(np.fft.ifft2(H*H2*IM))
    
      ph = np.arctan(f/np.sqrt(h1f**2 + h2f**2 + eps))
      E = np.sqrt(f**2 + h1f**2 + h2f**2)
      res = np.sin(ph)*np.log1p(E)
      self.res = res


   # =========================================================    
   def getdata(self):
      return self.res
       

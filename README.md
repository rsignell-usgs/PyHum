### About
PyHum

![alt tag](http://dbuscombe-usgs.github.io/figs/class_R01560.png)
Sand dunes on the bed of the Colorado River in Grand Canyon


![alt tag](http://dbuscombe-usgs.github.io/figs/R00426_map.jpg)
Dog River, Alabama. Credit: Allen Aven, Dauphin Island Sea Lab

Python/Cython scripts to read Humminbird DAT and associated SON files, export data, carry out rudimentary radiometric corrections to data, and classify bed texture using the algorithm detailed in Buscombe, Grams, Smith, "Automated riverbed sediment classification using low-cost sidescan sonar", forthcoming.

### Contributing & Credits

Author:    Daniel Buscombe
           Grand Canyon Monitoring and Research Center
           United States Geological Survey
           Flagstaff, AZ 86001
           dbuscombe@usgs.gov
Version: 1.0.9      Revision: Mar, 2015

For latest code version please visit:
https://github.com/dbuscombe-usgs

This function is part of PyHum software
This software is in the public domain because it contains materials that originally came 
from the United States Geological Survey, an agency of the United States Department of Interior. 
For more information, see the official USGS copyright policy at 
```
http://www.usgs.gov/visual-id/credit_usgs.html#copyright
```

Any use of trade, product, or firm names is for descriptive purposes only and does not imply endorsement by the U.S. government. 

thanks to Barb Fagetter (blueseas@oceanecology.ca) for some format info

This software has been tested with Python 2.7 on Linux Fedora 16 & 20, Ubuntu 12.4 & 13.4 & 14.4, Windows 7.
This software has (so far) been used only with Humminbird 998 and 1198 series instruments. 

### Contents

The programs in this package are as follows:
1) pyhum_read.py
Python script to read Humminbird DAT and associated SON files, and export data in MAT format

2) pyhum_correct.py
Python script to read Humminbird data in MAT format (output from pyhum_read.py) and perform some radiometric corrections and produce some rudimentary plots

3) pyhum_texture.py
Python script to read radiometrically corrected Humminbird data in MAT format (output from pyhum_correct.py) and perform a textural analysis using the spectral method of Buscombe et al (in review) and produce some rudimentary plots

These are all command-line programs which take a number of input (some required, some optional). Please see the individual files for a comprehensive list of input options

### Setup

You could try before you install, using a virtual environment:

```
virtualenv venv
source venv/bin/activate
pip install numpy
pip install Cython
pip install scipy
pip install simplekml
pip install pyproj
pip install scikit-learn
pip install Pillow
pip install matplotlib
pip install basemap --allow-external basemap --allow-unverified basemap
pip install PyHum
python -c "import PyHum; PyHum.test.dotest()"
deactivate (or source venv/bin/deactivate)
```

The results will live in "venv/lib/python2.7/site-packages/PyHum"

Note for Fedora linux users: you need the geos-devel package for basemap, and the blas and libpack libraries for scipy


Automatic Installation from PyPI:

```
pip install PyHum
```

Automatic Installation from github:

```
git clone git@github.com:dbuscombe-usgs/PyHum.git
cd PyHum
python setup.py install
```

or a local installation:

```
python setup.py install --user
```

or with admin privileges, e.g.:

```
sudo python setup.py install
```

Manual Installation:

PYTHON LIBRARIES YOU MAY NEED TO INSTALL TO USE PyHum:
1) Pyproj: http://code.google.com/p/pyproj/
2) SciPy: http://www.scipy.org/scipylib/download.html
3) Numpy: http://www.scipy.org/scipylib/download.html
4) Matplotlib: http://matplotlib.org/downloads.html
5) Scikit-learn: http://scikit-learn.org/stable/
6) Python Image LIbrary (PIL) http://www.pythonware.com/products/pil/
7) simplekml: http://simplekml.readthedocs.org/en/latest/index.html
8) pyproj: https://pypi.python.org/pypi/pyproj
9) basemap: http://matplotlib.org/basemap/

All of the above are available through pip (https://pypi.python.org/pypi/pip) and easy_install (https://pythonhosted.org/setuptools/easy_install.html)

OTHER LIBRARIES (CYTHON) NEED TO BE COMPILED FOR SPEED:
1) pyread.pyx
2) ppdrc.pyx
3) cwt.pyx
4) replace_nans.pyx
5) spec_noise.pyx

On a Linux platform this can be achieved using:

```
echo "Compiling file reading module"
cython pyread.pyx
gcc -c -fPIC -I/usr/include/python2.7/ pyread.c
gcc -shared pyread.o -o pyread.so

echo "Compiling wavelet computations module"
cython cwt.pyx
gcc -c -fPIC -I/usr/include/python2.7/ cwt.c
gcc -shared cwt.o -o cwt.so

echo "Compiling nan infilling module"
cython replace_nans.pyx
gcc -c -fPIC -I/usr/include/python2.7/ replace_nans.c
gcc -shared replace_nans.o -o replace_nans.so

echo "Compiling spectral noise module"
cython spec_noise.pyx
gcc -c -fPIC -I/usr/include/python2.7/ spec_noise.c
gcc -shared spec_noise.o -o spec_noise.so

echo "Compiling the phase preserving dynamic range compression module"
cython ppdrc.pyx
gcc -c -fPIC -I/usr/include/python2.7/ ppdrc.c
gcc -shared ppdrc.o -o ppdrc.so
```

### Test

A test can be carried out by running the supplied script:

```
python -c "import PyHum; PyHum.test.dotest()"
```

which carries out the following operations:

```
   humfile = PyHum.__path__[0]+os.sep+'test.DAT'
   sonpath = PyHum.__path__[0]

   # reading specific settings
   cs2cs_args = "epsg:26949"
   draft = 0
   bedpick = 1
   c = 1450
   t = 0.108
   f = 455
   draft = 0.3
   flip_lr = 1

   # correction specific settings
   maxW = 1000

   # for texture calcs
   win = 100
   shift = 10
   density = win/2
   numclasses = 4
   maxscale = 20
   notes = 4
   shorepick = 0
   do_two = 0

   # for mapping
   imagery = 1 # server='http://server.arcgisonline.com/ArcGIS', service='World_Imagery'

   PyHum.humread(humfile, sonpath, cs2cs_args, c, draft, doplot, t, f, bedpick, flip_lr)

   PyHum.humcorrect(humfile, sonpath, maxW, doplot)

   PyHum.humtexture(humfile, sonpath, win, shift, doplot, density, numclasses, maxscale, notes, shorepick, do_two)

   PyHum.domap(humfile, sonpath, cs2cs_args, imagery)
```

on the following files:
test.DAT
B003.SON
B002.SON
B001.SON
B000.SON

and results in a set of outputs such as csv, mat and kml files, and including some rudimentary figures such as:

![alt tag](http://dbuscombe-usgs.github.io/figs/bed_pick.png)
port and starboard scans showing automated bed picks

![alt tag](http://dbuscombe-usgs.github.io/figs/merge_corrected_scan_ppdrc.png)
a merged port/starboard scan

![alt tag](http://dbuscombe-usgs.github.io/figs/raw_dwnhi.png)
a raw 200 kHz downward sonar scan

![alt tag](http://dbuscombe-usgs.github.io/figs/raw_dwnlow.png)
a raw 83 kHz downward sonar scan

![alt tag](http://dbuscombe-usgs.github.io/figs/class.png)
radiometrically corrected scan (top) and wavelet lengthscale classification (bottom)

![alt tag](http://dbuscombe-usgs.github.io/figs/class_kmeans.png)
k=4 means lengthscale classification

### Support

This is a new project written and maintained by Daniel Buscombe. Thus far extensive testing has not been possible so bugs are expected. 

Please download, try, report bugs, fork, modify, evaluate, discuss, collaborate. Please address all suggestions, comments and queries to: dbuscombe@usgs.gov. Thanks for stopping by! 




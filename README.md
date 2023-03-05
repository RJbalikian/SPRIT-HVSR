# SPRĪT 
SpRĪT (HV): Spectral Ratio Investigation Toolset (Horizontal Vertical Ratio)

# Introduction

The Horizontal to Vertical Spectral Ratio (HVSR) technique is a method used to analyze ambient seismic noise to calculate the dominant frequency at a site.

This package will allow ambient seismic data to be read in the most common seismic data formats, and will perform Horizontal Vertical Spectral Ratio (HVSR) analysis on the data. H/V analysis was standardized and popularized by the Site EffectS assessment using AMbient Excitations (SESAME) project, with a comprehensive final report issued in 2003. [1] This SESAME project and its J-SESAME pacakge were crucial in the developing of the HVSR technique, and the outputs aided in the development of this software package.

This python package is built in large part off the Incorporated Research Institutions in Seismology (IRIS) Horizontal to Vertical Spectral Ratio (HVSR) processing package.[2] Specifically, the computeHVSR.py tools that enable the ability to rank HVSR peaks, calculate data quality and peak quality, and the combining of the horizontal components was adapted directly from that package. Because the SpRĪT package is intended to be used to analyze data from rapid field data acquisitions (less than an hour per site), much of the IRIS package was adapted from daily to HV curve calculations to sub-hourly and even sub-minute HV calculations. Because there is limited data, there is no baseline to compare to, so that element is excluded from this package.

That version is intended to read data from the IRIS Data Management Center (DMC) MUSTANG online service[3], which is a toolbox that provides processes for enabling data quality analysis services to data archived in the DMC. For example, a simple service query can extract power spectral density estimates, noise spectrograms, H/V plots, etc.

# Documentation
- API Documentation here: https://sprite-hvsr.readthedocs.io/en/latest/modules.html

# Dependencies 
Aside from the modules in the python standard library, the following package dependencies must be installed in your environment for this package to work
- [matplotlib](https://matplotlib.org/): copmrehensive library for creating static, animated, andinteractive visualizationsin python
- numpy
- obspy
- scipy

# References
- [1] http://sesame.geopsy.org/Delivrables/SESAME-Finalreport_april05.pdf
- [2] https://github.com/iris-edu/HVSR
- [3] http://service.iris.edu/mustang/

Documentation: https://www.youtube.com/watch?v=b4iFyrLQQh4&ab_channel=avcourt

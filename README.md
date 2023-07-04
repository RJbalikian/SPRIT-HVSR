# SPRĪT 
SpRĪT (HVSR): Spectral Ratio Investigation Toolset for basic Horizontal Vertical Spectral Ratio processing, using any data format readable by the Obspy python package.

# Introduction

The Horizontal to Vertical Spectral Ratio (HVSR) technique is a method used to analyze ambient seismic noise to calculate the dominant frequency at a site.

This package will allow ambient seismic data to be read in the most common seismic data formats, and will perform Horizontal Vertical Spectral Ratio (HVSR) analysis on the data. H/V analysis was standardized and popularized by the Site EffectS assessment using AMbient Excitations (SESAME) project, with a comprehensive final report issued in 2003.<sup>[1](#1)</sup> This SESAME project and its J-SESAME pacakge were crucial in the developing of the HVSR technique, and the outputs aided in the development of this software package.

This python package is built in large part off the Incorporated Research Institutions in Seismology (IRIS) Horizontal to Vertical Spectral Ratio (HVSR) processing package.<sup>[2](#2)</sup> Specifically, the computeHVSR.py tools that enable the ability to rank HVSR peaks, calculate data quality and peak quality, and the combining of the horizontal components was adapted directly from that package. Because the SpRĪT package is intended to be used to analyze data from rapid field data acquisitions (less than an hour per site), much of the IRIS package was adapted from daily to HV curve calculations to sub-hourly and even sub-minute HV calculations. Because there is limited data, there is no baseline to compare to, so that element is excluded from this package.

That version is intended to read data from the IRIS Data Management Center (DMC) MUSTANG online service,<sup>[3](#3)</sup> which is a toolbox that provides processes for enabling data quality analysis services to data archived in the DMC. For example, a simple service query can extract power spectral density estimates, noise spectrograms, H/V plots, etc.

For guidelines on acquisition, processing, and interpration of H/V data, see: <http://sesame.geopsy.org/Papers/HV_User_Guidelines.pdf>. 

# Documentation
- API Documentation [here](https://rjbalikian.github.io/SPRIT-HVSR/main.html)</a>
- See Wiki for more information [here](https://github.com/RJbalikian/SPRIT-HVSR/wiki) (in progress)

# Dependencies 
Aside from the modules in the python standard library, the following package dependencies must be installed in your environment for this package to work

- [Obspy](https://docs.obspy.org/): Python framework for processing seismological data
- [Matplotlib](https://matplotlib.org/): Comprehensive library for creating static, animated, andinteractive visualizationsin python
- [Numpy](https://matplotlib.org/): "The fundamental package for scientific computing with Python"
- [Scipy](https://scipy.org/): "Fundamental algorithms for scientific computing in Python"
- [Pandas](https://pandas.pydata.org): "A fast, powerful, flexible and easy to use open source data analysis and manipulation tool" (Used primarily for exporting and managing results)
- [pyqt5](https://pypi.org/project/PyQt5): Python binding of Qt GUI toolkit (used for window selection in jupyter notebooks)
- [tkcalendar](https://pypi.org/project/tkcalendar/): Module for tkinter calendar widget (used for date selection in the GUI)

# References
- <a id="1">[1]</a> <http://sesame.geopsy.org/Delivrables/SESAME-Finalreport_april05.pdf>
- <a id="2">[2]</a> <https://github.com/iris-edu/HVSR>
- <a id="3">[3]</a> <http://service.iris.edu/mustang/>

# Considerations
Summary from SESAME Project (from <https://www.iitk.ac.in/nicee/wcee/article/13_2207.pdf>):
In very brief, the main learnings may be summarized as follows: 

- In situ soil / sensor coupling should be handled with care. Concrete and asphalt provide good results, whereas measuring on soft / irregular soils such as mud, grass, ploughed soil, ice, gravel, not compacted snow, etc. should be avoided. Artificial soil / sensor coupling should be avoided unless it is absolutely necessary, for example, to compensate a strong inclination of the soil. In such a case, either a pile of sand, or a trihedron should be used This soil/sensor coupling issue proves to be particularly important under windy conditions.
- It is recommended not to measure above underground structures. Nearby surface structures should be considered with care, particularly under windy conditions. 
- Measurements under wind or strong rain should be avoided. Wind has been found to induce very significant low frequency perturbations. 
- The proximity of some specific noise sources should be considered with care (or avoided using an anti-trigger window selection to remove the transients): nearby walking, high speed car or truck traffic, industrial machinery, etc. 
- Results tend to be stable with time (if other parameters, such as weather conditions, etc. are kept constant). 
- No matter how strongly a parameter influences H/V amplitudes, the value of the frequency peak is usually not or slightly affected, with the noticeable exception of the wind in certain conditions.

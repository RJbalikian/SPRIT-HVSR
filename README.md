[![DOI](https://zenodo.org/badge/593014510.svg)](https://zenodo.org/doi/10.5281/zenodo.10899401)

# SPRĪT 
SpRĪT (HVSR): Spectral Ratio Investigation Toolset for basic Horizontal Vertical Spectral Ratio processing, using any data format readable by the Obspy python package.

# Introduction

The Horizontal to Vertical Spectral Ratio (HVSR) technique is a method used to analyze ambient seismic noise to calculate the dominant frequency at a site.

This package will allow ambient seismic data to be read in the most common seismic data formats, and will perform Horizontal Vertical Spectral Ratio (HVSR) analysis on the data. H/V analysis was standardized and popularized by the Site EffectS assessment using AMbient Excitations (SESAME) project, with a comprehensive final report issued in 2003.<sup>[1](#1)</sup> This SESAME project and its J-SESAME pacakge were crucial in the developing of the HVSR technique, and the outputs aided in the development of this software package.

This python package is built in large part off the Incorporated Research Institutions in Seismology (IRIS) Horizontal to Vertical Spectral Ratio (HVSR) processing package.<sup>[2](#2)</sup> Specifically, the computeHVSR.py tools that enable the ability to rank HVSR peaks, calculate data quality and peak quality, and the combining of the horizontal components was adapted directly from that package. Because the SpRĪT package is intended to be used to analyze data from rapid field data acquisitions (less than an hour per site), much of the IRIS package was adapted from daily to HV curve calculations to sub-hourly and even sub-minute HV calculations. Because there is limited data, there is no baseline to compare to, so that element is excluded from this package.

That version is intended to read data from the IRIS Data Management Center (DMC) MUSTANG online service,<sup>[3](#3)</sup> which is a toolbox that provides processes for enabling data quality analysis services to data archived in the DMC. For example, a simple service query can extract power spectral density estimates, noise spectrograms, H/V plots, etc.

For guidelines on acquisition, processing, and interpration of H/V data, see: <http://sesame.geopsy.org/Papers/HV_User_Guidelines.pdf>. 

# Installation
Sprit may be installed from the [pypi repository](https://pypi.org/project/sprit/) using the pip command:

`pip install sprit`

The sprit package is in active development. Add the `--upgrade` argument (`pip install sprit --upgrade`) to ensure you have the latest version. If there are prerelease versions newer than the latest stable version that you would like to try out, use the `--pre` flag, i.e., `pip install sprit --pre`.

This should be done using command line. It is recommended to do this in a virtual environment. For information on creating virtual environments in python, see [this page](https://docs.python.org/3/library/venv.html). For the creation of anaconda environments, see [here](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html). Note that it is not officially recommended to use pip repositories in anaconda environments, but it often works without any issues.

For troubleshooting issues with installation or usage of the sprit package, see the [Troubleshooting](https://github.com/RJbalikian/SPRIT-HVSR/wiki/Troubleshooting) page of the wiki.
# Documentation
- API Documentation [here](https://rjbalikian.github.io/SPRIT-HVSR/main.html)
- See Wiki for more tips, tutorials, usage guidelines, troubleshooting, and other information [here](https://github.com/RJbalikian/SPRIT-HVSR/wiki)
- Pypi repository [here](https://pypi.org/project/sprit/)

# Web App
An experimental, browser based web app is available for use via Streamlit. you can find this at [sprithvsr.streamlit.app](https://sprithvsr.streamlit.app)

# Dependencies 
Aside from the modules in the python standard library, the following package dependencies must be installed in your environment for this package to work

- [Obspy](https://docs.obspy.org/): Python framework for processing seismological data
- [Numpy](https://matplotlib.org/): "The fundamental package for scientific computing with Python"
- [Scipy](https://scipy.org/): "Fundamental algorithms for scientific computing in Python"
- [Pandas](https://pandas.pydata.org): "A fast, powerful, flexible and easy to use open source data analysis and manipulation tool"
- [pyproj](https://pyproj4.github.io/pyproj/stable/): Module for cartographic projections and coordinate transformations, a python interface to [PROJ](https://proj.org/en/9.2/)
- [Matplotlib](https://matplotlib.org/): Comprehensive library for creating static, animated, and interactive visualizations in python
- [plotly](https://plotly.com/python/): Open Source Graphing Library for Python that makes interactive, publication-quality graphs.

## Dependencies specifically for GUIs
### Jupyter Widget GUI
- ipython
- ipywidgets
- nbformat

### Streamlit GUI (browser based)
- streamlit

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

# Citation
If you use the sprit package in your research, please use the following citation:

`Riley Balikian, Hongyu Xaio, Alexandra Sanchez. SPRIT HVSR: An open-source software package for processing, analyzing, and visualizing ambient seismic vibrations. Proceedings of the Geological Society of America, 2023. Pittsburgh, PA.`


"""
This module will be used for calibration of the ambient HVSR data acquired near wells 
to derive a relation between the resonant frequency and the depth to bedrock beneath the subsurface.

"""
import math
import numpy as np
import numpy.linalg as nla
import scipy
import scipy.linalg as sla
import obspy
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import csv
import json
import os
import pathlib
import pkg_resources
#import GeoPandas 

"""
Attempt 1: Regression equations: 

Load the calibration data as a CSV file. Read in the frequency and the depth to bedrock. 
Use array structures to organize data. The depth should be the independent variable so probably 
the predictor and the frequency is the dependent variable so the response variable. 

Two approaches- either use the power law  y=ax^b 
or find the least squares solution using the matrix-vector multiplication. 

Use GeoPandas to eliminate outliers

calibrate - does calibration
view_results - produces Pandas dataframe of results
view_plot - produces calibration curve
"""

resource_dir = pathlib.Path(pkg_resources.resource_filename(__name__, 'resources/'))
sample_data_dir = resource_dir.joinpath("sample_data")
sampleFileName = {'sample_1': sample_data_dir.joinpath("SampleHVSRSite1_2024-06-13_1633-1705.csv")}
class HVSR_calibrate:


    def calibrate(HVSRData,datapath, type = "power", model = "ISGS", outlier_radius = None, tags = None):    #May need **kwargs later


        type_list = ["power", "Vs", "matrix"]
        
        power_list = ["Power", "power", "pw", "POWER"]

        Vs_list = ["vs", "VS", "v_s", "V_s", "V_S"]

        matrix_list = ["matrix", "Matrix", "MATRIX"]

        model_list = ["ISGS", "Ibs-von-A", "Ibs-von-B" "Delgado-A", "Delgado-B", 
                      "Parolai", "Hinzen", "Birgoren", "Ozalaybey", "Harutoonian",
                      "Fairchild", "Del Monaco", "Tun", "Thabet-A", "Thabet-B",
                      "Thabet-C", "Thabet-D"]
        basepath = "/path/to"
        file_name = "example.csv"

        datapath = os.path.join(basepath, file_name)

        # if type in type_list and model in model_list and datapath in sampleFileName.values():
                
        #         #eliminate outlier points
        #         #pick only relevant points according to tags 
                
        #         data = pd.read_csv(datapath, sep = ",")                            #need to define usecols after making the spreadsheet
                

                
        #         if type.lower() in power_list():
                     
        #              if model.lower() == "isgs":
                          
        #                   #do something

                     





        







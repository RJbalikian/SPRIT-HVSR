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
import scipy.optimize as sco
#from pyproj import GeoPandas    #need conda environment

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


@staticmethod
def cal_bedrockdepth(a, b, x):
        
        assert a > 0 and b > 0
    
        return a*(x**b)


def calibrate(HVSRData,datapath, type = "power", model = "ISGS", outlier_radius = None, bedrock_type = None):    
    #May need **kwargs later
    
    #need try-catch blocks while reading in files and checking membership
    bedrock_depths = []

    type_list = ["power", "Vs", "matrix"]
    
    power_list = ["Power", "power", "pw", "POWER"]

    Vs_list = ["vs", "VS", "v_s", "V_s", "V_S"]

    matrix_list = ["matrix", "Matrix", "MATRIX"]

    model_list = ["ISGS", "Ibs-von-A", "Ibs-von-B" "Delgado-A", "Delgado-B", 
                    "Parolai", "Hinzen", "Birgoren", "Ozalaybey", "Harutoonian",
                    "Fairchild", "Del Monaco", "Tun", "Thabet-A", "Thabet-B",
                    "Thabet-C", "Thabet-D"]
    
    bedrock_types = ["shale", "sand", "gravel", "limetone", "dolomite", "till", 
                     "sedimentary", "igneous", "metamorphic"]
    

    basepath = "/path/to"
    file_name = "example.csv"

    datapath = os.path.join(basepath, file_name)

    if type in type_list and model in model_list and datapath in sampleFileName.values():
            
            #eliminate outlier points
            #pick only relevant points according to bedrock_type
            
            data = pd.read_csv(datapath, sep = ",")                            #need to define usecols after making the spreadsheet
            #convert columns to arrays

            #user could also say model = all, in that case compare all
            
            if type.lower() in power_list():
                    
                    if model.lower() == "isgs":    
                        
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(1, 1, each)  #change depending on import of data

                    elif model.lower() == "ibs-von-a":
                        
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(96, 1.388, each) 

                    elif model.lower() == "ibs-von-b":
                        
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(146, 1.375, each) 

                    elif model.lower() == "delgado-a":
                        
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(55.11, 1.256, each) 

                    elif model.lower() == "delgado-b":
                        
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(55.64, 1.268, each) 

                    elif model.lower() == "parolai":
                        
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(108, 1.551, each) 

                    elif model.lower() == "hinzen":
                        
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(137, 1.19, each) 

                    elif model.lower() == "birgoren":
                        
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(150.99, 1.153, each) 
                    
                    elif model.lower() == "ozalaybey":
                        
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(141, 1.270, each) 

                    elif model.lower() == "harutoonian":
                        
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(73, 1.170, each) 

                    elif model.lower() == "fairchild":
                        
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(90.53, 1, each)

                    elif model.lower() == "del monaco":
                        
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(53.461, 1.01, each)  

                    elif model.lower() == "tun":
                        
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(136, 1.357, each) 
                    
                    elif model.lower() == "thabet-a":
                        
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(117.13, 1.197, each) 

                    elif model.lower() == "thabet-b":
                    
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(105.14, 0.899, each)

                    elif model.lower() == "thabet-c":
                
                        for each in data:                             #change
                            bedrock_depths[each] = cal_bedrockdepth(132.67, 1.084, each)

                    elif model.lower() == "thabet-d":
                    
                        for each in data:                              #change
                            bedrock_depths[each] = cal_bedrockdepth(116.62, 1.169, each)

                    # else:

                    #     sco.least_squares() 
















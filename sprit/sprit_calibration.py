"""
This module will be used for calibration of the ambient HVSR data acquired near wells 
to derive a relation between the resonant frequency and the depth to bedrock beneath the subsurface.

"""
import math
import sprit_hvsr
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
import warnings
from warnings import warn
from scipy.optimize import curve_fit
from scipy.optimize import least_squares
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


Things to add:
- #checkinstance - HVSRData/HVSR Batch
- #need try-catch blocks while reading in files and checking membership
- 
"""

resource_dir = pathlib.Path(pkg_resources.resource_filename(__name__, 'resources/'))
sample_data_dir = resource_dir.joinpath("sample_data")
sampleFileName = {'sample_1': sample_data_dir.joinpath("SampleHVSRSite1_2024-06-13_1633-1705.csv")}


def cal_bedrockdepth(a, b, x, updatevalues = False, disable_warnings = False):

    while not updatevalues:
    
        if a > 0 and b > 0 and x > 0:
             
             return a*(x**b)
        
        else:

            if not disable_warnings:

                warn("Read negative frequency value", category = FutureWarning)
            
            return a*(x**b)    
                
             
    else:

        if not disable_warnings:

            warn("Read negative frequency value, changed to positive")

        
        x = -x
        return a*(x**b)
             

        #Disable warnings if repeatedly using the same model
        #Use f-strings to show the function if this function is called on its own
    
        


def calibrate(hvsr_results,calib_filepath, type = "power", model = "ISGS", outlier_radius = None, bedrock_type = None, **kwargs):    

    #@checkinstance
    if not isinstance(hvsr_results, sprit_hvsr.HVSRData): 

        raise TypeError("Object passed not an HVSR data object -- see sprit documentation for details")



    a = 0
    b = 0
    
    rows_no = kwargs["nrows"]

    bedrock_depths = None

    data = None

    calib_data = None

    types = ["Power", "Vs", "Matrix"]

    type_list = list(map(lambda x : x.casefold(), types))
    
    power_list = ["Power", "power", "pw", "POWER"]

    Vs_list = ["vs", "VS", "v_s", "V_s", "V_S"]

    matrix_list = ["matrix", "Matrix", "MATRIX"]

    models = ["ISGS", "IbsvonA", "IbsvonB" "DelgadoA", "DelgadoB", 
                    "Parolai", "Hinzen", "Birgoren", "Ozalaybey", "Harutoonian",
                    "Fairchild", "DelMonaco", "Tun", "ThabetA", "ThabetB",
                    "ThabetC", "ThabetD"]
    
    model_list = list(map(lambda x : x.casefold(), models))
    
    bedrock_types = ["shale", "limetone", "dolomite", 
                     "sedimentary", "igneous", "metamorphic"]
    
    model_parameters = {"ISGS" : (1,1), "IbsvonA" : (96, 1.388), "IbsvonB" : (146, 1.375), "DelgadoA" : (55.11, 1.256), 
                        "DelgadoB" : (55.64, 1.268), "Parolai" : (108, 1.551), "Hinzen" : (137, 1.19), "Birgoren" : (150.99, 1.153), 
                        "Ozalaybey" : (141, 1.270), "Harutoonian" : (73, 1.170), "Fairchild" : (90.53, 1), "DelMonaco" : (53.461, 1.01), 
                        "Tun" : (136, 1.357), "ThabetA": (117.13, 1.197), "ThabetB":(105.14, 0.899), "ThabetC":(132.67, 1.084), "ThabetD":(116.62, 1.169)}
    

    freq_columns_names = ["PeakFrequency", "ResonanceFrequency", "peak_freq", "res_freq", "Peakfrequency", "Resonancefrequency", "PF", "RF", "pf", "rf"]

    bedrock_depth_names = ["BedrockDepth", "DepthToBedrock", "bedrock_depth", "depth_bedrock", "depthtobedrock", "bedrockdepth"]
    basepath = "/path/to"
    file_name = "example.csv"

    calib_filepath = os.path.join(basepath, file_name)

    if type.casefold() in type_list and calib_filepath in sampleFileName.values():
            
            #eliminate outlier points - will have to read in latitude and longitude from spreadsheet and then compare against that of well to find distance in meters 
            #pick only relevant points according to bedrock_type

            
            if type.casefold() in power_list:

                data = pd.read_csv(calib_filepath, sep = ",", usecols = [lambda x: x in freq_columns_names, lambda y: y in bedrock_depth_names], 
                               names = ["Resonance Frequency", "Depth to Bedrock"], dtype = float,
                               skipinitialspace= True,index_col=False, nrows = rows_no, skip_blank_lines= True, on_bad_lines= "error")                            
            

                calib_data = np.array((data["Resonance Frequency"].values, data["Depth to Bedrock"].values))

                calib_data = calib_data.T

                bedrock_depths = np.zeros(calib_data.shape[0])
                
                while model.casefold() in model_list: 

                    for k, v in model_parameters.items():
                                
                        if model.casefold() == k.casefold():
                                    
                            (a, b) = model_parameters[k]

                        else:
                            break
                
                for each in bedrock_depths:

                    bedrock_depths[each] = cal_bedrockdepth(a, b, calib_data[each, 0])

                calib_data[:, 1] = bedrock_depths

                return calib_data
                    

                    #Now plot using curve_fit




                if model.casefold() == "all":
                    dummy = 3
                
                     
                    #do something








                else: 
                    #model = None: derive model using least_squares
                    dummy = 3
                    #do something
        





#Add calibration equation to get_report csv
#Add parameter to sprit.run


                         

                           
                           
                        
                  




































# def show_data():
#      #To display the data considered for calibration to the user










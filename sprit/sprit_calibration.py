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
import re
import pathlib
import pkg_resources
import warnings
from warnings import warn
from scipy.optimize import curve_fit
from scipy.optimize import least_squares
#from pyproj import GeoPandas    #need conda environment

try:  # For distribution
    from sprit import sprit_hvsr
except Exception:  # For testing
    import sprit_hvsr


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
- # eliminate outlier points - will have to read in latitude and longitude from spreadsheet and then compare against that of well to find distance in meters 
- #pick only relevant points according to bedrock_type (lithology)
- #Add calibration equation to get_report csv
- #Add parameter to sprit.run
"""

resource_dir = pathlib.Path(pkg_resources.resource_filename(__name__, 'resources/'))
sample_data_dir = resource_dir.joinpath("sample_data")
sampleFileName = {'sample_1': sample_data_dir.joinpath("SampleHVSRSite1_2024-06-13_1633-1705.csv")}

models = ["ISGS", "IbsvonA", "IbsvonB" "DelgadoA", "DelgadoB", 
                    "Parolai", "Hinzen", "Birgoren", "Ozalaybey", "Harutoonian",
                    "Fairchild", "DelMonaco", "Tun", "ThabetA", "ThabetB",
                    "ThabetC", "ThabetD"]
    
model_list = list(map(lambda x : x.casefold(), models))

model_parameters = {"ISGS" : (2,1), "IbsvonA" : (96, 1.388), "IbsvonB" : (146, 1.375), "DelgadoA" : (55.11, 1.256), 
                    "DelgadoB" : (55.64, 1.268), "Parolai" : (108, 1.551), "Hinzen" : (137, 1.19), "Birgoren" : (150.99, 1.153), 
                    "Ozalaybey" : (141, 1.270), "Harutoonian" : (73, 1.170), "Fairchild" : (90.53, 1), "DelMonaco" : (53.461, 1.01), 
                    "Tun" : (136, 1.357), "ThabetA": (117.13, 1.197), "ThabetB":(105.14, 0.899), "ThabetC":(132.67, 1.084), "ThabetD":(116.62, 1.169)}

def calculate_depth(freq_input = {sprit_hvsr.HVSRData, sprit_hvsr.HVSRBatch, float, os.PathLike},  
                    model = "ISGS",
                    site = "HVSRSite", 
                    unit = "m",
                    freq_col = "PeakFrequency", 
                    calculate_elevation = False, 
                    elevation_col = "Elevation", 
                    depth_col = "BedrockDepth", 
                    verbose = False,    #if verbose is True, display warnings otherwise not
                    update_negative_values = False,
                    export_path = None,
                    **kwargs):
    
    a = 0
    b = 0
    params = None

    #Checking how model is inputted
    if isinstance(model,(tuple, list, dict)):  
        (a,b) = model  
        if b >= a:                     #b should always be less than a
            if verbose:
                warn("Second parameter greater than the first, inverting values")
            (b,a) = model
        elif a == 0 or b == 0:         
            raise ValueError("Parameters cannot be zero, check model inputs")

    elif model.casefold() in model_list:
        
        for k,v in model_parameters.items():

            if model.casefold() == k.casefold():   
                (a, b) = model_parameters[k]
                break

    
    elif isinstance(model, str):   #parameters a and b could be passed in as a parsable string
        params = [int(s) for s in re.findall(r"[-+]?(?:\d*\.*\d+)", model)]  #figure this out later for floating points; works for integers
        (a,b) = params
        if a == 0 or b == 0:         
            raise ValueError("Parameters cannot be zero, check model inputs")
        elif b >= a:                     #b should always be less than a
            if verbose:
                warn("Second parameter greater than the first, inverting values")
            (b,a) = params
        
    
    else:
        if (a,b) == (0, 0):

            raise ValueError( "Model not found: check inputs")

    #Checking freq_input is a filepath

    try:
        if os.path.exists(freq_input):
            data = pd.read_csv(freq_input,
                                skipinitialspace= True,
                                index_col=False,
                                on_bad_lines= "error")

            pf_values= data["PeakFrequency"].values

            calib_data = np.array((pf_values, np.ones(len(pf_values))))

            calib_data = calib_data.T

                
            for each in range(calib_data.shape[0]):

                calib_data[each, 1] = a*(calib_data[each, 0]**b)
                
            if unit.casefold() in {"ft", "feet"}:
                data["Depth to Bedrock (ft)"] = calib_data[:, 1]*3.281
            else:    
                data["Depth to Bedrock (m)"] = calib_data[:, 1]
            
            

            if export_path is not None and os.path.exists(export_path):
                if export_path == freq_input:
                    data.to_csv(freq_input)
                    if verbose:
                        print("Saving data in the original file")

                else:
                    if "/" in export_path:
                        temp = os.path.join(export_path+ "/"+ site + ".csv")
                        data.to_csv(temp)
                    
                    else:
                        temp = os.path.join(export_path+"\\"+ site + ".csv")
                        data.to_csv(temp)

                    if verbose:
                        print("Saving data to the path specified")
                

            return data
    except Exception:
        if verbose:
            print("freq_input not a filepath, checking other types")
        
    
    #Reading in HVSRData object
    if isinstance(freq_input, sprit_hvsr.HVSRData):
        try:
            data = freq_input.CSV_Report
        except Exception:
            data = sprit_hvsr.get_report(freq_input,report_format = 'csv')
        
        pf_values= data["PeakFrequency"].values

        calib_data = np.array((pf_values, np.ones(len(pf_values))))

        calib_data = calib_data.T

            
        for each in range(calib_data.shape[0]):

            calib_data[each, 1] = a*(calib_data[each, 0]**b)
        
        if unit.casefold() in {"ft", "feet"}:
            data["Depth to Bedrock (ft)"] = calib_data[:, 1]*3.281

        else:
            data["Depth to Bedrock (m)"] = calib_data[:, 1]
        

        if export_path is not None and os.path.exists(export_path):
            if export_path == freq_input:
                data.to_csv(freq_input)
                if verbose:
                    print("Saving data in the original file")

            else:
                if "/" in export_path:
                    temp = os.path.join(export_path+ "/"+ site + ".csv")
                    data.to_csv(temp)
                
                else:
                    temp = os.path.join(export_path+"\\"+ site + ".csv")
                    data.to_csv(temp)

                if verbose:
                    print("Saving data to the path specified")
            

        return data



    if model.casefold() == "all":
        #Statistical analysis
        sorry = True


    print("I'm here because nothing worked")




        
        


















    

    #@checkinstance
    # if not isinstance(hvsr_results, sprit_hvsr.HVSRData): 

    #     raise TypeError("Object passed not an HVSR data object -- see sprit documentation for details")
    #hvsrData.CSV_Report










    
    # if not update_values:
    
    #     if a > 0 and b > 0 and x > 0:
             
    #          return a*(x**b)
        
    #     else:

    #         if not disable_warnings:

    #             warn("Read negative frequency value", category = FutureWarning)
            
    #         return a*(x**b)    
                
             
    # else:

    #     if not disable_warnings:

    #         warn("Read negative frequency value, changed to positive")

        
    #     x = -x
    #     return a*(x**b)
    
    # return a*(x**b)
















def calibrate(calib_filepath, calib_type = "power",outlier_radius = None, bedrock_type = None,peak_freq_col = "PeakFrequency",
              bed_depth_col = "Bedrock_Depth", **kwargs):    

    calib_data = None

    calib_types = ["Power", "Vs", "Matrix"]

    calib_type_list = list(map(lambda x : x.casefold(), calib_types))
    
    power_list = ["Power", "power", "pw", "POWER"]

    Vs_list = ["vs", "VS", "v_s", "V_s", "V_S"]

    matrix_list = ["matrix", "Matrix", "MATRIX"]

    
    bedrock_types = ["shale", "limetone", "dolomite", 
                     "sedimentary", "igneous", "metamorphic"]
    
   
    

    freq_columns_names = ["PeakFrequency", "ResonanceFrequency", "peak_freq", "res_freq", "Peakfrequency", "Resonancefrequency", "PF", "RF", "pf", "rf"]

    bedrock_depth_names = ["BedrockDepth", "DepthToBedrock", "bedrock_depth", "depth_bedrock", "depthtobedrock", "bedrockdepth"]

    # if calib_type.casefold() in calib_type_list: 
        
       
    #     if calib_type.casefold() in power_list:









    








                         

                           
                           
                        
                  














































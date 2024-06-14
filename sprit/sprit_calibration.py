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





"""
Attempt 1: Regression equations: 

Load the calibration data as a CSV file. Read in the frequency and the depth to bedrock. 
Use array structures to organize data. The depth should be the independent variable so probably 
the predictor and the frequency is the dependent variable so the response variable. 

Two approaches- either use the power law  y=ax^b 
or find the least squares solution using the matrix-vector multiplication. 

"""



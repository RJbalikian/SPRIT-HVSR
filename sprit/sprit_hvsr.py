"""
This module is the main SpRIT module that contains all the functions needed to run HVSR analysis.

The functions defined here are read both by the SpRIT graphical user interface and by the command-line interface to run HVSR analysis on input data.

See documentation for individual functions for more information.
"""
import base64
import copy
import datetime
import gzip
import inspect
import io
import json
import math
import operator
import os
import pathlib
import pickle
import importlib
import re
import struct
import sys
import tempfile
import traceback
import warnings
import xml.etree.ElementTree as ET
import zoneinfo

import kaleido
import matplotlib
from matplotlib.backend_bases import MouseButton
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import obspy
from obspy.signal import PPSD
import pandas as pd
import plotly
from pyproj import CRS, Transformer
import scipy
from scipy.spatial.distance import squareform, pdist

try:  # For distribution
    from sprit import sprit_utils
    from sprit import sprit_tkinter_ui
    from sprit import sprit_jupyter_UI
    from sprit import sprit_plot
except Exception:  # For testing
    import sprit_utils
    import sprit_tkinter_ui
    import sprit_jupyter_UI
    import sprit_plot

# Constants, etc
NOWTIME = datetime.datetime.now()
DEFAULT_PLOT_STR = "HVSR p ann COMP+ p ann SPEC p ann"
OBSPY_FORMATS = ['AH', 'ALSEP_PSE', 'ALSEP_WTH', 'ALSEP_WTN', 'CSS', 'DMX', 
                 'GCF', 'GSE1', 'GSE2', 'KINEMETRICS_EVT', 'KNET', 'MSEED', 
                 'NNSA_KB_CORE', 'PDAS', 'PICKLE', 'Q', 'REFTEK130', 'RG16', 
                 'SAC', 'SACXY', 'SEG2', 'SEGY', 'SEISAN', 'SH_ASC', 'SLIST', 'TRC',
                 'SU', 'TSPAIR', 'WAV', 'WIN', 'Y']
DEFAULT_BAND = [0.5, 40]
PLOT_KEYS = ["Input_Plot", "Outlier_Plot", "Plot_Report", "Depth_Plot", "Plot_Report"]

# Resources directory path, and the other paths as well
RESOURCE_DIR = pathlib.Path(str(importlib.resources.files('sprit'))).joinpath('resources')
SAMPLE_DATA_DIR = RESOURCE_DIR.joinpath('sample_data')
SETTINGS_DIR = RESOURCE_DIR.joinpath('settings')

global spritApp

# Predefined variables
max_rank = 0
global do_run 
do_run = False

sampleListNos = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
SAMPLE_LIST = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'batch', 'sample', 'sample_batch']
for s in sampleListNos:
    SAMPLE_LIST.append(f'sample{s}')
    SAMPLE_LIST.append(f'sample_{s}')

sampleFileKeyMap = {'1':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite1_AM.RAC84.00.2023.046_2023-02-15_1704-1734.MSEED'),
                    '2':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite2_AM.RAC84.00.2023-02-15_2132-2200.MSEED'),
                    '3':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite3_AM.RAC84.00.2023.199_2023-07-18_1432-1455.MSEED'),
                    '4':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite4_AM.RAC84.00.2023.199_2023-07-18_1609-1629.MSEED'),
                    '5':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite5_AM.RAC84.00.2023.199_2023-07-18_2039-2100.MSEED'),
                    '6':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite6_AM.RAC84.00.2023.192_2023-07-11_1510-1528.MSEED'),
                    '7':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite7_BNE_4_AM.RAC84.00.2023.191_2023-07-10_2237-2259.MSEED'),
                    '8':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite8_BNE_6_AM.RAC84.00.2023.191_2023-07-10_1806-1825.MSEED'),
                    '9':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite9_BNE-2_AM.RAC84.00.2023.192_2023-07-11_0000-0011.MSEED'),
                    '10':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite10_BNE_4_AM.RAC84.00.2023.191_2023-07-10_2237-2259.MSEED'),
                    
                    'sample1':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite1_AM.RAC84.00.2023.046_2023-02-15_1704-1734.MSEED'),
                    'sample2':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite2_AM.RAC84.00.2023-02-15_2132-2200.MSEED'),
                    'sample3':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite3_AM.RAC84.00.2023.199_2023-07-18_1432-1455.MSEED'),
                    'sample4':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite4_AM.RAC84.00.2023.199_2023-07-18_1609-1629.MSEED'),
                    'sample5':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite5_AM.RAC84.00.2023.199_2023-07-18_2039-2100.MSEED'),
                    'sample6':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite6_AM.RAC84.00.2023.192_2023-07-11_1510-1528.MSEED'),
                    'sample7':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite7_BNE_4_AM.RAC84.00.2023.191_2023-07-10_2237-2259.MSEED'),
                    'sample8':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite8_BNE_6_AM.RAC84.00.2023.191_2023-07-10_1806-1825.MSEED'),
                    'sample9':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite9_BNE-2_AM.RAC84.00.2023.192_2023-07-11_0000-0011.MSEED'),
                    'sample10':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite10_BNE_4_AM.RAC84.00.2023.191_2023-07-10_2237-2259.MSEED'),

                    'sample_1':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite1_AM.RAC84.00.2023.046_2023-02-15_1704-1734.MSEED'),
                    'sample_2':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite2_AM.RAC84.00.2023-02-15_2132-2200.MSEED'),
                    'sample_3':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite3_AM.RAC84.00.2023.199_2023-07-18_1432-1455.MSEED'),
                    'sample_4':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite4_AM.RAC84.00.2023.199_2023-07-18_1609-1629.MSEED'),
                    'sample_5':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite5_AM.RAC84.00.2023.199_2023-07-18_2039-2100.MSEED'),
                    'sample_6':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite6_AM.RAC84.00.2023.192_2023-07-11_1510-1528.MSEED'),
                    'sample_7':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite7_BNE_4_AM.RAC84.00.2023.191_2023-07-10_2237-2259.MSEED'),
                    'sample_8':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite8_BNE_6_AM.RAC84.00.2023.191_2023-07-10_1806-1825.MSEED'),
                    'sample_9':SAMPLE_DATA_DIR.joinpath('SampleHVSRSite9_BNE-2_AM.RAC84.00.2023.192_2023-07-11_0000-0011.MSEED'),
                    'sample_10': SAMPLE_DATA_DIR.joinpath('SampleHVSRSite10_BNE_4_AM.RAC84.00.2023.191_2023-07-10_2237-2259.MSEED'),
                    
                    'batch': SAMPLE_DATA_DIR.joinpath('Batch_SampleData.csv'),
                    'sample_batch': SAMPLE_DATA_DIR.joinpath('Batch_SampleData.csv')}


# CLASSES
# Check if the data is already the right class
# Define a decorator that wraps the __init__ method
def check_instance(init):
    def wrapper(self, *args, **kwargs):
        # Check if the first argument is an instance of self.__class__
        if args and isinstance(args[0], self.__class__):
            # Copy its attributes to self
            self.__dict__.update(args[0].__dict__)
        else:
            # Call the original __init__ method
            init(self, *args, **kwargs)
    return wrapper


# Class for batch data
class HVSRBatch:
    """HVSRBatch is the data container used for batch processing. 
    It contains several HVSRData objects (one for each site). 
    These can be accessed using their site name, 
    either square brackets (HVSRBatchVariable["SiteName"]) or the dot (HVSRBatchVariable.SiteName) accessor.
    
    The dot accessor may not work if there is a space in the site name.
    
    All of the  functions in the sprit package are designed to perform the bulk of their operations iteratively
    on the individual HVSRData objects contained in the HVSRBatch object, and do little with the HVSRBatch object itself, 
    besides using it determine which sites are contained within it.
    
    """
    @check_instance
    def __init__(self, batch_input, batch_ext=None, batch_use=None, df_as_read=None):
        """HVSR Batch initializer

        Parameters
        ----------
        batch_input : dict, list, tuple, HVSRData, or filepath(s)
            If:

            * dict, dictionary containing Key value pairs with {sitename: HVSRData object}.
            * list or tuple, assumed to be dicts, HVSRData objects, or filepaths to processed .hvsr files or seismic data to be processed.
            * HVSRData object, will transform into HVSRBatch object with single HVSRData object. The add() or append() methods, or using square brackes can be used to add additional sites.
            * filepaths, if:
                * If directory, will use `batch_ext` as the input to a `glob()` function to get all files in that directory and add them to batch. Defaults to '.hvsr' files if `batch_ext` not specified.
                * Filepath, will make a HVSRBatch object importing that single file, or if readable by pandas.read_csv() will use in conjunction with `batch_use` (see below)
        batch_ext : str or None
            Filepath extension to use in `glob()` function for filetypes to import, if batch_input is a filepath.
        batch_use : {dict, list, tuple, None}
            Intended to be used as dict with keys "site", "filepath", and "batch". 
            In this case, should be {'site':"name_of_df_col_with_sitenames", 'filepath':"name_of_df_col_with_filepaths_to_data", 'batch':values_to_include}.
            values_to_include can be a value (or list of values) in a column called "batch" to specify that that row should be included in the HVSRBatch object or
            a dictionary where they keys are column names and the values are the values to look for in each column name for inclusion in HVSRBatch object.
            If not specified, defaults to None and uses all rows in dataframe.

        df_as_read : {None, pd.DataFrame}
            Used in various sprit functions to allow original DataFrame used to create HVSRBatch object to be carried through.        
        """

        # Just return it as-is if it's already Batch object
        if isinstance(batch_input, HVSRBatch):
            return batch_input
        
        self._batch_input = batch_input
        self.batch_input = self._batch_input
        
        self._batch_dict = self.batch_dict = {}

        self._input_df = df_as_read
        self.input_df = self._input_df
        
        self.batch = True
        
        if isinstance(batch_input, (list, tuple,)):
            # This is for a list/tuple with the following structure:
            # batch_input = [HVSRData, HVSRData, HVSRData]
            # or batch_input = ['/file/path1.hvsr', '/file/path2.hvsr']
            # Can also be mixed: [HVSRData, '/file/path3/.hvsr']
            siteNo = 0
            zfilldigs = len(str(len(batch_input)))
            
            for hvdata in batch_input:
                if isinstance(hvdata, (dict, HVSRData)):
                    if hasattr(hvdata, 'site'):
                        sitename = hvdata.site
                    elif hasattr(hvdata, 'Table_Report') and 'Site Name' in hvdata.Table_Report.columns:
                        sitename = hvdata.Table_Report['Site Name'][0]
                    else:
                        sitename = f"HVSRSite{str(siteNo).zfill(zfilldigs)}"
                        siteNo += 1
                    self.batch_dict[sitename] = hvdata
                elif pathlib.Path(hvdata).exists():
                    def _get_sitename(proposed_sitename, batch_dict):
                        # Get unique site name based on stem
                        j = 0
                        if proposed_sitename in batch_dict.keys():
                            # 100 is limit
                            for index in range(100):
                                if len(proposed_sitename.split('_')) <= index:
                                    if proposed_sitename.split('_')[-1].isdigit():
                                        j = int(proposed_sitename.split('_')[-1]) + 1
                                        sitenameList = proposed_sitename.split('_')
                                        sitenameList[-1] = str(j)
                                        proposed_sitename = '_'.join(sitenameList)
                                        break
                                    else:
                                        proposed_sitename = proposed_sitename+'_'+str(j)
                                        break
                                    j += 1
                                else:
                                    proposed_sitename = '_'.join(proposed_sitename.split('_')[:index+1])
                        return proposed_sitename

                    if 'hvsr' in pathlib.Path(hvdata).suffix:
                        sitename = pathlib.path(hvdata).stem
                        sitename = _get_sitename(sitename, batch_dict)

                        self.batch_dict[sitename] = hvdata
                    elif pathlib.Path(hvdata).suffix.upper()[1:] in OBSPY_FORMATS:
                        if verbose:
                            print(f"Site specified for inclusion in HVSRBatch has not been processed. Processing. ({hvdata})")
                        sitename = pathlib.Path(hvdata).stem
                        sitename = _get_sitename(sitename, batch_dict)
                        self.batch_dict[sitename] = run(pathlib.Path(hvdata).as_posix())
                    else:
                        print(f"Could not parse Batch input. Excluding from HVSRBatch object: {hvdata}")
        elif isinstance(batch_input, dict):
            # This is for a dictionary with the following structure:
            # batch_input = {"SiteName1":HVSRData, "Sitename2":HVSRData}
            self.batch_dict = batch_input
        elif isinstance(batch_input, HVSRData):
            # If iniitializing HVSRBatch with single HVSRData
            self.batch_dict[batch_input['site']] = batch_input
        elif pathlib.Path(batch_input).exists():
            # This is intended for filepaths
            if pathlib.Path(batch_input).is_dir():
                if batch_ext is not None:
                    batchfileglob = pathlib.Path(batch_input).glob("*."+batch_ext)
                    batchfiledict = {}
                    #if 'hvsr' in batch_ext:
                    for hvfile in batchfileglob:
                        currhvfile = import_data(hvfile)
                        batchfiledict[currhvfile['site']] = currhvfile
                    self.batch_dict = self._batch_dict = batchfiledict
                else:
                    # Assume it is .hvsr file you wish to import
                    batchfileglob = []
                    batchfiledict = {}

                    batchfileglob = pathlib.Path(batch_input).glob("*")
                    for hvfile in batchfileglob:
                        if hvfile.as_posix().lower().endswith('hvsr'):
                            currhvfile = import_data(hvfile.as_posix())
                            batchfiledict[currhvfile['site']] = currhvfile
                    self.batch_dict = self._batch_dict = batchfiledict           
            else:
                if '.hvsr' in pathlib.Path(batch_input).suffix:
                    # In this case, assume this is alreayd a batch file and import/return it
                    return import_data(batch_input)
                else:
                    # For reading in a csv and specifying column map
                    batch_df = pd.read_csv(batch_input)

                    # Convert columns to lowercase
                    batch_df.columns = [c.lower() for c in batch_df.columns]

                    # This is for if dictionary mapping is not specified
                    snList = ['site', 'sitename', 'sites', 'sitenames', 
                                'identifier', 'batch', 'profile', 'crosssection', 'group']
                    pathList = ['hvsr_export_path', 'import_filepath', 'batch_input', 'filepath', 'input_data',
                                'path', 'filepath', 'filename', 'file', 'hvsrdata', 'hvsr', 'data']

                    siteCol = batch_df.columns[0]
                    for sn in snList:
                        if sn in snList:
                            siteCol = sn
                            break

                    pathCol = batch_df.columns[1]
                    for pa in pathList:
                        if pa in pathList:
                            pathCol = pa
                            break

                    def _read_data_into_batch(batch_df_row, site_col, path_col):
                        if '.hvsr' in str(batch_df_row[path_col]):
                            dataObj = import_data(str(batch_df_row[path_col]))
                        elif pathlib.Path(batch_df_row[path_col]).suffix.upper()[1:] in OBSPY_FORMATS:
                            dataObj = run(pathlib.Path(batch_df_row[path_col]).as_posix())
                        else:
                            warnings.Warn(f"Batch input specified as site {batch_df_row[site_col]} cannot be read, skipping: {batch_df_row[path_col]}")
                            dataObj = None
                        
                        return dataObj

                    if isinstance(batch_use, dict):
                        # Dictionary of {'site':"site_col", 'filepath':'path_col', 'batch':values_in_batch_col_to_include}
                        if len(list(batch_use.keys())) != 3:
                            warnMsg = f"batch_use dict should have three keys called 'site', 'filepath', and 'batch' (not {len(list(batch_use.keys()))}: {list(batch_use.keys())}). \n\t'batch' may be changed to name of column you are using to specify inclusion in HVSRBatch object, or input DataFrame should have column called 'batch'"
                            warnings.Warn(warnMsg)

                        # Should be site and filepath, but just in case
                        for k in batch_use.keys():
                            if str(k).lower() in snList:
                                siteCol = batch_use[k]
                                siteKey = k

                            if str(k).lower() in pathList:
                                pathCol = batch_use[k]
                                pathKey = k

                            if str(k).lower() not in snList and str(k).lower() not in pathList:
                                includeMe = batch_use[k]
                                batchKey = k
    
                        # Get subset df with only rows that we want
                        #includeMe = batchCol#batch_use[batchCol]
                        if isinstance(includeMe, (list, tuple)):
                            sites_df = batch_df[batch_df[batchKey].isin(includeMe)]
                        elif isinstance(includeMe, dict):
                            sitesDFList = []
                            for batchCol, includeValue in includeMe.items():
                                sitesDFList.append(batch_df[batch_df[batchCol]==includeValue])
                            sites_df = pd.concat(sitesDFList, ignore_index=True)
                        else:
                            sites_df = batch_df[batch_df[batchKey]==includeMe]

                        # Import, process, or otherwise read data into batch object
                        for i, row in sites_df.iterrows():
                            dataObj = _read_data_into_batch(row, siteCol, pathCol)
                            if dataObj is not None:
                                self.batch_dict[str(row[siteCol])] = dataObj

                    elif isinstance(batch_use, (list, tuple)):
                        # This should be list/tuples of site names
                        sites_df = batch_df[batch_df[siteCol].isin(batch_use)]
                        for i, row in sites_df.iterrows():
                            dataObj = _read_data_into_batch(row, siteCol, pathCol)
                            if dataObj is not None:
                                self.batch_dict[str(row[siteCol])] = dataObj
                    
                    else:
                        # Use all rows (as possible)
                        print(f"**NOTE**: All data specified will be read into batch object, from: {batch_input}")
                        for i, row in batch_df.iterrows():
                            dataObj = _read_data_into_batch(row, siteCol, pathCol)

                            if dataObj is not None:
                                self.batch_dict[str(row[siteCol])] = dataObj
        else:
            raise TypeError(f"The batch_input parameter of the HVSRBatch class must be a dict of parameters, list or tuple of HVSRData obejcts, or an HVSRData object itself. {type(batch_input)}")


        self._batch_dict = self.batch_dict
        for sitename, hvsrdata in self.batch_dict.items():
            setattr(self, sitename, hvsrdata)
            self[sitename]['batch'] = True
        self.sites = list(self.batch_dict.keys())


    # METHODS
    def __to_json(self, filepath):
        """Not yet implemented, but may allow import/export to json files in the future, rather than just .hvsr pickles

        Parameters
        ----------
        filepath : filepath object
            Location to save HVSRBatch object as json
        """
        # open the file with the given filepath
        with open(filepath, 'w') as f:
            # dump the JSON string to the file
            json.dump(self, f, default=lambda o: o.__dict__, sort_keys=True, indent=4)


    def add(self, hvsr_data):
        """Function to add HVSRData objects to existing HVSRBatch objects"""
        if isinstance(hvsr_data, (dict, HVSRData)):
            hvsr_data = [hvsr_data]

        if isinstance(hvsr_data, (list, tuple,)):
            siteNo = 0
            zfilldigs = len(str(len(hvsr_data)))

            for hvdata in hvsr_data:
                sitename = f"HVSRSite{str(siteNo).zfill(zfilldigs)}"

                if hasattr(hvdata, 'site'):
                    sitename = hvdata.site
                elif hasattr(hvdata, 'Table_Report') and 'Site Name' in hvdata.Table_Report.columns:
                    sitename = hvdata.Table_Report['Site Name'][0]
                elif isinstance(hvdata, dict):
                    if 'site' in hvdata.keys():
                        sitename = hvdata['site']

                self[sitename] = hvsr_data
        

    def append(self, hvsr_data):
        """Alias of add()"""
        add(self, hvsr_data)
        

    def export(self, hvsr_export_path=True, ext='hvsr'):
        """Method to export HVSRData objects in HVSRBatch container to indivdual .hvsr pickle files.

        Parameters
        ----------
        hvsr_export_path : filepath, default=True
            Filepath to save file. Can be either directory (which will assign a filename based on the HVSRData attributes). By default True. If True, it will first try to save each file to the same directory as input_data, then if that does not work, to the current working directory, then to the user's home directory, by default True
        ext : str, optional
            The extension to use for the output, by default 'hvsr'. This is still a pickle file that can be read with pickle.load(), but will have .hvsr extension.
        """
        export_hvsr(hvsr_data=self, hvsr_export_path=hvsr_export_path, ext=ext)


    def keys(self):
        """Method to return the "keys" of the HVSRBatch object. For HVSRBatch objects, these are the site names. Functions similar to dict.keys().

        Returns
        -------
        dict_keys
            A dict_keys object listing the site names of each of the HVSRData objects contained in the HVSRBatch object
        """
        return self.batch_dict.keys()


    def items(self):
        """Method to return both the site names and the HVSRData object as a set of dict_items tuples. Functions similar to dict.items().

        Returns
        -------
        _type_
            _description_
        """
        return self.batch_dict.items()


    def copy(self, type='shallow'):
        """Make a copy of the HVSRBatch object. Uses python copy module.
        
        Parameters
        ----------
        type : str {'shallow', 'deep'}
            Based on input, creates either a shallow or deep copy of the HVSRBatch object. Shallow is equivalent of copy.copy(). Input of 'deep' is equivalent of copy.deepcopy() (still experimental). Defaults to shallow.
    
        """
        if type.lower()=='deep':
            return HVSRBatch(copy.deepcopy(self._batch_dict), df_as_read=self._input_df)
        else:
            return HVSRBatch(copy.copy(self._batch_dict), df_as_read=self._input_df)


    #Method wrapper of sprit.plot_hvsr function
    def plot(self, **kwargs):
        """Method to plot data, based on the sprit.plot_hvsr() function. 
        
        All the same kwargs and default values apply as plot_hvsr().
        For return_fig, returns it to the 'Plot_Report' attribute of each HVSRData object

        Returns
        -------
        _type_
            _description_

        See Also
        --------
        plot_hvsr
        """
        for sitename in self:
            if 'return_fig' in kwargs.keys() and kwargs['return_fig']:
                self[sitename]['Plot_Report'] = plot_hvsr(self[sitename], **kwargs)
            else:
                plot_hvsr(self[sitename], **kwargs)

        return self
    
    def get_report(self, **kwargs):
        """Method to get report from processed data, in print, graphical, or tabular format.

        Returns
        -------
        Variable
            May return nothing, pandas.Dataframe, or pyplot Figure, depending on input.

        See Also
        --------
        get_report
        """
        if 'report_formats' in kwargs.keys():
            if 'table' == kwargs['report_formats']:
                for sitename in self:
                    rowList = []
                    rowList.append(get_report(self[sitename], **kwargs))
                return pd.concat(rowList, ignore_index=True)
            elif 'plot' == kwargs['report_formats']:
                plotDict = {}
                for sitename in self:
                    if 'return_fig' in kwargs.keys() and kwargs['return_fig']:
                        plotDict[sitename] = get_report(self[sitename], **kwargs)
                    else:
                        get_report(self[sitename], **kwargs)
                return plotDict
            
        #Only report_formats left is print, doesn't return anything, so doesn't matter if defalut or not
        for sitename in self:
            get_report(self[sitename], **kwargs)
        return

    def report(self, **kwargs):
        """Wrapper of get_report()
        
        See Also
        --------
        get_report
        """
        return self.get_report(**kwargs)

    def export_settings(self, site_name=None, export_settings_path='default', export_settings_type='all', include_location=False, verbose=True):
        """Method to export settings from HVSRData object in HVSRBatch object. 
        
        Simply calls sprit.export_settings() from specified HVSRData object in the HVSRBatch object. 
        See sprit.export_settings() for more details.

        Parameters
        ----------
        site_name : str, default=None
            The name of the site whose settings should be exported. If None, will default to the first site, by default None.
        export_settings_path : str, optional
            Filepath to output file. If left as 'default', will save as the default value in the resources directory. If that is not possible, will save to home directory, by default 'default'
        export_settings_type : str, {'all', 'instrument', 'processing'}, optional
            They type of settings to save, by default 'all'
        include_location : bool, optional
            Whether to include the location information in the instrument settings, if that settings type is selected, by default False
        verbose : bool, optional
            Whether to print output (filepath and settings) to terminal, by default True
        
        
        See Also
        --------
        export_settings
        """
        #If no site name selected, use first site
        if site_name is None:
            site_name = self.sites[0]
            
        export_settings(hvsr_data=self[site_name], 
                        export_settings_path=export_settings_path, export_settings_type=export_settings_type, include_location=include_location, verbose=verbose)

    def __iter__(self):
        return iter(self._batch_dict.keys())

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)
    
# Class for HVSR site data
class HVSRData:
    """HVSRData is the basic data class of the sprit package. 
    It contains all the processed data, input parameters, and reports.
    
    These attributes and objects can be accessed using square brackets or the dot accessor. For example, to access the site name, HVSRData['site'] and HVSRData.site will both return the site name.
    
    Some of the methods that work on the HVSRData object (e.g., .plot() and .get_report()) are essentially wrappers for some of the main sprit package functions (sprit.plot_hvsr() and sprit.get_report(), respectively)
    """
    @check_instance    
    def __init__(self, params):
        self.params = params
        self.batch = False
        #self.tsteps_used = []

        for key, value in params.items():
            setattr(self, key, value)
            if key == 'input_params':
                for k, v in params[key].items():
                    setattr(self, k, v)

        self.processing_status = {'input_params_status': None,
                                  'fetch_data_status': None,
                                  'calculate_azimuths_status': None,
                                  'remove_noise_status': None,
                                  'generate_psds_status': None,
                                  'process_hvsr_status': None,
                                  'remove_outlier_curves_status': None,
                                  'overall_status': False}


    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __str__(self):
        attrsToUse = ['project', 'site', 
            'instrument', 'network', 'station', 'location', 'channels',
            'acq_date', 'starttime', 'endtime',
            'xcoord', 'ycoord', 'input_crs', 'elevation', 'elev_unit',
            ]

        if not all([atu in self.keys() for atu in attrsToUse]):
            return 'String representation cannot be generated. Object not instatianted correctly using sprit.input_params()'

        def __get_ip_default(parameter):
            if parameter in inspect.signature(input_params).parameters:
                return inspect.signature(input_params).parameters[parameter].default
            elif parameter in params:
                return params[parameter]
            else:
                return parameter

        # Get title lines formatted
        if self.project == __get_ip_default('project'):
            projStr = 'No project specified'
        else:
            projStr = self.project

        hvsrIDStr = ''
        if hasattr(self, 'hvsr_id'):
            hvsrIDStr = self.hvsr_id
        elif 'hvsr_id' in params:
            hvsrIDStr = params['hvsr_id']

        titleInfoStr =f"\nSpRIT HVSR DATA INFORMATION\n"
        titleLen = len(titleInfoStr)
        bigLineBreak = "—"*titleLen+ '\n'
        titleInfoStr += bigLineBreak
        titleInfoStr += f"Site Name: {self.site}\nProject: ({projStr})\n"
        titleInfoStr = f"{titleInfoStr}HVSRID (autogenerated): {hvsrIDStr}\n"
        titleInfoStr += bigLineBreak
        
        # Acquisition instrument information
        instInfoStr = "\n\nINSTRUMENT INFO\n"
        instInfoStr += '-'*(len(instInfoStr)-3) + '\n'

        instStr = f"Instrument in use: {self.instrument}"
        if self.instrument == __get_ip_default('instrument'):
            instStr = 'No instrument type specified'

        netStr = self.network
        staStr = self.station
        locStr = self.location
        chaStr = self.channels
        if chaStr == __get_ip_default('channels'):
            chaStr = f'No channels specified (using {chaStr})'

        acqInstStr = instInfoStr
        acqInstStr += f"{instStr}"
        acqInstStr += f"\n\tInstrument ID: {netStr}.{staStr}.{locStr}"
        acqInstStr += f"\n\t\tChannels: {chaStr}"

        # Acquisition site information
        xcoordINStr = self.xcoord_input
        xcoordStr = self.xcoord
        lonStr = self.longitude
        ycoordINstr = self.ycoord_input
        ycoordStr = self.ycoord
        latStr = self.latitude
        inCRSStr = self.input_crs
        outCRSStr = self.output_crs

        inputLocStr = f"{xcoordINStr}, {ycoordINstr} (as input in {inCRSStr})\n"
        
        transLocStr = ''
        if inCRSStr != outCRSStr:
            transLocStr = f"{xcoordStr}, {ycoordstr} (transformed to output_crs: {outCRSStr})\n"

        wgs84Str = f"{lonStr:.5f}°, {latStr:.5f}° | Lon/Lat in WGS84 (EPSG:4326)"

        siteLocInfoStr = "\n\nSITE INFO\n"
        siteLocInfoStr += '-'*(len(siteLocInfoStr)-3) + '\n'
        siteLocInfoStr += inputLocStr + transLocStr + wgs84Str

        # Acquistion time information
        acqTimeStr = "\n\nACQUISITION TIME\n"
        acqTimeStr += '-'*(len(acqTimeStr)-3) + '\n'

        aDateStr = self.acq_date
        sTimeStr = self.starttime
        eTimeStr = self.endtime
        if hasattr(self, 'stream'):
            dataST = self.stream
            utcSTime = dataST[0].stats.starttime
            utcETime = dataST[0].stats.endtime
        else:
            utcSTime = self.starttime
            utcETime = self.endtime
        
        minDur = int(str((utcETime - utcSTime)//60).split('.')[0])
        secDur = float(round((((utcETime - utcSTime) / 60) - int(minDur)) * 60, 3))
        if secDur >= 60:
            minDur += int(secDur//60)
            secDur = secDur - (secDur//60)*60

        acqDurStr = f'Record duration: {minDur}:{secDur:06.3f} ({utcETime-utcSTime} seconds)'
        if aDateStr == __get_ip_default('acq_date') and sTimeStr == __get_ip_default('starttime'):
            acqTimeStr += 'No acquisition time specified.\n'
        else:
            acqTimeStr += f"Acquisition Date: {aDateStr}\n"
            acqTimeStr += f"\tStarted at: {sTimeStr}\n"
            acqTimeStr += f"\tEnded at  : {eTimeStr}\n"
        acqTimeStr += acqDurStr


        # PEAK INFORMATION (IF CALCULATED)
        peakInfoStr = ''
        azimuth='HV'
        if 'BestPeak' in self.keys():
            curvTestsPassed = (self['BestPeak'][azimuth]['PassList']['WinLen'] +
                                self['BestPeak'][azimuth]['PassList']['SigCycles']+
                                self['BestPeak'][azimuth]['PassList']['LowCurveStD'])
            curvePass = curvTestsPassed > 2
            
            #Peak Pass?
            peakTestsPassed = ( self['BestPeak'][azimuth]['PassList']['ProminenceLow'] +
                        self['BestPeak'][azimuth]['PassList']['ProminenceHi']+
                        self['BestPeak'][azimuth]['PassList']['AmpClarity']+
                        self['BestPeak'][azimuth]['PassList']['FreqStability']+
                        self['BestPeak'][azimuth]['PassList']['LowStDev_Freq']+
                        self['BestPeak'][azimuth]['PassList']['LowStDev_Amp'])
            peakPass = peakTestsPassed >= 5

            peakInfoStr = "\nCALCULATED F₀\n"
            peakInfoStr += "-"*(len(peakInfoStr) - 3) + '\n'
            peakInfoStr += '{0:.3f} Hz ± {1:.4f} Hz'.format(self['BestPeak'][azimuth]['f0'], float(self["BestPeak"][azimuth]['Sf']))
            if curvePass and peakPass:
                peakInfoStr += '\n\t  {} Peak at {} Hz passed SESAME quality tests! :D'.format(sprit_utils._check_mark(), round(self['BestPeak'][azimuth]['f0'],3))
            else:
                peakInfoStr += '\n\t  {} Peak at {} Hz did NOT pass SESAME quality tests :('.format(sprit_utils._x_mark(), round(self['BestPeak'][azimuth]['f0'],3))
        else:
            peakInfoStr = 'F₀ not Calculated'

        printList = [
                    titleInfoStr,
                    peakInfoStr,
                    acqInstStr,
                    siteLocInfoStr,
                    acqTimeStr
                    ]

        strRep = ''
        for ps in printList:
            strRep += ps
        
        return strRep

        #try:
            # Check if running in IPython environment
        #    from IPython.display import display, HTML
        #    return f"<b>Person Information:</b><br>Name: {self.name}<br>Age: {self.age}"
        #except ImportError:
            # Fallback for terminal/console
        #    return f"Person Information:\nName: {self.name}\nAge: {self.age}"

    def __repr__(self):
        return self.__str__()

    # METHODS (many reflect dictionary methods)    
    def to_json(self, json_filepath=None, export_json=True, return_json=False, **kwargs):
        """Not yet supported, will export HVSRData object to json"""

        class_keys_to_convert = (datetime.date, obspy.UTCDateTime, 
                             datetime.time, CRS, obspy.Inventory)

        def iterative_json_parser(input_attrib=self, level=0):
            outValue = input_attrib
            
            if isinstance(input_attrib, dict):  # simplified condition for demo
            # if isinstance(input_attrib, (dict, sprit.HVSRData)):  # use this line instead
                outValue = {}
                level += 1
                for i, (key, value) in enumerate(input_attrib.items()):
                    outKey = key
                    print(level, "".join(['  ']*level), outKey)
                    if not isinstance(outKey, (str, int, float, bool, type(None))):
                        outKey = str(outKey)
                    
                    # Recursively process the value
                    processed_value = iterative_json_parser(value, level)
                    
                    # Apply string conversion if needed
                    if isinstance(processed_value, class_keys_to_convert):
                        processed_value = str(processed_value)
                    
                    outValue[outKey] = processed_value
                
                return outValue
            
            elif isinstance(input_attrib, list):
                outValue = []
                for item in input_attrib:
                    if isinstance(item, np.ndarray):
                        outValue.append(item.tolist())
                    else:
                        # Recursively process list items
                        outValue.append(iterative_json_parser(item, level))
                return outValue
            
            elif isinstance(input_attrib, np.ndarray):
                outValue = input_attrib.tolist()
                return outValue
            
            elif isinstance(input_attrib, pd.DataFrame):
                # Convert DataFrame to dict, but then recursively process it
                dict_value = input_attrib.to_dict()
                return iterative_json_parser(dict_value, level)
            
            elif isinstance(input_attrib, class_keys_to_convert):
                return str(input_attrib)
            
            else:
                return input_attrib

        sKeys = True
        if 'sort_keys' in kwargs:
            sKeys = kwargs['sort_keys']
            del kwargs['sort_keys']

        indent = 4
        if 'indent' in kwargs:
            indent = kwargs['indent']
            del kwargs['indent']

        if export_json and json_filepath is not None:
            with open(json_filepath, 'w') as f:
                # dump the JSON string to the file
                json.dump(self, fp=f, default=iterative_json_parser, 
                        sort_keys=True, indent=indent, **kwargs)

        if return_json or json_filepath is None:
            return json.dumps(self, default=iterative_json_parser,
                              sort_keys=True, indent=indent, **kwargs)

    def export(self, hvsr_export_path=None, ext='hvsr'):
        """Method to export HVSRData objects to .hvsr pickle files.

        Parameters
        ----------
        hvsr_export_path : filepath, default=True
            Filepath to save file. Can be either directory (which will assign a filename based on the HVSRData attributes). 
            By default True. 
            If True, it will first try to save each file to the same directory as input_data, then if that does not work, to the current working directory, then to the user's home directory, by default True
        ext : str, optional
            The extension to use for the output, by default 'hvsr'. This is still a pickle file that can be read with pickle.load(), but will have .hvsr extension.
        
        See Also
        --------
        export_hvsr
        
        """
        export_hvsr(hvsr_data=self, hvsr_export_path=hvsr_export_path, ext=ext)

    def copy(self, copy_type='shallow'):
        """Make a copy of the HVSRData object. Uses python copy module.
        
        Parameters
        ----------
        copy_type : str {'shallow', 'deep'}
            Based on input, creates either a shallow or deep copy of the HVSRData object. 
            Shallow is equivalent of copy.copy(). 
            Input of copy_type='deep' is equivalent of copy.deepcopy() (still experimental). 
            Defaults to shallow.
    
        """
        if copy_type.lower() == 'deep':
            return copy.deepcopy(self)
        else:
            return HVSRData(copy.copy(self.params))

    def export_settings(self, export_settings_path='default', export_settings_type='all', include_location=False, verbose=True):
        """Method to export settings from HVSRData object. Simply calls sprit.export_settings() from the HVSRData object. See sprit.export_settings() for more details.

        Parameters
        ----------
        export_settings_path : str, optional
            Filepath to output file. If left as 'default', will save as the default value in the resources directory. If that is not possible, will save to home directory, by default 'default'
        export_settings_type : str, {'all', 'instrument', 'processing'}, optional
            They type of settings to save, by default 'all'
        include_location : bool, optional
            Whether to include the location information in the instrument settings, if that settings type is selected, by default False
        verbose : bool, optional
            Whether to print output (filepath and settings) to terminal, by default True
        """
        export_settings(hvsr_data=self, 
                        export_settings_path=export_settings_path, export_settings_type=export_settings_type, include_location=include_location, verbose=verbose)

    def get_report(self, **kwargs):
        """Method to get report from processed data, in print, graphical, or tabular format.

        Returns
        -------
        Variable
            May return nothing, pandas.Dataframe, or pyplot Figure, depending on input.

        See Also
        --------
        get_report
        """
        report_return = get_report(hvsr_results=self, **kwargs)
        return report_return

    def items(self):
        """Method to return the "items" of the HVSRData object. For HVSRData objects, this is a dict_items object with the keys and values in tuples. Functions similar to dict.items().

        Returns
        -------
        dict_items
            A dict_items object of the HVSRData objects attributes, parameters, etc.
        """                
        return self.params.items()

    def keys(self):
        """Method to return the "keys" of the HVSRData object. For HVSRData objects, these are the attributes and parameters of the object. Functions similar to dict.keys().

        Returns
        -------
        dict_keys
            A dict_keys object of the HVSRData objects attributes, parameters, etc.
        """        
        keyList = []
        for k in dir(self):
            if not k.startswith('_'):
                keyList.append(k)
        return keyList   
        
    def plot(self, **kwargs):
        """Method to plot data, wrapper of sprit.plot_hvsr()

        Returns
        -------
        matplotlib.Figure, matplotlib.Axis (if return_fig=True)

        See Also
        --------
        plot_hvsr
        plot_azimuth
        """
        if 'close_figs' not in kwargs.keys():
            kwargs['close_figs']=True
        plot_return = plot_hvsr(self, **kwargs)
        plt.show()
        return plot_return

    def report(self, **kwargs):
        """Wrapper of get_report()
        
        See Also
        --------
        get_report
        """
        report_return = get_report(hvsr_results=self, **kwargs)
        return report_return
    
    def select(self, **kwargs):
        """Wrapper for obspy select method on 'stream' attribute of HVSRData object"""

        if hasattr(self, 'stream'):
            stream = self['stream'].select(**kwargs)
            return stream

        else:
            warnings.Warn("HVSRData.select() method applied, but 'stream' attribute (obspy.Stream object) not found")

    # ATTRIBUTES
    @property
    def params(self):
        """Dictionary containing the parameters used to process the data

        Returns
        -------
        dict
            Dictionary containing the process parameters
        """
        return self._params

    @params.setter
    def params(self, value):
        if not (isinstance(value, dict)):
            raise ValueError("params must be a dict type, currently passing {} type.".format(type(value)))
        self._params = value
    
    # batch
    @property
    def batch(self):
        """Whether this HVSRData object is part of an HVSRBatch object. This is used throughout the code to help direct the object into the proper processing pipeline.

        Returns
        -------
        bool
            True if HVSRData object is part of HVSRBatch object, otherwise, False
        """
        return self._batch

    @batch.setter
    def batch(self, value):
        if value == 0:
            value = False
        elif value == 1:
            value = True
        else:
            value = None
        if not isinstance(value, bool):
            raise ValueError("batch must be boolean type")
        self._batch = value

    #PPSD object from obspy (static)
    @property
    def ppsds_obspy(self):
        """The original ppsd information from the obspy.signal.spectral_estimation.PPSD(), so as to keep original if copy is manipulated/changed."""        
        return self._ppsds_obspy

    @ppsds_obspy.setter
    def ppsds_obspy(self, value):
        """Checks whether the ppsd_obspy is of the proper type before saving as attribute"""
        if not isinstance(value, obspy.signal.spectral_estimation.PPSD):
            if not isinstance(value, dict):
                raise ValueError("ppsds_obspy must be obspy.PPSD or dict with osbpy.PPSDs")
            else:
                for key in value.keys():
                    if not isinstance(value[key], obspy.signal.spectral_estimation.PPSD):
                        raise ValueError("ppsds_obspy must be obspy.PPSD or dict with osbpy.PPSDs")
        self._ppsds_obspy=value
                        
    #PPSD dict, copied from obspy ppsds (dynamic)
    @property
    def ppsds(self):
        """Dictionary copy of the class object obspy.signal.spectral_estimation.PPSD(). The dictionary copy allows manipulation of the data in PPSD, whereas that data cannot be easily manipulated in the original Obspy object.

        Returns
        -------
        dict
            Dictionary copy of the PPSD information from generate_psds()
        """
        return self._ppsds

    @ppsds.setter
    def ppsds(self, value):
        if not isinstance(value, dict):
            raise ValueError("ppsds dict with infomration from osbpy.PPSD (created by sprit.generate_psds())")                  
        self._ppsds=value

# Test guis
def _gui_test():
    import subprocess
    print(sprit_tkinter_ui.__file__)
    guiFile = sprit_tkinter_ui.__file__
    subprocess.call(guiFile, shell=True)


# Launch a gui
def gui(kind: str = 'browser'):
    """Function to open a graphical user interface (gui)

    Parameters
    ----------
    kind : str, optional
        What type of gui to open: 
        * "browser" or "default" opens browser interface (using streamlit)
        * "widget" opens jupyter widget (using ipywidgets)
        * "window" opens windowed gui (using tkinter)
        
    """
    browserList = ['browser', 'streamlit', 'default', 'd', 'b', 's']
    windowList = ['windowed', 'window', 'tkinter', 'tk', 't', 'win']
    widgetList = ['widget', 'jupyter', 'notebook', 'nb']
    liteList = ['lite', 'light', 'basic', 'l']

    if kind.lower() in browserList:
        import subprocess
        streamlitPath = pathlib.Path(__file__).parent.joinpath("sprit_streamlit_ui.py")
        cmd = ['streamlit', 'run', streamlitPath.as_posix()]
        #subprocess.run(cmd)
        import sys

        from streamlit.web import cli as stcli
        import streamlit
        import sys

        import subprocess
        import tempfile

        temp_dir = tempfile.TemporaryDirectory()
        def run_streamlit_app(path_dir):
            temp_dir = tempfile.TemporaryDirectory()
            # create a temporary directory
            fpathList = ['sprit_hvsr.py', 'sprit_tkinter_ui.py', 'sprit_jupyter_ui.py', 'sprit_utils.py', 'sprit_plot.py', '__init__.py', 'sprit_streamlit_ui.py']
            currDir = os.path.dirname(os.path.abspath(__file__))
            for fpath in fpathList:
                temp_file_path = os.path.join(temp_dir.name, fpath)
                with open(pathlib.Path(currDir).joinpath(fpath), 'r') as cf:
                    scriptText = cf.read()
                # write the streamlit app code to a Python script in the temporary directory
                with open(temp_file_path, 'w') as f:
                    f.write(scriptText)
            
            # execute the streamlit app
            try:
                # execute the streamlit app
                subprocess.run(
                    ['streamlit', "run", temp_file_path],
                    stderr=subprocess.DEVNULL
                    )
                
            except KeyboardInterrupt:
                pass
            # clean up the temporary directory when done
            temp_dir.cleanup()
        
        #with open(streamlitPath.parent.as_posix(), 'r') as file:
        #    appText = file.read()

        run_streamlit_app(pathlib.Path(__name__).parent)

        #streamlit.web.bootstrap.run(streamlitPath.as_posix(), '', [], [])
        #process = subprocess.Popen(["streamlit", "run", os.path.join(
        #            'application', 'main', 'services', 'streamlit_app.py')])             
    elif kind.lower() in windowList:
        #guiPath = pathlib.Path(os.path.realpath(__file__))
        try:
            from sprit.sprit_tkinter_ui import SPRIT_App
        except:
            from sprit.sprit_tkinter_ui import SPRIT_App
        
        try:
            import tkinter as tk
        except:
            if sys.platform == 'linux':
                raise ImportError('The SpRIT graphical interface uses tkinter, which ships with python but is not pre-installed on linux machines. Use "apt-get install python-tk" or "apt-get install python3-tk" to install tkinter. You may need to use the sudo command at the start of those commands.')

        def on_gui_closing():
            plt.close('all')
            gui_root.quit()
            gui_root.destroy()

        if sys.platform == 'linux':
            if not pathlib.Path("/usr/share/doc/python3-tk").exists():
                warnings.warn('The SpRIT graphical interface uses tkinter, which ships with python but is not pre-installed on linux machines. Use "apt-get install python-tk" or "apt-get install python3-tk" to install tkinter. You may need to use the sudo command at the start of those commands.')

        gui_root = tk.Tk()
        try:
            try:
                icon_path = pathlib.Path(str(importlib.resources.files('sprit'))).joinpath('resources').joinpath("icon").joinpath('sprit_icon_alpha.ico') 
                gui_root.iconbitmap(icon_path.as_posix())
            except:
                icon_path = pathlib.Path(str(importlib.resources.files('sprit'))).joinpath('resources').joinpath("icon").joinpath('sprit_icon.png') 
                gui_root.iconphoto(False, tk.PhotoImage(file=icon_path.as_posix()))
        except Exception as e:
            print("ICON NOT LOADED, still opening GUI")

        gui_root.resizable(True, True)
        spritApp = SPRIT_App(master=gui_root)  # Open the app with a tk.Tk root

        gui_root.protocol("WM_DELETE_WINDOW", on_gui_closing)    
        gui_root.mainloop()  # Run the main loop
    elif kind.lower() in widgetList:
        try:
            sprit_jupyter_UI.create_jupyter_ui()
        except Exception as e:
            if hasattr(e, 'message'):
                errMsg = e.message
            else:
                errMsg = e
            print(errMsg)
            raise e
            
    elif kind.lower() in liteList:
        print("Lite GUI is not currently supported")

# FUNCTIONS AND METHODS
# The run function to rule them all (runs all needed for simply processing HVSR)
def run(input_data=None, source='file', azimuth_calculation=False, noise_removal=False, outlier_curves_removal=False, verbose=False, **kwargs):
    """The sprit.run() is the main function that allows you to do all your HVSR processing in one simple step (sprit.run() is how you would call it in your code, but it may also be called using sprit.sprit_hvsr.run())
    
    The input_data parameter of sprit.run() is the only required parameter (if nothing entered, it will run sample data). This can be either a single file, a list of files (one for each component, for example), a directory (in which case, all obspy-readable files will be added to an HVSRBatch instance), a Rasp. Shake raw data directory, or sample data.
    
    Notes
    -----
    The sprit.run() function calls the following functions. This is the recommended order/set of functions to run to process HVSR using SpRIT. See the API documentation for these functions for more information:
    - input_params(): The input_data parameter of input_params() is the only required variable, though others may also need to be called for your data to process correctly.
    - fetch_data(): the source parameter of fetch_data() is the only explicit variable in the sprit.run() function aside from input_data and verbose. Everything else gets delivered to the correct function via the kwargs dictionary
    - remove_noise(): by default, the kind of noise removal is remove_method='auto'. See the remove_noise() documentation for more information. If remove_method is set to anything other than one of the explicit options in remove_noise, noise removal will not be carried out.
    - calculate_azimuth(): calculate one or several azimuths. Single azimuth can be a way to combine H components too.
    - generate_psds(): generates ppsds for each component, which will be combined/used later. Any parameter of obspy.signal.spectral_estimation.PPSD() may also be read into this function.
    - remove_outlier_curves(): removes any outlier ppsd curves so that the data quality for when curves are combined will be enhanced. See the remove_outlier_curves() documentation for more information.
    - process_hvsr(): this is the main function processing the hvsr curve and statistics. See process_hvsr() documentation for more details. The hvsr_band parameter sets the frequency spectrum over which these calculations occur.
    - check_peaks(): this is the main function that will find and 'score' peaks to get a best peak. The parameter peak_freq_range can be set to limit the frequencies within which peaks are checked and scored.
    - get_report(): this is the main function that will print, plot, and/or save the results of the data. See the get_report() API documentation for more information.
    - export_hvsr(): this function exports the final data output as a pickle file (by default, this pickle object has a .hvsr extension). This can be used to read data back into SpRIT without having to reprocess data.

    Parameters
    ----------
    input_data : str or filepath object that can be read by obspy
        Filepath to data to be processed. This may be a file or directory, depending on what kind of data is being processed (this can be specified with the source parameter). 
        For sample data, The following can be specified as the input_data parameter:
            - Any integer 1-6 (inclusive), or the string (e.g., input_data="1" or input_data=1 will work)
            - The word "sample" before any integer (e.g., input_data="sample1")
            - The word "sample" will default to "sample1" if source='file'. 
            - If source='batch', input_data should be input_data='sample' or input_data='batch'. In this case, it will read and process all the sample files using the HVSRBatch class. Set verbose=True to see all the information in the sample batch csv file.
    source : str, optional
        _description_, by default 'file'
    azimuth_calculation : bool, optional
        Whether to perform azimuthal analysis, by default False.
    noise_removal : bool, default=False
        Whether to remove noise (before processing PPSDs)
    outlier_curves_removal : bool, default=False
        Whether to remove outlier curves from HVSR time windows
    show_plot : bool, default=True
        Whether to show plots. This does not affect whether the plots are created (and then inserted as an attribute of HVSRData), only whether they are shown.
    verbose : bool, optional
        _description_, by default False
    **kwargs
        Keyword arguments for the functions listed above. The keyword arguments are unique, so they will get parsed out and passed into the appropriate function.

    Returns
    -------
    hvsr_results : sprit.HVSRData or sprit.HVSRBatch object
        If a single file/data point is being processed, a HVSRData object will be returned. Otherwise, it will be a HVSRBatch object. See their documention for more information.

    See Also
    --------
    input_params
    fetch_data
    remove_noise
    calculate_azimuth
    generate_psds
    remove_outlier_curves
    process_hvsr
    check_peaks
    get_report
    export_hvsr
        

    Raises
    ------
    RuntimeError
        If the input parameter may not be read correctly. This is raised if the input_params() function fails. This raises an error since no other data processing or reading steps will be able to carried out correctly.
    RuntimeError
        If the data is not read/fetched correctly using fetch_data(), an error will be raised. This is raised if the fetch_data() function fails. This raises an error since no other data processing steps will be able to carried out correctly.
    RuntimeError
        If the data being processed is a single file, an error will be raised if generate_psds() does not work correctly. No errors are raised for remove_noise() errors (since that is an optional step) and the process_hvsr() step (since that is the last processing step) .
    """
    
    if input_data is None or input_data == '':
        print("********************* PROCESSING SAMPLE DATA *****************************************")
        print("To read in your own data, use sprit.run(input_data='/path/to/your/seismic/data.mseed')")
        print("See SpRIT Wiki or API documentation for more information:")
        print("\t Wiki: https://github.com/RJbalikian/SPRIT-HVSR/wiki")
        print("\t API Documentation: https://sprit.readthedocs.io/en/latest/#")
        print("**************************************************************************************")
        print()
        input_data = 'sample'
    
    orig_args = locals().copy()  # Get the initial arguments
    global do_run
    do_run = True

    if verbose:
        print('Using sprit.run() with the following parameters:')
        print(f'\tinput_data = {input_data}')
        print(f'\tazimuth_calculation = {azimuth_calculation}')
        print(f'\tnoise_removal = {noise_removal}')
        print(f'\toutlier_curves_removal = {outlier_curves_removal}')
        print("\tWith the following kwargs: ", end='')
        if kwargs is not {}:
            print()
            for k, v in kwargs.items():
                print(f"\t\t{k} = {v}")
        else:
            print("{None}")
        print()
    
    if 'hvsr_band' not in kwargs.keys():
        kwargs['hvsr_band'] = inspect.signature(input_params).parameters['hvsr_band'].default
    if 'peak_freq_range' not in kwargs.keys():
        kwargs['peak_freq_range'] = inspect.signature(input_params).parameters['peak_freq_range'].default
    if 'processing_parameters' not in kwargs.keys():
        kwargs['processing_parameters'] = {}
    
    # Separate out input_params and fetch_data processes based on whether batch has been specified
    batchlist = ['batch', 'bach', 'bath', 'b']
    if str(source).lower() in batchlist and str('input_data').lower() not in SAMPLE_LIST:
        try:
            batch_data_read_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(batch_data_read).parameters.keys())}
            hvsrDataIN = batch_data_read(batch_data=input_data, verbose=verbose, **batch_data_read_kwargs)
        except Exception as e:
            raise RuntimeError(f'Batch data read in was not successful:\n{e}')
    else:
        # Get the input parameters
        try:
            input_params_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(input_params).parameters.keys())}
            params = input_params(input_data=input_data, verbose=verbose, **input_params_kwargs)
        except Exception as e:
            if hasattr(e, 'message'):
                errMsg = e.message
            else:
                errMsg = e
            
            print(f"ERROR during input_params(): {errMsg}")        
            # Even if batch, this is reading in data for all sites so we want to raise error, not just warn
            raise RuntimeError('Input parameters not read correctly, see sprit.input_params() function and parameters')
            # If input_params fails, initialize params as an HVSRDATA
            #params = {'processing_status':{'input_params_status':False, 'overall_status':False}}
            #params.update(input_params_kwargs)
            #params = sprit_utils._make_it_classy(params)

        # Fetch Data
        try:
            fetch_data_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(fetch_data).parameters.keys())}
            if 'obspy_ppsds' in kwargs:
                fetch_data_kwargs['obspy_ppsds'] = kwargs['obspy_ppsds']
            else:
                fetch_data_kwargs['obspy_ppsds'] = False
            hvsrDataIN = fetch_data(params=params, source=source, verbose=verbose, **fetch_data_kwargs)    
        except Exception as e:
            # Even if batch, this is reading in data for all sites so we want to raise error, not just warn
            if hasattr(e, 'message'):
                errMsg = e.message
            else:
                errMsg = e
            
            print(f"ERROR during fetch_data(): {errMsg}")
            raise RuntimeError('Data not read correctly, see sprit.fetch_data() function and parameters for more details.')
    
    # BREAK OUT FOR BATCH PROCESSING
    run_kwargs_for_df = []
    if isinstance(hvsrDataIN, HVSRBatch):
        
        # Create dictionary that will be used to create HVSRBatch object
        hvsrBatchDict = {}
        
        # Loop through each site and run sprit.run() for each HVSRData object
        for site_name, site_data in hvsrDataIN.items():
            run_kwargs = {}  #orig_args.copy()  # Make a copy so we don't accidentally overwrite
            print(f'\n\n**PROCESSING DATA FOR SITE {site_name.upper()}**\n')
            run_kwargs['input_data'] = site_data
            
            # Update run kwargs       
            # First, get processing_parameters per site
            for funname, fundict in site_data['processing_parameters'].items():
                for funk, funv in fundict.items():
                    run_kwargs[funk] = funv
                                                
            # Overwrite per-site processing parameters with params passed  to sprit.run() as kwargs
            for paramname, paramval in kwargs.items():
                if paramname != 'source':  # Don't update source for batch data
                    run_kwargs[paramname] = paramval

            dont_update_these_args = ['input_data', 'source', 'kwargs']

            # Overwrite per-site processing parameters with sprit.run()
            run_args = orig_args.copy()
            for k, v in run_args.items():
                if k not in dont_update_these_args:
                    if v != inspect.signature(run).parameters[k].default:
                        run_kwargs[k] = v
                                   
            try:
                hvsrBatchDict[site_name] = run(**run_kwargs)
                run_kwargs_for_df.append(run_kwargs)
            except Exception as e:
                hvsrBatchDict[site_name] = site_data
                hvsrBatchDict[site_name]['Error_Message'] = sprit_utils._get_error_from_exception(e,
                                                                                                  print_error_message=False,
                                                                                                  return_error_message=True)
                if verbose:
                    sprit_utils._get_error_from_exception(e)
                    
                print(f"Error processing site {site_name}. Continuing processing of remaining sites.")
                
                hvsrBatchDict[site_name]['processing_status']['generate_psds_status'] = False
                hvsrBatchDict[site_name]['processing_status']['overall_status'] = False         
        
        # Create batch object
        hvsrBatchData = HVSRBatch(hvsrBatchDict, df_as_read=pd.DataFrame(run_kwargs_for_df))
        
        # Use batch object to get Output Table with all data, including results and inputs
        for s, site in enumerate(hvsrBatchData):
            if hasattr(hvsrBatchData[site], 'Table_Report'):
                if s == 0:
                    table_reports = hvsrBatchData[site].Table_Report
                else:
                    table_reports = pd.concat([table_reports, hvsrBatchData[site].Table_Report])
            else:
                if s == 0:
                    table_reports = pd.DataFrame()
                
        hvsrBatchData['Table_Report'] = pd.merge(left=hvsrBatchData.input_df, right=table_reports,
                                                 how='outer',
                                                 left_on='site', right_on='Site Name')
        return hvsrBatchData

    # Calculate azimuths
    hvsr_az = hvsrDataIN
    azimuth_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(calculate_azimuth).parameters.keys())}
    
    azList = ['azimuth', 'single azimuth', 'single']
    
    azCond1 = 'horizontal_method' in kwargs.keys() and str(kwargs['horizontal_method']) == '8'
    azCond2 = 'horizontal_method' in kwargs.keys() and str(kwargs['horizontal_method']).lower() in azList
    azCond3 = azimuth_calculation
    azCond4 = len(azimuth_kwargs.keys()) > 0

    if azCond1 or azCond2 or azCond3 or azCond4:
        azimuth_calculation = True
        azimuth_kwargs['azimuth_type'] = kwargs['azimuth_type'] = 'single'
        
        if 'azimuth_angle' not in kwargs.keys():
            azimuth_kwargs['azimuth_angle'] = kwargs['azimuth_angle'] = 45
        
        kwargs['azimuth'] = "R"  # str(kwargs['azimuth_angle']).zfill(3)
        
        if 'horizontal_method' not in kwargs.keys():
            kwargs['horizontal_method'] = 'Single Azimuth'

        try:
            hvsr_az = calculate_azimuth(hvsrDataIN, verbose=verbose, **azimuth_kwargs)
        except Exception as e:
            if hasattr(e, 'message'):
                errMsg = e.message
            else:
                errMsg = e
            
            print(f"Error during calculate_azimuth() for {hvsr_az.site}: \n{errMsg}")            

            if isinstance(hvsr_az, HVSRBatch):
                for site_name in hvsr_az.keys():
                    hvsr_az[site_name]['processing_status']['calculate_azimuths_status'] = False
            else:
                hvsr_az['processing_status']['calculate_azimuths_status'] = False
    else:
        azimuth_calculation = False
        
     
    # Remove Noise
    data_noiseRemoved = hvsr_az
    try:
        remove_noise_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(remove_noise).parameters.keys())}
        if noise_removal or remove_noise_kwargs != {}:
            remove_noise_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(remove_noise).parameters.keys())}
            try:
                data_noiseRemoved = remove_noise(hvsr_data=data_noiseRemoved, verbose=verbose, **remove_noise_kwargs)   
            except Exception as e:
                if hasattr(e, 'message'):
                    errMsg = e.message
                else:
                    errMsg = e                    
                
                print(f"Error with remove_noise for site {data_noiseRemoved.site}: {errMsg}")
                
                # Mark that remove_noise failed
                # Reformat data so HVSRData and HVSRBatch data both work here
                if isinstance(data_noiseRemoved, HVSRData):
                    data_noiseRemoved = {data_noiseRemoved.site: data_noiseRemoved}
                    data_noiseRemoved = {data_noiseRemoved.site: data_noiseRemoved}
                    
                for site_name in data_noiseRemoved.keys():
                    data_noiseRemoved[site_name]['processing_status']['remove_noise_status'] = False
                    # Since noise removal is not required for data processing, check others first
                    if data_noiseRemoved[site_name]['processing_status']['overall_status']:
                        data_noiseRemoved[site_name]['processing_status']['overall_status'] = True        
                    else:
                        data_noiseRemoved[site_name]['processing_status']['overall_status'] = False

                    # If it wasn't originally HVSRBatch, make it HVSRData object again
                    if not data_noiseRemoved[site_name]['batch']:
                        data_noiseRemoved = data_noiseRemoved[site_name]
        else:
            if isinstance(data_noiseRemoved, HVSRData):
                data_noiseRemoved = {data_noiseRemoved.site: data_noiseRemoved}
                
            for site_name in data_noiseRemoved.keys():  # This should work more or less the same for batch and regular data now
                data_noiseRemoved[site_name]['stream_edited'] = data_noiseRemoved[site_name]['stream']
                
                data_noiseRemoved[site_name]['processing_status']['remove_noise_status'] = None
        
                # If it wasn't originally HVSRBatch, make it HVSRData object again
                #if not data_noiseRemoved[site_name]['batch']:
                data_noiseRemoved = data_noiseRemoved[site_name]
    except Exception as e:
        if (source == 'file' or source == 'raw'):
            if hasattr(e, 'message'):
                errMsg = e.message
            else:
                errMsg = e
            if not ('batch' in data_noiseRemoved.keys() and data_noiseRemoved['batch']):
                raise RuntimeError(f"generate_psds() error: {errMsg}")
    
    # Generate PPSDs
    psd_data = data_noiseRemoved
    try:
        generate_psds_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(generate_psds).parameters.keys())}
        PPSDkwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(PPSD).parameters.keys())}
        generate_psds_kwargs.update(PPSDkwargs)
        generate_psds_kwargs['azimuthal_psds'] = azimuth_calculation
        psd_data = generate_psds(hvsr_data=psd_data, verbose=verbose, **generate_psds_kwargs)
    except Exception as e:
        if hasattr(e, 'message'):
            errMsg = e.message
        else:
            errMsg = e
        
        if verbose:
            print(f"Error during generate_psds() for {site_name}: \n{errMsg}")
        if (source == 'file' or source == 'raw') and verbose:
            raise RuntimeError(f"generate_psds() error: {errMsg}")

        # Reformat data so HVSRData and HVSRBatch data both work here
        if isinstance(psd_data, HVSRData):
            psd_data = {psd_data['site']: psd_data}
            
        for site_name in psd_data.keys():  # This should work more or less the same for batch and regular data now
            psd_data[site_name]['processing_status']['generate_psds_status'] = False
            psd_data[site_name]['processing_status']['overall_status'] = False
    
            #If it wasn't originally HVSRBatch, make it HVSRData object again
            if not psd_data[site_name]['batch']:
                psd_data = psd_data[site_name]

    # Remove Outlier PSD Curves
    data_curvesRemoved = psd_data
    try:
        remove_outlier_curve_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(remove_outlier_curves).parameters.keys())}
        if 'use_hv_curves' not in remove_outlier_curve_kwargs.keys():
            use_hv_curves = False
        else:
            use_hv_curves = remove_outlier_curve_kwargs['use_hv_curves']
        # Check whether it is indicated to remove outlier curves
        outlier_curve_keys_used = True
        if remove_outlier_curve_kwargs == {} or list(remove_outlier_curve_kwargs.keys()) == ['show_plot']:
            outlier_curve_keys_used = False
        if (outlier_curves_removal or outlier_curve_keys_used) and not use_hv_curves:
            remove_outlier_curve_kwargs['remove_outliers_during_plot'] = False
            data_curvesRemoved = remove_outlier_curves(hvsr_data=data_curvesRemoved, verbose=verbose,**remove_outlier_curve_kwargs)   
    except Exception as e:
        traceback.print_exception(sys.exc_info()[1])
        exc_type, exc_obj, tb = sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        errLineNo = str(traceback.extract_tb(sys.exc_info()[2])[-1].lineno)
        error_category = type(e).__name__.title().replace('error', 'Error')
        error_message = f"{e} ({errLineNo})"
        print(f"{error_category} ({errLineNo}): {error_message}")
        print(lineno, filename, f)
        
        # Reformat data so HVSRData and HVSRBatch data both work here
        if isinstance(data_curvesRemoved, HVSRData):
            data_curvesRemoved_interim = {data_curvesRemoved['site']: data_curvesRemoved}
        else:
            data_curvesRemoved_interim = data_curvesRemoved
        
        for site_name in data_curvesRemoved_interim.keys():  # This should work more or less the same for batch and regular data now
            data_curvesRemoved_interim[site_name]['processing_status']['remove_outlier_curves_status'] = False
            #data_curvesRemoved_interim[site_name]['processing_status']['overall_status'] = False
    
            #If it wasn't originally HVSRBatch, make it HVSRData object again
            if not data_curvesRemoved_interim[site_name]['batch']:
                data_curvesRemoved_interim = data_curvesRemoved_interim[site_name]
        data_curvesRemoved = data_curvesRemoved_interim
        
    # Process HVSR Curves
    hvsr_results = data_curvesRemoved
    try:
        process_hvsr_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(process_hvsr).parameters.keys())}
        
        if azimuth_calculation:
            if azimuth_kwargs['azimuth_type'] == 'single':
                process_hvsr_kwargs['azimuth'] = azimuth_kwargs['azimuth_angle']
        
        hvsr_results = process_hvsr(hvsr_data=psd_data, verbose=verbose, **process_hvsr_kwargs)
    except Exception as e:
        sprit_utils._get_error_from_exception(e,
                                              print_error_message=True)
        if isinstance(hvsr_results, HVSRData):
            hvsr_results = {hvsr_results['site']: hvsr_results}
            
        for site_name in hvsr_results.keys():  # This should work more or less the same for batch and regular data now
        
            hvsr_results[site_name]['processing_status']['process_hvsr_status']=False
            hvsr_results[site_name]['processing_status']['overall_status'] = False
            
            # If it wasn't originally HVSRBatch, make it HVSRData object again
            if not hvsr_results[site_name]['batch']:
                hvsr_results = hvsr_results[site_name]            

    # Remove outlier HV Curves
    try:
        remove_outlier_curve_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(remove_outlier_curves).parameters.keys())}
        if 'use_hv_curves' not in remove_outlier_curve_kwargs.keys():
            use_hv_curves = False
        else:
            use_hv_curves = remove_outlier_curve_kwargs['use_hv_curves']
        # Check whether it is indicated to remove outlier curves
        outlier_curve_keys_used = True
        if remove_outlier_curve_kwargs == {} or list(remove_outlier_curve_kwargs.keys()) == ['show_plot']:
            outlier_curve_keys_used = False
        if (outlier_curves_removal or outlier_curve_keys_used) and use_hv_curves:
            remove_outlier_curve_kwargs['remove_outliers_during_plot'] = False
            hvsr_results = remove_outlier_curves(hvsr_data=hvsr_results, verbose=verbose,**remove_outlier_curve_kwargs)   
    except Exception as e:
        traceback.print_exception(sys.exc_info()[1])
        exc_type, exc_obj, tb = sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        errLineNo = str(traceback.extract_tb(sys.exc_info()[2])[-1].lineno)
        error_category = type(e).__name__.title().replace('error', 'Error')
        error_message = f"{e} ({errLineNo})"
        print(f"{error_category} ({errLineNo}): {error_message}")
        print(lineno, filename, f)
        
        # Reformat data so HVSRData and HVSRBatch data both work here
        if isinstance(hvsr_results, HVSRData):
            data_curvesRemoved_interim = {hvsr_results['site']: hvsr_results}
        else:
            data_curvesRemoved_interim = hvsr_results
        
        for site_name in data_curvesRemoved_interim.keys():  # This should work more or less the same for batch and regular data now
            data_curvesRemoved_interim[site_name]['processing_status']['remove_outlier_curves_status'] = False
            #data_curvesRemoved_interim[site_name]['processing_status']['overall_status'] = False
    
            #If it wasn't originally HVSRBatch, make it HVSRData object again
            if not data_curvesRemoved_interim[site_name]['batch']:
                data_curvesRemoved_interim = data_curvesRemoved_interim[site_name]
        hvsr_results = data_curvesRemoved_interim
        

    # Final post-processing/reporting
    # Check peaks
    check_peaks_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(check_peaks).parameters.keys())}
    hvsr_results = check_peaks(hvsr_data=hvsr_results, verbose=verbose, **check_peaks_kwargs)

    get_report_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(get_report).parameters.keys())}
    # Add 'az' as a default plot if the following conditions
    # first check if report_formats is specified, if not, add default value
    if 'report_formats' not in get_report_kwargs.keys():
        get_report_kwargs['report_formats'] = inspect.signature(get_report).parameters['report_formats'].default
    
    # Now, check if plot is specified, then if plot_type is specified, then add 'az' if stream has azimuths
    if 'plot' in get_report_kwargs['report_formats']:
        plot_hvsr_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(plot_hvsr).parameters.keys())}
        get_report_kwargs.update(plot_hvsr_kwargs)
        usingDefault = True
        if 'plot_type' not in get_report_kwargs.keys():
            get_report_kwargs['plot_type'] = inspect.signature(get_report).parameters['plot_type'].default
        else:
            usingDefault = False

        # Check if az is already specified as plot output
        azList = ['azimuth', 'az', 'a', 'radial', 'r']
        az_requested = False
        
        get_report_kwargs['plot_type'] = [item.lower() for item in get_report_kwargs['plot_type'].split(' ')]
        for azStr in azList:
            if azStr.lower() in get_report_kwargs['plot_type']:
                az_requested = True
                break
        get_report_kwargs['plot_type'] = ' '.join(get_report_kwargs['plot_type'])

        if isinstance(hvsr_results, HVSRData):
            hvsr_results_interim = {hvsr_results['site']: hvsr_results}
        else:
            hvsr_results_interim = hvsr_results

        for site_name in hvsr_results_interim.keys():  # This should work more or less the same for batch and regular data now
            # Check if data has azimuth data
            hasAz = False
            if 'stream' in hvsr_results_interim[site_name].keys():
                for tr in hvsr_results_interim[site_name]['stream']:
                    if tr.stats.component == 'R':
                        hasAz = True
                        break
            
            # Assuming all sites in batch have az if one does
            if hasAz:
                break

            # If it wasn't originally HVSRBatch, make it HVSRData object again
            #if not hvsr_results_interim[site_name]['batch']:
            #    hvsr_results_interim = hvsr_results_interim[site_name]            
            
        # Add azimuth as a requested plot if azimuthal data exists but not requested in plot
        if not az_requested and hasAz and hvsr_results.horizontal_method != 'Single Azimuth':
            get_report_kwargs['plot_type'] = get_report_kwargs['plot_type'] + ' az'

    hvsr_results = get_report(hvsr_results=hvsr_results, verbose=verbose, **get_report_kwargs)

    if verbose:
        if 'report_formats' in get_report_kwargs.keys():
            if type(get_report_kwargs['report_formats']) is str:
                report_formats = get_report_kwargs['report_formats'].lower()
            elif isinstance(get_report_kwargs['report_formats'], (tuple, list)):
                for i, rf in enumerate(get_report_kwargs['report_formats']):
                    get_report_kwargs['report_formats'][i] = rf.lower()
                    
            # if report_formats is 'print', we would have already printed it in previous step
            if get_report_kwargs['report_formats'] == 'print' or 'print' in get_report_kwargs['report_formats'] or isinstance(hvsr_results, HVSRBatch):
                # We do not need to print another report if already printed to terminal
                pass
            else:
                # We will just change the report_formats kwarg to print, since we already got the originally intended report format above, 
                #   now need to print for verbose output
                get_report_kwargs['report_formats'] = 'print'
                get_report(hvsr_results=hvsr_results, **get_report_kwargs)
                
            if get_report_kwargs['report_formats'] == 'plot' or 'plot' in get_report_kwargs['report_formats']:
                # We do not need to plot another report if already plotted
                pass
            else:
                # hvplot_kwargs = {k: v for k, v in kwargs.items() if k in plot_hvsr.__code__.co_varnames}
                # hvsr_results['Plot_Report'] = plot_hvsr(hvsr_results, return_fig=True, show_plot=False, close_figs=True)
                pass
        else:
            pass
    
    # Export processed data if hvsr_export_path(as pickle currently, default .hvsr extension)
    if 'hvsr_export_path' in kwargs.keys():
        if kwargs['hvsr_export_path'] is None:
            pass
        else:
            if 'ext' in kwargs.keys():
                ext = kwargs['ext']
            else:
                ext = 'hvsr'
            export_hvsr(hvsr_data=hvsr_results, hvsr_export_path=kwargs['hvsr_export_path'], ext=ext, verbose=verbose)        
    if 'show_plot' in kwargs:
        if not kwargs['show_plot']:
            plt.close()


    return hvsr_results


# Read data as batch
def batch_data_read(batch_data, batch_type='table', param_col=None, batch_params=None, verbose=False, **readcsv_getMeta_fetch_kwargs):
    """Function to read data in data as a batch of multiple data files. 
      This is best used through sprit.fetch_data(*args, source='batch', **other_kwargs).

    Parameters
    ----------
    batch_data : filepath or list
        Input data information for how to read in data as batch. Can be filepath or list of filepaths/stream objects.
        If filepath, should point to .csv (or similar that can be read by pandas.read_csv()) with batch data information.
    batch_type : str, optional
        Type of batch read, only 'table' and 'filelist' accepted. 
        If 'table', will read data from a file read in using pandas.read_csv(), by default 'table'
    param_col : None or str, optional
        Name of parameter column from batch information file. Only used if a batch_type='table' and single parameter column is used, rather than one column per parameter (for single parameter column, parameters are formatted with = between keys/values and , between item pairs), by default None
    batch_params : list, dict, or None, default = None
        Parameters to be used if batch_type='filelist'. If it is a list, needs to be the same length as batch_data. If it is a dict, will be applied to all files in batch_data and will combined with extra keyword arguments caught by **readcsv_getMeta_fetch_kwargs.
    verbose : bool, optional
        Whether to print information to terminal during batch read, by default False
    **readcsv_getMeta_fetch_kwargs
        Keyword arguments that will be read into pandas.read_csv(), sprit.input_params, sprit.get_metadata(), and/or sprit.fetch_data()

    Returns
    -------
    hvsrBatch
        HVSRBatch object with each item representing a different HVSRData object

    Raises
    ------
    IndexError
        _description_
    """

    if verbose:
        print(f'Processing batch data from {batch_type}:')
        print(f"  Batch data source: {batch_data}")

    # First figure out which parameters go with which function
    input_params_params = inspect.signature(input_params).parameters
    get_metadata_params = inspect.signature(get_metadata).parameters
    fetch_data_params = inspect.signature(fetch_data).parameters
    calculate_azimuth_params = inspect.signature(calculate_azimuth).parameters
    remove_noise_params = inspect.signature(remove_noise).parameters
    generate_ppsds_params = inspect.signature(generate_psds).parameters
    remove_outlier_curves_params = inspect.signature(remove_outlier_curves).parameters
    process_hvsr_params = inspect.signature(process_hvsr).parameters
    check_peaks_params = inspect.signature(check_peaks).parameters
    get_report_params = inspect.signature(get_report).parameters
  
    dict_of_params = {'input_params': input_params_params,
                      'get_metadata': get_metadata_params,
                      'fetch_data_params': fetch_data_params,
                      'calculate_azimuth_params': calculate_azimuth_params,
                      'remove_noise_params': remove_noise_params,
                      'generate_ppsds_params': generate_ppsds_params,
                      'remove_outlier_curves_params': remove_outlier_curves_params,
                      'process_hvsr_params': process_hvsr_params,
                      'check_peaks_params': check_peaks_params,
                      'get_report_params': get_report_params}
    
    def __get_run_functions():
        # Get a list of all functions (for which paramters are used) in sprit.run()
        run_functions_list = [input_params, fetch_data, batch_data_read,
                            get_metadata, calculate_azimuth, 
                            remove_noise, generate_psds, remove_outlier_curves, 
                            process_hvsr, check_peaks, 
                            get_report, export_hvsr]
        
        return run_functions_list
    SPRIT_RUN_FUNCTIONS = __get_run_functions()
    # Get default values of all functions in a dict
    default_dict = {}
    for i, fun in enumerate(SPRIT_RUN_FUNCTIONS):
        for param_name, param_info in inspect.signature(fun).parameters.items():
            if param_info.default is not inspect._empty:
                default_dict[param_name] = param_info.default
    
    if batch_type == 'sample' or batch_data in sampleFileKeyMap.keys():
        sample_data = True
        batch_type = 'table'
    else:
        sample_data = False
    
    # Dictionary to store the stream objects
    stream_dict = {}
    data_dict = {}
    if batch_type == 'table':
        # If this is sample data, we need to create absolute paths to the filepaths
        if sample_data:
            dataReadInfoDF = pd.read_csv(sampleFileKeyMap['sample_batch'])
            for index, row in dataReadInfoDF.iterrows():
                dataReadInfoDF.loc[index, 'input_data'] = SAMPLE_DATA_DIR.joinpath(row.loc['input_data'])
        elif isinstance(batch_data, pd.DataFrame):
            dataReadInfoDF = batch_data
        elif isinstance(batch_data, dict):
            # For params input
            dataReadInfoDF = pd.DataFrame.from_dict(batch_data)
            pass
        else:  # Read csv
            read_csv_kwargs = {k: v for k, v in locals()['readcsv_getMeta_fetch_kwargs'].items() if k in inspect.signature(pd.read_csv).parameters}
            dataReadInfoDF = pd.read_csv(batch_data, **read_csv_kwargs)
            if 'input_data' in dataReadInfoDF.columns:
                filelist = list(dataReadInfoDF['input_data'])

        # Generate site names if they don't exist already           
        if 'site' not in dataReadInfoDF.columns:
            siterows = []
            filldigs = len(str(dataReadInfoDF.shape[0]))  # Number of digits in df shape
            for i, row in dataReadInfoDF.iterrows():
                siterows.append(f'HVSRSite_{str(i).zfill(filldigs)}')
            dataReadInfoDF['site'] = siterows

        # Print information about batch read, as specified
        print(f"  {dataReadInfoDF.shape[0]} sites found: {list(dataReadInfoDF['site'])}")
        if verbose:
            maxLength = 25
            maxColWidth = 12
            if dataReadInfoDF.shape[0] > maxLength:
                print(f'\t Showing information for first {maxLength} files only:')
            print()
            
            # Print nicely formatted df
            # Print column names
            print('  ', end='')
            for col in dataReadInfoDF.columns:
                print(str(col)[:maxColWidth].ljust(maxColWidth), end='  ')
            
            print('\n', end='')
            # Print separator
            tableLen = (maxColWidth+2)*len(dataReadInfoDF.columns)
            for r in range(tableLen):
                print('-', end='')
            print()

            #Print columns/rows
            for index, row in dataReadInfoDF.iterrows():
                print('  ', end='')
                for col in row:
                    if len(str(col)) > maxColWidth:
                        print((str(col)[:maxColWidth-3]+'...').ljust(maxColWidth), end='  ')
                    else:
                        print(str(col)[:maxColWidth].ljust(maxColWidth), end='  ')
                print()
            if dataReadInfoDF.shape[0] > maxLength:
                endline = f'\t...{dataReadInfoDF.shape[0]-maxLength} more rows in file.\n'
            else:
                endline = '\n'
            print(endline)

            print('Fetching the following files:')
            
        # Get processing parameters, either from column param_col or from individual columns
        # If param_col, format is string of format: "param_name=param_val, param_name2=param_val2"
        param_dict_list = []
        verboseStatement = []
        if param_col is None:  # Not a single parameter column, each col=parameter
            for row_ind in range(dataReadInfoDF.shape[0]):
                param_dict = {}
                verboseStatement.append([])
                for col in dataReadInfoDF.columns:
                    for fun in SPRIT_RUN_FUNCTIONS:
                        if col in inspect.signature(fun).parameters:
                            currParam = dataReadInfoDF.loc[row_ind, col]
                            if pd.isna(currParam) or currParam == 'nan':
                                if col in default_dict.keys():
                                    param_dict[col] = default_dict[col]  # Get default value
                                    if verbose:
                                        if type(default_dict[col]) is str:
                                            verboseStatement[row_ind].append("\t\t'{}' parameter not specified in batch file. Using {}='{}'".format(col, col, default_dict[col]))
                                        else:
                                            verboseStatement[row_ind].append("\t\t'{}' parameter not specified in batch file. Using {}={}".format(col, col, default_dict[col]))
                                else:
                                    param_dict[col] = None
                            else:
                                param_dict[col] = dataReadInfoDF.loc[row_ind, col]
                param_dict_list.append(param_dict)
        else:
            if param_col not in dataReadInfoDF.columns:
                raise IndexError('{} is not a column in {} (columns are: {})'.format(param_col, batch_data, dataReadInfoDF.columns))
            for row in dataReadInfoDF[param_col]:
                param_dict = {}
                splitRow = str(row).split(',')
                for item in splitRow:
                    param_dict[item.split('=')[0]] = item.split('=')[1]
                param_dict_list.append(param_dict)

    elif batch_type == 'filelist':
        if not isinstance(batch_data, (list, tuple)):
            raise RuntimeError(f"If batch_type is specified as 'filelist' or 'list', batch_data must be list or tuple, not {type(batch_data)}.")

        # Update formatting of batch_params for rest of processing
        if batch_params is None:
            batch_params = [{}] * len(batch_data)
        
        # Get batch_parameters
        if isinstance(batch_params, list):
            if len(batch_params) != len(batch_data):
                raise RuntimeError('If batch_params is list, it must be the same length as batch_data. len(batch_params)={} != len(batch_data)={}'.format(len(batch_params), len(batch_data)))
            param_dict_list = batch_params
        elif isinstance(batch_params, dict):
            batch_params.update(readcsv_getMeta_fetch_kwargs)
            param_dict_list = []
            for i in range(len(batch_data)):
                param_dict_list.append(batch_params)
        
        # Read and process each MiniSEED file
        for i, file in enumerate(batch_data):
            param_dict_list[i]['input_data'] = file
    
    # Get a uniformly formatted input DataFrame
    input_df_uniformatted = pd.DataFrame(param_dict_list)   
    
    # Do batch fun of input_params() and fetch_data() (these are skipped in run() if batch mode is used)
    hvsr_batchDict = {}
    zfillDigs = len(str(len(param_dict_list)))  # Get number of digits of length of param_dict_list
    i = 0
    for i, param_dict in enumerate(param_dict_list):       
        # Read the data file into a Stream object
        input_params_kwargs = {k: v for k, v in locals()['readcsv_getMeta_fetch_kwargs'].items() if k in inspect.signature(input_params).parameters}
        input_params_kwargs2 = {k: v for k, v in param_dict.items() if k in inspect.signature(input_params).parameters}
        input_params_kwargs.update(input_params_kwargs2)

        # Run input_params()
        try:
            ipverboseString = '\tinput_params: <No parameters specified>, '
            for arg, value in input_params_kwargs.items():
                ipverboseString = ipverboseString.replace('<No parameters specified>, ', '')                    
                ipverboseString += f"{arg}={value}, "
            ipverboseString = ipverboseString[:-2]
            ipverboseString = (ipverboseString[:96] + '...') if len(ipverboseString) > 99 else ipverboseString

            params = input_params(**input_params_kwargs)
        except Exception as e:
            params = input_params_kwargs
            params['processing_status'] = {}
            params['processing_status']['input_params_status'] = False
            params['processing_status']['overall_status'] = False 
            verboseStatement.append(f"\t{e}")

        # Run fetch_data()
        fetch_data_kwargs = {k: v for k, v in locals()['readcsv_getMeta_fetch_kwargs'].items() if k in inspect.signature(fetch_data).parameters}
        fetch_data_kwargs2 = {k: v for k, v in param_dict.items() if k in inspect.signature(fetch_data).parameters}
        fetch_data_kwargs.update(fetch_data_kwargs2)
        
        try:
            fdverboseString = '\tfetch_data: <No parameters specified>, '
            for arg, value in fetch_data_kwargs.items():
                fdverboseString = fdverboseString.replace('<No parameters specified>, ', '')
                fdverboseString += f"{arg}={value}, "
            fdverboseString = fdverboseString[:-2]
            fdverboseString = (fdverboseString[:96] + '...') if len(fdverboseString) > 99 else fdverboseString
                
            hvsrData = fetch_data(params=params, **fetch_data_kwargs)
        except Exception as e:
            hvsrData = params
            hvsrData['processing_status']['fetch_data_status'] = False
            hvsrData['processing_status']['overall_status'] = False
            verboseStatement.append(f"\t{e}")
    
        if verbose and hvsrData['processing_status']['overall_status']:
            print(f"  {hvsrData['site']}")
            print(ipverboseString)
            print(fdverboseString)
            if verboseStatement != []:
                for item in verboseStatement[i]:
                    print(item)
        elif verbose and not hvsrData['processing_status']['overall_status']:
            if 'site' in param_dict.keys():
                sitename = param_dict['site']
            else:
                sitename = 'UNSPECIFIED_SITE'
                
            print(f"  {sitename}")
            print(ipverboseString)
            print(fdverboseString)
            if verboseStatement != []:
                for item in verboseStatement[i]:
                    print(item)
            print(f"     *{sitename} not read correctly. Processing will not be carried out.")

        hvsrData['batch'] = True

        # This may be redundant
        if hvsrData['site'] == default_dict['site']:  # If site was not designated
            hvsrData['site'] = "{}_{}".format(hvsrData['site'], str(i).zfill(zfillDigs))
            i += 1
            
        # Get processing parameters for other functions in sprit.run() besides input_params and fetch_data
        if 'processing_parameters' in hvsrData.keys():
            processing_parameters = hvsrData['processing_parameters'].copy()
        else:
            processing_parameters = {}  # "input_params": input_params_kwargs, "fetch_data": fetch_data_kwargs}

        for fun in SPRIT_RUN_FUNCTIONS:
            specified_params = {k: v for k, v in param_dict.items() if k in inspect.signature(fun).parameters}
            processing_parameters[fun.__name__] = specified_params

        # Assume source is 'file' if not specified
        hvsrData['processing_parameters'] = processing_parameters
        if 'source' not in hvsrData['processing_parameters']['fetch_data'].keys():
            hvsrData['processing_parameters']['fetch_data']['source'] = 'file'
        
        hvsr_batchDict[hvsrData['site']] = hvsrData

    hvsrBatch = HVSRBatch(hvsr_batchDict, df_as_read=input_df_uniformatted)

    print()
    print('Finished reading input data in preparation for batch processing')
    return hvsrBatch


# Function to generate azimuthal readings from the horizontal components
def calculate_azimuth(hvsr_data, azimuth_angle=45, azimuth_type='multiple', azimuth_unit='degrees', 
                      show_az_plot=False, verbose=False, **plot_azimuth_kwargs):
    """Function to calculate azimuthal horizontal component at specified angle(s). 
       Adds each new horizontal component as a radial component to obspy.Stream object at hvsr_data['stream']

    Parameters
    ----------
    hvsr_data : HVSRData
        Input HVSR data
    azimuth_angle : int, default=10
        If `azimuth_type='multiple'`, this is the angular step (in unit `azimuth_unit`) of each of the azimuthal measurements.
        If `azimuth_type='single'` this is the angle (in unit `azimuth_unit`) of the single calculated azimuthal measruement. By default 10.
    azimuth_type : str, default='multiple'
        What type of azimuthal measurement to make, by default 'multiple'.
        If 'multiple' (or {'multi', 'mult', 'm'}), will take a measurement at each angular step of azimuth_angle of unit azimuth_unit.
        If 'single' (or {'sing', 's'}), will take a single azimuthal measurement at angle specified in azimuth_angle.
    azimuth_unit : str, default='degrees'
        Angular unit used to specify `azimuth_angle` parameter. By default 'degrees'.
        If 'degrees' (or {'deg', 'd'}), will use degrees.
        If 'radians' (or {'rad', 'r'}), will use radians.
    show_az_plot : bool, default=False
        Whether to show azimuthal plot, by default False.
    verbose : bool, default=False
        Whether to print terminal output, by default False

    Returns
    -------
    HVSRData
        Updated HVSRData object specified in hvsr_data with hvsr_data['stream'] attribute containing additional components (EHR-***),
        with *** being zero-padded (3 digits) azimuth angle in degrees.
    """
    # Get intput paramaters
    orig_args = locals().copy()
    start_time = datetime.datetime.now()

    # Update with processing parameters specified previously in input_params, if applicable
    if 'processing_parameters' in hvsr_data.keys():
        if 'calculate_azimuth' in hvsr_data['processing_parameters'].keys():
            update_msg = []
            for k, v in hvsr_data['processing_parameters']['calculate_azimuth'].items():
                defaultVDict = dict(zip(inspect.getfullargspec(calculate_azimuth).args[1:], 
                                        inspect.getfullargspec(calculate_azimuth).defaults))
                # Manual input to function overrides the imported parameter values
                if (not isinstance(v, (HVSRData, HVSRBatch))) and (k in orig_args.keys()) and (orig_args[k]==defaultVDict[k]):
                    update_msg.append(f'\t\t{k} = {v} (previously {orig_args[k]})')
                    orig_args[k] = v
                                     
    azimuth_angle = orig_args['azimuth_angle']
    azimuth_unit = orig_args['azimuth_unit']
    show_az_plot = orig_args['show_az_plot']
    verbose = orig_args['verbose']

    if (verbose and isinstance(hvsr_data, HVSRBatch)) or (verbose and not hvsr_data['batch']):
        if isinstance(hvsr_data, HVSRData) and hvsr_data['batch']:
            pass
        else:
            print('\nGenerating azimuthal data (calculate_azimuth())')
            print('\tUsing the following parameters:')
            for key, value in orig_args.items():
                if key == 'hvsr_data':
                    pass
                else:
                    print('\t  {}={}'.format(key, value))

            if 'processing_parameters' in hvsr_data.keys() and 'calculate_azimuth' in hvsr_data['processing_parameters'].keys():
                if update_msg != []:
                    print()
                    update_msg.insert(0, '\tThe following parameters were updated using the processing_parameters attribute:')
                    for msg_line in update_msg:
                        print(msg_line)
                    print()

    if isinstance(hvsr_data, HVSRBatch):
        # If running batch, we'll loop through each site
        hvsr_out = {}
        for site_name in hvsr_data.keys():
            args = orig_args.copy() #Make a copy so we don't accidentally overwrite
            args['hvsr_data'] = hvsr_data[site_name] #Get what would normally be the "hvsr_data" variable for each site
            if hvsr_data[site_name]['processing_status']['overall_status']:
                try:
                   hvsr_out[site_name] = __azimuth_batch(**args) #Call another function, that lets us run this function again
                except Exception as e:
                    hvsr_out[site_name]['processing_status']['calculate_azimuths_status'] = False
                    hvsr_out[site_name]['processing_status']['overall_status'] = False
                    if verbose:
                        print(e)
            else:
                hvsr_data[site_name]['processing_status']['calculate_azimuths_status'] = False
                hvsr_data[site_name]['processing_status']['overall_status'] = False
                hvsr_out = hvsr_data

        output = HVSRBatch(hvsr_out, df_as_read=hvsr_data.input_df)
        return output
    elif isinstance(hvsr_data, (HVSRData, dict, obspy.Stream)):

        degList = ['degrees', 'deg', 'd', '°']
        radList = ['radians', 'rad', 'r']
        if azimuth_unit.lower() in degList:
            az_angle_rad = np.deg2rad(azimuth_angle)
            az_angle_deg = azimuth_angle
        elif azimuth_unit.lower() in radList:
            az_angle_rad = azimuth_angle
            az_angle_deg = np.rad2deg(azimuth_angle)
        else:
            warnings.warn(f"azimuth_unit={azimuth_unit} not supported. Try 'degrees' or 'radians'. No azimuthal analysis run.")
            return hvsr_data

        # Limit to 1-180 (and "right" half of compass) (will be reflected on other half if applicable to save computation time)
        conversion_message = ''
        will_convert = False
        if az_angle_deg < 0:
            will_convert = True
            conversion_message = conversion_message + 'converted to a positive value'
            if az_angle_deg < -180:
                conversion_message = conversion_message + ' between 0 and 180 degrees'

        if az_angle_deg > 180:
            will_convert = True
            conversion_message = conversion_message + ' converted to a value between 0 and 180 degrees'

        if will_convert:
            conversion_message = f"\tThe azimuth angle specified will be{conversion_message}"

        if verbose:
            print(conversion_message, end=f': {az_angle_deg}')
        # Convert angle to 0-180
        az_angle_deg = az_angle_deg - (180 * (az_angle_deg // 180))
        az_angle_rad = az_angle_rad = np.deg2rad(azimuth_angle)

        if verbose:
            print(f' degrees --> {az_angle_deg} degrees.')

        multAzList = ['multiple azimuths', 'multiple', 'multi', 'mult', 'm']
        singleAzList = ['single azimuth', 'single', 'sing', 's']
        if azimuth_type.lower() in multAzList:
            azimuth_list = list(np.arange(0, np.pi, az_angle_rad))
            azimuth_list_deg = list(np.arange(0, 180, az_angle_deg))
        elif azimuth_type.lower() in singleAzList:
            azimuth_list = [az_angle_rad]
            azimuth_list_deg = [az_angle_deg]
        else:
            warnings.warn(f"azimuth_type={azimuth_type} not supported. Try 'multiple' or 'single'. No azimuthal analysis run.")
            return hvsr_data

        if isinstance(hvsr_data, (HVSRData, dict)):
            zComp = hvsr_data['stream'].select(component='Z').merge()
            eComp = hvsr_data['stream'].select(component='E').merge()
            nComp = hvsr_data['stream'].select(component='N').merge()
        elif isinstance(hvsr_data, obspy.Stream):
            zComp = hvsr_data.select(component='Z').merge()
            eComp = hvsr_data.select(component='E').merge()
            nComp = hvsr_data.select(component='N').merge()          

        # Reset stats for original data too
        zComp[0].stats['azimuth_deg'] = 0
        eComp[0].stats['azimuth_deg'] = 90
        nComp[0].stats['azimuth_deg'] = 0

        zComp[0].stats['azimuth_rad'] = 0
        eComp[0].stats['azimuth_rad'] = np.pi/2
        nComp[0].stats['azimuth_rad'] = 0

        zComp[0].stats['location'] = '000'
        eComp[0].stats['location'] = '090'
        nComp[0].stats['location'] = '000'

        statsDict = {}
        for key, value in eComp[0].stats.items():
            statsDict[key] = value

        for i, az_rad in enumerate(azimuth_list):
            az_deg = azimuth_list_deg[i]
            statsDict['location'] = f"{str(round(az_deg,0)).zfill(3)}" #Change location name
            statsDict['channel'] = f"EHR"#-{str(round(az_deg,0)).zfill(3)}" #Change channel name
            statsDict['azimuth_deg'] = az_deg
            statsDict['azimuth_rad'] = az_rad

            hasMask = [False, False]
            if np.ma.is_masked(nComp[0].data):
                nData = nComp[0].data.data
                nMask = nComp[0].data.mask
                hasMask[0] = True
            else:
                nData = nComp[0].data
                nMask = [True] * len(nData)

            if np.ma.is_masked(eComp[0].data):
                eData = eComp[0].data.data
                eMask = eComp[0].data.mask
                hasMask[1] = True
            else:
                eData = eComp[0].data
                eMask = [True] * len(eData)

            # From hvsrpy: horizontal = self.ns._amp * math.cos(az_rad) + self.ew._amp*math.sin(az_rad)
            if True in hasMask:
                radial_comp_data = np.ma.array(np.add(nData * np.cos(az_rad), eData * np.sin(az_angle_rad)), mask=list(map(operator.and_, nMask, eMask)))
            else:
                radial_comp_data = np.add(nData * np.cos(az_rad), eData * np.sin(az_rad))

            radial_trace = obspy.Trace(data=radial_comp_data, header=statsDict)
            hvsr_data['stream'].append(radial_trace)
    
    # Verbose printing
    if verbose and not isinstance(hvsr_data, HVSRBatch):
        dataINStr = hvsr_data.stream.__str__().split('\n')
        for line in dataINStr:
            print('\t\t', line)
    
    if show_az_plot:
        hvsr_data['Azimuth_Fig'] = plot_azimuth(hvsr_data=hvsr_data, **plot_azimuth_kwargs)

    hvsr_data['processing_status']['calculate_azimuths_status'] = True
    hvsr_data = sprit_utils._check_processing_status(hvsr_data, start_time=start_time, func_name=inspect.stack()[0][3], verbose=verbose)

    return hvsr_data


# Quality checks, stability tests, clarity tests
# def check_peaks(hvsr, x, y, index_list, peak, peakm, peakp, hvsr_peaks, stdf, hvsr_log_std, rank, hvsr_band=[0.1, 50], do_rank=False):
def check_peaks(hvsr_data, hvsr_band=DEFAULT_BAND, peak_selection='max', peak_freq_range=DEFAULT_BAND, azimuth='HV', verbose=False):
    """Function to run tests on HVSR peaks to find best one and see if it passes SESAME quality checks

        Parameters
        ----------
        hvsr_data : dict
            Dictionary containing all the calculated information about the HVSR data (i.e., hvsr_out returned from process_hvsr)
        hvsr_band : tuple or list, default=[0.1, 50]
            2-item tuple or list with lower and upper limit of frequencies to analyze
        peak_selection : str or numeric, default='max'
            How to select the "best" peak used in the analysis. For peak_selection="max" (default value), the highest peak within peak_freq_range is used.
            For peak_selection='scored', an algorithm is used to select the peak based in part on which peak passes the most SESAME criteria.
            If a numeric value is used (e.g., int or float), this should be a frequency value to manually select as the peak of interest.
        peak_freq_range : tuple or list, default=[0.1, 50];
            The frequency range within which to check for peaks. If there is an HVSR curve with multiple peaks, this allows the full range of data to be processed while limiting peak picks to likely range.
        verbose : bool, default=False
            Whether to print results and inputs to terminal.
        
        Returns
        -------
        hvsr_data   : HVSRData or HVSRBatch object
            Object containing previous input data, plus information about peak tests
    """
    orig_args = locals().copy() # Get the initial arguments
    
    # Update with processing parameters specified previously in input_params, if applicable
    if 'processing_parameters' in hvsr_data.keys():
        if 'check_peaks' in hvsr_data['processing_parameters'].keys():
            update_msg = []
            for k, v in hvsr_data['processing_parameters']['check_peaks'].items():
                defaultVDict = dict(zip(inspect.getfullargspec(check_peaks).args[1:], 
                                        inspect.getfullargspec(check_peaks).defaults))
                # Manual input to function overrides the imported parameter values
                if (not isinstance(v, (HVSRData, HVSRBatch))) and (k in orig_args.keys()) and (orig_args[k]==defaultVDict[k]):
                    update_msg.append(f'\t\t{k} = {v} (previously {orig_args[k]})')
                    orig_args[k] = v
                    
    hvsr_band = orig_args['hvsr_band']
    peak_selection = orig_args['peak_selection']
    peak_freq_range = orig_args['peak_freq_range']
    verbose = orig_args['verbose']

    #if (verbose and 'input_params' not in hvsr_data.keys()) or (verbose and not hvsr_data['batch']):
    #    if isinstance(hvsr_data, HVSRData) and hvsr_data['batch']:
    #        pass
    #    else:
    if verbose:
        print('\nChecking peaks in the H/V Curve (check_peaks())')
        print('\tUsing the following parameters:')
        for key, value in orig_args.items():
            if key == 'hvsr_data':
                pass
            else:
                print('\t  {}={}'.format(key, value))
        print()

        if 'processing_parameters' in hvsr_data.keys() and 'check_peaks' in hvsr_data['processing_parameters'].keys():
            if update_msg != []:
                update_msg.insert(0, '\tThe following parameters were updated using the processing_parameters attribute:')
                for msg_line in update_msg:
                    print(msg_line)
                print()

    # First, divide up for batch or not
    if isinstance(hvsr_data, HVSRBatch):
        if verbose:
            print('\t  Running in batch mode')
        #If running batch, we'll loop through each site
        for site_name in hvsr_data.keys():
            args = orig_args.copy() #Make a copy so we don't accidentally overwrite
            args['hvsr_data'] =  hvsr_data[site_name] #Get what would normally be the "params" variable for each site
            if hvsr_data[site_name]['processing_status']['overall_status']:
                try:
                    hvsr_data[site_name] = __check_peaks_batch(**args) #Call another function, that lets us run this function again
                except:
                    if verbose:
                        print(f"\t{site_name}: check_peaks() unsuccessful. Peaks not checked.")
                    else:
                        warnings.warn(f"\t{site_name}: check_peaks() unsuccessful. Peaks not checked.", RuntimeWarning)
                
        hvsr_data = HVSRBatch(hvsr_data, df_as_read=hvsr_data.input_df)
    else:
        HVColIDList = ['_'.join(col_name.split('_')[2:]) for col_name in hvsr_data['hvsr_windows_df'].columns if col_name.startswith('HV_Curves') and 'Log' not in col_name]
        HVColIDList[0] = 'HV'
        
        if hvsr_data['processing_status']['overall_status']:
            if not hvsr_band:
                hvsr_band = DEFAULT_BAND
            
            hvsr_data['hvsr_band'] = hvsr_band

            anyK = list(hvsr_data['x_freqs'].keys())[0]

            hvsr_data['PeakReport'] = {}
            hvsr_data['BestPeak'] = {}
            for i, col_id in enumerate(HVColIDList):
                x = hvsr_data['x_freqs'][anyK]  # Consistent for all curves
                if col_id == 'HV':
                    y = hvsr_data['hvsr_curve']  # Calculated based on "Use" column            
                else:
                    y = hvsr_data['hvsr_az'][col_id]
                
                scorelist = ['score', 'scored', 'best', 's']
                maxlist = ['maximum', 'max', 'highest', 'm']
                # Convert peak_selection to numeric, get index of nearest value as list item for __init_peaks()
                try:
                    peak_val = float(peak_selection)
                    index_list = [np.argmin(np.abs(x - peak_val))]
                except Exception as e:
                    # If score method is being used, get index list for __init_peaks()
                    if peak_selection in scorelist:
                        index_list = hvsr_data['hvsr_peak_indices'][col_id] #Calculated based on hvsr_curve
                    else:# str(peak_selection).lower() in maxlist:
                        #Get max index as item in list for __init_peaks()
                        startInd = np.argmin(np.abs(x - peak_freq_range[0]))
                        endInd = np.argmin(np.abs(x - peak_freq_range[1]))
                        if startInd > endInd:
                            holder = startInd
                            startInd = endInd
                            endInd = holder
                        subArrayMax = np.argmax(y[startInd:endInd])

                        # If max val is in subarray, this will be the same as the max of curve
                        # Otherwise, it will be the index of the value that is max within peak_freq_range
                        index_list = [subArrayMax+startInd]
                
                hvsrp = hvsr_data['hvsrp'][col_id]  # Calculated based on "Use" column
                hvsrm = hvsr_data['hvsrm'][col_id]  # Calculated based on "Use" column
                
                hvsrPeaks = hvsr_data['hvsr_windows_df'][hvsr_data['hvsr_windows_df']['Use']]['CurvesPeakIndices_'+col_id]
                
                hvsr_log_std = hvsr_data['hvsr_log_std'][col_id]
                peak_freq_range = hvsr_data['peak_freq_range']

                # Do for hvsr
                peak = __init_peaks(x, y, index_list, hvsr_band, peak_freq_range, _min_peak_amp=0.5)

                peak = __check_curve_reliability(hvsr_data, peak, col_id)
                peak = __check_clarity(x, y, peak, do_rank=True)

                # Do for hvsrp
                # Find  the relative extrema of hvsrp (hvsr + 1 standard deviation)
                if not np.isnan(np.sum(hvsrp)):
                    index_p = __find_peaks(hvsrp)
                else:
                    index_p = list()

                peakp = __init_peaks(x, hvsrp, index_p, hvsr_band, peak_freq_range, _min_peak_amp=1)
                peakp = __check_clarity(x, hvsrp, peakp, do_rank=True)

                # Do for hvsrm
                # Find  the relative extrema of hvsrm (hvsr - 1 standard deviation)
                if not np.isnan(np.sum(hvsrm)):
                    index_m = __find_peaks(hvsrm)
                else:
                    index_m = list()

                peakm = __init_peaks(x, hvsrm, index_m, hvsr_band, peak_freq_range, _min_peak_amp=0)
                peakm = __check_clarity(x, hvsrm, peakm, do_rank=True)

                # Get standard deviation of time peaks
                stdf = __get_stdf(x, index_list, hvsrPeaks)
                
                peak = __check_freq_stability(peak, peakm, peakp)
                peak = __check_stability(stdf, peak, hvsr_log_std, rank=True)

                hvsr_data['PeakReport'][col_id] = peak

                #Iterate through peaks and 
                #   Get the BestPeak based on the peak score
                #   Calculate whether each peak passes enough tests
                curveTests = ['WinLen','SigCycles', 'LowCurveStD']
                peakTests = ['ProminenceLow', 'ProminenceHi', 'AmpClarity', 'FreqStability', 'LowStDev_Freq', 'LowStDev_Amp']
                bestPeakScore = 0

                for p in hvsr_data['PeakReport'][col_id]:
                    # Get BestPeak
                    if p['Score'] > bestPeakScore:
                        bestPeakScore = p['Score']
                        bestPeak = p

                    # Calculate if peak passes criteria
                    cTestsPass = 0
                    pTestsPass = 0
                    for testName in p['PassList'].keys():
                        if testName in curveTests:
                            if p['PassList'][testName]:
                                cTestsPass += 1
                        elif testName in peakTests:
                            if p['PassList'][testName]:
                                pTestsPass += 1

                    if cTestsPass == 3 and pTestsPass >= 5:
                        p['PeakPasses'] = True
                    else:
                        p['PeakPasses'] = False
                        
                # Designate BestPeak in output dict
                if len(hvsr_data['PeakReport'][col_id]) == 0:
                    bestPeak = {}
                    print(f"No Best Peak identified for {hvsr_data['site']} (azimuth {col_id})")

                hvsr_data['BestPeak'][col_id] = bestPeak
        else:
            for i, col_id in enumerate(HVColIDList):
                if hasattr(hvsr_data, 'BestPeak'):
                    hvsr_data['BestPeak'][col_id] = {}
                else:
                    print(f"Processing Errors: No Best Peak identified for {hvsr_data['site']} (azimuth {col_id})")
            try:
                hvsr_data.plot()
            except:
                pass

        hvsr_data['processing_parameters']['check_peaks'] = {}
        exclude_params_list = ['hvsr_data']
        for key, value in orig_args.items():
            if key not in exclude_params_list:  
                hvsr_data['processing_parameters']['check_peaks'][key] = value
    return hvsr_data


# Function to export data stream to mseed (by default) or other format supported by obspy.write()
def export_data(hvsr_data, data_export_path, data_export_format='mseed', starttime=None, endtime=None, tzone=None, export_edited_stream=False, 
                site=None, project=None, verbose=False, **kwargs):
    """Export data stream to file. This uses the obspy.Stream.write() method on the hvsr_data['stream'] object,
    but the stream can first be trimmed using starttime, endtime, and tzone.

    Parameters
    ----------
    hvsr_data : HVSRData, HVSRBatch, obspy.Stream, obspy.Trace
        Input stream or HVSR object
    data_export_path : pathlike-object
        Filepath at which to format data. If directory (recommended), filename will be generated automatically.
    data_export_format : str, optional
        Format of data, should be file format supported by obspy.write(), by default 'mseed'
    starttime : str, UTCDateTime, or datetime.datetime, optional
        Starttime of stream, if trimming is desired, by default None
    endtime : str, UTCDateTime, or datetime.datetime, optional
        Endtime of stream, if trimming is desired, by default None
    tzone : str, zoneinfo.Zoneinfo, optional
        String readable by zoneinfo.Zoneinfo() or Zoneinfo object, by default None
    export_edited_stream : bool, optional
        Whether to export the raw stream ('stream' property; if False) or edited stream ('stream_edited' property; if True) in HVSRData object, by default False.
    site : str, optional
        Site name, to be used in filename generation, by default None
    project : str, optional
        Project or county name, to be used in filename generation, by default None
    verbose : bool, optional
        Whether to print information to terminal, by default False

    Returns
    -------
    obspy.Stream
        Stream object exported

    Raises
    ------
    TypeError
        hvsr_data must be of type HVSRData, HVSRBatch, obspy.Stream, or obspy.Trace
    """
    
    # Extract stream for export
    if isinstance(hvsr_data, HVSRBatch):
        for site in hvsr_data:
            export_data(hvsr_data[site], data_export_path=data_export_path, data_export_format=data_export_format,
                        starttime=starttime, endtime=endtime, verbose=verbose, **kwargs)
        return
    elif isinstance(hvsr_data, (obspy.Stream, obspy.Trace)):
        if isinstance(hvsr_data, obspy.Stream):
            outputStream = hvsr_data.copy()
        else:
            outputStream = obspy.Stream([hvsr_data])
    else:
        # Assume data is in hvsr_data
        if not isinstance(hvsr_data, HVSRData):
            raise TypeError(f"The sprit.export_data() parameter hvsr_data must be of type HVSRData, HVSRBatch, obspy.Stream, or obspy.Trace, not {type(hvsr_data)}")

        if export_edited_stream and hasattr(hvsr_data, 'stream_edited'):
            outputStream = hvsr_data['stream_edited'].copy()
        else:
            outputStream = hvsr_data['stream'].copy()
        
    # Get starttime in obspy.UTCDateTime format
    if starttime is not None:
        if type(starttime) == str:
            sTimeDT = sprit_utils._format_time(starttime, tzone=tzone)
            acqDate = outputStream[0].stats.starttime.date
            sTimeDT.replace(year=acqDate.year, month=acqDate.month, day=acqDate.day)
            sTimeUTC = obspy.UTCDateTime(sTimeDT)
        elif isinstance(starttime, datetime.datetime):
            if tzone is not None:
                starttime = starttime.replace(tzinfo=tzone)
            sTimeUTC = obspy.UTCDateTime(starttime.astimezone(datetime.timezone.utc))
        else:
            sTimeUTC = obspy.UTCDateTime(starttime)
    else:
        sTimeUTC = outputStream[0].stats.starttime
    
    # Get endtime in obspy.UTCDateTime format
    if endtime is not None:
        if type(endtime) == str:
            eTimeDT = sprit_utils._format_time(endtime, tzone=tzone)
            acqDate = outputStream[-1].stats.endtime.date
            eTimeDT.replace(year=acqDate.year, month=acqDate.month, day=acqDate.day)
            eTimeUTC = obspy.UTCDateTime(eTimeDT)
        elif isinstance(endtime, datetime.datetime):
            if tzone is not None:
                endtime = endtime.replace(tzinfo=tzone)
            eTimeUTC = obspy.UTCDateTime(endtime.astimezone(datetime.timezone.utc))
        else:
            eTimeUTC = obspy.UTCDateTime(endtime)    
    else:
        eTimeUTC = outputStream[-1].stats.endtime

    # Build filepath
    
    siteName = site
    if site is None:
        siteName = "HVSRSite"
    
    projectName = project
    if project is None:
        projectName = ""
    if projectName != "" and len(projectName)>0 and projectName[-1] != '-':
        projectName += "-"

    sDateStr = outputStream[0].stats.starttime.strftime("%Y%m%d")
    sTimeStr = outputStream[0].stats.starttime.strftime("%H%M")
    staStr = outputStream[0].stats.station
    
    deFormat = str(data_export_format).upper()
    if data_export_format[0] == '.':
        deFormat = deFormat[1:]
    
    dePath = pathlib.Path(data_export_path)    
    autoFname = f"{siteName}_Stream_{projectName}{sDateStr}-{sTimeStr}-{staStr}_{datetime.date.today()}.{deFormat}"
    if dePath.is_dir():
        if not dePath.exists():
            dePath.mkdir(parents=True)
        outfPath = dePath.joinpath(autoFname)
    elif dePath.is_file():
        outfPath = dePath
    
    # Trim stream as needed
    if starttime is None and endtime is None:
        pass
    else:
        isMasked = False
        doTrim = False
        
        for tr in outputStream:
            if isinstance(tr.data, np.ma.masked_array):
                isMasked = True
            if sTimeUTC > tr.stats.endtime or eTimeUTC < tr.stats.starttime:
                doTrim = True

        if isMasked:
            outputStream = outputStream.split()
        
        if doTrim:
            if verbose:
                print(f"\t Trimming data to {sTimeUTC} and {eTimeUTC}\n\t\t Stream starttime: {outputStream[0].stats.starttime}\n\t\t Stream endtime: {outputStream[0].stats.endtime}")
            outputStream.trim(starttime=sTimeUTC, endtime=eTimeUTC)
        
    outputStream.merge(method=1)

    # Take care of masked arrays for writing purposes
    if 'fill_value' in kwargs.keys():
        for tr in outputStream:
            if isinstance(tr.data, np.ma.masked_array):
                tr.data = tr.data.filled(kwargs['fill_value'])
    else:
        outputStream = outputStream.split()
    
    outputStream.write(filename=outfPath.as_posix())
    
    if verbose:
        print('Stream has been written to ' + outfPath.as_posix())
    return outputStream
    

# Function to export data to .hvsr file (pickled)
def export_hvsr(hvsr_data, hvsr_export_path=None, ext='hvsr', export_type='gzip',
                export_plots=False,
                verbose=False):
    """Export data into pickle format that can be read back in using import_data().
       Intended so data does not need to be processed each time it needs to be used. 
       By default, first, export_hvsr serializes the HVSRData object(s) using pickle.dumps(). 
       Then, to save space, it writes that to a gzip file.
       Default extension is .hvsr no matter the format, though this can be set with `ext` parameter.

    Parameters
    ----------
    hvsr_data : HVSRData or HVSRBatch
        Data to be exported
    hvsr_export_path : str or filepath object, default = None
        String or filepath object to be read by pathlib.Path() and/or a with open(hvsr_export_path, 'wb') statement. If None, defaults to input input_data directory, by default None
    ext : str, default = 'hvsr'
        Filepath extension to use for data file, by default 'hvsr'. 
        This will be the extension no matter the export_type
    export_type : str, default = 'gzip'
        Export type to use. If `export_type` is 'pickle', will just save to disk using pickle.dump.
        Otherwise, saves a pickle-serialized object to a gzip file (with a .hvsr extension in both cases, by default).
    verbose : bool, default=False
        Whether to print information about export. A confirmation message is printed no matter what.
    """
    def _hvsr_export(_hvsr_data=hvsr_data, _export_path=hvsr_export_path, _ext=ext):
        
        fname = f"{_hvsr_data['site']}_HVSRData_{_hvsr_data['hvsr_id']}_{datetime.date.today()}_pickled.{ext}"
        if _export_path is None or _export_path is True:
            _export_path = _hvsr_data['input_data']
            _export_path = pathlib.Path(_export_path).with_name(fname)
        else:
            _export_path = pathlib.Path(_export_path)
            if _export_path.is_dir():
                _export_path = _export_path.joinpath(fname)    

        _export_path = str(_export_path)

        if export_type == 'pickle':
            with open(_export_path, 'wb') as f:
                pickle.dump(_hvsr_data, f)
        else:
            with gzip.open(_export_path, 'wb') as f:
                f.write(pickle.dumps(_hvsr_data))

        if verbose:
            print('EXPORT COMPLETE')
        print(f"Processed data exported as pickled data to: {_export_path} [~{round(float(pathlib.Path(_export_path).stat().st_size)/2**20,1)} Mb]")    

    hvData = hvsr_data
    #hvData = copy.deepcopy(hvsr_data)
    #if export_plots is False:
    #    for pk in PLOT_KEYS:
    #        if hasattr(hvData, pk):
    #            del hvData[pk]

    if isinstance(hvData, HVSRBatch):
        for sitename in hvData.keys():
            _hvsr_export(_hvsr_data=hvData[sitename], _export_path=hvsr_export_path, _ext=ext)
    elif isinstance(hvData, HVSRData):
        _hvsr_export(_hvsr_data=hvData, _export_path=hvsr_export_path, _ext=ext)
    else:
        print("Error in data export. Data must be either of type sprit.HVSRData or sprit.HVSRBatch")         
    
    return


# Function to export reports to disk in various formats
def export_report(hvsr_results, report_export_path=None, report_export_format=['pdf'], azimuth='HV', csv_handling='rename', show_report=True, verbose=False):
    """Function to export reports to disk. Exportable formats for report_export_format include: 
        * 'table': saves a pandas DataFrame as a csv)
        * 'plot': saves the matplotlib or plotly plot figure (depending on what is designated via plot_engine) as an image (png by default)
        * 'print': saves the print report as a .txt file
        * 'html': saves the html report as a .html file
        * 'pdf': saves the pdf report as a .pdf file

    Parameters
    ----------
    hvsr_results : HVSRData object
        HVSRData object containing the HVSR data
    report_export_path : path-like object, optional
        The path to where the report should be exported. 
        If this is None (default), this is written to the home directory.
        If this is a True, uses the same directory as the input data, but generates a filename.
        If this is a directory, generates a filename. 
        If filename is specified and the extension does not match the report type, the extension is adjusted.
        Otherwise, this is the output file or , by default None
    csv_handling : {'rename', 'append', 'overwrite', 'keep'}, optional
        If table is the report type, this can prevent overwriting data, by default 'rename'.
        * "rename" (or "keep"): renames the new file to prevent overwrite, appends a digit to the end of filename
        * "append": appends the new data to the existing file
        * "overwrite": overwrites the existing file
    report_export_format : str or list, optional
        The format (or a list of formats) to export the report, by default ['pdf'].
    show_report : bool, optional
        Whether to show the designated reports that were chosen for export, by default True
    verbose : bool, optional
        Whether to print progress and other information to terminal, by default False

    Returns
    -------
    HVSRData
        An HVSRData object that is the same as hvsr_results, but with any additionally generated reports.
    """

    if type(report_export_format) is str:
        report_export_format = [report_export_format]
    
    for ref in report_export_format:

        if report_export_path is None:
            print('The export_report(report_export_path) parameter was not specified.')
            print(f'The report will be saved the home directory: {pathlib.Path.home()}')

        if ref == 'table':
            ext = '.csv'
        elif ref == 'plot':
            ext = '.png'
        elif ref == 'print':
            ext = '.txt'
        elif ref == 'html':
            ext = '.html'
        else:
            ref == 'pdf'
            ext = '.pdf'
            
        sitename = hvsr_results['input_params']['site']
        fname = f"{sitename}_REPORT_{hvsr_results['hvsr_id']}_{datetime.date.today()}{ext}"
        fname = fname.replace(':', '')

        # Initialize output as file in home directory (if not updated)
        outFile = pathlib.Path().home().joinpath(fname)
        if report_export_path is True or report_export_path is None:
            # Check so we don't write in sample directory
            if pathlib.Path(hvsr_results['input_params']['input_data']) in sampleFileKeyMap.values():
                if pathlib.Path(os.getcwd()) in sampleFileKeyMap.values(): #Just in case current working directory is also sample directory
                    inFile = pathlib.Path.home() #Use the path to user's home if all else fails
                else:
                    inFile = pathlib.Path(os.getcwd())
            else:
                inFile = pathlib.Path(hvsr_results['input_params']['input_data'])
                            
            if inFile.is_dir():
                outFile = inFile.joinpath(fname)
            else:
                outFile = inFile.with_name(fname)
        else:
            if report_export_path is False:
                pass
            elif pathlib.Path(report_export_path).is_dir():
                outFile = pathlib.Path(report_export_path).joinpath(fname)
            else:
                outFile = pathlib.Path(report_export_path)

        if ref == 'table':
            if not hasattr(hvsr_results, 'Table_Report'):
                hvsr_results = _generate_table_report(hvsr_results, azimuth=azimuth, show_table_report=show_report, verbose=verbose)
            reportDF = hvsr_results['Table_Report']

            # Check if file already exists, and handle as specified in csv_handling
            if outFile.exists():
                existFile = pd.read_csv(outFile)

                 

                if csv_handling.lower() == 'append':
                    # Append report to existing report as new row
                    reportDF = pd.concat([existFile, reportDF], ignore_index=True, join='inner')
                elif csv_handling.lower() == 'overwrite':
                    # Overwrite existing report file
                    pass
                else:  # csv_handling.lower() in ['keep', 'rename', or other]:
                    # Rename new report so as not to modify existing report (default handling)
                    if outFile.stem[-3] == '_' and outFile.stem[-2:].isdigit():
                        fileDigit = int(outFile.stem[-2:]) + 1
                    else:
                        fileDigit = 1
                    fileDigit = str(fileDigit).zfill(2)
                    outFile = outFile.with_stem(outFile.stem + '_' + fileDigit)

            # Export to csv using pandas to_csv method
            try:
                print(f'\nSaving table report to: {outFile}')
                reportDF.to_csv(outFile, index_label='ID')
            except:
                warnings.warn("Table report not exported. \n\tDataframe to be exported as csv has been saved in hvsr_results['BestPeak']['Report']['Table_Report]", category=RuntimeWarning)
 
            if show_report or verbose:
                print('\nTable Report:\n')
                maxColWidth = 13
                print('  ', end='')
                for col in reportDF.columns:
                    if len(str(col)) > maxColWidth:
                        colStr = str(col)[:maxColWidth-3]+'...'
                    else:
                        colStr = str(col)
                    print(colStr.ljust(maxColWidth), end='  ')
                print() #new line
                for c in range(len(reportDF.columns) * (maxColWidth+2)):
                    if c % (maxColWidth+2) == 0:
                        print('|', end='')
                    else:
                        print('-', end='')
                print('|') #new line
                print('  ', end='') #Small indent at start                    
                for row in reportDF.iterrows():
                    for col in row[1]:
                        if len(str(col)) > maxColWidth:
                            colStr = str(col)[:maxColWidth-3]+'...'
                        else:
                            colStr = str(col)
                        print(colStr.ljust(maxColWidth), end='  ')
                    print()
        elif ref == 'plot':
            if not hasattr(hvsr_results, 'Plot_Report'):
                fig = plot_hvsr(hvsr_results, return_fig=True)
            hvsr_results['BestPeak'][azimuth]['Report']['Plot_Report'] = hvsr_results['Plot_Report'] = fig

            if verbose:
                print(f'\nSaving plot to: {outFile}')
            plt.scf = fig
            plt.savefig(outFile)
        elif ref == 'print':
            if not hasattr(hvsr_results, "Print_Report") or hvsr_results['Print_Report'] is None:
                hvsr_results = _generate_print_report(hvsr_results, azimuth=azimuth, show_print_report=show_report, verbose=verbose)            
            with open(outFile, 'w') as outF:
                outF.write(hvsr_results['Print_Report'])
                # Could write more details in the future
                if show_report or verbose:
                    print(hvsr_results['Print_Report'])
        elif ref == "html":
            if not hasattr(hvsr_results, "HTML_Report") or hvsr_results['HTML_Report'] is None:
                hvsr_results = _generate_html_report(hvsr_results)
            with open(outFile, 'w') as outF:
                outF.write(hvsr_results['HTML_Report'])
        elif ref == "pdf":
            hvsr_results = _generate_pdf_report(hvsr_results, pdf_report_filepath=report_export_path, show_pdf_report=show_report, verbose=verbose)
        
    return hvsr_results


# **WORKING ON THIS**
# Save default instrument and processing settings to json file(s)
def export_settings(hvsr_data, export_settings_path='default', export_settings_type='all', include_location=False, verbose=True):
    """Save processing settings to json file.

    Parameters
    ----------
    export_settings_path : str, default="default"
        Where to save the json file(s) containing the settings, by default 'default'. 
        If "default," will save to sprit package resources. Otherwise, set a filepath location you would like for it to be saved to.
        If 'all' is selected, a directory should be supplied. 
        Otherwise, it will save in the directory of the provided file, if it exists. Otherwise, defaults to the home directory.
    export_settings_type : str, {'all', 'instrument', 'processing'}
        What kind of settings to save. 
        If 'all', saves all possible types in their respective json files.
        If 'instrument', save the instrument settings to their respective file.
        If 'processing', saves the processing settings to their respective file. By default 'all'
    include_location : bool, default=False, input CRS
        Whether to include the location parametersin the exported settings document.This includes xcoord, ycoord, elevation, elev_unit, and input_crs
    verbose : bool, default=True
        Whether to print outputs and information to the terminal

    """
    fnameDict = {}
    fnameDict['instrument'] = "instrument_settings.json"
    fnameDict['processing'] = "processing_settings.json"

    if export_settings_path == 'default' or export_settings_path is True:
        settingsPath = RESOURCE_DIR.joinpath('settings')
    else:
        export_settings_path = pathlib.Path(export_settings_path)
        if not export_settings_path.exists():
            if not export_settings_path.parent.exists():
                print(f'The provided value for export_settings_path ({export_settings_path}) does not exist. Saving settings to the home directory: {pathlib.Path.home()}')
                settingsPath = pathlib.Path.home()
            else:
                settingsPath = export_settings_path.parent
        
        if export_settings_path.is_dir():
            settingsPath = export_settings_path
        elif export_settings_path.is_file():
            settingsPath = export_settings_path.parent
            fnameDict['instrument'] = export_settings_path.name+"_instrumentSettings.json"
            fnameDict['processing'] = export_settings_path.name+"_processingSettings.json"

    #Get final filepaths        
    instSetFPath = settingsPath.joinpath(fnameDict['instrument'])
    procSetFPath = settingsPath.joinpath(fnameDict['processing'])

    #Get settings values
    instKeys = ["instrument", "net", "sta", "loc", "cha", "depth", "metadata", "hvsr_band"]
    inst_location_keys = ['xcoord', 'ycoord', 'elevation', 'elev_unit', 'input_crs']
    procFuncs = [fetch_data, remove_noise, generate_psds, process_hvsr, check_peaks, get_report]

    instrument_settings_dict = {}
    processing_settings_dict = {}

    for k in instKeys:
        if isinstance(hvsr_data[k], pathlib.PurePath):
            #For those that are paths and cannot be serialized
            instrument_settings_dict[k] = hvsr_data[k].as_posix()
        else:
            instrument_settings_dict[k] = hvsr_data[k]

    if include_location:
        for k in inst_location_keys:
            if isinstance(hvsr_data[k], pathlib.PurePath):
                #For those that are paths and cannot be serialized
                instrument_settings_dict[k] = hvsr_data[k].as_posix()
            else:
                instrument_settings_dict[k] = hvsr_data[k]

    
    for func in procFuncs:
        funcName = func.__name__
        processing_settings_dict[funcName] = {}
        for arg in hvsr_data['processing_parameters'][funcName]:
            if isinstance(hvsr_data['processing_parameters'][funcName][arg], (HVSRBatch, HVSRData)):
                pass
            else:
                processing_settings_dict[funcName][arg] = hvsr_data['processing_parameters'][funcName][arg]
    
    if verbose:
        print("Exporting Settings")
    #Save settings files
    if export_settings_type.lower()=='instrument' or export_settings_type.lower()=='all':
        try:
            with open(instSetFPath.with_suffix('.inst').as_posix(), 'w') as instSetF:
                jsonString = json.dumps(instrument_settings_dict, indent=2)
                #Format output for readability
                jsonString = jsonString.replace('\n    ', ' ')
                jsonString = jsonString.replace('[ ', '[')
                jsonString = jsonString.replace('\n  ]', ']')
                #Export
                instSetF.write(jsonString)
        except:
            instSetFPath = pathlib.Path.home().joinpath(instSetFPath.name)
            with open(instSetFPath.with_suffix('.inst').as_posix(), 'w') as instSetF:
                jsonString = json.dumps(instrument_settings_dict, indent=2)
                #Format output for readability
                jsonString = jsonString.replace('\n    ', ' ')
                jsonString = jsonString.replace('[ ', '[')
                jsonString = jsonString.replace('\n  ]', ']')
                #Export
                instSetF.write(jsonString)
                            
        if verbose:
            print(f"Instrument settings exported to {instSetFPath}")
            print(f"{jsonString}")
            print()
    if export_settings_type.lower()=='processing' or export_settings_type.lower()=='all':
        try:
            with open(procSetFPath.with_suffix('.proc').as_posix(), 'w') as procSetF:
                jsonString = json.dumps(processing_settings_dict, indent=2)
                #Format output for readability
                jsonString = jsonString.replace('\n    ', ' ')
                jsonString = jsonString.replace('[ ', '[')
                jsonString = jsonString.replace('\n  ]', ']')
                jsonString = jsonString.replace('\n  },','\n\t\t},\n')
                jsonString = jsonString.replace('{ "', '\n\t\t{\n\t\t"')
                jsonString = jsonString.replace(', "', ',\n\t\t"')
                jsonString = jsonString.replace('\n  }', '\n\t\t}')
                jsonString = jsonString.replace(': {', ':\n\t\t\t{')
                
                #Export
                procSetF.write(jsonString)
        except:
            procSetFPath = pathlib.Path.home().joinpath(procSetFPath.name)
            with open(procSetFPath.with_suffix('.proc').as_posix(), 'w') as procSetF:
                jsonString = json.dumps(processing_settings_dict, indent=2)
                #Format output for readability
                jsonString = jsonString.replace('\n    ', ' ')
                jsonString = jsonString.replace('[ ', '[')
                jsonString = jsonString.replace('\n  ]', ']')
                jsonString = jsonString.replace('\n  },','\n\t\t},\n')
                jsonString = jsonString.replace('{ "', '\n\t\t{\n\t\t"')
                jsonString = jsonString.replace(', "', ',\n\t\t"')
                jsonString = jsonString.replace('\n  }', '\n\t\t}')
                jsonString = jsonString.replace(': {', ':\n\t\t\t{')
                
                #Export
                procSetF.write(jsonString)            
        if verbose:
            print(f"Processing settings exported to {procSetFPath}")
            print(f"{jsonString}")
            print()


# Reads in traces to obspy stream
def fetch_data(params, source='file', data_export_path=None, data_export_format='mseed', 
               detrend='spline', detrend_options=2, filter_type=None, filter_options={},
               update_metadata=True, 
               plot_input_stream=False, plot_engine='matplotlib', show_plot=True, 
               verbose=False, **kwargs):
    
    """Fetch ambient seismic data from a source to read into obspy stream. 
    
    Parameters
    ----------
    params  : dict
        Dictionary containing all the necessary params to get data.
            Parameters defined using input_params() function.
    source  : str, {'raw', 'dir', 'file', 'batch'}
        String indicating where/how data file was created. For example, if raw data, will need to find correct channels.
            'raw' finds raspberry shake data, from raw output copied using scp directly from Raspberry Shake, either in folder or subfolders; 
            'dir' is used if the day's 3 component files (currently Raspberry Shake supported only) are all 3 contained in a directory by themselves.
            'file' is used if the params['input_data'] specified in input_params() is the direct filepath to a single file to be read directly into an obspy stream.
            'batch' is used to read a list or specified set of seismic files. 
                Most commonly, a csv file can be read in with all the parameters. Each row in the csv is a separate file. Columns can be arranged by parameter.
    data_export_path : None or str or pathlib obj, default=None
        If None (or False), data is not trimmed in this function.
        Otherwise, this is the directory to save trimmed and exported data.
    data_export_format: str='mseed'
        If data_export_path is not None, this is the format in which to save the data
    detrend : str or bool, default='spline'
        If False, data is not detrended.
        Otherwise, this should be a string accepted by the type parameter of the obspy.core.trace.Trace.detrend method: https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.detrend.html
    detrend_options : int, default=2
        If detrend parameter is 'spline' or 'polynomial', this is passed directly to the order parameter of obspy.core.trace.Trace.detrend method.
    filter_type : None, str
        Type of filter to use on raw data.
        This should either be None or any of {'bandpass', 'bandstop', 'lowpass', 'highpass', 'lowpass_cheby_2', 'lowpass_fir', 'remez_fir'}.
        This passes `filter_type` to the `type` parameter and `**filter_options` to the `**options` parameter of the obspy.Stream filter() method.
        See here for more information: https://docs.obspy.org/packages/autogen/obspy.core.stream.Stream.filter.html
        If None, no filtering is done on the input seismic data.
    filter_options : dict
        Dictionary that will be unpacked into the `**options` parameter of the filter() method of the obspy.Stream class.
        This should fit the parameters of whichever filter type is specifed by filter_type.
        Example options for the 'bandpass' filter_type might be: `filter_options={'freqmin': 0.1, 'freqmax':50, 'df':100, 'corners':4, 'zerophase':True}`.
        See here for more information: https://docs.obspy.org/packages/autogen/obspy.core.stream.Stream.filter.html
    update_metadata : bool, default=True
        Whether to update the metadata file, used primarily with Raspberry Shake data which uses a generic inventory file.
    plot_input_stream : bool, default=False
        Whether to plot the raw input stream. This plot includes a spectrogram (Z component) and the raw (with decimation for speed) plots of each component signal.
    plot_engine : str, default='matplotlib'
        Which plotting library/engine to use for plotting the Input stream. Options are 'matplotlib', 'plotly', or 'obspy' (not case sensitive).
    verbose : bool, default=False
        Whether to print outputs and inputs to the terminal
    **kwargs
        Keywords arguments, primarily for 'batch' and 'dir' sources
        
    Returns
    -------
    params : HVSRData or HVSRBatch object
        Same as params parameter, but with an additional "stream" attribute with an obspy data stream with 3 traces: Z (vertical), N (North-south), and E (East-west)
    """
    # Get intput paramaters
    orig_args = locals().copy()
    start_time = datetime.datetime.now()
    
    # Keep track of any updates made to raw input along the way
    update_msg = []

    # Update with processing parameters specified previously in input_params, if applicable
    if 'processing_parameters' in params.keys():
        if 'fetch_data' in params['processing_parameters'].keys():
            defaultVDict = dict(zip(inspect.getfullargspec(fetch_data).args[1:], 
                        inspect.getfullargspec(fetch_data).defaults))
            defaultVDict['kwargs'] = kwargs
            for k, v in params['processing_parameters']['fetch_data'].items():
                # Manual input to function overrides the imported parameter values
                if k != 'params' and k in orig_args.keys() and orig_args[k]==defaultVDict[k]:
                    update_msg.append(f'\t\t{k} = {v} (previously {orig_args[k]})')
                    orig_args[k] = v
                    
    # Update local variables, in case of previously-specified parameters
    source = orig_args['source'].lower()
    data_export_path = orig_args['data_export_path']
    data_export_format = orig_args['data_export_format']
    detrend = orig_args['detrend']
    detrend_options = orig_args['detrend_options']
    filter_type = orig_args['filter_type']
    filter_options = orig_args['filter_options']
    update_metadata = orig_args['update_metadata']
    plot_input_stream = orig_args['plot_input_stream']
    plot_engine = orig_args['plot_engine']
    verbose = orig_args['verbose']
    kwargs = orig_args['kwargs']

    # Print inputs for verbose setting
    if verbose:
        print('\nFetching data (fetch_data())')
        for key, value in orig_args.items():
            if not isinstance(value, (HVSRData, HVSRBatch)):
                print('\t  {}={}'.format(key, value))
        print()
        
        if 'processing_parameters' in params.keys() and 'fetch_data' in params['processing_parameters'].keys():
            if update_msg != []:
                update_msg.insert(0, '\tThe following parameters were updated using the processing_parameters attribute:')
                for msg_line in update_msg:
                    print(msg_line)
                print()

    raspShakeInstNameList = ['raspberry shake', 'shake', 'raspberry', 'rs', 'rs3d', 'rasp. shake', 'raspshake']
    trominoNameList = ['tromino', 'trom','tromino blue', 'tromino blu', 'tromino 3g', 'tromino 3g+', 'tr', 't']

    # Check if data is from tromino, and adjust parameters accordingly
    if 'trc' in pathlib.Path(str(params['input_data'])).suffix:
        if verbose and hasattr(params, 'instrument') and params['instrument'].lower() not in trominoNameList:
            print(f"\t Data from tromino detected. Changing instrument from {params['instrument']} to 'Tromino'")
        if 'tromino' not in str(params['instrument']).lower():
            params['instrument'] = 'Tromino'

    # Get metadata (inventory/response information)
    params = get_metadata(params, update_metadata=update_metadata, source=source, verbose=verbose)
    inv = params['inv']
    date = params['acq_date']

    # Cleanup for gui input
    if isinstance(params['input_data'], (obspy.Stream, obspy.Trace)):
        pass
    elif '}' in str(params['input_data']): # This is how tkinter gui data comes in
        params['input_data'] = params['input_data'].as_posix().replace('{', '')
        params['input_data'] = params['input_data'].split('}')

    # Make sure input_data is pointing to an actual file
    if isinstance(params['input_data'], list):
        for i, d in enumerate(params['input_data']):
            params['input_data'][i] = sprit_utils._checkifpath(str(d).strip(), sample_list=SAMPLE_LIST)
        dPath = params['input_data']
    elif isinstance(params['input_data'], (obspy.Stream, obspy.Trace)):
        dPath = pathlib.Path() #params['input_data']
    elif isinstance(params['input_data'], HVSRData):
        dPath = pathlib.Path(params['input_data']['input_data'])
        if not isinstance(params['input_data']['stream'], (obspy.Stream, obspy.Trace)):
            try:
                for k, v in params.items():
                    if isinstance(v, (obspy.Trace, obspy.Stream)):
                        params['input_data']['stream'] = v
                    elif pathlib.Path(str(v)).exists():
                        try:
                            params['input_data']['stream'] = obspy.read(v)
                        except Exception as e:
                            pass
            except:
                raise RuntimeError(f'The params["input_data"] parameter of fetch_data() was determined to be an HVSRData object, but no data in the "stream" attribute.')
        else:
            if verbose:
                print('\tThe params["input_data"] argument is already an HVSRData obect.')
                print("\tChecking metadata then moving on.")
    else:
        dPath = sprit_utils._checkifpath(params['input_data'], sample_list=SAMPLE_LIST)

    inst = params['instrument']

    # Need to put dates and times in right formats first
    if type(date) is datetime.datetime:
        doy = date.timetuple().tm_yday
        year = date.year
    elif type(date) is datetime.date:
        date = datetime.datetime.combine(date, datetime.time(hour=0, minute=0, second=0))
        doy = date.timetuple().tm_yday
        year = date.year
    elif type(date) is tuple:
        if date[0]>366:
            raise ValueError('First item in date tuple must be day of year (0-366)', 0)
        elif date[1] > datetime.datetime.now().year:
            raise ValueError('Second item in date tuple should be year, but given item is in the future', 0)
        else:
            doy = date[0]
            year = date[1]
    elif type(date) is str:
        if '/' in date:
            dateSplit = date.split('/')
        elif '-' in date:
            dateSplit = date.split('-')
        else:
            dateSplit = date

        if int(dateSplit[0]) > 31:
            date = datetime.datetime(int(dateSplit[0]), int(dateSplit[1]), int(dateSplit[2]))
            doy = date.timetuple().tm_yday
            year = date.year
        elif int(dateSplit[0])<=12 and int(dateSplit[2]) > 31:
            warnings.warn("Preferred date format is 'yyyy-mm-dd' or 'yyyy/mm/dd'. Will attempt to parse date.")
            date = datetime.datetime(int(dateSplit[2]), int(dateSplit[0]), int(dateSplit[1]))
            doy = date.timetuple().tm_yday
            year = date.year
        else:
            warnings.warn("Preferred date format is 'yyyy-mm-dd' or 'yyyy/mm/dd'. Cannot parse date.")
    elif type(date) is int:
        doy = date
        year = datetime.datetime.today().year
    else:  
        date = datetime.datetime.now()
        doy = date.timetuple().tm_yday
        year = date.year
        warnings.warn("Did not recognize date, using year {} and day {}".format(year, doy))

    # Select which instrument we are reading from (requires different processes for each instrument)
    # Get any kwargs that are included in obspy.read
    obspyReadKwargs = {}
    for argName in inspect.getfullargspec(obspy.read)[0]:
        if argName in kwargs.keys():
            obspyReadKwargs[argName] = kwargs[argName]

    # Select how reading will be done
    if isinstance(params['input_data'], obspy.Stream):
        rawDataIN = params['input_data'].copy()
        tr = params['input_data'][0]
        params['input_data'] = '_'.join([tr.id, str(tr.stats.starttime)[:10],
                                       str(tr.stats.starttime)[11:19],
                                       str(tr.stats.endtime)[11:19]])
    elif isinstance(params['input_data'], obspy.Trace):
        rawDataIN = obspy.Stream(params['input_data'])
        tr = params['input_data']
        params['input_data'] = '_'.join([tr.id, str(tr.stats.starttime)[:10], 
                                       str(tr.stats.starttime)[11:19], 
                                       str(tr.stats.endtime)[11:19]])
    elif isinstance(params['input_data'], HVSRData):
        rawDataIN = params['input_data']['stream']
    else:
        if source=='raw':
            try:
                if inst.lower() in trominoNameList:
                    params['instrument'] = 'Tromino'
                    params['params']['instrument'] = 'Tromino'

                    trominoKwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(read_tromino_files).parameters.keys())}
                    paramDict = {k:v for k, v in params.items()}
                    trominoKwargs.update(paramDict)
                    rawDataIN = read_tromino_files(dPath, verbose=verbose, **trominoKwargs)

                else:
                    if inst.lower() not in raspShakeInstNameList:
                        print(f"Unrecognized value instrument={inst}. Defaulting to raw raspberry shake data.")
                    rawDataIN = __read_RS_file_struct(dPath, source, year, doy, inv, params, verbose=verbose)

            except Exception as e:
                raise RuntimeError(f"Data not fetched for {params['site']}. Check input parameters or the data file.\n\n{e}")
        elif source == 'stream' or isinstance(params, (obspy.Stream, obspy.Trace)):
            rawDataIN = params['input_data'].copy()
        elif source == 'dir':
            if inst.lower() in raspShakeInstNameList:
                rawDataIN = __read_RS_file_struct(dPath, source, year, doy, inv, params, verbose=verbose)
            else:
                obspyFiles = {}
                for obForm in OBSPY_FORMATS:
                    temp_file_glob = pathlib.Path(dPath.as_posix().lower()).glob('.'+obForm.lower())
                    for f in temp_file_glob:
                        currParams = params
                        currParams['input_data'] = f

                        curr_data = fetch_data(params, source='file', #all the same as input, except just reading the one file using the source='file'
                                    data_export_path=data_export_path, data_export_format=data_export_format, detrend=detrend, detrend_options=detrend_options, update_metadata=update_metadata, verbose=verbose, **kwargs)
                        curr_data.merge()
                        obspyFiles[f.stem] = curr_data  #Add path object to dict, with filepath's stem as the site name
                return HVSRBatch(obspyFiles)
        elif source == 'file' and str(params['input_data']).lower() not in SAMPLE_LIST:
            # Read the file specified by input_data
            # Automatically read tromino data
            if inst.lower() in trominoNameList or 'trc' in dPath.suffix:
                params['instrument'] = 'Tromino'
                params['params']['instrument'] = 'Tromino'

                if 'blu' in str(inst).lower():
                    params['instrument'] = 'Tromino Blue'
                    params['params']['instrument'] = 'Tromino Blue'

                if 'trc' in dPath.suffix:
                    trominoKwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(read_tromino_files).parameters.keys())}
                    paramDict = {k:v for k, v in params.items()}
                    trominoKwargs.update(paramDict)
                    if 'input_data' in trominoKwargs:
                        del trominoKwargs['input_data']
                    if 'tromino_model' not in trominoKwargs:
                        trominoKwargs['tromino_model'] = params['instrument']
                    rawDataIN = read_tromino_files(input_data=dPath, verbose=verbose, **trominoKwargs)
                else:
                    try:
                        rawDataIN = obspy.read(dPath)
                    except Exception:
                        raise ValueError(f"{dPath.suffix} is not a a filetype that can be read by SpRIT (via ObsPy)")
            else:
                if isinstance(dPath, list) or isinstance(dPath, tuple):
                    rawStreams = []
                    for datafile in dPath:
                        rawStream = obspy.read(datafile, **obspyReadKwargs)
                        rawStreams.append(rawStream) #These are actually streams, not traces
                    for i, stream in enumerate(rawStreams):
                        if i == 0:
                            rawDataIN = obspy.Stream(stream) #Just in case
                        else:
                            rawDataIN = rawDataIN + stream #This adds a stream/trace to the current stream object
                elif str(dPath)[:6].lower() == 'sample':
                    pass
                else:
                    rawDataIN = obspy.read(dPath, **obspyReadKwargs)#, starttime=obspy.core.UTCDateTime(params['starttime']), endttime=obspy.core.UTCDateTime(params['endtime']), nearest_sample =True)
                #import warnings # For some reason not being imported at the start
                #with warnings.catch_warnings():
                    #warnings.simplefilter(action='ignore', category=UserWarning)
                    #rawDataIN.attach_response(inv)
        elif source == 'batch' and str(params['input_data']).lower() not in SAMPLE_LIST:
            if verbose:
                print('\nFetching data (fetch_data())')
            batch_data_read_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(batch_data_read).parameters.keys())}
            params = batch_data_read(batch_data=params['input_data'], verbose=verbose, **batch_data_read_kwargs)
            params = HVSRBatch(params, df_as_read=params.input_df)
            return params
        elif str(params['input_data']).lower() in SAMPLE_LIST or f"sample{params['input_data'].lower()}" in SAMPLE_LIST:
            if source=='batch':
                params['input_data'] = SAMPLE_DATA_DIR.joinpath('Batch_SampleData.csv')
                params = batch_data_read(batch_data=params['input_data'], batch_type='sample', verbose=verbose)
                params = HVSRBatch(params, df_as_read=params.input_df)
                return params
            elif source=='dir':
                params['input_data'] = SAMPLE_DATA_DIR.joinpath('Batch_SampleData.csv')
                params = batch_data_read(batch_data=params['input_data'], batch_type='sample', verbose=verbose)
                params = HVSRBatch(params, df_as_read=params.input_df)
                return params
            elif source=='file':
                params['input_data'] = str(params['input_data']).lower()
                
                if params['input_data'].lower() in sampleFileKeyMap.keys():
                    if params['input_data'].lower() == 'sample':
                        params['input_data'] = sampleFileKeyMap
                        
                    params['input_data'] = sampleFileKeyMap[params['input_data'].lower()]
                else:
                    params['input_data'] = SAMPLE_DATA_DIR.joinpath('SampleHVSRSite1_AM.RAC84.00.2023.046_2023-02-15_1704-1734.MSEED')

                dPath = params['input_data']
                rawDataIN = obspy.read(dPath)#, starttime=obspy.core.UTCDateTime(params['starttime']), endttime=obspy.core.UTCDateTime(params['endtime']), nearest_sample =True)
                #import warnings
                #with warnings.catch_warnings():
                #    warnings.simplefilter(action='ignore', category=UserWarning)
                #    rawDataIN.attach_response(inv)
        else:
            # Last try if source cannot be read correctly
            try:
                rawDataIN = obspy.read(dPath)
            except:
                RuntimeError(f'source={source} not recognized, and input_data cannot be read using obspy.read()')

    if verbose:
        print('\t Data as read in initially:')
        print(f'\t  {len(rawDataIN)} trace(s) in Stream:')
        for i, trace in enumerate(rawDataIN):
            if i == 0:
                prevComponent = trace.stats.component
                print(f'\t\t{prevComponent} Component')
                
            currComponent = trace.stats.component
            if prevComponent != currComponent:
                print(f"\t\t{currComponent} Component")
            print("\t\t  ", trace)
            prevComponent = trace.stats.component
        print()
        
    # Get metadata from the data itself, if not reading raw data
    try:
        # If the data already exists (not reading in raw from RS, for example), get the parameters from the data
        dataIN = rawDataIN.copy()
        if source != 'raw':           
            # Use metadata from file for updating: 
            # site
            site_default = inspect.signature(input_params).parameters['site'].default
            updateMsg = []
            if params['site'] == site_default and params['site'] != dPath.stem:
                if isinstance(dPath, (list, tuple)):
                    dPath = dPath[0]
                params['site'] = dPath.stem
                params['params']['site'] = dPath.stem
                if verbose:
                    updateMsg.append(f"\tSite name updated to {params['site']}")
            
            # network
            net_default = inspect.signature(input_params).parameters['network'].default
            if params['net'] == net_default and net_default != dataIN[0].stats.network:
                params['net'] = dataIN[0].stats.network
                params['params']['net'] = dataIN[0].stats.network
                if verbose:
                    updateMsg.append(f"\tNetwork name updated to {params['net']}")

            # station
            sta_default = inspect.signature(input_params).parameters['station'].default
            if str(params['sta']) == sta_default and str(params['sta']) != dataIN[0].stats.station:
                params['sta'] = dataIN[0].stats.station
                params['station'] = dataIN[0].stats.station
                params['params']['sta'] = dataIN[0].stats.station
                params['params']['station'] = dataIN[0].stats.station
                if verbose:
                    updateMsg.append(f"\tStation name updated to {params['sta']}")

            # location
            loc_default = inspect.signature(input_params).parameters['location'].default
            if params['location'] == loc_default and params['location'] != dataIN[0].stats.location:
                params['location'] = dataIN[0].stats.location
                params['params']['location'] = dataIN[0].stats.location
                if verbose:
                    updateMsg.append(f"\tLocation updated to {params['location']}")

            # channels
            channelList = []
            cha_default = inspect.signature(input_params).parameters['channels'].default
            if str(params['cha']) == cha_default:
                for tr in dataIN:
                    if tr.stats.channel not in channelList:
                        channelList.append(tr.stats.channel)
                        channelList.sort(reverse=True) #Just so z is first, just in case
                if set(params['cha']) != set(channelList):
                    params['cha'] = channelList
                    params['params']['cha'] = channelList
                    if verbose:
                        updateMsg.append(f"\tChannels updated to {params['cha']}")

            # Acquisition date
            # acqdate_default = inspect.signature(input_params).parameters['acq_date'].default
            acqdate_default = str(datetime.datetime.now().date())

            if str(params['acq_date']) == acqdate_default and params['acq_date'] != dataIN[0].stats.starttime.date:
                params['acq_date'] = dataIN[0].stats.starttime.date
                if verbose:
                    updateMsg.append(f"\tAcquisition Date updated to {params['acq_date']}")

            # starttime
            today_Starttime = obspy.UTCDateTime(datetime.datetime(year=datetime.date.today().year, month=datetime.date.today().month,
                                                                 day = datetime.date.today().day,
                                                                hour=0, minute=0, second=0, microsecond=0))
            maxStarttime = datetime.datetime(year=params['acq_date'].year, month=params['acq_date'].month, day=params['acq_date'].day, 
                                             hour=0, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc)

            stime_default = obspy.UTCDateTime(NOWTIME.year, NOWTIME.month, NOWTIME.day, 0, 0, 0, 0)
            if str(params['starttime']) == str(stime_default):
                for tr in dataIN.merge():
                    currTime = datetime.datetime(year=tr.stats.starttime.year, month=tr.stats.starttime.month, day=tr.stats.starttime.day,
                                        hour=tr.stats.starttime.hour, minute=tr.stats.starttime.minute, 
                                       second=tr.stats.starttime.second, microsecond=tr.stats.starttime.microsecond, tzinfo=datetime.timezone.utc)
                    if currTime > maxStarttime:
                        maxStarttime = currTime

                newStarttime = obspy.UTCDateTime(datetime.datetime(year=params['acq_date'].year, month=params['acq_date'].month,
                                                                 day = params['acq_date'].day,
                                                                hour=maxStarttime.hour, minute=maxStarttime.minute, 
                                                                second=maxStarttime.second, microsecond=maxStarttime.microsecond))
                if params['starttime'] != newStarttime:
                    params['starttime'] = newStarttime
                    params['params']['starttime'] = newStarttime
                    if verbose:
                        updateMsg.append(f"\tStarttime updated to {params['starttime']}")

            # endttime
            today_Endtime = obspy.UTCDateTime(datetime.datetime(year=datetime.date.today().year, month=datetime.date.today().month,
                                                                 day = datetime.date.today().day,
                                                                hour=23, minute=59, second=59, microsecond=999999))
            tomorrow_Endtime = today_Endtime + (60*60*24)
            minEndtime = datetime.datetime.now(tz=datetime.timezone.utc)#.replace(tzinfo=datetime.timezone.utc)#(hour=23, minute=59, second=59, microsecond=999999)

            etime_default = obspy.UTCDateTime(NOWTIME.year, NOWTIME.month, NOWTIME.day, 23, 59, 59, 999999)
            if str(params['endtime']) == etime_default or str(params['endtime']) == tomorrow_Endtime:
                for tr in dataIN.merge():
                    currTime = datetime.datetime(year=tr.stats.endtime.year, month=tr.stats.endtime.month, day=tr.stats.endtime.day,
                                        hour=tr.stats.endtime.hour, minute=tr.stats.endtime.minute, 
                                       second=tr.stats.endtime.second, microsecond=tr.stats.endtime.microsecond, tzinfo=datetime.timezone.utc)
                    if currTime < minEndtime:
                        minEndtime = currTime
                newEndtime = obspy.UTCDateTime(datetime.datetime(year=minEndtime.year, month=minEndtime.month,
                                                                 day = minEndtime.day,
                                                                hour=minEndtime.hour, minute=minEndtime.minute, 
                                                                second=minEndtime.second, microsecond=minEndtime.microsecond, tzinfo=datetime.timezone.utc))
                
                if params['endtime'] != newEndtime:
                    params['endtime'] = newEndtime
                    params['params']['endtime'] = newEndtime
                    if verbose:
                        updateMsg.append(f"\tEndtime updated to {params['endtime']}")

            # HVSR_ID (derived)
            project = params['project']
            if project is None:
                proj_id = ''
            else:
                proj_id = str(project)+'-'
            
            # Update HVSR_ID with new information
            params['hvsr_id'] = f"{proj_id}{params['acq_date'].strftime('%Y%m%d')}-{params['starttime'].strftime('%H%M')}-{params['station']}"
            params['params']['hvsr_id'] = f"{proj_id}{params['acq_date'].strftime('%Y%m%d')}-{params['starttime'].strftime('%H%M')}-{params['station']}"

            if verbose and len(updateMsg) > 0:
                updateMsg.insert(0, 'The following parameters have been updated directly from the data:')
                for msgLine in updateMsg:
                    print('\t', msgLine)
                print()

            # Clean up
            dataIN = dataIN.split()
            dataIN = dataIN.trim(starttime=params['starttime'], endtime=params['endtime'])
            dataIN.merge()

    except Exception as e:
        raise RuntimeError(f'Data as read by obspy does not contain the proper metadata. \n{e}.\nCheck your input parameters or the data file.')

    # Latitude, Longitude, Elevation
    # Maybe make this more comprehensive, like for all input_params
    if hasattr(dataIN[0].stats, 'latitude'):
        params['latitude'] = params['params']['latitude'] = dataIN[0].stats['latitude']
    if hasattr(dataIN[0].stats, 'longitude'):
        params['longitude'] = params['params']['longitude'] = dataIN[0].stats['longitude']
    if hasattr(dataIN[0].stats, 'elevation'):
        params['elevation']  = params['params']['elevation'] = dataIN[0].stats['elevation']
    if hasattr(dataIN[0].stats, 'elev_unit'):
        params['elev_unit'] = params['params']['elev_unit'] = dataIN[0].stats['elev_unit']
    if hasattr(dataIN[0].stats, 'input_crs'):
        params['input_crs'] = params['params']['input_crs'] = dataIN[0].stats['input_crs']

    # Get and update metadata after updating data from source
    params = get_metadata(params, update_metadata=update_metadata, source=source)
    inv = params['inv']

    # Trim and save data as specified
    if data_export_path == 'None':
        data_export_path = None
    
    if not data_export_path:
        pass
    else:
        if isinstance(params, HVSRBatch):
            pass
        else:
            dataIN = _trim_data(input=params, stream=dataIN, export_dir=data_export_path, source=source, data_export_format=data_export_format)

    # Split data if masked array (if there are gaps)...detrending cannot be done without
    for tr in dataIN:
        if isinstance(tr.data, np.ma.masked_array):
            dataIN = dataIN.split()
            #Splits entire stream if any trace is masked_array
            break

    # Detrend data
    if isinstance(params, HVSRBatch):
        pass
    else:
        dataIN = __detrend_data(input=dataIN, detrend=detrend, detrend_options=detrend_options, verbose=verbose, source=source)

    # Filter data
    if isinstance(params, HVSRBatch):
        pass
    elif filter_type is None:
        pass
    else:
        dataIN.filter_type(type=filter_type, **filter_options)

    # Remerge data
    dataIN = dataIN.merge(method=1)

    # Plot the input stream?
    if plot_input_stream:
        if plot_engine.lower() in ['plotly', 'plty', 'p']:
            if 'spectrogram_component' in kwargs.keys():
                specComp = kwargs['spectrogram_component']
            else:
                specComp = 'Z'
            params['Input_Plot'] = sprit_plot.plot_input_stream(hv_data=params, stream=dataIN, spectrogram_component=specComp, show_plot=show_plot, return_fig=True)
        elif plot_engine.lower() in ['obspy', 'ospby', 'osbpy', 'opsby', 'opspy', 'o']:
            params['Input_Plot'] = dataIN.plot(method='full', linewidth=0.25, handle=True, show=False)
            if show_plot:
                plt.show()
            else:
                plt.close()
        else:
            try:
                params['Input_Plot'] = sprit_plot._plot_input_stream_mpl(stream=dataIN, hv_data=params, component='Z', stack_type='linear', detrend='mean', dbscale=True, fill_gaps=None, ylimstd=3, return_fig=True, fig=None, ax=None, show_plot=False)
                
                if show_plot:
                    plt.show()
                else:
                    plt.close()                    
            except Exception as e:
                print(f'Error with default plotting method: {e}.\n Falling back to internal obspy plotting method')
                params['Input_Plot'] = dataIN.plot(method='full', linewidth=0.25, handle=True, show=False)
                if show_plot:
                    plt.show()
                else:
                    plt.close()
    else:
        params['Input_Plot'] = None

    # Sort channels (make sure Z is first, makes things easier later)
    if isinstance(params, HVSRBatch):
        pass
    else:
        dataIN = _sort_channels(input=dataIN, source=source, verbose=verbose)

    # Clean up the ends of the data unless explicitly specified to do otherwise (this is a kwarg, not a parameter)
    if 'clean_ends' not in kwargs.keys():
        clean_ends = True 
    else:
        clean_ends = kwargs['clean_ends']

    if clean_ends:
        maxStarttime = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=36500)  # 100 years ago
        minEndtime = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=36500)  # 100 years from now

        for tr in dataIN:
            currStarttime = datetime.datetime(year=tr.stats.starttime.year, month=tr.stats.starttime.month, day=tr.stats.starttime.day, 
                                              hour=tr.stats.starttime.hour, minute=tr.stats.starttime.minute, 
                                              second=tr.stats.starttime.second, microsecond=tr.stats.starttime.microsecond, tzinfo=datetime.timezone.utc)
            if currStarttime > maxStarttime:
                maxStarttime = currStarttime

            currEndtime = datetime.datetime(year=tr.stats.endtime.year, month=tr.stats.endtime.month, day=tr.stats.endtime.day, 
                                         hour=tr.stats.endtime.hour, minute=tr.stats.endtime.minute, 
                                         second=tr.stats.endtime.second, microsecond=tr.stats.endtime.microsecond, tzinfo=datetime.timezone.utc)

            if currEndtime < minEndtime:
                minEndtime = currEndtime

        maxStarttime = obspy.UTCDateTime(maxStarttime)
        minEndtime = obspy.UTCDateTime(minEndtime)
        dataIN = dataIN.split()
        for tr in dataIN:
            tr.trim(starttime=maxStarttime, endtime=minEndtime)
            pass
        dataIN.merge()
    
    params['batch'] = False  # Set False by default, will get corrected later if batch
    params['input_stream'] = dataIN.copy()  # Original stream as read
    params['stream'] = dataIN.copy()  # Stream that may be modified later
    
    if 'processing_parameters' not in params.keys():
        params['processing_parameters'] = {}
    params['processing_parameters']['fetch_data'] = {}
    exclude_params_list = ['params']
    for key, value in orig_args.items():
        if key not in exclude_params_list:
            params['processing_parameters']['fetch_data'][key] = value

    # Attach response data to stream and get paz (for PPSD later)
    # Check if response can be attached
    try:
        responseMatch = {}
        for trace in params['stream']:
            k = trace.stats.component
            
            # Check if station, channel, location, and timing match
            responseMatch[k] = False  # Default to false until proven otherwise

            for sta in params['inv'].networks[0].stations:  # Assumes only one network per inst
                hasCha = False  # all default to false until proven otherwise
                hasLoc = False
                hasSta = False
                isStarted = False
                notEnded = False
                
                # Check station
                if sta.code == params['stream'][0].stats.station:
                    hasSta = True
                else:
                    continue

                # Check Channel
                for cha in sta:
                    if cha.code == trace.stats.channel:
                        hasCha = True

                    # Check location
                    if cha.location_code == trace.stats.location:
                        hasLoc = True


                    # Check time
                    if (cha.start_date is None or cha.start_date <= tr.stats.starttime):
                        isStarted = True

                    if (cha.end_date is None or cha.end_date >= tr.stats.endtime):
                        notEnded = True

                    
                    if all([hasSta, hasCha, hasLoc, isStarted, notEnded]):
                        responseMatch[k] = True

            if responseMatch[k] is not True:
                responseMatch[k] = {'Station':  (hasSta, [sta.code for sta in params['inv'].networks[0].stations]),
                                    'Channel':  (hasCha, [cha.code for cha in sta for sta in params['inv'].networks[0].stations]), 
                                    'Location': (hasLoc, [cha.location_code for cha in sta for sta in params['inv'].networks[0].stations]), 
                                    'Starttime':(isStarted, [cha.start_date for cha in sta for sta in params['inv'].networks[0].stations]), 
                                    'Endtime':  (notEnded,  [cha.end_date for cha in sta for sta in params['inv'].networks[0].stations])}

        metadataMatchError = False
        for comp, matchItems in responseMatch.items():
            if matchItems is not True:
                metadataMatchError = True
                errorMsg = 'The following items in your data need to be matched in the instrument response/metadata:'
                for matchType, match in matchItems.items():
                    if match[0] is False:
                        errorMsg = errorMsg + f"\n\t{matchType} does not match {match[1]} correctly for component {comp}: {params['stream'].select(component=comp)[0].stats[matchType.lower()]}"

        if metadataMatchError:
            if verbose:
                print(errorMsg)
            raise ValueError('Instrument Response/Metadata does not match input data and cannot be used!!\n'+errorMsg)
        else:
            params['stream'].attach_response(params['inv'])
            for tr in params['stream']:
                cmpnt = tr.stats.component

                params['paz'][cmpnt]['poles'] = tr.stats.response.get_paz().poles
                params['paz'][cmpnt]['zeros'] = tr.stats.response.get_paz().zeros
                params['paz'][cmpnt]['sensitivity'] = tr.stats.response.get_paz().stage_gain
                params['paz'][cmpnt]['gain'] = tr.stats.response.get_paz().normalization_factor
    except Exception as e:
        if 'obspy_ppsds' in kwargs and kwargs['obspy_ppsds']:
            errMsg = "Metadata missing, incomplete, or incorrect. Instrument response cannot be removed."
            errMsg += "if metadata cannot be matched, use obspy_ppsds=False to perform analysis on raw data (without instrument response removed)"
            raise ValueError(errMsg)
        else:
            if verbose:
                print("\tMetadata/instrument response does not match data.")
                print("\t  Raw data (without the instrument response removed) will be used for processing.")
    
    params['processing_status']['fetch_data_status'] = True
    if verbose and not isinstance(params, HVSRBatch):
        print('\n')
        dataINStr = dataIN.__str__().split('\n')
        for line in dataINStr:
            print('\t\t', line)
    
    params = sprit_utils._check_processing_status(params, start_time=start_time, func_name=inspect.stack()[0][3], verbose=verbose)

    return params


# For backwards compatibility (now generate_psds()
def generate_ppsds(hvsr_data, **gen_psds_kwargs):
    """This function is to maintain backwards compatibility with previous version
    
    See Also
    --------
    generate_psds
    
    """
    warnings.warn("generate_ppsds() is now deprecated, use generate_psds()", DeprecationWarning)
    hvsrData = generate_psds(hvsr_data, **gen_psds_kwargs)
    return hvsrData


# Generate PSDs for each channel
def generate_psds(hvsr_data, window_length=30.0, overlap_pct=0.5, window_type='hann', window_length_method='length', 
                  remove_response=False, skip_on_gaps=True, num_freq_bins=512, hvsr_band=DEFAULT_BAND,
                  obspy_ppsds=False, azimuthal_psds=False, verbose=False, plot_psds=False, **obspy_ppsd_kwargs):
    
    """Calculate Power Spectral Density (PSD) curves for each channel.
        Uses the [scipy.signal.welch()](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html) function 
        to generate PSDs by default, or can use Obspy's PPSD class.
        Info on Obspy PPSD creation here (if obspy_ppsds=True): https://docs.obspy.org/packages/autogen/obspy.signal.spectral_estimation.PPSD.html
        
        Parameters
        ----------
        hvsr_data : dict, HVSRData object, or HVSRBatch object
            Data object containing all the parameters and other data of interest (stream and paz, for example)
        window_length : float
            Length of the window, in seconds, to use for each PSD calculation. Defaults to 30.0.
        overlap_pct : float
            Percentage (should be 0-1) for overlapping each window used for PSD calculation. Defaults to 0.5.
        window_type : str
            Type of window to use. This is passed to the window parameter of the scipy.signal.welch function
        window_length_method : str = {'length', 'number'}
            Whether the window length should be a measure of length in seconds or number of windows. 
            If number of windows uses integer value.
        remove_response : bool, default=False
            Whether to remove the instrument response from the data traces before calculating PSD data.
            If True, the appropriate metadata (i.e., obspy.Inventory object) must be attached to the stream and should be stored in the 'inv' attribute of hvsr_data.
        skip_on_gaps : bool, default=True
            Whether to skip data gaps when processing windows. 
            This is passed to the skip_on_gaps parameter of the Obspy PPSD class.
        num_freq_bins : int, default=512
            Number of frequency bins to use. When using the default (i.e., scipy.signal.welch) PSD function, the frequency bins are created manually for processing.
        obspy_ppsds : bool, default=False
            Whether to use the Obspy PPSD class.
        azimuthal_psds : bool, default=False
            Whether to generate PPSDs for azimuthal data
        verbose : bool, default=True
            Whether to print inputs and results to terminal
        plot_psds : bool, default=False
            Whether to show a plot of the psds here.
        **obspy_ppsd_kwargs : dict
            Dictionary with keyword arguments that are passed directly to obspy.signal.PPSD.
            If the following keywords are not specified, their defaults are amended in this function from the obspy defaults for its PPSD function. Specifically:
                - ppsd_length defaults to 30 (seconds) here instead of 3600
                - skip_on_gaps defaults to True instead of False
                - period_step_octaves defaults to 0.03125 instead of 0.125

        Returns
        -------
            ppsds : HVSRData object
                Dictionary containing entries with ppsds for each channel
                
        See Also
        --------
        [scipy.signal.welch](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html)
        [obspy.signal.spectral_estimation.PPSD](https://docs.obspy.org/packages/autogen/obspy.signal.spectral_estimation.PPSD.html)
        
    """
    
    # First, divide up for batch or not
    orig_args = locals().copy()  # Get the initial arguments
    start_time = datetime.datetime.now()

    obspy_ppsd_kwargs_sprit_defaults = obspy_ppsd_kwargs.copy()
    # Set defaults here that are different than obspy defaults
    if 'ppsd_length' not in obspy_ppsd_kwargs.keys():
        obspy_ppsd_kwargs_sprit_defaults['ppsd_length'] = 30.0      
    if 'period_step_octaves' not in obspy_ppsd_kwargs.keys():
        obspy_ppsd_kwargs_sprit_defaults['period_step_octaves'] = 0.03125
    if 'period_limits' not in obspy_ppsd_kwargs.keys():
        if 'hvsr_band' in hvsr_data.keys():
            obspy_ppsd_kwargs_sprit_defaults['period_limits'] = [1/hvsr_data['hvsr_band'][1], 1/hvsr_data['hvsr_band'][0]]
        elif 'input_params' in hvsr_data.keys() and 'hvsr_band' in hvsr_data['input_params'].keys():
            obspy_ppsd_kwargs_sprit_defaults['period_limits'] = [1/hvsr_data['input_params']['hvsr_band'][1], 1/hvsr_data['input_params']['hvsr_band'][0]]
        else:
            obspy_ppsd_kwargs_sprit_defaults['period_limits'] = [1/hvsr_band[1], 1/hvsr_band[0]]
    else:
        if verbose:
            print(f"\t\tUpdating hvsr_band to band specified by period_limits={obspy_ppsd_kwargs['period_limits']}")
        
        if 'hvsr_band' in hvsr_data.keys():
            if obspy_ppsd_kwargs['period_limits'] is None:
                obspy_ppsd_kwargs['period_limits'] = np.round([1/hvsr_data['hvsr_band'][1], 1/hvsr_data['hvsr_band'][0]], 3).tolist()
            else:
                hvsr_data['hvsr_band'] = np.round([1/obspy_ppsd_kwargs['period_limits'][1], 1/obspy_ppsd_kwargs['period_limits'][0]], 2).tolist()
        
        if 'input_params' in hvsr_data.keys() and 'hvsr_band' in hvsr_data['input_params'].keys():
            hvsr_data['input_params']['hvsr_band'] = np.round([1/obspy_ppsd_kwargs['period_limits'][1], 1/obspy_ppsd_kwargs['period_limits'][0]], 2).tolist()
            
        
    # Get Probablistic power spectral densities (PPSDs)
    # Get default args for function
    obspy_ppsd_kwargs = sprit_utils._get_default_args(PPSD)
    obspy_ppsd_kwargs.update(obspy_ppsd_kwargs_sprit_defaults)  # Update with sprit defaults, or user input
    orig_args['obspy_ppsd_kwargs'] = obspy_ppsd_kwargs

    # Update with processing parameters specified previously in input_params, if applicable
    if 'processing_parameters' in hvsr_data.keys():
        if 'generate_psds' in hvsr_data['processing_parameters'].keys():
            defaultVDict = dict(zip(inspect.getfullargspec(generate_psds).args[1:], 
                                    inspect.getfullargspec(generate_psds).defaults))
            defaultVDict['obspy_ppsd_kwargs'] = obspy_ppsd_kwargs
            update_msg = []
            for k, v in hvsr_data['processing_parameters']['generate_psds'].items():
                # Manual input to function overrides the imported parameter values
                if not isinstance(v, (HVSRData, HVSRBatch)) and (k in orig_args.keys()) and (orig_args[k] == defaultVDict[k]):
                    update_msg.append(f'\t\t{k} = {v} (previously {orig_args[k]})')
                    orig_args[k] = v

    azimuthal_psds = orig_args['azimuthal_psds']
    verbose = orig_args['verbose']
    obspy_ppsd_kwargs = orig_args['obspy_ppsd_kwargs']

    # if (verbose and isinstance(hvsr_data, HVSRBatch)) or (verbose and not hvsr_data['batch']):
    if verbose:
        print('\nGenerating Probabilistic Power Spectral Densities (generate_psds())')
        print('\tUsing the following parameters:')
        for key, value in orig_args.items():
            if key == 'hvsr_data':
                pass
            else:
                print('\t  {}={}'.format(key, value))
        print()

        if 'processing_parameters' in hvsr_data.keys() and 'generate_psds' in hvsr_data['processing_parameters'].keys():
            if update_msg != []:
                update_msg.insert(0, '\tThe following parameters were updated using the processing_parameters attribute:')
                for msg_line in update_msg:
                    print(msg_line)
                print()

    if isinstance(hvsr_data, HVSRBatch):
        # If running batch, we'll loop through each one
        for site_name in hvsr_data.keys():
            args = orig_args.copy()  # Make a copy so we don't accidentally overwrite
            individual_params = hvsr_data[site_name]  # Get what would normally be the "hvsr_data" variable for each site
            args['hvsr_data'] = individual_params  # reset the hvsr_data parameter we originally read in to an individual site hvsr_data

            if hvsr_data[site_name]['processing_status']['overall_status']:
                try:
                    hvsr_data[site_name] = __generate_ppsds_batch(**args) #Call another function, that lets us run this function again
                except:
                    hvsr_data[site_name]['processing_status']['generate_psds_status']=False
                    hvsr_data[site_name]['processing_status']['overall_status'] = False                     
            else:
                hvsr_data[site_name]['processing_status']['generate_psds_status']=False
                hvsr_data[site_name]['processing_status']['overall_status'] = False                
            
            try:
                sprit_tkinter_ui.update_progress_bars(prog_percent=5)
            except Exception as e:
                pass
                #print(e)
        return hvsr_data
    
    def _get_obspy_ppsds(hvsr_data,**obspy_ppsd_kwargs):
        paz = hvsr_data['paz']
        stream = hvsr_data['stream']

        # Get ppsds of e component
        eStream = stream.select(component='E')
        estats = eStream.traces[0].stats
        ppsdE = PPSD(estats, paz['E'],  **obspy_ppsd_kwargs)
        ppsdE.add(eStream)

        # Get ppsds of n component
        nStream = stream.select(component='N')
        nstats = nStream.traces[0].stats
        ppsdN = PPSD(nstats, paz['N'], **obspy_ppsd_kwargs)
        ppsdN.add(nStream)

        # Get ppsds of z component
        zStream = stream.select(component='Z')
        zstats = zStream.traces[0].stats
        ppsdZ = PPSD(zstats, paz['Z'], **obspy_ppsd_kwargs)
        ppsdZ.add(zStream)

        # Get ppsds of R components (azimuthal data)
        has_az = False
        ppsds = {'Z':ppsdZ, 'E':ppsdE, 'N':ppsdN}
        rStream = stream.select(component='R')
        for curr_trace in stream:
            if 'R' in curr_trace.stats.channel:
                curr_stats = curr_trace.stats
                ppsd_curr = PPSD(curr_stats, paz['E'], **obspy_ppsd_kwargs)        
                has_az = True
                ppsdName = curr_trace.stats.location
                ppsd_curr.add(rStream)
                ppsds[ppsdName] = ppsd_curr
        
        # Add to the input dictionary, so that some items can be manipulated later on, and original can be saved
        hvsr_data['ppsds_obspy'] = ppsds
        hvsr_data['ppsds'] = {}
        anyKey = list(hvsr_data['ppsds_obspy'].keys())[0]
        
        # Get ppsd class members
        members = [mems for mems in dir(hvsr_data['ppsds_obspy'][anyKey]) if not callable(mems) and not mems.startswith("_")]
        for k in ppsds.keys():
            hvsr_data['ppsds'][k] = {}
        
        #Get lists/arrays so we can manipulate data later and copy everything over to main 'ppsds' subdictionary (convert lists to np.arrays for consistency)
        listList = ['times_data', 'times_gaps', 'times_processed','current_times_used', 'psd_values'] #Things that need to be converted to np.array first, for consistency
        timeKeys= ['times_processed','current_times_used','psd_values']
        timeDiffWarn = True
        dfList = []
        time_data = {}
        time_dict = {}
        for m in members:
            for k in hvsr_data['ppsds'].keys():
                hvsr_data['ppsds'][k][m] = getattr(hvsr_data['ppsds_obspy'][k], m)
                if m in listList:
                    hvsr_data['ppsds'][k][m] = np.array(hvsr_data['ppsds'][k][m])
            
            if str(m)=='times_processed':
                unique_times = np.unique(np.array([hvsr_data['ppsds']['Z'][m],
                                                    hvsr_data['ppsds']['E'][m],
                                                    hvsr_data['ppsds']['N'][m]]))

                common_times = []
                for currTime in unique_times:
                    if currTime in hvsr_data['ppsds']['Z'][m]:
                        if currTime in hvsr_data['ppsds']['E'][m]:
                            if currTime in hvsr_data['ppsds']['N'][m]:
                                common_times.append(currTime)

                cTimeIndList = []
                for cTime in common_times:
                    ZArr = hvsr_data['ppsds']['Z'][m]
                    EArr = hvsr_data['ppsds']['E'][m]
                    NArr = hvsr_data['ppsds']['N'][m]

                    cTimeIndList.append([int(np.where(ZArr == cTime)[0][0]),
                                        int(np.where(EArr == cTime)[0][0]),
                                        int(np.where(NArr == cTime)[0][0])])
                    
            # Make sure number of time windows is the same between PPSDs (this can happen with just a few slightly different number of samples)
            if m in timeKeys:
                if str(m) != 'times_processed':
                    time_data[str(m)] = (hvsr_data['ppsds']['Z'][m], hvsr_data['ppsds']['E'][m], hvsr_data['ppsds']['N'][m])

                tSteps_same = hvsr_data['ppsds']['Z'][m].shape[0] == hvsr_data['ppsds']['E'][m].shape[0] == hvsr_data['ppsds']['N'][m].shape[0]

                if not tSteps_same:
                    shortestTimeLength = min(hvsr_data['ppsds']['Z'][m].shape[0], hvsr_data['ppsds']['E'][m].shape[0], hvsr_data['ppsds']['N'][m].shape[0])

                    maxPctDiff = 0
                    for comp in hvsr_data['ppsds'].keys():
                        currCompTimeLength = hvsr_data['ppsds'][comp][m].shape[0]
                        timeLengthDiff = currCompTimeLength - shortestTimeLength
                        percentageDiff = timeLengthDiff / currCompTimeLength
                        if percentageDiff > maxPctDiff:
                            maxPctDiff = percentageDiff

                    for comp in hvsr_data['ppsds'].keys():
                        while hvsr_data['ppsds'][comp][m].shape[0] > shortestTimeLength:
                            hvsr_data['ppsds'][comp][m] = hvsr_data['ppsds'][comp][m][:-1]
                    
                    
                    if maxPctDiff > 0.05 and timeDiffWarn:
                        warnings.warn(f"\t  Number of ppsd time windows between different components is significantly different: {round(maxPctDiff*100,2)}% > 5%. Last windows will be trimmed.")
                    elif verbose  and timeDiffWarn:
                        print(f"\t  Number of ppsd time windows between different components is different by {round(maxPctDiff*100,2)}%. Last window(s) of components with larger number of ppsd windows will be trimmed.")
                    timeDiffWarn = False #So we only do this warning once, even though there may be multiple arrays that need to be trimmed

        for i, currTStep in enumerate(cTimeIndList):
            colList = []
            currTStepList = []
            colList.append('Use')
            currTStepList.append(np.ones_like(common_times[i]).astype(bool))
            for tk in time_data.keys():
                if 'current_times_used' not in tk:
                    for i, k in enumerate(hvsr_data['ppsds'].keys()):
                        if k.lower() in ['z', 'e', 'n']:
                            colList.append(str(tk)+'_'+k)
                            currTStepList.append(time_data[tk][i][currTStep[i]])
            dfList.append(currTStepList)

        return hvsr_data, dfList, colList, common_times

    if obspy_ppsds:
        hvsr_data, dfList, colList, common_times = _get_obspy_ppsds(hvsr_data, **obspy_ppsd_kwargs)
    else:
        psdDict, common_times = __single_psd_from_raw_data(hvsr_data, window_length=window_length, window_length_method=window_length_method, window_type=window_type,
                                                           num_freq_bins=num_freq_bins,
                                                           overlap=overlap_pct, remove_response=remove_response, do_azimuths=azimuthal_psds, show_psd_plot=False)

        x_freqs = np.flip(np.logspace(np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1]), num_freq_bins))
        
        psdDictUpdate = {}
        hvsr_data['ppsds'] = {}
        for key, compdict in psdDict.items():
            psdDictUpdate[key] = np.array([list(np.flip(arr)) for time, arr in compdict.items()])
            hvsr_data['ppsds'][key] = {}
        
        #hvsr_data['ppsds'] = {'Z':{}, 'E':{}, 'N':{}}
        for key, item in psdDict.items():
            currSt = hvsr_data.stream.select(component=key).merge()
                      
            hvsr_data['ppsds'][key]['channel'] = currSt[0].stats.channel
            hvsr_data['ppsds'][key]['current_times_used'] = common_times
            hvsr_data['ppsds'][key]['delta'] = float(currSt[0].stats.delta)
            #hvsr_data['ppsds'][key]['get_mean'] = np.nanmean(item)
            #hvsr_data['ppsds'][key]['mean'] = np.nanmean(item)
            #hvsr_data['ppsds'][key]['get_mode'] = scipy.stats.mode(item)
            #hvsr_data['ppsds'][key]['mode'] = scipy.stats.mode(item)
            hvsr_data['ppsds'][key]['id'] = currSt[0].id
            hvsr_data['ppsds'][key]['len'] = int(window_length / hvsr_data['ppsds'][key]['delta'])
            hvsr_data['ppsds'][key]['location'] = currSt[0].stats.location
            hvsr_data['ppsds'][key]['metadata'] = [currSt[0].stats.response if hasattr(currSt[0].stats, 'response') else None][0]
            hvsr_data['ppsds'][key]['network'] = currSt[0].stats.network
            hvsr_data['ppsds'][key]['nfft'] = int(window_length / hvsr_data['ppsds'][key]['delta'])
            hvsr_data['ppsds'][key]['nlap'] = int(overlap_pct*window_length / hvsr_data['ppsds'][key]['delta'])
            hvsr_data['ppsds'][key]['overlap'] = overlap_pct
            hvsr_data['ppsds'][key]['period_bin_centers'] = [round(1/float(f + np.diff(x_freqs)[i]/2), 4) for i, f in enumerate(x_freqs[:-1])]
            hvsr_data['ppsds'][key]['period_bin_centers'].append(float(round(1/x_freqs[-1], 3)))
            hvsr_data['ppsds'][key]['period_bin_centers'] = np.array(hvsr_data['ppsds'][key]['period_bin_centers'])
            hvsr_data['ppsds'][key]['period_bin_left_edges'] = 1/x_freqs[:-1]
            hvsr_data['ppsds'][key]['period_bin_right_edges'] = 1/x_freqs[1:]
            hvsr_data['ppsds'][key]['period_xedges'] = 1/x_freqs
            hvsr_data['ppsds'][key]['ppsd_length'] = window_length
            hvsr_data['ppsds'][key]['psd_length'] = window_length
            hvsr_data['ppsds'][key]['psd_frequencies'] = x_freqs
            hvsr_data['ppsds'][key]['psd_periods'] = 1/x_freqs
            hvsr_data['ppsds'][key]['psd_values'] = psdDictUpdate[key]
            hvsr_data['ppsds'][key]['sampling_rate'] = currSt[0].stats.sampling_rate
            hvsr_data['ppsds'][key]['skip_on_gaps'] = skip_on_gaps
            hvsr_data['ppsds'][key]['station'] = currSt[0].stats.station
            hvsr_data['ppsds'][key]['step'] = window_length * (1-overlap_pct)
            hvsr_data['ppsds'][key]['times_data'] = common_times
            hvsr_data['ppsds'][key]['times_gaps'] = [[None, None]]
            hvsr_data['ppsds'][key]['times_processed'] = [[None, None]]
            
        hvsr_data['ppsds_obspy'] = {}
        dfList = []
        for i, w in enumerate(common_times):
            ws = str(w)
            dfList.append([True, psdDictUpdate['Z'][i], psdDictUpdate['E'][i], psdDictUpdate['N'][i]])
        colList = ["Use", "psd_values_Z", "psd_values_E", "psd_values_N"]
        # dfList: list of np.arrays, fitting the above column
        # common_times: times in common between all, should be length of 1 psd dimension above
        # hvsr_data['ppsds']['Z']['times_gaps']: list of two-item lists with UTCDatetimes for gaps
        
        # #Maybe not needed hvsr_data['ppsds']['Z']['current_times_used']

    hvsrDF = pd.DataFrame(dfList, columns=colList)
    if verbose:
        print(f"\t\t{hvsrDF.shape[0]} processing windows generated and psd values stored in hvsr_windows_df with columns: {', '.join(hvsrDF.columns)}")
    hvsrDF['Use'] = hvsrDF['Use'].astype(bool)
    # Add azimuthal ppsds values
    for k in hvsr_data['ppsds'].keys():
        if k.upper() not in ['Z', 'E', 'N']:
            hvsrDF['psd_values_'+k] = hvsr_data['ppsds'][k]['psd_values'].tolist()

    hvsrDF['TimesProcessed_Obspy'] = common_times
    hvsrDF['TimesProcessed_ObspyEnd'] = hvsrDF['TimesProcessed_Obspy'] + obspy_ppsd_kwargs['ppsd_length']
    #    colList.append('TimesProcessed_Obspy')
    #    currTStepList.append(common_times[i])            
    # Add other times (for start times)
    
    # Create functions to be used in pandas .apply() for datetime conversions
    def convert_to_datetime(obspyUTCDateTime):
        return obspyUTCDateTime.datetime.replace(tzinfo=datetime.timezone.utc)
    def convert_to_mpl_dates(obspyUTCDateTime):
        return obspyUTCDateTime.matplotlib_date

    hvsrDF['TimesProcessed'] = hvsrDF['TimesProcessed_Obspy'].apply(convert_to_datetime)
    
    hvsrDF['TimesProcessed_End'] = hvsrDF['TimesProcessed'] + datetime.timedelta(days=0, seconds=obspy_ppsd_kwargs['ppsd_length'])
    hvsrDF['TimesProcessed_MPL'] = hvsrDF['TimesProcessed_Obspy'].apply(convert_to_mpl_dates)
    hvsrDF['TimesProcessed_MPLEnd'] = hvsrDF['TimesProcessed_MPL'] + (obspy_ppsd_kwargs['ppsd_length']/86400)
    
    # Take care of existing time gaps, in case not taken care of previously
    if obspy_ppsds:
        for gap in hvsr_data['ppsds']['Z']['times_gaps']:
            hvsrDF['Use'] = (hvsrDF['TimesProcessed_MPL'].gt(gap[1].matplotlib_date))| \
                        (hvsrDF['TimesProcessed_MPLEnd'].lt(gap[0].matplotlib_date)).astype(bool)# | \
    
    hvsrDF.set_index('TimesProcessed', inplace=True)
    hvsr_data['hvsr_windows_df'] = hvsrDF
    
    # Remove data set for removal during remove_noise()
    if 'x_windows_out' in hvsr_data.keys():
        if verbose:
            print("\t\tRemoving Noisy windows from hvsr_windows_df.")
        hvsr_data = __remove_windows_from_df(hvsr_data, verbose=verbose)
        #for window in hvsr_data['x_windows_out']:
        #    print(window)
        #    hvsrDF['Use'] = (hvsrDF['TimesProcessed_MPL'][hvsrDF['Use']].lt(window[0]) & hvsrDF['TimesProcessed_MPLEnd'][hvsrDF['Use']].lt(window[0]) )| \
        #            (hvsrDF['TimesProcessed_MPL'][hvsrDF['Use']].gt(window[1]) & hvsrDF['TimesProcessed_MPLEnd'][hvsrDF['Use']].gt(window[1])).astype(bool)
        #hvsrDF['Use'] = hvsrDF['Use'].astype(bool)
        
    # Create dict entry to keep track of how many outlier hvsr curves are removed 
    # This is a (2-item list with [0]=current number, [1]=original number of curves)
    hvsr_data['tsteps_used'] = [int(hvsrDF['Use'].sum()), hvsrDF['Use'].shape[0]]
    #hvsr_data['tsteps_used'] = [hvsr_data['ppsds']['Z']['times_processed'].shape[0], hvsr_data['ppsds']['Z']['times_processed'].shape[0]]
    #hvsr_data['tsteps_used'][0] = hvsr_data['ppsds']['Z']['current_times_used'].shape[0]
    
    hvsr_data = sprit_utils._make_it_classy(hvsr_data)

    if 'processing_parameters' not in hvsr_data.keys():
        hvsr_data['processing_parameters'] = {}
    hvsr_data['processing_parameters']['generate_psds'] = {}
    exclude_params_list = ['hvsr_data']
    for key, value in orig_args.items():
        if key not in exclude_params_list:
            hvsr_data['processing_parameters']['generate_psds'][key] = value
    
    hvsr_data['processing_status']['generate_psds_status'] = True
    hvsr_data = sprit_utils._check_processing_status(hvsr_data, start_time=start_time, func_name=inspect.stack()[0][3], verbose=verbose)
    
    #for ind, row in hvsrDF.iterrows():
    #    print(row['psd_values_Z'].shape)
    if plot_psds:
        for i, r in hvsrDF.iterrows():
            plt.plot(r['psd_values_Z'], c='k', linewidth=0.5)
            plt.plot(r['psd_values_E'], c='b', linewidth=0.5)
            plt.plot(r['psd_values_N'], c='r', linewidth=0.5)
        plt.show()

    return hvsr_data


# Gets the metadata for Raspberry Shake, specifically for 3D v.7
def get_metadata(params, write_path='', update_metadata=True, source=None, verbose=False, **read_inventory_kwargs):
    """Get metadata and calculate or get paz parameter needed for PSD
       Adds an obspy.Inventory object to the "inv" attribute or key of params
    

    Parameters
    ----------
    params : dict
        Dictionary containing all the input and other parameters needed for processing
            Ouput from input_params() function
    write_path : str
        String with output filepath of where to write updated inventory or metadata file
            If not specified, does not write file 
    update_metadata : bool
        Whether to update the metadata file itself, or just read as-is. If using provided raspberry shake metadata file, select True.
    source : str, default=None
        This passes the source variable value to _read_RS_metadata. It is expected that this is passed directly from the source parameter of sprit.fetch_data()

    Returns
    -------
    params : dict
        Modified input dictionary with additional key:value pair containing paz dictionary (key = "paz")
    """
    
    invPath = params['metadata']
    raspShakeInstNameList = ['raspberry shake', 'shake', 'raspberry', 
                             'rs', 'rs3d', 'rasp. shake', 
                             'raspshake', 'raspberry shake 3d']
    trominoNameList = ['tromino', 'trom', 'trm', 't']
       
    if str(params['instrument']).lower() in raspShakeInstNameList:
        if update_metadata:
            params = _update_shake_metadata(filepath=invPath, params=params, write_path=write_path, verbose=verbose)
        params = _read_RS_Metadata(params, source=source)
    elif params['instrument'].lower() in trominoNameList:
        params['paz'] = {'Z':{}, 'E':{}, 'N':{}}

        # Initially started here: https://ds.iris.edu/NRL/sensors/Sunfull/RESP.XX.NS721..BHZ.PS-4.5C1_LF4.5_RC3400_RSNone_SG82_STgroundVel
        tromino_paz = { 'zeros': [-3.141592653589793/2-0j, -3.141592653589793/2-0j],
                        'poles': [(17-24j), (17+24j)],
                        'stage_gain':100,
                        'stage_gain_frequency':10,
                        'normalization_frequency':5, 
                        'normalization_factor':1}
        
        params['paz']['Z'] =  params['paz']['E'] = params['paz']['N'] = tromino_paz
        
        tromChaResponse = obspy.core.inventory.response.Response().from_paz(**tromino_paz)

        obspyStartDate = obspy.UTCDateTime(1900,1,1)
        obspyNow = obspy.UTCDateTime.now()

        # Update location code to match partition
        if type(params['station']) is int or str(params['station']).isdigit():
            params['location'] = str(params['station'])

        # Create channel objects to be used in inventory                
        channelObj_Z = obspy.core.inventory.channel.Channel(code='EHZ', location_code=params['location'], latitude=params['params']['latitude'], 
                                                longitude=params['params']['longitude'], elevation=params['params']['elevation'], depth=params['params']['depth'], 
                                                azimuth=0, dip=90, start_date=obspyStartDate, end_date=obspyNow, response=tromChaResponse)
        channelObj_E = obspy.core.inventory.channel.Channel(code='EHE', location_code=params['location'], latitude=params['params']['latitude'], 
                                                longitude=params['params']['longitude'], elevation=params['params']['elevation'], depth=params['params']['depth'], 
                                                azimuth=90, dip=0, start_date=obspyStartDate, end_date=obspyNow, response=tromChaResponse) 
        channelObj_N = obspy.core.inventory.channel.Channel(code='EHN', location_code=params['location'], latitude=params['params']['latitude'], 
                                                longitude=params['params']['longitude'], elevation=params['params']['elevation'], depth=params['params']['depth'], 
                                                azimuth=0, dip=0, start_date=obspyStartDate, end_date=obspyNow, response=tromChaResponse) 
        
        # Create site object for inventory
        siteObj = obspy.core.inventory.util.Site(name=params['params']['site'], description=None, town=None, county=None, region=None, country=None)
        
        # Create station object for inventory
        stationObj = obspy.core.inventory.station.Station(code='TRMNO', latitude=params['params']['latitude'], longitude=params['params']['longitude'], 
                                            elevation=params['params']['elevation'], channels=[channelObj_Z, channelObj_E, channelObj_N], site=siteObj, 
                                            vault=None, geology=None, equipments=None, operators=None, creation_date=obspyStartDate,
                                            termination_date=obspy.UTCDateTime(2100,1,1), total_number_of_channels=3, 
                                            selected_number_of_channels=3, description='Estimated data for Tromino, this is NOT from the manufacturer',
                                            comments=None, start_date=obspyStartDate, end_date=obspyNow, 
                                            restricted_status=None, alternate_code=None, historical_code=None, 
                                            data_availability=obspy.core.inventory.util.DataAvailability(obspyStartDate, obspy.UTCDateTime.now()), 
                                            identifiers=None, water_level=None, source_id=None)

        # Create network object for inventory
        network = [obspy.core.inventory.network.Network(code='AM', stations=[stationObj], total_number_of_stations=None, 
                                            selected_number_of_stations=None, description=None, comments=None, start_date=obspyStartDate, 
                                            end_date=obspyNow, restricted_status=None, alternate_code=None, historical_code=None, 
                                            data_availability=None, identifiers=None, operators=None, source_id=None)]
        
        params['inv'] = obspy.Inventory(networks=network)
    else:
        if not invPath:
            pass #if invPath is None
        elif not pathlib.Path(invPath).exists() or invPath == '':
            warnings.warn(f"The metadata parameter was not specified correctly. Returning original params value {params['metadata']}")
        readInvKwargs = {}
        argspecs = inspect.getfullargspec(obspy.read_inventory)
        for argName in argspecs[0]:
            if argName in read_inventory_kwargs.keys():
                readInvKwargs[argName] = read_inventory_kwargs[argName]

        readInvKwargs['path_or_file_object'] = invPath
        params['inv'] = obspy.read_inventory(invPath)
        if 'params' in params.keys():
            params['params']['inv'] = params['inv']

    return params


# Get report (report generation and export)
def get_report(hvsr_results, report_formats=['print', 'table', 'plot', 'html', 'pdf'], azimuth='HV',
               plot_type=DEFAULT_PLOT_STR, plot_engine='matplotlib', 
               show_print_report=True, show_table_report=False, show_plot_report=False, show_html_report=False, show_pdf_report=True,
               suppress_report_outputs=False, show_report_outputs=False,
               csv_handling='append', 
               report_export_format=None, report_export_path=None, 
               verbose=False, **kwargs):    
    """Generate and/or print and/or export a report of the HVSR analysis in a variety of formats. 
    
    Formats include:
    * 'print': A (monospace) text summary of the HVSR results
    * 'table': A pandas.DataFrame summary of the HVSR Results.
            This is useful for copy/pasting directly into a larger worksheet.
    * 'plot': A plot summary of the HVSR results, generated using the plot_hvsr() function.
    * 'html': An HTML document/text of the HVSR results. This includes the table, print, and plot reports in one document.
    * 'pdf': A PDF document showing the summary of the HVSR Results. 
            The PDF report is simply the HTML report saved to an A4-sized PDF document.

        
    Parameters
    ----------
    hvsr_results : dict
        Dictionary containing all the information about the processed hvsr data
    report_formats : {'table', 'print', plot}
        Format in which to print or export the report.
        The following report_formats return the following items in the following attributes:
            - 'plot': hvsr_results['Print_Report'] as a str
            - 'print': hvsr_results['Plot_Report'] - matplotlib.Figure object
            - 'table':  hvsr_results['Table_Report']- pandas.DataFrame object
                - list/tuple - a list or tuple of the above objects, in the same order they are in the report_formats list
            - 'html': hvsr_results['HTML_Report'] - a string containing the text for an HTML document
            - 'pdf': currently does not save to the HVSRData object itself, can only be saved to the disk directly
    plot_type : str, default = 'HVSR p ann C+ p ann Spec p ann'
        What type of plot to plot, if 'plot' part of report_formats input
    azimuth : str, default = 'HV'
        Which azimuth to plot, by default "HV" which is the main "azimuth" combining the E and N components
    csv_handling : str, {'append', 'overwrite', 'keep/rename'}
        How to handle table report outputs if the designated csv output file already exists. By default, appends the new information to the end of the existing file.
    suppress_report_outputs : bool, default=False
        If True, only reads output to appropriate attribute of data class (ie, print does not print, only reads text into variable). If False, performs as normal.
    report_export_format : list or str, default=['pdf']
        A string or list of strings indicating which report formats should be exported to disk.
    report_export_path : None, bool, or filepath, default = None
        If None or False, does not export; if True, will export to same directory as the input_data parameter in the input_params() function.
        Otherwise, it should be a string or path object indicating where to export results. May be a file or directory.
        If a directory is specified, the filename will be  "<site_name>_<acq_date>_<UTC start time>-<UTC end time>". 
        The extension/suffix defaults to png for report_formats="plot", csv for 'table', txt for 'print', html for 'html', and pdf for 'pdf.'
    verbose : bool, default=True
        Whether to print the results to terminal. This is the same output as report_formats='print', and will not repeat if that is already selected

    Returns
    -------
    sprit.HVSRData
    """
    orig_args = locals().copy() #Get the initial arguments
    orig_args['report_formats'] = [str(f).lower() for f in orig_args['report_formats']]
    update_msg = []

    # Update with processing parameters specified previously in input_params, if applicable
    if 'processing_parameters' in hvsr_results.keys():
        if 'get_report' in hvsr_results['processing_parameters'].keys():
            for k, v in hvsr_results['processing_parameters']['get_report'].items():
                defaultVDict = dict(zip(inspect.getfullargspec(get_report).args[1:], 
                                        inspect.getfullargspec(get_report).defaults))
                defaultVDict['kwargs'] = {}
                # Manual input to function overrides the imported parameter values
                if (not isinstance(v, (HVSRData, HVSRBatch))) and (k in orig_args.keys()) and (orig_args[k]==defaultVDict[k]):
                    update_msg.append(f'\t\t{k} = {v} (previously {orig_args[k]})')
                    orig_args[k] = v
                    
    report_formats = orig_args['report_formats']
    azimuth = orig_args['azimuth']
    plot_type = orig_args['plot_type']
    plot_engine = orig_args['plot_engine']
    show_print_report = orig_args['show_print_report']
    show_table_report = orig_args['show_table_report']
    show_plot_report = orig_args['show_plot_report']
    show_html_report = orig_args['show_html_report']
    show_pdf_report = orig_args['show_pdf_report']
    suppress_report_outputs = orig_args['suppress_report_outputs']
    show_report_outputs = orig_args['show_report_outputs']
    report_export_format = orig_args['report_export_format']
    report_export_path = orig_args['report_export_path']
    csv_handling = orig_args['csv_handling']
    verbose = orig_args['verbose']
    kwargs = orig_args['kwargs']

    # Put Processing parameters in hvsr_results immediately (gets used later local function in get_report)
    hvsr_results['processing_parameters']['get_report'] = {}
    exclude_params_list = ['hvsr_results']
    for key, value in orig_args.items():
        if key not in exclude_params_list:
            hvsr_results['processing_parameters']['get_report'][key] = value
    
    if verbose:
        print('\nGetting HVSR Report: get_report()')
        print('\tUsing the following parameters:')
        for key, value in orig_args.items():
            if key == 'params' or isinstance(value, (HVSRData, HVSRBatch)):
                pass
            else:
                print('\t  {}={}'.format(key, value))
        print()

        if update_msg != [] and verbose:
            update_msg.insert(0, '\tThe following parameters were updated using the processing_parameters attribute:')
            for msg_line in update_msg:
                print(msg_line)
                    
    if isinstance(hvsr_results, HVSRBatch):
        if verbose:
            print('\nGetting Reports: Running in batch mode')

            print('\tUsing parameters:')
            for key, value in orig_args.items():
                print(f'\t  {key}={value}')    
            print()
        
        #If running batch, we'll loop through each site
        for site_name in hvsr_results.keys():
            args = orig_args.copy() #Make a copy so we don't accidentally overwrite
            individual_params = hvsr_results[site_name] #Get what would normally be the "params" variable for each site
            args['hvsr_results'] = individual_params #reset the params parameter we originally read in to an individual site params
            if hvsr_results[site_name]['processing_status']['overall_status']:
                try:
                    hvsr_results[site_name] = __get_report_batch(**args) #Call another function, that lets us run this function again
                except:
                    hvsr_results[site_name] = hvsr_results[site_name]
            else:
                hvsr_results[site_name] = hvsr_results[site_name]
        
        combined_csvReport = pd.DataFrame()
        for site_name in hvsr_results.keys():
            if 'Table_Report' in hvsr_results[site_name].keys():
                combined_csvReport = pd.concat([combined_csvReport, hvsr_results[site_name]['Table_Report']], ignore_index=True, join='inner')
        
        if report_export_path is not None:
            if report_export_path is True:
                if pathlib.Path(hvsr_results['input_params']['input_data']) in sampleFileKeyMap.values():
                    csvExportPath = pathlib.Path(os.getcwd())
                else:
                    csvExportPath = pathlib.Path(hvsr_results['input_params']['input_data'])
            elif pathlib.Path(report_export_path).is_dir():
                csvExportPath = report_export_path
            elif pathlib.Path(report_export_path).is_file():
                csvExportPath = report_export_path.parent
            else:
                csvExportPath = pathlib.Path(hvsr_results[site_name].input_data)
                if csvExportPath.is_dir():
                    pass
                else:
                    csvExportPath = csvExportPath.parent
                
            combined_csvReport.to_csv(csvExportPath, index=False)
        return hvsr_results
    
    if suppress_report_outputs:
        show_print_report = show_plot_report = show_table_report = show_html_report = show_pdf_report = False
    elif show_report_outputs:
        show_print_report = show_plot_report = show_table_report = show_html_report = show_pdf_report = True
    #if 'BestPeak' in hvsr_results.keys() and 'PassList' in hvsr_results['BestPeak'].keys():
    try:
        curvTestsPassed = (hvsr_results['BestPeak'][azimuth]['PassList']['WinLen'] +
                            hvsr_results['BestPeak'][azimuth]['PassList']['SigCycles']+
                            hvsr_results['BestPeak'][azimuth]['PassList']['LowCurveStD'])
        curvePass = curvTestsPassed > 2
        
        #Peak Pass?
        peakTestsPassed = ( hvsr_results['BestPeak'][azimuth]['PassList']['ProminenceLow'] +
                    hvsr_results['BestPeak'][azimuth]['PassList']['ProminenceHi']+
                    hvsr_results['BestPeak'][azimuth]['PassList']['AmpClarity']+
                    hvsr_results['BestPeak'][azimuth]['PassList']['FreqStability']+
                    hvsr_results['BestPeak'][azimuth]['PassList']['LowStDev_Freq']+
                    hvsr_results['BestPeak'][azimuth]['PassList']['LowStDev_Amp'])
        peakPass = peakTestsPassed >= 5
    except Exception as e:
        errMsg= 'No BestPeak identified. Check peak_freq_range or hvsr_band or try to remove bad noise windows using remove_noise() or change processing parameters in process_hvsr() or generate_psds(). Otherwise, data may not be usable for HVSR.'
        print(errMsg)
        print(e)
        plotString_noBestPeak = 'HVSR t all C+ t SPEC'
        hvsr_results['Plot_Report'] = plot_hvsr(hvsr_results, plot_type=plotString_noBestPeak, azimuth=azimuth, return_fig=True)
        return hvsr_results
        #raise RuntimeError('No BestPeak identified. Check peak_freq_range or hvsr_band or try to remove bad noise windows using remove_noise() or change processing parameters in process_hvsr() or generate_psds(). Otherwise, data may not be usable for HVSR.')

    # Figure out which reports will be used, and format them correctly
    if isinstance(report_formats, (list, tuple)):
        report_formats = [str(rf).lower() for rf in report_formats]
    else:
        #We will use a loop later even if it's just one report type, so reformat to prepare for for loop
        allList = [':', 'all']
        if report_formats.lower() in allList:
            report_formats = ['print', 'table', 'plot', 'html', 'pdf']
        else:
            report_formats = [str(report_formats).lower()]   

    # Format the export formats correctly
    if isinstance(report_export_format, (list, tuple)):
        pass
    elif report_export_format is None:
        pass
    else:
        # We will use list methods later even if it's just one report type, so reformat as list
        allList = [':', 'all']
        if report_export_format.lower() in allList:
            report_export_format = ['print', 'table', 'plot', 'html', 'pdf']
        else:
            report_export_format = [report_export_format]   

    # Put print first to get results immediatley while plots and others are created
    if 'print' in report_formats and report_formats[0] != 'print':
        report_formats = ['table', 'plot', 'print', 'html', 'pdf']
        report_formats.pop(report_formats.index('print'))
        report_formats.insert(0, 'print')

    for i, rep_form in enumerate(report_formats):
        if isinstance(report_export_path, (list, tuple)):
            if not isinstance(report_formats, (list, tuple)):
                warnings.warn('report_export_path is a list/tuple and report_formats is not. This may result in unexpected behavior.')
            if isinstance(report_formats, (list, tuple)) and isinstance(report_export_path, (list, tuple)) and len(report_formats) != len(report_export_path):
                warnings.warn('report_export_path and report_formats are both lists or tuples, but they are not the same length. This may result in unexpected behavior.')
            exp_path = report_export_path[i]
        else:
            exp_path = report_export_path
        
        if report_export_format is None:
            report_export_format = ''
       
        # Print_Report
        if rep_form == 'print':
            verbose_print = verbose
            if show_print_report:
                verbose_print = True
            
            # Generates print report and saves to hvsr_results["Print_Report"]
            hsvr_results = _generate_print_report(hvsr_results, 
                                azimuth = azimuth, 
                                show_print_report = True, verbose=verbose_print)

            if 'print' in report_export_format:
                if exp_path is None:
                    print_exp_path = exp_path
                else:
                    print_exp_path = pathlib.Path(exp_path).with_suffix('.txt')
                
                export_report(hvsr_results, azimuth=azimuth,
                              report_export_format='print', report_export_path=print_exp_path, 
                              show_report = False, # If report is to be shown, done in previous step
                              verbose = verbose_print)

        # Table_Report
        elif rep_form == 'table':
            verbose_table = verbose
            if show_table_report:
                verbose_table = True
            
            hsvr_results = _generate_table_report(hvsr_results, 
                                azimuth=azimuth,
                                show_table_report=show_table_report,
                                verbose=verbose_table)

            if 'table' in report_export_format:
                if exp_path is None:
                    table_exp_path = exp_path
                else:
                    table_exp_path = pathlib.Path(exp_path).with_suffix('.csv')
                
                export_report(hvsr_results, azimuth=azimuth,
                            report_export_format='table', report_export_path=table_exp_path,
                            csv_handling=csv_handling,
                            show_report = False, # If report is to be shown, done in previous step
                            verbose = verbose_table)

        # Plot_Report
        elif rep_form == 'plot':
            plot_hvsr_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(plot_hvsr).parameters.keys())}
            if 'plot_type' in plot_hvsr_kwargs.keys():
                plot_hvsr_kwargs.pop('plot_type')
            if 'plot_engine' in plot_hvsr_kwargs.keys():
                plot_hvsr_kwargs.pop('plot_engine')

            fig = plot_hvsr(hvsr_results, plot_type=plot_type, azimuth=azimuth, plot_engine=plot_engine, show_plot=show_plot_report, return_fig=True)
            expFigAx = fig
            
            if 'plot' in report_export_format:
                export_report(hvsr_results=hvsr_results, report_export_path=report_export_path, report_export_format='plot')
            #hvsr_results['BestPeak'][azimuth]['Report']['Plot_Report'] = fig
            hvsr_results['Plot_Report'] = fig

            if show_plot_report:#'show_plot' in plot_hvsr_kwargs.keys() and plot_hvsr_kwargs['show_plot'] is False:
                if not verbose:
                    if str(plot_engine).lower():
                        plt.show()
                    else:
                        fig.show()
                else:
                    print('\nPlot of data report:')
                    if str(plot_engine).lower():
                        plt.show()
                    else:
                        fig.show()                    
            else:
                if verbose:
                    print("\n\tPlot of data report created and saved in ['Plot_Report'] attribute")

        # HTML_Report
        elif rep_form == 'html':
            verbose_html = verbose
            if verbose or show_html_report:
                verbose_html = True
            hvsr_results = _generate_html_report(hsvr_results, show_html_report=show_html_report, verbose=verbose_html)

            if 'html' in report_export_format:
                if exp_path is None:
                    html_exp_path = exp_path
                else:
                    html_exp_path = pathlib.Path(exp_path).with_suffix('.html')

                export_report(hvsr_results, azimuth=azimuth,
                            report_export_format='html', report_export_path=html_exp_path,
                            show_report = False, # If report is to be shown, done in previous step
                            verbose = verbose_html)

        # PDF_Report
        elif rep_form == 'pdf':
            verbose_pdf = verbose

            # Don't repeat html printing, etc. if already done
            if 'html' in report_formats:
                show_html_report = False
            else:
                show_html_report = show_html_report

            if exp_path is None:
                pdf_exp_path = exp_path
            else:
                pdf_exp_path = pathlib.Path(exp_path)
            hvsr_results = _generate_pdf_report(hvsr_results, pdf_report_filepath=pdf_exp_path,
                            show_pdf_report=show_pdf_report, show_html_report=show_html_report, verbose=verbose_pdf)


    return hvsr_results


# Import data
def import_data(import_filepath, data_format='gzip', show_data=True):
    """Function to import .hvsr (or other extension) data exported using export_hvsr() function

    Parameters
    ----------
    import_filepath : str or path object
        Filepath of file created using export_hvsr() function. This is usually a pickle file with a .hvsr extension
    data_format : str, default='pickle'
        Type of format data is in. Currently, only 'pickle' supported. Eventually, json or other type may be supported, by default 'pickle'.

    Returns
    -------
    HVSRData or HVSRBatch object
    """
    
    sample_list = ['sample', 'sampledata', 's']
    if import_filepath in sample_list:
        import_filepath = RESOURCE_DIR.joinpath(r'sample_data')
        import_filepath = import_filepath.joinpath(r'SampleHVSRSite01.hvsr')

    if data_format == 'pickle':
        with open(import_filepath, 'rb') as f:
            dataIN = pickle.load(f)
    elif data_format.lower() == 'dataframe':
        dataIN = pd.read_csv(import_filepath)
    else:
        try:
            with gzip.open(import_filepath, 'rb') as f:
                dataIN = pickle.loads(f.read())
        except Exception as e:
            with open(import_filepath, 'rb') as f:
                dataIN = pickle.load(f)
    
    if show_data:
        print(dataIN)
    
    return dataIN


# Import settings
def import_settings(settings_import_path, settings_import_type='instrument', verbose=False):
    """Function to import settings, intended for use with settings saved to disk using export_settings

    Parameters
    ----------
    settings_import_path : pathlike object
        Filepath to exported settings document
    settings_import_type : str, optional
        What type of settings to export (can be 'instrument' or 'all'), by default 'instrument'
    verbose : bool, optional
        Whether to print information to terminal, by default False

    Returns
    -------
    dict
        A dictionary containing the function names as keys of internal dictionaries, 
        with key:value pairs for each parameter name:value in that function.

    """
    allList = ['all', ':', 'both', 'any']
    if settings_import_type.lower() not in allList:
        # if just a single settings dict is desired
        with open(settings_import_path, 'r') as f:
            settingsDict = json.load(f)
    else:
        # Either a directory or list
        if isinstance(settings_import_path, (list, tuple)):
            for setPath in settings_import_path:
                pass
        else:
            settings_import_path = sprit_utils._checkifpath(settings_import_path)
            if not settings_import_path.is_dir():
                raise RuntimeError(f'settings_import_type={settings_import_type}, but settings_import_path is not list/tuple or filepath to directory')
            else:
                instFile = settings_import_path.glob('*.inst')
                procFile = settings_import_path.glob('*.proc')
    return settingsDict


# Define input parameters
def input_params(input_data,
                site='HVSRSite',
                project=None,
                network='AM', 
                station='NONE', 
                location='00', 
                channels=['EHZ', 'EHN', 'EHE'],
                acq_date = None,
                starttime = None,
                endtime = None,
                tzone = 'UTC',
                xcoord = -88.229,
                ycoord =  40.101,
                elevation = 225,
                input_crs = 'EPSG:4326', #Default is WGS84,#4269 is NAD83
                output_crs = None,
                elev_unit = 'meters',
                depth = 0,
                instrument = "Seismometer",
                metadata = None,
                hvsr_band = DEFAULT_BAND,
                peak_freq_range = DEFAULT_BAND,
                processing_parameters={},
                verbose=False
                ):
    """Function for designating input parameters for reading in and processing data
    
    Parameters
    ----------
    input_data : str or pathlib.Path object
        Filepath of data. This can be a directory or file, but will need to match with what is chosen later as the source parameter in fetch_data()
    site : str, default="HVSR Site"
        Site name as designated by user for ease of reference. Used for plotting titles, filenames, etc.
    project : str, default=None
        A prefix that may be used to create unique identifiers for each site. 
        The identifier created is saved as the ['HVSR_ID'] attribute of the HVSRData object,
        and is equivalent to the following formatted string:
        f"{project}-{acq_date.strftime("%Y%m%d")}-{starttime.strftime("%H%M")}-{station}".
    network : str, default='AM'
        The network designation of the seismometer. This is necessary for data from Raspberry Shakes. 'AM' is for Amateur network, which fits Raspberry Shakes.
    station : str, default='None'
        The station name of the seismometer. This is necessary for data from Raspberry Shakes.
    location : str, default='00'
        Location information of the seismometer.
    channels : list, default=['EHZ', 'EHN', 'EHE']
        The three channels used in this analysis, as a list of strings. Preferred that Z component is first, but not necessary
    acq_date : str, int, date object, or datetime object
        If string, preferred format is 'YYYY-MM-DD'. 
        If int, this will be interpreted as the time_int of year of current year (e.g., 33 would be Feb 2 of current year)
        If date or datetime object, this will be the date. Make sure to account for time change when converting to UTC (if UTC is the following time_int, use the UTC time_int).
    starttime : str, time object, or datetime object, default='00:00:00.00'
        Start time of data stream. This is necessary for Raspberry Shake data in 'raw' form, or for trimming data. Format can be either 'HH:MM:SS.micros' or 'HH:MM' at minimum.
    endtime : str, time obejct, or datetime object, default='23:59:99.99'
        End time of data stream. This is necessary for Raspberry Shake data in 'raw' form, or for trimming data. Same format as starttime.
    tzone : str or int, default = 'UTC'
        Timezone of input data. If string, 'UTC' will use the time as input directly. Any other string value needs to be a TZ identifier in the IANA database, a wikipedia page of these is available here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones.
        If int, should be the int value of the UTC offset (e.g., for American Eastern Standard Time: -5). 
        This is necessary for Raspberry Shake data in 'raw' format.
    xcoord : float, default=-88.2290526
        Longitude (or easting, or, generally, X coordinate) of data point, in Coordinate Reference System (CRS) designated by input_crs. Currently only used in table output, but will likely be used in future for mapping/profile purposes.
    ycoord : float, default=40.1012122
        Latitute (or northing, or, generally, X coordinate) of data point, in Coordinate Reference System (CRS) designated by input_crs. Currently only used in table output, but will likely be used in future for mapping/profile purposes.
    input_crs : str or other format read by pyproj, default='EPSG:4326'
        Coordinate reference system of input data, as used by pyproj.CRS.from_user_input()
    output_crs : str or other format read by pyproj, default='EPSG:4326'
        Coordinate reference system to which input data will be transformed, as used by pyproj.CRS.from_user_input()
    elevation : float, default=755
        Surface elevation of data point. Not currently used (except in table output), but will likely be used in the future.
    depth : float, default=0
        Depth of seismometer. Not currently used, but will likely be used in the future.
    instrument : str {'Raspberry Shake', "Tromino"}
        Instrument from which the data was acquired. 
    metadata : str or pathlib.Path object, default=None
        Filepath of metadata, in format supported by obspy.read_inventory. If default value of None, will read from resources folder of repository (only supported for Raspberry Shake).
    hvsr_band : list, default=[0.1, 50]
        Two-element list containing low and high "corner" frequencies (in Hz) for processing. This can specified again later.
    peak_freq_range : list or tuple, default=[0.1, 50]
        Two-element list or tuple containing low and high frequencies (in Hz) that are used to check for HVSR Peaks. This can be a tigher range than hvsr_band, but if larger, it will still only use the hvsr_band range.
    processing_parameters={} : dict or filepath, default={}
        If filepath, should point to a .proc json file with processing parameters (i.e, an output from sprit.export_settings()). 
        Note that this only applies to parameters for the functions: 'fetch_data', 'remove_noise', 'generate_psds', 'process_hvsr', 'check_peaks', and 'get_report.'
        If dictionary, dictionary containing nested dictionaries of function names as they key, and the parameter names/values as key/value pairs for each key. 
        If a function name is not present, or if a parameter name is not present, default values will be used.
        For example: 
            `{ 'fetch_data' : {'source':'batch', 'data_export_path':"/path/to/trimmed/data", 'data_export_format':'mseed', 'detrend':'spline', 'plot_input_stream':True, 'verbose':False, kwargs:{'kwargskey':'kwargsvalue'}} }`
    verbose : bool, default=False
        Whether to print output and results to terminal

    Returns
    -------
    params : sprit.HVSRData
        sprit.HVSRData class containing input parameters, including data file path and metadata path. This will be used as an input to other functions. If batch processing, params will be converted to batch type in fetch_data() step.

    """
    orig_args = locals().copy() #Get the initial arguments
    # Record starting time for this function run
    start_time = datetime.datetime.now()

    # Record any updates that are made to input_params based
    update_msg = []
    
    # Reformat times
    # Date will come out of this block as a string of datetime.date
    if acq_date is None:
        date = str(datetime.datetime.now().date())
    elif type(acq_date) is datetime.datetime:
        date = str(acq_date.date())
    elif type(acq_date) is datetime.date:
        date=str(acq_date)
    elif type(acq_date) is str:
        monthStrs = {'jan':1, 'january':1,
                    'feb':2, 'february':2,
                    'mar':3, 'march':3,
                    'apr':4, 'april':4,
                    'may':5,
                    'jun':6, 'june':6,
                    'jul':7, 'july':7,
                    'aug':8, 'august':8,
                    'sep':9, 'sept':9, 'september':9,
                    'oct':10,'october':10, 
                    'nov':11,'november':11,
                    'dec':12,'december':12}

        spelledMonth = False
        for m in monthStrs.keys():
            acq_date = acq_date.lower()
            if m in acq_date:
                spelledMonth = True
                break

        if spelledMonth is not False:
            month = monthStrs[m]

        if '/' in acq_date:
            sep = '/'
        elif '.' in acq_date:
            sep='.'
        elif ' ' in acq_date:
            sep = ' '
            acq_date = acq_date.replace(',', '')
        else:
            sep = '-'

        acq_date = acq_date.split(sep)
        if len(acq_date[2]) > 2: #American format
            date = '{}-{}-{}'.format(acq_date[2], acq_date[0], acq_date[1])
        else: #international format, one we're going to use
            date = '{}-{}-{}'.format(acq_date[0], acq_date[1], acq_date[2])     
    elif type(acq_date) is int:
        year=datetime.datetime.today().year
        date = str((datetime.datetime(year, 1, 1) + datetime.timedelta(acq_date - 1)).date())

    # Starttime will be standardized as string, then converted to UTCDateTime
    # If not specified, will be set to 00:00 of current UTC date
    if starttime is None:
        starttime = obspy.UTCDateTime(NOWTIME.year, NOWTIME.month, NOWTIME.day, 0, 0, 0, 0)
    elif type(starttime) is str:
        if 'T' in starttime:
            #date=starttime.split('T')[0]
            starttime = starttime.split('T')[1]
        else:
            pass
            #starttime = date+'T'+starttime
    elif type(starttime) is datetime.datetime:
        #date = str(starttime.date())
        starttime = str(starttime.time())
        ###HERE IS NEXT
    elif type(starttime) is datetime.time():
        starttime = str(starttime)
    
    if not isinstance(starttime, obspy.UTCDateTime):
        starttime = str(date)+"T"+str(starttime)
    starttime = obspy.UTCDateTime(sprit_utils._format_time(starttime, tzone=tzone))
    
    if not isinstance(orig_args['starttime'], obspy.UTCDateTime) or starttime != orig_args['starttime']:
        update_msg.append(f"\t\tstarttime was updated from {orig_args['starttime']} to {starttime}")

    # endtime will be standardized as string, then converted to UTCDateTime
    # If not specified, will be set to 23:59:59.999999 of current UTC date
    if endtime is None:
        endtime = obspy.UTCDateTime(NOWTIME.year, NOWTIME.month, NOWTIME.day, 23, 59, 59, 999999)
    elif type(endtime) is str:
        if 'T' in endtime:
            date=endtime.split('T')[0]
            endtime = endtime.split('T')[1]
    elif type(endtime) is datetime.datetime:
        date = str(endtime.date())
        endtime = str(endtime.time())
    elif type(endtime) is datetime.time():
        endtime = str(endtime)

    if not isinstance(endtime, obspy.UTCDateTime):
        endtime = str(date)+"T"+str(endtime)
    endtime = obspy.UTCDateTime(sprit_utils._format_time(endtime, tzone=tzone))

    if not isinstance(orig_args['starttime'], obspy.UTCDateTime) or starttime != orig_args['starttime']:
        update_msg.append(f"\t\tendtime was updated from {orig_args['endtime']} to {endtime}")

    acq_date = datetime.date(year=int(date.split('-')[0]), month=int(date.split('-')[1]), day=int(date.split('-')[2]))
    if acq_date != orig_args['acq_date']:
        update_msg.append(f"\t\tacq_date was updated from {orig_args['acq_date']} to {acq_date}")

    raspShakeInstNameList = ['raspberry shake', 'shake', 'raspberry', 'rs', 'rs3d', 'rasp. shake', 'raspshake']
    
    # If no CRS specified, assume WGS84
    if input_crs is None or input_crs == '':
        if verbose:
            update_msg.append(f"\t\tNo value specified for input_crs, assuming WGS84 (EPSG:4326)")
        input_crs = 'EPSG:4326'
    
    if output_crs is None:
        if verbose:
            update_msg.append(f"\t\tNo value specified for output_crs, using same coordinate system is input_crs: ({input_crs})")
        output_crs = input_crs

    if xcoord is None or xcoord == '':
        xcoord = 0.0
    else:
        xcoord = float(xcoord)
    
    if ycoord is None or ycoord == '':
        ycoord = 0.0
    else:
        ycoord = float(ycoord)
    # Get CRS Objects
    input_crs = CRS.from_user_input(input_crs)
    output_crs = CRS.from_user_input(output_crs)

    # We always need latitude and longitude, so specify this regadless of in/output crs
    # Get WGS84 coordinates (needed for inventory)
    wgs84_crs = CRS.from_user_input('EPSG:4326')
    wgs84_transformer = Transformer.from_crs(input_crs, wgs84_crs, always_xy=True)
    xcoord_wgs84, ycoord_wgs84 = wgs84_transformer.transform(xcoord, ycoord)

    xcoord_wgs84 = round(xcoord_wgs84, 7)
    ycoord_wgs84 = round(ycoord_wgs84, 7)

    update_msg.append(f"\t\tLongitude ({xcoord_wgs84}) and Latitude ({ycoord_wgs84}) calculated for compatibility with obspy.")

    # Get coordinates in CRS specified in output_crs
    xcoordIN = xcoord
    ycoordIN = ycoord
    coord_transformer = Transformer.from_crs(input_crs, output_crs, always_xy=True)
    xcoord, ycoord = coord_transformer.transform(xcoordIN, ycoordIN)

    if isinstance(processing_parameters, dict):
        pass
    else:
        processing_parameters = sprit_utils._checkifpath(processing_parameters)
        processing_parameters = import_settings(processing_parameters, settings_import_type='processing', verbose=verbose)

    # Get elevation in meters
    if str(elev_unit).lower() in ['feet', 'foot', 'ft', 'f', 'imperial', 'imp', 'american', 'us']:
        elevation = elevation * 0.3048
        elev_unit = 'meters'
        update_msg.append(f"\t\t Elevations are automatically converted to meters during processing")
        update_msg.append(f"\t\t elevation was updated to {elevation} m (from {orig_args['elevation']} ft)")
        update_msg.append(f"\t\t elev_unit was also updated to {elev_unit} (from {orig_args['elev_unit']})")
    
    # Create a unique identifier for each site
    if project is None:
        proj_id = ''
    else:
        proj_id = str(project)+'-'
    
    hvsr_id = f"{proj_id}{acq_date.strftime('%Y%m%d')}-{starttime.strftime('%H%M')}-{station}"
    update_msg.append(f"\t\thvsr_id generated from input parameters: {hvsr_id}")

    #Add key/values to input parameter dictionary for use throughout the rest of the package
    inputParamDict = {'site':site, 'project':project, 'hvsr_id':hvsr_id, 'network':network, 'station':station,'location':location, 'channels':channels,
                      'net':network,'sta':station, 'loc':location, 'cha':channels, 'instrument':instrument,
                      'acq_date':acq_date,'starttime':starttime,'endtime':endtime, 'timezone':'UTC', #Will be in UTC by this point
                      'xcoord_input':xcoordIN, 'ycoord_input': ycoordIN ,'xcoord':xcoord, 'ycoord':ycoord, 'longitude':xcoord_wgs84,'latitude':ycoord_wgs84,
                      'elevation':elevation, 'elev_unit':elev_unit, 'input_crs':input_crs, 'output_crs':output_crs,
                      'depth':depth, 'input_data': input_data, 'metadata':metadata, 'hvsr_band':hvsr_band, 'peak_freq_range':peak_freq_range,
                      'processing_parameters':processing_parameters, 'processing_status':{'input_params_status':True, 'overall_status':True}
                      }
    

    #Replace any default parameter settings with those from json file of interest, potentially
    instrument_settings_dict = {}
    if pathlib.Path(str(instrument)).exists():
        instrument_settings = import_settings(settings_import_path=instrument, settings_import_type='instrument', verbose=verbose)
        input_params_args = inspect.getfullargspec(input_params).args
        input_params_args.append('net')
        input_params_args.append('sta')
        for k, settings_value in instrument_settings.items():
            if k in input_params_args:
                instrument_settings_dict[k] = settings_value
        inputParamDict['instrument_settings'] = inputParamDict['instrument']
        inputParamDict.update(instrument_settings_dict)
    
    if str(instrument).lower() in raspShakeInstNameList:
        if metadata is None or metadata=='':
            metadata = pathlib.Path(str(importlib.resources.files('sprit'))).joinpath('resources').joinpath("rs3dv5plus_metadata.inv").as_posix()
            inputParamDict['metadata'] = metadata

    for settingName in instrument_settings_dict.keys():
        if settingName in inputParamDict.keys():
            inputParamDict[settingName] = instrument_settings_dict[settingName]

    if verbose:
        print('Gathering input parameters (input_params())')
        for key, value in inputParamDict.items():
            print('\t  {}={}'.format(key, value))
        print()

        update_msg.insert(0, '\tThe following parameters were modified from the raw input:')
        for msg_line in update_msg:
            print(msg_line)
        print()
        
    #Format everything nicely
    params = sprit_utils._make_it_classy(inputParamDict)
    params['processing_status']['input_params_status'] = True
    params = sprit_utils._check_processing_status(params, start_time=start_time, func_name=inspect.stack()[0][3], verbose=verbose)
    return params


# Plot Azimuth data
def plot_azimuth(hvsr_data, fig=None, ax=None, show_azimuth_peaks=False, interpolate_azimuths=True, show_azimuth_grid=False, show_plot=True, **plot_azimuth_kwargs):
    """Function to plot azimuths when azimuths are calculated

    Parameters
    ----------
    hvsr_data : HVSRData or HVSRBatch
        HVSRData that has gone through at least the sprit.fetch_data() step, and before sprit.generate_psds()
    show_azimuth_peaks : bool, optional
        Whether to display the peak value at each azimuth calculated on the chart, by default False
    interpolate_azimuths : bool, optional
        Whether to interpolate the azimuth data to get a smoother plot. 
        This is just for visualization, does not change underlying data.
        It takes a lot of time to process the data, but interpolation for vizualization can happen fairly fast. By default True.
    show_azimuth_grid : bool, optional
        Whether to display the grid on the chart, by default False

    Returns
    -------
    matplotlib.Figure, matplotlib.Axis
        Figure and axis of resulting azimuth plot
    """
    orig_args = locals().copy() #Get the initial arguments

    if isinstance(hvsr_data, HVSRBatch):
        #If running batch, we'll loop through each site
        for site_name in hvsr_data.keys():
            args = orig_args.copy() #Make a copy so we don't accidentally overwrite
            individual_params = hvsr_data[site_name] #Get what would normally be the "params" variable for each site
            args['hvsr_data'] = individual_params #reset the params parameter we originally read in to an individual site params
            if hvsr_data[site_name]['processing_status']['overall_status']:
                try:
                    hvsr_data['Azimuth_Fig'] = __plot_azimuth_batch(**args) #Call another function, that lets us run this function again
                except:
                    print(f"ERROR: {site_name} will not have azimuths plotted.")
    elif isinstance(hvsr_data, HVSRData):
        if fig is None:
            fig = plt.figure()

        hvsr_band = hvsr_data.hvsr_band

        azDataList = []
        azExtraDataList = []

        for k in sorted(hvsr_data.hvsr_az.keys()):
            currData = hvsr_data.hvsr_az[k]
            azDataList.append(currData)
            azExtraDataList.append(currData)
        
            
        freq = hvsr_data.x_freqs['Z'].tolist()[1:]
        a = np.deg2rad(np.array(sorted(hvsr_data.hvsr_az.keys())).astype(float))
        b = a + np.pi

        z = np.array(azDataList)
        z2 =np.array(azExtraDataList)

        def interp_along_theta(orig_array, orig_ind):
            newArrayList = []
            for a1 in orig_array.T:
                # Resample the array along the first dimension using numpy.interp
                newZ = np.interp(
                    np.linspace(np.pi/180, np.pi, 180),  # New indices
                    orig_ind,  # Original indices
                    a1)
                newArrayList.append(newZ)
            return np.array(newArrayList).T

        if 'plot_type' in plot_azimuth_kwargs.keys():
            if 'i' in plot_azimuth_kwargs['plot_type']:
                interpolate_azimuths = True
            if '-i' in plot_azimuth_kwargs['plot_type']:
                interpolate_azimuths = False


        if interpolate_azimuths:
            z = interp_along_theta(z, a)
            z2 = interp_along_theta(z2, a)

            a =  np.linspace(np.deg2rad(1), np.pi, 180)
            b = (a + np.pi).tolist()
            a = a.tolist()

        r, th = np.meshgrid(freq, a)
        r2, th2 = np.meshgrid(freq, b)

        # Set up plot
        if ax is None:
            ax = plt.subplot(polar=True)
            plt.title(hvsr_data['site'])

        else:
            plt.sca(ax)

        plt.semilogy()
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        plt.xlim([0, np.pi*2])
        plt.ylim([hvsr_band[1], hvsr_band[0]])

        # Plot data
        pmesh1 = plt.pcolormesh(th, r, z, cmap = 'jet')
        pmesh2 = plt.pcolormesh(th2, r2, z2, cmap = 'jet')

        azList = ['azimuth', 'az', 'a', 'radial', 'r']
        azOpts = []
        if 'plot_type' in plot_azimuth_kwargs.keys():
            if type(plot_azimuth_kwargs['plot_type']) is str:
                ptList = plot_azimuth_kwargs['plot_type'].split(' ')
            elif isinstance(plot_azimuth_kwargs['plot_type'], (list, tuple)):
                ptList = list(plot_azimuth_kwargs['plot_type'])

            for az in azList:
                if az in ptList:
                    azOpts = [item.lower() for item in ptList[ptList.index(az)+1:]]

        if 'p' in azOpts:
            show_azimuth_peaks = True

        if 'g' in azOpts:
            show_azimuth_grid = True

        if show_azimuth_peaks:
            peakVals = []
            peakThetas = []
            for k in sorted(hvsr_data.hvsr_az.keys()):
                peakVals.append(hvsr_data.BestPeak[k]['f0'])
                peakThetas.append(int(k))
            peakThetas = peakThetas + (180 + np.array(peakThetas)).tolist()
            peakThetas = np.deg2rad(peakThetas).tolist()
            peakVals = peakVals + peakVals
            peakVals.append(peakVals[0])
            peakThetas.append(peakThetas[0]+(np.pi*2))
            peakThetas.append(peakThetas[1]+(np.pi*2))

            peakThetas = (np.convolve(peakThetas, np.ones(2), 'full')/2).tolist()[1:-1]
            newThetas = []
            newVals = []
            for i, p in enumerate(peakThetas):
                newThetas.append(p)
                newThetas.append(p)
                if i == 0:
                    newVals.append(peakVals[-1])
                    newVals.append(peakVals[-1])
                else:
                    newVals.append(peakVals[i])
                    newVals.append(peakVals[i])

            newThetas.insert(0, newThetas[-1])
            newThetas.pop()

            newVals.append(newVals[0])
            newThetas.append(newThetas[0])

            #peakThetas = newThetas
            #peakVals = newVals
            if len(peakThetas) >= 20:
                alphaVal = 0.2
            else:
                alphaVal = 0.9 - (19/28) 
            plt.scatter(peakThetas, peakVals, marker='h', facecolors='none', edgecolors='k', alpha=alphaVal)
        #plt.plot(a, r, ls='none', color = 'k') 

        if show_azimuth_grid:
            plt.grid(visible=show_azimuth_grid, which='both', alpha=0.5)
            plt.grid(visible=show_azimuth_grid, which='major', c='k', linewidth=1, alpha=1)
        #plt.colorbar(pmesh1)
        if show_plot:
            plt.show()

        hvsr_data['AzimuthFig'] = fig
    else:
        warnings.warn(f'hvsr_data must be of type HVSRData or HVSRBatch, not {type(hvsr_data)}')
    return fig, ax


# Main function for plotting results
def plot_hvsr(hvsr_data, plot_type=DEFAULT_PLOT_STR, azimuth='HV', use_subplots=True, fig=None, ax=None, return_fig=False,  plot_engine='matplotlib', save_dir=None, save_suffix='', show_legend=False, show_plot=True, close_figs=False, clear_fig=True,**kwargs):
    """Function to plot HVSR data

    Parameters
    ----------
    hvsr_data : dict                  
        Dictionary containing output from process_hvsr function
    plot_type : str or list, default = 'HVSR ann p C+ ann p SPEC ann p'
        The plot_type of plot(s) to plot. If list, will plot all plots listed
        - 'HVSR' - Standard HVSR plot, including standard deviation. Options are included below:
            - 'p' shows a vertical dotted line at frequency of the "best" peak
            - 'ann' annotates the frequency value of of the "best" peak
            - 'all' shows all the peaks identified in check_peaks() (by default, only the max is identified)
            - 't' shows the H/V curve for all time windows
            - 'tp' shows all the peaks from the H/V curves of all the time windows
            - 'fr' shows the window within which SpRIT will search for peak frequencies, as set by peak_freq_range
            - 'test' shows a visualization of the results of the peak validity test(s). Examples:
                - 'tests' visualizes the results of all the peak tests (not the curve tests)
                - 'test12' shows the results of tests 1 and 2.
                    - Append any number 1-6 after 'test' to show a specific test result visualized
        - 'COMP' - plot of the PPSD curves for each individual component ("C" also works)
            - '+' (as a suffix in 'C+' or 'COMP+') plots C on a plot separate from HVSR (C+ is default, but without + will plot on the same plot as HVSR)
            - 'p' shows a vertical dotted line at frequency of the "best" peak
            - 'ann' annotates the frequency value of of the "best" peak
            - 'all' shows all the peaks identified in check_peaks() (by default, only the max is identified)
            - 't' shows the H/V curve for all time windows
        - 'SPEC' - spectrogram style plot of the H/V curve over time
            - 'p' shows a horizontal dotted line at the frequency of the "best" peak
            - 'ann' annotates the frequency value of the "best" peak
            - 'all' shows all the peaks identified in check_peaks()
            - 'tp' shows all the peaks of the H/V curve at all time windows
        - 'AZ' - circular plot of calculated azimuthal HV curves, similar in style to SPEC plot.
            - 'p' shows a point at each calculated (not interpolated) azimuth peak
            - 'g' shows grid lines at various angles
            - 'i' interpolates so that there is an interpolated azimuth at each degree interval (1 degree step)
                This is the default, so usually 'i' is not needed.
            - '-i' prohibits interpolation (only shows the calculated azimuths, as determined by azimuth_angle (default = 30))
    azimuth : str, default = 'HV'
        What 'azimuth' to plot, default being standard N E components combined
    use_subplots : bool, default = True
        Whether to output the plots as subplots (True) or as separate plots (False)
    fig : matplotlib.Figure, default = None
        If not None, matplotlib figure on which plot is plotted
    ax : matplotlib.Axis, default = None
        If not None, matplotlib axis on which plot is plotted
    return_fig : bool
        Whether to return figure and axis objects
    plot_engine : str, default='Matplotlib'
        Which engine to use for plotting. Both "matplotlib" and "plotly" are acceptable. For shorthand, 'mpl', 'm' also work for matplotlib; 'plty' or 'p' also work for plotly. Not case sensitive.
    save_dir : str or None
        Directory in which to save figures
    save_suffix : str
        Suffix to add to end of figure filename(s), if save_dir is used
    show_legend : bool, default=False
        Whether to show legend in plot
    show_plot : bool
        Whether to show plot
    close_figs : bool, default=False
        Whether to close figures before plotting
    clear_fig : bool, default=True
        Whether to clear figures before plotting
    **kwargs : keyword arguments
        Keyword arguments for matplotlib.pyplot

    Returns
    -------
    fig, ax : matplotlib figure and axis objects
        Returns figure and axis matplotlib.pyplot objects if return_fig=True, otherwise, simply plots the figures
    """
    orig_args = locals().copy() #Get the initial arguments
    if isinstance(hvsr_data, HVSRBatch):
        #If running batch, we'll loop through each site
        for site_name in hvsr_data.keys():
            args = orig_args.copy() #Make a copy so we don't accidentally overwrite
            individual_params = hvsr_data[site_name] #Get what would normally be the "params" variable for each site
            args['hvsr_results'] = individual_params #reset the params parameter we originally read in to an individual site params
            if hvsr_data[site_name]['processing_status']['overall_status']:
                try:
                    __hvsr_plot_batch(**args) #Call another function, that lets us run this function again
                except:
                    print(f"{site_name} not able to be plotted.")

        return

    mplList = ['matplotlib', 'mpl', 'm']
    plotlyList = ['plotly', 'plty', 'p']

    if plot_engine.lower() in plotlyList:
        plotlyFigure = sprit_plot.plot_results_plotly(hvsr_data, plot_string=plot_type, azimuth=azimuth,
                                            results_fig=fig, return_fig=return_fig, use_figure_widget=False,
                                            show_results_plot=show_plot)
        if return_fig:
            return plotlyFigure
    else: #plot_engine.lower() in mplList or any other value not in plotly list
        if clear_fig and fig is not None and ax is not None: #Intended use for tkinter
            #Clear everything
            for key in ax:
                ax[key].clear()
            for t in fig.texts:
                del t
            fig.clear()
        if close_figs:
            plt.close('all')

        # The possible identifiers in plot_type for the different kind of plots
        hvsrList = ['hvsr', 'hv', 'h']
        compList = ['c', 'comp', 'component', 'components']
        specgramList = ['spec', 'specgram', 'spectrogram']
        azList = ['azimuth', 'az', 'a', 'radial', 'r']

        hvsrInd = np.nan
        compInd = np.nan
        specInd = np.nan
        azInd = np.nan

        plot_type = plot_type.replace(',', '')
        kList = plot_type.split(' ')
        for i, k in enumerate(kList):
            kList[i] = k.lower()

        # Get the plots in the right order, no matter how they were input (and ensure the right options go with the right plot)
        # HVSR index
        if len(set(hvsrList).intersection(kList)):
            for i, hv in enumerate(hvsrList):
                if hv in kList:
                    hvsrInd = kList.index(hv)
                    break
        # Component index
        #if len(set(compList).intersection(kList)):
        for i, c in enumerate(kList):
            if '+' in c and c[:-1] in compList:
                compInd = kList.index(c)
                break
            
        # Specgram index
        if len(set(specgramList).intersection(kList)):
            for i, sp in enumerate(specgramList):
                if sp in kList:
                    specInd = kList.index(sp)
                    break        

        # Azimuth index
        if len(set(azList).intersection(kList)):
            for i, sp in enumerate(azList):
                if sp in kList:
                    azInd = kList.index(sp)
                    break        

        
        # Get indices for all plot type indicators
        indList = [hvsrInd, compInd, specInd, azInd]
        indListCopy = indList.copy()
        plotTypeList = ['hvsr', 'comp', 'spec', 'az']

        plotTypeOrder = []
        plotIndOrder = []

        # Get lists with first and last indices of the specifiers for each plot
        lastVal = 0
        while lastVal != 99:
            firstInd = np.nanargmin(indListCopy)
            plotTypeOrder.append(plotTypeList[firstInd])
            plotIndOrder.append(indList[firstInd])
            lastVal = indListCopy[firstInd]
            indListCopy[firstInd] = 99  #just a high number

        plotTypeOrder.pop()
        plotIndOrder[-1] = len(kList)
        
        # set up subplots
        figLayout = 'constrained'
        figWidth = 6
        figHeight = 4
        figdpi = 220

        for i, p in enumerate(plotTypeOrder):
            pStartInd = plotIndOrder[i]
            pEndInd = plotIndOrder[i+1]
            plotComponents = kList[pStartInd:pEndInd]

            if use_subplots and i == 0 and fig is None and ax is None:
                mosaicPlots = []
                for pto in plotTypeOrder:
                    if pto == 'az':
                        for i, subp in enumerate(mosaicPlots):
                            if (subp[0].lower() == 'hvsr' or subp[0].lower() == 'comp') and len([item for item in plotTypeOrder if item != "hvsr"]) > 0:
                                mosaicPlots[i].append(subp[0])
                                mosaicPlots[i].append(subp[0])
                            else:
                                mosaicPlots[i].append(subp[0])
                                mosaicPlots[i].append(pto)
                    else:
                        mosaicPlots.append([pto])
                perSubPDict = {}
                if 'az' in plotTypeOrder:
                    perSubPDict['az'] = {'projection':'polar'}
                fig, ax = plt.subplot_mosaic(mosaicPlots, per_subplot_kw=perSubPDict, 
                                             layout=figLayout, figsize=(figWidth, figHeight), dpi=figdpi)
                axis = ax[p]
            elif use_subplots:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore") #Often warns about xlim when it is not an issue
                    if hasattr(ax, '__len__'):#print(dir(ax), ax, len(ax))
                        ax[p].clear()
                        axis = ax[p]
            else:
                fig, axis = plt.subplots(figsize=(figWidth, figHeight), dpi=figdpi)

            if p == 'hvsr':
                kwargs['subplot'] = p
                fig, ax[p] = _plot_hvsr(hvsr_data, fig=fig, ax=axis, plot_type=plotComponents, azimuth=azimuth, xtype='x_freqs', show_legend=show_legend, axes=ax, **kwargs)
            elif p == 'comp':
                plotComponents[0] = plotComponents[0][:-1]
                kwargs['subplot'] = p
                minY = 99999 # Start high
                maxY = -99999 # Start low
                
                for key in hvsr_data.psd_raw.keys():
                    if min(hvsr_data.ppsd_std_vals_m[key]) < minY:
                        minY = min(hvsr_data.ppsd_std_vals_m[key])
                    if max(hvsr_data.ppsd_std_vals_m[key]) > maxY:
                        maxY = max(hvsr_data.ppsd_std_vals_m[key])
                yRange = maxY - minY
                compYlim = [float(minY - (yRange*0.05)), float(maxY + (yRange * 0.05))]
                compYlim.reverse()
                compKwargs = {'ylim':compYlim}
                compKwargs.update(kwargs)
                fig, ax[p] = _plot_hvsr(hvsr_data, fig=fig, ax=axis, plot_type=plotComponents, azimuth=azimuth, xtype='x_freqs', show_legend=show_legend, axes=ax, **kwargs)
            elif p == 'spec':
                plottypeKwargs = {}
                for c in plotComponents:
                    plottypeKwargs[c] = True
                kwargs.update(plottypeKwargs)
                _plot_specgram_hvsr(hvsr_data, fig=fig, ax=axis, azimuth=azimuth, colorbar=False, **kwargs)
            elif p == 'az':
                kwargs['plot_type'] = plotComponents
                hvsr_data['Azimuth_fig'] = plot_azimuth(hvsr_data, fig=fig, ax=axis, **kwargs)
            else:
                warnings.warn('Plot type {p} not recognized', UserWarning)   

        windowsUsedStr = f"{hvsr_data['hvsr_windows_df']['Use'].astype(bool).sum()}/{hvsr_data['hvsr_windows_df'].shape[0]} windows used"
        winText = fig.text(x=1, y=0.0, s=windowsUsedStr, ha='right', va='bottom', fontsize='xx-small',
                bbox=dict(facecolor='w', edgecolor=None, linewidth=0, alpha=1, pad=-1))
        winText.set_in_layout(False)
        
        if len(plotTypeOrder)>1:
            matplotlib.rcParams["figure.constrained_layout.h_pad"] = 0.075
        #if use_subplots:
        #    fig.subplots_adjust()#.set(h_pad=0.075, hspace=-5)
        if show_plot:
            fig.canvas.draw()
            
        if return_fig:
            return fig

    return


# Main function for processing HVSR Curve
def process_hvsr(hvsr_data, horizontal_method=None, smooth=True, freq_smooth='konno ohmachi', 
                 f_smooth_width=40, resample=True, 
                 outlier_curve_percentile_threshold=False, azimuth=None, verbose=False):
    """Process the input data and get HVSR data
    
    This is the main function that uses other (private) functions to do 
    the bulk of processing of the HVSR data and the data quality checks.

    Parameters
    ----------
    hvsr_data  : HVSRData or HVSRBatch
        Data object containing all the parameters input and generated by the user (usually, during sprit.input_params(), sprit.fetch_data(), sprit.generate_psds() and/or sprit.remove_noise()).
    horizontal_method  : int or str, default=3
        Method to use for combining the horizontal components. Default is 3) Geometric Mean
            0) (not used) 
            1) 'Diffuse field assumption'   H = √( (eie_E + eie_N) / eie_Z), eie = equal interval energy
            2) 'Arithmetic Mean'            H ≡ (HN + HE)/2
            3) 'Geometric Mean'             H ≡ √(HN · HE), recommended by the SESAME project (2004)
            4) 'Vector Summation'           H ≡ √(HN^2 + HE^2)
            5) 'Quadratic Mean'             H ≡ √(HN^2 + HE^2)/2
            6) 'Maximum Horizontal Value'   H ≡ max {HN, HE}
            7) 'Minimum Horizontal Valey'   H ≡ min {HN, HE}
            8) 'Single Azimuth'             H = H2·cos(az) + H1·sin(az)
    smooth  : bool, default=True
        bool or int may be used. 
            If True, default to smooth H/V curve to using savgoy filter with window length of 51 (works well with default resample of 1000 pts)
            If int, the length of the window in the savgoy filter.
    freq_smooth : str {'konno ohmachi', 'constant', 'proportional'}
        Which frequency smoothing method to use. By default, uses the 'konno ohmachi' method.
            - The Konno & Ohmachi method uses the obspy.signal.konnoohmachismoothing.konno_ohmachi_smoothing() function: https://docs.obspy.org/packages/autogen/obspy.signal.konnoohmachismoothing.konno_ohmachi_smoothing.html
            - The constant method uses a window of constant length f_smooth_width
            - The proportional method uses a window the percentage length of the frequncy steps/range (f_smooth_width now refers to percentage)
        See here for more information: https://www.geopsy.org/documentation/geopsy/hv-processing.html
    f_smooth_width : int, default = 40
        - For 'konno ohmachi': passed directly to the bandwidth parameter of the konno_ohmachi_smoothing() function, determines the width of the smoothing peak, with lower values resulting in broader peak. Must be > 0.
        - For 'constant': the size of a triangular smoothing window in the number of frequency steps
        - For 'proportional': the size of a triangular smoothing window in percentage of the number of frequency steps (e.g., if 1000 frequency steps/bins and f_smooth_width=40, window would be 400 steps wide)
    resample  : bool, default = True
        bool or int. 
            If True, default to resample H/V data to include 1000 frequency values for the rest of the analysis
            If int, the number of data points to interpolate/resample/smooth the component psd/HV curve data to.
    outlier_curve_percentile_threshold : bool, float, default = False
        If False, outlier curve removal is not carried out here. 
        If True, defaults to 98 (98th percentile). 
        Otherwise, float of percentile used as outlier_threshold of remove_outlier_curve().
    azimuth : float, default = None
        The azimuth angle to use when method is single azimuth.
    verbose : bool, defualt=False
        Whether to print output to terminal

    Returns
    -------
        hvsr_out    : dict
            Dictionary containing all the information about the data, including input parameters

    """
    orig_args = locals().copy() #Get the initial arguments
    start_time = datetime.datetime.now()

    # Update with processing parameters specified previously in input_params, if applicable
    if 'processing_parameters' in hvsr_data.keys():
        if 'process_hvsr' in hvsr_data['processing_parameters'].keys():
            update_msg = []
            for k, v in hvsr_data['processing_parameters']['process_hvsr'].items():
                defaultVDict = dict(zip(inspect.getfullargspec(process_hvsr).args[1:], 
                                        inspect.getfullargspec(process_hvsr).defaults))
                # Manual input to function overrides the imported parameter values
                if (not isinstance(v, (HVSRData, HVSRBatch))) and (k in orig_args.keys()) and (orig_args[k]==defaultVDict[k]):
                    update_msg.append(f'\t\t{k} = {v} (previously {orig_args[k]})')
                    orig_args[k] = v
                                        
    horizontal_method = orig_args['horizontal_method']
    smooth = orig_args['smooth']
    freq_smooth = orig_args['freq_smooth']
    f_smooth_width = orig_args['f_smooth_width']
    resample = orig_args['resample']
    outlier_curve_percentile_threshold = orig_args['outlier_curve_percentile_threshold']
    verbose = orig_args['verbose']

    if (verbose and isinstance(hvsr_data, HVSRBatch)) or (verbose and not hvsr_data['batch']):
        if isinstance(hvsr_data, HVSRData) and hvsr_data['batch']:
            pass
        else:
            print('\nCalculating Horizontal/Vertical Ratios at all frequencies/time steps (process_hvsr())')
            print('\tUsing the following parameters:')
            for key, value in orig_args.items():
                if key=='hvsr_data':
                    pass
                else:
                    print('\t  {}={}'.format(key, value))
            print()

        if 'processing_parameters' in hvsr_data.keys() and 'process_hvsr' in hvsr_data['processing_parameters'].keys():
            if update_msg != []:
                update_msg.insert(0, '\tThe following parameters were updated using the processing_parameters attribute:')
                for msg_line in update_msg:
                    print(msg_line)
                print()
            
    # PROCESSING STARTS HERE (SEPARATE LOOP FOR BATCH)
    if isinstance(hvsr_data, HVSRBatch):
        #If running batch, we'll loop through each site
        hvsr_out = {}
        for site_name in hvsr_data.keys():
            args = orig_args.copy() #Make a copy so we don't accidentally overwrite
            args['hvsr_data'] = hvsr_data[site_name] #Get what would normally be the "hvsr_data" variable for each site
            if hvsr_data[site_name]['processing_status']['overall_status']:
                try:
                    hvsr_out[site_name] = __process_hvsr_batch(**args) #Call another function, that lets us run this function again
                except:
                    hvsr_out = hvsr_data
                    hvsr_out[site_name]['processing_status']['process_hvsr_status']=False
                    hvsr_out[site_name]['processing_status']['overall_status'] = False                    
            else:
                hvsr_out = hvsr_data
                hvsr_out[site_name]['processing_status']['process_hvsr_status']=False
                hvsr_out[site_name]['processing_status']['overall_status'] = False
        hvsr_out = HVSRBatch(hvsr_out, df_as_read=hvsr_data.input_df)
        hvsr_out = sprit_utils._check_processing_status(hvsr_out, start_time=start_time, func_name=inspect.stack()[0][3], verbose=verbose)
        return hvsr_out
    
    ppsds = hvsr_data['ppsds'].copy()#[k]['psd_values']
    ppsds = sprit_utils._check_xvalues(ppsds)

    methodList = ['<placeholder_0>', # 0
                    'Diffuse Field Assumption', # 1
                    'Arithmetic Mean', # 2
                    'Geometric Mean', # 3
                    'Vector Summation', # 4
                    'Quadratic Mean', # 5
                    'Maximum Horizontal Value', # 6
                    'Minimum Horizontal Value', # 7
                    'Single Azimuth' ] # 8
    x_freqs = {}
    x_periods = {}

    psdValsTAvg = {}
    stDev = {}
    stDevValsP = {}
    stDevValsM = {}
    psdRaw={}
    currTimesUsed={}
    hvsr_data['hvsr_windows_df']['Use'] = hvsr_data['hvsr_windows_df']['Use'].astype(bool)
    hvsrDF = hvsr_data['hvsr_windows_df']
    def move_avg(y, box_pts):
        #box = np.ones(box_pts)/box_pts
        box = np.hanning(box_pts)
        y_smooth = np.convolve(y, box, mode='same') / sum(box)
        return y_smooth

    resampleList = ['period_bin_centers', 'period_bin_left_edges', 'period_bin_right_edges', 'period_xedges',
                    'psd_frequencies', 'psd_periods']

    for k in ppsds.keys():
        #for ppsdk, ppsdv in ppsds[k].items():
            #print(ppsdk, isinstance(ppsdv, np.ndarray))
        #input_ppsds = ppsds[k]['psd_values'] #original, not used anymore
        input_ppsds = np.stack(hvsrDF['psd_values_'+k].values)

        #currPPSDs = hvsrDF['psd_values_'+k][hvsrDF['Use']].values
        #used_ppsds = np.stack(currPPSDs)

        xValMin_per = np.round(1/hvsr_data['hvsr_band'][1], 4)
        xValMax_per = np.round(1/hvsr_data['hvsr_band'][0], 4)
        
        # If resampling has been selected...
        if resample is True or type(resample) is int or type(resample) is float:
            if resample is True:
                resample = 1000 #Default smooth value

            # Resample period bin values
            x_periods[k] = np.logspace(np.log10(xValMin_per), np.log10(xValMax_per), num=resample)
                
            if smooth or isinstance(smooth, (int, float)):
                if smooth:
                    smooth = 51 #Default smoothing window
                    padVal = 25
                elif smooth % 2==0:
                    smooth + 1 #Otherwise, needs to be odd
                    padVal = smooth // 2
                    if padVal % 2 == 0:
                        padVal += 1


            # Resample raw ppsd values
            for i, ppsd_t in enumerate(input_ppsds):
                if i==0:
                    psdRaw[k] = np.interp(x_periods[k], ppsds[k]['period_bin_centers'], ppsd_t)
                    if smooth is not False and smooth is not None:
                        padRawKPad = np.pad(psdRaw[k], [padVal, padVal], mode='reflect')
                        #padRawKPadSmooth = scipy.signal.savgol_filter(padRawKPad, smooth, 3)
                        padRawKPadSmooth = move_avg(padRawKPad, smooth)
                        psdRaw[k] = padRawKPadSmooth[padVal:-padVal]

                else:
                    psdRaw[k] = np.vstack((psdRaw[k], np.interp(x_periods[k], ppsds[k]['period_bin_centers'], ppsd_t)))
                    if smooth is not False:
                        padRawKiPad = np.pad(psdRaw[k][i], [padVal, padVal], mode='reflect')
                        #padRawKiPadSmooth = scipy.signal.savgol_filter(padRawKiPad, smooth, 3)
                        padRawKiPadSmooth = move_avg(padRawKiPad, smooth)
                        psdRaw[k][i] = padRawKiPadSmooth[padVal:-padVal]

            # Resample other values
            for keys in resampleList:
                if keys == 'period_bin_centers':
                    baseLength = len(ppsds[k][keys])
                
                if ppsds[k][keys].ndim == 1:
                    if ppsds[k][keys].shape[-1] == baseLength:
                        ppsds[k][keys] = np.logspace(np.log10(min(ppsds[k][keys])), np.log10(max(ppsds[k][keys])), num=resample)
                    else:
                        ppsds[k][keys] = np.logspace(np.log10(min(ppsds[k][keys])), np.log10(max(ppsds[k][keys])), num=resample-1)
                else:
                    arrList = []
                    for arr in ppsds[k][keys]:
                        arrList.append(np.logspace(np.log10(min(arr)), np.log10(max(arr)), num=resample))
                    
                    ppsds[k][keys] = np.array(arrList)
        else:
            #If no resampling desired
            x_periods[k] =  np.array(ppsds[k]['period_bin_centers'])#[:-1]#np.round([1/p for p in hvsr_data['ppsds'][k]['period_xedges'][:-1]], 3)

            # Clean up edge freq. values
            x_periods[k][0] = 1/hvsr_data['hvsr_band'][1]
            x_periods[k][-1] = 1/hvsr_data['hvsr_band'][0]

            # If simple curve smooothing desired
            if smooth or isinstance(smooth, (int, float)):
                if smooth:
                    smooth = 51 #Default smoothing window
                    padVal = 25
                elif smooth % 2==0:
                    smooth + 1 #Otherwise, needs to be odd
                    padVal = smooth // 2
                    if padVal % 2 == 0:
                        padVal += 1

                for i, ppsd_t in enumerate(input_ppsds):
                    if i == 0:
                        psdRaw[k] = ppsd_t
                        padRawKPad = np.pad(psdRaw[k], [padVal, padVal], mode='reflect')
                        #padRawKPadSmooth = scipy.signal.savgol_filter(padRawKPad, smooth, 3)
                        padRawKPadSmooth = move_avg(padRawKPad, smooth)
                        psdRaw[k] = padRawKPadSmooth[padVal:-padVal]
                    else:
                        psdRaw[k] = np.vstack((psdRaw[k], ppsd_t))
                        padRawKiPad = np.pad(psdRaw[k][i], [padVal, padVal], mode='reflect')
                        #padRawKiPadSmooth = scipy.signal.savgol_filter(padRawKiPad, smooth, 3)
                        padRawKiPadSmooth = move_avg(padRawKiPad, smooth)
                        psdRaw[k][i] = padRawKiPadSmooth[padVal:-padVal]
            else:
                # If no simple curve smoothing
                psdRaw[k] = np.array(input_ppsds)
        
        hvsrDF['psd_values_'+k] = list(psdRaw[k])
        use = hvsrDF['Use'].astype(bool)

        #Get average psd value across time for each channel (used to calc main H/V curve)
        psdValsTAvg[k] = np.nanmedian(np.stack(hvsrDF[use]['psd_values_'+k]), axis=0)
        x_freqs[k] = np.array([1/p for p in x_periods[k]]) #np.divide(np.ones_like(x_periods[k]), x_periods[k]) 
        stDev[k] = np.nanstd(np.stack(hvsrDF[use]['psd_values_'+k]), axis=0)

        stDevValsM[k] = np.array(psdValsTAvg[k] - stDev[k])
        stDevValsP[k] = np.array(psdValsTAvg[k] + stDev[k])

        currTimesUsed[k] = np.stack(hvsrDF[use]['TimesProcessed_Obspy'])
        #currTimesUsed[k] = ppsds[k]['current_times_used'] #original one
    
    #print('XFREQS', x_freqs[k].shape)
    #print('XPERs', x_periods[k].shape)
    #print('PSDRAW', psdRaw[k].shape)

    # Get string of horizontal_method type
    # First, define default
    if horizontal_method is None:
        horizontal_method = 3 # Geometric mean is used as default if nothing is specified

    # If an azimuth has been calculated and it's only one, automatically use the single azimuth method
    if len(hvsr_data.stream.merge().select(component='R')) == 1:
        horizontal_method = 8 # Single azimuth

    # horizontal_method needs to be str or int
    # First check if input is a string
    if type(horizontal_method) is str:
        if horizontal_method.isdigit():
            horizontal_method = int(horizontal_method)
        elif str(horizontal_method).title() in methodList:
            horizontal_method = methodList.index(horizontal_method.title())
        else:
            print(f"\tHorizontal method {f} not recognized, reverting to default (geometric mean).\n\tMust be one of {methodList}")
            horizontal_method = 3

    # Now, horizontal_method is int no matter how it was entered
    methodInt = horizontal_method
    horizontal_method = methodList[horizontal_method]
    
    hvsr_data['horizontal_method'] = horizontal_method

    #This gets the main hvsr curve averaged from all time steps
    anyK = list(x_freqs.keys())[0]
    hvsr_curve, hvsr_az, hvsr_tSteps = __get_hvsr_curve(x=x_freqs[anyK], psd=psdValsTAvg, horizontal_method=methodInt, hvsr_data=hvsr_data, azimuth=azimuth, verbose=verbose)
    origPPSD = hvsr_data['ppsds_obspy'].copy()

    #print('hvcurv', np.array(hvsr_curve).shape)
    #print('hvaz', np.array(hvsr_az).shape)

    #Add some other variables to our output dictionary
    hvsr_dataUpdate = {'input_params':hvsr_data,
                'x_freqs':x_freqs,
                'hvsr_curve':hvsr_curve,
                'hvsr_az':hvsr_az,
                'x_period':x_periods,
                'psd_raw':psdRaw,
                'current_times_used': currTimesUsed,
                'psd_values_tavg':psdValsTAvg,
                'ppsd_std':stDev,
                'ppsd_std_vals_m':stDevValsM,
                'ppsd_std_vals_p':stDevValsP,
                'horizontal_method':horizontal_method,
                'ppsds':ppsds,
                'ppsds_obspy':origPPSD,
                'tsteps_used': hvsr_data['tsteps_used'].copy(),
                'hvsr_windows_df':hvsr_data['hvsr_windows_df']
                }
    
    hvsr_out = HVSRData(hvsr_dataUpdate)

    #This is if manual editing was used (should probably be updated at some point to just use masks)
    if 'x_windows_out' in hvsr_data.keys():
        hvsr_out['x_windows_out'] = hvsr_data['x_windows_out']
    else:
        hvsr_out['x_windows_out'] = []

    freq_smooth_ko = ['konno ohmachi', 'konno-ohmachi', 'konnoohmachi', 'konnohmachi', 'ko', 'k']
    freq_smooth_constant = ['constant', 'const', 'c']
    freq_smooth_proport = ['proportional', 'proportion', 'prop', 'p']

    #Frequency Smoothing
    if not freq_smooth:
        if verbose:
            warnings.warn('No frequency smoothing is being applied. This is not recommended for noisy datasets.')
    elif freq_smooth is True or (freq_smooth.lower() in freq_smooth_ko and (not not f_smooth_width and not not freq_smooth)):
        from obspy.signal import konnoohmachismoothing
        for k in hvsr_out['psd_raw']:
            colName = f'psd_values_{k}'

            psd_data = np.stack(hvsr_out['hvsr_windows_df'][colName])
            psd_data = hvsr_out['psd_raw'][k]


            freqs = hvsr_out['x_freqs'][k]
            padding_length = int(f_smooth_width)

            padding_value_R = np.nanmean(psd_data[:,-1*padding_length:])
            padding_value_L = np.nanmean(psd_data[:,:padding_length])

            # Pad the data to prevent boundary anamolies
            padded_ppsd_data = np.pad(psd_data, ((0, 0), (padding_length, padding_length)), 
                                        'constant', constant_values=(padding_value_L, padding_value_R))

            # Pad the frequencies
            ratio = freqs[1] / freqs[0]
            # Generate new elements on either side and combine
            left_padding = [freqs[0] / (ratio ** i) for i in range(padding_length, 0, -1)]
            right_padding = [freqs[-1] * (ratio ** i) for i in range(1, padding_length + 1)]
            padded_freqs = np.concatenate([left_padding, freqs, right_padding])
            
            #Filter out UserWarning for just this method, since it throws up a UserWarning that doesn't really matter about dtypes often
            with warnings.catch_warnings():
                #warnings.simplefilter('ignore', category=UserWarning)
                padded_ppsd_data = padded_ppsd_data.astype(padded_freqs.dtype) # Make them the same datatype
                padded_ppsd_data = np.round(padded_ppsd_data, 12) # Prevent overflows
                padded_freqs = np.round(padded_freqs, 9)

                smoothed_ppsd_data = konnoohmachismoothing.konno_ohmachi_smoothing(padded_ppsd_data, padded_freqs, 
                                                    bandwidth=f_smooth_width, normalize=True)
            
            # Only use the original, non-padded data
            smoothed_ppsd_data = smoothed_ppsd_data[:,padding_length:-1*padding_length]
            hvsr_out['psd_raw'][k] = smoothed_ppsd_data
            hvsr_out['hvsr_windows_df'][colName] = pd.Series(list(smoothed_ppsd_data), index=hvsr_out['hvsr_windows_df'].index)
    elif freq_smooth.lower() in freq_smooth_constant:
        hvsr_out = __freq_smooth_window(hvsr_out, f_smooth_width, kind_freq_smooth='constant')
    elif freq_smooth.lower() in freq_smooth_proport:
        hvsr_out = __freq_smooth_window(hvsr_out, f_smooth_width, kind_freq_smooth='proportional')
    else:
        if verbose:
            warnings.warn(f'You indicated no frequency smoothing should be applied (freq_smooth = {freq_smooth}). This is not recommended for noisy datasets.')

    #Get hvsr curve from three components at each time step
    anyK = list(hvsr_out['psd_raw'].keys())[0]
    if horizontal_method==1 or horizontal_method =='dfa' or horizontal_method =='Diffuse Field Assumption':
        hvsr_tSteps_az = {}
    else:
        hvsr_tSteps = []
        hvsr_tSteps_az = {}
        for tStep in range(len(hvsr_out['psd_raw'][anyK])):
            tStepDict = {}
            for k in hvsr_out['psd_raw']:
                tStepDict[k] = hvsr_out['psd_raw'][k][tStep]
            hvsr_tstep, hvsr_az_tstep, _ = __get_hvsr_curve(x=hvsr_out['x_freqs'][anyK], psd=tStepDict, horizontal_method=methodInt, hvsr_data=hvsr_out, verbose=verbose)
            
            hvsr_tSteps.append(np.float64(hvsr_tstep)) #Add hvsr curve for each time step to larger list of arrays with hvsr_curves
            for k, v in hvsr_az_tstep.items():
                if tStep == 0:
                    hvsr_tSteps_az[k] = [np.float32(v)]
                else:
                    hvsr_tSteps_az[k].append(np.float32(v))
    hvsr_out['hvsr_windows_df']['HV_Curves'] = hvsr_tSteps
    
    # Add azimuth HV Curves to hvsr_windows_df, if applicable
    for key, values in hvsr_tSteps_az.items():
        hvsr_out['hvsr_windows_df']['HV_Curves_'+key] = values
    
    hvsr_out['ind_hvsr_curves'] = {}
    for col_name in hvsr_out['hvsr_windows_df']:
        if "HV_Curves" in col_name:
            if col_name == 'HV_Curves':
                colID = 'HV'
            else:
                colID = col_name.split('_')[2]
            hvsr_out['ind_hvsr_curves'][colID] = np.stack(hvsr_out['hvsr_windows_df'][hvsr_out['hvsr_windows_df']['Use']][col_name])

    #Initialize array based only on the curves we are currently using
    indHVCurvesArr = np.stack(hvsr_out['hvsr_windows_df']['HV_Curves'][hvsr_out['hvsr_windows_df']['Use']])

    if outlier_curve_percentile_threshold:
        if outlier_curve_percentile_threshold is True:
            outlier_curve_percentile_threshold = 98
        hvsr_out = remove_outlier_curves(hvsr_out, use_percentile=True, outlier_threshold=outlier_curve_percentile_threshold, use_hv_curves=True, verbose=verbose)

    hvsr_out['ind_hvsr_stdDev'] = {}
    for col_name in hvsr_out['hvsr_windows_df'].columns:
        if "HV_Curves" in col_name:
            if col_name == 'HV_Curves':
                keyID = 'HV'
            else:
                keyID = col_name.split('_')[2]
            curr_indHVCurvesArr = np.stack(hvsr_out['hvsr_windows_df'][col_name][hvsr_out['hvsr_windows_df']['Use']])
            hvsr_out['ind_hvsr_stdDev'][keyID] = np.nanstd(curr_indHVCurvesArr, axis=0)

    #Get peaks for each time step
    hvsr_out['ind_hvsr_peak_indices'] = {}
    tStepPFDict = {}
    #hvsr_out['hvsr_windows_df']['CurvesPeakFreqs'] = {}
    for col_name in hvsr_out['hvsr_windows_df'].columns:
        if col_name.startswith("HV_Curves"):
            tStepPeaks = []
            if len(col_name.split('_')) > 2:
                colSuffix = "_"+'_'.join(col_name.split('_')[2:])
            else:
                colSuffix = '_HV'

            for tStepHVSR in hvsr_out['hvsr_windows_df'][col_name]:
                tStepPeaks.append(__find_peaks(tStepHVSR))                
            hvsr_out['ind_hvsr_peak_indices']['CurvesPeakIndices'+colSuffix] = tStepPeaks

            tStepPFList = []
            for tPeaks in tStepPeaks:
                tStepPFs = []
                for pInd in tPeaks:
                    tStepPFs.append(np.float32(hvsr_out['x_freqs'][anyK][pInd]))
                tStepPFList.append(tStepPFs)
            tStepPFDict['CurvesPeakFreqs'+colSuffix] = tStepPFList
    
    indHVPeakIndsDF = pd.DataFrame(hvsr_out['ind_hvsr_peak_indices'], index=hvsr_out['hvsr_windows_df'].index)
    tStepPFDictDF = pd.DataFrame(tStepPFDict, index=hvsr_out['hvsr_windows_df'].index)
    for col in indHVPeakIndsDF.columns:
        hvsr_out['hvsr_windows_df'][col] = indHVPeakIndsDF.loc[:, col]
    for col in tStepPFDictDF.columns:
        hvsr_out['hvsr_windows_df'][col] = tStepPFDictDF.loc[:, col]

    #Get peaks of main HV curve
    hvsr_out['hvsr_peak_indices'] = {}
    hvsr_out['hvsr_peak_indices']['HV'] = __find_peaks(hvsr_out['hvsr_curve'])
    for k in hvsr_az.keys():
        hvsr_out['hvsr_peak_indices'][k] = __find_peaks(hvsr_out['hvsr_az'][k])
    
    #Get frequency values at HV peaks in main curve
    hvsr_out['hvsr_peak_freqs'] = {}
    for k in hvsr_out['hvsr_peak_indices'].keys():
        hvsrPF = []
        for p in hvsr_out['hvsr_peak_indices'][k]:
            hvsrPF.append(hvsr_out['x_freqs'][anyK][p])
        hvsr_out['hvsr_peak_freqs'][k] = np.array(hvsrPF)

    #Get other HVSR parameters (i.e., standard deviations, etc.)
    hvsr_out = __gethvsrparams(hvsr_out)

    #Include the original obspy stream in the output
    hvsr_out['input_stream'] = hvsr_dataUpdate['input_params']['input_stream'] #input_stream
    hvsr_out = sprit_utils._make_it_classy(hvsr_out)
    hvsr_out['processing_status']['process_hvsr_status'] = True

    if 'processing_parameters' not in hvsr_out.keys():
        hvsr_out['processing_parameters'] = {}
    hvsr_out['processing_parameters']['process_hvsr'] = {}
    exclude_params_list = ['hvsr_data']
    for key, value in orig_args.items():
        if key not in exclude_params_list:
            hvsr_out['processing_parameters']['process_hvsr'][key] = value
    
    if str(horizontal_method) == '8' or horizontal_method.lower() == 'single azimuth':
        if azimuth is None:
            azimuth = 90
        hvsr_out['single_azimuth'] = azimuth

    hvsr_out = sprit_utils._check_processing_status(hvsr_out, start_time=start_time, func_name=inspect.stack()[0][3], verbose=verbose)

    return hvsr_out


# Read data from Tromino
def read_tromino_files(input_data, struct_format='H', tromino_model=None,
    sampling_rate=None, set_record_duration=None, start_byte=24576, verbose=False, **kwargs):
    
    """Function to read data from tromino. Specifically, this has been lightly tested on Tromino 3G+ and Blue machines

    Parameters
    ----------
    input_data : str
        Falseilepath to .trc file
    struct_format : str, optional
        This is the format used in the struct module. 
        Usually should not be changed, by default 'H'
    tromino_model : str, optional
        Which tromino model is being read. 
        Currently only "Yellow" and "Blue" are supported.
        If None, assumes "Yellow", by default None.
    sampling_rate : int, optional
        Sampling rate (samples per second) used during acquisition. 
        This may later be detected automatically.
        If None, 128 used, by default None
    set_record_duration : int, optional
        Duration of record to set manually in minutes, by default None
    start_byte : int, optional
        Used internally, by default 24576
    verbose : bool, optional
        Whether to print information to terminal, by default False

    Returns
    -------
    obspy.stream.Stream
        Obspy Stream object with Tromino data
    """
        
    dPath = input_data

    blueModelList = ['blue', 'blu', 'tromino blu', 'tromino blue']

    if str(tromino_model).lower() in blueModelList or 'blue' in str(tromino_model).lower():
        tBlueKwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(__read_tromino_data_blue).parameters.keys())}
        if 'sampling_rate' not in tBlueKwargs:
            tBlueKwargs['sampling_rate'] = sampling_rate
            return __read_tromino_data_blue(input_data, verbose=False, **tBlueKwargs)
            
    if sampling_rate is None:
        sampling_rate = 128 # default value

    strucSizes = {'c':1, 'b':1,'B':1, '?':1,
                'h':2,'H':2,'e':2,
                'i':4,'I':4,'l':4,'L':4,'f':4,
                'q':8,'Q':8,'d':8,
                'n':8,'N':8,'s':16,'p':16,'P':16,'x':16}

    #H (pretty sure it's Q) I L or Q all seem to work (probably not Q?)
    structFormat = struct_format
    structSize = strucSizes[structFormat]

    dataList = []
    with open(dPath, 'rb') as f:
        while True:
            data = f.read(structSize)  # Read 4 bytes
            if not data:  # End of file
                break
            value = struct.unpack(structFormat, data)[0]  # Interpret as a float
            dataList.append(value)
     
    import numpy as np
    dataArr = np.array(dataList)
    import matplotlib.pyplot as plt

    medVal = np.nanmedian(dataArr[50000:100000])

    if 'start_byte' in kwargs.keys():
        start_byte = kwargs['start_byte']

    station = 'Tromino'
    if 'station' in kwargs:
        station = kwargs['station']

    acq_date = datetime.date.today()
    if 'acq_date' in kwargs:
        acq_date = kwargs['acq_date']

    starttime = datetime.time(0, 0)
    if 'starttime' in kwargs:
        starttime = kwargs['starttime']

    startByte = start_byte
    comp1 = dataArr[startByte::3] - medVal
    comp2 = dataArr[startByte+1::3] - medVal
    comp3 = dataArr[startByte+2::3] - medVal
    headerBytes = dataArr[:startByte]

    if 'diagnose' in kwargs and kwargs['diagnose']:
        print("Total file bytes: ", len(dataArr))

    #fig, ax = plt.subplots(3, sharex=True, sharey=True)
    #ax[0].plot(comp1, linewidth=0.1, c='k')
    #ax[1].plot(comp2, linewidth=0.1, c='k')
    #ax[2].plot(comp3, linewidth=0.1, c='k')

    if 'sampling_rate' in kwargs.keys():
        sampling_rate = kwargs['sampling_rate']

    sTime = obspy.UTCDateTime(acq_date.year, acq_date.month, acq_date.day,
                              starttime.hour, starttime.minute,
                              starttime.second, starttime.microsecond)
    eTime = sTime + (((len(comp1))/sampling_rate)/60)*60

    loc = ''
    if type(station) is int or station.isdigit():
        loc = str(station)

    traceHeader1 = {'sampling_rate':sampling_rate,
            'calib' : 1,
            'npts':len(comp1),
            'network':'AM',
            'location': loc,
            'station' : 'TRMNO',
            'channel':'EHE',
            'starttime':sTime}
    
    traceHeader2=traceHeader1.copy()
    traceHeader3=traceHeader1.copy()
    traceHeader2['channel'] = 'EHN'
    traceHeader3['channel'] = 'EHZ'

    trace1 = obspy.Trace(data=comp1, header=traceHeader1)
    trace2 = obspy.Trace(data=comp2, header=traceHeader2)
    trace3 = obspy.Trace(data=comp3, header=traceHeader3)

    st = obspy.Stream([trace1, trace2, trace3])
    return st


# Function to remove noise windows from data
def remove_noise(hvsr_data, remove_method=None, 
                 processing_window=None, sat_percent=0.995, noise_percent=0.80, 
                 sta=2, lta=30, stalta_thresh=[8, 16], 
                 std_ratio_thresh=2.0, std_window_size=20.0, min_std_win=5.0,
                 warmup_time=0, cooldown_time=0, min_win_size=1,
                 remove_raw_noise=False, show_stalta_plot=False, verbose=False):
    """Function to remove noisy windows from data, using various methods.
    
    Methods include 
    - Manual window selection (by clicking on a chart with spectrogram and stream data), 
    - Auto window selection, which does the following two in sequence (these can also be done indepently):
        - A sta/lta "antitrigger" method (using stalta values to automatically remove triggered windows where there appears to be too much noise)
        - A noise threshold method, that cuts off all times where the noise threshold equals more than (by default) 80% of the highest amplitude noise sample for the length specified by lta (in seconds)
        - A saturation threshold method, that cuts off all times where the noise threshold equals more than (by default) 99.5% of the highest amplitude noise sample.

    Parameters
    ----------
    hvsr_data : dict, obspy.Stream, or obspy.Trace
        Dictionary containing all the data and parameters for the HVSR analysis
    remove_method : str, {'auto', 'manual', 'stalta'/'antitrigger', 'saturation threshold', 'noise threshold', 'warmup'/'cooldown'/'buffer'/'warm_cool'}
        The different methods for removing noise from the dataset. A list of strings will also work, in which case, it should be a list of the above strings. See descriptions above for what how each method works. By default 'auto.'
        If remove_method='auto', this is the equivalent of remove_method=['noise threshold', 'antitrigger', 'saturation threshold', 'warm_cool']
    processing_window : list, tuple, or None
        A list/tuple of two items [s, e] or a list/tuple of two-item lists/tuples [[s0, e0], [s1,e1],...[sn, en]] with start and end time(s) for windows to *keep* for processing. 
        Data outside of these times will be excluded from processing. 
        Times should be obspy.UTCDateTime objects to ensure precision, but time strings ("13:05") will also work in most cases (excpetions may be when the data stream starts/ends on different UTC days)
    sat_percent : float, default=0.995
        Percentage (between 0 and 1), to use as the threshold at which to remove data. This is used in the saturation method. By default 0.995. 
        If a value is passed that is greater than 1, it will be divided by 100 to obtain the percentage.
    noise_percent : float, default = 0.8
        Percentage (between 0 and 1), to use as the threshold at which to remove data, if it persists for longer than time (in seconds (specified by min_win_size)). This is used in the noise threshold method. By default 0.8. 
        If a value is passed that is greater than 1, it will be divided by 100 to obtain the percentage.
    sta : int, optional
        Short term average (STA) window (in seconds), by default 2. For use with sta/lta antitrigger method.
    lta : int, optional
        Long term average (STA) window (in seconds), by default 30. For use with sta/lta antitrigger method.
    stalta_thresh : list, default=[0.5,5]
        Two-item list or tuple with the thresholds for the stalta antitrigger. The first value (index [0]) is the lower threshold, the second value (index [1] is the upper threshold), by default [0.5,5]
    std_ratio_thresh : float, optional
        The ratio to use as a threshold for removal of noise. The ratio represents the standard deviation value for a rolling window (the size of which is determined by the std_window_size parameter) 
        divided by the standard deviation calculated for the entire trace. This rolling window standard deviation method is similar to the default noise removal method used by the Grilla HVSR software.
    std_window_size : float, optional
        The length of the window (in seconds) to use for calculating the rolling/moving standard deviation of a trace for the rolling standard deviation method.
    min_std_win : float, optional
        The minimum size of "window" that will be remove using the rolling standard deviation method.
    warmup_time : int, default=0
        Time in seconds to allow for warmup of the instrument (or while operator is still near instrument). This will renove any data before this time, by default 0.
    cooldown_time : int, default=0
        Time in seconds to allow for cooldown of the instrument (or for when operator is nearing instrument). This will renove any data before this time, by default 0.
    min_win_size : float, default=1
        The minumum size a window must be over specified threshold (in seconds) for it to be removed
    remove_raw_noise : bool, default=False
        If remove_raw_noise=True, will perform operation on raw data ('input_stream'), rather than potentially already-modified data ('stream').
    verbose : bool, default=False
        Whether to print status of remove_noise

    Returns
    -------
    output : dict
        Dictionary similar to hvsr_data, but containing modified data with 'noise' removed
    """
    #Get intput paramaters
    orig_args = locals().copy()
    start_time = datetime.datetime.now()
    
    # Update with processing parameters specified previously in input_params, if applicable
    if 'processing_parameters' in hvsr_data.keys():
        if 'remove_noise' in hvsr_data['processing_parameters'].keys():
            update_msg = []
            for k, v in hvsr_data['processing_parameters']['remove_noise'].items():
                defaultVDict = dict(zip(inspect.getfullargspec(remove_noise).args[1:], 
                                        inspect.getfullargspec(remove_noise).defaults))
                # Manual input to function overrides the imported parameter values
                if (not isinstance(v, (HVSRData, HVSRBatch))) and (k in orig_args.keys()) and (orig_args[k]==defaultVDict[k]):
                    update_msg.append(f'\t\t{k} = {v} (previously {orig_args[k]})')
                    orig_args[k] = v
                    
    remove_method = orig_args['remove_method']
    processing_window = orig_args['processing_window']
    sat_percent = orig_args['sat_percent']
    noise_percent = orig_args['noise_percent']
    sta = orig_args['sta']
    lta = orig_args['lta']
    stalta_thresh = orig_args['stalta_thresh']
    warmup_time = orig_args['warmup_time']
    cooldown_time = orig_args['cooldown_time']
    min_win_size = orig_args['min_win_size']
    remove_raw_noise = orig_args['remove_raw_noise']
    verbose = orig_args['verbose']

    if (verbose and isinstance(hvsr_data, HVSRBatch)) or (verbose and not hvsr_data['batch']):
        if isinstance(hvsr_data, HVSRData) and hvsr_data['batch']:
            pass
        else:
            print('\nRemoving noisy data windows (remove_noise())')
            print('\tUsing the following parameters:')
            for key, value in orig_args.items():
                if key=='hvsr_data':
                    pass
                else:
                    print('\t  {}={}'.format(key, value))
            print()

            if 'processing_parameters' in hvsr_data.keys() and 'remove_noise' in hvsr_data['processing_parameters'].keys():
                if update_msg != []:
                    update_msg.insert(0, '\tThe following parameters were updated using the processing_parameters attribute:')
                    for msg_line in update_msg:
                        print(msg_line)
                print()

    # Set up lists
    manualList = ['manual', 'man', 'm', 'window', 'windows', 'w']
    autoList = ['auto', 'automatic', 'all', 'a']
    antitrigger = ['stalta', 'anti', 'antitrigger', 'trigger', 'at']
    movingstdList = ['moving_std', 'std', 'stdev', 'standard deviation', 'stdev', 'moving_stdev', 'movingstd', 'movingstdev']
    saturationThresh = ['saturation threshold', 'sat_thresh', 'sat thresh', 'saturation', 'sat', 's']
    noiseThresh = ['noise threshold', 'noise thresh', 'noise_thresh', 'noise', 'threshold', 'n']
    warmup_cooldown=['warmup', 'cooldown', 'warm', 'cool', 'buffer', 'warmup-cooldown', 'warmup_cooldown', 'wc', 'warm_cool', 'warm-cool']
    procWinList = ['processing_window', 'processing window', 'windows', 'window', 'win', 'pw']

    # Do batch runs
    if isinstance(hvsr_data, HVSRBatch):
        #If running batch, we'll loop through each site
        hvsr_out = {}
        for site_name in hvsr_data.keys():
            args = orig_args.copy() #Make a copy so we don't accidentally overwrite
            args['hvsr_data'] = hvsr_data[site_name] #Get what would normally be the "hvsr_data" variable for each site
            if hvsr_data[site_name]['processing_status']['overall_status']:
                try:
                   hvsr_out[site_name] = __remove_noise_batch(**args) #Call another function, that lets us run this function again
                except Exception as e:
                    hvsr_out[site_name]['processing_status']['remove_noise_status']=False
                    hvsr_out[site_name]['processing_status']['overall_status']=False
                    if verbose:
                        print(e)
            else:
                hvsr_data[site_name]['processing_status']['remove_noise_status']=False
                hvsr_data[site_name]['processing_status']['overall_status']=False
                hvsr_out = hvsr_data

        output = HVSRBatch(hvsr_out, df_as_read=hvsr_data.input_df)
        return output
    
    if not isinstance(hvsr_data, (HVSRData, dict, obspy.Stream, obspy.Trace)):
        warnings.warn(f"Input of type type(hvsr_data)={type(hvsr_data)} cannot be used.")
        return hvsr_data
    
    # Which stream to use (input, or current)
    if isinstance(hvsr_data, (HVSRData, dict)):
        if remove_raw_noise:
            inStream = hvsr_data['input_stream'].copy()
        else:
            inStream = hvsr_data['stream'].copy()
        output = hvsr_data#.copy()
    else:
        inStream = hvsr_data.copy()
        output = inStream.copy()

    outStream = inStream

    # Get remove_method into consistent format (list)
    if isinstance(remove_method, str):
        if ',' in remove_method:
            remove_method = remove_method.split(',')
        else:
            remove_method = [remove_method]
    elif isinstance(remove_method, (list, tuple)):
        pass
    elif not remove_method:
        remove_method=[None]
    else:
        warnings.warn(f"Input value remove_method={remove_method} must be either string, list of strings, None, or False. No noise removal will be carried out. Please choose one of the following: 'manual', 'auto', 'antitrigger', 'noise threshold', 'warmup_cooldown'.")
        return output
    orig_removeMeth = remove_method
    # Check if any parameter values are different from default (if they are, automatically add that method to remove_method)
    rn_signature = inspect.signature(remove_noise)

    methodDict = {'moving_std': ['std_ratio_thresh', 'std_window_size', 'min_std_win'],
                  'sat_thresh': ['sat_percent'],
                  'antitrigger': ['sta', 'lta', 'stalta_thresh', 'show_stalta_plot'],
                  'noise_thresh': ['noise_percent', 'min_win_size'],
                  'warmup_cooldown': ['warmup_time', 'cooldown_time'],
                  'processing_window': ['processing_window']}

    defaultValDict = {param.name: param.default for param in rn_signature.parameters.values() if param.default is not inspect.Parameter.empty}

    # If a non-default parameter is specified, add the method it corresponds to to remove_method
    for key, def_val in defaultValDict.items():
        if key in orig_args:
            if def_val != orig_args[key]:
                for methodKey, methParamList in methodDict.items():
                    if key in methParamList:
                        # Add the corresponding method to remove_mehtod if not already
                        if (methodKey not in remove_method) and ('auto' not in remove_method):
                            if remove_method == [None]:
                                remove_method = [methodKey]
                            else:
                                remove_method.append(methodKey)

    # Reorder list so manual is always first, if it is specified
    do_manual = False
    if len(set(remove_method).intersection(manualList)) > 0:
        do_manual = True
        manInd = list(set(remove_method).intersection(manualList))[0]
        remove_method.remove(manInd)
        remove_method.insert(0, manInd)

    # Reorder list so auto is always first (if no manual) or second (if manual)
    # B/c if 'auto' is carried out, no other methods need to be carried out (repetitive)
    newAutoInd = 0
    if do_manual:
        newAutoInd = 1
    if len(set(remove_method).intersection(autoList)) > 0:
        autoInd = list(set(remove_method).intersection(autoList))[0]
        remove_method.remove(autoInd)
        remove_method.insert(newAutoInd, autoInd)        
    
    #Go through each type of removal and remove
    if orig_removeMeth != remove_method:
        if verbose:
            print(f'\tThe remove_method parameter has been updated because non-default parameter values were detected.')
            print(f'\tThe remove_method parameter was entered as {orig_removeMeth}, but has been updated to {remove_method}')

    # REMOVE DATA FROM ANALYSIS
    for rem_kind in remove_method:
        try:
            if not rem_kind:
                break
            elif rem_kind.lower() in manualList:
                if isinstance(output, (HVSRData, dict)):
                    if 'x_windows_out' in output.keys():
                        pass
                    else:
                        output = _select_windows(output)
                    window_list = output['x_windows_out']
                if isinstance(outStream, obspy.core.stream.Stream):
                    if window_list is not None:
                        output['stream'] = __remove_windows(inStream, window_list, warmup_time)
                    else:
                        output = _select_windows(output)
                elif isinstance(output, (HVSRData, dict)):
                    pass
                else:
                    RuntimeError("Only obspy.core.stream.Stream data type is currently supported for manual noise removal method.")     
            elif rem_kind.lower() in autoList:
                outStream = __remove_moving_std(stream=outStream, std_ratio_thresh=std_ratio_thresh, std_window_s=std_window_size, min_win_size=min_std_win)
                outStream = __remove_noise_saturate(outStream, sat_percent=sat_percent, min_win_size=min_win_size, verbose=verbose)
                # Break for-loop, since all the rest are already done as part of auto
                break
            elif rem_kind.lower() in antitrigger:
                outStream = __remove_anti_stalta(outStream, sta=sta, lta=lta, thresh=stalta_thresh, show_stalta_plot=show_stalta_plot, verbose=verbose)
            elif rem_kind.lower() in movingstdList:
                outStream = __remove_moving_std(stream=outStream, std_ratio_thresh=std_ratio_thresh, std_window_s=std_window_size, min_win_size=min_std_win)
            elif rem_kind.lower() in saturationThresh:
                outStream = __remove_noise_saturate(outStream, sat_percent=sat_percent, min_win_size=min_win_size, verbose=verbose)
            elif rem_kind.lower() in noiseThresh:
                outStream = __remove_noise_thresh(outStream, noise_percent=noise_percent, lta=lta, min_win_size=min_win_size, verbose=verbose)
            elif rem_kind.lower() in warmup_cooldown:
                outStream = __remove_warmup_cooldown(stream=outStream, warmup_time=warmup_time, cooldown_time=cooldown_time, verbose=verbose)
            elif rem_kind.lower() in procWinList and str(processing_window).lower() != 'none':
                outStream = _keep_processing_windows(stream=outStream, processing_window=processing_window, verbose=verbose)
            else:
                if len(remove_method)==1:
                    warnings.warn(f"Input value remove_method={remove_method} is not recognized. No noise removal will be carried out. Please choose one of the following: 'manual', 'auto', 'antitrigger', 'noise threshold', 'warmup_cooldown'.")
                    break
                warnings.warn(f"Input value remove_method={remove_method} is not recognized. Continuing with other noise removal methods.")
        except Exception as e:
            print(f'\t  *Error with {rem_kind} method. Data was not removed using that method.')
            print(f'\t  *{e}')
    
    # Add output
    if isinstance(output, (HVSRData, dict)):
        if isinstance(outStream, (obspy.Stream, obspy.Trace)):
            output['stream_edited'] = outStream
        else:
            output['stream_edited'] = outStream['stream']
        output['input_stream'] = hvsr_data['input_stream']
        
        if 'processing_parameters' not in output.keys():
            output['processing_parameters'] = {}
        output['processing_parameters']['remove_noise'] = {}
        for key, value in orig_args.items():
            output['processing_parameters']['remove_noise'][key] = value
        
        output['processing_status']['remove_noise_status'] = True
        output = sprit_utils._check_processing_status(output, start_time=start_time, func_name=inspect.stack()[0][3], verbose=verbose)

        output = __remove_windows_from_df(output, verbose=verbose)

        #if 'hvsr_windows_df' in output.keys() or ('params' in output.keys() and 'hvsr_windows_df' in output['params'].keys())or ('input_params' in output.keys() and 'hvsr_windows_df' in output['input_params'].keys()):
        #    hvsrDF = output['hvsr_windows_df']
        #    
        #    outStream = output['stream_edited'].split()
        #    for i, trace in enumerate(outStream):
        #        if i == 0:
        #            trEndTime = trace.stats.endtime
        #            comp_end = trace.stats.component
        #            continue
        #        trStartTime = trace.stats.starttime
        #        comp_start = trace.stats.component
                
        #        if trEndTime < trStartTime and comp_end == comp_start:
        #            gap = [trEndTime,trStartTime]

        #            output['hvsr_windows_df']['Use'] = (hvsrDF['TimesProcessed_Obspy'].gt(gap[0]) & hvsrDF['TimesProcessed_Obspy'].gt(gap[1]) )| \
        #                            (hvsrDF['TimesProcessed_ObspyEnd'].lt(gap[0]) & hvsrDF['TimesProcessed_ObspyEnd'].lt(gap[1]))# | \
        #            output['hvsr_windows_df']['Use'] = output['hvsr_windows_df']['Use'].astype(bool)
        #        
        #        trEndTime = trace.stats.endtime
        #    
        #    outStream.merge()
        #    output['stream_edited'] = outStream
                
    elif isinstance(hvsr_data, obspy.Stream) or isinstance(hvsr_data, obspy.Trace):
        output = outStream
    else:
        warnings.warn(f"Output of type {type(output)} for this function will likely result in errors in other processing steps. Returning hvsr_data data.")
        return hvsr_data
    output = sprit_utils._make_it_classy(output)
    if 'x_windows_out' not in output.keys():
        output['x_windows_out'] = []

    return output


# Remove outlier ppsds
def remove_outlier_curves(hvsr_data, outlier_method='prototype',
                          outlier_threshold=50, use_percentile=True, min_pts=5,
                          use_hv_curves=False,
                          plot_engine='matplotlib', show_outlier_plot=False, generate_outlier_plot=True,
                          verbose=False, **kwargs):
    """Function used to remove outliers curves using a "prototype" or "dbscan" method. 
    Prototype method calculates a prototype curve (i.e., median) and calculates the distance of the H/V or PSD curve from each window from that prototype curve.
    Currently, Root Mean Square Error is used to calculate the distance for each windowed H/V or PSD curve at each frequency step for all times.
    It calculates the RMSE for the PPSD curves of each component individually. All curves are removed from analysis.

    DBSCAN uses the DBSCAN method, outlier_threshold being by default the percentile value of distances of all curves from all other curves.
    Distance is calculated using scipy.spatial.distance.pdist, by default with 'euclidean' distance. 
    The `min_pts` parameter specifies the minimum number of curves whose distance must be within the threshold distance percentile/value to be retained.
    
    Some abberant curves often occur due to the remove_noise() function, so this should be run some time after remove_noise(). 
    In general, the recommended workflow is to run this immediately following the `generate_psds()` function. or if use_hv_curves=True, after `process_hvsr()`.

    Parameters
    ----------
    hvsr_data : dict
        Input dictionary containing all the values and parameters of interest
    outlier_method : str, default='prototype'
        The method to use for outlier detection. Currently, 'dbscan' and 'prototype' is supported.
    outlier_threshold : float or int, default=98
        The Root Mean Square Error value to use as a threshold for determining whether a curve is an outlier. 
        This averages over each individual entire curve so that curves with very abberant data (often occurs when using the remove_noise() method), can be identified.
        Otherwise, specify a float or integer to use as the cutoff RMSE value (all curves with RMSE above will be removed)
    use_percentile :  float, default=True
        Whether outlier_threshold should be interepreted as a raw RMSE value or as a percentile of the RMSE values.
    min_pts : int, default=5
        The minimum number of points to use for the outlier detection method.
        This is only used if outlier_method='dbscan' 
        This is minimum number of points a point needs in its neighborhood to not be considered an outlier.
    use_hv_curves : bool, default=False
        Whether to use the calculated HV Curve or the individual components. This can only be True after process_hvsr() has been run.
    show_plot : bool, default=False
        Whether to show a plot of the removed data
    verbose : bool, default=False
        Whether to print output of function to terminal

    Returns
    -------
    hvsr_data : dict
        Input dictionary with values modified based on work of function.

    SEE ALSO
    --------
    [scipy.spatial.distance.pdist](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.pdist.html#scipy.spatial.distance.pdist)
    """
    # Setup function
    #Get intput paramaters
    orig_args = locals().copy()
    start_time = datetime.datetime.now()
    
    # Update with processing parameters specified previously in input_params, if applicable
    if 'processing_parameters' in hvsr_data.keys():
        if 'remove_outlier_curves' in hvsr_data['processing_parameters'].keys() and 'remove_noise' in hvsr_data['processing_parameters'].keys():
            update_msg = []
            for k, v in hvsr_data['processing_parameters']['remove_noise'].items():
                defaultVDict = dict(zip(inspect.getfullargspec(remove_outlier_curves).args[1:], 
                                        inspect.getfullargspec(remove_outlier_curves).defaults))
                # Manual input to function overrides the imported parameter values
                if (not isinstance(v, (HVSRData, HVSRBatch))) and (k in orig_args.keys()) and (orig_args[k]==defaultVDict[k]):
                    update_msg.append(f'\t\t{k} = {v} (previously {orig_args[k]})')
                    orig_args[k] = v

    # Reset parameters in case of manual override of imported parameters
    outlier_method = orig_args['outlier_method']
    outlier_threshold = orig_args['outlier_threshold']
    use_percentile = orig_args['use_percentile']
    min_pts = orig_args['min_pts']
    use_hv_curves = orig_args['use_hv_curves']
    plot_engine = orig_args['plot_engine']
    show_outlier_plot = orig_args['show_outlier_plot']
    generate_outlier_plot = orig_args['generate_outlier_plot']
    verbose = orig_args['verbose']

    # Allow skipping step if outlier_method specified as None (may help GUIs)
    if str(outlier_method).lower() == 'none' or outlier_method is None:
        return hvsr_data

    #Print if verbose, which changes depending on if batch data or not
    if (verbose and isinstance(hvsr_data, HVSRBatch)) or (verbose and not hvsr_data['batch']):
        if isinstance(hvsr_data, HVSRData) and hvsr_data['batch']:
            pass
        else:
            print('\nRemoving outlier curves from further analysis (remove_outlier_curves())')
            print('\tUsing the following parameters:')
            for key, value in orig_args.items():
                if key == 'hvsr_data':
                    pass
                else:
                    print('\t  {}={}'.format(key, value))
            print()
                        
            if 'processing_parameters' in hvsr_data.keys() and 'remove_outlier_curves' in hvsr_data['processing_parameters'].keys():
                if update_msg != []:
                    update_msg.insert(0, '\tThe following parameters were updated using the processing_parameters attribute:')
                    for msg_line in update_msg:
                        print(msg_line)
                print()
    
    #First, divide up for batch or not
    #Site is in the keys anytime it's not batch
    if isinstance(hvsr_data, HVSRBatch):
        #If running batch, we'll loop through each site
        hvsr_out = {}
        for site_name in hvsr_data.keys():
            args = orig_args.copy() #Make a copy so we don't accidentally overwrite
            args['hvsr_data'] = hvsr_data[site_name] #Get what would normally be the "hvsr_data" variable for each site
            if hvsr_data[site_name]['processing_status']['overall_status']:
                try:
                    hvsr_out[site_name] = __remove_outlier_curves(**args) #Call another function, that lets us run this function again
                except:
                    hvsr_out = hvsr_data
                    hvsr_out[site_name]['processing_status']['remove_outlier_curves_status'] = False
                    hvsr_out[site_name]['processing_status']['overall_status'] = False                    
            else:
                hvsr_out = hvsr_data
                hvsr_out[site_name]['processing_status']['remove_outlier_curves_status'] = False
                hvsr_out[site_name]['processing_status']['overall_status'] = False
        hvsr_out = HVSRBatch(hvsr_out, df_as_read=hvsr_data.input_df)
        hvsr_out = sprit_utils._check_processing_status(hvsr_out, start_time=start_time, func_name=inspect.stack()[0][3], verbose=verbose)
        return hvsr_out

    dbscanList = ['dbscan', 'distance', 'dist', 'dbs', 'db', 'd']
    prototypeList = ['prototype', 'proto', 'ptype', 'p',
                     'root mean square', 'root mean square error', 
                     'rms', 'rmse', 'r']

    # Determine names of hvsr_windows_df columns to use
    if not use_hv_curves:
        compNames = ['Z', 'E', 'N']
        for col_name in hvsr_data['hvsr_windows_df'].columns:
            if 'psd_values' in col_name and 'RMSE' not in col_name:
                cName = col_name.split('_')[2]
                if cName not in compNames:
                    compNames.append(cName)
        col_prefix = 'psd_values_'
        colNames = [col_prefix+cn for cn in compNames]
    else:
        compNames = []
        for col_name in hvsr_data['hvsr_windows_df'].columns:
            if col_name.startswith('HV_Curves') and "Log10" not in col_name:
                compNames.append(col_name)
        colNames = compNames
        col_prefix = 'HV_Curves'

    # Remove outlier depending on method, prototype as default
    if str(outlier_method).lower() in dbscanList:
        hvsr_out = __dbscan_outlier_detect(hvsr_data=hvsr_data, use_hv_curves=use_hv_curves, 
                                           use_percentile=use_percentile,
                                           neighborhood_size=outlier_threshold,
                                           dist_metric='euclidean', 
                                           min_neighborhood_pts=min_pts,
                                           col_names=colNames,
                                           comp_names=compNames,
                                           col_prefix=col_prefix,
                                           verbose=verbose)
        
    elif str(outlier_method).lower() in prototypeList:
        hvsr_out = __prototype_outlier_detect(hvsr_data, use_hv_curves=use_hv_curves, 
                                              use_percentile=use_percentile,
                                              outlier_threshold=outlier_threshold,
                                              col_names=colNames,
                                              comp_names=compNames,
                                              col_prefix=col_prefix,
                                              verbose=verbose)
    else:
        hvsr_out = __prototype_outlier_detect(hvsr_data, use_hv_curves=use_hv_curves, 
                                              use_percentile=use_percentile,
                                              outlier_threshold=outlier_threshold,
                                              col_names=colNames,
                                              comp_names=compNames,
                                              col_prefix=col_prefix,
                                              verbose=verbose)

    # Show plot of removed/retained data
    if plot_engine.lower() == 'matplotlib' and (generate_outlier_plot or show_outlier_plot):
        hvsr_data['Outlier_Plot'] = sprit_plot.plot_outlier_curves(hvsr_data, outlier_threshold=outlier_threshold, use_percentile=use_percentile, use_hv_curves=use_hv_curves, plot_engine='matplotlib', show_plot=show_outlier_plot, verbose=verbose)
    elif plot_engine.lower() == 'plotly'  and (generate_outlier_plot or show_outlier_plot):
        hvsr_data['Outlier_Plot'] = sprit_plot.plot_outlier_curves(hvsr_data, outlier_threshold=outlier_threshold, use_percentile=use_percentile, use_hv_curves=use_hv_curves, plot_engine='plotly', from_roc=True, show_plot=show_outlier_plot, verbose=verbose)
    else:
        pass

    if 'processing_parameters' not in hvsr_out.keys():
        hvsr_out['processing_parameters'] = {}
    hvsr_out['processing_parameters']['remove_outlier_curves'] = {}
    exclude_params_list = ['hvsr_data']
    for key, value in orig_args.items():
        if key not in exclude_params_list:
            hvsr_out['processing_parameters']['remove_outlier_curves'][key] = value

    hvsr_out['processing_status']['remove_outlier_curves_status'] = True
    
    hvsr_out = sprit_utils._check_processing_status(hvsr_out, start_time=start_time, func_name=inspect.stack()[0][3], verbose=verbose)
    
    return hvsr_out


# Just for testing
def test_function():
    print('is this working?')


# Update all elevation-related attriutes
def update_elevation(hvsr_data, updated_surface_elevation, updated_elevation_unit):
    """Function to quickly update all attributes associated with elevation of an HVSRData object

    Parameters
    ----------
    hvsr_data : HVSRData or HVSRBatch
        HVSRData or HVSRBatch object containing attributes related to elevation.
        If HVSRBatch, updated_surface_elevation should be list or tuple and 
        updated_elevation_unit may either be str or  list/tuple of strings.        
    updated_surface_elevation : numbers.Number
        Number (float or int) with the updated elevation.
        Meters is the preferred unit. If feet are used instead, it will be converted to meters.
    updated_elevation_unit : str
        Unit used for updated_surface_elevation. If 'feet', it will be converted to meters.

    Returns
    -------
    HVSRData
        HVSRData object with all attributes related to elevation updated
    """
    
    # Break out for HVSRBatch
    if isinstance(hvsr_data, HVSRBatch):
        if len(updated_surface_elevation) != len(hvsr_data.sites):
            warnings.warn(f'Elevations for HVSRBatch object could not be updated. \
                Length of updated_surface_elevation ({len(updated_surface_elevation)}) must equal\
                the number of sites ({len(hvsr_data.sites)}) in hvsr_data')
            return hvsr_data
        
        if isinstance(updated_elevation_unit, (list, tuple)):
            if len(updated_elevation_unit) != len(hvsr_data.sites):
                warnings.warn(f'Elevations for HVSRBatch object could not be updated. \
                    Length of updated_elevation_unit ({len(updated_elevation_unit)}) must equal\
                    the number of sites ({len(hvsr_data.sites)}) in hvsr_data')
            return hvsr_data
        
        elif type(updated_elevation_unit) is str:
            updated_elevation_unit = [updated_elevation_unit] * len(hvsr_data.sites)
        else:
            warnings.warn(f"updated_elevation_unit must be list, tuple, or str, not {type(updated_elevation_unit)}")
        
        for i, sitename in enumerate( hvsr_data):
            hvsr_data[sitename] = _update_elevation(hvsr_data[sitename], 
                                                   updated_surface_elevation[i],
                                                   updated_elevation_unit[i])
        return hvsr_data
    
    #elevation_attrs = ['elevation', 'x_elev_m', 'x_elev_ft']
    if hasattr(hvsr_data, 'elevation'):
        elev_diff = hvsr_data['elevation'] - updated_surface_elevation
    else:
        elev_diff = -1 * updated_surface_elevation
        

    mList = ['meters', 'm', 'standard', 'metric', 'si', 'metres', 'metre', 'meter']
    fList = ['feet', 'ft', 'f', 'foot', 'american', 'imperial', 'imp']
    
    # Update parameters with elevations in them
    if str(updated_elevation_unit).lower() in fList:
        updated_surface_elevation = updated_surface_elevation * 0.3048
    hvsr_data['elevation'] = updated_surface_elevation
        
    hvsr_data['elev_unit'] = 'meters'
    
    if hasattr(hvsr_data, 'x_elev_m'):
        hvsr_data['x_elev_m']['Z'] = hvsr_data['x_elev_m']['Z'] - elev_diff
        hvsr_data['x_elev_m']['E'] = hvsr_data['x_elev_m']['E'] - elev_diff
        hvsr_data['x_elev_m']['N'] = hvsr_data['x_elev_m']['N'] - elev_diff
        
        hvsr_data['x_elev_ft']['Z'] = hvsr_data['x_elev_m']['Z'] / 0.3048
        hvsr_data['x_elev_ft']['E'] = hvsr_data['x_elev_m']['E'] / 0.3048
        hvsr_data['x_elev_ft']['N'] = hvsr_data['x_elev_m']['N'] / 0.3048
    
    # Update elevations in Table_Report
    table_report_cols = ['Elevation', 'BedrockElevation']
    if hasattr(hvsr_data, 'Table_Report'):
        hvsr_data.Table_Report['Elevation'] = updated_surface_elevation
        if 'BedrockDepth' in hvsr_data.Table_Report.columns:
            hvsr_data.Table_Report['BedrockElevation'] = updated_surface_elevation - hvsr_data.Table_Report['BedrockDepth']

    # Update elevations in Print_Report
    if hasattr(hvsr_data, "Print_Report"):
        hvsr_data['Print_Report'] = re.sub(r"Elevation:\s*[\d.]+", 
                                            f"Elevation: {updated_surface_elevation}", 
                                            hvsr_data['Print_Report'])

    # Update elevations in HTML_Report
    if hasattr(hvsr_data, "HTML_Report"):
        hvsr_data['HTML_Report'] = re.sub(r"Elevation:\s*[\d.]+", 
                                            f"Elevation: {updated_surface_elevation}", 
                                            hvsr_data['HTML_Report'])
    
    # Update elevations in PeakReport attributes
    azList = ['HV']
    azList.extend(list(hvsr_data.hvsr_az.keys()))
    for az in azList:
        for peakReport in hvsr_data.PeakReport[az]:
            if 'Table_Report' in peakReport['Report']: #This is a dict
                peakReport['Report']['Table_Report']['Elevation'] = updated_surface_elevation
                if 'BedrockDepth' in peakReport['Report']['Table_Report'].columns:
                    peakReport['Report']['Table_Report']['BedrockElevation'] = updated_surface_elevation - peakReport['Report']['Table_Report']['BedrockDepth']
            
            if 'Print_Report' in peakReport['Report']: #This is a dict
                peakReport['Report']['Print_Report'] = re.sub(r"Elevation:\s*[\d.]+", 
                                                              f"Elevation: {updated_surface_elevation}", 
                                                              peakReport['Report']['Print_Report'])
                
    # Update processing_parameters to reflect new elevations
    hvsr_data['processing_parameters']['fetch_data']['params']['elevation'] = updated_surface_elevation
    hvsr_data['processing_parameters']['fetch_data']['params']['elev_unit'] = 'meters'
    hvsr_data['processing_parameters']['fetch_data']['params']['params']['elevation'] = updated_surface_elevation
    hvsr_data['processing_parameters']['fetch_data']['params']['params']['elev_unit'] = 'meters'
    
    return hvsr_data


# Update instrument response file headers in .resp format
def update_resp_file(resp_file, new_network, new_station, 
                     return_inv=True, new_channels='CHZ', new_location="",
                     starttime_new=None, endtime_new=None, new_resp_file=None,
                     existing_starttime='2015,001,00:00:00.0000', existing_endtime="No Ending Time",
                     existing_network='XX', existing_station='NS124', existing_channel='CHZ', existing_location='??'):
    """Function to update headers in .RESP instrument response files for easy copying.
       It is recommended to read this into a variable and set it as the metadata parameter of input_params
       if it is desired to correct for instrument response, for example.

    Parameters
    ----------
    resp_file : str
        Filepath to input response file
    new_network : str
        Name of network to update header to.
    new_station : str
        Name of station to update header to.
    return_inv : bool, optional
        Whether to return an obspy inventory object.
        If False, a .RESP file will be saved in the same directory as resp_file, by default True
    new_channels : str, optional
        Name or list of channels to update the header to.
        If list, multiple inventory objects will be created/saved, by default 'CHZ'
    new_location : str, optional
        New instrument location attribute to update header to, by default ""
    starttime : obspy.UTCDateTime, optional
        Input to update starttime. Must be readable by obspy.UTCDateTime(), by default None
    endtime : obspy.UTCDateTime, optional
        Input to update endtime. Must be readable by obspy.UTCDateTime(), by default None
    new_resp_file : str, optional
        Filepath to designate for .RESP file output, if desired (and return_inv=False)
        If None, uses same directory as resp_file, by default None
    existing_network : str, optional
        Name of network as specified in input file, by default 'XX'
    existing_station : str, optional
        name of station as specified in input file, by default 'NS124'
    existing_channel : str, optional
        Name of channel as specified in input file, by default 'CHZ'
    existing_location : str, optional
        Name of location as specified in input file, by default '??'

    Returns
    -------
    obspy.Inventory
        Only returned if return_inv = True
    """

    with open(resp_file) as inFile:
        respTextIN = inFile.read()

    respText = respTextIN.replace(existing_network, new_network)
    respText = respText.replace(existing_station, new_station)
    respTextNoChann = respText.replace(existing_location, new_location)
    if not isinstance(new_channels, (list, tuple)):
        new_channels = [new_channels]

    if starttime_new is not None:
        sTime = obspy.UTCDateTime(starttime_new)
        sTimeText = existing_starttime.replace('2015,', str(sTime.year)+',')
        sTimeText = sTimeText.replace('001,', str(sTime.julday)+',')
        sTimeText = sTimeText.replace('00:00:00.0000', str(sTime.strftime("%H:%M:%S.%f")))
        respTextNoChann = respTextNoChann.replace(existing_starttime, sTimeText)

    if endtime_new is not None:
        eTime = obspy.UTCDateTime(endtime_new)
        respTextNoChann = respTextNoChann.replace(existing_endtime, 
                                                  f"{eTime.year},{eTime.julday},{eTime.strftime('%H:%M:%S.%f')}")

    invList = []
    for i, newcha in enumerate(new_channels):
        print(newcha)
        respText = respTextNoChann.replace(existing_channel, newcha)

        if return_inv:
            invList.append(obspy.read_inventory(io.StringIO(respText)))
                        
        else:
            if new_resp_file is None:
                dir = pathlib.Path(resp_file).parent
                new_resp_file = dir.joinpath(f"RESP_{new_network}.{new_station}.{new_station}.{newcha}.resp")
            else:
                new_resp_file = pathlib.Path(new_resp_file)

            with open(new_resp_file.as_posix(), 'w') as outFile:
                outFile.write(new_resp_file.as_posix())
    
    if return_inv:
        for i, r in enumerate(invList):
            if i == 0:
                inv = r
            else:
                inv = inv + r
        return inv

# BATCH FUNCTIONS: various functions that are used to help the regular functions handle batch data
# Helper function for batch processing of check_peaks
def __check_peaks_batch(**check_peaks_kwargs):
    try:
        hvsr_data = check_peaks(**check_peaks_kwargs)
        if check_peaks_kwargs['verbose']:
            print('\t{} succesfully completed check_peaks()'.format(hvsr_data['input_params']['site']))    
    except:
        warnings.warn(f"Error in check_peaks({check_peaks_kwargs['hvsr_data']['input_params']['site']}, **check_peaks_kwargs)", RuntimeWarning)
        hvsr_data = check_peaks_kwargs['hvsr_data']
        
    return hvsr_data


# Support function for running batch
def __generate_ppsds_batch(**generate_psds_kwargs):
    try:
        params = generate_psds(**generate_psds_kwargs)
        if generate_psds_kwargs['verbose']:
            print('\t{} successfully completed generate_psds()'.format(params['site']))
    except Exception as e:
        print(e)
        warnings.warn(f"Error in generate_psds({generate_psds_kwargs['params']['site']}, **generate_psds_kwargs)", RuntimeWarning)
        params = generate_psds_kwargs['params']
        
    return params


# Helper function for batch processing of get_report
def __get_report_batch(**get_report_kwargs):

    try:
        hvsr_results = get_report(**get_report_kwargs)
        #Print if verbose, but selected report_formats was not print
        print('\n\n\n') #add some 'whitespace'
        if get_report_kwargs['verbose']:
            if 'print' in get_report_kwargs['report_formats']:
                pass
            else:
                get_report_kwargs['report_formats'] = 'print'
                get_report(**get_report_kwargs)
        
    except:
        warnMsg = f"Error in get_report({get_report_kwargs['hvsr_results']['input_params']['site']}, **get_report_kwargs)"
        if get_report_kwargs['verbose']:
            print('\t'+warnMsg)
        else:
            warnings.warn(warnMsg, RuntimeWarning)
        hvsr_results = get_report_kwargs['hvsr_results']
        
    return hvsr_results


# Helper function for batch procesing of azimuth
def __azimuth_batch(**azimuth_kwargs):
    try:
        hvsr_data = calculate_azimuth(**azimuth_kwargs)

        if azimuth_kwargs['verbose']:
            if 'input_params' in hvsr_data.keys():
                print('\t{} successfully completed calculate_azimuth()'.format(hvsr_data['input_params']['site']))
            elif 'site' in hvsr_data.keys():
                print('\t{} successfully completed calculate_azimuth()'.format(hvsr_data['site']))
    except Exception as e:
        warnings.warn(f"Error in calculate_azimuth({azimuth_kwargs['input']['site']}, **azimuth_kwargs)", RuntimeWarning)

    return hvsr_data


# Helper function for batch procesing of remove_noise
def __remove_noise_batch(**remove_noise_kwargs):
    try:
        hvsr_data = remove_noise(**remove_noise_kwargs)

        if remove_noise_kwargs['verbose']:
            if 'input_params' in hvsr_data.keys():
                print('\t{} successfully completed remove_noise()'.format(hvsr_data['input_params']['site']))
            elif 'site' in hvsr_data.keys():
                print('\t{} successfully completed remove_noise()'.format(hvsr_data['site']))
    except Exception as e:
        warnings.warn(f"Error in remove_noise({remove_noise_kwargs['input']['site']}, **remove_noise_kwargs)", RuntimeWarning)

    return hvsr_data


# Helper function batch processing of remove_outlier_curves
def __remove_outlier_curves(**remove_outlier_curves_kwargs):
    try:
        hvsr_data = remove_outlier_curves(**remove_outlier_curves_kwargs)

        if remove_outlier_curves_kwargs['verbose']:
            if 'input_params' in hvsr_data.keys():
                print('\t{} successfully completed remove_outlier_curves()'.format(hvsr_data['input_params']['site']))
            elif 'site' in hvsr_data.keys():
                print('\t{} successfully completed remove_outlier_curves()'.format(hvsr_data['site']))
    except Exception as e:
        warnings.warn(f"Error in remove_outlier_curves({remove_outlier_curves_kwargs['input']['site']}, **remove_outlier_curves_kwargs)", RuntimeWarning)

    return hvsr_data


# Batch function for plot_hvsr()
def __hvsr_plot_batch(**hvsr_plot_kwargs):
    try:
        hvsr_data = plot_hvsr(**hvsr_plot_kwargs)
    except:
        warnings.warn(f"Error in plotting ({hvsr_plot_kwargs['hvsr_data']['input_params']['site']}, **hvsr_plot_kwargs)", RuntimeWarning)
        hvsr_data = hvsr_plot_kwargs['hvsr_data']
        
    return hvsr_data


# Support function for batch of plot_azimuth()
def __plot_azimuth_batch(**plot_azimuth_kwargs):
    try:
        hvsr_data['Azimuth_Fig'] = plot_azimuth(**plot_azimuth_kwargs)
        if plot_azimuth_kwargs['verbose']:
            print('\t{} successfully completed plot_azimuth()'.format(hvsr_data['input_params']['site']))
    except:
        errMsg = f"Error in plot_azimuth({plot_azimuth_kwargs['params']['site']}, **plot_azimuth_kwargs)"
        if plot_azimuth_kwargs['verbose']:
            print('\t'+errMsg)
        else:
            warnings.warn(errMsg, RuntimeWarning)
        hvsr_data = plot_azimuth_kwargs['params']
        
    return hvsr_data


# Helper function for batch version of process_hvsr()
def __process_hvsr_batch(**process_hvsr_kwargs):
    try:
        hvsr_data = process_hvsr(**process_hvsr_kwargs)
        if process_hvsr_kwargs['verbose']:
            print('\t{} successfully completed process_hvsr()'.format(hvsr_data['input_params']['site']))
    except:
        errMsg=f"Error in process_hvsr({process_hvsr_kwargs['params']['site']}, **process_hvsr_kwargs)"
        if process_hvsr_kwargs['verbose']:
            print('\t'+errMsg)
        else:
            warnings.warn(errMsg, RuntimeWarning)
        hvsr_data = process_hvsr_kwargs['params']
        
    return hvsr_data

# OTHER HELPER FUNCTIONS

# HELPER functions for fetch_data() and get_metadata()
# Read in metadata .inv file, specifically for RaspShake
def _update_shake_metadata(filepath, params, write_path='', verbose=False):
    """Reads static metadata file provided for Rasp Shake and updates with input parameters. Used primarily in the get_metadata() function.

        PARAMETERS
        ----------
        filepath : str or pathlib.Path object
            Filepath to metadata file. Should be a file format supported by obspy.read_inventory().
        params : dict
            Dictionary containing necessary keys/values for updating, currently only supported for STATIONXML with Raspberry Shakes.
                Necessary keys: 'net', 'sta', 
                Optional keys: 'longitude', 'latitude', 'elevation', 'depth'
        write_path   : str, default=''
            If specified, filepath to write to updated inventory file to.

        Returns
        -------
        params : dict
            Updated params dict with new key:value pair with updated updated obspy.inventory object (key="inv")
    """
    if verbose:
        print("\tUpdating Metadata for Raspberry Shake Instrument Type")

    network = params['net']
    station = params['sta']
    optKeys = ['longitude', 'latitude', 'elevation', 'depth']
    for k in optKeys:
        if k not in params.keys():
            params[k] = '0'
    
    wgs84_transformer = Transformer.from_crs(params['input_crs'], "4326")
    
    xcoord = str(params['longitude'])
    ycoord = str(params['latitude'])
    elevation = str(params['elevation'])
    depth = str(params['depth'])
    
    
    startdate = str(datetime.datetime(year=2023, month=2, day=15)) #First day sprit code worked :)
    enddate=str(datetime.datetime.today())

    filepath = sprit_utils._checkifpath(filepath)
    tree = ET.parse(str(filepath))
    root = tree.getroot()

    prefix= "{http://www.fdsn.org/xml/station/1}"

    for item in root.iter(prefix+'Channel'):
        item.attrib['startDate'] = startdate
        item.attrib['endDate'] = enddate

    for item in root.iter(prefix+'Station'):
        item.attrib['code'] = station
        item.attrib['startDate'] = startdate
        item.attrib['endDate'] = enddate

    for item in root.iter(prefix+'Network'):
        item.attrib['code'] = network
        
    for item in root.iter(prefix+'Latitude'):
        item.text = ycoord

    for item in root.iter(prefix+'Longitude'):
        item.text = xcoord

    for item in root.iter(prefix+'Created'):
        nowTime = str(datetime.datetime.now())
        item.text = nowTime

    for item in root.iter(prefix+'Elevation'):
        item.text= elevation

    for item in root.iter(prefix+'Depth'):
        item.text=depth

    #Set up (and) export
    #filetag = '_'+str(datetime.datetime.today().date())
    #outfile = str(parentPath)+'\\'+filename+filetag+'.inv'

    if write_path != '':
        try:
            write_path = pathlib.Path(write_path)
            if write_path.is_dir():
                fname = params['network']+'_'+params['station']+'_'+params['site']
                fname = fname + '_response.xml'
                write_file = write_path.joinpath(fname)
            else:
                write_file=write_path
            tree.write(write_file, xml_declaration=True, method='xml',encoding='UTF-8')
            inv = obspy.read_inventory(write_file, format='STATIONXML', level='response')
        except:
            warnings.warn(f'write_path={write_path} is not recognized as a filepath, updated metadata file will not be written')
            write_path=''
    else:
        try:
            #Create temporary file for reading into obspy
            tpf = tempfile.NamedTemporaryFile(delete=False)
            stringRoot = ET.tostring(root, encoding='UTF-8', method='xml')
            tpf.write(stringRoot)

            inv = obspy.read_inventory(tpf.name, format='STATIONXML', level='response')
            tpf.close()

            os.remove(tpf.name)
        except:
            write_file = pathlib.Path(__file__).with_name('metadata.xml')
            tree.write(write_file, xml_declaration=True, method='xml',encoding='UTF-8')
            inv = obspy.read_inventory(write_file.as_posix(), format='STATIONXML', level='response')
            os.remove(write_file.as_posix())

    params['inv'] = inv
    params['params']['inv'] = inv
    return params


# Support function for get_metadata()
def _read_RS_Metadata(params, source=None):
    """Function to read the metadata from Raspberry Shake using the StationXML file provided by the company.
    Intended to be used within the get_metadata() function.

    Parameters
    ----------
    params : dict
        The parameter dictionary output from input_params() and read into get_metadata()

    Returns
    -------
    params : dict
        Further modified parameter dictionary
    """
    if 'inv' in params.keys():
        inv = params['inv']
    else:
        sprit_utils._checkifpath(params['metadata'])
        inv = obspy.read_inventory(params['metadata'], format='STATIONXML', level='response')
        params['inv'] = inv

    station = params['sta']
    network = params['net']
    channels = params['cha']

    if isinstance(inv, obspy.core.inventory.inventory.Inventory):
        #Create temporary file from inventory object
        tpf = tempfile.NamedTemporaryFile(delete=False)
        inv.write(tpf.name, format='STATIONXML')

        #Read data into xmlTree
        tree = ET.parse(tpf.name)
        root = tree.getroot()

        #Close and remove temporary file
        tpf.close()
        os.remove(tpf.name)
    else:
        inv = sprit_utils._checkifpath(inv)
        inv = obspy.read_inventory(params['metadata'], format='STATIONXML', level='response')
        params['inv'] = inv
        tree = ET.parse(inv)
        root = tree.getroot()

    #if write_path != '':
    #    inv.write(write_path, format='STATIONXML')

    #This is specific to RaspShake
    c=channels[0]
    pzList = [str(n) for n in list(range(7))]
    s=pzList[0]

    prefix= "{http://www.fdsn.org/xml/station/1}"

    sensitivityPath = "./"+prefix+"Network[@code='"+network+"']/"+prefix+"Station[@code='"+station+"']/"+prefix+"Channel[@code='"+c+"']/"+prefix+"Response/"+prefix+"InstrumentSensitivity/"+prefix+"Value"
    gainPath = "./"+prefix+"Network[@code='"+network+"']/"+prefix+"Station[@code='"+station+"']/"+prefix+"Channel[@code='"+c+"']/"+prefix+"Response/"+prefix+"Stage[@number='1']/"+prefix+"StageGain/"+prefix+"Value"

    #paz = []
    rsCList = ['EHZ', 'EHN', 'EHE']
    paz = {}
    for c in channels:
        channelPaz = {}
        #channelPaz['channel'] = c
        for item in root.findall(sensitivityPath):
            channelPaz['sensitivity']=float(item.text)

        for item in root.findall(gainPath):
            channelPaz['gain']=float(item.text)
        
        poleList = []
        zeroList = []
        for s in pzList:
            if int(s) < 4:
                polePathReal = "./"+prefix+"Network[@code='"+network+"']/"+prefix+"Station[@code='"+station+"']/"+prefix+"Channel[@code='"+c+"']/"+prefix+"Response/"+prefix+"Stage[@number='1']/"+prefix+"PolesZeros/"+prefix+"Pole[@number='"+s+"']/"+prefix+"Real"
                polePathImag = "./"+prefix+"Network[@code='"+network+"']/"+prefix+"Station[@code='"+station+"']/"+prefix+"Channel[@code='"+c+"']/"+prefix+"Response/"+prefix+"Stage[@number='1']/"+prefix+"PolesZeros/"+prefix+"Pole[@number='"+s+"']/"+prefix+"Imaginary"
                for poleItem in root.findall(polePathReal):
                    poleReal = poleItem.text
                for poleItem in root.findall(polePathImag):
                    pole = complex(float(poleReal), float(poleItem.text))
                    poleList.append(pole)
                    channelPaz['poles'] = poleList
                    #channelPaz['poles'] = list(set(poleList))
            else:
                zeroPathReal = "./"+prefix+"Network[@code='"+network+"']/"+prefix+"Station[@code='"+station+"']/"+prefix+"Channel[@code='"+c+"']/"+prefix+"Response/"+prefix+"Stage[@number='1']/"+prefix+"PolesZeros/"+prefix+"Zero[@number='"+s+"']/"+prefix+"Real"
                zeroPathImag = "./"+prefix+"Network[@code='"+network+"']/"+prefix+"Station[@code='"+station+"']/"+prefix+"Channel[@code='"+c+"']/"+prefix+"Response/"+prefix+"Stage[@number='1']/"+prefix+"PolesZeros/"+prefix+"Zero[@number='"+s+"']/"+prefix+"Imaginary"
                for zeroItem in root.findall(zeroPathReal):
                    zeroReal = zeroItem.text
                
                for zeroItem in root.findall(zeroPathImag):
                    zero = complex(float(zeroReal), float(zeroItem.text))
                    #zero = zeroReal + "+" + zeroItem.text+'j'
                    zeroList.append(zero)
                    #channelPaz['zeros'] = list(set(zeroList))
                    channelPaz['zeros'] = zeroList
        if str(c).upper() in rsCList:
            c = str(c)[-1].upper()
        paz[str(c)] = channelPaz
    params['paz'] = paz
    params['params']['paz'] = paz

    return params


# Helper function to sort channels
def _sort_channels(input, source, verbose):
    if source!='batch':
        input = {'SITENAME': {'stream':input}} #Make same structure as batch

    for site in input.keys():
        rawDataIN = input[site]['stream']

        if rawDataIN is None:
            if verbose:
                raise RuntimeError("No data was read using specified parameters {}".format(input[site]))
            else:
                raise RuntimeError("No data was read using specified parameters")

        elif isinstance(rawDataIN, obspy.core.stream.Stream):
            #Make sure z component is first
            dataIN = rawDataIN.sort(['channel'], reverse=True) #z, n, e order
        else:
            #Not usually used anymore, retained just in case
            dataIN = []
            for i, st in enumerate(rawDataIN):
                if 'Z' in st[0].stats['channel']:#).split('.')[3]:#[12:15]:
                    dataIN.append(rawDataIN[i])
                else:
                    dataIN.append(rawDataIN[i].sort(['channel'], reverse=True)) #z, n, e order            

        input[site]['stream'] = dataIN
            
    if source=='batch':
        #Return a dict
        output = input
    else:
        #Return a stream otherwise
        output = input[site]['stream']
    return output


# Trim data 
def _trim_data(input, stream=None, export_dir=None, data_export_format=None, source=None, **kwargs):
    """Function to trim data to start and end time

        Trim data to start and end times so that stream being analyzed only contains wanted data.
        Can also export data to specified directory using a specified site name and/or data_export_format

        Parameters
        ----------
            input  : HVSRData
                HVSR Data class containing input parameters for trimming
            stream  : obspy.stream object  
                Obspy stream to be trimmed
            export_dir: str or pathlib obj   
                Output filepath to export trimmed data to. If not specified, does not export. 
            data_export_format  : str or None, default=None  
                If None, and export_dir is specified, format defaults to .mseed. Otherwise, exports trimmed stream using obspy.core.stream.Stream.write() method, with data_export_format being passed to the format argument. 
                https://docs.obspy.org/packages/autogen/obspy.core.stream.Stream.write.html#obspy.core.stream.Stream.write
            **kwargs
                Keyword arguments passed directly to obspy.core.stream.Stream.trim() method.
                
        Returns
        -------
            st_trimmed  : obspy.stream object 
                Obpsy Stream trimmed to start and end times
    """
    #if source!='batch':
    #    #input = {'SITENAME': {'stream':input}} #Make same structure as batch
    #    pass

    if 'starttime' in kwargs.keys():
        start = kwargs['starttime']
    elif isinstance(input, (HVSRData, dict)):
        start = input['starttime']
    
    if 'endtime' in kwargs.keys():
        end = kwargs['endtime']
    else:
        end = input['endtime']
        
    if 'site' in kwargs.keys():
        site = kwargs['site']
    else:
        site = input['site']

    if stream is not None:
        st_trimmed = stream.copy()
    elif 'stream' in input.keys():
        st_trimmed = input['stream'].copy()
    else:
        raise UnboundLocalError("stream not specified. Must either be specified using stream parameter or as a key in the input parameters (input['stream'])")
        
    trimStart = obspy.UTCDateTime(start)
    trimEnd = obspy.UTCDateTime(end)

    #If data is contained in a masked array, split to undo masked array
    if isinstance(st_trimmed[0].data, np.ma.masked_array):
        st_trimmed = st_trimmed.split()
        #This split is undone with the .merge() method a few lines down

    for tr in st_trimmed:
        if trimStart > tr.stats.endtime or trimEnd < tr.stats.starttime:
            pass
        else:
            st_trimmed.trim(starttime=trimStart, endtime=trimEnd, **kwargs)

    st_trimmed.merge(method=1)

    if data_export_format is None:
        data_export_format = '.mseed'

    #Format export filepath, if exporting
    if export_dir is not None:
        if site is None:
            site=''
        else:
            site = site+'_'
        if '.' not in data_export_format:
            data_export_format = '.'+data_export_format
        net = st_trimmed[0].stats.network
        sta = st_trimmed[0].stats.station
        loc = st_trimmed[0].stats.location
        yr = str(st_trimmed[0].stats.starttime.year)
        strtD=str(st_trimmed[0].stats.starttime.date)
        strtT=str(st_trimmed[0].stats.starttime.time)[0:2]
        strtT=strtT+str(st_trimmed[0].stats.starttime.time)[3:5]
        endT = str(st_trimmed[0].stats.endtime.time)[0:2]
        endT = endT+str(st_trimmed[0].stats.endtime.time)[3:5]
        doy = str(st_trimmed[0].stats.starttime.utctimetuple().tm_yday).zfill(3)

        export_dir = sprit_utils._checkifpath(export_dir)
        export_dir = str(export_dir)
        export_dir = export_dir.replace('\\', '/')
        export_dir = export_dir.replace('\\'[0], '/')

        if type(data_export_format) is str:
            filename = site+net+'.'+sta+'.'+loc+'.'+yr+'.'+doy+'_'+strtD+'_'+strtT+'-'+endT+data_export_format
        elif type(data_export_format) is bool:
            filename = site+net+'.'+sta+'.'+loc+'.'+yr+'.'+doy+'_'+strtD+'_'+strtT+'-'+endT+'.mseed'

        if export_dir[-1]=='/':
            export_dir=export_dir[:-1]
        
        exportFile = export_dir+'/'+filename

        #Take care of masked arrays for writing purposes
        if 'fill_value' in kwargs.keys():
            for tr in st_trimmed:
                if isinstance(tr.data, np.ma.masked_array):
                    tr.data = tr.data.filled(kwargs['fill_value'])
        else:
            st_trimmed = st_trimmed.split()
        
        st_trimmed.write(filename=exportFile)
    else:
        pass

    return st_trimmed


# Helper function to detrend data
def __detrend_data(input, detrend, detrend_options, verbose, source):
    """Helper function to detrend data, specifically formatted for the HVSRData and HVSRBatch objects"""
    if source != 'batch':
        input = {'SITENAME': {'stream':input}} #Make same structure as batch

    for key in input.keys():
        dataIN = input[key]['stream']
        if detrend==False:
            pass
        elif detrend==True:
            #By default, do a spline removal
            for tr in dataIN:
                tr.detrend(type='spline', order=detrend_options, dspline=1000)        
        else:
            data_undetrended = dataIN.copy()
            try:
                if str(detrend).lower()=='simple':
                    for tr in dataIN:
                        tr.detrend(type=detrend)
                if str(detrend).lower()=='linear':
                    for tr in dataIN:
                        tr.detrend(type=detrend)
                if str(detrend).lower()=='constant' or detrend=='demean':
                    for tr in dataIN:
                        tr.detrend(type=detrend)                
                if str(detrend).lower()=='polynomial':
                    for tr in dataIN:
                        tr.detrend(type=detrend, order=detrend_options)   
                if str(detrend).lower()=='spline':
                    for tr in dataIN:
                        tr.detrend(type=detrend, order=int(detrend_options), dspline=1000)       
            except Exception as e:
                try:
                    for tr in dataIN:
                        tr.detrend(type='constant')
                    print(f'\tDetrend type {detrend} could not be carried out, using "constant" detrend instead.\n')
                except Exception as e2:                        
                    dataIN = data_undetrended
                    if verbose:
                        warnings.warn(f"\tDetrend error, data not detrended. \nDetrend Error Report below. Carrying on processing with non-detrended data: {e}",  UserWarning)
            
        input[key]['stream'] = dataIN

    if source=='batch':
        #Return a dict
        output = input
    else:
        #Return a stream otherwise
        output = input[key]['stream']
    return output


# Helper function to read data from Tromino Blue instruments
def __read_tromino_data_blue(input_data, sampling_rate=None, 
                            channel_map={'Z':6, 'E':4, 'N':2}, data_start_buffer=113,
                            return_dict=False, verbose=False):
    
    # Reconfigure data for some of the analysis
    swapped = __swap_bytes(input_data) 

    # Initialize a result dictionary
    result = {
        'header': {},
        'gps_data': [],
        'seismometer_data': None, # Will be replaced with a (7, n) numpy array
        'stream': None 
        }
    
    # Extract header information (text sections)
    header_text = __extract_text_sections(swapped)
    for text in header_text:
        if b'NAKAGRILLA FLASHCARD HEADER' in text:
            result['header']['file_type'] = text.decode('ascii', errors='ignore').strip('\x00')
        # Add more header parsing as needed
    
    # Extract GPS NMEA sentences
    gps_data = __extract_gps_data(swapped)
    for sentence in gps_data:
        if sentence.startswith('$GPGGA'):
            # Parse GPGGA sentence (position data)
            parts = sentence.split(',')
            if len(parts) >= 15:
                try:
                    timestamp = parts[1]
                    lat = float(parts[2][:2]) + float(parts[2][2:]) / 60 if parts[2] else None
                    lat_dir = parts[3]
                    lon = float(parts[4][:3]) + float(parts[4][3:]) / 60 if parts[4] else None
                    lon_dir = parts[5]
                    
                    if lat_dir == 'S':
                        lat = -lat
                    if lon_dir == 'W':
                        lon = -lon
                        
                    result['gps_data'].append({
                        'type': 'GPGGA',
                        'timestamp': timestamp,
                        'latitude': lat,
                        'longitude': lon,
                        'raw': sentence
                    })
                except (ValueError, IndexError):
                    result['gps_data'].append({'type': 'GPGGA', 'raw': sentence, 'parse_error': True})
        
        elif sentence.startswith('$GPZDA'):
            # Parse GPZDA sentence (date & time)
            parts = sentence.split(',')
            if len(parts) >= 5:
                try:
                    timestamp = parts[1]
                    day = parts[2]
                    month = parts[3]
                    year = parts[4]
                    
                    result['gps_data'].append({
                        'type': 'GPZDA',
                        'timestamp': timestamp,
                        'date': f"{year}-{month}-{day}",
                        'raw': sentence
                    })
                except (ValueError, IndexError):
                    result['gps_data'].append({'type': 'GPZDA', 'raw': sentence, 'parse_error': True})
    
    # Extract seismometer data
    # Find the start of seismometer data section (after GPS data)
    seis_data_start = __locate_data_start_blue(swapped)
    
    # Get seismic starting buffer
    for item in header_text:
        if "FIRST DATA" in str(item):
            data_buffer = data_start_buffer #137#int(str(item).split('-')[2].split("ADDRES ")[1].split('.')[0])

    # Get sampling rate
    if sampling_rate is None:
        for item in header_text:
            if "PER SECOND" in str(item):
                sampling_rate = int(str(item).split('-')[1].split("BYTE ")[1].split('PER')[0])
        if verbose:
            print('\tSampling rate detected as:', sampling_rate)

    # Read the file as simple bytes
    with open(input_data, 'rb') as f:
        #data_start_byte SHOULD NOT BE HARDCODED! (will eventually determine)
        f.seek(seis_data_start + data_buffer)
        # Read the rest of the file
        raw_bytes = f.read()
    #raw_bytes = swapped[seis_data_start + data_buffer:]

    # Assign variables for reading data
    bytes_per_sample = 2  # 16-bit
    num_channels = 7 #3x accel, 3x seism, 1x trigger
    total_samples = len(raw_bytes) // bytes_per_sample

    # Decode all samples
    values = []
    for i in range(total_samples):
        start_byte = i * bytes_per_sample
        sample_bytes = raw_bytes[start_byte:start_byte + bytes_per_sample]
        
        # Try little-endian first
        value = int.from_bytes(sample_bytes, byteorder='little', signed=True)
        values.append(value)

    # Convert to numpy array
    data = np.array(values, dtype=np.int32)

    # Ensure we have complete sets of channel data
    usable_samples = (len(data) // num_channels) * num_channels
    channel_data = data[:usable_samples].reshape(-1, num_channels)

    if verbose:
        # Analyze the data
        zero_percent = np.sum(channel_data == 0) / channel_data.size * 100
        print(f"Zero percentage: {zero_percent:.2f}%")

        # Check zeros by channel
        zeros_by_channel = np.sum(channel_data == 0, axis=0)
        samples_per_channel = channel_data.shape[0]
        print("Zero percentage by channel:")
        for i in range(num_channels):
            channel_zero_percent = zeros_by_channel[i] / samples_per_channel * 100
            print(f"Channel {i+1}: {channel_zero_percent:.2f}%")

        # Plot the first 1000 samples of each channel
        plt.figure(figsize=(15, 12))
        for i in range(num_channels):
            plt.subplot(num_channels, 1, i+1)
            plt.plot(channel_data[:1000, i])
            plt.title(f"Channel {i}")
            plt.grid(True)
        plt.tight_layout()
        plt.show()


    # Extract data from GPS strings
    acq_date = obspy.UTCDateTime().now()
    sTime = datetime.time()
    latPts = []
    lonPts = []
    elevPts = []

    for gpsPt in result['gps_data']:
        if 'ZDA' in gpsPt['type']:
            if 'timestamp' in gpsPt:
                sTime = datetime.time(int(gpsPt['timestamp'][:2]), int(gpsPt['timestamp'][2:4]), int(gpsPt['timestamp'][4:6]))
            if 'date' in gpsPt:
                acq_date=obspy.UTCDateTime(gpsPt['date'])

        if 'GGA' in gpsPt['type']:
            latPts.append(gpsPt['latitude'])
            lonPts.append(gpsPt['longitude'])
            elevPts.append(float(gpsPt['raw'].split(',')[9]))
        
    acq_date = acq_date + (sTime.hour* 60*60 + sTime.minute*60 + sTime.second)
    stats = {'network':'TR',
            'station':'BLUE',
            'sampling_rate':sampling_rate,
            'starttime':acq_date,
            'longitude': round(float(np.nanmedian(lonPts)), 7),
            'latitude':round(float(np.nanmedian(latPts)), 7),
            'input_crs':'EPSG:4326',
            'elevation':round(float(np.nanmedian(elevPts)), 7),
            'elev_unit':'m',
            'instrument': 'Tromino Blue'
            }
    
    stats['channel'] = 'EHN'
    nTrace = obspy.Trace(data=channel_data.T[channel_map['N']], header=stats)
    stats['channel'] = 'EHE'
    eTrace = obspy.Trace(data=channel_data.T[channel_map['E']], header=stats)
    stats['channel'] = 'EHZ'
    zTrace = obspy.Trace(data=channel_data.T[channel_map['Z']], header=stats)

    st = obspy.Stream([zTrace, eTrace, nTrace])

    result['stream'] = st

    if return_dict:
        return result

    return st


def __extract_text_sections(data):
    """Extract text sections from binary data"""
    # Find blocks of ASCII text (simple approach)
    text_sections = []
    
    # Look for consecutive printable ASCII characters
    ascii_chunks = re.finditer(rb'[A-Za-z0-9 \t\r\n\.,_\-\+\*\/\$]{6,}', data)
    for match in ascii_chunks:
        text_sections.append(match.group(0))
    
    return text_sections


def __extract_gps_data(data):
    """Extract GPS NMEA sentences from binary data"""
    # NMEA sentences start with $ and end with \r\n
    data_str = data.decode('ascii', errors='ignore')
    
    # Look for NMEA sentences
    gps_sentences = []
    nmea_pattern = r'\$(GP[A-Z]{3},.+?)\r\n'
    matches = re.finditer(nmea_pattern, data_str)
    
    for match in matches:
        gps_sentences.append(match.group(0))
    
    return gps_sentences


def __locate_data_start_blue(data):
    """This function looks after the last GPS point for an intitial, likely starting position of seismometer data"""
    
    # Look for the last NMEA sentence and start from there (small skip ahead
    data_str = data.decode('ascii', errors='ignore')
    last_nmea_pos = data_str.rfind('$GP')

    
    # Assuming we find GPS data, find the spot after that indicating a new line
    if last_nmea_pos > 0:
        # Find the end of this sentence
        end_GPS_marker = data_str.find('\r\n', last_nmea_pos)
        #end_marker = data_str.find('[', last_nmea_pos)

        if end_GPS_marker > 0:
            # Skip a bit further to be safe
            return end_GPS_marker + 8
    
    return end_GPS_marker


def __swap_bytes(input_file):
    """
    Private function (not meant to be called except by internal functions) 
    to read a binary file and return a bytearray with all bytes swapped in pairs.
    This handles odd-length files correctly.
    """

    # Open binary file
    with open(input_file, 'rb') as f:
        data = f.read()
    
    # Create new byte array for the swapped data
    swapped = bytearray(len(data))
    
    # Swap bytes in pairs
    for i in range(0, len(data) - 1, 2):
        swapped[i] = data[i + 1]
        swapped[i + 1] = data[i]
    
    # Handle odd length
    if len(data) % 2 == 1:
        swapped[-1] = data[-1]
    
    return swapped


# Read data from raspberry shake
def __read_RS_file_struct(input_data, source, year, doy, inv, params, verbose=False):
    """"Private function used by fetch_data() to read in Raspberry Shake data"""
    from obspy.core import UTCDateTime
    fileList = []
    folderPathList = []
    filesinfolder = False
    input_data = sprit_utils._checkifpath(input_data)
    #Read RS files
    if source=='raw': #raw data with individual files per trace
        if input_data.is_dir():
            for child in input_data.iterdir():
                if child.is_file() and child.name.startswith('AM') and str(doy).zfill(3) in child.name and str(year) in child.name:
                    filesinfolder = True
                    folderPathList.append(input_data)
                    fileList.append(child)
                elif child.is_dir() and child.name.startswith('EH') and not filesinfolder:
                    folderPathList.append(child)
                    for c in child.iterdir():
                        if c.is_file() and c.name.startswith('AM') and c.name.endswith(str(doy).zfill(3)) and str(year) in c.name:
                            fileList.append(c)


            if len(fileList) == 0:
                doyList = []
                printList= []
                for j, folder in enumerate(folderPathList):
                    for i, file in enumerate(folder.iterdir()):
                        if j ==0:
                            doyList.append(str(year) + ' ' + str(file.name[-3:]))
                            printList.append(f"{datetime.datetime.strptime(doyList[i], '%Y %j').strftime('%b %d')} | Day of year: {file.name[-3:]}")
                if len(printList) == 0:
                    warnings.warn('No files found matching Raspberry Shake data structure or files in specified directory.')
                else:
                    warnings.warn(f'No file found for specified date: {params["acq_date"]}. The following days/files exist for specified year in this directory')
                    for p in printList:
                        print('\t',p)
                return None
            elif len(fileList) !=3:
                warnings.warn('3 channels needed! {} found.'.format(len(folderPathList)), UserWarning)
            else:
                fileList.sort(reverse=True) # Puts z channel first
                folderPathList.sort(reverse=True)
                if verbose:
                    print('\n\tReading files: \n\t{}\n\t{}\n\t{}'.format(fileList[0].name, fileList[1].name, fileList[2].name))

            traceList = []
            for i, f in enumerate(fileList):
                with warnings.catch_warnings():
                    warnings.filterwarnings(action='ignore', message='^readMSEEDBuffer()')
                    st = obspy.read(str(f))#, starttime=UTCDateTime(params['starttime']), endtime=UTCDateTime(params['endtime']), nearest_sample=False)
                    st = st.split()
                    st.trim(starttime=UTCDateTime(params['starttime']), endtime=UTCDateTime(params['endtime']), nearest_sample=False)
                    st.merge()
                    tr = (st[0])
                    #tr= obspy.Trace(tr.data,header=meta)
                    traceList.append(tr)
            rawDataIN = obspy.Stream(traceList)

        else:
            rawDataIN = obspy.read(str(input_data), starttime=UTCDateTime(params['starttime']), endttime=UTCDateTime(params['endtime']), nearest_sample=True)

    elif source=='dir': #files with 3 traces, but may be several in a directory or only directory name provided
        OBSPY_FORMATS = ['AH','ALSEP_PSE','ALSEP_WTH','ALSEP_WTN','CSS','DMX','GCF','GSE1','GSE2','KINEMETRICS_EVT','MSEED','NNSA_KB_CORE','PDAS','PICKLE','Q','REFTEK130','RG16','SAC','SACXY','SEG2','SEGY','SEISAN','SH_ASC','SLIST','SU','TSPAIR','WAV','WIN','Y']
        for file in input_data.iterdir():
            ext = file.suffix[1:]
            rawFormat = False
            if ext.isnumeric():
                if float(ext) >= 0 and float(ext) < 367:
                    rawFormat=True
            
            if ext.upper() in OBSPY_FORMATS or rawFormat:
                filesinfolder = True
                folderPathList.append(input_data)
                fileList.append(file.name)
                        
        filepaths = []
        rawDataIN = obspy.Stream()
        for i, f in enumerate(fileList):
            filepaths.append(folderPathList[i].joinpath(f))
            #filepaths[i] = pathlib.Path(filepaths[i])
            currData = obspy.read(filepaths[i])
            currData.merge()
            #rawDataIN.append(currData)
            #if i == 0:
            #    rawDataIN = currData.copy()
            if isinstance(currData, obspy.core.stream.Stream):
                rawDataIN += currData.copy()
        #rawDataIN = obspy.Stream(rawDataIN)
        if type(rawDataIN) is list and len(rawDataIN)==1:
            rawDataIN = rawDataIN[0]
    elif source=='file':
        rawDataIN = obspy.read(str(input_data), starttime=UTCDateTime(params['starttime']), endttime=UTCDateTime(params['endtime']), nearest=True)
        rawDataIN.merge()   
    elif isinstance(source, (list, tuple)):
        print('List of sources not currently supported')
        pass  # Eventually do something

    return rawDataIN


# Helper functions for remove_noise()
# Helper function for removing gaps
def __remove_gaps(stream, window_gaps_obspy):
    """Helper function for removing gaps"""
    
    # combine overlapping windows
    overlapList = []
    for i in range(len(window_gaps_obspy)-2):
        if window_gaps_obspy[i][1] > window_gaps_obspy[i+1][0]:
            overlapList.append(i)
    
    for i, t in enumerate(overlapList):
        if i < len(window_gaps_obspy)-2:
            window_gaps_obspy[i][1] = window_gaps_obspy[i+1][1]
            window_gaps_obspy.pop(i+1)

    # Add streams
    window_gaps_s = []
    for w, win in enumerate(window_gaps_obspy):
        if w == 0:
            pass
        elif w == len(window_gaps_obspy)-1:
            pass
        else:
            window_gaps_s.append(win[1]-win[0])
    
    if len(window_gaps_s) > 0:
        stream_windows = []
        j = 0
        for i, window in enumerate(window_gaps_s):
            j=i
            newSt = stream.copy()
            stream_windows.append(newSt.trim(starttime=window_gaps_obspy[i][1], endtime=window_gaps_obspy[i+1][0]))
        i = j + 1
        newSt = stream.copy()
        stream_windows.append(newSt.trim(starttime=window_gaps_obspy[i][1], endtime=window_gaps_obspy[i+1][0]))

        for i, st in enumerate(stream_windows):
            if i == 0:
                outStream = st.copy()
            else:
                newSt = st.copy()
                gap = window_gaps_s[i-1]
                outStream = outStream + newSt.trim(starttime=st[0].stats.starttime - gap, pad=True, fill_value=None)
        outStream.merge()
    else:
        outStream = stream.copy()

    return outStream


# Helper function for getting windows to remove noise using stalta antitrigger method
def __remove_anti_stalta(stream, sta, lta, thresh, show_stalta_plot=False, verbose=False):
    """Helper function for getting windows to remove noise using stalta antitrigger method

    Parameters
    ----------
    stream : obspy.core.stream.Stream object
        Input stream on which to perform noise removal
    sta : int
        Number of seconds to use as short term window, reads from remove_noise() function.
    lta : int
        Number of seconds to use as long term window, reads from remove_noise() function.
    thresh : list
        Two-item list or tuple with the thresholds for the stalta antitrigger. 
        Reads from remove_noise() function. The first value (index [0]) is the lower threshold (below which trigger is deactivated), 
        the second value (index [1] is the upper threshold (above which trigger is activated)), by default [8, 8]
    show_plot : bool
        If True, will plot the trigger and stalta values. Reads from remove_noise() function, by default False.

    Returns
    -------
    outStream : obspy.core.stream.Stream object
        Stream with a masked array for the data where 'noise' has been removed

    """
    from obspy.signal.trigger import classic_sta_lta

    if verbose:
        print(f'\tRemoving noise using sta/lta antitrigger method: sta={sta}, lta={lta}, stalta_thresh={thresh}')
    sampleRate = float(stream[0].stats.delta)

    sta_samples = sta / sampleRate #Convert to samples
    lta_samples = lta / sampleRate #Convert to samples
    staltaStream = stream.copy()
    cFunList = []

    for t, tr in enumerate(staltaStream):
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=UserWarning)
            cFunList.append(classic_sta_lta(tr, nsta=sta_samples, nlta=lta_samples))

    if show_stalta_plot is True:
        obspy.signal.trigger.plot_trigger(tr, cFunList[0], thresh[1], thresh[0])
    elif type(show_stalta_plot) is int:
        obspy.signal.trigger.plot_trigger(tr, cFunList[show_stalta_plot], thresh[1], thresh[0])

    windows_samples = []
    for t, cf in enumerate(cFunList):
        if len(obspy.signal.trigger.trigger_onset(cf, thresh[1], thresh[0])) > 0:
            windows_samples.extend(obspy.signal.trigger.trigger_onset(cf, thresh[1], thresh[0]).tolist())
    def condense_window_samples(win_samples):
        # Sort the list of lists based on the first element of each internal list
        sorted_list = sorted(win_samples, key=lambda x: x[0])
        
        # Initialize an empty result list
        result = []
        if len(win_samples) == 0:
            return result
        # Initialize variables to track the current range
        start, end = sorted_list[0]
        
        # Iterate over the sorted list
        for i in range(1, len(sorted_list)):
            current_start, current_end = sorted_list[i]
            
            # If the current range overlaps with the previous range
            if current_start <= end:
                # Update the end of the current range
                end = max(end, current_end)
            else:
                # Add the previous range to the result and update the current range
                result.append([start, end])
                start, end = current_start, current_end
        
        # Add the last range to the result
        result.append([start, end])
        
        return result        
    windows_samples = condense_window_samples(windows_samples)

    startT = stream[0].stats.starttime
    endT = stream[0].stats.endtime
    window_UTC = []
    window_MPL = []
    window_UTC.append([startT, startT])
    for w, win in enumerate(windows_samples):
        for i, t in enumerate(win):
            if i == 0:
                window_UTC.append([])
                window_MPL.append([])
            trigShift = sta
            if trigShift > t * sampleRate:
                trigShift = 0
            tSec = t * sampleRate - trigShift
            window_UTC[w+1].append(startT+tSec)
            window_MPL[w].append(window_UTC[w][i].matplotlib_date)
    
    window_UTC.append([endT, endT])
    #window_MPL[w].append(window_UTC[w][i].matplotlib_date)
    outStream = __remove_gaps(stream, window_UTC)
    return outStream


# Helper function for getting windows to remove noise using moving stdev
def __remove_moving_std(stream, std_ratio_thresh=2, std_window_s=20, min_win_size=2):
    """Helper function for removing noisy data due to high local standard deviation.
    This is similar to the default noise removal method used in Grilla software.

    Parameters
    ----------
    stream : obspy.Stream
        Obspy stream that should be analyzed and segmented for noise removal
    std_ratio_thresh : float, optional
        Threshold ratio value to use for removing data.
        Ratio is calculated as the total standard deviation (of entire trace) over 
        moving/local standard deviation (over rolling window specified by std_window_s), by default 2
    std_window_s : float, optional
        Size of the rolling window in seconds to use to calculate the local/moving/rolling standard deviation, by default 20
    min_win_size : float, optional
        The minimum size of window in seconds for data removal (where all points in that window exceed std_ratio_thresh), by default 5

    Returns
    -------
    obspy.Stream
        Obspy Stream object with "noisy" windows calculated by remove_moving_std masked, if applicable.
    """
    instream = stream.copy()
    outstream = instream.copy()

    removeDTs = pd.DatetimeIndex([], tz='UTC')  # Empty index to start
    # Use pandas to simplify rolling/moving std
    for tr in instream.split():
        dtList = []
        for t in tr.times(type="utcdatetime"):
            dtList.append(t.datetime.replace(tzinfo=zoneinfo.ZoneInfo('UTC')))
        # Create pandas series out of trace data
        traceData = pd.Series(data=tr.data,
                            index=dtList)

        # Get StDev values
        totalSTD = traceData.std()
        movingSTD = traceData.rolling(datetime.timedelta(seconds=std_window_s), center=True).std()

        # Calculate whether ratio is larger than threshold value
        boolseries = np.abs(movingSTD/totalSTD) > std_ratio_thresh

        # Create index of just removed windows
        removeDTs = removeDTs.join(boolseries.iloc[np.nonzero(boolseries)[0]].index, how='outer')

    # Get unique indices as datetime.datetime objects
    removeDTs = removeDTs.unique()  # Get unique dtindex
    removeDTs.sort_values()  # Sort dt index
    removeDTs = removeDTs.to_pydatetime()  # Convert to np.array of datetime.datetime objs

    delta = stream[0].stats.delta  # Get sample rate

    # Convert instances of mstd/totstd > thresh to windows (keep if longer than min_win_size)
    windows = []
    windex = 0
    for i, rdt in enumerate(removeDTs):
        if i == 0:
            # Intialize windows list
            windows.append([rdt, None])
        else:
            # If the "window" is just two samples next to each other, keep moving
            if (rdt - removeDTs[i-1]).total_seconds() == delta:
                pass
            elif (rdt - removeDTs[i-1]).total_seconds() < delta:
                # if for some reason the window is less than sample rate, move on
                pass
            else:
                # if window exists, but is smaller than min_win_size
                if (removeDTs[i-1] - windows[windex][0]).total_seconds() < min_win_size:
                    windows.pop()  # remove this window
                    windows.append([removeDTs[i+1], None]) # Rest the window w/next data point
                    continue  # Go to next dt

                windows[windex][1] = removeDTs[i-1] # Close last window
                windows.append([rdt, None]) # Start a new window
                windex += 1 # Update window index
    windows = windows[:-1]
    # Need to convert these to windows now!
    removeUTC = []
    for swin, ewin in windows:
        removeUTC.append([obspy.UTCDateTime(swin), obspy.UTCDateTime(ewin)])
    
    stime = outstream.split()[0].stats.starttime
    etime = outstream.split()[-1].stats.endtime
    removeUTC.insert(0, [stime, stime])
    removeUTC.append([etime, etime])

    #for win0, win1 in removeUTC:
    #    print(win0, win1, win1>win0)
    outstream  = __remove_gaps(outstream, removeUTC)

    return outstream


# Remove noise saturation
def __remove_noise_saturate(stream, sat_percent, min_win_size, verbose=False):
    """Function to remove "saturated" data points that exceed a certain percent (sat_percent) of the maximum data value in the stream.  

    Parameters
    ----------
    stream : obspy.Stream
        Obspy Stream of interest
    sat_percent : float
        Percentage of the maximum amplitude, which will be used as the saturation threshold above which data points will be excluded
    min_win_size : float
        The minumum size a window must be (in seconds) for it to be removed

    Returns
    -------
    obspy.Stream
        Stream with masked array (if data removed) with "saturated" data removed
    """
    if verbose:
        print(f'\tRemoving noise using noise saturation method: sat_percent={sat_percent}, min_win_size={min_win_size}')
    if sat_percent > 1:
        sat_percent = sat_percent / 100

    removeInd = np.array([], dtype=int)
    for trace in stream:
        dataArr = trace.data.copy()

        sample_rate = trace.stats.delta

        #Get max amplitude value
        maxAmp = np.max(np.absolute(dataArr, where = not None))
        thresholdAmp = maxAmp * sat_percent
        cond = np.nonzero(np.absolute(dataArr, where=not None) > thresholdAmp)[0]
        removeInd = np.hstack([removeInd, cond])
        #trace.data = np.ma.where(np.absolute(data, where = not None) > (noise_percent * maxAmp), None, data)
    #Combine indices from all three traces
    removeInd = np.unique(removeInd)
    
    removeList = []  # initialize
    min_win_samples = int(min_win_size / sample_rate)

    if len(removeInd) > 0:
        startInd = removeInd[0]
        endInd = removeInd[0]

        for i in range(0, len(removeInd)):             
            if removeInd[i] - removeInd[i-1] > 1:
                if endInd - startInd >= min_win_samples:
                    removeList.append([int(startInd), int(endInd)])
                startInd = removeInd[i]
            endInd = removeInd[i]

    removeList.append([-1, -1]) #figure out a way to get rid of this

    #Convert removeList from samples to seconds after start to UTCDateTime
    sampleRate = stream[0].stats.delta
    startT = stream[0].stats.starttime
    endT = stream[0].stats.endtime
    removeSec = []
    removeUTC = []
    removeUTC.append([startT, startT])
    for i, win in enumerate(removeList):
        removeSec.append(list(np.round(sampleRate * np.array(win),6)))
        removeUTC.append(list(np.add(startT, removeSec[i])))
    removeUTC[-1][0] = removeUTC[-1][1] = endT
    
    outstream  = __remove_gaps(stream, removeUTC)
    return outstream


# Helper function for removing data using the noise threshold input from remove_noise()
def __remove_noise_thresh(stream, noise_percent=0.8, lta=30, min_win_size=1, verbose=False):
    """Helper function for removing data using the noise threshold input from remove_noise()

    The purpose of the noise threshold method is to remove noisy windows (e.g., lots of traffic all at once). 
    
    This function uses the lta value (which can be specified here), and finds times where the lta value is at least at the noise_percent level of the max lta value for at least a specified time (min_win_size)

    Parameters
    ----------
    stream : obspy.core.stream.Stream object
        Input stream from which to remove windows. Passed from remove_noise().
    noise_percent : float, default=0.995
        Percentage (between 0 and 1), to use as the threshold at which to remove data. This is used in the noise threshold method. By default 0.995. 
        If a value is passed that is greater than 1, it will be divided by 100 to obtain the percentage. Passed from remove_noise().
    lta : int, default = 30
        Length of lta to use (in seconds)
    min_win_size : int, default = 1
        Minimum amount of time (in seconds) at which noise is above noise_percent level.
    
    Returns
    -------
    outStream : obspy.core.stream.Stream object
        Stream with a masked array for the data where 'noise' has been removed. Passed to remove_noise().
    """
    if verbose:
        print(f'\tRemoving noise using continuous noise threshold method: sat_percent={noise_percent}, lta={lta}')
    if noise_percent > 1:
        noise_percent = noise_percent / 100

    removeInd = np.array([], dtype=int)
    for trace in stream:
        dataArr = trace.data.copy()

        sample_rate = trace.stats.delta
        lta_samples = int(lta / sample_rate)

        #Get lta values across traces data
        window_size = lta_samples
        if window_size == 0:
            window_size = 1
        kernel = np.ones(window_size) / window_size
        maskedArr = np.ma.array(dataArr, dtype=float, fill_value=None)
        ltaArr = np.convolve(maskedArr, kernel, mode='same')
        #Get max lta value
        maxLTA = np.max(ltaArr, where = not None)
        cond = np.nonzero(np.absolute(ltaArr, where=not None) > (noise_percent * maxLTA))[0]
        removeInd = np.hstack([removeInd, cond])
        #trace.data = np.ma.where(np.absolute(data, where = not None) > (noise_percent * maxAmp), None, data)
    #Combine indices from all three traces
    removeInd = np.unique(removeInd)

    # Make sure we're not removing single indices (we only want longer than min_win_size)
    removeList = []  # initialize    
    min_win_samples = int(min_win_size / sample_rate)

    if len(removeInd) > 0:
        startInd = removeInd[0]
        endInd = removeInd[0]

        for i in range(0, len(removeInd)):
            #If indices are non-consecutive... 
            if removeInd[i] - removeInd[i-1] > 1:
                #If the indices are non-consecutive and the 
                if endInd - startInd >= min_win_samples:
                    removeList.append([int(startInd), int(endInd)])
                    
                #Set startInd as the current index
                startInd = removeInd[i]
            endInd = removeInd[i]
            
    removeList.append([-1, -1])

    sampleRate = stream[0].stats.delta
    startT = stream[0].stats.starttime
    endT = stream[0].stats.endtime
    removeSec = []
    removeUTC = []

    removeUTC.append([startT, startT])
    for i, win in enumerate(removeList):
        removeSec.append(list(np.round(sampleRate * np.array(win),6)))
        removeUTC.append(list(np.add(startT, removeSec[i])))
    removeUTC[-1][0] = removeUTC[-1][1] = endT

    outstream  = __remove_gaps(stream, removeUTC)

    return outstream


# Helper function for removing data during warmup (when seismometers are still initializing) and "cooldown" (when there may be noise from deactivating seismometer) time, if desired
def __remove_warmup_cooldown(stream, warmup_time = 0, cooldown_time = 0, verbose=False):
    """Private helper function to remove data from the start and/or end of each site

    Parameters
    ----------
    stream : obspy.Stream()
        Input stream to use for analysis for noise removal
    warmup_time : int, optional
        Time in seconds at the start of the record to remove from analysis, by default 0
    cooldown_time : int, optional
        Time in seconds at the end of the record to remove from analysis, by default 0
    verbose : bool, optional
        Whether to print information about the process to the terminal, by default False

    Returns
    -------
    obspy.Stream()
        obspy.Stream() with masked arrays for the data where removed/kept.
    """
    if verbose:
        print(f"\tRemoving noise using warmup/cooldown buffers: warmup_time={warmup_time} s, cooldown_time={cooldown_time} s ")
    sampleRate = float(stream[0].stats.delta)
    outStream = stream.copy()

    warmup_samples = int(warmup_time / sampleRate) #Convert to samples
    windows_samples=[]
    for tr in stream:
        totalSamples = len(tr.data)-1#float(tr.stats.endtime - tr.stats.starttime) / tr.stats.delta
        cooldown_samples = int(totalSamples - (cooldown_time / sampleRate)) #Convert to samples
    
    # Initiate list with warmup and cooldown samples
    windows_samples = [[0, warmup_samples],[cooldown_samples, totalSamples]]
    
    # Remove cooldown and warmup samples if there is none indicated (default of 0 for both)
    if cooldown_time == 0:
        windows_samples.pop(1)
    if warmup_time == 0:
        windows_samples.pop(0)


    if windows_samples == []:
        # If no warmup or cooldown indicated, don't do anything
        pass
    else:
        # Otherwise, get the actual starttime (UTCDateTime)
        startT = stream[0].stats.starttime
        endT = stream[-1].stats.endtime
        window_UTC = []
        window_MPL = []

        print("warmup starttime", startT)
        # Initiate list with starttimes
        for w, win in enumerate(windows_samples):
            # win is a list with start/end time for each buffer, in samples
            for j, tm in enumerate(win):
                # For each side (warmup or cooldown), add a new item
                # There will be 2 list items for warmup, 2 for cooldown (extra is for "padding")
                if j == 0:
                    window_UTC.append([])
                    window_MPL.append([])
                tSec = tm * sampleRate

                # Get the UTC time for the new item
                window_UTC[w].append(startT+tSec)
                window_MPL[w].append(window_UTC[w][j].matplotlib_date)
        # "pad" list with endtime
        window_UTC.insert(0, [startT, startT])
        window_UTC.append([endT, endT])

        outStream = __remove_gaps(stream, window_UTC)
    
    return outStream


# Helper function for selecting windows
def _keep_processing_windows(stream, processing_window=[":"], verbose=False):
    """Keep processing windows

    Parameters
    ----------
    stream : obspy.Stream()
        Stream
    processing_window : list, optional
        Processing window list, by default [":"]
    verbose : bool, optional
        Whether to print information about the removal to the terminal

    Returns
    -------
    obspy.Stream()
        Obspy stream object with selected windows retained and all else removed
    """

    if verbose:
        print(f"\tRemoving noise outside the indicated processing window(s): processing_window={processing_window}")
    instream = stream
    allList = [':', 'all', 'everything']

    year = stream[0].stats.starttime.year
    month = stream[0].stats.starttime.month
    day = stream[0].stats.starttime.day

    if not isinstance(processing_window, (tuple, list)):
        processing_window = [processing_window]

    windows_to_get = []
    for p in processing_window:
        if str(p).lower() in allList:
            return instream
        
        if isinstance(p, (tuple, list)):
            windows_to_get.append([])
            if isinstance(p[0], (obspy.UTCDateTime, datetime.datetime)) and isinstance(p[1], (obspy.UTCDateTime, datetime.datetime)):
                windows_to_get[-1].append(obspy.UTCDateTime(p[0]))
                windows_to_get[-1].append(obspy.UTCDateTime(p[1]))
            else:
                windows_to_get[-1].append(obspy.UTCDateTime(sprit_utils._format_time(p[0], tzone='UTC')))
                windows_to_get[-1].append(obspy.UTCDateTime(sprit_utils._format_time(p[1], tzone='UTC')))

                # Make sure time are on the right day
                windows_to_get[-1][0] = obspy.UTCDateTime(year, month, day, windows_to_get[-1][0].hour, windows_to_get[-1][0].minute, windows_to_get[-1][0].second)
                windows_to_get[-1][1] = obspy.UTCDateTime(year, month, day, windows_to_get[-1][1].hour, windows_to_get[-1][1].minute, windows_to_get[-1][1].second)
        else:
            if len(processing_window) == 2:
                windows_to_get = [[obspy.UTCDateTime(sprit_utils._format_time(processing_window[0], tzone='UTC')),
                        obspy.UTCDateTime(sprit_utils._format_time(processing_window[1], tzone='UTC'))]]
            else:
                print(f'The processing_window parameter of remove_noise was set as {processing_window}')
                print("The processing_window parameter must be a list or tuple with a start and end time or with lists/tuples of start/end times.")
                print('processing_window noise removal method not applied')
                return instream
    
    # windows_to_get should be a list of two-item lists with UTCDateTime objects no matter how it came in
    stime = instream[0].stats.starttime
    etime = instream[-1].stats.endtime

    windows_to_get.insert(0, [stime, stime])
    windows_to_get.append([etime, etime])

    # Need the list formatted slightly different, use window_UTC
    window_UTC = []
    # Rearrange
    for i, win in enumerate(windows_to_get):
        if i == 0:
            window_UTC.append([stime, windows_to_get[i+1][0]])
        elif i < len(windows_to_get) - 1:
            window_UTC.append([win[1], windows_to_get[i+1][0]])

    window_UTC.insert(0, windows_to_get[0])
    window_UTC.append(windows_to_get[-1])

    outStream = __remove_gaps(stream, window_UTC)

    return outStream


# Plot noise windows
def _plot_noise_windows(hvsr_data, fig=None, ax=None, clear_fig=False, fill_gaps=None,
                         do_stalta=False, sta=5, lta=30, stalta_thresh=[0.5,5], 
                         do_pctThresh=False, sat_percent=0.8, min_win_size=1, 
                         do_noiseWin=False, noise_percent=0.995, 
                         do_warmup=False, warmup_time=0, cooldown_time=0, 
                         return_dict=False, use_tkinter=False):
    
    if clear_fig: #Intended use for tkinter
        #Clear everything
        for key in ax:
            ax[key].clear()
        fig.clear()

        #Really make sure it's out of memory
        fig = []
        ax = []
        try:
            fig.get_children()
        except:
            pass
        try:
            ax.get_children()
        except:
            pass

    if use_tkinter:
        try:
            pass #Don't think this is being used anymore, defined in sprit_gui separately
            #ax=ax_noise #self.ax_noise #?
            #fig=fig_noise
        except:
            pass

    #Reset axes, figure, and canvas widget
    noise_mosaic = [['spec'],['spec'],['spec'],
            ['spec'],['spec'],['spec'],
            ['signalz'],['signalz'], ['signaln'], ['signale']]
    fig, ax = plt.subplot_mosaic(noise_mosaic, sharex=True)  
    #self.noise_canvas = FigureCanvasTkAgg(fig, master=canvasFrame_noise)
    #self.noise_canvasWidget.destroy()
    #self.noise_canvasWidget = self.noise_canvas.get_tk_widget()#.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    #self.noise_canvasWidget.pack(fill='both')#.grid(row=0, column=0, sticky='nsew')
    fig.canvas.draw()
    
    fig, ax = sprit_plot._plot_input_stream_mpl(stream=hvsr_data['stream'], hv_data=hvsr_data, fig=fig, ax=ax, component='Z', stack_type='linear', detrend='mean', fill_gaps=fill_gaps, dbscale=True, return_fig=True, cmap_per=[0.1, 0.9])
    fig.canvas.draw()

    #Set initial input
    input = hvsr_data['stream']

    if do_stalta:
        hvsr_data['stream'] = remove_noise(hvsr_data=input, remove_method='stalta', sta=sta, lta=lta, stalta_thresh=stalta_thresh)
        input = hvsr_data['stream']

    if do_pctThresh:
        hvsr_data['stream'] = remove_noise(hvsr_data=input, remove_method='saturation',  sat_percent=sat_percent, min_win_size=min_win_size)
        input = hvsr_data['stream']

    if do_noiseWin:
        hvsr_data['stream'] = remove_noise(hvsr_data=input, remove_method='noise', noise_percent=noise_percent, lta=lta, min_win_size=min_win_size)
        input = hvsr_data['stream']

    if do_warmup:
        hvsr_data['stream'] = remove_noise(hvsr_data=input, remove_method='warmup', warmup_time=warmup_time, cooldown_time=cooldown_time)

    fig, ax, noise_windows_line_artists, noise_windows_window_artists = _get_removed_windows(input=hvsr_data, fig=fig, ax=ax, time_type='matplotlib')
    
    fig.canvas.draw()
    plt.show()
    if return_dict:
        hvsr_data['Windows_Plot'] = (fig, ax)
        return hvsr_data
    return 


# Helper function for manual window selection 
def __draw_boxes(event, clickNo, xWindows, pathList, windowDrawn, winArtist, lineArtist, x0, fig, ax):
    """Helper function for manual window selection to draw boxes to show where windows have been selected for removal"""
    #Create an axis dictionary if it does not already exist so all functions are the same

    if isinstance(ax, np.ndarray) or isinstance(ax, dict):
        ax = ax
    else:
        ax = {'a':ax}

    
    if len(ax) > 1:
        if type(ax) is not dict:
            axDict = {}
            for i, a in enumerate(ax):
                axDict[str(i)] = a
            ax = axDict
    #else:
    #    ax = {'a':ax}
    
    #if event.inaxes!=ax: return
    #y0, y1 = ax.get_ylim()
    y0 = []
    y1 = []
    kList = []
    for k in ax.keys():
        kList.append(k)
        y0.append(ax[k].get_ylim()[0])
        y1.append(ax[k].get_ylim()[1])
    #else:
    #    y0 = [ax.get_ylim()[0]]
    #    y1 = [ax.get_ylim()[1]]

    if clickNo == 0:
        #y = np.linspace(ax.get_ylim()[0], ax.get_ylim()[1], 2)
        x0 = event.xdata
        clickNo = 1   
        lineArtist.append([])
        winNums = len(xWindows)
        for i, k in enumerate(ax.keys()):
            linArt = ax[k].axvline(x0, 0, 1, color='k', linewidth=1, zorder=100)
            lineArtist[winNums].append([linArt, linArt])
        #else:
        #    linArt = plt.axvline(x0, y0[i], y1[i], color='k', linewidth=1, zorder=100)
        #    lineArtist.append([linArt, linArt])
    else:
        x1 = event.xdata
        clickNo = 0

        windowDrawn.append([])
        winArtist.append([])  
        pathList.append([])
        winNums = len(xWindows)
        for i, key in enumerate(kList):
            path_data = [
                (matplotlib.path.Path.MOVETO, (x0, y0[i])),
                (matplotlib.path.Path.LINETO, (x1, y0[i])),
                (matplotlib.path.Path.LINETO, (x1, y1[i])),
                (matplotlib.path.Path.LINETO, (x0, y1[i])),
                (matplotlib.path.Path.LINETO, (x0, y0[i])),
                (matplotlib.path.Path.CLOSEPOLY, (x0, y0[i])),
            ]
            codes, verts = zip(*path_data)
            path = matplotlib.path.Path(verts, codes)

            windowDrawn[winNums].append(False)
            winArtist[winNums].append(None)

            pathList[winNums].append(path)
            __draw_windows(event=event, pathlist=pathList, ax_key=key, windowDrawn=windowDrawn, winArtist=winArtist, xWindows=xWindows, fig=fig, ax=ax)
            linArt = plt.axvline(x1, 0, 1, color='k', linewidth=0.5, zorder=100)

            [lineArtist[winNums][i].pop(-1)]
            lineArtist[winNums][i].append(linArt)
        x_win = [x0, x1]
        x_win.sort() #Make sure they are in the right order
        xWindows.append(x_win)
    fig.canvas.draw()
    return clickNo, x0


# Helper function for manual window selection to draw boxes to deslect windows for removal
def __remove_on_right(event, xWindows, pathList, windowDrawn, winArtist,  lineArtist, fig, ax):
    """Helper function for manual window selection to draw boxes to deslect windows for removal"""

    if xWindows is not None:
        for i, xWins in enumerate(xWindows):
            if event.xdata > xWins[0] and event.xdata < xWins[1]:
                linArtists = lineArtist[i]
                pathList.pop(i)
                for j, a in enumerate(linArtists):
                    winArtist[i][j].remove()#.pop(i)
                    lineArtist[i][j][0].remove()#.pop(i)#[i].pop(j)
                    lineArtist[i][j][1].remove()
                windowDrawn.pop(i)
                lineArtist.pop(i)#[i].pop(j)
                winArtist.pop(i)#[i].pop(j)
                xWindows.pop(i)
    fig.canvas.draw() 


# Helper function for updating the canvas and drawing/deleted the boxes
def __draw_windows(event, pathlist, ax_key, windowDrawn, winArtist, xWindows, fig, ax):
    """Helper function for updating the canvas and drawing/deleted the boxes"""
    for i, pa in enumerate(pathlist):
        for j, p in enumerate(pa): 
            if windowDrawn[i][j]:
                pass
            else:
                patch = matplotlib.patches.PathPatch(p, facecolor='k', alpha=0.75)                            
                winArt = ax[ax_key].add_patch(patch)
                windowDrawn[i][j] = True
                winArtist[i][j] = winArt

    if event.button is MouseButton.RIGHT:
        fig.canvas.draw()


# Helper function for getting click event information
def __on_click(event):
    """Helper function for getting click event information"""
    global clickNo
    global x0
    if event.button is MouseButton.RIGHT:
        __remove_on_right(event, xWindows, pathList, windowDrawn, winArtist, lineArtist, fig, ax)

    if event.button is MouseButton.LEFT:            
        clickNo, x0 = __draw_boxes(event, clickNo, xWindows, pathList, windowDrawn, winArtist, lineArtist, x0, fig, ax)    


# Function to select windows using original stream specgram/plots
def _select_windows(input):
    """Function to manually select windows for exclusion from data.

    Parameters
    ----------
    input : dict
        Dictionary containing all the hvsr information.

    Returns
    -------
    xWindows : list
        List of two-item lists containing start and end times of windows to be removed.
    """
    from matplotlib.backend_bases import MouseButton
    import matplotlib.pyplot as plt
    import matplotlib
    import time
    global fig
    global ax

    if isinstance(input, (HVSRData, dict)):
        if 'hvsr_curve' in input.keys():
            fig = plot_hvsr(hvsr_data=input, plot_type='spec', returnfig=True, cmap='turbo')
        else:
            hvsr_data = input#.copy()
            input_stream = hvsr_data['stream']
    
    if isinstance(input_stream, obspy.core.stream.Stream):
        fig, ax = sprit_plot._plot_input_stream_mpl(input_stream, component=['Z'])
    elif isinstance(input_stream, obspy.core.trace.Trace):
        fig, ax = sprit_plot._plot_input_stream_mpl(input_stream)

    global lineArtist
    global winArtist
    global windowDrawn
    global pathList
    global xWindows
    global clickNo
    global x0
    x0=0
    clickNo = 0
    xWindows = []
    pathList = []
    windowDrawn = []
    winArtist = []
    lineArtist = []

    global fig_closed
    fig_closed = False
    while fig_closed is False:
        fig.canvas.mpl_connect('button_press_event', __on_click)#(clickNo, xWindows, pathList, windowDrawn, winArtist, lineArtist, x0, fig, ax))
        fig.canvas.mpl_connect('close_event', _on_fig_close)#(clickNo, xWindows, pathList, windowDrawn, winArtist, lineArtist, x0, fig, ax))
        plt.pause(1)

    hvsr_data['x_windows_out'] = xWindows
    hvsr_data['fig_noise'] = fig
    hvsr_data['ax_noise'] = ax
    return hvsr_data


# Support function to help select_windows run properly
def _on_fig_close(event):
    global fig_closed
    fig_closed = True
    return


# Shows windows with None on input plot
def _get_removed_windows(input, fig=None, ax=None, lineArtist =[], winArtist = [], existing_lineArtists=[], existing_xWindows=[], exist_win_format='matplotlib', keep_line_artists=True, time_type='matplotlib',show_plot=False):
    """This function is for getting Nones from masked arrays and plotting them as windows"""
    if fig is None and ax is None:
        fig, ax = plt.subplots()

    if isinstance(input, (dict, HVSRData)):
        stream = input['stream'].copy()
    elif isinstance(input, (obspy.core.trace.Trace, obspy.core.stream.Stream)):
        stream = input.copy()
    else:
        pass #Warning?
        
    samplesList = ['sample', 'samples', 's']
    utcList = ['utc', 'utcdatetime', 'obspy', 'u', 'o']
    matplotlibList = ['matplotlib', 'mpl', 'm']    
    
    #Get masked indices of trace(s)
    trace = stream.merge()[0]
    sample_rate = trace.stats.delta
    windows = []
    #windows.append([0,np.nan])
    #mask = np.isnan(trace.data)  # Create a mask for None values
    #masked_array = np.ma.array(trace.data, mask=mask).copy()
    masked_array = trace.data.copy()
    if isinstance(masked_array, np.ma.MaskedArray):
        masked_array = masked_array.mask.nonzero()[0]
        lastMaskInd = masked_array[0]-1
        wInd = 0
        for i in range(0, len(masked_array)-1):
            maskInd = masked_array[i]
            if maskInd-lastMaskInd > 1 or i==0:
                windows.append([np.nan, np.nan])
                if i==0:
                    windows[wInd][0] = masked_array[i]
                else:
                    windows[wInd-1][1] = masked_array[i - 1]
                windows[wInd][0] = masked_array[i]
                wInd += 1
            lastMaskInd = maskInd
        windows[wInd-1][1] = masked_array[-1] #Fill in last masked value (wInd-1 b/c wInd+=1 earlier)
    winTypeList = ['gaps'] * len(windows)

    #Check if the windows are just gaps
    if len(existing_xWindows) > 0:
        existWin = []
        #Check if windows are already being taken care of with the gaps
        startList = []
        endList = []
        for start, end in windows:
            startList.append((trace.stats.starttime + start*sample_rate).matplotlib_date)
            endList.append((trace.stats.starttime + end*sample_rate).matplotlib_date)
        for w in existing_xWindows:
            removed=False
            if w[0] in startList and w[1] in endList:
                existing_xWindows.remove(w)

                removed=True                    
            if exist_win_format.lower() in matplotlibList and not removed:
                sTimeMPL = trace.stats.starttime.matplotlib_date #Convert time to samples from starttime
                existWin.append(list(np.round((w - sTimeMPL)*3600*24/sample_rate)))
                                    
        windows = windows + existWin
        existWinTypeList = ['removed'] * len(existWin)
        winTypeList = winTypeList + existWinTypeList

    #Reformat ax as needed
    if isinstance(ax, np.ndarray):
        origAxes = ax.copy()
        newAx = {}
        for i, a in enumerate(ax):
            newAx[i] = a
        axes = newAx
    elif isinstance(ax, dict):
        origAxes = ax
        axes = ax
    else:
        origAxes = ax
        axes = {'ax':ax}

    for i, a in enumerate(axes.keys()):
        ax = axes[a]
        pathList = []
        
        windowDrawn = []
        winArtist = []
        if existing_lineArtists == []:
            lineArtist = []
        elif len(existing_lineArtists)>=1 and keep_line_artists:
            lineArtist = existing_lineArtists
        else:
            lineArtist = []

        for winNums, win in enumerate(windows):
            if time_type.lower() in samplesList:
                x0 = win[0]
                x1 = win[1]
            elif time_type.lower() in utcList or time_type.lower() in matplotlibList:
                #sample_rate = trace.stats.delta

                x0 = trace.stats.starttime + (win[0] * sample_rate)
                x1 = trace.stats.starttime + (win[1] * sample_rate)

                if time_type.lower() in matplotlibList:
                    x0 = x0.matplotlib_date
                    x1 = x1.matplotlib_date
            else:
                warnings.warn(f'time_type={time_type} not recognized. Defaulting to matplotlib time formatting')
                x0 = trace.stats.starttime + (win[0] * sample_rate)
                x1 = trace.stats.starttime + (win[1] * sample_rate)
                
                x0 = x0.matplotlib_date
                x1 = x1.matplotlib_date
            
            y0, y1 = ax.get_ylim()

            path_data = [
                        (matplotlib.path.Path.MOVETO, (x0, y0)),
                        (matplotlib.path.Path.LINETO, (x1, y0)),
                        (matplotlib.path.Path.LINETO, (x1, y1)),
                        (matplotlib.path.Path.LINETO, (x0, y1)),
                        (matplotlib.path.Path.LINETO, (x0, y0)),
                        (matplotlib.path.Path.CLOSEPOLY, (x0, y0)),
                    ]
            
            codes, verts = zip(*path_data)
            path = matplotlib.path.Path(verts, codes)

            #
            windowDrawn.append(False)
            winArtist.append(None)
            lineArtist.append([])
            
            if winTypeList[winNums] == 'gaps':
                clr = '#b13d41'
            elif winTypeList[winNums] == 'removed':
                clr = 'k'
            else:
                clr = 'yellow'

            linArt0 = ax.axvline(x0, y0, y1, color=clr, linewidth=0.5, zorder=100)
            linArt1 = plt.axvline(x1, y0, y1, color=clr, linewidth=0.5, zorder=100)
            lineArtist[winNums].append([linArt0, linArt1])
            #
            
            pathList.append(path)

        for i, pa in enumerate(pathList):
            if windowDrawn[i]:
                pass
            else:
                patch = matplotlib.patches.PathPatch(pa, facecolor=clr, alpha=0.75)                            
                winArt = ax.add_patch(patch)
                windowDrawn[i] = True
                winArtist[i] = winArt
        
        #Reformat ax as needed
        if isinstance(origAxes, np.ndarray):
            origAxes[i] = ax
        elif isinstance(origAxes, dict):
            origAxes[a] = ax
        else:
            origAxes = ax

        ax = origAxes

        fig.canvas.draw()
    
    if show_plot:
        plt.show()
    return fig, ax, lineArtist, winArtist


# Helper function for removing windows from data, leaving gaps
def __remove_windows(stream, window_list, warmup_time):
    """Helper function that actually does the work in obspy to remove the windows calculated in the remove_noise function
s
    Parameters
    ----------
    stream : obspy.core.stream.Stream object
        Input stream from which to remove windows
    window_list : list
        A list of windows with start and end times for the windows to be removed
    warmup_time : int, default = 0
        Passed from remove_noise, the amount of time in seconds to allow for warmup. Anything before this is removed as 'noise'.

    Returns
    -------
    outStream : obspy.core.stream.Stream object
        Stream with a masked array for the data where 'noise' has been removed
    """
    og_stream = stream.copy()

    #Find the latest start time and earliest endtime of all traces (in case they aren't consistent)
    maxStartTime = obspy.UTCDateTime(-1e10) #Go back pretty far (almost 400 years) to start with
    minEndTime = obspy.UTCDateTime(1e10)
    for comp in ['E', 'N', 'Z']:
        tr = stream.select(component=comp).copy()
        if tr[0].stats.starttime > maxStartTime:
            maxStartTime = tr[0].stats.starttime
        if tr[0].stats.endtime < minEndTime:
            minEndTime = tr[0].stats.endtime

    #Trim all traces to the same start/end time
    stream.trim(starttime=maxStartTime, endtime=minEndTime)      

    #Sort windows by the start of the window
    sorted_window_list = []
    windowStart = []
    for i, window in enumerate(window_list):
        windowStart.append(window[0])
    windowStart_og = windowStart.copy()
    windowStart.sort()
    sorted_start_list = windowStart
    ranks = [windowStart_og.index(item) for item in sorted_start_list]
    for r in ranks:
        sorted_window_list.append(window_list[r])

    for i, w in enumerate(sorted_window_list):
        if i < len(sorted_window_list) - 1:
            if w[1] > sorted_window_list[i+1][0]:
                warnings.warn(f"Warning: Overlapping windows. Please start over and reselect windows to be removed or use a different noise removal method: {w[1]} '>' {sorted_window_list[i+1][0]}")
                return
                
    window_gaps_obspy = []
    window_gaps = []

    buffer_time = np.ceil((stream[0].stats.endtime-stream[0].stats.starttime)*0.01)

    #Get obspy.UTCDateTime objects for the gap times
    window_gaps_obspy.append([stream[0].stats.starttime + warmup_time, stream[0].stats.starttime + warmup_time])
    for i, window in enumerate(sorted_window_list):
        for j, item in enumerate(window):
            if j == 0:
                window_gaps_obspy.append([0,0])
            window_gaps_obspy[i+1][j] = obspy.UTCDateTime(matplotlib.dates.num2date(item))
        window_gaps.append((window[1]-window[0])*86400)
    window_gaps_obspy.append([stream[0].stats.endtime-buffer_time, stream[0].stats.endtime-buffer_time])
    #Note, we added start and endtimes to obpsy list to help with later functionality

    #Clean up stream windows (especially, start and end)
    for i, window in enumerate(window_gaps):
        newSt = stream.copy()
        #Check if first window starts before end of warmup time
        #If the start of the first exclusion window is before the warmup_time is over
        if window_gaps_obspy[i+1][0] - newSt[0].stats.starttime < warmup_time:
            #If the end of first exclusion window is also before the warmup_time is over
            if window_gaps_obspy[i+1][1] - newSt[0].stats.starttime < warmup_time:
                #Remove that window completely, it is unnecessary
                window_gaps.pop(i)
                window_gaps_obspy.pop(i+1)
                #...and reset the entire window to start at the warmup_time end
                window_gaps_obspy[0][0] = window_gaps_obspy[0][1] = newSt[0].stats.starttime + warmup_time
                continue
            else: #if window overlaps the start of the stream after warmup_time
                #Remove that window
                window_gaps.pop(i)
                #...and reset the start of the window to be the end of warm up time
                #...and  remove that first window from the obspy list
                window_gaps_obspy[0][0] = window_gaps_obspy[0][1] =  window_gaps_obspy[i+1][1]#newSt[0].stats.starttime + warmup_time
                window_gaps_obspy.pop(i+1)


        if stream[0].stats.endtime - window_gaps_obspy[i+1][1] > stream[0].stats.endtime - buffer_time:        
            if stream[0].stats.endtime - window_gaps_obspy[i+1][0] > stream[0].stats.endtime - buffer_time:
                window_gaps.pop(i)
                window_gaps_obspy.pop(i+1)
            else:  #if end of window overlaps the buffer time, just end it at the start of the window (always end with stream, not gap)
                window_gaps.pop(i)
                window_gaps_obspy[-1][0] = window_gaps_obspy[-1][1] = newSt[0].stats.endtime - buffer_time
   
    #Add streams
    stream_windows = []
    j = 0
    for i, window in enumerate(window_gaps):
        j=i
        newSt = stream.copy()
        stream_windows.append(newSt.trim(starttime=window_gaps_obspy[i][1], endtime=window_gaps_obspy[i+1][0]))
    i = j + 1
    newSt = stream.copy()
    stream_windows.append(newSt.trim(starttime=window_gaps_obspy[i][1], endtime=window_gaps_obspy[i+1][0]))

    for i, st in enumerate(stream_windows):
        if i == 0:
            outStream = st.copy()
        else:
            newSt = st.copy()
            gap = window_gaps[i-1]
            outStream = outStream + newSt.trim(starttime=st[0].stats.starttime - gap, pad=True, fill_value=None)       
    outStream.merge()
    return outStream


# Helper functions for remove_outlier_curves()
# Use DBSCAN algorithm for outlier detection
def __dbscan_outlier_detect(hvsr_data, use_hv_curves=True, use_percentile=True,
                            dist_metric='euclidean', 
                            neighborhood_size=50, min_neighborhood_pts=5,
                            col_names=['HV_Curves'], comp_names=['Z', 'E', 'N'], 
                            col_prefix = 'HV_Curves',                       
                            verbose=False):
    """
    This is a helper function for remove_outlier_curves() to use a DBSCAN algorithm 
    to identify and discard outlier curves.

    Parameters
    ----------
    hvsr_data : HVSRData
        HVSRData instance on which to perform DBSCAN analysis
    use_hv_curves : bool, optional
        Whether to use HV_Curves as the curve set of interest, by default True
    dist_metric : str, optional
        Distance metric to use (see scipy.spatial.distance.pdist), by default 'euclidean'
    neighborhood_size : int, optional
        Percentile value to use in selecting neighborhood cutoff size.
        100 would use the largest distance in the distance matrix. 0 would use the smallest (0), by default 95
    min_neighborhood_pts : int, optional
        Minimum number of points in a curve's neighborhood for that point to be considered a core point, by default 5

    Returns
    -------
    HVSRData
        HVSRData instance with the hvsr_windows_df DataFrame "Use" column updated
    """

    # Get the correct set of curves to use
    # This can be generalized better (and adapted for azimuthal values)
    #if use_hv_curves:
    #    curveCols = ['HV_Curves']
    #else:
    #    curveCols = ['psd_values_Z', 'psd_values_E', 'psd_values_N']


    # Clean up percentile value
    if use_percentile:
        if neighborhood_size < 0 or neighborhood_size > 100:
            print("\tNeighborhood_percentile must be between 0-100, not ", neighborhood_size)
            print('\t  Resetting neighborhood_size to 95')
            neighborhood_size = 95
        elif neighborhood_size > 0 and neighborhood_size < 1:
            neighborhood_size = neighborhood_size * 100

    # Define local function to use general dbscan algorithm for identifying outliers
    def _dbscan_outliers(distance_matrix, n_size, min_pts, _use_percentile=True):
        n = dist_matrix.shape[0]
        has_neighbors = np.ones(n, dtype=bool)

        # Get epsilon based on whether it is a percentile
        if _use_percentile:
            eps = np.percentile(dist_matrix, n_size)
        else:
            eps = n_size

        for i in range(n):
            neighbors = np.where(dist_matrix[i] <= eps)[0]
            if len(neighbors)-1 < min_pts:
                has_neighbors[i] = False
            
            #print(i, len(neighbors), has_neighbors[i])
        
        return has_neighbors


    for i, column in enumerate(col_names):
        if column in comp_names:
            if use_hv_curves == False:
                column = col_prefix + column
            else:
                column = column


    # Iterate through curves of interest
    for i, column in enumerate(col_names):
        if column in comp_names:
            if use_hv_curves == False:
                column = col_prefix + column
            else:
                column = column
        curves = np.stack(hvsr_data['hvsr_windows_df'][column])
        dist_matrix = squareform(pdist(curves, metric=dist_metric))

        noise_array = _dbscan_outliers(distance_matrix=dist_matrix, 
                                       n_size=neighborhood_size, 
                                       min_pts=min_neighborhood_pts,
                                       _use_percentile=use_percentile)
        # Remove curves from analysis
        hvsr_data.hvsr_windows_df.loc[~noise_array, 'Use'] = False

    return hvsr_data


# This is a remove_outlier_curve() helper function to use a "prototype" curve (median curve) to detect outliers
def __prototype_outlier_detect(hvsr_data, use_hv_curves=False, 
                                use_percentile=True, outlier_threshold=98,
                                col_names=['HV_Curves'], comp_names=['Z', 'E', 'N'], 
                                col_prefix = 'HV_Curves',
                                verbose=False):

    # Loop through each component, and determine which curves are outliers
    bad_rmse = []
    for i, column in enumerate(col_names):
        if column in comp_names:
            if use_hv_curves == False:
                column = col_prefix + column
            else:
                column = column

        # Retrieve data from dataframe (use all windows, just in case)
        curr_data = np.stack(hvsr_data['hvsr_windows_df'][column])

        # Calculate a median curve, and reshape so same size as original
        medCurve = np.nanmedian(curr_data, axis=0)
        medCurveArr = np.tile(medCurve, (curr_data.shape[0], 1))

        # Calculate RMSE
        rmse = np.sqrt(((np.subtract(curr_data, medCurveArr)**2).sum(axis=1))/curr_data.shape[1])
        hvsr_data['hvsr_windows_df']['RMSE_'+column] = rmse
        if use_percentile is True:
            rmse_threshold = np.percentile(rmse[~np.isnan(rmse)], outlier_threshold)
            if verbose:
                print(f'\tRMSE at {outlier_threshold}th percentile for {column} calculated at: {rmse_threshold:.2f}')
        else:
            rmse_threshold = outlier_threshold

        # Retrieve index of those RMSE values that lie outside the threshold
        for j, curve in enumerate(curr_data):
            if rmse[j] > rmse_threshold:
                bad_rmse.append(j)

    # Get unique values of bad_rmse indices and set the "Use" column of the hvsr_windows_df to False for that window
    bad_rmse = np.unique(bad_rmse)
    if len(bad_rmse) > 0:
        hvsr_data['hvsr_windows_df']['Use'] = hvsr_data['hvsr_windows_df']['Use'] * (rmse_threshold > hvsr_data['hvsr_windows_df']['RMSE_'+column])
        #hvsr_data['hvsr_windows_df'].loc[bad_index, "Use"] = False   

    if verbose:
        if len(bad_rmse) > 0:
            print(f"\n\t\tThe windows starting at the following times have been removed from further analysis ({len(bad_rmse)}/{hvsr_data['hvsr_windows_df'].shape[0]}):")
            for b in hvsr_data['hvsr_windows_df'].index[pd.Series(bad_rmse)]:
                print(f"\t\t  {b}")
        else:
            print('\tNo outlier curves have been removed')

    return hvsr_data


# Helper functions for generate_psds()
# Generate psds from raw data (no response removed)
def __single_psd_from_raw_data(hvsr_data, window_length=30.0, window_length_method='length', window_type='hann',
                               overlap=0.5, num_freq_bins=512,
                               show_psd_plot=False, remove_response=False, do_azimuths=False, verbose=False):
    """Helper function to get psds from raw trace streams (no response information is needed in this case)

    Parameters
    ----------
    hvsr_data : HVSRData object
        HVSRData object containing data to be processed
    window_length : float, optional
        Length of FFT processing window for in seconds, by default 30.0
    overlap : float, optional
        Percent overlap between windows (0-1), by default 0.5.
        A percentage value between 1-100 will be accepted, but will be divided by 100 to convert to 0-1.
        If the value is over 100, the modulus of 100 will be calculated, then divided by 100; i.e., (overlap%100)/100.
    show_psd_plot : bool, optional
        Whether to show a plot of the psds, by default False
    verbose : bool, optional
        Whether to print information about the PSD processing to terminal, by default False

    Returns
    -------
    Tuple (dict, np.array)
        Tuple with index 0 being a dictionary with keys of components ("Z", "E", "N").
        Values are numpy array containing the PSDs for that component at each time step.
        Index 1 of tuple contains a numpy array with the start and end times of each time window used for FFT processing.
    """
    zdata = hvsr_data.stream.select(component='Z').merge()
    edata = hvsr_data.stream.select(component='E').merge()
    ndata = hvsr_data.stream.select(component='N').merge()

    dataDict = {'Z':zdata,
                'E':edata,
                'N':ndata}

    if do_azimuths:
        azimuthStream = hvsr_data.stream.select(component='R').merge()
        
        for azimuthTrace in azimuthStream:
            dataDict[azimuthTrace.stats.component.upper()] = azimuthTrace
        
    

    if remove_response:
        for key, compStream in dataDict.items():
            compStream = compStream.split()
            
            for trace in compStream:
                trace.remove_response(hvsr_data['inv'])
            
            compStream.merge()

        if verbose:
            print("\n\tInstrument Response Removed from Traces\n")

    sample_rate = zdata[0].stats.sampling_rate
    sample_space = zdata[0].stats.delta
    zdata = zdata.split()


    # Transform overlap to proper formatting (% b/w 0-1)
    if overlap > 100:
        if verbose:
            print(f"\tThe parameter overlap={overlap} should be a float between 0-1")
            print(f"\t  Since it is over 100, the modulus of 100 (overlap%100)/100=({overlap%100}) will be used")
        overlap = (overlap % 100)/100
    elif overlap > 1:
        overlap = overlap / 100
    elif overlap >= 0:
        overlap = overlap
    else:
        if verbose:
            print(f"\tThe parameter overlap={overlap} should be a float between 0-1")
            print(f"\t  This has been updated to the default value of overlap=0.5")
        overlap = 0.5 #just set it default otherwise

    # Get number of samples instead of seconds/percentage
    psd_window_samples = int(window_length * sample_rate)
    overlap_samples = overlap * psd_window_samples

    # Generated x values to which data will be interpolated later
    #  This maintains consistency in array size across all FFT windows
    if hasattr(hvsr_data, 'hvsr_band'):
        low_freq = hvsr_data.hvsr_band[0]
        hi_freq = hvsr_data.hvsr_band[1]
    else:
        low_freq = DEFAULT_BAND[0]
        hi_freq = DEFAULT_BAND[1]

    x_freqs = np.logspace(np.log10(low_freq), np.log10(hi_freq), num_freq_bins)

    # For each component, create the time windows and do FFT analysis
    psdDict = {}
    for key, curr_component in dataDict.items():
        psdDict[key] = {}
        
        # Get all data in same format (obspy.Stream, traces will be extracted later)
        if isinstance(curr_component, obspy.Trace):
            st = obspy.Stream([curr_component]).merge()
        else:
            st = curr_component.merge()
        tr = st[0]

        # Initialize for intermediate outputs
        psds = []
        freqs = []
        final_psds = []

        # Get all possible windows and initialize output window list for windows that are actually used
        #  This will likely be the same if there are no gaps in the data
        windows = _create_windows(hvsr_data=hvsr_data, window=window_length, 
                                  overlap=overlap, window_length_method=window_length_method, verbose=False)
        windows_out = []

        # Iterate through each window to trim data trace and perform fft analysis
        for i, (stime, etime) in enumerate(windows):
            # Trim trace to just window time (copy so doesn't overwrite main trace)
            window_trace = tr.copy()
            window_trace.trim(starttime=stime, endtime=etime) 
            
            # Handle gaps in data 
            # Only process longest continous data section in each window, if gaps exist
            window_st = window_trace.split()  # Split into continuous data sections
            longest_trace = window_st[0] # Initialize longest as first trace

            if len(window_st) > 1: # if more than one trace comes out of .split()
                # Get the longest trace and used that for analysis for this window
                for shorttr in window_st:
                    if len(shorttr) > len(longest_trace):
                        longest_trace = shorttr
            window_trace = longest_trace

            # If the data being processed ends up being shorter than window time
            #    Reset inputs to scipy.signal.welch to match new "window" length
            nsamplesperwin = psd_window_samples
            if len(window_trace) < nsamplesperwin:
                nsamplesperwin = len(window_trace.data)
                overlap_samples = nsamplesperwin - 1

            # PERFORM FFT analysis using Welch method if length of window is > 1 sample
            # If time window used, the start time will be recorded in window_out list
                # and PSD will be stored in psdDict[key][str(starttime)] as numpy array.
            if nsamplesperwin > 1:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore') # Sometimes unnecessary warnings arise
                    f, pxx = scipy.signal.welch(window_trace.data, fs=window_trace.stats.sampling_rate, 
                                                window=window_type, nperseg=nsamplesperwin, 
                                                noverlap=overlap_samples, nfft=None, detrend='linear', return_onesided=True, 
                                                scaling='density', axis=-1, average='mean')
                
                # Only add successful psds to psdDict (and the window starttime to window_out)
                if pxx.size > 0 and f.size > 0:
                    freqs.append(f)
                    psds.append(np.flip(pxx))
                    interpPSD = np.interp(x_freqs, f, pxx, left=None, right=None, period=None)
                    interpPSD_dB = 10*np.log10(interpPSD) # Convert to decibels
                    psdDict[key][str(stime)] = interpPSD_dB
                    final_psds.append(interpPSD_dB)
                
                    windows_out.append(stime)
                else:
                    if verbose:
                        print(f"\tWindow starting at {stime} not used ({len(window_trace)} samples long)")
            else:
                if verbose:
                    print(f"\tWindow starting at {stime} not used ({len(window_trace)} samples long)")
        #psds = np.mean(np.array(final_psds), axis=0)
        #psdDict[key][str(stime)] = np.array(final_psds)

        if show_psd_plot:
            plt.plot(x_freqs, psds, linewidth=0.5, c='k')
            plt.semilogx()
            plt.semilogy()

    return psdDict, np.array(windows_out)


# Generate windows "manually"
def _create_windows(hvsr_data, window=30, overlap=0.5, window_length_method='length', verbose=False):
    """Function to create time windows based on input stream.

    Parameters
    ----------
    hvsr_data : HVSRData object, Obspy.Stream, or Obspy.Trace
        Input object with stream data
    window : float or int, optional
        Windowing parameter. If window_length_method='length', this is the length of each window in seconds.
        If window_length_method='number', this must be int or be able to be converted to int, and is the number of windows, by default 30
    overlap : float, optional
        Window overlap in percentage. If >=1, it will be interpreted as a percentage out of 100, by default 0.5
    window_length_method : str, optional
        Which windowing method to use, "length", which creates windows of a specified length, or 
        "number", which creates a specified number of windows, by default 'length'
    verbose : bool, optional
        Whether to print information about the process to terminal, by default False

    Returns
    -------
    np.array
        2D Numpy array containing, the size of the first dimension is the number of windows, size of second dimension is 2 (start and end) 
    """

    length_list = ['window_length', 'window length', 
                   'length', 'len', 'l', 'size', 's']
    
    winNum_list = ['number of windows', 'window_number', 'window number', 
                   'number', 'num', 'winnum', 'window_num', 'amount']

    # Get input data as obspy.Stream
    if isinstance(hvsr_data, HVSRData):
        st = hvsr_data.stream.merge()
    elif isinstance(hvsr_data, obspy.Stream):
        st = hvsr_data.merge()
    elif isinstance(hvsr_data, obspy.Trace):
        st = obspy.Stream([hvsr_data]).merge()
    else:
        raise RuntimeError("hvsr_data parameter of _create_windows() must be sprit.HVSRData, obspy.Stream, or obspy.Trace")

    # Get largest starttime and smallest endtime (to ensure all data is used)
    for i, tr in enumerate(st):
        if i==0:
            maxStart = tr.stats.starttime
            minEnd = tr.stats.endtime
        else:
            if tr.stats.starttime > maxStart:
                maxStart = tr.stats.starttime
            if tr.stats.endtime < minEnd:
                minEnd = tr.stats.endtime
    # Calculate time between end and start
    timeRange = minEnd - maxStart

    # Transform overlap to proper formatting (% b/w 0-1)
    if overlap > 100:
        if verbose:
            print(f"\tThe parameter overlap={overlap} should be a float between 0-1")
            print(f"\t  Since it is over 100, the modulus of 100 (overlap%100)/100=({overlap%100}) will be used")
        overlap = (overlap % 100)/100
    elif overlap > 1:
        overlap = overlap / 100
    elif overlap >= 0:
        overlap = overlap
    else:
        if verbose:
            print(f"\tThe parameter overlap={overlap} should be a float between 0-1")
            print(f"\t  This has been updated to the default value of overlap=0.5")
        overlap = 0.5 #just set it default otherwise

    # Calculate "stride" (time between start of each window) and window length
    if window_length_method.lower() in length_list:
        stride = window * (1-overlap)
        winLength = window
    elif window_length_method.lower() in winNum_list:
        stride = timeRange // window
        winLength = stride / overlap
    else:
        if verbose:
            print(f"\twindow_method={window_length_method} is not a valid entry.")
            print(f"\t  Use any of the following to create windows using a specific size: {length_list}")
            print(f"\t  Use any of the following to create a specific number of windows : {winNum_list}")
            print(f"\t  By default, using a window length of 30 seconds and overlap of 0.5")
        # Default of overlap=0.5, window_length=30
        stride = 15
        winLength = 30
        overlap = 0.5

    # Get start and end of each window, and format appropriately (2d Numpy array)
    windowStarts = np.arange(maxStart, minEnd, stride)
    windowEnds = windowStarts + winLength
    windows = np.array(list(zip(windowStarts, windowEnds)))
    
    # print information if verbose specified
    if verbose:
        verboseStatement = ["\tUsing the following windowing parameters"]
        verboseStatement.append(f"\t Number of windows: {windows.shape[0]}")
        verboseStatement.append(f"\t Window Size: {winLength}")
        verboseStatement.append(f"\t Window Overlap: {overlap}")

        for l in verboseStatement:
            print(l)
    
    return windows


# Remove noisy windows from df
def __remove_windows_from_df(hvsr_data, verbose=False):
    # Get gaps from masked regions of traces
    gaps0 = []
    gaps1 = []
    outStream = hvsr_data['stream_edited'].split()
    for i, trace in enumerate(outStream):
        if i == 0:
            trEndTime = trace.stats.endtime
            comp_end = trace.stats.component
            continue # Wait until the second trace

        trStartTime = trace.stats.starttime
        comp_start = trace.stats.component
        firstDiff = True
        secondDiff = True

        # Check if both are different from any existing gap times
        if trEndTime in gaps0:
            firstDiff = False
        if trStartTime in gaps1:
            secondDiff = False
        
        # If the first element and second element are both new, add to gap list
        if firstDiff and secondDiff:
            gaps0.append(trEndTime)
            gaps1.append(trStartTime)

        trEndTime = trace.stats.endtime
    
    gaps = list(zip(gaps0, gaps1))
    hvsr_windows_df_exists = ('hvsr_windows_df' in hvsr_data.keys()) or ('params' in hvsr_data.keys() and 'hvsr_windows_df' in hvsr_data['params'].keys()) or ('input_params' in hvsr_data.keys() and 'hvsr_windows_df' in hvsr_data['input_params'].keys())
    if hvsr_windows_df_exists:
        hvsrDF = hvsr_data['hvsr_windows_df']
        use_before = hvsrDF["Use"].copy().astype(bool)
        outStream = hvsr_data['stream_edited'].split()
        #for i, trace in enumerate(outStream):
            #if i == 0:
            #    trEndTime = trace.stats.endtime
            #    comp_end = trace.stats.component
            #    continue
            #trStartTime = trace.stats.starttime
            #comp_start = trace.stats.component
            
            #if trEndTime < trStartTime and comp_end == comp_start:
        hvsrDF['Use'] = hvsrDF['Use'].astype(bool)
        for gap in gaps:
            # All windows whose starts occur within the gap are set to False
            gappedIndices = hvsrDF.between_time(gap[0].datetime.time(), gap[1].datetime.time()).index#.loc[:, 'Use']
            hvsrDF.loc[gappedIndices,'Use'] = False

            # The previous window is also set to false, since the start of the gap lies within that window
            prevInd = hvsrDF.index.get_indexer([gap[0]], method='ffill')
            prevDTInd = hvsrDF.index[prevInd]
            hvsrDF.loc[prevDTInd, 'Use'] = False

        hvsrDF['Use'] = hvsrDF['Use'].astype(bool)
            
        hvsr_data['hvsr_windows_df'] = hvsrDF  # May not be needed, just in case, though

        use_after = hvsrDF["Use"].astype(bool)
        removed = ~use_before.eq(use_after)

        if verbose:
            if removed[removed].shape[0]>0:
                print(f"\n\t\tThe windows starting at the following times have been removed from further analysis ({removed[removed].shape[0]}/{hvsrDF.shape[0]})")
                for t in removed[removed].index.to_pydatetime():
                    print(f'\t\t  {t} ')
            else:
                print(f"\t\tNo windows removed using remove_noise()")

        outStream.merge()
        hvsr_data['stream_edited'] = outStream

    hvsr_data['x_gaps_obspyDT'] = gaps

    return hvsr_data


# Helper functions for process_hvsr()
# Get diffuse field assumption data
def _dfa(x, hvsr_data=None, verbose=False):#, equal_interval_energy, median_daily_psd, verbose=False):
    """Helper function for performing Diffuse Field Assumption (DFA) analysis

        x : numpy.array
            Numpy array or list containing all x values (frequency or period) for each psd
        hvsr_data : HVSRData object
            HVSRData object containing all the data and information about the HVSR point being processed
        verbose : bool, optional
            Whether to print information about the DFA processing to terminal, default = False.
    
    """
    # Use equal energy for daily PSDs to give small 'events' a chance to contribute
    # the same as large ones, so that pH1List+pH2List+P3=1
    hvsr_tSteps = []
    
    if verbose:
        print('\tUsing Diffuse Field Assumption (DFA)', flush=True)
        warnings.warn('WARNING: DFA method is currently experimental and has not been extensively tested.')

    hvsr_data['dfa'] = {}
    sum_ns_power = list()
    sum_ew_power = list()
    sum_z_power = list()
    hvsr_data['dfa']['time_int_psd'] = {'Z':{}, 'E':{}, 'N':{}}
    hvsr_data['dfa']['time_values'] = list()
    hvsr_data['dfa']['equal_interval_energy'] = {'Z':{}, 'E':{}, 'N':{}}

    ti = 0    
    for i, t_int in enumerate(hvsr_data['ppsds']['Z']['current_times_used']):
        ti+=1
        hvsr_curve_tinterval = []

        # Initialize some lists for later use
        sum_ns_power = list()
        sum_ew_power = list()
        sum_z_power = list()
        
        # Add the time interval to the time_values list
        time_int = str(t_int)#day_time.split('T')[0]
        if time_int not in hvsr_data['dfa']['time_values']:
            hvsr_data['dfa']['time_values'].append(time_int)

        # Get the psd data for each time, 
        tiIndDF = hvsr_data['hvsr_windows_df'].index[i]
        hvsr_data['dfa']['time_int_psd']['Z'][time_int] = hvsr_data['hvsr_windows_df'].loc[tiIndDF,'psd_values_Z']
        hvsr_data['dfa']['time_int_psd']['E'][time_int] = hvsr_data['hvsr_windows_df'].loc[tiIndDF,'psd_values_E']
        hvsr_data['dfa']['time_int_psd']['N'][time_int] = hvsr_data['hvsr_windows_df'].loc[tiIndDF,'psd_values_N']

        # Each PSD for the time_int (there is only one in SpRIT)
        pZList = list()
        pH1List = list()
        pH2List = list()
        sum_pz = 0
        sum_p1 = 0
        sum_p2 = 0

        # Each sample of the PSD , convert to power
        for j in range(len(x) - 1):
            pz = __get_power([hvsr_data['dfa']['time_int_psd']['Z'][time_int][j][()], hvsr_data['dfa']['time_int_psd']['Z'][time_int][j + 1][()]], [x[j], x[j + 1]])
            pZList.append(pz)
            sum_pz += pz

            p1 = __get_power([hvsr_data['dfa']['time_int_psd']['E'][time_int][j][()], hvsr_data['dfa']['time_int_psd']['E'][time_int][j + 1][()]], [x[j], x[j + 1]])
            pH1List.append(p1)
            sum_p1 += p1

            p2 = __get_power([hvsr_data['dfa']['time_int_psd']['N'][time_int][j][()], hvsr_data['dfa']['time_int_psd']['N'][time_int][j + 1][()]], [x[j], x[j + 1]])
            pH2List.append(p2)
            sum_p2 += p2
        
        sum_power = sum_pz + sum_p1 + sum_p2  # total power

        # Mormalized power
        for j in range(len(x) - 1):
            sum_z_power.append(pZList[j] / sum_power)
            sum_ew_power.append(pH1List[j] / sum_power)
            sum_ns_power.append(pH2List[j] / sum_power)
            
        # Average the normalized time interval power
        for j in range(len(x) - 1):
            sum_z_power[j] /= len(hvsr_data['dfa']['time_int_psd']['Z'][time_int])
            sum_ew_power[j] /= len(hvsr_data['dfa']['time_int_psd']['E'][time_int])
            sum_ns_power[j] /= len(hvsr_data['dfa']['time_int_psd']['N'][time_int])

        hvsr_data['dfa']['equal_interval_energy']['Z'][time_int] = sum_z_power
        hvsr_data['dfa']['equal_interval_energy']['E'][time_int] = sum_ew_power
        hvsr_data['dfa']['equal_interval_energy']['N'][time_int] = sum_ns_power


        # Start Second dfa section in original iris script
        # Perform h/v calculation at each frequency/time step
        eie = hvsr_data['dfa']['equal_interval_energy'] 
        for j in range(len(x) - 1):
            if (time_int in list(eie['Z'].keys())) and (time_int in list(eie['E'].keys())) and (time_int in list(eie['N'].keys())):
                hv_x = math.sqrt((eie['E'][time_int][j] + eie['N'][time_int][j]) / eie['Z'][time_int][j])
                hvsr_curve_tinterval.append(hv_x)
            else:
                if verbose > 0:
                    print('WARNING: '+ t_int + ' missing component, skipped!')
                continue
        
        #Average over time
        hvsr_tSteps.append(hvsr_curve_tinterval)

    return hvsr_tSteps


# Helper function for smoothing across frequencies
def __freq_smooth_window(hvsr_out, f_smooth_width, kind_freq_smooth):
    """Helper function to smooth frequency if 'constant' or 'proportional' is passed to freq_smooth parameter of process_hvsr() function"""
    if kind_freq_smooth == 'constant':
        fwidthHalf = f_smooth_width//2
    elif kind_freq_smooth == 'proportional':
        anyKey = list(hvsr_out['psd_raw'].keys())[0]
        freqLength = hvsr_out['psd_raw'][anyKey].shape[1]
        if f_smooth_width > 1:
            fwidthHalf = int(f_smooth_width/100 * freqLength)
        else:
            fwidthHalf = int(f_smooth_width * freqLength)
    else:
        warnings.warn('Oops, typo somewhere')


    for k in hvsr_out['psd_raw']:
        colName = f'psd_values_{k}'

        newTPSD = list(np.stack(hvsr_out['hvsr_windows_df'][colName]))
        #newTPSD = list(np.ones_like(hvsr_out['psd_raw'][k]))

        for t, tPSD in enumerate(hvsr_out['psd_raw'][k]):
            for i, fVal in enumerate(tPSD):
                if i < fwidthHalf:
                    downWin = i
                    ind = -1*(fwidthHalf-downWin)
                    windMultiplier_down = np.linspace(1/fwidthHalf, 1-1/fwidthHalf, fwidthHalf)
                    windMultiplier_down = windMultiplier_down[:ind]
                else:
                    downWin = fwidthHalf
                    windMultiplier_down =  np.linspace(1/fwidthHalf, 1-1/fwidthHalf, fwidthHalf)
                if i + fwidthHalf >= len(tPSD):
                    upWin = (len(tPSD) - i)
                    ind = -1 * (fwidthHalf-upWin+1)
                    windMultiplier_up = np.linspace(1-1/fwidthHalf, 0, fwidthHalf)
                    windMultiplier_up = windMultiplier_up[:ind]

                else:
                    upWin = fwidthHalf+1
                    windMultiplier_up = np.linspace(1 - 1/fwidthHalf, 0, fwidthHalf)
            
                windMultiplier = list(np.hstack([windMultiplier_down, windMultiplier_up]))
                midInd = np.argmax(windMultiplier)
                if i > 0:
                    midInd+=1
                windMultiplier.insert(midInd, 1)
                smoothVal = np.divide(np.sum(np.multiply(tPSD[i-downWin:i+upWin], windMultiplier)), np.sum(windMultiplier))
                newTPSD[t][i] = smoothVal

        hvsr_out['psd_raw'][k] = newTPSD
        hvsr_out['hvsr_windows_df'][colName] = pd.Series(list(newTPSD), index=hvsr_out['hvsr_windows_df'].index)


    return hvsr_out


# Get an HVSR curve, given an array of x values (freqs), and a dict with psds for three components
def __get_hvsr_curve(x, psd, horizontal_method, hvsr_data, azimuth=None, verbose=False):
    """ Get an HVSR curve from three components over the same time period/frequency intervals

    Parameters
    ----------
        x   : list or array_like
            x value (frequency or period)
        psd : dict
            Dictionary with psd values for three components. Usually read in as part of hvsr_data from process_hvsr
        horizontal_method : int or str
            Integer or string, read in from process_hvsr method parameter
    
    Returns
    -------
        tuple
         (hvsr_curve, hvsr_tSteps), both np.arrays. hvsr_curve is a numpy array containing H/V ratios at each frequency/period in x.
         hvsr_tSteps only used with diffuse field assumption method. 

    """
    hvsr_curve = []
    hvsr_tSteps = []
    hvsr_azimuth = {}

    params = hvsr_data
    if horizontal_method==1 or horizontal_method =='dfa' or horizontal_method =='Diffuse Field Assumption':
        hvsr_tSteps = _dfa(x, hvsr_data, verbose)
        hvsr_curve = np.mean(hvsr_tSteps, axis=0)
    else:
        for j in range(len(x)-1):
            psd0 = [psd['Z'][j], psd['Z'][j + 1]]
            psd1 = [psd['E'][j], psd['E'][j + 1]]
            psd2 = [psd['N'][j], psd['N'][j + 1]]
            f =    [x[j], x[j + 1]]

            hvratio = __get_hvsr(psd0, psd1, psd2, f, azimuth=azimuth, use_method=horizontal_method)
            hvsr_curve.append(hvratio)
            
            # Do azimuth HVSR Calculations, if applicable
            hvratio_az = 0
            for k in psd.keys():
                if k.lower() not in ['z', 'e', 'n']:
                    psd_az = [psd[k][j], psd[k][j + 1]]
                    hvratio_az = __get_hvsr(psd0, psd_az, None, f, azimuth=azimuth, use_method='az')
                    if j == 0:
                        hvsr_azimuth[k] = [hvratio_az]
                    else:
                        hvsr_azimuth[k].append(hvratio_az)
            
        hvsr_tSteps = None # Only used for DFA


    return np.array(hvsr_curve), hvsr_azimuth, hvsr_tSteps


# Get HVSR
def __get_hvsr(_dbz, _db1, _db2, _x, azimuth=None, use_method=3):
    """ Helper function to calculate H/V ratio

    _dbz : list
        Two item list with deciBel value of z component at either end of particular frequency step
    _db1 : list
        Two item list with deciBel value of either e or n component (does not matter which) at either end of particular frequency step
    _db2 : list
        Two item list with deciBel value of either e or n component (does not matter which) at either end of particular frequency step
    _x : list
        Two item list containing frequency values at either end of frequency step of interest
    use_method : int, default = 4
        H is computed based on the selected use_method see: https://academic.oup.com/gji/article/194/2/936/597415
            use_method:
            (1) Diffuse Field Assumption (DFA)
            (2) arithmetic mean, that is, H ≡ (HN + HE)/2
            (3) geometric mean, that is, H ≡ √HN · HE, recommended by the SESAME project (2004)
            (4) vector summation, that is, H ≡ √H2 N + H2 E
            (5) quadratic mean, that is, H ≡ √(H2 N + H2 E )/2
            (6) maximum horizontal value, that is, H ≡ max {HN, HE}
        """

    _pz = __get_power(_dbz, _x)
    _p1 = __get_power(_db1, _x)
    
    _hz = math.sqrt(_pz)
    _h1 = math.sqrt(_p1)

    if _db2 is None:
        _p2 = 1
        _h2 = 1
    else:
        _p2 = __get_power(_db2, _x)
        _h2 = math.sqrt(_p2)

    def az_calc(az, h1, h2):
        if az is None:
            az = 90

        if az == 'HV':
            return math.sqrt(_h1 * _h2)

        az_rad = np.deg2rad(az)
        return np.add(h2 * np.cos(az_rad), h1 * np.sin(az_rad))

    # Previous structure from IRIS module
    #_h = {  2: (_h1 + _h2) / 2.0, # Arithmetic mean
    #        3: math.sqrt(_h1 * _h2), # Geometric mean
    #        4: math.sqrt(_p1 + _p2), # Vector summation
    #        5: math.sqrt((_p1 + _p2) / 2.0), # Quadratic mean
    #        6: max(_h1, _h2), # Max horizontal value
    #        7: min(_h1, _h2), # Minimum horizontal value
    #        8: 'do_azimuth_calc',
    #        'az': _h1} # If azimuth, horizontals are already combined, no _h2} 
    
    # Combine horizontal methods
    if use_method == 2 or str(use_method) == '2':
        _hCombined = (_h1 + _h2) / 2.0
    elif use_method == 3 or str(use_method) == '3':
        _hCombined = math.sqrt(_h1 * _h2)
    elif use_method == 4 or str(use_method) == '4':
        _hCombined = math.sqrt(_p1 + _p2)
    elif use_method == 5 or str(use_method) == '5':
        _hCombined = math.sqrt((_p1 + _p2) / 2.0)
    elif use_method == 6 or str(use_method) == '6':
        _hCombined = max(_h1, _h2)
    elif use_method == 7 or str(use_method) == '7':
        _hCombined = min(_h1, _h2)
    elif use_method == 8 or str(use_method) == '8':
        _hCombined = az_calc(azimuth, _h1, _h2)
    elif use_method == 'az' or str(use_method) == 'az':
        _hCombined = _h1
    else:
        _hCombined = _h1
    
    _hvsr = _hCombined / _hz
    return _hvsr


# For converting dB scaled data to power units
def __get_power(_db, _x):
    """Calculate power for HVSR

    #FROM ORIGINAL (I think this is only step 6)
        Undo deciBel calculations as outlined below:
            1. Dividing the window into 13 segments having 75% overlap
            2. For each segment:
                2.1 Removing the trend and mean
                2.2 Apply a 10% sine taper
                2.3 FFT
            3. Calculate the normalized PSD
            4. Average the 13 PSDs & scale to compensate for tapering
            5. Frequency-smooth the averaged PSD over 1-octave intervals at 1/8-octave increments
            6. Convert power to decibels
    #END FROM ORIGINAL

    Parameters
    ----------
    _db : list
        Two-item list with individual power values in decibels for specified freq step.
    _x : list
        Two-item list with Individual x value (either frequency or period)
    
    Returns
    -------
    _p : float
        Individual power value, converted from decibels

    NOTE
    ----
        PSD is equal to the power divided by the width of the bin
          PSD = P / W
          log(PSD) = Log(P) - log(W)
          log(P) = log(PSD) + log(W)  here W is width in frequency
          log(P) = log(PSD) - log(Wt) here Wt is width in period

    for each bin perform rectangular integration to compute power
    power is assigned to the point at the begining of the interval
         _   _
        | |_| |
        |_|_|_|

     Here we are computing power for individual ponts, so, no integration is necessary, just
     compute area.
    """
    _dx = abs(np.diff(_x)[0])
    _p = np.multiply(np.mean(__remove_db(_db)), _dx)
    return _p


# Remove decibel scaling
def __remove_db(_db_value):
    """convert dB power to power"""
    _values = list()
    for _d in _db_value:
        _values.append(10 ** (float(_d) / 10.0))
    #FIX THIS
    if _values[1]==0:
       _values[1]=10e-300
    return _values


# Find peaks in the hvsr ccruve
def __find_peaks(_y):
    """Finds all possible peaks on hvsr curves
    Parameters
    ----------
    _y : list or array
        _y input is list or array of a curve.
          In this case, this is either main hvsr curve or individual time step curves
    """
    _index_list = scipy.signal.argrelextrema(np.array(_y), np.greater)

    return _index_list[0]


# Get additional HVSR params for later calcualtions
def __gethvsrparams(hvsr_out):
    """Private function to get HVSR parameters for later calculations (things like standard deviation, etc)"""

    hvsrp2 = {}
    hvsrm2 = {}
    
    hvsrp2=[]
    hvsrm=[]
    
    hvsr_log_std = {}

    hvsr = hvsr_out['hvsr_curve']
    hvsr_az = hvsr_out['hvsr_az']
    hvsrDF = hvsr_out['hvsr_windows_df']

    if len(hvsr_out['ind_hvsr_curves'].keys()) > 0:
        # With arrays, original way of doing it
        hvsr_log_std = {}
        for k in hvsr_out['ind_hvsr_curves'].keys():
            hvsr_log_std[k] = np.nanstd(np.log10(hvsr_out['ind_hvsr_curves'][k]), axis=0)

        #With dataframe, updated way to use DF for all time-step tasks, still testing
        logStackedata = {}
        hvsrp = {}
        hvsrm = {}
        hvsrp2 = {}
        hvsrm2 = {}
        hvsr_log_std = {}
        for col_name in hvsr_out['hvsr_windows_df'].columns:
            if col_name.startswith("HV_Curves"):
                if col_name == 'HV_Curves':
                    colSuffix = '_HV'
                    colID = 'HV'
                else:
                    colSuffix = '_'+'_'.join(col_name.split('_')[2:])
                    colID = colSuffix.split('_')[1]
                stackedData = np.stack(hvsr_out['hvsr_windows_df'][col_name])

                logStackedata = np.log10(stackedData).tolist()
                for i, r in enumerate(logStackedata):
                    logStackedata[i] = np.array(r)

                hvsr_out['hvsr_windows_df']['Log10_HV_Curves'+colSuffix] = logStackedata
                hvsr_log_std[colID] = np.nanstd(np.stack(hvsr_out['hvsr_windows_df']['Log10_HV_Curves'+colSuffix][hvsrDF['Use']]), axis=0)

                #The components are already calculated, don't need to recalculate aren't calculated at the time-step level
                hvsrp[colID] = np.add(hvsr_out['hvsr_curve'], hvsr_out['ind_hvsr_stdDev'][colID])
                hvsrm[colID] = np.subtract(hvsr_out['hvsr_curve'], hvsr_out['ind_hvsr_stdDev'][colID])
                for k in hvsr_out['hvsr_az'].keys():
                    hvsrp[colID] = np.add(hvsr_out['hvsr_az'][k], hvsr_out['ind_hvsr_stdDev'][colID])
                    hvsrm[colID] = np.subtract(hvsr_out['hvsr_az'][k], hvsr_out['ind_hvsr_stdDev'][colID])
                hvsrp2[colID] = np.multiply(hvsr, np.exp(hvsr_log_std[colID]))
                hvsrm2[colID] = np.divide(hvsr, np.exp(hvsr_log_std[colID]))

                newKeys = ['hvsr_log_std', 'hvsrp','hvsrm', 'hvsrp2','hvsrm2']
                newVals = [hvsr_log_std,    hvsrp,  hvsrm,   hvsrp2,  hvsrm2]
                for i, nk in enumerate(newKeys):
                    if nk not in hvsr_out.keys():
                        hvsr_out[nk] = {}
                    hvsr_out[nk][colID] = np.array(newVals[i][colID])

    return hvsr_out


# HELPER FUNCTIONS FOR GET REPORT
# Private function to generate print report
def _generate_print_report(hvsr_results, azimuth="HV", show_print_report=True, verbose=False):
    """Helper function to perform create a printed (monospace) report with summary data for HVSR Site 

    Parameters
    ----------
    hvsr_results : HVSRData object
        HVSRData object with data to be reported on
    show_print_report : bool, optional
        Whether output will be produced or not (if show_print_report=True, no ouptut will be produced (report will not be printed)), by default False

    Returns
    -------
    HVSRData object
        HVSRData object with the ["Print_Report"] attribute created or updated.
        The .Print_Report attribute is a formatted string that can be 
        displayed using print(hvsr_results['Print_Report'] with a summary of the HVSR results)
    """
    #Print results

    #Make separators for nicely formatted print output
    sepLen = 99
    siteSepSymbol = '='
    intSepSymbol = u"\u2012"
    extSepSymbol = u"\u2014"
    
    if sepLen % 2 == 0:
        remainVal = 1
    else:
        remainVal = 0

    siteWhitespace = 2
    #Format the separator lines internal to each site
    internalSeparator = intSepSymbol.center(sepLen-4, intSepSymbol).center(sepLen, ' ')

    extSiteSeparator = "".center(sepLen, extSepSymbol)
    siteSeparator = f"{hvsr_results['input_params']['site']}".center(sepLen - siteWhitespace, ' ').center(sepLen, siteSepSymbol)
    endSiteSeparator = "".center(sepLen, siteSepSymbol)

    #Start building list to print
    report_string_list = []
    report_string_list.append("") #Blank line to start
    report_string_list.append(extSiteSeparator)
    report_string_list.append(siteSeparator)
    report_string_list.append(extSiteSeparator)
    #report_string_list.append(internalSeparator)
    report_string_list.append('')
    report_string_list.append(f"\tSite Name: {hvsr_results['input_params']['site']}")
    report_string_list.append(f"\tAcq. Date: {hvsr_results['input_params']['acq_date']}")
    report_string_list.append(f"\tLocation : {hvsr_results['input_params']['longitude']}°, {hvsr_results['input_params']['latitude']}°")
    report_string_list.append(f"\tElevation: {hvsr_results['input_params']['elevation']} meters")
    report_string_list.append('')
    report_string_list.append(internalSeparator)
    report_string_list.append('')
    if 'BestPeak' not in hvsr_results.keys():
        report_string_list.append('\tNo identifiable BestPeak was present between {} for {}'.format(hvsr_results['input_params']['hvsr_band'], hvsr_results['input_params']['site']))
    else:
        curvTestsPassed = (hvsr_results['BestPeak'][azimuth]['PassList']['WinLen'] +
                            hvsr_results['BestPeak'][azimuth]['PassList']['SigCycles']+
                            hvsr_results['BestPeak'][azimuth]['PassList']['LowCurveStD'])
        curvePass = curvTestsPassed > 2
        
        #Peak Pass?
        peakTestsPassed = ( hvsr_results['BestPeak'][azimuth]['PassList']['ProminenceLow'] +
                    hvsr_results['BestPeak'][azimuth]['PassList']['ProminenceHi']+
                    hvsr_results['BestPeak'][azimuth]['PassList']['AmpClarity']+
                    hvsr_results['BestPeak'][azimuth]['PassList']['FreqStability']+
                    hvsr_results['BestPeak'][azimuth]['PassList']['LowStDev_Freq']+
                    hvsr_results['BestPeak'][azimuth]['PassList']['LowStDev_Amp'])
        peakPass = peakTestsPassed >= 5

        report_string_list.append('\t{0:.3f} Hz Peak Frequency ± {1:.4f} Hz'.format(hvsr_results['BestPeak'][azimuth]['f0'], float(hvsr_results["BestPeak"][azimuth]['Sf'])))        
        if curvePass and peakPass:
            report_string_list.append('\t  {} Peak at {} Hz passed quality checks! :D'.format(sprit_utils._check_mark(), round(hvsr_results['BestPeak'][azimuth]['f0'],3)))
        else:
            report_string_list.append('\t  {} Peak at {} Hz did NOT pass quality checks :('.format(sprit_utils._x_mark(), round(hvsr_results['BestPeak'][azimuth]['f0'],3)))
        report_string_list.append('')
        report_string_list.append(internalSeparator)
        report_string_list.append('')

        justSize=34
        #Print individual results
        report_string_list.append('\tCurve Tests: {}/3 passed (3/3 needed)'.format(curvTestsPassed))
        report_string_list.append(f"\t\t {hvsr_results['BestPeak'][azimuth]['Report']['Lw'][-1]}"+" Length of processing windows".ljust(justSize)+f"{hvsr_results['BestPeak'][azimuth]['Report']['Lw']}")
        report_string_list.append(f"\t\t {hvsr_results['BestPeak'][azimuth]['Report']['Nc'][-1]}"+" Number of significant cycles".ljust(justSize)+f"{hvsr_results['BestPeak'][azimuth]['Report']['Nc']}")
        report_string_list.append(f"\t\t {hvsr_results['BestPeak'][azimuth]['Report']['σ_A(f)'][-1]}"+" Small H/V StDev over time".ljust(justSize)+f"{hvsr_results['BestPeak'][azimuth]['Report']['σ_A(f)']}")

        report_string_list.append('')
        report_string_list.append("\tPeak Tests: {}/6 passed (5/6 needed)".format(peakTestsPassed))
        report_string_list.append(f"\t\t {hvsr_results['BestPeak'][azimuth]['Report']['A(f-)'][-1]}"+" Peak is prominent below".ljust(justSize)+f"{hvsr_results['BestPeak'][azimuth]['Report']['A(f-)']}")
        report_string_list.append(f"\t\t {hvsr_results['BestPeak'][azimuth]['Report']['A(f+)'][-1]}"+" Peak is prominent above".ljust(justSize)+f"{hvsr_results['BestPeak'][azimuth]['Report']['A(f+)']}")
        report_string_list.append(f"\t\t {hvsr_results['BestPeak'][azimuth]['Report']['A0'][-1]}"+" Peak is large".ljust(justSize)+f"{hvsr_results['BestPeak'][azimuth]['Report']['A0']}")
        if hvsr_results['BestPeak'][azimuth]['PassList']['FreqStability']:
            res = sprit_utils._check_mark()
        else:
            res = sprit_utils._x_mark()
        report_string_list.append(f"\t\t {res}"+ " Peak freq. is stable over time".ljust(justSize)+ f"{hvsr_results['BestPeak'][azimuth]['Report']['P-'][:5]} and {hvsr_results['BestPeak'][azimuth]['Report']['P+'][:-1]} {res}")
        report_string_list.append(f"\t\t {hvsr_results['BestPeak'][azimuth]['Report']['Sf'][-1]}"+" Stability of peak (Freq. StDev)".ljust(justSize)+f"{hvsr_results['BestPeak'][azimuth]['Report']['Sf']}")
        report_string_list.append(f"\t\t {hvsr_results['BestPeak'][azimuth]['Report']['Sa'][-1]}"+" Stability of peak (Amp. StDev)".ljust(justSize)+f"{hvsr_results['BestPeak'][azimuth]['Report']['Sa']}")
    report_string_list.append('')
    report_string_list.append(f"Calculated using {hvsr_results['hvsr_windows_df']['Use'].astype(bool).sum()}/{hvsr_results['hvsr_windows_df']['Use'].count()} time windows".rjust(sepLen-1))
    report_string_list.append(extSiteSeparator)
    #report_string_list.append(endSiteSeparator)
    #report_string_list.append(extSiteSeparator)
    report_string_list.append('')
    
    reportStr=''
    #Now print it
    for line in report_string_list:
        reportStr = reportStr+'\n'+line

    if show_print_report or verbose:
        print(reportStr)

    hvsr_results['BestPeak'][azimuth]['Report']['Print_Report'] = reportStr
    if azimuth=='HV' or azimuth=='R':
        hvsr_results['Print_Report'] = reportStr
    return hvsr_results


# Private function to generate table report
def _generate_table_report(hvsr_results, azimuth='HV', show_table_report=True, verbose=False):
    """Helper function for get_report() to generate a site report formatted into a pandas dataframe 

    Parameters
    ----------
    hvsr_results : HVSRData
        HVSRData object containing information about which the report will be generated.
    azimuth : str, optional
        The azimuth for which this report will be generated. If none specified/calculated, by default 'HV'
    show_table_report : bool, optional
        Whether to print the table report (as text) to the terminal
    verbose : bool, optional
        Whether or not to print information about the table report generation (including the pandas dataframe upon creation) to the terminal, by default False


    Returns
    -------
    HVSRData
        An HVSRData object with the ["Table_Report"] attribute created/updated. 
        This is a pandas.DataFrame instance, but can be exported to csv.
    """
    
    coord0Dir = hvsr_results['input_params']['output_crs'].axis_info[0].direction

    # Figure out which coordinate axis is which (some CRS do Y, X)
    if coord0Dir.lower() in ['north', 'south']:
        xaxisinfo = hvsr_results['input_params']['output_crs'].axis_info[1]
        yaxisinfo = hvsr_results['input_params']['output_crs'].axis_info[0]
    else:
        xaxisinfo = hvsr_results['input_params']['output_crs'].axis_info[0]
        yaxisinfo = hvsr_results['input_params']['output_crs'].axis_info[1]
    
    # Get the axis name
    xaxis_name = xaxisinfo.name
    yaxis_name = yaxisinfo.name
    
    # Simplify the axis name
    if 'longitude' in xaxis_name.lower():
        xaxis_name = 'Longitude'
    if 'latitude' in yaxis_name.lower():
        yaxis_name = 'Latitude'
        
    pdCols = ['Site Name', 'Acq_Date', xaxis_name, yaxis_name, 'Elevation', 'Peak', 'Peak_StDev',
            'PeakPasses','WinLen','SigCycles','LowCurveStD',
            'ProminenceLow','ProminenceHi','AmpClarity','FreqStability', 'LowStDev_Freq','LowStDev_Amp']
    d = hvsr_results
    criteriaList = []
    criteriaList.append(hvsr_results['BestPeak'][azimuth]["PeakPasses"])
    for p in hvsr_results['BestPeak'][azimuth]["PassList"]:
        criteriaList.append(hvsr_results['BestPeak'][azimuth]["PassList"][p])
    dfList = [[d['input_params']['site'], d['input_params']['acq_date'], d['input_params']['xcoord'], d['input_params']['ycoord'], d['input_params']['elevation'], round(d['BestPeak'][azimuth]['f0'], 3), round(d['BestPeak'][azimuth]['Sf'], 4)]]
    dfList[0].extend(criteriaList)

    outDF = pd.DataFrame(dfList, columns=pdCols)
    outDF.index.name = 'ID'
    
    if show_table_report or verbose:
        print('\nTable Report:\n')
        maxColWidth = 13
        print('  ', end='')
        for col in outDF.columns:
            if len(str(col)) > maxColWidth:
                colStr = str(col)[:maxColWidth-3]+'...'
            else:
                colStr = str(col)
            print(colStr.ljust(maxColWidth), end='  ')
        print() #new line
        for c in range(len(outDF.columns) * (maxColWidth+2)):
            if c % (maxColWidth+2) == 0:
                print('|', end='')
            else:
                print('-', end='')
        print('|') #new line
        print('  ', end='') #Small indent at start                    
        for row in outDF.iterrows():
            for col in row[1]:
                if len(str(col)) > maxColWidth:
                    colStr = str(col)[:maxColWidth-3]+'...'
                else:
                    colStr = str(col)
                print(colStr.ljust(maxColWidth), end='  ')
            print()

    hvsr_results['BestPeak'][azimuth]['Report']['Table_Report'] = outDF
    if azimuth == 'HV' or azimuth == 'R':
        hvsr_results['Table_Report'] = outDF
    return hvsr_results


# Display html report without creating temporary file
def _display_html_report(html_report):
    import platform
    import tempfile
    import time
    import webbrowser

    autodelete = platform.system() != "Windows"

    with tempfile.NamedTemporaryFile(mode="w", delete=autodelete, suffix=".html") as tmp_file:
        tmp_file.write(html_report)
        file_path = tmp_file.name
        file_path = file_path.replace('\\'[0], '/')
        rawfpath = file_path
        print(rawfpath)
        
        if autodelete:
            client = webbrowser
            if not file_path.startswith("file:///"):
                file_path = f"file:///{file_path}"
            client.open_new(file_path)                
            # Adding a short sleep so that the file does not get cleaned
            # up immediately in case the browser takes a while to boot.
            time.sleep(3)

    if not autodelete:
        client = webbrowser
        if not file_path.startswith("file:///"):
            file_path = f"file:///{file_path}"
        client.open_new(file_path)
        
        time.sleep(3)
        os.unlink(rawfpath)  # Cleaning up the file in case of Windows


# Private function for html report generation
def _generate_html_report(hvsr_results, azimuth='HV', show_html_report=False, verbose=False):
    """Private function that generates html report, intented to be used by get_report() public function

    Parameters
    ----------
    hvsr_results : HVSRData or HVSRBatch
        Input data from which to generate report
    show_html_report : bool, optional
        Whether to show the report or simply generate and save it in the "HTML_Report" attribute of hvsr_results, by default False
    verbose : bool, optional
        Whether to print information about the HTML report generation to terminal

    Returns
    -------
    HVSRData or HVSRBatch
        Returns the input dataset, with the HTML_Report attribute updated with the html text of the report
    """
    htmlTemplatePath = RESOURCE_DIR.joinpath('html_report_template.html')

    with open(htmlTemplatePath, 'r') as htmlF:
        html = htmlF.read()

    # Update report title (site name)
    html = html.replace("HVSR_REPORT_TITLE", hvsr_results['site'])
    html = html.replace("HVSR_ID", hvsr_results['hvsr_id'])

    # Update peak freq info
    html = html.replace("PEAKFREQ", str(round(hvsr_results['BestPeak'][azimuth]['f0'], 3)))
    html = html.replace("PEAKSTDEV", str(round(hvsr_results['BestPeak'][azimuth]['Sf'], 3)))

    if hvsr_results.Table_Report['PeakPasses'][0]:
        html = html.replace("SESAME_TESTS_RESULTS", 'Peak has passed the SESAME validation tests.')
    else:
        html = html.replace("SESAME_TESTS_RESULTS", 'Peak did not pass the SESAME validation tests.')

    # Update image source
    # Save the plot to a BytesIO object
    # Default to matplotlib object
    plotEngine = 'matplotlib'
    if 'get_report' in hvsr_results.processing_parameters:
        plotEngine = hvsr_results.processing_parameters['get_report']['plot_engine'].lower()
        
    if str(plotEngine).lower() not in ['plotly', 'plty', 'p']:
        fig = plt.figure(hvsr_results['Plot_Report'])
        fig.set_size_inches(8.5, 6)
        #fig.set_size_inches(4.25, 3)
        # Create a byte stream from the image
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)

        # Encode the image to base64
        hvplot_base64 = base64.b64encode(buf.read()).decode('utf-8')
        # Embed the image in the html document
        html = html.replace("./output.png", f'data:image/png;base64,{hvplot_base64}')
    else:
        #htmlstring = plotly.io.to_html(hvsr_results.Plot_Report, include_plotlyjs=False)
        #print(type(htmlstring))

        img = hvsr_results.Plot_Report.to_image(format='png', engine='kaleido')
        hvplot_base64 = base64.b64encode(img).decode('utf8')

        html = html.replace("./output.png", f'data:image/png;base64,{hvplot_base64}')

    # Update formatting for print report for html
    html_print_report = hvsr_results.Print_Report.replace('\n', '<br>').replace('\t', "&nbsp;&nbsp;&nbsp;&nbsp;")
    html_print_report = html_print_report.replace('<br>', '', 2) #Remove the first two breaks
    html_print_report = html_print_report.replace('✔', '&#10004;')
    html_print_report = html_print_report.replace('✘', '&cross;')

    majorSepLine = u"\u2014"*99
    majorSepLine = u"\u2014"*99
    minorSepLine = u"\u2012"*95
    majorSepLineHTML = '&mdash;'*40
    minorSepLineHTML = '&mdash;&nbsp;'*25

    startInd = html_print_report.index('&nbsp;&nbsp;&nbsp;&nbsp;Site Name:')
    html_print_report = "<br><br>" + html_print_report[startInd:]
    lastInd = html_print_report.index(majorSepLine)
    html_print_report = html_print_report[:lastInd]
    
    html_print_report = html_print_report.replace(majorSepLine, 'majorSepLineHTML') # Replace the major separator lines
    html_print_report = html_print_report.replace(minorSepLine, minorSepLineHTML) # Replace the minor separator lines
    html_print_report = html_print_report.replace("=", '') # Get rid of =

    html = html.replace('HVSR_PRINT_REPORT', html_print_report)

    # Update table
    htmlTable = hvsr_results.Table_Report.iloc[:,2:]
    for i in range(len(htmlTable.columns)):
        tableHeader = htmlTable.columns[i]
        #html = html.replace(f"TableHeader_{str(i).zfill(2)}", tableHeader)
        
        tableValue = htmlTable.iloc[:,i][0]
        html = html.replace(f"TableData_{str(i).zfill(2)}", str(tableValue))

    coord0Dir = hvsr_results['input_params']['output_crs'].axis_info[0].direction

    # Figure out which coordinate axis is which (some CRS do Y, X)
    if coord0Dir.lower() in ['north', 'south']:
        xaxisinfo = hvsr_results['input_params']['output_crs'].axis_info[1]
        yaxisinfo = hvsr_results['input_params']['output_crs'].axis_info[0]
    else:
        xaxisinfo = hvsr_results['input_params']['output_crs'].axis_info[0]
        yaxisinfo = hvsr_results['input_params']['output_crs'].axis_info[1]

    # Get the axis name
    xaxis_name = xaxisinfo.name
    yaxis_name = yaxisinfo.name
    
    # Simplify the axis name
    if 'longitude' in xaxis_name.lower():
        xaxis_name = 'Longitude'
    if 'latitude' in yaxis_name.lower():
        yaxis_name = 'Latitude'
        
    
    html = html.replace("X_Coordinate", xaxis_name)
    html = html.replace("Y_Coordinate", yaxis_name)

    html = html.replace("Deg_E", xaxisinfo.unit_name)
    html = html.replace("Deg_N", yaxisinfo.unit_name)

    hvsr_results['HTML_Report'] = html
    # View in browser, if indicated to
    if show_html_report:
        try:
            _display_html_report(html)
        except Exception as e:
            print('\tHTML Report could not be displayed, but has been saved to the .HTML_Report attribute')
            print(e)

    return hvsr_results


# Private/Helper function to generate pdf report
def _generate_pdf_report(hvsr_results, pdf_report_filepath=None, show_pdf_report=False, show_html_report=False, return_pdf_path=False, verbose=False):
    """Private/helper function to generate pdf report from HTML report, intended to be used by get_report() function

    Parameters
    ----------
    hvsr_results : HVSRData or HVSRBatch
        Input dataset with all processing already carried out
    show_pdf_report : bool, optional
        EXPERIMENTAL: Whether to open the report after generating it, by default False
    show_html_report : bool, optional
        Whether to open the html report that the pdf report is based on, by default False
    verbose : bool, optional
        Whether to print verbose description of what the function is doing
    """
    from xhtml2pdf import pisa

    # Generate HTML Report if not already (this will be converted to pdf using xhtml2pdf)
    if not hasattr(hvsr_results, "HTML_Report"):
        hvsr_results = _generate_html_report(hvsr_results, show_html_report=show_html_report)
        if verbose:
            print('\tNo HTML Report previously generated, attempting now.')
        # try Code to generate HTML report from template

    htmlReport = hvsr_results['HTML_Report']

    if pdf_report_filepath is None:
        if verbose:
            print('\t pdf_report_filepath not specified, saving to temporary file.')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            pdf_export_path = temp_file.name  # Get the name of the temporary file

        # Now, open the file again for writing
        with open(pdf_export_path, 'wb') as temp_file:
            pisa_status = pisa.CreatePDF(htmlReport, dest=temp_file)

    else:
        if pathlib.Path(pdf_report_filepath).is_dir():
            fname = f"{hvsr_results['site']}_REPORT_{hvsr_results['hvsr_id']}_{datetime.date.today()}.pdf"
            pdf_report_filepath = pathlib.Path(pdf_report_filepath).joinpath(fname)
        
        try:        
            with open(pdf_report_filepath, "w+b") as export_file:
                pisa_status = pisa.CreatePDF(htmlReport, dest=export_file)
            pdf_export_path = pdf_report_filepath
            if verbose:
                print(f'PDF report saved to {pdf_export_path}')
        except Exception as e:
            print(f'PDF could not be saved to {pdf_report_filepath}')
            if verbose:
                print(f'\t{e}')
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                pdf_export_path = temp_file.name  # Get the name of the temporary file
            print(f'Saving pdf to temporary file instead: {temp_file.name}')
            # Now, open the file again for writing
            with open(pdf_export_path, 'wb') as temp_file:
                pisa_status = pisa.CreatePDF(htmlReport, dest=temp_file)

        
    if verbose:
        if not str(pisa_status.err) == '0':
            print('\t', pisa_status.err)

    if show_html_report:
        _display_html_report(hvsr_results['HTML_Report'])
        
    if show_pdf_report:
        if verbose:
            print(f'\tAttempting to open pdf at {pdf_export_path}')
        
        pdf_report_shown = False
        if hasattr(os, 'startfile'):
            try:
                os.startfile(pdf_export_path)
                pdf_report_shown = True
            except Exception as e:
                print(f"\tError opening pdf report: {e}")
        
        if not pdf_report_shown:
            try:
                import webbrowser
                webbrowser.open_new(pdf_export_path)
                pdf_report_shown = True
            except Exception as e:
                print(f"\tOpening pdf via webbrowser did not work, Error opening pdf report: {e}")

        if not pdf_report_shown:
            try:
                print(f"\tAttempting os.open()")
                os.open(pdf_export_path, flags=os.O_RDWR)
                pdf_report_shown = True            
            except Exception as e:
                print(f"\tError opening pdf report: {e}")

        if not pdf_report_shown:
            try:
                print("\tAttempting os.system")
                os.system(pdf_export_path)
                pdf_report_shown = True                
            except Exception as e:
                print(f"\tError opening pdf report: {e}")
                
        if not pdf_report_shown:
            print(f"\tSpRIT cannot open your pdf report, but it has been saved to {pdf_export_path}")
            print('\tAttempting to open HTML version of report')
        
            try:
                print('\tOpening via pdf did not work, opening HTML')
                _display_html_report(hvsr_results['HTML_Report'])
            except Exception as e:
                print('\tHTML Report could not be displayed, but has been saved to the .HTML_Report attribute')

    if return_pdf_path:
        return pdf_export_path

    return hvsr_results


# Plot hvsr curve, private supporting function for plot_hvsr
def _plot_hvsr(hvsr_data, plot_type, xtype='frequency', fig=None, ax=None, azimuth='HV', save_dir=None, save_suffix='', show_plot=True, **kwargs):
    """Private function for plotting hvsr curve (or curves with components)
    """
    
    # Get kwargs all straightened out
    if 'kwargs' in kwargs.keys():
        kwargs = kwargs['kwargs']

    if fig is None and ax is None:
        fig, ax = plt.subplots()

    if 'xlim' not in kwargs.keys():
        xlim = hvsr_data['hvsr_band']
    else:
        xlim = kwargs['xlim']
    
    if 'ylim' not in kwargs.keys():
        plotymax = max(hvsr_data.hvsrp2['HV']) + (max(hvsr_data.hvsrp2['HV']) - max(hvsr_data.hvsr_curve))
        if plotymax > hvsr_data.BestPeak['HV']['A0'] * 1.5:
            plotymax = hvsr_data.BestPeak['HV']['A0'] * 1.5
        ylim = [0, plotymax]
    else:
        ylim = kwargs['ylim']
    
    if 'grid' in kwargs.keys():
        plt.grid(which=kwargs['grid'], alpha=0.25)

    # Get x y data (for main hvsr plot esp.)
    hvsrDF = hvsr_data.hvsr_windows_df

    freqList = ['x_freqs', 'freqs', 'freq', 'hz', 'f', 'frequency']
    if xtype.lower() in freqList:
        xlabel = 'Frequency [Hz]'
    else:
        xlabel = 'Period [s]'

    if save_dir is not None:
        filename = hvsr_data['input_params']['site']
    else:
        filename = ""

    anyKey = list(hvsr_data[xtype].keys())[0]
    x = hvsr_data[xtype][anyKey][:-1]
    y = hvsr_data['hvsr_curve']
    
    # Set up plot viz and export
    plotSuff = ''
    legendLoc = 'upper left'
    
    # Plot HVSR curve first
    plotHVSR = False
    for item in plot_type:
        if item.lower()=='hvsr':
            plotHVSR = True
            ax.plot(x, y, color='k', label='H/V Ratio', zorder=1000)
            plotSuff = 'HVSRCurve_'
            if '-s' not in plot_type:
                ax.fill_between(x, hvsr_data['hvsrm2'][azimuth], hvsr_data['hvsrp2'][azimuth], color='k', alpha=0.2, label='StDev',zorder=997)
                ax.plot(x, hvsr_data['hvsrm2'][azimuth], color='k', alpha=0.25, linewidth=0.5, zorder=998)
                ax.plot(x, hvsr_data['hvsrp2'][azimuth], color='k', alpha=0.25, linewidth=0.5, zorder=999)
            else:
                plotSuff = plotSuff+'noStdDev_'
            break
    
    # Plot parameters
    ax.semilogx()
    ax.set_ylim(ylim)
    ax.set_xlim(xlim)
    ax.set_ylabel('H/V Ratio'+'\n['+hvsr_data['horizontal_method']+']', fontsize='small',)
    ax.tick_params(axis='x', labelsize=8)
    ax.tick_params(axis='y', labelsize=5)
    plt.suptitle(hvsr_data['input_params']['site'])

    if 'processing_parameters' in hvsr_data.keys() and 'generate_psds' in hvsr_data['processing_parameters'].keys():
        if hvsr_data['processing_parameters']['generate_psds']['obspy_ppsds']:
            compLabel = 'COMPONENTS\nAmplitude\n[m2/s4/Hz] [dB]'
        else:
            compLabel = 'COMPONENTS\n PSDs'

    # Get peak parameters (if exist, otherwise, get dummy ones)
    if "BestPeak" in hvsr_data.keys():
        f0 = hvsr_data['BestPeak'][azimuth]['f0']
        a0 = hvsr_data['BestPeak'][azimuth]['A0']
    else:
        f0 = hvsr_data['hvsr_band'][0]
        a0 = 0
    f0_div4 = f0/4
    f0_mult4 = f0*4
    a0_div2 = a0/2

    # Predefine so only need to set True if True
    peakAmpAnn = False
    peakPoint = False
    peakLine = False
    used = hvsrDF['Use'].astype(bool)
    notused = ~hvsrDF['Use'].astype(bool)     
    
    # Go through each "token" in plot_type str and plot as specified
    for k in plot_type:
        # Show peak(s)
        # Show f0 peak (and annotate if indicated)
        if k=='p' and 'all' not in plot_type:
            plotSuff=plotSuff+'BestPeak_'
            
            bestPeakScore = 0
            for i, p in enumerate(hvsr_data['PeakReport'][azimuth]):
                if p['Score'] > bestPeakScore:
                    bestPeakScore = p['Score']
                    bestPeak = p

            ax.axvline(bestPeak['f0'], color='k', linestyle='dotted', label='Peak')          
            
            # Annotate primary peak
            if 'ann' in plot_type:
                xLoc = bestPeak['f0']
                yLoc = ylim[0] + (ylim[1] - ylim[0]) * 0.008
                ax.text(x=xLoc, y=yLoc, s="Peak at "+str(round(bestPeak['f0'],2))+'Hz',
                            fontsize='xx-small', horizontalalignment='center', verticalalignment='bottom', 
                            bbox=dict(facecolor='w', edgecolor='none', alpha=0.8, pad=0.1))
                plotSuff = plotSuff+'ann_'  
        #Show all peaks in h/v curve
        elif k=='p'  and 'all' in plot_type:
            plotSuff = plotSuff+'allPeaks_'

            ax.vlines(hvsr_data['hvsr_peak_freqs'][azimuth], ax.get_ylim()[0], ax.get_ylim()[1], colors='k', linestyles='dotted', label='Peak')          

            # Annotate all peaks
            if 'ann' in plot_type:
                for i, p in enumerate(hvsr_data['hvsr_peak_freqs'][azimuth]):
                    y = hvsr_data['hvsr_curve'][hvsr_data['hvsr_peak_indices'][azimuth][i]]
                    ax.annotate('Peak at '+str(round(p,2))+'Hz', (p, 0.1), xycoords='data', 
                                    horizontalalignment='center', verticalalignment='bottom', 
                                    bbox=dict(facecolor='w', edgecolor='none', alpha=0.8, pad=0.1))
                plotSuff=plotSuff+'ann_'

        # Show primary peak amplitude (and annotate if indicated)
        if k=='pa':
            ax.hlines([a0], ax.get_xlim()[0], f0, linestyles='dashed')
            ax.scatter([f0], [a0], marker="o", facecolor='none', edgecolor='k')
            peakPoint = True
            peakLine = True
            
            # Annotate primary peak amplitude
            if 'ann' in plot_type:
                ax.annotate(f"Peak Amp.: {a0:.2f}", [f0+0.1*f0, a0])
                peakAmpAnn = True                

        # Show the curves and/or peaks at each time window
        if 't' in k and 'test' not in k:
            plotSuff = plotSuff+'allTWinCurves_'

            # If this is a component subplot
            if kwargs['subplot'] == 'comp':
                
                if k == 'tp':
                    pass  # This is not calculated for individual components
                if k == 't':
                    azKeys = ['Z', 'E', 'N']
                    azKeys.extend(list(hvsr_data.hvsr_az.keys()))
                    azColors = {'Z':'k', 'E':'b', 'N':'r'}
                    for az in azKeys:
                        if az.upper() in azColors.keys():
                            col = azColors[az]
                        else:
                            col = 'g'

                        for pv, t in enumerate(np.stack(hvsrDF[used]['psd_values_'+az])):
                            ax.plot(x, t[:-1], color=col, alpha=0.2, linewidth=0.8, linestyle=':', zorder=0)
            # For the main H/V plot
            else:
                # Show all peaks at all times (semitransparent red bars)
                if k == 'tp':
                    for j, t in enumerate(hvsrDF[used]['CurvesPeakIndices_'+azimuth]):
                        for i, v in enumerate(t):
                            v= x[v]
                            if i==0:
                                width = (x[i+1]-x[i])/16
                            else:
                                width = (x[i]-x[i-1])/16
                            if j == 0 and i==0:
                                ax.fill_betweenx(ylim,v-width,v+width, color='r', alpha=0.05, label='Individual H/V Peaks')
                            else:
                                ax.fill_betweenx(ylim,v-width,v+width, color='r', alpha=0.05)
                # Show curves at all time windows
                if k == 't':
                    if used.sum() > 0:
                        for t in np.stack(hvsrDF[used]['HV_Curves']):
                            ax.plot(x, t, color='k', alpha=0.25, linewidth=0.8, linestyle=':')
                    if notused.sum() > 0:
                        for t in np.stack(hvsrDF[notused]['HV_Curves']):
                            ax.plot(x, t, color='orangered', alpha=0.666, linewidth=0.8, linestyle=':', zorder=0)

        # Plot SESAME test results and thresholds on HVSR plot
        if 'test' in k and kwargs['subplot'] == 'hvsr':
            if k=='tests' or 'all' in k or ':' in k:
                # Change k to pass all test plot conditions
                k='test123456c'

            if '1' in k:
                # Peak is higher than 2x lowest point in f0/4-f0
                # Plot the line threshold that the curve needs to cross
                ax.plot([f0_div4, f0], [a0_div2, a0_div2],  color='tab:blue', marker='|', linestyle='dashed')
                
                # Get minimum of curve in desired range
                indexList=[]
                fList = []
                for i, f in enumerate(hvsr_data.x_freqs['Z']):
                    if f >= f0_div4 and f <= f0:
                        indexList.append(i)
                        fList.append(f)

                newCurveList= []
                newFreqList = []
                for ind in indexList:
                    if ind < len(hvsr_data.hvsr_curve):
                        newFreqList.append(hvsr_data.x_freqs['Z'][ind])
                        newCurveList.append(hvsr_data.hvsr_curve[ind])
                curveTestList = list(np.ones_like(newFreqList) * a0_div2)


                # Plot line showing where test succeeds or not
                if hvsr_data['BestPeak'][azimuth]['Report']['A(f-)'][-1] == sprit_utils._x_mark():
                    lowf2 = float(hvsr_data['BestPeak'][azimuth]['Report']['A(f-)'].replace('Hz', '').replace('-', '').split()[-3])
                    hif2 = float(hvsr_data['BestPeak'][azimuth]['Report']['A(f-)'].replace('Hz', '').replace('-', '').split()[-2])
                    ym = float(hvsr_data['BestPeak'][azimuth]['Report']['A(f-)'].replace('Hz', '').replace('-', '').split()[3])
                    yp = min(newCurveList)
                    ax.fill_betweenx(y=[ym, yp], x1=lowf2, x2=hif2, alpha=0.1, color='r')
                else:
                    #fpass = float(hvsr_data['BestPeak'][azimuth]['Report']['A(f-)'].replace('Hz', '').replace('-', '').split()[3])
                    #fpassAmp = float(hvsr_data['BestPeak'][azimuth]['Report']['A(f-)'].replace('Hz', '').replace('-', '').split()[5])
                    ax.fill_between(newFreqList, y1=newCurveList, y2=curveTestList, where=np.array(newCurveList)<=a0_div2, color='g', alpha=0.2)
                    minF = newFreqList[np.argmin(newCurveList)]
                    minA = min(newCurveList)
                    ax.plot([minF, minF, minF], [0, minA, a0_div2], marker='.', color='g', linestyle='dotted')

                # Plot the Peak Point if not already
                if not peakPoint:
                    ax.scatter([f0], [a0], marker="o", facecolor='none', edgecolor='k')
                    peakPoint=True

                # Annotate the Peak Amplitude if not already
                if not peakAmpAnn and 'ann' in plot_type:
                    ax.annotate(f"Peak Amp.: {a0:.2f}", [f0+0.1*f0, a0])
                    peakAmpAnn=True

                # Add peak line
                if 'pa' not in plot_type and not peakLine:
                    ax.hlines([a0], ax.get_xlim()[0], f0, linestyles='dashed')
                    peakLine = True  
            if '2' in k:
                # Peak is higher than 2x lowest point in f0-f0*4

                # Plot the line threshold that the curve needs to cross
                ax.plot([f0, f0_mult4], [a0_div2, a0_div2],  color='tab:blue', marker='|', linestyle='dashed')

                
                # Get minimum of curve in desired range
                indexList=[]
                fList = []
                for i, f in enumerate(hvsr_data.x_freqs['Z']):
                    if f >= f0 and f <= f0_mult4:
                        indexList.append(i)
                        fList.append(f)

                newCurveList= []
                newFreqList = []
                for ind in indexList:
                    if ind < len(hvsr_data.hvsr_curve):
                        newFreqList.append(hvsr_data.x_freqs['Z'][ind])
                        newCurveList.append(hvsr_data.hvsr_curve[ind])
                curveTestList = list(np.ones_like(newFreqList) * a0_div2)

                if hvsr_data['BestPeak'][azimuth]['Report']['A(f+)'][-1] == sprit_utils._x_mark():
                    lowf2 = float(hvsr_data['BestPeak'][azimuth]['Report']['A(f+)'].replace('Hz', '').replace('-', '').split()[-3])
                    hif2 = float(hvsr_data['BestPeak'][azimuth]['Report']['A(f+)'].replace('Hz', '').replace('-', '').split()[-2])
                    ym = float(hvsr_data['BestPeak'][azimuth]['Report']['A(f+)'].replace('Hz', '').replace('-', '').split()[3])
                    yp = min(newCurveList)
                    ax.fill_betweenx(y=[ym, yp], x1=lowf2, x2=hif2, alpha=0.1, color='r')
                else:
                    #fpass = float(hvsr_data['BestPeak'][azimuth]['Report']['A(f+)'].replace('Hz', '').replace('-', '').split()[3])
                    #fpassAmp = float(hvsr_data['BestPeak'][azimuth]['Report']['A(f+)'].replace('Hz', '').replace('-', '').split()[5])
                    ax.fill_between(newFreqList, y1=newCurveList, y2=curveTestList, where=np.array(newCurveList)<=a0_div2, color='g', alpha=0.2)
                    minF = newFreqList[np.argmin(newCurveList)]
                    minA = min(newCurveList)
                    ax.plot([minF, minF, minF], [0, minA, a0_div2], marker='.', color='g', linestyle='dotted')

                # Plot the Peak Point if not already
                if not peakPoint:
                    ax.scatter([f0], [a0], marker="o", facecolor='none', edgecolor='k')
                    peakPoint=True
                
                # Annotate the amplitude of peak point if not already
                if not peakAmpAnn and 'ann' in plot_type:
                    ax.annotate(f"Peak Amp.: {a0:.2f}", [f0+0.1*f0, a0])
                    peakAmpAnn=True
                
                if 'pa' not in plot_type and not peakLine:
                    ax.hlines([a0], ax.get_xlim()[0], f0, linestyles='dashed')
                    peakLine = True
            if '3' in k:
                if 'c' in k:
                    #Plot curve test3
                    lowfc3 = hvsr_data['BestPeak'][azimuth]['Report']['σ_A(f)'].split(' ')[4].split('-')[0]
                    hifc3 = hvsr_data['BestPeak'][azimuth]['Report']['σ_A(f)'].split(' ')[4].split('-')[1].replace('Hz', '')
                    pass # May not even finish this
                
                lcolor='r'
                if f0 > 2:
                    lcolor='g'

                if 'c' not in k or all(num in k for num in ["1", "2", "3", "4", "5", "6"]):
                    ax.hlines([2], ax.get_xlim()[0], ax.get_xlim()[1], color='tab:blue', linestyles='dashed')
                    ax.plot([f0, f0], [2, a0], linestyle='dotted', color=lcolor)

                    if 'pa' not in plot_type:
                        ax.hlines([a0], ax.get_xlim()[0], f0, linestyles='dashed')
                        ax.scatter([f0], [a0], marker="o", facecolor='none', edgecolor='k')
                        peakPoint = True
                        peakLine = True
            if '4' in k:
                lowf4 = float(hvsr_data['BestPeak'][azimuth]['Report']['P-'].split(' ')[0])
                hif4 = float(hvsr_data['BestPeak'][azimuth]['Report']['P+'].split(' ')[0])
                m2Max = hvsr_data.x_freqs["Z"][np.argmax(hvsr_data.hvsrm2)]#, np.max(hvsr_data.hvsrm2))
                p2Max = hvsr_data.x_freqs["Z"][np.argmax(hvsr_data.hvsrp2)]#, np.max(hvsr_data.hvsrp2))

                # ax.vlines([f0*0.95, f0*1.05], [0,0], [ax.get_xlim()[1],ax.get_xlim()[1]])
                ax.fill_betweenx(np.linspace(0, ax.get_xlim()[1]), x1=f0*0.95, x2=f0*1.05, color='tab:blue', alpha=0.3)
                
                mcolor = 'r'
                pcolor = 'r'
                if hvsr_data['BestPeak'][azimuth]['Report']['P-'][-1] == sprit_utils._check_mark():
                    mcolor='g'
                if hvsr_data['BestPeak'][azimuth]['Report']['P+'][-1] == sprit_utils._check_mark():
                    pcolor='g'

                print(lowf4, hif4)

                ax.scatter([lowf4, hif4], [np.max(hvsr_data.hvsrm2[azimuth]),  np.max(hvsr_data.hvsrp2[azimuth])], c=[mcolor, pcolor], marker='x')
                
                if not peakPoint:
                    ax.scatter([f0], [a0], marker="o", facecolor='none', edgecolor='k')
                    peakPoint = True
            if '5' in k:
                sf = float(hvsr_data['BestPeak'][azimuth]['Report']['Sf'].split(' ')[4].strip('()'))
                sfp = f0+sf
                sfm = f0-sf

                sfLim = float(hvsr_data['BestPeak'][azimuth]['Report']['Sf'].split(' ')[-2])
                sfLimp = f0+sfLim
                sfLimm = f0-sfLim

                if hvsr_data['BestPeak'][azimuth]['Report']['Sf'][-1] == sprit_utils._check_mark():
                    xColor = 'g'
                else:
                    xColor='r'

                ax.scatter([sfLimm, sfLimp], [a0, a0], marker='|', c='tab:blue')
                ax.scatter([sfm, sfp], [a0, a0], marker='x', c=xColor)
                ax.plot([sfLimm, sfLimp], [a0, a0], color='tab:blue')
                if not peakPoint:
                    ax.scatter([f0], [a0], marker="o", facecolor='none', edgecolor='k')
                    peakPoint = True
            if '6' in k:
                sa = float(hvsr_data['BestPeak'][azimuth]['Report']['Sa'].split(' ')[4].strip('()'))
                sap = a0+sa
                sam = a0-sa

                saLim = float(hvsr_data['BestPeak'][azimuth]['Report']['Sa'].split(' ')[-2])
                saLimp = a0+saLim
                saLimm = a0-saLim

                if hvsr_data['BestPeak'][azimuth]['Report']['Sa'][-1] == sprit_utils._check_mark():
                    xColor = 'g'
                else:
                    xColor='r'

                ax.scatter([f0, f0], [saLimm, saLimp], marker='_', c='tab:blue')
                ax.scatter([f0, f0],[sam, sap], marker='x', c=xColor)
                ax.plot([f0, f0],[saLimm, saLimp], color='tab:blue')                
                if not peakPoint:
                    ax.scatter([f0], [a0], marker="o", facecolor='none', edgecolor='k')
                    peakPoint = True
        
        # Plot frequency search range bars
        if 'fr' in k:
            lowPeakSearchThresh = hvsr_data.peak_freq_range[0]
            hiPeakSearchThresh = hvsr_data.peak_freq_range[1]
            
            frStyleDict = {'linestyle':'dashed', 'facecolors':'#1B060544', 'edgecolors':'#000000'}

            ax.fill_betweenx(ylim, [xlim[0], xlim[0]],[lowPeakSearchThresh,lowPeakSearchThresh], **frStyleDict)          
            ax.fill_betweenx(ylim, [hiPeakSearchThresh, hiPeakSearchThresh],[xlim[1],xlim[1]], **frStyleDict)          

        # Plot individual components
        if 'c' in k and 'test' not in k: #Spectrogram uses a different function, so c is unique to the component plot flag
            plotSuff = plotSuff+'IndComponents_'
            
            if 'c' not in plot_type[0]:
                #This section is if comps plotted in hvsr axis
                
                compAxis = ax.twinx()
                plt.sca(compAxis)
                #axis2 = plt.gca()
                #fig = plt.gcf()
                compAxis.set_ylabel(compLabel, rotation=270, labelpad=20)
                #plt.sca(compAxis)
                #plt.ylabel(compLabel, rotate=180)
                compAxis.set_facecolor([0,0,0,0])
                legendLoc2 = 'upper right'
            else:
                # This section is for if they are plotted on different plots
                ax.set_title('') #Remove title
                ax.sharex(kwargs['axes']['hvsr'])
                compAxis = ax
                legendLoc2 = 'upper right'
                compAxis.set_ylabel(compLabel)
                
            minY = []
            maxY = []
            keyList = ['Z', 'E', 'N']
            for az in hvsr_data.hvsr_az.keys():
                keyList.append(az)
            keyList.sort()
            hvsrDF = hvsr_data.hvsr_windows_df
            for key in keyList:
                #hvsr_data['ppsds'][key]['psd_values']                
                minY.append(hvsr_data['ppsd_std_vals_m'][key].min())
                maxY.append(hvsr_data['ppsd_std_vals_p'][key].max())
                #minY.append(np.min(np.stack(hvsrDF['psd_values_'+key][hvsrDF['Use']])))
                #maxY.append(np.max(np.stack(hvsrDF['psd_values_'+key][hvsrDF['Use']])))
            minY = min(minY)
            maxY = max(maxY)
            #if maxY > 20:
            #    maxY = max(hvsr_data['hvsr_curve']) * 1.15
            rng = maxY-minY
            pad = abs(rng * 0.15)
            ylim = [float(minY-pad), float(maxY+pad+pad)]

            compAxis.set_ylim(ylim)
            yLoc = min(ylim) - abs(ylim[1]-ylim[0]) * 0.05
            xlab = ax.text(x=xlim[0], y=yLoc, s=xlabel, 
                        fontsize='x-small', horizontalalignment='right', verticalalignment='top', 
                        bbox=dict(facecolor='w', edgecolor='none', alpha=0.8, pad=0.1))
            xlab.set_in_layout(False)
            #Modify based on whether there are multiple charts
            if plotHVSR:
                linalpha = 0.2
                stdalpha = 0.05
            else:
                linalpha=1
                stdalpha=0.2
            
            #Plot individual components
            azsLabeled = False
            y={}
            psdKeys = list(hvsr_data['psd_values_tavg'])
            psdKeys.sort()  # Put Z last so it plots on top
            for key in psdKeys:
                if key.upper() == 'Z':
                    pltColor = 'k'
                elif key.upper() =='E':
                    pltColor = 'b'
                elif key.upper() == 'N':
                    pltColor = 'r'
                else:
                    pltColor = 'g'

                if key in keyList or key == azimuth:
                    if hvsr_data.horizontal_method == 'Single Azimuth' and key in ['E', 'N']:
                        pass
                    else:
                        y[key] = hvsr_data['psd_values_tavg'][key][:-1]
                        # Make sure azimuth only shows up in legend once
                        if pltColor == 'g':
                            if azsLabeled:
                                leglabel = None
                            else:
                                leglabel = 'Azimuths'    
                            azsLabeled = True
                        else:
                            leglabel = key

                        compAxis.plot(x, y[key], c=pltColor, label=leglabel, alpha=linalpha)
                        if '-s' not in plot_type:
                            compAxis.fill_between(x, hvsr_data['ppsd_std_vals_m'][key][:-1], hvsr_data['ppsd_std_vals_p'][key][:-1], color=pltColor, alpha=stdalpha)

                if 'c' not in plot_type[0].lower():
                    if not kwargs['show_legend'] == False:
                        compAxis.legend(loc=legendLoc2)
            else:
                ax.legend(loc=legendLoc, ncols = len(psdKeys), 
                        borderaxespad=0.1, columnspacing=1,markerfirst=False, reverse=True, borderpad=0.2)
        else:
            yLoc = min(ylim) - abs(ylim[1]-ylim[0]) * 0.05
            ax.text(x=xlim[0], y=yLoc, s=xlabel, 
                fontsize='x-small', horizontalalignment='right', verticalalignment='top', 
                bbox=dict(facecolor='w', edgecolor='none', alpha=0.8, pad=0.1))
    
    bbox = ax.get_window_extent()
    bboxStart = bbox.__str__().find('Bbox(',0,50)+5
    bboxStr = bbox.__str__()[bboxStart:].split(',')[:4]
    axisbox = []
    for i in bboxStr:
        i = i.split('=')[1]
        if ')' in i:
            i = i[:-1]
        axisbox.append(float(i))

    if kwargs['show_legend']:
        ax.legend(loc=legendLoc,bbox_to_anchor=(1.05, 1))

    __plot_current_fig(save_dir=save_dir, 
                        filename=filename, 
                        fig=fig, ax=ax,
                        plot_suffix=plotSuff, 
                        user_suffix=save_suffix, 
                        show_plot=show_plot)
    
    return fig, ax


# Private function to help for when to show and format and save plots
def __plot_current_fig(save_dir, filename, fig, ax, plot_suffix, user_suffix, show_plot):
    """Private function to support plot_hvsr, for plotting and showing plots"""
    #plt.gca()
    #plt.gcf()
    #fig.tight_layout() #May need to uncomment this

    #plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)

    if save_dir is not None:
        outFile = save_dir+'/'+filename+'_'+plot_suffix+str(datetime.datetime.today().date())+'_'+user_suffix+'.png'
        fig.savefig(outFile, bbox_inches='tight', pad_inches=0.2)
    if show_plot:
        fig.canvas.draw()#.show()
        #fig.tight_layout()
        #plt.ion()
    return


# Plot specgtrogram, private supporting function for plot_hvsr
def _plot_specgram_hvsr(hvsr_data, fig=None, ax=None, azimuth='HV', save_dir=None, save_suffix='',**kwargs):
    """Private function for plotting average spectrogram of all three channels from ppsds
    """
    # Get all input parameters
    if fig is None and ax is None:
        fig, ax = plt.subplots()    

    if 'kwargs' in kwargs.keys():
        kwargs = kwargs['kwargs']

    if 'spec' in kwargs.keys():
        del kwargs['spec']

    if 'p' in kwargs.keys():
        peak_plot=True
        del kwargs['p']
    else:
        peak_plot=False

    if 'ann' in kwargs.keys():
        annotate=True
        del kwargs['ann']
    else:
        annotate=False

    if 'all' in kwargs.keys():
        show_all_peaks = True
        del kwargs['all']
    else:
        show_all_peaks = False

    if 'tp' in kwargs.keys():
        show_all_time_peaks = True
        del kwargs['tp']
    else:
        show_all_time_peaks = False

    if 'grid' in kwargs.keys():
        ax.grid(which=kwargs['grid'], alpha=0.25)
        del kwargs['grid']
        
    if 'ytype' in kwargs:
        if kwargs['ytype']=='freq':
            ylabel = 'Frequency [Hz]'
            del kwargs['ytype']
        else:
            ylabel = 'Period [s]'
        del kwargs['ytype']
    else:
        ylabel='Frequency [Hz]'
        
    if 'detrend' in kwargs.keys():
        detrend= kwargs['detrend']
        del kwargs['detrend']
    else:
        detrend=True

    if 'colorbar' in kwargs.keys():
        colorbar = kwargs['colorbar']
        del kwargs['colorbar']
    else:
        colorbar=True

    if 'cmap' in kwargs.keys():
        pass
    else:
        kwargs['cmap'] = 'turbo'

    hvsrDF = hvsr_data['hvsr_windows_df']
    used = hvsrDF['Use'].astype(bool)
    notused = ~hvsrDF['Use'].astype(bool)     

    # Setup
    ppsds = hvsr_data['ppsds']#[k]['current_times_used']
    import matplotlib.dates as mdates
    anyKey = list(ppsds.keys())[0]
    
    # Get data
    hvCurveColumn = 'HV_Curves'
    if azimuth != 'HV':
        hvCurveColumn += '_'+azimuth
    
    psdArr = np.stack(hvsrDF[hvCurveColumn].apply(np.flip))
    useArr = np.array(hvsrDF['Use'])
    useArr = np.tile(useArr, (psdArr.shape[1], 1)).astype(int)
    useArr = np.clip(useArr, a_min=0.15, a_max=1)

    # Get times
    xmin = hvsrDF['TimesProcessed_MPL'].min()
    xmax = hvsrDF['TimesProcessed_MPL'].max()

    #Format times
    tTicks = mdates.MinuteLocator(byminute=range(0,60,5))
    ax.xaxis.set_major_locator(tTicks)
    tTicks_minor = mdates.SecondLocator(bysecond=[0])
    ax.xaxis.set_minor_locator(tTicks_minor)

    tLabels = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(tLabels)
    ax.tick_params(axis='both', labelsize='x-small')

    #Get day label for bottom of chart
    if hvsrDF.index[0].date() != hvsrDF.index[-1].date():
        day = str(hvsr_data['hvsr_windows_df'].index[0].date())+' - '+str(hvsr_data['hvsr_windows_df'].index[-1].date())
    else:
        day = str(hvsr_data['hvsr_windows_df'].index[0].date())

    #Get extents
    ymin = hvsr_data['input_params']['hvsr_band'][0]
    ymax = hvsr_data['input_params']['hvsr_band'][1]

    freqticks = np.flip(hvsr_data['x_freqs'][anyKey])
    yminind = np.argmin(np.abs(ymin-freqticks))
    ymaxind = np.argmin(np.abs(ymax-freqticks))
    freqticks = freqticks[yminind:ymaxind]
    freqticks = np.logspace(np.log10(freqticks[0]), np.log10(freqticks[-1]), num=psdArr.shape[1])

    extList = [xmin, xmax, ymin, ymax]
    #Set up axes
    ax.set_facecolor([0,0,0]) #Create black background for transparency to look darker

    # Interpolate into linear
    new_indices = np.linspace(freqticks[0], freqticks[-1], len(freqticks))
    linList = []
    for row in psdArr:
        row = row.astype(np.float16)
        linList.append(np.interp(new_indices, freqticks, row))
    linear_arr = np.stack(linList)

    # Create chart
    if 'subplot' in kwargs.keys():
        del kwargs['subplot']
    
    # Get min and max of colormap normalization from array that is used
    if 'vmin' not in kwargs.keys():
        kwargs['vmin'] = np.min(np.stack(hvsrDF[used]['HV_Curves']))
    if 'vmax' not in kwargs.keys():
        kwargs['vmax'] = np.max(np.stack(hvsrDF[used]['HV_Curves']))

    im = ax.imshow(linear_arr.T, origin='lower', extent=extList, aspect='auto', alpha=useArr, **kwargs)
    ax.tick_params(left=True, right=True, top=True)

    if peak_plot:
        ax.axhline(hvsr_data['BestPeak'][azimuth]['f0'], c='k',  linestyle='dotted', zorder=1000)

    if annotate:
        if float(hvsr_data['BestPeak'][azimuth]['f0']) < 1:
            boxYPerc = 0.998
            vertAlign = 'top'
        else:
            boxYPerc = 0.002
            vertAlign = 'bottom'
        xLocation = float(xmin) + (float(xmax)-float(xmin))*0.99
        yLocation = hvsr_data['input_params']['hvsr_band'][0] + (hvsr_data['input_params']['hvsr_band'][1]-hvsr_data['input_params']['hvsr_band'][0])*(boxYPerc)
        ann = ax.text(x=xLocation, y=yLocation, fontsize='x-small', s=f"Peak at {hvsr_data['BestPeak'][azimuth]['f0']:0.2f} Hz", ha='right', va=vertAlign, 
                      bbox={'alpha':0.8, 'edgecolor':None, 'linewidth':0, 'fc':'w', 'pad':0.3})

    if show_all_time_peaks:
        timeVals = []
        peakFreqs = []
        for tIndex, pFreqs in enumerate(hvsrDF[used]['CurvesPeakFreqs_'+azimuth]):
            endWindow = hvsrDF.iloc[tIndex]['TimesProcessed_MPLEnd']
            startWindow = hvsrDF.iloc[tIndex]['TimesProcessed_MPL']
            midTime = (endWindow + startWindow) / 2
            for f in pFreqs:
                timeVals.append(midTime)
                peakFreqs.append(f)
        ax.scatter(timeVals, peakFreqs, marker="^", facecolors='#00000000', edgecolors='#00000088',s=12)

    if show_all_peaks:
        ax.hlines(hvsr_data['hvsr_peak_freqs'][azimuth], ax.get_xlim()[0], ax.get_xlim()[1], colors='gray', alpha=0.666, linestyles='dotted', zorder=999)

    xLoc = xmin + (xmax - xmin) * 0.001
    yLoc = ymin + (ymax - ymin) * 0.97
    ax.text(x=xLoc, y=yLoc, s=day,
                fontsize='small', horizontalalignment='left', verticalalignment='top', 
                bbox=dict(facecolor='w', edgecolor=None, linewidth=0, alpha=0.8, pad=0.2))

    if colorbar:
        cbar = plt.colorbar(mappable=im, orientation='horizontal')
        cbar.set_label('H/V Ratio')

    #Set x and y labels
    yLoc = ymin - (ymin * 2.5e-1)
    ax.text(x=xmin, y=yLoc,s="UTC Time", 
                fontsize='x-small', horizontalalignment='right', verticalalignment='top', 
                bbox=dict(facecolor='w', edgecolor='none', alpha=0.8, pad=0.1))
    ax.set_ylabel(ylabel, fontsize='x-small')
    ax.set_yscale('log')

    #plt.sca(ax)
    #plt.rcParams['figure.dpi'] = 500
    #plt.rcParams['figure.figsize'] = (12,4)
    fig.canvas.draw()

    return fig, ax


# HELPER functions for checking peaks
# Initialize peaks
def __init_peaks(_x, _y, _index_list, _hvsr_band, peak_freq_range=DEFAULT_BAND, _min_peak_amp=0):
    """ Initialize peaks.
        
        Creates dictionary with relevant information and removes peaks in hvsr curve that are not relevant for data analysis (outside HVSR_band)

        Parameters
        ----------
        x : list-like obj 
            List with x-values (frequency or period values)
        y : list-like obj 
            List with hvsr curve values
        index_list : list or array_like 
            List with indices of peaks
        _hvsr_band : list
            Two-item list with low and high frequency to limit frequency range of data analysis extent
        peak_freq_range : list
            Two-item list with low and high frequency to limit frequency range for checking for peaks
        _min_peak_amp : float
            Minimum amplitude to be used for peak selection (to limit number of meaningless peaks found)

        Returns
        -------
        _peak               : list 
            List of dictionaries, one for each input peak
    """

    _peak = list()
    for _i in _index_list:
        if (_hvsr_band[0] <= _x[_i] <= _hvsr_band[1]) and (peak_freq_range[0] <= _x[_i] <= peak_freq_range[1]) and (_y[_i]>_min_peak_amp):
            _peak.append({'f0': float(_x[_i]), 'A0': float(_y[_i]), 
                          'f-': None, 'f+': None, 'Sf': None, 'Sa': None,
                          'Score': 0, 
                          'Report': {'Lw':'', 'Nc':'', 'σ_A(f)':'', 'A(f-)':'', 'A(f+)':'', 'A0': '', 'P+': '', 'P-': '', 'Sf': '', 'Sa': ''},
                          'PassList':{},
                          'PeakPasses':False})
    return _peak


# Check reliability of HVSR of curve
def __check_curve_reliability(hvsr_data, _peak, col_id='HV'):
    """Tests to check for reliable H/V curve

    Tests include:
        1) Peak frequency is greater than 10 / window length (f0 > 10 / Lw)
            f0 = peak frequency [Hz]
            Lw = window length [seconds]
        2) Number of significant cycles (Nc) is greater than 200 (Nc(f0) > 200)
                Nc = Lw * Nw * f0
                Lw = window length [sec]
                Nw = Number of windows used in analysis
                f0 = peak frequency [Hz]
        3) StDev of amplitude of H/V curve is less than 2 at all frequencies between 0.5f0 and 2f0
            (less than 3 if f0 is less than 0.5 Hz)
            f0 = peak frequency [Hz]
            StDev is a measure of the variation of all the H/V curves generated for each time window
                Our main H/V curve is the median of these

    Parameters
    ----------
    hvsr_data   : dict
        Dictionary containing all important information generated about HVSR curve
    _peak       : list
        A list of dictionaries, with each dictionary containing information about each peak

    Returns
    -------
    _peak   : list
        List of dictionaries, same as above, except with information about curve reliability tests added
    """
    anyKey = list(hvsr_data['ppsds'].keys())[0]#Doesn't matter which channel we use as key

    delta = hvsr_data['ppsds'][anyKey]['delta']
    window_len = hvsr_data['ppsds'][anyKey]['ppsd_length'] #Window length in seconds
    window_num = np.array(hvsr_data['psd_raw'][anyKey]).shape[0]

    for _i in range(len(_peak)):
        # Test 1
        peakFreq= _peak[_i]['f0']
        test1 = peakFreq > 10/window_len

        nc = window_len * window_num * peakFreq
        test2 = nc > 200

        halfF0 = peakFreq/2
        doublef0 = peakFreq*2
        

        test3 = True
        failCount = 0
        for i, freq in enumerate(hvsr_data['x_freqs'][anyKey][:-1]):
            if freq >= halfF0 and freq <doublef0:
                compVal = 2
                if peakFreq >= 0.5:
                    if hvsr_data['hvsr_log_std'][col_id][i] >= compVal:
                        test3=False
                        failCount +=1

                else: #if peak freq is less than 0.5
                    compVal = 3
                    if hvsr_data['hvsr_log_std'][col_id][i] >= compVal:
                        test3=False
                        failCount +=1

        if test1:
            _peak[_i]['Report']['Lw'] = f'{round(peakFreq,3)} > {10/int(window_len):0.3} (10 / {int(window_len)})  {sprit_utils._check_mark()}'
        else:
            _peak[_i]['Report']['Lw'] = f'{round(peakFreq,3)} > {10/int(window_len):0.3} (10 / {int(window_len)})  {sprit_utils._x_mark()}'

        if test2:
            _peak[_i]['Report']['Nc'] = f'{int(nc)} > 200  {sprit_utils._check_mark()}'
        else:
            _peak[_i]['Report']['Nc'] = f'{int(nc)} > 200  {sprit_utils._x_mark()}'

        if test3:
            _peak[_i]['Report']['σ_A(f)'] = f'H/V Amp. St.Dev. for {peakFreq*0.5:0.3f}-{peakFreq*2:0.3f}Hz < {compVal}  {sprit_utils._check_mark()}'
        else:
            _peak[_i]['Report']['σ_A(f)'] = f'H/V Amp. St.Dev. for {peakFreq*0.5:0.3f}-{peakFreq*2:0.3f}Hz < {compVal}  {sprit_utils._x_mark()}'

        _peak[_i]['PassList']['WinLen'] = test1
        _peak[_i]['PassList']['SigCycles'] = test2
        _peak[_i]['PassList']['LowCurveStD'] = test3
    return _peak


# Check clarity of peaks
def __check_clarity(_x, _y, _peak, do_rank=True):
    """Check clarity of peak amplitude(s)

       Test peaks for satisfying amplitude clarity conditions as outlined by SESAME 2004:
           - there exist one frequency f-, lying between f0/4 and f0, such that A0 / A(f-) > 2
           - there exist one frequency f+, lying between f0 and 4*f0, such that A0 / A(f+) > 2
           - A0 > 2

        Parameters
        ----------
        x : list-like obj 
            List with x-values (frequency or period values)
        y : list-like obj 
            List with hvsr curve values
        _peak : list
            List with dictionaries for each peak, containing info about that peak
        do_rank : bool, default=False
            Include Rank in output

        Returns
        -------
        _peak : list
            List of dictionaries, each containing the clarity test information for the different peaks that were read in
    """
    global max_rank

    # Test each _peak for clarity.
    if do_rank:
        max_rank += 1

    if np.array(_x).shape[0] == 1000:
        jstart = len(_y)-2
    else:
        jstart = len(_y)-1

    
    for _i in range(len(_peak)):
        #Initialize as False
        _peak[_i]['f-'] = sprit_utils._x_mark()
        _peak[_i]['Report']['A(f-)'] = f"H/V curve > {_peak[_i]['A0']/2:0.2f} for all {_peak[_i]['f0']/4:0.2f} Hz-{_peak[_i]['f0']:0.3f} Hz {sprit_utils._x_mark()}"
        _peak[_i]['PassList']['ProminenceLow'] = False #Start with assumption that it is False until we find an instance where it is True
        for _j in range(jstart, -1, -1):
            # There exist one frequency f-, lying between f0/4 and f0, such that A0 / A(f-) > 2.
            if (float(_peak[_i]['f0']) / 4.0 <= _x[_j] < float(_peak[_i]['f0'])) and float(_peak[_i]['A0']) / _y[_j] > 2.0:
                _peak[_i]['Score'] += 1
                _peak[_i]['f-'] = '%10.3f %1s' % (_x[_j], sprit_utils._check_mark())
                _peak[_i]['Report']['A(f-)'] = f"Amp. of H/V Curve @{_x[_j]:0.3f}Hz ({_y[_j]:0.3f}) < {_peak[_i]['A0']/2:0.3f} {sprit_utils._check_mark()}"
                _peak[_i]['PassList']['ProminenceLow'] = True
                break
            else:
                pass
    
    if do_rank:
        max_rank += 1
    for _i in range(len(_peak)):
        #Initialize as False
        _peak[_i]['f+'] = sprit_utils._x_mark()
        _peak[_i]['Report']['A(f+)'] = f"H/V curve > {_peak[_i]['A0']/2:0.2f} for all {_peak[_i]['f0']:0.2f} Hz-{_peak[_i]['f0']*4:0.3f} Hz {sprit_utils._x_mark()}"
        _peak[_i]['PassList']['ProminenceHi'] = False
        for _j in range(len(_x) - 1):

            # There exist one frequency f+, lying between f0 and 4*f0, such that A0 / A(f+) > 2.
            if float(_peak[_i]['f0']) * 4.0 >= _x[_j] > float(_peak[_i]['f0']) and \
                    float(_peak[_i]['A0']) / _y[_j] > 2.0:
                _peak[_i]['Score'] += 1
                _peak[_i]['f+'] = f"{_x[_j]:0.3f} {sprit_utils._check_mark()}"
                _peak[_i]['Report']['A(f+)'] = f"H/V Curve at {_x[_j]:0.2f} Hz: {_y[_j]:0.2f} < {_peak[_i]['A0']/2:0.2f} (f0/2) {sprit_utils._check_mark()}"
                _peak[_i]['PassList']['ProminenceHi'] = True
                break
            else:
                pass

    # Amplitude Clarity test
    # Only peaks with A0 > 2 pass
    if do_rank:
        max_rank += 1
    _a0 = 2.0
    for _i in range(len(_peak)):

        if float(_peak[_i]['A0']) > _a0:
            _peak[_i]['Report']['A0'] = f"Amplitude of peak ({_peak[_i]['A0']:0.2f}) > {int(_a0)} {sprit_utils._check_mark()}"
            _peak[_i]['Score'] += 1
            _peak[_i]['PassList']['AmpClarity'] = True
        else:
            _peak[_i]['Report']['A0'] = '%0.2f > %0.1f %1s' % (_peak[_i]['A0'], _a0, sprit_utils._x_mark())
            _peak[_i]['PassList']['AmpClarity'] = False

    return _peak


# Check the stability of the frequency peak
def __check_freq_stability(_peak, _peakm, _peakp):
    """Test peaks for satisfying stability conditions

    Test as outlined by SESAME 2004:
        - the _peak should appear at the same frequency (within a percentage ± 5%) on the H/V
            curves corresponding to mean + and - one standard deviation.

    Parameters
    ----------
    _peak : list
        List of dictionaries containing input information about peak, without freq stability test
    _peakm : list
        List of dictionaries containing input information about peakm (peak minus one StDev in freq)
    _peakp : list
        List of dictionaries containing input information about peak (peak plus one StDev in freq)

    Returns
    -------
    _peak : list
        List of dictionaries containing output information about peak test
    """
    global max_rank

    # check σf and σA
    max_rank += 1

    # First check below
    # Initialize list
    _found_m = list()

    for _i in range(len(_peak)):
        _dx = 1000000.
        # Initialize test as not passing for this frequency
        _found_m.append(False)
        _peak[_i]['Report']['P-'] = sprit_utils._x_mark()
        # Iterate through all time windows
        for _j in range(len(_peakm)):
            if abs(_peakm[_j]['f0'] - _peak[_i]['f0']) < _dx:
                _index = _j
                _dx = abs(_peakm[_j]['f0'] - _peak[_i]['f0']) #_dx is difference between peak frequencies for each time window and main peak
            if _peak[_i]['f0'] * 0.95 <= _peakm[_j]['f0'] <= _peak[_i]['f0'] * 1.05:
                _peak[_i]['Report']['P-'] = f"{_peakm[_j]['f0']:0.2f} Hz within ±5% of {_peak[_i]['f0']:0.2f} Hz {sprit_utils._check_mark()}"
                _found_m[_i] = True
                break
        
        if _peak[_i]['Report']['P-'] == sprit_utils._x_mark():
            _peak[_i]['Report']['P-'] = f"{_peakm[_j]['f0']:0.2f} Hz within ±5% of {_peak[_i]['f0']:0.2f} Hz {sprit_utils._x_mark()}"

    # Then Check above
    _found_p = list()
    for _i in range(len(_peak)):
        _dx = 1000000.
        _found_p.append(False)
        _peak[_i]['Report']['P+'] = sprit_utils._x_mark()
        for _j in range(len(_peakp)):
            if abs(_peakp[_j]['f0'] - _peak[_i]['f0']) < _dx:

                _dx = abs(_peakp[_j]['f0'] - _peak[_i]['f0'])
            if _peak[_i]['f0'] * 0.95 <= _peakp[_j]['f0'] <= _peak[_i]['f0'] * 1.05:
                if _found_m[_i]:
                    _peak[_i]['Report']['P+'] = f"{_peakp[_j]['f0']:0.2f} Hz within ±5% of {_peak[_i]['f0']:0.2f} Hz {sprit_utils._check_mark()}"
                    _peak[_i]['Score'] += 1
                    _peak[_i]['PassList']['FreqStability'] = True
                else:
                    _peak[_i]['Report']['P+'] = f"{_peakp[_j]['f0']:0.2f} Hz within ±5% of {_peak[_i]['f0']:0.2f} Hz {sprit_utils._x_mark()}"
                    _peak[_i]['PassList']['FreqStability'] = False
                break
            else:
                _peak[_i]['Report']['P+'] = f"{_peakp[_j]['f0']:0.2f} Hz within ±5% of {_peak[_i]['f0']:0.2f} Hz {sprit_utils._x_mark()}"
                _peak[_i]['PassList']['FreqStability'] = False                
        if _peak[_i]['Report']['P+'] == sprit_utils._x_mark() and len(_peakp) > 0:
            _peak[_i]['Report']['P+'] = f"{_peakp[_j]['f0']:0.2f} Hz within ±5% of {_peak[_i]['f0']:0.2f} Hz {sprit_utils._x_mark()}"

    return _peak


# Check stability
def __check_stability(_stdf, _peak, _hvsr_log_std, rank):
    """Test peaks for satisfying stability conditions as outlined by SESAME 2004
    This includes:
       - σf lower than a frequency dependent threshold ε(f)
       - σA (f0) lower than a frequency dependent threshold θ(f),


    Parameters
    ----------
    _stdf : list
        List with dictionaries containint frequency standard deviation for each peak
    _peak : list
        List of dictionaries containing input information about peak, without freq stability test
    _hvsr_log_std : list
        List of dictionaries containing log standard deviation along curve
    rank : int
        Integer value, higher value is "higher-ranked" peak, helps determine which peak is actual hvsr peak

    Returns
    -------
    _peak : list
        List of dictionaries containing output information about peak test
    """

    global max_rank

    #
    # check σf and σA
    #
    if rank:
        max_rank += 2
    for _i in range(len(_peak)):
        _peak[_i]['Sf'] = _stdf[_i]
        _peak[_i]['Sa'] = _hvsr_log_std[_i]
        _this_peak = _peak[_i]
        if _this_peak['f0'] < 0.2:
            _e = 0.25
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils._check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['LowStDev_Freq'] = True
            else:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils._x_mark()}"
                _this_peak['PassList']['LowStDev_Freq'] = False

            _t = 0.48
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils._check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['LowStDev_Amp'] = True
            else:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils._check_mark()}"
                _this_peak['PassList']['LowStDev_Amp'] = False

        elif 0.2 <= _this_peak['f0'] < 0.5:
            _e = 0.2
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils._check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['LowStDev_Freq'] = True
            else:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils._x_mark()}"
                _this_peak['PassList']['LowStDev_Freq'] = False

            _t = 0.40
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils._check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['LowStDev_Amp'] = True
            else:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils._check_mark()}"
                _this_peak['PassList']['LowStDev_Amp'] = False

        elif 0.5 <= _this_peak['f0'] < 1.0:
            _e = 0.15
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils._check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['LowStDev_Freq'] = True
            else:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils._x_mark()}"
                _this_peak['PassList']['LowStDev_Freq'] = False

            _t = 0.3
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils._check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['LowStDev_Amp'] = True
            else:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils._check_mark()}"
                _this_peak['PassList']['LowStDev_Amp'] = False

        elif 1.0 <= _this_peak['f0'] <= 2.0:
            _e = 0.1
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils._check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['LowStDev_Freq'] = True
            else:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils._x_mark()}"
                _this_peak['PassList']['LowStDev_Freq'] = False

            _t = 0.25
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils._check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['LowStDev_Amp'] = True
            else:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils._check_mark()}"
                _this_peak['PassList']['LowStDev_Amp'] = False

        elif _this_peak['f0'] > 0.2:
            _e = 0.05
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils._check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['LowStDev_Freq'] = True
            else:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils._x_mark()}"
                _this_peak['PassList']['LowStDev_Freq'] = False

            _t = 0.2
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils._check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['LowStDev_Amp'] = True
            else:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils._check_mark()}"
                _this_peak['PassList']['LowStDev_Freq'] = False

    return _peak


# Get frequency standard deviation
def __get_stdf(x_values, indexList, hvsrPeaks):
    """Private function to get frequency standard deviation of peak(s) of interest, from multiple time-step HVSR curves
    Paramaters
    ----------
        
        x_values : list or np.array
            Array of x_values of dataset (frequency or period, most often frequency)
        indexList : list
            List of index/indices of peak(s) of interest, (index is within the x_values list)
    
    Returns
    -------
        stdf : list
            List of standard deviations of the peak 
    """
    stdf = list()
    # Go through list containing all peak indices (often, just a single index of the main peak)
    for index in indexList:
        point = list()
        # Iterate to get index for all rows of pandas series, 
        #   each row contains a list of peak indices for the H/V curve from that time window
        for j in range(len(hvsrPeaks)):
            p = None
            
            # Iterate through each peak in each time window
            for k in range(len(hvsrPeaks.iloc[j])):
                if p is None:
                    p = hvsrPeaks.iloc[j][k]
                else:
                    # Find frequency peak closest in the current time window to the (current) hvsr peak
                    if abs(index - hvsrPeaks.iloc[j][k]) < abs(index - p):
                        p = hvsrPeaks.iloc[j][k]
                        # p = hvsrPeaks[j][k]
                        # print(p=p1, p, p1)
            if p is not None:
                # It should never be None, this is just a double check
                # Append the index of interest for that time window
                point.append(p)
        # Append the last index
        point.append(index)
        v = list()
        
        # Get all the actual frequencies (go through each index and extract the frequency from x_values)
        for pl in range(len(point)):
            v.append(x_values[point[pl]])
        
        # stdf is a list in case there are multiple peaks to check. 
        # Most of the time this is only a 1-item list
        # Contains std of frequencies of the peaks from each time window H/V curve that are closest to the main H/V peak
        stdf.append(np.std(v))
    return stdf

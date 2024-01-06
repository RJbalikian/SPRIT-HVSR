"""
This module is the main SpRIT module that contains all the functions needed to run HVSR analysis.

The functions defined here are read both by the SpRIT graphical user interface and by the command-line interface to run HVSR analysis on input data.

See documentation for individual functions for more information.
"""
import copy
import datetime
import inspect
import json
import math
import os
import pathlib
import pickle
import pkg_resources
import struct
import sys
import tempfile
import traceback
import warnings
import xml.etree.ElementTree as ET

import matplotlib
from matplotlib.backend_bases import MouseButton
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import obspy
from obspy.signal import PPSD
import pandas as pd
from pyproj import CRS, Transformer
import scipy

try: #For distribution
    from sprit import sprit_utils
    from sprit import sprit_gui
    from sprit import sprit_jupyter_UI
except: #For testing
    import sprit_utils
    import sprit_gui
    import sprit_jupyter_UI


global spritApp

#Main variables
greek_chars = {'sigma': u'\u03C3', 'epsilon': u'\u03B5', 'teta': u'\u03B8'}
channel_order = {'Z': 0, '1': 1, 'N': 1, '2': 2, 'E': 2}
separator_character = '='
obspyFormats =  ['AH', 'ALSEP_PSE', 'ALSEP_WTH', 'ALSEP_WTN', 'CSS', 'DMX', 'GCF', 'GSE1', 'GSE2', 'KINEMETRICS_EVT', 'KNET', 'MSEED', 'NNSA_KB_CORE', 'PDAS', 'PICKLE', 'Q', 'REFTEK130', 'RG16', 'SAC', 'SACXY', 'SEG2', 'SEGY', 'SEISAN', 'SH_ASC', 'SLIST', 'SU', 'TSPAIR', 'WAV', 'WIN', 'Y']

t0 = datetime.datetime.now().time()
max_rank = 0
plotRows = 4

#Get the main resources directory path, and the other paths as well
resource_dir = pathlib.Path(pkg_resources.resource_filename(__name__, 'resources/'))
sample_data_dir = resource_dir.joinpath('sample_data')
settings_dir = resource_dir.joinpath('settings')

sampleFileKeyMap = {'1':sample_data_dir.joinpath('SampleHVSRSite1_AM.RAC84.00.2023.046_2023-02-15_1704-1734.MSEED'),
                    '2':sample_data_dir.joinpath('SampleHVSRSite2_AM.RAC84.00.2023-02-15_2132-2200.MSEED'),
                    '3':sample_data_dir.joinpath('SampleHVSRSite3_AM.RAC84.00.2023.199_2023-07-18_1432-1455.MSEED'),
                    '4':sample_data_dir.joinpath('SampleHVSRSite4_AM.RAC84.00.2023.199_2023-07-18_1609-1629.MSEED'),
                    '5':sample_data_dir.joinpath('SampleHVSRSite5_AM.RAC84.00.2023.199_2023-07-18_2039-2100.MSEED'),
                    '6':sample_data_dir.joinpath('SampleHVSRSite6_AM.RAC84.00.2023.192_2023-07-11_1510-1528.MSEED'),
                    
                    'sample1':sample_data_dir.joinpath('SampleHVSRSite1_AM.RAC84.00.2023.046_2023-02-15_1704-1734.MSEED'),
                    'sample2':sample_data_dir.joinpath('SampleHVSRSite2_AM.RAC84.00.2023-02-15_2132-2200.MSEED'),
                    'sample3':sample_data_dir.joinpath('SampleHVSRSite3_AM.RAC84.00.2023.199_2023-07-18_1432-1455.MSEED'),
                    'sample4':sample_data_dir.joinpath('SampleHVSRSite4_AM.RAC84.00.2023.199_2023-07-18_1609-1629.MSEED'),
                    'sample5':sample_data_dir.joinpath('SampleHVSRSite5_AM.RAC84.00.2023.199_2023-07-18_2039-2100.MSEED'),
                    'sample6':sample_data_dir.joinpath('SampleHVSRSite6_AM.RAC84.00.2023.192_2023-07-11_1510-1528.MSEED'),

                    'sample_1':sample_data_dir.joinpath('SampleHVSRSite1_AM.RAC84.00.2023.046_2023-02-15_1704-1734.MSEED'),
                    'sample_2':sample_data_dir.joinpath('SampleHVSRSite2_AM.RAC84.00.2023-02-15_2132-2200.MSEED'),
                    'sample_3':sample_data_dir.joinpath('SampleHVSRSite3_AM.RAC84.00.2023.199_2023-07-18_1432-1455.MSEED'),
                    'sample_4':sample_data_dir.joinpath('SampleHVSRSite4_AM.RAC84.00.2023.199_2023-07-18_1609-1629.MSEED'),
                    'sample_5':sample_data_dir.joinpath('SampleHVSRSite5_AM.RAC84.00.2023.199_2023-07-18_2039-2100.MSEED'),
                    'sample_6':sample_data_dir.joinpath('SampleHVSRSite6_AM.RAC84.00.2023.192_2023-07-11_1510-1528.MSEED'),
                    
                    'batch':sample_data_dir.joinpath('Batch_SampleData.csv')}

#plt.rcParams['figure.figsize'] = (8,5.25)
#plt.rcParams['figure.dpi'] = 500

#CLASSES

#Check if the data is already the right class
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

#Class for batch data
class HVSRBatch:
    """HVSRBatch is the data container used for batch processing. It contains several HVSRData objects (one for each site). These can be accessed using their site name, either square brackets (HVSRBatchVariable["SiteName"]) or the dot (HVSRBatchVariable.SiteName) accessor.
    
    The dot accessor may not work if there is a space in the site name.
    
    All of the  functions in the sprit.pacakge are designed to perform the bulk of their operations iteratively on the individual HVSRData objects contained in the HVSRBatch object, and do little with the HVSRBatch object itself, besides using it determine which sites are contained within it.
    
    """
    @check_instance
    def __init__(self, sites_dict):
      
        self._batch_dict = sites_dict
        self.batch_dict = self._batch_dict
        self.batch = True

        for sitename, hvsrdata in sites_dict.items():
            setattr(self, sitename, hvsrdata)
            self[sitename]['batch']=True
            
        self.sites = list(self._batch_dict.keys())

    #METHODS
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

    def export(self, export_path=True, ext='hvsr'):
        """Method to export HVSRData objects in HVSRBatch container to indivdual .hvsr pickle files.

        Parameters
        ----------
        export_path : filepath, default=True
            Filepath to save file. Can be either directory (which will assign a filename based on the HVSRData attributes). By default True. If True, it will first try to save each file to the same directory as datapath, then if that does not work, to the current working directory, then to the user's home directory, by default True
        ext : str, optional
            The extension to use for the output, by default 'hvsr'. This is still a pickle file that can be read with pickle.load(), but will have .hvsr extension.
        """
        export_data(hvsr_data=self, export_path=export_path, ext=ext)

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
            return HVSRBatch(copy.deepcopy(self._batch_dict))
        else:
            return HVSRBatch(copy.copy(self._batch_dict))

    #Method wrapper of sprit.plot_hvsr function
    def plot(self, **kwargs):
        """Method to plot data, based on the sprit.plot_hvsr() function. All the same kwargs and default values apply as plot_hvsr(). For return_fig, returns it to the 'Plot_Report' attribute of each HVSRData object

        Returns
        -------
        _type_
            _description_
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
        """
        if 'report_format' in kwargs.keys():
            if 'csv' == kwargs['report_format']:
                for sitename in self:
                    rowList = []
                    rowList.append(get_report(self[sitename], **kwargs))
                return pd.concat(rowList, ignore_index=True)
            elif 'plot' == kwargs['report_format']:
                plotDict = {}
                for sitename in self:
                    if 'return_fig' in kwargs.keys() and kwargs['return_fig']:
                        plotDict[sitename] = get_report(self[sitename], **kwargs)
                    else:
                        get_report(self[sitename], **kwargs)
                return plotDict
            
        #Only report_format left is print, doesn't return anything, so doesn't matter if defalut or not
        for sitename in self:
            get_report(self[sitename], **kwargs)
        return

    def report(self, **kwargs):
        """Wrapper of get_report()"""
        return self.get_report(**kwargs)

    def export_settings(self, site_name=None, export_settings_path='default', export_settings_type='all', include_location=False, verbose=True):
        """Method to export settings from HVSRData object in HVSRBatch object. Simply calls sprit.export_settings() from specified HVSRData object in the HVSRBatch object. See sprit.export_settings() for more details.

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

#Class for each HVSR site
class HVSRData:
    """HVSRData is the basic data class of the sprit package. It contains all the processed data, input parameters, and reports.
    
    These attributes and objects can be accessed using square brackets or the dot accessor. For example, to access the site name, HVSRData['site'] and HVSRData.site will both return the site name.
    
    Some of the methods that work on the HVSRData object (e.g., .plot() and .get_report()) are essentially wrappers for some of the main sprit package functions (sprit.plot_hvsr() and sprit.get_report(), respectively)
    """
    #Old way of using this
    #def __new__(cls, params):
    #    if isinstance(params, (cls, HVSRBatch)):
    #        return params
    #    return super().__new__(cls)

    @check_instance    
    def __init__(self, params):
        self.params = params
        #self.datastream = None
        self.batch = False
        #self.tsteps_used = []

        for key, value in params.items():
            setattr(self, key, value)
            if key=='input_params':
                for k, v in params[key].items():
                    setattr(self, k, v)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __to_json(self, filepath):
        """Not yet supported, will export HVSRData object to json"""
        # open the file with the given filepath
        def unseriable_fun(o):
            if isinstance(o, np.ndarray):
                output = o.tolist()
            try:
                output = o.__dict__
            except:
                output = dir(o)
            return output

        with open(filepath, 'w') as f:
            # dump the JSON string to the file
            json.dump(self, f, default=unseriable_fun, sort_keys=True, indent=4)

    def export(self, export_path=None, ext='hvsr'):
        """Method to export HVSRData objects to .hvsr pickle files.

        Parameters
        ----------
        export_path : filepath, default=True
            Filepath to save file. Can be either directory (which will assign a filename based on the HVSRData attributes). 
            By default True. 
            If True, it will first try to save each file to the same directory as datapath, then if that does not work, to the current working directory, then to the user's home directory, by default True
        ext : str, optional
            The extension to use for the output, by default 'hvsr'. This is still a pickle file that can be read with pickle.load(), but will have .hvsr extension.
        """
        export_data(hvsr_data=self, export_path=export_path, ext=ext)

    #METHODS (many reflect dictionary methods)
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

    def items(self):
        """Method to return the "items" of the HVSRData object. For HVSRData objects, this is a dict_items object with the keys and values in tuples. Functions similar to dict.items().

        Returns
        -------
        dict_items
            A dict_items object of the HVSRData objects attributes, parameters, etc.
        """                
        return self.params.items()

    def copy(self, type='shallow'):
        """Make a copy of the HVSRData object. Uses python copy module.
        
        Parameters
        ----------
        type : str {'shallow', 'deep'}
            Based on input, creates either a shallow or deep copy of the HVSRData object. Shallow is equivalent of copy.copy(). Input of type='deep' is equivalent of copy.deepcopy() (still experimental). Defaults to shallow.
    
        """
        if type.lower()=='deep':
            return HVSRData(copy.deepcopy(self.params))
        else:
            return HVSRData(copy.copy(self.params))
        
    def plot(self, **kwargs):
        """Method to plot data, wrapper of sprit.plot_hvsr()

        Returns
        -------
        matplotlib.Figure, matplotlib.Axis (if return_fig=True)
        """
        if 'close_figs' not in kwargs.keys():
            kwargs['close_figs']=True
        plot_return = plot_hvsr(self, **kwargs)
        plt.show()
        return plot_return
        
    def get_report(self, **kwargs):
        """Method to get report from processed data, in print, graphical, or tabular format.

        Returns
        -------
        Variable
            May return nothing, pandas.Dataframe, or pyplot Figure, depending on input.
        """
        report_return = get_report(self, **kwargs)
        return report_return

    def report(self, **kwargs):
        """Wrapper of get_report()"""
        report_return = get_report(self, **kwargs)
        return report_return

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
    
    #ATTRIBUTES
    #params
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
    
    #datastream
    @property
    def datastream(self):
        """A copy of the original obspy datastream read in. This helps to retain the original data even after processing is carried out.

        Returns
        -------
        obspy.core.Stream.stream
            Obspy stream
        """
        return self._datastream

    @datastream.setter
    def datastream(self, value):
        if value is not None and (not isinstance(value, obspy.core.stream.Stream)):
            raise ValueError("datastream must be an obspy Stream.")
        self._datastream = value
        
    #batch
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
            Dictionary copy of the PPSD information from generate_ppsds()
        """
        return self._ppsds

    @ppsds.setter
    def ppsds(self, value):
        if not isinstance(value, dict):
            raise ValueError("ppsds dict with infomration from osbpy.PPSD (created by sprit.generate_ppsds())")                  
        self._ppsds=value

def gui_test():
    import subprocess
    print(sprit_gui.__file__)
    guiFile = sprit_gui.__file__
    subprocess.call(guiFile, shell=True)

    

#Launch the tkinter gui
def gui(kind='default'):
    """Function to open a graphical user interface (gui)

    Parameters
    ----------
    kind : str, optional
        What type of gui to open. "default" opens regular windowed interface, 
        "widget" opens jupyter widget'
        "lite" open lite (pending update), by default 'default'

    """

    defaultList = ['windowed', 'window', 'default', 'd']
    widgetList = ['widget', 'jupyter', 'notebook', 'w', 'nb']
    liteList = ['lite', 'light', 'basic', 'l', 'b']

    if kind.lower() in defaultList:
        import pkg_resources
        #guiPath = pathlib.Path(os.path.realpath(__file__))
        try:
            from sprit.sprit_gui import SPRIT_App
        except:
            from sprit_gui import SPRIT_App
        
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
                icon_path =pathlib.Path(pkg_resources.resource_filename(__name__, 'resources/icon/sprit_icon_alpha.ico')) 
                gui_root.iconbitmap(icon_path)
            except:
                icon_path = pathlib.Path(pkg_resources.resource_filename(__name__, 'resources/icon/sprit_icon.png'))
                gui_root.iconphoto(False, tk.PhotoImage(file=icon_path.as_posix()))
        except Exception as e:
            print("ICON NOT LOADED, still opening GUI")

        gui_root.resizable(True, True)
        spritApp = SPRIT_App(master=gui_root) #Open the app with a tk.Tk root

        gui_root.protocol("WM_DELETE_WINDOW", on_gui_closing)    
        gui_root.mainloop() #Run the main loop
    elif kind.lower() in widgetList:
        sprit_jupyter_UI.create_jupyter_ui()
    

#FUNCTIONS AND METHODS
#The run function to rule them all (runs all needed for simply processing HVSR)
def run(datapath, source='file', verbose=False, **kwargs):
    """The sprit.run() is the main function that allows you to do all your HVSR processing in one simple step (sprit.run() is how you would call it in your code, but it may also be called using sprit.sprit_hvsr.run())
    
    The datapath parameter of sprit.run() is the only required parameter. This can be either a single file, a list of files (one for each component, for example), a directory (in which case, all obspy-readable files will be added to an HVSRBatch instance), a Rasp. Shake raw data directory, or sample data.
    
        The sprit.run() function calls the following functions. This is the recommended order/set of functions to run to process HVSR using SpRIT. See the API documentation for these functions for more information:
        - input_params(): The datapath parameter of input_params() is the only required variable, though others may also need to be called for your data to process correctly.
        - fetch_data(): the source parameter of fetch_data() is the only explicit variable in the sprit.run() function aside from datapath and verbose. Everything else gets delivered to the correct function via the kwargs dictionary
        - remove_noise(): by default, the kind of noise removal is remove_method='auto'. See the remove_noise() documentation for more information. If remove_method is set to anything other than one of the explicit options in remove_noise, noise removal will not be carried out.
        - generate_ppsds(): generates ppsds for each component, which will be combined/used later. Any parameter of obspy.signal.spectral_estimation.PPSD() may also be read into this function.
        - remove_outlier_curves(): removes any outlier ppsd curves so that the data quality for when curves are combined will be enhanced. See the remove_outlier_curves() documentation for more information.
        - process_hvsr(): this is the main function processing the hvsr curve and statistics. See process_hvsr() documentation for more details. The hvsr_band parameter sets the frequency spectrum over which these calculations occur.
        - check_peaks(): this is the main function that will find and 'score' peaks to get a best peak. The parameter peak_freq_range can be set to limit the frequencies within which peaks are checked and scored.
        - get_report(): this is the main function that will print, plot, and/or save the results of the data. See the get_report() API documentation for more information.
        - export_data(): this function exports the final data output as a pickle file (by default, this pickle object has a .hvsr extension). This can be used to read data back into SpRIT without having to reprocess data.

    Parameters
    ----------
    datapath : str or filepath object that can be read by obspy
        Filepath to data to be processed. This may be a file or directory, depending on what kind of data is being processed (this can be specified with the source parameter). 
        For sample data, The following can be specified as the datapath parameter:
            - Any integer 1-6 (inclusive), or the string (e.g., datapath="1" or datapath=1 will work)
            - The word "sample" before any integer (e.g., datapath="sample1")
            - The word "sample" will default to "sample1" if source='file'. 
            - If source='batch', datapath should be datapath='sample' or datapath='batch'. In this case, it will read and process all the sample files using the HVSRBatch class. Set verbose=True to see all the information in the sample batch csv file.
    source : str, optional
        _description_, by default 'file'
    verbose : bool, optional
        _description_, by default False
    **kwargs
        Keyword arguments for the functions listed above. The keyword arguments are unique, so they will get parsed out and passed into the appropriate function.

    Returns
    -------
    hvsr_results : sprit.HVSRData or sprit.HVSRBatch object
        If a single file/data point is being processed, a HVSRData object will be returned. Otherwise, it will be a HVSRBatch object. See their documention for more information.

    Raises
    ------
    RuntimeError
        If the input parameter may not be read correctly. This is raised if the input_params() function fails. This raises an error since no other data processing or reading steps will be able to carried out correctly.
    RuntimeError
        If the data is not read/fetched correctly using fetch_data(), an error will be raised. This is raised if the fetch_data() function fails. This raises an error since no other data processing steps will be able to carried out correctly.
    RuntimeError
        If the data being processed is a single file, an error will be raised if generate_ppsds() does not work correctly. No errors are raised for remove_noise() errors (since that is an optional step) and the process_hvsr() step (since that is the last processing step) .
    """
   
    if 'hvsr_band' not in kwargs.keys():
        kwargs['hvsr_band'] = inspect.signature(input_params).parameters['hvsr_band'].default
    if 'peak_freq_range' not in kwargs.keys():
        kwargs['peak_freq_range'] = inspect.signature(input_params).parameters['peak_freq_range'].default

    #Get the input parameters
    input_params_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in tuple(inspect.signature(input_params).parameters.keys())}  
    try:
        params = input_params(datapath=datapath, verbose=verbose, **input_params_kwargs)
    except:
        #Even if batch, this is reading in data for all sites so we want to raise error, not just warn
        raise RuntimeError('Input parameters not read correctly, see sprit.input_params() function and parameters')
        #If input_params fails, initialize params as an HVSRDATA
        params = {'ProcessingStatus':{'InputParamsStatus':False, 'OverallStatus':False}}
        params.update(input_params_kwargs)
        params = sprit_utils.make_it_classy(params)

    #Fetch Data
    try:
        fetch_data_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in tuple(inspect.signature(fetch_data).parameters.keys())}
        dataIN = fetch_data(params=params, source=source, verbose=verbose, **fetch_data_kwargs)    
    except:
        #Even if batch, this is reading in data for all sites so we want to raise error, not just warn
        raise RuntimeError('Data not read correctly, see sprit.fetch_data() function and parameters for more details.')
    
    # Remove Noise
    try:
        remove_noise_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in tuple(inspect.signature(remove_noise).parameters.keys())}
        data_noiseRemoved = remove_noise(hvsr_data=dataIN, verbose=verbose,**remove_noise_kwargs)   
    except:
        data_noiseRemoved = dataIN
        
        #Reformat data so HVSRData and HVSRBatch data both work here
        if isinstance(data_noiseRemoved, HVSRData):
            data_noiseRemoved = {'place_holder_sitename':data_noiseRemoved}
            dataIN = {'place_holder_sitename':dataIN}
            
        for site_name in data_noiseRemoved.keys():
            data_noiseRemoved[site_name]['ProcessingStatus']['RemoveNoiseStatus']=False
            #Since noise removal is not required for data processing, check others first
            if dataIN[site_name]['ProcessingStatus']['OverallStatus']:
                data_noiseRemoved[site_name]['ProcessingStatus']['OverallStatus'] = True        
            else:
                data_noiseRemoved[site_name]['ProcessingStatus']['OverallStatus'] = False

            #If it wasn't originally HVSRBatch, make it HVSRData object again
            if not data_noiseRemoved[site_name]['batch']:
                data_noiseRemoved = data_noiseRemoved[site_name]
    
    #Generate PPSDs
    try:
        generate_ppsds_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in tuple(inspect.signature(generate_ppsds).parameters.keys())}
        PPSDkwargs = {k: v for k, v in locals()['kwargs'].items() if k in tuple(inspect.signature(PPSD).parameters.keys())}
        generate_ppsds_kwargs.update(PPSDkwargs)
        ppsd_data = generate_ppsds(hvsr_data=data_noiseRemoved, verbose=verbose,**generate_ppsds_kwargs)
    except Exception as e:
        if source == 'file' or source=='raw':
            if hasattr(e, 'message'):
                errMsg = e.message
            else:
                errMsg = e
            raise RuntimeError(f"generate_ppsds() error: {errMsg}")

        #Reformat data so HVSRData and HVSRBatch data both work here
        ppsd_data = data_noiseRemoved
        if isinstance(ppsd_data, HVSRData):
            ppsd_data = {'place_holder_sitename':ppsd_data}
            
        for site_name in ppsd_data.keys(): #This should work more or less the same for batch and regular data now
            ppsd_data[site_name]['ProcessingStatus']['PPSDStatus']=False
            ppsd_data[site_name]['ProcessingStatus']['OverallStatus'] = False
    
            #If it wasn't originally HVSRBatch, make it HVSRData object again
            if not ppsd_data[site_name]['batch']:
                ppsd_data = ppsd_data[site_name]
    
    # Remove Outlier Curves
    try:
        remove_outlier_curve_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in tuple(inspect.signature(remove_outlier_curves).parameters.keys())}
        data_curvesRemoved = remove_outlier_curves(hvsr_data=ppsd_data, verbose=verbose,**remove_outlier_curve_kwargs)   
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
        
        #Reformat data so HVSRData and HVSRBatch data both work here
        data_curvesRemoved = ppsd_data
        if isinstance(data_curvesRemoved, HVSRData):
            data_curvesRemoved = {'place_holder_sitename':data_curvesRemoved}
            
        for site_name in data_curvesRemoved.keys(): #This should work more or less the same for batch and regular data now
            data_curvesRemoved[site_name]['ProcessingStatus']['RemoveOutlierCurvesStatus'] = False
            data_curvesRemoved[site_name]['ProcessingStatus']['OverallStatus'] = False
    
            #If it wasn't originally HVSRBatch, make it HVSRData object again
            if not data_curvesRemoved[site_name]['batch']:
                data_curvesRemoved = data_curvesRemoved[site_name]
    
    #Process HVSR Curves
    try:
        process_hvsr_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in tuple(inspect.signature(process_hvsr).parameters.keys())}
        hvsr_results = process_hvsr(hvsr_data=ppsd_data, verbose=verbose,**process_hvsr_kwargs)
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

        hvsr_results = ppsd_data
        if isinstance(hvsr_results, HVSRData):
            hvsr_results = {'place_holder_sitename':hvsr_results}
            
        for site_name in hvsr_results.keys(): #This should work more or less the same for batch and regular data now
        
            hvsr_results[site_name]['ProcessingStatus']['HVStatus']=False
            hvsr_results[site_name]['ProcessingStatus']['OverallStatus'] = False
            
            #If it wasn't originally HVSRBatch, make it HVSRData object again
            if not hvsr_results[site_name]['batch']:
                hvsr_results = hvsr_results[site_name]            
            
    #Final post-processing/reporting

    #Check peaks
    check_peaks_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in tuple(inspect.signature(check_peaks).parameters.keys())}
    hvsr_results = check_peaks(hvsr_data=hvsr_results, verbose=verbose, **check_peaks_kwargs)

    get_report_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in tuple(inspect.signature(get_report).parameters.keys())}
    get_report(hvsr_results=hvsr_results, verbose=verbose, **get_report_kwargs)

    if verbose:
        if 'report_format' in get_report_kwargs.keys():
            #if report_format is 'print', we would have already printed it in previous step
            if get_report_kwargs['report_format']=='print' or 'print' in get_report_kwargs['report_format'] or isinstance(hvsr_results, HVSRBatch):
                #We do not need to print another report if already printed to terminal
                pass
            else:
                #We will just change the report_format kwarg to print, since we already got the originally intended report format above, 
                #   now need to print for verbose output
                get_report_kwargs['report_format']='print'
                get_report(hvsr_results=hvsr_results, **get_report_kwargs)
                
            if get_report_kwargs['report_format']=='plot' or 'plot' in get_report_kwargs['report_format']:
                #We do not need to plot another report if already plotted
                pass
            else:
                #hvplot_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in plot_hvsr.__code__.co_varnames}
                #hvsr_results['HV_Plot'] = plot_hvsr(hvsr_results, return_fig=True, show=False, close_figs=True)
                pass
        else:
            pass
    
    #Export processed data if export_path(as pickle currently, default .hvsr extension)
    if 'export_path' in kwargs.keys():
        if kwargs['export_path'] is None:
            pass
        else:
            if 'ext' in kwargs.keys():
                ext = kwargs['ext']
            else:
                ext = 'hvsr'
            export_data(hvsr_data=hvsr_results, export_path=kwargs['export_path'], ext=ext, verbose=verbose)        

    return hvsr_results

#Quality checks, stability tests, clarity tests
#def check_peaks(hvsr, x, y, index_list, peak, peakm, peakp, hvsr_peaks, stdf, hvsr_log_std, rank, hvsr_band=[0.4, 40], do_rank=False):
def check_peaks(hvsr_data, hvsr_band=[0.4, 40], peak_selection='max', peak_freq_range=[1, 20], verbose=False):
    """Function to run tests on HVSR peaks to find best one and see if it passes quality checks

        Parameters
        ----------
        hvsr_data : dict
            Dictionary containing all the calculated information about the HVSR data (i.e., hvsr_out returned from process_hvsr)
        hvsr_band : tuple or list, default=[0.4, 40]
            2-item tuple or list with lower and upper limit of frequencies to analyze
        peak_selection : str or numeric, default='max'
            How to select the "best" peak used in the analysis. For peak_selection="max" (default value), the highest peak within peak_freq_range is used.
            For peak_selection='scored', an algorithm is used to select the peak based in part on which peak passes the most SESAME criteria.
            If a numeric value is used (e.g., int or float), this should be a frequency value to manually select as the peak of interest.
        peak_freq_range : tuple or list, default=[1, 20];
            The frequency range within which to check for peaks. If there is an HVSR curve with multiple peaks, this allows the full range of data to be processed while limiting peak picks to likely range.
        verbose : bool, default=False
            Whether to print results and inputs to terminal.
        
        Returns
        -------
        hvsr_data   : HVSRData or HVSRBatch object
            Object containing previous input data, plus information about peak tests
    """
    orig_args = locals().copy() #Get the initial arguments

    # Update with processing parameters specified previously in input_params, if applicable
    if 'processing_parameters' in hvsr_data.keys():
        if 'check_peaks' in hvsr_data['processing_parameters'].keys():
            for k, v in hvsr_data['processing_parameters']['check_peaks'].items():
                defaultVDict = dict(zip(inspect.getfullargspec(check_peaks).args[1:], 
                                        inspect.getfullargspec(check_peaks).defaults))
                # Manual input to function overrides the imported parameter values
                if (not isinstance(v, (HVSRData, HVSRBatch))) and (k in orig_args.keys()) and (orig_args[k]==defaultVDict[k]):
                    orig_args[k] = v

    hvsr_band = orig_args['hvsr_band']
    peak_selection = orig_args['peak_selection']
    peak_freq_range = orig_args['peak_freq_range']
    verbose = orig_args['verbose']

    if (verbose and 'input_params' not in hvsr_data.keys()) or (verbose and not hvsr_data['batch']):
        if isinstance(hvsr_data, HVSRData) and hvsr_data['batch']:
            pass
        else:
            print('\nChecking peaks in the H/V Curve (check_peaks())')
            print('\tUsing the following parameters:')
            for key, value in orig_args.items():
                if key=='hvsr_data':
                    pass
                else:
                    print('\t  {}={}'.format(key, value))
            print()
  
    #First, divide up for batch or not
    if isinstance(hvsr_data, HVSRBatch):
        if verbose:
            print('\t  Running in batch mode')
        #If running batch, we'll loop through each site
        for site_name in hvsr_data.keys():
            args = orig_args.copy() #Make a copy so we don't accidentally overwrite
            args['hvsr_data'] =  hvsr_data[site_name] #Get what would normally be the "params" variable for each site
            if hvsr_data[site_name]['ProcessingStatus']['OverallStatus']:
                try:
                    hvsr_data[site_name] = _check_peaks_batch(**args) #Call another function, that lets us run this function again
                except:
                    if verbose:
                        print(f"\t{site_name}: check_peaks() unsuccessful. Peaks not checked.")
                    else:
                        warnings.warn(f"\t{site_name}: check_peaks() unsuccessful. Peaks not checked.", RuntimeWarning)
                
        hvsr_data = HVSRBatch(hvsr_data)
    else:
        if hvsr_data['ProcessingStatus']['OverallStatus']:
            if not hvsr_band:
                hvsr_band = [0.4,40]
            
            hvsr_data['hvsr_band'] = hvsr_band

            anyK = list(hvsr_data['x_freqs'].keys())[0]

            x = hvsr_data['x_freqs'][anyK] #Consistent for all curves
            y = hvsr_data['hvsr_curve'] #Calculated based on "Use" column

            scorelist = ['score', 'scored', 'best', 's']
            maxlist = ['max', 'highest', 'm']
            # Convert peak_selection to numeric, get index of nearest value as list item for __init_peaks()
            try:
                peak_val = float(peak_selection)
                index_list = [np.argmin(np.abs(x - peak_val))]        
            except:
                # If score method is being used, get index list for __init_peaks()
                if peak_selection in scorelist:
                    index_list = hvsr_data['hvsr_peak_indices'] #Calculated based on hvsr_curve
                elif peak_selection in maxlist:
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
            
            hvsrp = hvsr_data['hvsrp'] #Calculated based on "Use" column
            hvsrm = hvsr_data['hvsrm'] #Calculated based on "Use" column

            hvsrPeaks = hvsr_data['hvsr_df'][hvsr_data['hvsr_df']['Use']]['CurvesPeakIndices']
            #hvsrPeaks = hvsr_data['ind_hvsr_peak_indices'] #Original calculation

            hvsr_log_std = hvsr_data['hvsr_log_std']
            peak_freq_range = hvsr_data['peak_freq_range']

            #Do for hvsr
            peak = __init_peaks(x, y, index_list, hvsr_band, peak_freq_range)

            peak = __check_curve_reliability(hvsr_data, peak)
            peak = __check_clarity(x, y, peak, do_rank=True)

            #Do for hvsrp
            # Find  the relative extrema of hvsrp (hvsr + 1 standard deviation)
            if not np.isnan(np.sum(hvsrp)):
                index_p = __find_peaks(hvsrp)
            else:
                index_p = list()

            peakp = __init_peaks(x, hvsrp, index_p, hvsr_band, peak_freq_range)
            peakp = __check_clarity(x, hvsrp, peakp, do_rank=True)

            # Do for hvsrm
            # Find  the relative extrema of hvsrm (hvsr - 1 standard deviation)
            if not np.isnan(np.sum(hvsrm)):
                index_m = __find_peaks(hvsrm)
            else:
                index_m = list()

            peakm = __init_peaks(x, hvsrm, index_m, hvsr_band, peak_freq_range)
            peakm = __check_clarity(x, hvsrm, peakm, do_rank=True)

            # Get standard deviation of time peaks
            stdf = __get_stdf(x, index_list, hvsrPeaks)

            peak = __check_freq_stability(peak, peakm, peakp)
            peak = __check_stability(stdf, peak, hvsr_log_std, rank=True)

            hvsr_data['PeakReport'] = peak

            #Iterate through peaks and 
            #   Get the BestPeak based on the peak score
            #   Calculate whether each peak passes enough tests
            curveTests = ['WindowLengthFreq.','SignificantCycles', 'LowCurveStDevOverTime']
            peakTests = ['PeakProminenceBelow', 'PeakProminenceAbove', 'PeakAmpClarity', 'FreqStability', 'PeakStability_FreqStD', 'PeakStability_AmpStD']
            bestPeakScore = 0

            for p in hvsr_data['PeakReport']:
                #Get BestPeak
                if p['Score'] > bestPeakScore:
                    bestPeakScore = p['Score']
                    bestPeak = p

                #Calculate if peak passes criteria
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
                
            #Designate BestPeak in output dict
            if len(hvsr_data['PeakReport']) == 0:
                bestPeak={}
                print(f"No Best Peak identified for {hvsr_data['site']}")

            hvsr_data['BestPeak'] = bestPeak
        else:
            hvsr_data['BestPeak'] = {}
            print(f"Processing Errors: No Best Peak identified for {hvsr_data['site']}")
            try:
                hvsr_data.plot()
            except:
                pass

        hvsr_data['processing_parameters']['check_peaks'] = {}
        for key, value in orig_args.items():
            hvsr_data['processing_parameters']['check_peaks'][key] = value


    return hvsr_data

#Function to export data to file
def export_data(hvsr_data, export_path=None, ext='hvsr', verbose=False):
    """Export data into pickle format that can be read back in using import_data() so data does not need to be processed each time. 
    Default extension is .hvsr but it is still a pickled file that can be read in using pickle.load().

    Parameters
    ----------
    hvsr_data : HVSRData or HVSRBatch
        Data to be exported
    export_path : str or filepath object, default = None
        String or filepath object to be read by pathlib.Path() and/or a with open(export_path, 'wb') statement. If None, defaults to input datapath directory, by default None
    ext : str, default = 'hvsr'
        Filepath extension to use for data file, by default 'hvsr'
    """
    def _do_export(_hvsr_data=hvsr_data, _export_path=export_path, _ext=ext):
        
        fname = f"{_hvsr_data.site}_{_hvsr_data.acq_date}_pickled.{ext}"
        if _export_path is None or _export_path is True:
            _export_path = _hvsr_data['datapath']
            _export_path = pathlib.Path(_export_path).with_name(fname)
        else:
            _export_path = pathlib.Path(_export_path)
            if _export_path.is_dir():
                _export_path = _export_path.joinpath(fname)    

        _export_path = str(_export_path)
        with open(_export_path, 'wb') as f:
            pickle.dump(_hvsr_data, f) 
            
        if verbose:
            print(f"Processed data exported as pickled data to: {_export_path} [~{round(float(pathlib.Path(_export_path).stat().st_size)/2**20,1)} Mb]")    
            
    if isinstance(hvsr_data, HVSRBatch):
        for sitename in hvsr_data.keys():
            _do_export(hvsr_data[sitename], export_path, ext)
    elif isinstance(hvsr_data, HVSRData):
        _do_export(hvsr_data, export_path, ext)
    else:
        print("Error in data export. Data must be either of type sprit.HVSRData or sprit.HVSRBatch")         
    return

###WORKING ON THIS
#Save default instrument and processing settings to json file(s)
def export_settings(hvsr_data, export_settings_path='default', export_settings_type='all', include_location=False, verbose=True):
    """Save settings to json file

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
        settingsPath = resource_dir.joinpath('settings')
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
    instKeys = ["instrument", "net", "sta", "loc", "cha", "depth", "metapath", "hvsr_band"]
    inst_location_keys = ['xcoord', 'ycoord', 'elevation', 'elev_unit', 'input_crs']
    procFuncs = [fetch_data, remove_noise, generate_ppsds, process_hvsr, check_peaks, get_report]

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

#Reads in traces to obspy stream
def fetch_data(params, source='file', trim_dir=None, export_format='mseed', detrend='spline', detrend_order=2, update_metadata=True, plot_input_stream=False, verbose=False, **kwargs):
    """Fetch ambient seismic data from a source to read into obspy stream
    
    Parameters
    ----------
    params  : dict
        Dictionary containing all the necessary params to get data.
            Parameters defined using input_params() function.
    source  : str, {'raw', 'dir', 'file', 'batch'}
        String indicating where/how data file was created. For example, if raw data, will need to find correct channels.
            'raw' finds raspberry shake data, from raw output copied using scp directly from Raspberry Shake, either in folder or subfolders; 
            'dir' is used if the day's 3 component files (currently Raspberry Shake supported only) are all 3 contained in a directory by themselves.
            'file' is used if the params['datapath'] specified in input_params() is the direct filepath to a single file to be read directly into an obspy stream.
            'batch' is used to read a list or specified set of seismic files. 
                Most commonly, a csv file can be read in with all the parameters. Each row in the csv is a separate file. Columns can be arranged by parameter.
    trim_dir : None or str or pathlib obj, default=None
        If None (or False), data is not trimmed in this function.
        Otherwise, this is the directory to save trimmed and exported data.
    export_format: str='mseed'
        If trim_dir is not None, this is the format in which to save the data
    detrend : str or bool, default='spline'
        If False, data is not detrended.
        Otherwise, this should be a string accepted by the type parameter of the obspy.core.trace.Trace.detrend method: https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.detrend.html
    detrend_order : int, default=2
        If detrend parameter is 'spline' or 'polynomial', this is passed directly to the order parameter of obspy.core.trace.Trace.detrend method.
    update_metadata : bool, default=True
        Whether to update the metadata file, used primarily with Raspberry Shake data which uses a generic inventory file.
    plot_input_stream : bool, default=False
        Whether to plot the raw input stream. This plot includes a spectrogram (Z component) and the raw (with decimation for speed) plots of each component signal.
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
    
    # Update with processing parameters specified previously in input_params, if applicable
    if 'processing_parameters' in params.keys():
        if 'fetch_data' in params['processing_parameters'].keys():
            defaultVDict = dict(zip(inspect.getfullargspec(fetch_data).args[1:], 
                        inspect.getfullargspec(fetch_data).defaults))
            defaultVDict['kwargs'] = kwargs
            for k, v in params['processing_parameters']['fetch_data'].items():
                # Manual input to function overrides the imported parameter values
                if k!='params' and k in orig_args.keys() and orig_args[k]==defaultVDict[k]:
                    orig_args[k] = v

    #Update local variables, in case of previously-specified parameters
    source=orig_args['source']
    trim_dir=orig_args['trim_dir']
    export_format=orig_args['export_format']
    detrend=orig_args['detrend']
    detrend_order=orig_args['detrend_order']
    update_metadata=orig_args['update_metadata']
    plot_input_stream=orig_args['plot_input_stream']
    verbose=orig_args['verbose']
    kwargs=orig_args['kwargs']

    if source != 'batch' and verbose:
        print('\nFetching data (fetch_data())')
        print()

    params = get_metadata(params, update_metadata=update_metadata, source=source)
    inv = params['inv']
    date=params['acq_date']

    #Cleanup for gui input
    if isinstance(params['datapath'], (obspy.Stream, obspy.Trace)):
        pass
    elif '}' in str(params['datapath']):
        params['datapath'] = params['datapath'].as_posix().replace('{','')
        params['datapath'] = params['datapath'].split('}')
    
    sampleListNos = ['1', '2', '3', '4', '5', '6']
    sampleList = ['1', '2', '3', '4', '5', '6', 'batch', 'sample', 'sample_batch']
    for s in sampleListNos:
        sampleList.append(f'sample{s}')
        sampleList.append(f'sample_{s}')

    #Make sure datapath is pointing to an actual file
    if isinstance(params['datapath'],list):
        for i, d in enumerate(params['datapath']):
            params['datapath'][i] = sprit_utils.checkifpath(str(d).strip(), sample_list=sampleList)
        dPath = params['datapath']
    elif isinstance(params['datapath'], (obspy.Stream, obspy.Trace)):
        pass
    else:
        dPath = sprit_utils.checkifpath(params['datapath'], sample_list=sampleList)

    inst = params['instrument']

    #Need to put dates and times in right formats first
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
    else: #FOR NOW, need to update
        date = datetime.datetime.now()
        doy = date.timetuple().tm_yday
        year = date.year
        warnings.warn("Did not recognize date, using year {} and day {}".format(year, doy))

    #Select which instrument we are reading from (requires different processes for each instrument)
    raspShakeInstNameList = ['raspberry shake', 'shake', 'raspberry', 'rs', 'rs3d', 'rasp. shake', 'raspshake']
    trominoNameList = ['tromino', 'trom', 'tromino 3g', 'tromino 3g+', 'tr', 't']

    #Get any kwargs that are included in obspy.read
    obspyReadKwargs = {}
    for argName in inspect.getfullargspec(obspy.read)[0]:
        if argName in kwargs.keys():
            obspyReadKwargs[argName] = kwargs[argName]

    #Select how reading will be done
    if source=='raw':
        try:
            if inst.lower() in raspShakeInstNameList:
                rawDataIN = __read_RS_file_struct(dPath, source, year, doy, inv, params, verbose=verbose)

            elif inst.lower() in trominoNameList:
                rawDataIN = __read_tromino_files(dPath, params, verbose=verbose)
        except:
            raise RuntimeError(f"Data not fetched for {params['site']}. Check input parameters or the data file.")
    elif source=='stream' or isinstance(params, (obspy.Stream, obspy.Trace)):
        rawDataIN = params['datapath'].copy()
    elif source=='dir':
        if inst.lower() in raspShakeInstNameList:
            rawDataIN = __read_RS_file_struct(dPath, source, year, doy, inv, params, verbose=verbose)
        else:
            obspyFiles = {}
            for obForm in obspyFormats:
                temp_file_glob = pathlib.Path(dPath.as_posix().lower()).glob('.'+obForm.lower())
                for f in temp_file_glob:
                    currParams = params
                    currParams['datapath'] = f

                    curr_data = fetch_data(params, source='file', #all the same as input, except just reading the one file using the source='file'
                                trim_dir=trim_dir, export_format=export_format, detrend=detrend, detrend_order=detrend_order, update_metadata=update_metadata, verbose=verbose, **kwargs)
                    curr_data.merge()
                    obspyFiles[f.stem] = curr_data  #Add path object to dict, with filepath's stem as the site name
            return HVSRBatch(obspyFiles)
    elif source=='file' and str(params['datapath']).lower() not in sampleList:
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
        elif str(dPath)[:6].lower()=='sample':
            pass
        else:
            rawDataIN = obspy.read(dPath, **obspyReadKwargs)#, starttime=obspy.core.UTCDateTime(params['starttime']), endttime=obspy.core.UTCDateTime(params['endtime']), nearest_sample =True)
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter(action='ignore', category=UserWarning)
            rawDataIN.attach_response(inv)
    elif source=='batch' and str(params['datapath']).lower() not in sampleList:
        if verbose:
            print('\nFetching data (fetch_data())')
        batch_data_read_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in batch_data_read.__code__.co_varnames}
        params = batch_data_read(input_data=params['datapath'], verbose=verbose, **batch_data_read_kwargs)
        params = HVSRBatch(params)
        return params
    elif str(params['datapath']).lower() in sampleList or f"sample{params['datapath'].lower()}" in sampleList:
        sample_data_dir = pathlib.Path(pkg_resources.resource_filename(__name__, 'resources/sample_data/'))
        if source=='batch':
            params['datapath'] = sample_data_dir.joinpath('Batch_SampleData.csv')
            params = batch_data_read(input_data=params['datapath'], batch_type='sample', verbose=verbose)
            params = HVSRBatch(params)
            return params

        elif source=='dir':
            params['datapath'] = sample_data_dir.joinpath('Batch_SampleData.csv')
            params = batch_data_read(input_data=params['datapath'], batch_type='sample', verbose=verbose)
            params = HVSRBatch(params)
            return params

        elif source=='file':
            params['datapath'] = str(params['datapath']).lower()
            
            if params['datapath'].lower() in sampleFileKeyMap.keys():
                params['datapath'] = sampleFileKeyMap[params['datapath'].lower()]
            else:
                params['datapath'] = sample_data_dir.joinpath('SampleHVSRSite1_AM.RAC84.00.2023.046_2023-02-15_1704-1734.MSEED')

            dPath = params['datapath']
            rawDataIN = obspy.read(dPath)#, starttime=obspy.core.UTCDateTime(params['starttime']), endttime=obspy.core.UTCDateTime(params['endtime']), nearest_sample =True)
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter(action='ignore', category=UserWarning)
                rawDataIN.attach_response(inv)
    else:
        try:
            rawDataIN = obspy.read(dPath)
            rawDataIN.attach_response(inv)
        except:
            RuntimeError(f'source={source} not recognized, and datapath cannot be read using obspy.read()')

    #Get metadata from the data itself, if not reading raw data
    try:
        dataIN = rawDataIN.copy()
        if source!='raw':
            #Use metadata from file for;
            # site
            if params['site'] == "HVSR Site":
                if isinstance(dPath, (list, tuple)):
                    dPath = dPath[0]
                params['site'] = dPath.stem
                params['params']['site'] = dPath.stem
            
            # network
            if str(params['net']) == 'AM':
                params['net'] = dataIN[0].stats.network
                params['params']['net'] = dataIN[0].stats.network

            # station
            if str(params['sta']) == 'RAC84':
                params['sta'] = dataIN[0].stats.station
                params['params']['sta'] = dataIN[0].stats.station

            # loc
            if str(params['loc']) == '00':
                params['loc'] = dataIN[0].stats.location
                params['params']['loc'] = dataIN[0].stats.location
            
            # channels
            channelList = []
            if str(params['cha']) == ['EHZ', 'EHN', 'EHE']:
                for tr in dataIN:
                    if tr.stats.channel not in channelList:
                        channelList.append(tr.stats.channel)
                        channelList.sort(reverse=True) #Just so z is first, just in case
                params['cha'] = channelList
                params['params']['cha'] = channelList
           
            # Acquisition date
            if str(params['acq_date']) == str(datetime.datetime.now().date()):
                params['acq_date'] = dataIN[0].stats.starttime.date

            # starttime
            today_Starttime = obspy.UTCDateTime(datetime.datetime(year=datetime.date.today().year, month=datetime.date.today().month,
                                                                 day = datetime.date.today().day,
                                                                hour=0, minute=0, second=0, microsecond=0))
            maxStarttime = datetime.datetime(year=params['acq_date'].year, month=params['acq_date'].month, day=params['acq_date'].day, 
                                             hour=0, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc)
            if str(params['starttime']) == str(today_Starttime):
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
                params['starttime'] = newStarttime
                params['params']['starttime'] = newStarttime

            # endttime
            today_Endtime = obspy.UTCDateTime(datetime.datetime(year=datetime.date.today().year, month=datetime.date.today().month,
                                                                 day = datetime.date.today().day,
                                                                hour=23, minute=59, second=59, microsecond=999999))
            tomorrow_Endtime = today_Endtime + (60*60*24)
            minEndtime = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)#(hour=23, minute=59, second=59, microsecond=999999)
            if str(params['endtime']) == str(today_Endtime) or str(params['endtime'])==tomorrow_Endtime:
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
                params['endtime'] = newEndtime
                params['params']['endtime'] = newEndtime


            #print(dataIN)
            #print(params['starttime'])
            #print(params['endtime'])
            dataIN = dataIN.split()
            dataIN = dataIN.trim(starttime=params['starttime'], endtime=params['endtime'])
            dataIN.merge()
            #print(dataIN)
    except:
        raise RuntimeError('Data not fetched. Check your input parameters or the data file.')
        
    #Trim and save data as specified
    if trim_dir=='None':
        trim_dir=None
    if not trim_dir:
        pass
    else:
        if isinstance(params, HVSRBatch):
            pass
        else:
            dataIN = _trim_data(input=params, stream=dataIN, export_dir=trim_dir, source=source, export_format=export_format)

    #Split data if masked array (if there are gaps)...detrending cannot be done without
    for tr in dataIN:
        if isinstance(tr.data, np.ma.masked_array):
            dataIN = dataIN.split()
            #Splits entire stream if any trace is masked_array
            break

    #Detrend data
    if isinstance(params, HVSRBatch):
        pass
    else:
        dataIN =  __detrend_data(input=dataIN, detrend=detrend, detrend_order=detrend_order, verbose=verbose, source=source)

    #Remerge data
    dataIN = dataIN.merge(method=1)

    #Plot the input stream?
    if plot_input_stream:
        try:
            params['InputPlot'] = _plot_specgram_stream(stream=dataIN, params=params, component='Z', stack_type='linear', detrend='mean', dbscale=True, fill_gaps=None, ylimstd=3, return_fig=True, fig=None, ax=None, show_plot=False)
            #_get_removed_windows(input=dataIN, fig=params['InputPlot'][0], ax=params['InputPlot'][1], lineArtist =[], winArtist = [], existing_lineArtists=[], existing_xWindows=[], exist_win_format='matplotlib', keep_line_artists=True, time_type='matplotlib', show_plot=True)
            plt.show()
        except:
            print('Error with default plotting method, falling back to internal obspy plotting method')
            dataIN.plot(method='full', linewidth=0.25)

    #Sort channels (make sure Z is first, makes things easier later)
    if isinstance(params, HVSRBatch):
        pass
    else:
        dataIN = _sort_channels(input=dataIN, source=source, verbose=verbose)

    #Clean up the ends of the data unless explicitly specified to do otherwise (this is a kwarg, not a parameter)
    if 'clean_ends' not in kwargs.keys():
        clean_ends=True 
    else:
        clean_ends = kwargs['clean_ends']

    if clean_ends:
        maxStarttime = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) - datetime.timedelta(days=36500) #100 years ago
        minEndtime = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) 

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
    
    params['batch'] = False #Set False by default, will get corrected later in batch mode        
    params['input_stream'] = dataIN.copy()
    params['stream'] = dataIN.copy()
    
    if 'processing_parameters' not in params.keys():
        params['processing_parameters'] = {}
    params['processing_parameters']['fetch_data'] = {}
    for key, value in orig_args.items():
        params['processing_parameters']['fetch_data'][key] = value

    
    params['ProcessingStatus']['FetchDataStatus'] = True
    if verbose and not isinstance(params, HVSRBatch):
        dataINStr = dataIN.__str__().split('\n')
        for line in dataINStr:
            print('\t',line)
    
    params = _check_processing_status(params, start_time=start_time, func_name=inspect.stack()[0][3], verbose=verbose)

    return params

#Generate PPSDs for each channel
def generate_ppsds(hvsr_data, verbose=False, **ppsd_kwargs):
    """Generates PPSDs for each channel

        Channels need to be in Z, N, E order
        Info on PPSD creation here: https://docs.obspy.org/packages/autogen/obspy.signal.spectral_estimation.PPSD.html
        
        Parameters
        ----------
        hvsr_data : dict, HVSRData object, or HVSRBatch object
            Data object containing all the parameters and other data of interest (stream and paz, for example)
        verbose : bool, default=True
            Whether to print inputs and results to terminal
        **ppsd_kwargs : dict
            Dictionary with keyword arguments that are passed directly to obspy.signal.PPSD.
            If the following keywords are not specified, their defaults are amended in this function from the obspy defaults for its PPSD function. Specifically:
                - ppsd_length defaults to 60 (seconds) here instead of 3600
                - skip_on_gaps defaults to True instead of False
                - period_step_octaves defaults to 0.03125 instead of 0.125

        Returns
        -------
            ppsds : HVSRData object
                Dictionary containing entries with ppsds for each channel
    """
    #First, divide up for batch or not
    orig_args = locals().copy() #Get the initial arguments
    start_time = datetime.datetime.now()

    ppsd_kwargs_sprit_defaults = ppsd_kwargs.copy()
    #Set defaults here that are different than obspy defaults
    if 'ppsd_length' not in ppsd_kwargs.keys():
        ppsd_kwargs_sprit_defaults['ppsd_length'] = 30.0
    if 'skip_on_gaps' not in ppsd_kwargs.keys():
        ppsd_kwargs_sprit_defaults['skip_on_gaps'] = True
    if 'period_step_octaves' not in ppsd_kwargs.keys():
        ppsd_kwargs_sprit_defaults['period_step_octaves'] = 0.03125
    if 'period_limits' not in ppsd_kwargs.keys():
        ppsd_kwargs_sprit_defaults['period_limits'] =  [1/40, 1/0.4]

    #Get Probablistic power spectral densities (PPSDs)
    #Get default args for function
    def get_default_args(func):
        signature = inspect.signature(func)
        return {
            k: v.default
            for k, v in signature.parameters.items()
            if v.default is not inspect.Parameter.empty
            }
    
    ppsd_kwargs = get_default_args(PPSD)
    ppsd_kwargs.update(ppsd_kwargs_sprit_defaults)#Update with sprit defaults, or user input
    orig_args['ppsd_kwargs'] = ppsd_kwargs

    # Update with processing parameters specified previously in input_params, if applicable
    if 'processing_parameters' in hvsr_data.keys():
        if 'generate_ppsds' in hvsr_data['processing_parameters'].keys():
            defaultVDict = dict(zip(inspect.getfullargspec(generate_ppsds).args[1:], 
                                    inspect.getfullargspec(generate_ppsds).defaults))
            defaultVDict['ppsd_kwargs'] = ppsd_kwargs
            for k, v in hvsr_data['processing_parameters']['generate_ppsds'].items():
                # Manual input to function overrides the imported parameter values
                if not isinstance(v, (HVSRData, HVSRBatch)) and (k in orig_args.keys()) and (orig_args[k]==defaultVDict[k]):
                    orig_args[k] = v

    verbose = orig_args['verbose']
    ppsd_kwargs = orig_args['ppsd_kwargs']

    if (verbose and isinstance(hvsr_data, HVSRBatch)) or (verbose and not hvsr_data['batch']):
        if isinstance(hvsr_data, HVSRData) and hvsr_data['batch']:
            pass
        else:
            print('\nGenerating Probabilistic Power Spectral Densities (generate_ppsds())')
            print('\tUsing the following parameters:')
            for key, value in orig_args.items():
                if key=='hvsr_data':
                    pass
                else:
                    print('\t  {}={}'.format(key, value))
            print()

    #Site is in the keys anytime it's not batch
    if isinstance(hvsr_data, HVSRBatch):
        #If running batch, we'll loop through each one
        for site_name in hvsr_data.keys():
            args = orig_args.copy() #Make a copy so we don't accidentally overwrite
            individual_params = hvsr_data[site_name] #Get what would normally be the "hvsr_data" variable for each site
            args['hvsr_data'] = individual_params #reset the hvsr_data parameter we originally read in to an individual site hvsr_data
            #args['hvsr_data']['batch'] = False #Set to false, since only running this time
            if hvsr_data[site_name]['ProcessingStatus']['OverallStatus']:
                try:
                    hvsr_data[site_name] = _generate_ppsds_batch(**args) #Call another function, that lets us run this function again
                except:
                    hvsr_data[site_name]['ProcessingStatus']['PPSDStatus']=False
                    hvsr_data[site_name]['ProcessingStatus']['OverallStatus'] = False                     
            else:
                hvsr_data[site_name]['ProcessingStatus']['PPSDStatus']=False
                hvsr_data[site_name]['ProcessingStatus']['OverallStatus'] = False                
            
            try:
                sprit_gui.update_progress_bars(prog_percent=5)
            except Exception as e:
                pass
                #print(e)
        return hvsr_data
    else:
        paz = hvsr_data['paz']
        stream = hvsr_data['stream']

        #Get ppsds of e component
        eStream = stream.select(component='E')
        estats = eStream.traces[0].stats
        ppsdE = PPSD(estats, paz['E'],  **ppsd_kwargs)
        ppsdE.add(eStream)

        #Get ppsds of n component
        nStream = stream.select(component='N')
        nstats = nStream.traces[0].stats
        ppsdN = PPSD(nstats, paz['N'], **ppsd_kwargs)
        ppsdN.add(nStream)

        #Get ppsds of z component
        zStream = stream.select(component='Z')
        zstats = zStream.traces[0].stats
        ppsdZ = PPSD(zstats, paz['Z'], **ppsd_kwargs)
        ppsdZ.add(zStream)

        ppsds = {'Z':ppsdZ, 'N':ppsdN, 'E':ppsdE}

        #Add to the input dictionary, so that some items can be manipulated later on, and original can be saved
        hvsr_data['ppsds_obspy'] = ppsds
        hvsr_data['ppsds'] = {}
        anyKey = list(hvsr_data['ppsds_obspy'].keys())[0]
        
        #Get ppsd class members
        members = [mems for mems in dir(hvsr_data['ppsds_obspy'][anyKey]) if not callable(mems) and not mems.startswith("_")]
        hvsr_data['ppsds']['Z'] = {}
        hvsr_data['ppsds']['E'] = {}
        hvsr_data['ppsds']['N'] = {}
        
        #Get lists/arrays so we can manipulate data later and copy everything over to main 'ppsds' subdictionary (convert lists to np.arrays for consistency)
        listList = ['times_data', 'times_gaps', 'times_processed','current_times_used', 'psd_values'] #Things that need to be converted to np.array first, for consistency
        timeKeys= ['times_processed','current_times_used','psd_values']
        timeDiffWarn = True
        dfList = []
        time_data = {}
        time_dict = {}
        for m in members:
            hvsr_data['ppsds']['Z'][m] = getattr(hvsr_data['ppsds_obspy']['Z'], m)
            hvsr_data['ppsds']['E'][m] = getattr(hvsr_data['ppsds_obspy']['E'], m)
            hvsr_data['ppsds']['N'][m] = getattr(hvsr_data['ppsds_obspy']['N'], m)
            if m in listList:
               
                hvsr_data['ppsds']['Z'][m] = np.array(hvsr_data['ppsds']['Z'][m])
                hvsr_data['ppsds']['E'][m] = np.array(hvsr_data['ppsds']['E'][m])
                hvsr_data['ppsds']['N'][m] = np.array(hvsr_data['ppsds']['N'][m])
            
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
                    
            #Make sure number of time windows is the same between PPSDs (this can happen with just a few slightly different number of samples)
            if m in timeKeys:
                if str(m) != 'times_processed':
                    time_data[str(m)] = (hvsr_data['ppsds']['Z'][m], hvsr_data['ppsds']['E'][m], hvsr_data['ppsds']['N'][m])

                #print(m, hvsr_data['ppsds']['Z'][m])

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
                    timeDiffWarn = False #So we only do this warning once, even though there are multiple arrays that need to be trimmed

        for i, currTStep in enumerate(cTimeIndList):
            colList = []
            currTStepList = []
            colList.append('TimesProcessed_Obspy')
            currTStepList.append(common_times[i])
            for tk in time_data.keys():
                colList.append(str(tk)+'_Z')
                colList.append(str(tk)+'_E')
                colList.append(str(tk)+'_N')
                currTStepList.append(time_data[tk][0][currTStep[0]])#z
                currTStepList.append(time_data[tk][1][currTStep[1]])#e
                currTStepList.append(time_data[tk][2][currTStep[2]])#n

            dfList.append(currTStepList)
            
        hvsrDF = pd.DataFrame(dfList, columns=colList)
        hvsrDF['TimesProcessed_ObspyEnd'] = hvsrDF['TimesProcessed_Obspy'] + ppsd_kwargs['ppsd_length']
        
        #Add other times (for start times)
        def convert_to_datetime(obspyUTCDateTime):
            return obspyUTCDateTime.datetime.replace(tzinfo=datetime.timezone.utc)

        def convert_to_mpl_dates(obspyUTCDateTime):
            return obspyUTCDateTime.matplotlib_date

        hvsrDF['TimesProcessed'] = hvsrDF['TimesProcessed_Obspy'].apply(convert_to_datetime)     
        hvsrDF['TimesProcessed_End'] = hvsrDF['TimesProcessed'] + datetime.timedelta(days=0,seconds=ppsd_kwargs['ppsd_length'])
        hvsrDF['TimesProcessed_MPL'] = hvsrDF['TimesProcessed_Obspy'].apply(convert_to_mpl_dates)
        hvsrDF['TimesProcessed_MPLEnd'] = hvsrDF['TimesProcessed_MPL'] + (ppsd_kwargs['ppsd_length']/86400)
        
        hvsrDF['Use'] = True
        hvsrDF['Use']=hvsrDF['Use'].astype(bool)
        for gap in hvsr_data['ppsds']['Z']['times_gaps']:
            hvsrDF['Use'] = (hvsrDF['TimesProcessed_MPL'].gt(gap[1].matplotlib_date))| \
                            (hvsrDF['TimesProcessed_MPLEnd'].lt(gap[0].matplotlib_date))# | \
        
        hvsrDF['Use'] = hvsrDF['Use'].astype(bool)
        if 'xwindows_out' in hvsr_data.keys():
            for window in hvsr_data['xwindows_out']:
                hvsrDF['Use'] = (hvsrDF['TimesProcessed_MPL'][hvsrDF['Use']].lt(window[0]) & hvsrDF['TimesProcessed_MPLEnd'][hvsrDF['Use']].lt(window[0]) )| \
                        (hvsrDF['TimesProcessed_MPL'][hvsrDF['Use']].gt(window[1]) & hvsrDF['TimesProcessed_MPLEnd'][hvsrDF['Use']].gt(window[1]))
            hvsrDF['Use'] = hvsrDF['Use'].astype(bool)
            
        hvsrDF.set_index('TimesProcessed', inplace=True)
        hvsr_data['hvsr_df'] = hvsrDF
        #Create dict entry to keep track of how many outlier hvsr curves are removed (2-item list with [0]=current number, [1]=original number of curves)
        hvsr_data['tsteps_used'] = [hvsrDF['Use'].sum(), hvsrDF['Use'].shape[0]]
        #hvsr_data['tsteps_used'] = [hvsr_data['ppsds']['Z']['times_processed'].shape[0], hvsr_data['ppsds']['Z']['times_processed'].shape[0]]
        
        hvsr_data['tsteps_used'][0] = hvsr_data['ppsds']['Z']['current_times_used'].shape[0]
        
        hvsr_data = sprit_utils.make_it_classy(hvsr_data)
    
        if 'processing_parameters' not in hvsr_data.keys():
            hvsr_data['processing_parameters'] = {}
        hvsr_data['processing_parameters']['generate_ppsds'] = {}
        for key, value in orig_args.items():
            hvsr_data['processing_parameters']['generate_ppsds'][key] = value
    hvsr_data['ProcessingStatus']['PPSDStatus'] = True
    hvsr_data = _check_processing_status(hvsr_data, start_time=start_time, func_name=inspect.stack()[0][3], verbose=verbose)
    return hvsr_data

#Gets the metadata for Raspberry Shake, specifically for 3D v.7
def get_metadata(params, write_path='', update_metadata=True, source=None, **read_inventory_kwargs):
    """Get metadata and calculate or get paz parameter needed for PPSD

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
    invPath = params['metapath']
    raspShakeInstNameList = ['raspberry shake', 'shake', 'raspberry', 'rs', 'rs3d', 'rasp. shake', 'raspshake']
    trominoNameList = ['tromino', 'trom', 'trm', 't']
    if params['instrument'].lower() in raspShakeInstNameList:
        if update_metadata:
            params = _update_shake_metadata(filepath=invPath, params=params, write_path=write_path)
        params = _read_RS_Metadata(params, source=source)
    elif params['instrument'].lower() in trominoNameList:
        params['paz'] = {'Z':{}, 'E':{}, 'N':{}}
        #ALL THESE VALUES ARE PLACEHOLDERS, taken from RASPBERRY SHAKE! (Needed for PPSDs)
        params['paz']['Z'] = {'sensitivity': 360000000.0,
                              'gain': 360000000.0,
                              'poles': [(-1+0j), (-3.03+0j), (-3.03+0j), (-666.67+0j)],  
                              'zeros': [0j, 0j, 0j]}
        params['paz']['E'] =  params['paz']['Z']
        params['paz']['N'] =  params['paz']['Z']

        channelObj_Z = obspy.core.inventory.channel.Channel(code='BHZ', location_code='00', latitude=params['params']['latitude'], 
                                                longitude=params['params']['longitude'], elevation=params['params']['elevation'], depth=params['params']['depth'], 
                                                azimuth=0, dip=90, types=None, external_references=None, 
                                                sample_rate=None, sample_rate_ratio_number_samples=None, sample_rate_ratio_number_seconds=None,
                                                storage_format=None, clock_drift_in_seconds_per_sample=None, calibration_units=None, 
                                                calibration_units_description=None, sensor=None, pre_amplifier=None, data_logger=None,
                                                equipments=None, response=None, description=None, comments=None, start_date=None, end_date=None, 
                                                restricted_status=None, alternate_code=None, historical_code=None, data_availability=None, 
                                                identifiers=None, water_level=None, source_id=None)
        channelObj_E = obspy.core.inventory.channel.Channel(code='BHE', location_code='00', latitude=params['params']['latitude'], 
                                                longitude=params['params']['longitude'], elevation=params['params']['elevation'], depth=params['params']['depth'], 
                                                azimuth=90, dip=0) 
        
        channelObj_N = obspy.core.inventory.channel.Channel(code='BHN', location_code='00', latitude=params['params']['latitude'], 
                                                longitude=params['params']['longitude'], elevation=params['params']['elevation'], depth=params['params']['depth'], 
                                                azimuth=0, dip=0) 
        
        siteObj = obspy.core.inventory.util.Site(name=params['params']['site'], description=None, town=None, county=None, region=None, country=None)
        stationObj = obspy.core.inventory.station.Station(code='TZ', latitude=params['params']['latitude'], longitude=params['params']['longitude'], 
                                            elevation=params['params']['elevation'], channels=[channelObj_Z, channelObj_E, channelObj_N], site=siteObj, 
                                            vault=None, geology=None, equipments=None, operators=None, creation_date=datetime.datetime.today(),
                                            termination_date=None, total_number_of_channels=None, 
                                            selected_number_of_channels=None, description='Estimated data for Tromino, this is NOT from the manufacturer',
                                            comments=None, start_date=None, 
                                            end_date=None, restricted_status=None, alternate_code=None, historical_code=None, 
                                            data_availability=None, identifiers=None, water_level=None, source_id=None)

        network = [obspy.core.inventory.network.Network(code='TROM', stations=[stationObj], total_number_of_stations=None, 
                                            selected_number_of_stations=None, description=None, comments=None, start_date=None, 
                                            end_date=None, restricted_status=None, alternate_code=None, historical_code=None, 
                                            data_availability=None, identifiers=None, operators=None, source_id=None)]
        
        params['inv'] = obspy.Inventory(networks=network)
    else:
        if not invPath:
            pass #if invPath is None
        elif not pathlib.Path(invPath).exists() or invPath=='':
            warnings.warn(f"The metapath parameter was not specified correctly. Returning original params value {params['metapath']}")
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

#Get or print report
def get_report(hvsr_results, report_format='print', plot_type='HVSR p ann C+ p ann Spec', export_path=None, csv_overwrite_opt='append', no_output=False, verbose=False):    
    """Get a report of the HVSR analysis in a variety of formats.
        
    Parameters
    ----------
    hvsr_results : dict
        Dictionary containing all the information about the processed hvsr data
    report_format : {'csv', 'print', plot}
        Format in which to print or export the report.
        The following report_formats return the following items in the following attributes:
            - 'plot': hvsr_results['Print_Report'] as a str str
            - 'print': hvsr_results['HV_Plot'] - matplotlib.Figure object
            - 'csv':  hvsr_results['CSV_Report']- pandas.DataFrame object
                - list/tuple - a list or tuple of the above objects, in the same order they are in the report_format list
    plot_type : str, default = 'HVSR p ann C+ p ann Spec
        What type of plot to plot, if 'plot' part of report_format input
    export_path : None, bool, or filepath, default = None
        If None or False, does not export; if True, will export to same directory as the datapath parameter in the input_params() function.
        Otherwise, it should be a string or path object indicating where to export results. May be a file or directory.
        If a directory is specified, the filename will be  "<site_name>_<acq_date>_<UTC start time>-<UTC end time>". The suffix defaults to png for report_format="plot", csv for 'csv', and does not export if 'print.'
    csv_overwrite_opts : str, {'append', 'overwrite', 'keep/rename'}
        How to handle csv report outputs if the designated csv output file already exists. By default, appends the new information to the end of the existing file.
    no_output : bool, default=False
        If True, only reads output to appropriate attribute of data class (ie, print does not print, only reads text into variable). If False, performs as normal.
    verbose : bool, default=True
        Whether to print the results to terminal. This is the same output as report_format='print', and will not repeat if that is already selected

    Returns
    -------
    sprit.HVSRData
    """
    orig_args = locals().copy() #Get the initial arguments

    # Update with processing parameters specified previously in input_params, if applicable
    if 'processing_parameters' in hvsr_results.keys():
        if 'get_report' in hvsr_results['processing_parameters'].keys():
            for k, v in hvsr_results['processing_parameters']['get_report'].items():
                defaultVDict = dict(zip(inspect.getfullargspec(get_report).args[1:], 
                                        inspect.getfullargspec(get_report).defaults))
                # Manual input to function overrides the imported parameter values
                if (not isinstance(v, (HVSRData, HVSRBatch))) and (k in orig_args.keys()) and (orig_args[k]==defaultVDict[k]):
                    orig_args[k] = v

    report_format = orig_args['report_format']
    plot_type = orig_args['plot_type']
    export_path = orig_args['export_path']
    csv_overwrite_opt = orig_args['csv_overwrite_opt']
    no_output = orig_args['no_output']
    verbose = orig_args['verbose']
    
    if (verbose and isinstance(hvsr_results, HVSRBatch)) or (verbose and not hvsr_results['batch']):
        if isinstance(hvsr_results, HVSRData) and hvsr_results['batch']:
            pass
        else:
            print('\nGetting HVSR Report: get_report()')
            print('\tUsing the following parameters:')
            for key, value in orig_args.items():
                if key=='params':
                    pass
                else:
                    print('\t  {}={}'.format(key, value))
            print()

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
            if hvsr_results[site_name]['ProcessingStatus']['OverallStatus']:
                try:
                    hvsr_results[site_name] = _get_report_batch(**args) #Call another function, that lets us run this function again
                except:
                    hvsr_results[site_name] = hvsr_results[site_name]
            else:
                hvsr_results[site_name] = hvsr_results[site_name]
        
        combined_csvReport = pd.DataFrame()
        for site_name in hvsr_results.keys():
            if 'CSV_Report' in hvsr_results[site_name].keys():
                combined_csvReport = pd.concat([combined_csvReport, hvsr_results[site_name]['CSV_Report']], ignore_index=True, join='inner')
        
        if export_path is not None:
            if export_path is True:
                if pathlib.Path(hvsr_results['input_params']['datapath']) in sampleFileKeyMap.values():
                    csvExportPath = pathlib.Path(os.getcwd())
                else:
                    csvExportPath = pathlib.Path(hvsr_results['input_params']['datapath'])
            elif pathlib.Path(export_path).is_dir():
                csvExportPath = export_path
            elif pathlib.Path(export_path).is_file():
                csvExportPath = export_path.parent
            else:
                csvExportPath = pathlib.Path(hvsr_results[site_name].datapath)
                if csvExportPath.is_dir():
                    pass
                else:
                    csvExportPath = csvExportPath.parent
                
            combined_csvReport.to_csv(csvExportPath, index=False)
        
    else:       
        #if 'BestPeak' in hvsr_results.keys() and 'PassList' in hvsr_results['BestPeak'].keys():
        try:
            curvTestsPassed = (hvsr_results['BestPeak']['PassList']['WindowLengthFreq.'] +
                                hvsr_results['BestPeak']['PassList']['SignificantCycles']+
                                hvsr_results['BestPeak']['PassList']['LowCurveStDevOverTime'])
            curvePass = curvTestsPassed > 2
            
            #Peak Pass?
            peakTestsPassed = ( hvsr_results['BestPeak']['PassList']['PeakProminenceBelow'] +
                        hvsr_results['BestPeak']['PassList']['PeakProminenceAbove']+
                        hvsr_results['BestPeak']['PassList']['PeakAmpClarity']+
                        hvsr_results['BestPeak']['PassList']['FreqStability']+
                        hvsr_results['BestPeak']['PassList']['PeakStability_FreqStD']+
                        hvsr_results['BestPeak']['PassList']['PeakStability_AmpStD'])
            peakPass = peakTestsPassed >= 5
        except Exception as e:
            errMsg= 'No BestPeak identified. Check peak_freq_range or hvsr_band or try to remove bad noise windows using remove_noise() or change processing parameters in process_hvsr() or generate_ppsds(). Otherwise, data may not be usable for HVSR.'
            print(errMsg)
            print(e)
            return hvsr_results
            #raise RuntimeError('No BestPeak identified. Check peak_freq_range or hvsr_band or try to remove bad noise windows using remove_noise() or change processing parameters in process_hvsr() or generate_ppsds(). Otherwise, data may not be usable for HVSR.')
    
        if isinstance(report_format, (list, tuple)):
            pass
        else:
            #We will use a loop later even if it's just one report type, so reformat to prepare for for loop
            allList = [':', 'all']
            if report_format.lower() in allList:
                report_format = ['print', 'csv', 'plot']
            else:
                report_format = [report_format]   

        def export_report(export_obj, _export_path, _rep_form):
            if _export_path is None:
                return
            else:
                if _rep_form == 'csv':
                    ext = '.csv'
                elif _rep_form =='plot':
                    ext='.png'
                else:
                    ext=''
                    
                sitename=hvsr_results['input_params']['site']#.replace('.', '-')
                fname = f"{sitename}_{hvsr_results['input_params']['acq_date']}_{str(hvsr_results['input_params']['starttime'].time)[:5]}-{str(hvsr_results['input_params']['endtime'].time)[:5]}{ext}"
                fname = fname.replace(':', '')

                if _export_path==True:
                    #Check so we don't write in sample directory
                    if pathlib.Path(hvsr_results['input_params']['datapath']) in sampleFileKeyMap.values():
                        if pathlib.Path(os.getcwd()) in sampleFileKeyMap.values(): #Just in case current working directory is also sample directory
                            inFile = pathlib.Path.home() #Use the path to user's home if all else fails
                        else:
                            inFile = pathlib.Path(os.getcwd())
                    else:
                        inFile = pathlib.Path(hvsr_results['input_params']['datapath'])
                                 
                    if inFile.is_dir():
                        outFile = inFile.joinpath(fname)
                    else:
                        outFile = inFile.with_name(fname)
                else:
                    if pathlib.Path(_export_path).is_dir():
                        outFile = pathlib.Path(_export_path).joinpath(fname)
                    else:
                        outFile=pathlib.Path(_export_path)

            if _rep_form == 'csv':
                if outFile.exists():
                    existFile = pd.read_csv(outFile)
                    if csv_overwrite_opt.lower() == 'append':
                        export_obj = pd.concat([existFile, export_obj], ignore_index=True, join='inner')
                    elif csv_overwrite_opt.lower() == 'overwrite':
                        pass
                    else:# csv_overwrite_opt.lower() in ['keep', 'rename']:
                        fileNameExists = True
                        i=1
                        while fileNameExists:
                            outFile = outFile.with_stem(f"{outFile.stem}_{i}")
                            i+=1
                            if not outFile.exists():
                                fileNameExists = False
                try:
                    print(f'\nSaving csv data to: {outFile}')
                    export_obj.to_csv(outFile, index_label='ID')
                except:
                    warnings.warn("Report not exported. \n\tDataframe to be exported as csv has been saved in hvsr_results['BestPeak']['Report']['CSV_Report]", category=RuntimeWarning)
            elif _rep_form =='plot':
                if verbose:
                    print(f'\nSaving plot to: {outFile}')
                plt.scf = export_obj
                plt.savefig(outFile)
            return 

        def report_output(_report_format, _plot_type='HVSR p ann C+ p ann Spec', _export_path=None, _no_output=False, verbose=False):
            if _report_format=='print':
                #Print results

                #Make separators for nicely formatted print output
                sepLen = 99
                siteSepSymbol = '='
                intSepSymbol = u"\u2013"
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
                report_string_list.append(f"\tLocation : {hvsr_results['input_params']['longitude']}, {hvsr_results['input_params']['latitude']}")
                report_string_list.append(f"\tElevation: {hvsr_results['input_params']['elevation']}")
                report_string_list.append('')
                report_string_list.append(internalSeparator)
                report_string_list.append('')
                if 'BestPeak' not in hvsr_results.keys():
                    report_string_list.append('\tNo identifiable BestPeak was present between {} for {}'.format(hvsr_results['input_params']['hvsr_band'], hvsr_results['input_params']['site']))
                else:
                    report_string_list.append('\t{0:.3f} Hz Peak Frequency'.format(hvsr_results['BestPeak']['f0']))        
                    if curvePass and peakPass:
                        report_string_list.append('\t  {} Curve at {} Hz passed quality checks! ☺ :D'.format(sprit_utils.check_mark(), round(hvsr_results['BestPeak']['f0'],3)))
                    else:
                        report_string_list.append('\t  {} Peak at {} Hz did NOT pass quality checks ☹:('.format(sprit_utils.x_mark(), round(hvsr_results['BestPeak']['f0'],3)))            
                    report_string_list.append('')
                    report_string_list.append(internalSeparator)
                    report_string_list.append('')

                    justSize=34
                    #Print individual results
                    report_string_list.append('\tCurve Tests: {}/3 passed (3/3 needed)'.format(curvTestsPassed))
                    report_string_list.append(f"\t\t {hvsr_results['BestPeak']['Report']['Lw'][-1]}"+" Length of processing windows".ljust(justSize)+f"{hvsr_results['BestPeak']['Report']['Lw']}")
                    report_string_list.append(f"\t\t {hvsr_results['BestPeak']['Report']['Nc'][-1]}"+" Number of significant cycles".ljust(justSize)+f"{hvsr_results['BestPeak']['Report']['Nc']}")
                    report_string_list.append(f"\t\t {hvsr_results['BestPeak']['Report']['σ_A(f)'][-1]}"+" Small H/V StDev over time".ljust(justSize)+f"{hvsr_results['BestPeak']['Report']['σ_A(f)']}")

                    report_string_list.append('')
                    report_string_list.append("\tPeak Tests: {}/6 passed (5/6 needed)".format(peakTestsPassed))
                    report_string_list.append(f"\t\t {hvsr_results['BestPeak']['Report']['A(f-)'][-1]}"+" Peak is prominent below".ljust(justSize)+f"{hvsr_results['BestPeak']['Report']['A(f-)']}")
                    report_string_list.append(f"\t\t {hvsr_results['BestPeak']['Report']['A(f+)'][-1]}"+" Peak is prominent above".ljust(justSize)+f"{hvsr_results['BestPeak']['Report']['A(f+)']}")
                    report_string_list.append(f"\t\t {hvsr_results['BestPeak']['Report']['A0'][-1]}"+" Peak is large".ljust(justSize)+f"{hvsr_results['BestPeak']['Report']['A0']}")
                    if hvsr_results['BestPeak']['PassList']['FreqStability']:
                        res = sprit_utils.check_mark()
                    else:
                        res = sprit_utils.x_mark()
                    report_string_list.append(f"\t\t {res}"+ " Peak freq. is stable over time".ljust(justSize)+ f"{hvsr_results['BestPeak']['Report']['P-'][:5]} and {hvsr_results['BestPeak']['Report']['P+'][:-1]} {res}")
                    report_string_list.append(f"\t\t {hvsr_results['BestPeak']['Report']['Sf'][-1]}"+" Stability of peak (Freq. StDev)".ljust(justSize)+f"{hvsr_results['BestPeak']['Report']['Sf']}")
                    report_string_list.append(f"\t\t {hvsr_results['BestPeak']['Report']['Sa'][-1]}"+" Stability of peak (Amp. StDev)".ljust(justSize)+f"{hvsr_results['BestPeak']['Report']['Sa']}")
                report_string_list.append('')
                report_string_list.append(f"Calculated using {hvsr_results['hvsr_df']['Use'].sum()}/{hvsr_results['hvsr_df']['Use'].count()} time windows".rjust(sepLen-1))
                report_string_list.append(extSiteSeparator)
                #report_string_list.append(endSiteSeparator)
                #report_string_list.append(extSiteSeparator)
                report_string_list.append('')
                
                reportStr=''
                #Now print it
                for line in report_string_list:
                    reportStr = reportStr+'\n'+line

                if not _no_output:
                    print(reportStr)

                export_report(export_obj=reportStr, _export_path=_export_path, _rep_form=_report_format)
                hvsr_results['BestPeak']['Report']['Print_Report'] = reportStr
                hvsr_results['Print_Report'] = reportStr

            elif _report_format=='csv':
                import pandas as pd
                pdCols = ['Site Name', 'Acq_Date', 'Longitude', 'Latitide', 'Elevation', 'PeakFrequency', 
                        'WindowLengthFreq.','SignificantCycles','LowCurveStDevOverTime',
                        'PeakProminenceBelow','PeakProminenceAbove','PeakAmpClarity','FreqStability', 'PeakStability_FreqStD','PeakStability_AmpStD', 'PeakPasses']
                d = hvsr_results
                criteriaList = []
                for p in hvsr_results['BestPeak']["PassList"]:
                    criteriaList.append(hvsr_results['BestPeak']["PassList"][p])
                criteriaList.append(hvsr_results['BestPeak']["PeakPasses"])
                dfList = [[d['input_params']['site'], d['input_params']['acq_date'], d['input_params']['longitude'], d['input_params']['latitude'], d['input_params']['elevation'], round(d['BestPeak']['f0'], 3)]]
                dfList[0].extend(criteriaList)
                outDF = pd.DataFrame(dfList, columns=pdCols)

                if verbose:
                    print('\nCSV Report:\n')
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

                try:
                    export_report(export_obj=outDF, _export_path=_export_path, _rep_form=_report_format)
                except:
                    print("Error in exporting csv report. CSV not exported")
                hvsr_results['BestPeak']['Report']['CSV_Report'] = outDF
                hvsr_results['CSV_Report'] = outDF
                        
            elif _report_format=='plot':
                fig_ax = plot_hvsr(hvsr_results, plot_type=_plot_type, show=False, return_fig=True)

                export_report(export_obj=fig_ax[0], _export_path=_export_path, _rep_form=_report_format)
                hvsr_results['BestPeak']['Report']['HV_Plot']=hvsr_results['HV_Plot']=fig_ax

                print('\nPlot of data report:')
                plt.show()
                
            return hvsr_results

        for i, rep_form in enumerate(report_format):
            if isinstance(export_path, (list, tuple)):
                if not isinstance(report_format, (list, tuple)):
                    warnings.warn('export_path is a list/tuple and report_format is not. This may result in unexpected behavior.')
                if isinstance(report_format, (list, tuple)) and isinstance(export_path, (list, tuple)) and len(report_format) != len(export_path):
                    warnings.warn('export_path and report_format are both lists or tuples, but they are not the same length. This may result in unexpected behavior.')
            
                exp_path = export_path[i]
            else:
                exp_path = export_path
            hvsr_results = report_output(_report_format=rep_form, _plot_type=plot_type, _export_path=exp_path, _no_output=no_output, verbose=verbose)

        hvsr_results['processing_parameters']['get_report'] = {}
        for key, value in orig_args.items():
            hvsr_results['processing_parameters']['get_report'][key] = value

    return hvsr_results

#Import data
def import_data(import_filepath, data_format='pickle'):
    """Function to import .hvsr (or other extension) data exported using export_data() function

    Parameters
    ----------
    import_filepath : str or path object
        Filepath of file created using export_data() function. This is usually a pickle file with a .hvsr extension
    data_format : str, default='pickle'
        Type of format data is in. Currently, only 'pickle' supported. Eventually, json or other type may be supported, by default 'pickle'.

    Returns
    -------
    HVSRData or HVSRBatch object
    """
    if data_format=='pickle':
        with open(import_filepath, 'rb') as f:
            dataIN = pickle.load(f)
    else:
        dataIN = import_filepath
    return dataIN

#Import settings
def import_settings(settings_import_path, settings_import_type='instrument', verbose=False):

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
            settings_import_path = sprit_utils.checkifpath(settings_import_path)
            if not settings_import_path.is_dir():
                raise RuntimeError(f'settings_import_type={settings_import_type}, but settings_import_path is not list/tuple or filepath to directory')
            else:
                instFile = settings_import_path.glob('*.inst')
                procFile = settings_import_path.glob('*.proc')
    return settingsDict

#Define input parameters
def input_params(datapath,
                site='HVSR Site',
                network='AM', 
                station='RAC84', 
                loc='00', 
                channels=['EHZ', 'EHN', 'EHE'],
                acq_date=str(datetime.datetime.now().date()),
                starttime = '00:00:00.00',
                endtime = '23:59:59.999999',
                tzone = 'UTC',
                xcoord = -88.2290526,
                ycoord =  40.1012122,
                elevation = 755,
                input_crs='EPSG:4326',#4269 is NAD83, defautling to WGS
                output_crs='EPSG:4326',
                elev_unit = 'feet',
                depth = 0,
                instrument = 'Raspberry Shake',
                metapath = None,
                hvsr_band = [0.4, 40],
                peak_freq_range=[0.4, 40],
                processing_parameters={},
                verbose=False
                ):
    """Function for designating input parameters for reading in and processing data
    
    Parameters
    ----------
    datapath : str or pathlib.Path object
        Filepath of data. This can be a directory or file, but will need to match with what is chosen later as the source parameter in fetch_data()
    site : str, default="HVSR Site"
        Site name as designated by user for ease of reference. Used for plotting titles, filenames, etc.
    network : str, default='AM'
        The network designation of the seismometer. This is necessary for data from Raspberry Shakes. 'AM' is for Amateur network, which fits Raspberry Shakes.
    station : str, default='RAC84'
        The station name of the seismometer. This is necessary for data from Raspberry Shakes.
    loc : str, default='00'
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
        Longitude (or easting, or, generally, X coordinate) of data point, in Coordinate Reference System (CRS) designated by input_crs. Currently only used in csv output, but will likely be used in future for mapping/profile purposes.
    ycoord : float, default=40.1012122
        Latitute (or northing, or, generally, X coordinate) of data point, in Coordinate Reference System (CRS) designated by input_crs. Currently only used in csv output, but will likely be used in future for mapping/profile purposes.
    input_crs : str or other format read by pyproj, default='EPSG:4326'
        Coordinate reference system of input data, as used by pyproj.CRS.from_user_input()
    output_crs : str or other format read by pyproj, default='EPSG:4326'
        Coordinate reference system to which input data will be transformed, as used by pyproj.CRS.from_user_input()
    elevation : float, default=755
        Surface elevation of data point. Not currently used (except in csv output), but will likely be used in the future.
    depth : float, default=0
        Depth of seismometer. Not currently used, but will likely be used in the future.
    instrument : str or list {'Raspberry Shake')
        Instrument from which the data was acquired. 
    metapath : str or pathlib.Path object, default=None
        Filepath of metadata, in format supported by obspy.read_inventory. If default value of None, will read from resources folder of repository (only supported for Raspberry Shake).
    hvsr_band : list, default=[0.4, 40]
        Two-element list containing low and high "corner" frequencies (in Hz) for processing. This can specified again later.
    peak_freq_range : list or tuple, default=[0.4, 40]
        Two-element list or tuple containing low and high frequencies (in Hz) that are used to check for HVSR Peaks. This can be a tigher range than hvsr_band, but if larger, it will still only use the hvsr_band range.
    processing_parameters={} : dict or filepath, default={}
        If filepath, should point to a .proc json file with processing parameters (i.e, an output from sprit.export_settings()). 
        Note that this only applies to parameters for the functions: 'fetch_data', 'remove_noise', 'generate_ppsds', 'process_hvsr', 'check_peaks', and 'get_report.'
        If dictionary, dictionary containing nested dictionaries of function names as they key, and the parameter names/values as key/value pairs for each key. 
        If a function name is not present, or if a parameter name is not present, default values will be used.
        For example: 
            `{ 'fetch_data' : {'source':'batch', 'trim_dir':"/path/to/trimmed/data", 'export_format':'mseed', 'detrend':'spline', 'plot_input_stream':True, 'verbose':False, kwargs:{'kwargskey':'kwargsvalue'}} }`
    verbose : bool, default=False
        Whether to print output and results to terminal

    Returns
    -------
    params : sprit.HVSRData
        sprit.HVSRData class containing input parameters, including data file path and metadata path. This will be used as an input to other functions. If batch processing, params will be converted to batch type in fetch_data() step.

    """
    orig_args = locals().copy() #Get the initial arguments
    start_time = datetime.datetime.now()

    #Reformat times
    if type(acq_date) is datetime.datetime:
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
    
    if type(starttime) is str:
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
    
    starttime = str(date)+"T"+str(starttime)
    starttime = obspy.UTCDateTime(sprit_utils.format_time(starttime, tzone=tzone))
    
    if type(endtime) is str:
        if 'T' in endtime:
            date=endtime.split('T')[0]
            endtime = endtime.split('T')[1]
    elif type(endtime) is datetime.datetime:
        date = str(endtime.date())
        endtime = str(endtime.time())
    elif type(endtime) is datetime.time():
        endtime = str(endtime)

    endtime = str(date)+"T"+str(endtime)
    endtime = obspy.UTCDateTime(sprit_utils.format_time(endtime, tzone=tzone))

    acq_date = datetime.date(year=int(date.split('-')[0]), month=int(date.split('-')[1]), day=int(date.split('-')[2]))
    raspShakeInstNameList = ['raspberry shake', 'shake', 'raspberry', 'rs', 'rs3d', 'rasp. shake', 'raspshake']
    
    if output_crs is None:
        output_crs='EPSG:4326'

    if input_crs is None:
        input_crs = 'EPSG:4326'#Default to WGS84
    else:        
        input_crs = CRS.from_user_input(input_crs)
        output_crs = CRS.from_user_input(output_crs)

        coord_transformer = Transformer.from_crs(input_crs, output_crs, always_xy=True)
        xcoord, ycoord = coord_transformer.transform(xcoord, ycoord)

    #Add key/values to input parameter dictionary
    inputParamDict = {'site':site, 'net':network,'sta':station, 'loc':loc, 'cha':channels, 'instrument':instrument,
                    'acq_date':acq_date,'starttime':starttime,'endtime':endtime, 'timezone':'UTC', #Will be in UTC by this point
                    'longitude':xcoord,'latitude':ycoord,'elevation':elevation,'input_crs':input_crs, 'output_crs':output_crs,
                    'depth':depth, 'datapath': datapath, 'metapath':metapath, 'hvsr_band':hvsr_band, 'peak_freq_range':peak_freq_range,
                    'ProcessingStatus':{'InputParamsStatus':True, 'OverallStatus':True}
                    }
    
    #Replace any default parameter settings with those from json file of interest, potentially
    instrument_settings_dict = {}
    if pathlib.Path(instrument).exists():
        instrument_settings = import_settings(settings_import_path=instrument, settings_import_type='instrument', verbose=verbose)
        input_params_args = inspect.getfullargspec(input_params).args
        input_params_args.append('net')
        input_params_args.append('sta')
        for k, settings_value in instrument_settings.items():
            if k in input_params_args:
                instrument_settings_dict[k] = settings_value
        inputParamDict['instrument_settings'] = inputParamDict['instrument']
        inputParamDict.update(instrument_settings_dict)
    
    if instrument.lower() in raspShakeInstNameList:
        if metapath is None or metapath=='':
            metapath = pathlib.Path(pkg_resources.resource_filename(__name__, 'resources/rs3dv5plus_metadata.inv')).as_posix()
            inputParamDict['metapath'] = metapath
            #metapath = pathlib.Path(os.path.realpath(__file__)).parent.joinpath('/resources/rs3dv7_metadata.inv')

    for settingName in instrument_settings_dict.keys():
        if settingName in inputParamDict.keys():
            inputParamDict[settingName] = instrument_settings_dict[settingName]

    #Declare obspy here instead of at top of file for (for example) colab, where obspy first needs to be installed on environment
    if verbose:
        print('Gathering input parameters (input_params())')
        for key, value in inputParamDict.items():
            print('\t  {}={}'.format(key, value))
        print()

    if isinstance(processing_parameters, dict):
        inputParamDict['processing_parameters'] = processing_parameters
    else:
        processing_parameters = sprit_utils.checkifpath(processing_parameters)
        inputParamDict['processing_parameters'] = import_settings(processing_parameters, settings_import_type='processing', verbose=verbose)

    #Format everything nicely
    params = sprit_utils.make_it_classy(inputParamDict)
    params['ProcessingStatus']['InputParamsStatus'] = True
    params = _check_processing_status(params, start_time=start_time, func_name=inspect.stack()[0][3], verbose=verbose)
    return params

#Main function for plotting results
def plot_hvsr(hvsr_data, plot_type='HVSR ann p C+ ann p SPEC', use_subplots=True, fig=None, ax=None, return_fig=False,  save_dir=None, save_suffix='', show_legend=False, show=True, close_figs=False, clear_fig=True,**kwargs):
    """Function to plot HVSR data

    Parameters
    ----------
    hvsr_data : dict                  
        Dictionary containing output from process_hvsr function
    plot_type : str or list, default = 'HVSR ann p C+ ann p SPEC'
        The plot_type of plot(s) to plot. If list, will plot all plots listed
        - 'HVSR' - Standard HVSR plot, including standard deviation. Options are included below:
            - 'p' shows a vertical dotted line at frequency of the "best" peak
            - 'ann' annotates the frequency value of of the "best" peak
            - 'all' shows all the peaks identified in check_peaks() (by default, only the max is identified)
            - 't' shows the H/V curve for all time windows
                -'tp' shows all the peaks from the H/V curves of all the time windows
        - 'COMP' - plot of the PPSD curves for each individual component ("C" also works)
            - '+' (as a suffix in 'C+' or 'COMP+') plots C on a plot separate from HVSR (C+ is default, but without + will plot on the same plot as HVSR)
            - 'p' shows a vertical dotted line at frequency of the "best" peak
            - 'ann' annotates the frequency value of of the "best" peak
            - 'all' shows all the peaks identified in check_peaks() (by default, only the max is identified)
            - 't' shows the H/V curve for all time windows
        - 'SPEC' - spectrogram style plot of the H/V curve over time
            - 'p' shows a horizontal dotted line at the frequency of the "best" peak
            - 'ann' annotates the frequency value of the "best" peak
    use_subplots : bool, default = True
        Whether to output the plots as subplots (True) or as separate plots (False)
    fig : matplotlib.Figure, default = None
        If not None, matplotlib figure on which plot is plotted
    ax : matplotlib.Axis, default = None
        If not None, matplotlib axis on which plot is plotted
    return_fig : bool
        Whether to return figure and axis objects
    save_dir : str or None
        Directory in which to save figures
    save_suffix : str
        Suffix to add to end of figure filename(s), if save_dir is used
    show_legend : bool, default=False
        Whether to show legend in plot
    show : bool
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
            if hvsr_data[site_name]['ProcessingStatus']['OverallStatus']:
                try:
                    _hvsr_plot_batch(**args) #Call another function, that lets us run this function again
                except:
                    print(f"{site_name} not able to be plotted.")
    else:
        if clear_fig and fig is not None and ax is not None: #Intended use for tkinter
            #Clear everything
            for key in ax:
                ax[key].clear()
            for t in fig.texts:
                del t
            fig.clear()
        if close_figs:
            plt.close('all')

        compList = ['c', 'comp', 'component', 'components']
        specgramList = ['spec', 'specgram', 'spectrogram']
        hvsrList = ['hvsr', 'hv', 'h']

        hvsrInd = np.nan
        compInd = np.nan
        specInd = np.nan

        kList = plot_type.split(' ')
        for i, k in enumerate(kList):
            kList[i] = k.lower()

        #Get the plots in the right order, no matter how they were input (and ensure the right options go with the right plot)
        #HVSR index
        if len(set(hvsrList).intersection(kList)):
            for i, hv in enumerate(hvsrList):
                if hv in kList:
                    hvsrInd = kList.index(hv)
                    break
        #Component index
        #if len(set(compList).intersection(kList)):
        for i, c in enumerate(kList):
            if '+' in c and c[:-1] in compList:
                compInd = kList.index(c)
                break
            
        #Specgram index
        if len(set(specgramList).intersection(kList)):
            for i, sp in enumerate(specgramList):
                if sp in kList:
                    specInd = kList.index(sp)
                    break        

        indList = [hvsrInd, compInd, specInd]
        indListCopy = indList.copy()
        plotTypeList = ['hvsr', 'comp', 'spec']

        plotTypeOrder = []
        plotIndOrder = []

        lastVal = 0
        while lastVal != 99:
            firstInd = np.nanargmin(indListCopy)
            plotTypeOrder.append(plotTypeList[firstInd])
            plotIndOrder.append(indList[firstInd])
            lastVal = indListCopy[firstInd]
            indListCopy[firstInd] = 99 #just a high number

        plotTypeOrder.pop()
        plotIndOrder[-1]=len(kList)
        
        for i, p in enumerate(plotTypeOrder):
            pStartInd = plotIndOrder[i]
            pEndInd = plotIndOrder[i+1]
            plotComponents = kList[pStartInd:pEndInd]

            if use_subplots and i==0 and fig is None and ax is None:
                mosaicPlots = []
                for pto in plotTypeOrder:
                    mosaicPlots.append([pto])
                fig, ax = plt.subplot_mosaic(mosaicPlots, gridspec_kw={'hspace':0.3})
                axis = ax[p]
            elif use_subplots:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore") #Often warns about xlim when it is not an issue
                    ax[p].clear()
                axis = ax[p]
            else:
                fig, axis = plt.subplots()
                    
            if p == 'hvsr':
                _plot_hvsr(hvsr_data, fig=fig, ax=axis, plot_type=plotComponents, xtype='x_freqs', show_legend=show_legend, axes=ax, **kwargs)
            elif p=='comp':
                plotComponents[0] = plotComponents[0][:-1]
                _plot_hvsr(hvsr_data, fig=fig, ax=axis, plot_type=plotComponents, xtype='x_freqs', show_legend=show_legend, axes=ax, **kwargs)
            elif p=='spec':
                plottypeKwargs = {}
                for c in plotComponents:
                    plottypeKwargs[c] = True
                kwargs.update(plottypeKwargs)
                _plot_specgram_hvsr(hvsr_data, fig=fig, ax=axis, colorbar=False, **kwargs)
            else:
                warnings.warn('Plot type {p} not recognized', UserWarning)   

        windowsUsedStr = f"{hvsr_data['hvsr_df']['Use'].sum()}/{hvsr_data['hvsr_df'].shape[0]} windows used"
        fig.text(x=0.98, y=0.02, s=windowsUsedStr, ha='right', va='bottom', fontsize='x-small',
                 bbox=dict(facecolor='w', edgecolor=None, linewidth=0, alpha=1, pad=9))

        if show:
            fig.canvas.draw()
            
        if return_fig:
            return fig, ax
    return

#Plot Obspy Trace in axis using matplotlib
def plot_stream(stream, params, fig=None, axes=None, show_plot=False, ylim_std=0.75, return_fig=True):
    """Function to plot a stream of data with Z, E, N components using matplotlib. Similar to obspy.Stream.Plot(), but will be formatted differently and eventually more customizable.
    This is also used in various functions throughout the package.

    Parameters
    ----------
    stream : obspy.core.Stream.stream
        Obpsy stream of data with Z, E, N componenents
    params : HVSRData or HVSRBatch
        Data object with parameters relevant for creating plot
    fig : matplotlib.Figure, default=None
        Optional: if not None, matplotlib.Figure in which to plot the resulting figure (i.e., can be plotted in existing figure)
    axes : matplotlib.Axis, default=None
        Optional: if not None, matplotlib.Axis in which to plot the resulting figure (i.e., can be plotted in existing axis)
    show_plot : bool, default=False
        Whether to do matplotlib.pylot.show(), by default False
    ylim_std : float, default = 0.75
        Optional: the standard deviation of the data at which to clip the chart, by default 0.75
    return_fig : bool, default=True
        Optional: whether to return the figure, by default True

    Returns
    -------
    (matplotlib.Figure, matplotlib.Axes)
        Tuple containing the figure and axes of the resulting plot, only returned if return_fig = True
    """
    if fig is None and axes is None:
        fig, axes = plt.subplot_mosaic([['Z'],['N'],['E']], sharex=True, sharey=False)

    new_stream = stream.copy()
    #axis.plot(trace.times, trace.data)
    
    sTime = stream[0].stats.starttime
    timeList = {}
    mplTimes = {}

    #In case data is masked, need to split, decimate, then merge back together
    if isinstance(new_stream[0].data, np.ma.masked_array):
        new_stream = new_stream.split()
    new_stream.decimate(10)
    new_stream.merge()

    zStream = new_stream.select(component='Z')#[0]
    eStream = new_stream.select(component='E')#[0]
    nStream = new_stream.select(component='N')#[0]
    streams = [zStream, nStream, eStream]

    for st in streams:
        key = st[0].stats.component
        timeList[key] = []
        mplTimes[key] = []
        for tr in st:
            for t in np.ma.getdata(tr.times()):
                newt = sTime + t
                timeList[key].append(newt)
                mplTimes[key].append(newt.matplotlib_date)

    #Ensure that the min and max times for each component are the same
    for i, k in enumerate(mplTimes.keys()):
        currMin = np.min(list(map(np.min, mplTimes[k])))
        currMax = np.max(list(map(np.max, mplTimes[k])))

        if i == 0:
            xmin = currMin
            xmax = currMax
        else:
            if xmin > currMin:
                xmin = currMin
            if xmax < currMax:
                xmax = currMax

    axes['Z'].xaxis_date()
    axes['N'].xaxis_date()
    axes['E'].xaxis_date()

    #tTicks = mdates.MinuteLocator(interval=5)
    #axis.xaxis.set_major_locator(tTicks)
    axes['E'].xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0,60,5)))
    axes['E'].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    axes["E"].xaxis.set_minor_locator(mdates.MinuteLocator(interval=1))
    axes["E"].tick_params(axis='x', labelsize=8)
    

    streams = [zStream.merge(method=1), 
               nStream.merge(method=1), 
               eStream.merge(method=1)]

    for st in streams:
        for i, tr in enumerate(st):
            key = tr.stats.component
            if key == 'Z':
                C='k'
            elif key=='N':
                C='r'
            else:
                C='b'
            axes[key].plot(mplTimes[key], tr.data, color=C, linewidth=0.15)


    axes['Z'].set_ylabel('Z')
    axes['N'].set_ylabel('N')
    axes['E'].set_ylabel('E')
    
    #stDz = np.abs(np.nanstd(stream.select(component='Z')[0].data))
    #stDn = np.abs(np.nanstd(stream.select(component='N')[0].data))
    #stDe = np.abs(np.nanstd(stream.select(component='E')[0].data))
    #stD = max([stDz, stDn, stDe])
    
    for i, comp in enumerate(list(mplTimes.keys())):
        stD = np.abs(np.nanstd(np.ma.getdata(stream.select(component=comp)[0].data)))
        dmed = np.nanmedian(np.ma.getdata(stream.select(component=comp)[0].data))

        axes[comp].set_ylim([dmed-ylim_std*stD, dmed+ylim_std*stD])
        if xmin < 0:
            xmin=params['hvsr_band'][0]
        axes[comp].set_xlim([xmin, xmax])

    fig.suptitle(params['site'])
    
    day = "{}-{}-{}".format(stream[0].stats.starttime.year, stream[0].stats.starttime.month, stream[0].stats.starttime.day)
    axes['E'].set_xlabel('UTC Time \n'+ day)

    #plt.rcParams['figure.dpi'] = 100
    #plt.rcParams['figure.figsize'] = (5,4)
    
    #fig.tight_layout()
    fig.canvas.draw()

    if show_plot:
        plt.show()

    if return_fig:
        return fig, axes
    return                 

#Main function for processing HVSR Curve
def process_hvsr(hvsr_data, method=3, smooth=True, freq_smooth='konno ohmachi', f_smooth_width=40, resample=True, outlier_curve_rmse_percentile=False, verbose=False):
    """Process the input data and get HVSR data
    
    This is the main function that uses other (private) functions to do 
    the bulk of processing of the HVSR data and the data quality checks.

    Parameters
    ----------
    hvsr_data  : HVSRData or HVSRBatch
        Data object containing all the parameters input and generated by the user (usually, during sprit.input_params(), sprit.fetch_data(), sprit.generate_ppsds() and/or sprit.remove_noise()).
    method  : int or str, default=3
        Method to use for combining the horizontal components
            0) (not used)
            1) Diffuse field assumption, or 'DFA' (not currently implemented)
            2) 'Arithmetic Mean': H ≡ (HN + HE)/2
            3) 'Geometric Mean': H ≡ √HN · HE, recommended by the SESAME project (2004)
            4) 'Vector Summation': H ≡ √H2 N + H2 E
            5) 'Quadratic Mean': H ≡ √(H2 N + H2 E )/2
            6) 'Maximum Horizontal Value': H ≡ max {HN, HE}
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
    outlier_curve_rmse_percentile : bool, float, default = False
        If False, outlier curve removal is not carried out here. 
        If True, defaults to 98 (98th percentile). 
        Otherwise, float of percentile used as rmse_thresh of remove_outlier_curve().
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
            for k, v in hvsr_data['processing_parameters']['process_hvsr'].items():
                defaultVDict = dict(zip(inspect.getfullargspec(process_hvsr).args[1:], 
                                        inspect.getfullargspec(process_hvsr).defaults))
                # Manual input to function overrides the imported parameter values
                if (not isinstance(v, (HVSRData, HVSRBatch))) and (k in orig_args.keys()) and (orig_args[k]==defaultVDict[k]):
                    orig_args[k] = v
                    
    method = orig_args['method']
    smooth = orig_args['smooth']
    freq_smooth = orig_args['freq_smooth']
    f_smooth_width = orig_args['f_smooth_width']
    resample = orig_args['resample']
    outlier_curve_rmse_percentile = orig_args['outlier_curve_rmse_percentile']
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

    #First, divide up for batch or not
    #Site is in the keys anytime it's not batch
    if isinstance(hvsr_data, HVSRBatch):
        #If running batch, we'll loop through each site
        hvsr_out = {}
        for site_name in hvsr_data.keys():
            args = orig_args.copy() #Make a copy so we don't accidentally overwrite
            args['hvsr_data'] = hvsr_data[site_name] #Get what would normally be the "hvsr_data" variable for each site
            if hvsr_data[site_name]['ProcessingStatus']['OverallStatus']:
                try:
                    hvsr_out[site_name] = _process_hvsr_batch(**args) #Call another function, that lets us run this function again
                except:
                    hvsr_out = hvsr_data
                    hvsr_out[site_name]['ProcessingStatus']['HVStatus']=False
                    hvsr_out[site_name]['ProcessingStatus']['OverallStatus'] = False                    
            else:
                hvsr_out = hvsr_data
                hvsr_out[site_name]['ProcessingStatus']['HVStatus']=False
                hvsr_out[site_name]['ProcessingStatus']['OverallStatus'] = False
        hvsr_out = HVSRBatch(hvsr_out)
    else:
        ppsds = hvsr_data['ppsds'].copy()#[k]['psd_values']
        ppsds = sprit_utils.check_xvalues(ppsds)

        methodList = ['<placeholder_0>', 'Diffuse Field Assumption', 'Arithmetic Mean', 'Geometric Mean', 'Vector Summation', 'Quadratic Mean', 'Maximum Horizontal Value']
        x_freqs = {}
        x_periods = {}

        psdValsTAvg = {}
        stDev = {}
        stDevValsP = {}
        stDevValsM = {}
        psdRaw={}
        currTimesUsed={}
        hvsrDF = hvsr_data['hvsr_df']

        def move_avg(y, box_pts):
            #box = np.ones(box_pts)/box_pts
            box = np.hanning(box_pts)
            y_smooth = np.convolve(y, box, mode='same') / sum(box)
            return y_smooth

        for k in ppsds.keys():
            #input_ppsds = ppsds[k]['psd_values'] #original, not used anymore
            input_ppsds = np.stack(hvsrDF['psd_values_'+k].values)

            currPPSDs = hvsrDF['psd_values_'+k][hvsrDF['Use']].values
            used_ppsds = np.stack(currPPSDs)
            
            #if reasmpling has been selected
            if resample is True or isinstance(resample, (int, float)):
                if resample is True:
                    resample = 1000 #Default smooth value

                #xValMin = min(ppsds[k]['period_bin_centers'])
                #xValMax = max(ppsds[k]['period_bin_centers'])
                xValMin = 1/hvsr_data['hvsr_band'][1]
                xValMax = 1/hvsr_data['hvsr_band'][0]
                #Resample period bin values
                x_periods[k] = np.logspace(np.log10(xValMin), np.log10(xValMax), num=resample)
                if smooth or isinstance(smooth, (int, float)):
                    if smooth:
                        smooth = 51 #Default smoothing window
                        padVal = 25
                    elif smooth % 2==0:
                        smooth +1 #Otherwise, needs to be odd
                        padVal = smooth//2
                        if padVal %2==0:
                            padVal += 1

                #Resample raw ppsd values
                for i, ppsd_t in enumerate(input_ppsds):
                    if i==0:
                        psdRaw[k] = np.interp(x_periods[k], ppsds[k]['period_bin_centers'], ppsd_t)
                        if smooth is not False:
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

            else:
                #If no resampling desired
                #x_periods[k] = np.array(ppsds[k]['period_bin_centers'])
                x_periods[k] = np.round([1/p for p in hvsr_data['ppsds'][k]['period_xedges'][:-1]],3)
                x_periods[k][0] = hvsr_data['hvsr_band'][1]
                x_periods[k][-1] = hvsr_data['hvsr_band'][0]
                psdRaw[k] = np.array(input_ppsds)

            hvsrDF['psd_values_'+k] = list(psdRaw[k])

            #Get average psd value across time for each channel (used to calc main H/V curve)
            psdValsTAvg[k] = np.nanmean(np.array(psdRaw[k]), axis=0)
            x_freqs[k] = np.array([1/p for p in x_periods[k]]) #np.divide(np.ones_like(x_periods[k]), x_periods[k]) 
            stDev[k] = np.std(psdRaw[k], axis=0)
            stDevValsM[k] = np.array(psdValsTAvg[k] - stDev[k])
            stDevValsP[k] = np.array(psdValsTAvg[k] + stDev[k])

            currTimesUsed[k] = np.array(hvsrDF['TimesProcessed_Obspy'][hvsrDF['Use']].values)
            #currTimesUsed[k] = ppsds[k]['current_times_used'] #original one
        
        #Get string of method type
        if type(method) is int:
            methodInt = method
            method = methodList[method]
        hvsr_data['method'] = method

        #This gets the main hvsr curve averaged from all time steps
        anyK = list(x_freqs.keys())[0]
        hvsr_curve, _ = __get_hvsr_curve(x=x_freqs[anyK], psd=psdValsTAvg, method=methodInt, hvsr_data=hvsr_data, verbose=verbose)
        origPPSD = hvsr_data['ppsds_obspy'].copy()


        #Add some other variables to our output dictionary
        hvsr_dataUpdate = {'input_params':hvsr_data,
                    'x_freqs':x_freqs,
                    'hvsr_curve':hvsr_curve,
                    'x_period':x_periods,
                    'psd_raw':psdRaw,
                    'current_times_used': currTimesUsed,
                    'psd_values_tavg':psdValsTAvg,
                    'ppsd_std':stDev,
                    'ppsd_std_vals_m':stDevValsM,
                    'ppsd_std_vals_p':stDevValsP,
                    'method':method,
                    'ppsds':ppsds,
                    'ppsds_obspy':origPPSD,
                    'tsteps_used': hvsr_data['tsteps_used'].copy(),
                    'hvsr_df':hvsr_data['hvsr_df']
                    }
        
        hvsr_out = HVSRData(hvsr_dataUpdate)

        #This is if manual editing was used (should probably be updated at some point to just use masks)
        if 'xwindows_out' in hvsr_data.keys():
            hvsr_out['xwindows_out'] = hvsr_data['xwindows_out']
        else:
            hvsr_out['xwindows_out'] = []


        freq_smooth_ko = ['konno ohmachi', 'konno-ohmachi', 'konnoohmachi', 'konnohmachi', 'ko', 'k']
        freq_smooth_constant = ['constant', 'const', 'c']
        freq_smooth_proport = ['proportional', 'proportion', 'prop', 'p']

        #Frequency Smoothing
        if not freq_smooth:
            if verbose:
                warnings.warn('No frequency smoothing is being applied. This is not recommended for noisy datasets.')
        elif freq_smooth is True or freq_smooth.lower() in freq_smooth_ko:
            from obspy.signal import konnoohmachismoothing
            for k in hvsr_out['psd_raw']:
                colName = f'psd_values_{k}'

                ppsd_data = np.stack(hvsr_out['hvsr_df'][colName])
                ppsd_data = hvsr_out['psd_raw'][k]


                freqs = hvsr_out['x_freqs'][k]
                padding_length = int(f_smooth_width)

                padding_value_R = np.nanmean(ppsd_data[:,-1*padding_length:])
                padding_value_L = np.nanmean(ppsd_data[:,:padding_length])

                # Pad the data to prevent boundary anamolies
                padded_ppsd_data = np.pad(ppsd_data, ((0, 0), (padding_length, padding_length)), 
                                          'constant', constant_values=(padding_value_L, padding_value_R))

                # Pad the frequencies
                ratio = freqs[1] / freqs[0]
                # Generate new elements on either side and combine
                left_padding = [freqs[0] / (ratio ** i) for i in range(padding_length, 0, -1)]
                right_padding = [freqs[-1] * (ratio ** i) for i in range(1, padding_length + 1)]
                padded_freqs = np.concatenate([left_padding, freqs, right_padding])
                
                #Filter out UserWarning for just this method, since it throws up a UserWarning that doesn't really matter about dtypes often
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', category=UserWarning)
                    smoothed_ppsd_data = konnoohmachismoothing.konno_ohmachi_smoothing(padded_ppsd_data, 
                                                    padded_freqs, bandwidth=f_smooth_width, normalize=True)
                
                #Just use the original data
                smoothed_ppsd_data = smoothed_ppsd_data[:,padding_length:-1*padding_length]
                hvsr_out['psd_raw'][k] = smoothed_ppsd_data
                hvsr_out['hvsr_df'][colName] = pd.Series(list(smoothed_ppsd_data), index=hvsr_out['hvsr_df'].index)

        elif freq_smooth.lower() in freq_smooth_constant:
            hvsr_out = __freq_smooth_window(hvsr_out, f_smooth_width, kind_freq_smooth='constant')
        elif freq_smooth.lower() in freq_smooth_proport:
            hvsr_out = __freq_smooth_window(hvsr_out, f_smooth_width, kind_freq_smooth='proportional')
        else:
            if verbose:
                warnings.warn(f'You indicated no frequency smoothing should be applied (freq_smooth = {freq_smooth}). This is not recommended for noisy datasets.')

        #Get hvsr curve from three components at each time step
        anyK = list(hvsr_out['psd_raw'].keys())[0]
        if method==1 or method =='dfa' or method =='Diffuse Field Assumption':
            pass ###UPDATE HERE NEXT???__get_hvsr_curve(x=hvsr_out['x_freqs'][anyK], psd=tStepDict, method=methodInt, hvsr_data=hvsr_out, verbose=verbose)
        else:
            hvsr_tSteps = []
            for tStep in range(len(hvsr_out['psd_raw'][anyK])):
                tStepDict = {}
                for k in hvsr_out['psd_raw']:
                    tStepDict[k] = hvsr_out['psd_raw'][k][tStep]
                hvsr_tstep, _ = __get_hvsr_curve(x=hvsr_out['x_freqs'][anyK], psd=tStepDict, method=methodInt, hvsr_data=hvsr_out, verbose=verbose)
                hvsr_tSteps.append(np.float32(hvsr_tstep)) #Add hvsr curve for each time step to larger list of arrays with hvsr_curves
        hvsr_out['hvsr_df']['HV_Curves'] = hvsr_tSteps

        hvsr_out['ind_hvsr_curves'] = np.stack(hvsr_out['hvsr_df']['HV_Curves'][hvsr_out['hvsr_df']['Use']])
        #hvsr_out['ind_hvsr_curves'] = np.array(hvsr_tSteps)

        #Initialize array based only on the curves we are currently using
        indHVCurvesArr = np.stack(hvsr_out['hvsr_df']['HV_Curves'][hvsr_out['hvsr_df']['Use']])
        #indHVCurvesArr = hvsr_out['ind_hvsr_curves']

        if outlier_curve_rmse_percentile:
            if outlier_curve_rmse_percentile is True:
                outlier_curve_rmse_percentile = 98
            hvsr_out = remove_outlier_curves(hvsr_out, use_percentile=True, rmse_thresh=outlier_curve_rmse_percentile, use_hv_curve=True, verbose=verbose)
  
        hvsr_out['ind_hvsr_stdDev'] = np.nanstd(indHVCurvesArr, axis=0)

        #Get peaks for each time step
        tStepPeaks = []
        for tStepHVSR in hvsr_tSteps:
            tStepPeaks.append(__find_peaks(tStepHVSR))
        hvsr_out['ind_hvsr_peak_indices'] = tStepPeaks
        hvsr_out['hvsr_df']['CurvesPeakIndices'] = tStepPeaks

        tStepPFList = []
        for tPeaks in tStepPeaks:
            tStepPFs = []
            for pInd in tPeaks:
                tStepPFs.append(np.float32(hvsr_out['x_freqs'][anyK][pInd]))
            tStepPFList.append(tStepPFs)
        hvsr_out['hvsr_df']['CurvesPeakFreqs'] = tStepPFList

        #Get peaks of main HV curve
        hvsr_out['hvsr_peak_indices'] = __find_peaks(hvsr_out['hvsr_curve'])
        
        #Get frequency values at HV peaks in main curve
        hvsrPF=[]
        for p in hvsr_out['hvsr_peak_indices']:
            hvsrPF.append(hvsr_out['x_freqs'][anyK][p])
        hvsr_out['hvsr_peak_freqs'] = np.array(hvsrPF)


        #Get other HVSR parameters (i.e., standard deviations, etc.)
        hvsr_out = __gethvsrparams(hvsr_out)

        #Include the original obspy stream in the output
        hvsr_out['input_stream'] = hvsr_dataUpdate['input_params']['input_stream'] #input_stream
        hvsr_out = sprit_utils.make_it_classy(hvsr_out)
        hvsr_out['ProcessingStatus']['HVStatus'] = True

        if 'processing_parameters' not in hvsr_out.keys():
            hvsr_out['processing_parameters'] = {}
        hvsr_out['processing_parameters']['generate_ppsds'] = {}
        for key, value in orig_args.items():
            hvsr_out['processing_parameters']['generate_ppsds'][key] = value

    hvsr_out = _check_processing_status(hvsr_out, start_time=start_time, func_name=inspect.stack()[0][3], verbose=verbose)

    return hvsr_out

#Function to remove noise windows from data
def remove_noise(hvsr_data, remove_method='auto', sat_percent=0.995, noise_percent=0.80, sta=2, lta=30, stalta_thresh=[0.5,5], warmup_time=0, cooldown_time=0, min_win_size=1, remove_raw_noise=False, verbose=False):
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
            for k, v in hvsr_data['processing_parameters']['remove_noise'].items():
                defaultVDict = dict(zip(inspect.getfullargspec(remove_noise).args[1:], 
                                        inspect.getfullargspec(remove_noise).defaults))
                # Manual input to function overrides the imported parameter values
                if (not isinstance(v, (HVSRData, HVSRBatch))) and (k in orig_args.keys()) and (orig_args[k]==defaultVDict[k]):
                    orig_args[k] = v

    remove_method = orig_args['remove_method']
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

    #Setup lists
    manualList = ['manual', 'man', 'm', 'window', 'windows', 'w']
    autoList = ['auto', 'automatic', 'all', 'a']
    antitrigger = ['stalta', 'anti', 'antitrigger', 'trigger', 'at']
    saturationThresh = ['saturation threshold', 'saturation', 'sat', 's']
    noiseThresh = ['noise threshold', 'noise', 'threshold', 'n']
    warmup_cooldown=['warmup', 'cooldown', 'warm', 'cool', 'buffer', 'warmup-cooldown', 'warmup_cooldown', 'wc', 'warm_cool', 'warm-cool']

    #Get Stream from hvsr_data
    if isinstance(hvsr_data, HVSRBatch):
        #If running batch, we'll loop through each site
        hvsr_out = {}
        for site_name in hvsr_data.keys():
            args = orig_args.copy() #Make a copy so we don't accidentally overwrite
            args['hvsr_data'] = hvsr_data[site_name] #Get what would normally be the "hvsr_data" variable for each site
            if hvsr_data[site_name]['ProcessingStatus']['OverallStatus']:
                try:
                   hvsr_out[site_name] = __remove_noise_batch(**args) #Call another function, that lets us run this function again
                except Exception as e:
                    hvsr_out[site_name]['ProcessingStatus']['RemoveNoiseStatus']=False
                    hvsr_out[site_name]['ProcessingStatus']['OverallStatus']=False
                    if verbose:
                        print(e)
            else:
                hvsr_data[site_name]['ProcessingStatus']['RemoveNoiseStatus']=False
                hvsr_data[site_name]['ProcessingStatus']['OverallStatus']=False
                hvsr_out = hvsr_data

        output = HVSRBatch(hvsr_out)
        return output
    elif isinstance(hvsr_data, (HVSRData, dict, obspy.Stream, obspy.Trace)):
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
            
        #Reorder list so manual is always first
        if len(set(remove_method).intersection(manualList)) > 0:
            manInd = list(set(remove_method).intersection(manualList))[0]
            remove_method.remove(manInd)
            remove_method.insert(0, manInd)
            
        #Go through each type of removal and remove
        for rem_kind in remove_method:
            if not rem_kind:
                break
            elif rem_kind.lower() in manualList:
                if isinstance(output, (HVSRData, dict)):
                    if 'xwindows_out' in output.keys():
                        pass
                    else:
                        output = _select_windows(output)
                    window_list = output['xwindows_out']
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
                outStream = __remove_noise_thresh(outStream, noise_percent=noise_percent, lta=lta, min_win_size=min_win_size)
                outStream = __remove_anti_stalta(outStream, sta=sta, lta=lta, thresh=stalta_thresh)
                outStream = __remove_noise_saturate(outStream, sat_percent=sat_percent, min_win_size=min_win_size)
                outStream = __remove_warmup_cooldown(stream=outStream, warmup_time=warmup_time, cooldown_time=cooldown_time)
            elif rem_kind.lower() in antitrigger:
                outStream = __remove_anti_stalta(outStream, sta=sta, lta=lta, thresh=stalta_thresh)
            elif rem_kind.lower() in saturationThresh:
                outStream = __remove_noise_saturate(outStream, sat_percent=sat_percent, min_win_size=min_win_size)
            elif rem_kind.lower() in noiseThresh:
                outStream = __remove_noise_thresh(outStream, noise_percent=noise_percent, lta=lta, min_win_size=min_win_size)
            elif rem_kind.lower() in warmup_cooldown:
                outStream = __remove_warmup_cooldown(stream=outStream, warmup_time=warmup_time, cooldown_time=cooldown_time)
            else:
                if len(remove_method)==1:
                    warnings.warn(f"Input value remove_method={remove_method} is not recognized. No noise removal will be carried out. Please choose one of the following: 'manual', 'auto', 'antitrigger', 'noise threshold', 'warmup_cooldown'.")
                    break
                warnings.warn(f"Input value remove_method={remove_method} is not recognized. Continuing with other noise removal methods.")

        #Add output
        if isinstance(output, (HVSRData, dict)):
            if isinstance(outStream, (obspy.Stream, obspy.Trace)):
                output['stream'] = outStream
            else:
                output['stream'] = outStream['stream']
            output['input_stream'] = hvsr_data['input_stream']
            
            if 'processing_parameters' not in output.keys():
                output['processing_parameters'] = {}
            output['processing_parameters']['remove_noise'] = {}
            for key, value in orig_args.items():
                output['processing_parameters']['remove_noise'][key] = value
            
            output['ProcessingStatus']['RemoveNoiseStatus'] = True
            output = _check_processing_status(output, start_time=start_time, func_name=inspect.stack()[0][3], verbose=verbose)

            if 'hvsr_df' in output.keys() or ('params' in output.keys() and 'hvsr_df' in output['params'].keys())or ('input_params' in output.keys() and 'hvsr_df' in output['input_params'].keys()):
                hvsrDF = output['hvsr_df']
                
                outStream = output['stream'].split()
                for i, trace in enumerate(outStream):
                    if i ==0:
                        trEndTime = trace.stats.endtime
                        comp_end = trace.stats.component
                        continue
                    trStartTime = trace.stats.starttime
                    comp_start = trace.stats.component
                    
                    if trEndTime < trStartTime and comp_end==comp_start:
                        gap = [trEndTime,trStartTime]

                        output['hvsr_df']['Use'] = (hvsrDF['TimesProcessed_Obspy'].gt(gap[0]) & hvsrDF['TimesProcessed_Obspy'].gt(gap[1]) )| \
                                        (hvsrDF['TimesProcessed_ObspyEnd'].lt(gap[0]) & hvsrDF['TimesProcessed_ObspyEnd'].lt(gap[1]))# | \
                        output['hvsr_df']['Use'] = output['hvsr_df']['Use'].astype(bool)
                    
                    trEndTime = trace.stats.endtime
                
                outStream.merge()
                output['stream'] = outStream
                    
        elif isinstance(hvsr_data, obspy.Stream) or isinstance(hvsr_data, obspy.Trace):
            output = outStream
        else:
            warnings.warn(f"Output of type {type(output)} for this function will likely result in errors in other processing steps. Returning hvsr_data data.")
            return hvsr_data
        output = sprit_utils.make_it_classy(output)
        if 'xwindows_out' not in output.keys():
            output['xwindows_out'] = []
    else:
        RuntimeError(f"Input of type type(hvsr_data)={type(hvsr_data)} cannot be used.")
    
    return output

#Remove outlier ppsds
def remove_outlier_curves(hvsr_data, rmse_thresh=98, use_percentile=True, use_hv_curve=False, show_plot=False, verbose=False):
    """Function used to remove outliers curves using Root Mean Square Error to calculate the error of each windowed
    Probabilistic Power Spectral Density (PPSD) curve against the median PPSD value at each frequency step for all times.
    It calculates the RMSE for the PPSD curves of each component individually. All curves are removed from analysis.
    
    Some abberant curves often occur due to the remove_noise() function, so this should be run some time after remove_noise(). 
    In general, the recommended workflow is to run this immediately following the generate_ppsds() function.

    Parameters
    ----------
    hvsr_data : dict
        Input dictionary containing all the values and parameters of interest
    rmse_thresh : float or int, default=98
        The Root Mean Square Error value to use as a threshold for determining whether a curve is an outlier. 
        This averages over each individual entire curve so that curves with very abberant data (often occurs when using the remove_noise() method), can be identified.
        Otherwise, specify a float or integer to use as the cutoff RMSE value (all curves with RMSE above will be removed)
    use_percentile :  float, default=True
        Whether rmse_thresh should be interepreted as a raw RMSE value or as a percentile of the RMSE values.
    use_hv_curve : bool, default=False
        Whether to use the calculated HV Curve or the individual components. This can only be True after process_hvsr() has been run.
    show_plot : bool, default=False
        Whether to show a plot of the removed data
    verbose : bool, default=False
        Whether to print output of function to terminal

    Returns
    -------
    hvsr_data : dict
        Input dictionary with values modified based on work of function.
    """
    # Setup function
    #Get intput paramaters
    orig_args = locals().copy()
    start_time = datetime.datetime.now()
    
    # Update with processing parameters specified previously in input_params, if applicable
    if 'processing_parameters' in hvsr_data.keys():
        if 'remove_outlier_curves' in hvsr_data['processing_parameters'].keys():
            for k, v in hvsr_data['processing_parameters']['remove_noise'].items():
                defaultVDict = dict(zip(inspect.getfullargspec(remove_outlier_curves).args[1:], 
                                        inspect.getfullargspec(remove_outlier_curves).defaults))
                # Manual input to function overrides the imported parameter values
                if (not isinstance(v, (HVSRData, HVSRBatch))) and (k in orig_args.keys()) and (orig_args[k]==defaultVDict[k]):
                    orig_args[k] = v

    # Reset parameters in case of manual override of imported parameters
    use_percentile = orig_args['use_percentile']
    rmse_thresh = orig_args['rmse_thresh']
    use_hv_curve = orig_args['use_hv_curve']
    show_plot = orig_args['show_plot']
    verbose = orig_args['verbose']

    #Print if verbose, which changes depending on if batch data or not
    if (verbose and isinstance(hvsr_data, HVSRBatch)) or (verbose and not hvsr_data['batch']):
        if isinstance(hvsr_data, HVSRData) and hvsr_data['batch']:
            pass
        else:
            print('\nRemoving outlier curves from further analysis (remove_outlier_curves())')
            print('\tUsing the following parameters:')
            for key, value in orig_args.items():
                if key=='hvsr_data':
                    pass
                else:
                    print('\t  {}={}'.format(key, value))
            print()
    
    #First, divide up for batch or not
    #Site is in the keys anytime it's not batch
    if isinstance(hvsr_data, HVSRBatch):
        #If running batch, we'll loop through each site
        hvsr_out = {}
        for site_name in hvsr_data.keys():
            args = orig_args.copy() #Make a copy so we don't accidentally overwrite
            args['hvsr_data'] = hvsr_data[site_name] #Get what would normally be the "hvsr_data" variable for each site
            if hvsr_data[site_name]['ProcessingStatus']['OverallStatus']:
                try:
                    hvsr_out[site_name] = __remove_outlier_curves(**args) #Call another function, that lets us run this function again
                except:
                    hvsr_out = hvsr_data
                    hvsr_out[site_name]['ProcessingStatus']['RemoveOutlierCurves'] = False
                    hvsr_out[site_name]['ProcessingStatus']['OverallStatus'] = False                    
            else:
                hvsr_out = hvsr_data
                hvsr_out[site_name]['ProcessingStatus']['RemoveOutlierCurves'] = False
                hvsr_out[site_name]['ProcessingStatus']['OverallStatus'] = False
        hvsr_out = HVSRBatch(hvsr_out)
    else:  
        #Create plot if designated        
        if not use_hv_curve:
            compNames = ['Z', 'E', 'N']
            colNames = compNames
        else:
            compNames=['HV Curve']
            colNames = ['HV_Curves']
        if show_plot:
            if use_hv_curve:
                spMosaic = ['HV Curve']
            else:
                spMosaic = [['Z'],
                            ['E'],
                            ['N']]
            fig, ax=plt.subplot_mosaic(spMosaic, sharex=True)

        #Loop through each component, and determine which curves are outliers
        bad_rmse=[]
        for i, column in enumerate(colNames):
            if column in compNames:
                column = 'psd_values_'+column
            # Retrieve data from dataframe (use all windows, just in case)
            curr_data = np.stack(hvsr_data['hvsr_df'][column])
            
            # Calculate a median curve, and reshape so same size as original
            medCurve = np.nanmedian(curr_data, axis=0)
            medCurveArr = np.tile(medCurve, (curr_data.shape[0], 1))
            
            # Calculate RMSE
            rmse = np.sqrt(((np.subtract(curr_data, medCurveArr)**2).sum(axis=1))/curr_data.shape[1])
            hvsr_data['hvsr_df']['RMSE_'+column] = rmse
            if use_percentile is True:
                rmse_threshold = np.percentile(rmse, rmse_thresh)
                if verbose:
                    print(f'\tRMSE at {rmse_thresh}th percentile for {column} calculated at: {rmse_threshold:.2f}')
                else:
                    rmse_threshold = rmse_thresh
            
            # Retrieve index of those RMSE values that lie outside the threshold
            for j, curve in enumerate(curr_data):
                if rmse[j] > rmse_threshold:
                    bad_rmse.append(j)

            # Show plot of removed/retained data
            if show_plot:
                # Intialize to only get unique labels
                rem_label_got = False
                keep_label_got = False
                
                # Iterate through each curve to determine if it's rmse is outside threshold, for plot
                for j, curve in enumerate(curr_data):
                    label=None
                    if rmse[j] > rmse_threshold:
                        linestyle = 'dashed'
                        linecolor='darkred'
                        alpha = 1
                        linewidth = 1
                        if not rem_label_got:
                            label='Removed Curve'
                            rem_label_got=True
                    else:
                        linestyle='solid'
                        linecolor = 'rosybrown'
                        alpha = 0.25
                        linewidth=0.5
                        if not keep_label_got:
                            keep_label_got=True
                            label='Retained Curve'

                    # Plot each individual curve
                    ax[compNames[i]].plot(1/hvsr_data.ppsds[compNames[i]]['period_bin_centers'], curve, linewidth=linewidth, c=linecolor, linestyle=linestyle, alpha=alpha, label=label)
                
                # Plot the median curve
                ax[compNames[i]].plot(1/hvsr_data.ppsds[compNames[i]]['period_bin_centers'],medCurve, linewidth=1, color='k', label='Median Curve')
                
                # Format axis
                ax[compNames[i]].set_ylabel(f"{compNames[i]}")
                ax[compNames[i]].legend(fontsize=10, labelspacing=0.1)
                ax[compNames[i]].semilogx()             
        if show_plot:
            plt.show()
                    
        # Get unique values of bad_rmse indices and set the "Use" column of the hvsr_df to False for that window
        bad_rmse = np.unique(bad_rmse)
        if len(bad_rmse) > 0:
            
            hvsr_data['hvsr_df']['Use'] = hvsr_data['hvsr_df']['Use'] * (rmse_threshold > hvsr_data['hvsr_df']['RMSE_'+column])
            #hvsr_data['hvsr_df'].loc[bad_index, "Use"] = False   
        
        if verbose:
            if len(bad_rmse)>0:
                print(f"\tThe windows starting at the following times have been removed from further analysis ({len(bad_rmse)}/{hvsr_data['hvsr_df'].shape[0]}):")
                for b in hvsr_data['hvsr_df'].index[pd.Series(bad_rmse)]:
                    print(f"\t\t{b}")
            else:
                print('\tNo outlier curves have been removed')
                    
        hvsr_out = hvsr_data

        if 'processing_parameters' not in hvsr_out.keys():
            hvsr_out['processing_parameters'] = {}
        hvsr_out['processing_parameters']['remove_outlier_curves'] = {}
        for key, value in orig_args.items():
            hvsr_out['processing_parameters']['remove_outlier_curves'][key] = value

        hvsr_data['ProcessingStatus']['RemoveOutlierCurvesStatus'] = True
    
    hvsr_out = _check_processing_status(hvsr_out, start_time=start_time, func_name=inspect.stack()[0][3], verbose=verbose)
    
    return hvsr_out

#Read data as batch
def batch_data_read(input_data, batch_type='table', param_col=None, batch_params=None, verbose=False, **readcsv_getMeta_fetch_kwargs):
    """Function to read data in data as a batch of multiple data files. This is best used through sprit.fetch_data(*args, source='batch', **other_kwargs).

    Parameters
    ----------
    input_data : filepath or list
        Input data information for how to read in data as batch
    batch_type : str, optional
        Type of batch read, only 'table' and 'filelist' accepted. If 'table', will read data from a file read in using pandas.read_csv(), by default 'table'
    param_col : None or str, optional
        Name of parameter column from batch information file. Only used if a batch_type='table' and single parameter column is used, rather than one column per parameter (for single parameter column, parameters are formatted with = between keys/values and , between item pairs), by default None
    batch_params : list, dict, or None, default = None
        Parameters to be used if batch_type='filelist'. If it is a list, needs to be the same length as input_data. If it is a dict, will be applied to all files in input_data and will combined with extra keyword arguments caught by **readcsv_getMeta_fetch_kwargs.
    verbose : bool, optional
        Whether to print information to terminal during batch read, by default False
    **readcsv_getMeta_fetch_kwargs
        Keyword arguments that will be read into pandas.read_csv(), sprit.input_params, sprit.get_metadata(), and/or sprit.fetch_data()

    Returns
    -------
    dict
        Dictionary with each item representing a different file read in, and which consists of its own parameter dictionary to be used by the rest of the processing steps

    Raises
    ------
    IndexError
        _description_
    """
    #First figure out columns
    input_params_params = input_params.__code__.co_varnames
    get_metadata_params = get_metadata.__code__.co_varnames
    fetch_data_params = fetch_data.__code__.co_varnames

    if batch_type=='sample':
        sample_data=True
        batch_type='table'
    else:
        sample_data = False
    # Dictionary to store the stream objects
    stream_dict = {}
    data_dict = {}
    if batch_type == 'table':
        if isinstance(input_data, pd.DataFrame):
            dataReadInfoDF = input_data
        elif isinstance(input_data, dict):
            #For params input
            pass
        else:#Read csv
            read_csv_kwargs = {k: v for k, v in locals()['readcsv_getMeta_fetch_kwargs'].items() if k in pd.read_csv.__code__.co_varnames}
            dataReadInfoDF = pd.read_csv(input_data, **read_csv_kwargs)
            if 'datapath' in dataReadInfoDF.columns:
                filelist = list(dataReadInfoDF['datapath'])
            #dataReadInfoDF = dataReadInfoDF.replace(np.nan, None)

        #If this is sample data, we need to create absolute paths to the filepaths
        if sample_data:
            sample_data_dir = pathlib.Path(pkg_resources.resource_filename(__name__, 'resources/sample_data/'))
            for index, row in dataReadInfoDF.iterrows():
                dataReadInfoDF.loc[index, 'datapath'] = sample_data_dir.joinpath(row.loc['datapath'])

        default_dict = {'site':'HVSR Site',
                    'network':'AM', 
                    'station':'RAC84', 
                    'loc':'00', 
                    'channels':['EHZ', 'EHN', 'EHE'],
                    'acq_date':str(datetime.datetime.now().date()),
                    'starttime' : '00:00:00.00',
                    'endtime' : '23:59:59.999',
                    'tzone' : 'UTC',
                    'xcoord' : -88.2290526,
                    'ycoord' :  40.1012122,
                    'elevation' : 755,
                    'input_crs':'EPSG:4326',#4269 is NAD83, defautling to WGS
                    'output_crs':'EPSG:4326',
                    'elev_unit' : 'feet',
                    'depth' : 0,
                    'instrument' : 'Raspberry Shake',
                    'metapath' : '',
                    'hvsr_band' : [0.4, 40],
                    'write_path':'',
                    'source':'file', 
                    'export_format':'mseed', 
                    'detrend':'spline', 
                    'detrend_order':2, 
                    'verbose':False}

        print(f"\t{dataReadInfoDF.shape[0]} sites found: {list(dataReadInfoDF['site'])}")
        if verbose:
            maxLength = 25
            maxColWidth = 12
            if dataReadInfoDF.shape[0] > maxLength:
                print(f'\t Showing information for first {maxLength} files only:')
            print()
            #Print nicely formated df
            #Print column names
            print('\t', end='')
            for col in dataReadInfoDF.columns:
                print(str(col)[:maxColWidth].ljust(maxColWidth), end='  ')
            print('\n\t', end='')

            #Print separator
            tableLen = (maxColWidth+2)*len(dataReadInfoDF.columns)
            for r in range(tableLen):
                print('-', end='')
            print()

            #Print columns/rows
            for index, row in dataReadInfoDF.iterrows():
                print('\t', end='')
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
        param_dict_list = []
        verboseStatement = []
        if param_col is None: #Not a single parameter column, each col=parameter
            for row_ind in range(dataReadInfoDF.shape[0]):
                param_dict = {}
                verboseStatement.append([])
                for col in dataReadInfoDF.columns:
                    if col in input_params_params or col in get_metadata_params or col in fetch_data_params:
                        currParam = dataReadInfoDF.loc[row_ind, col]
                        if pd.isna(currParam) or currParam == 'nan':
                            if col in default_dict.keys():
                                param_dict[col] = default_dict[col] #Get default value
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
                raise IndexError('{} is not a column in {} (columns are: {})'.format(param_col, input_data, dataReadInfoDF.columns))
            for row in dataReadInfoDF[param_col]:
                param_dict = {}
                splitRow = str(row).split(',')
                for item in splitRow:
                    param_dict[item.split('=')[0]] = item.split('=')[1]
                param_dict_list.append(param_dict)
        #input_params(datapath,site,network,station,loc,channels, acq_date,starttime, endtime, tzone, xcoord, ycoord, elevation, depth, instrument, metapath, hvsr_band)
        #fetch_data(params, inv, source, trim_dir, export_format, detrend, detrend_order, verbose)
        #get_metadata(params, write_path)
    elif batch_type == 'filelist':
        if isinstance(batch_params, list):
            if len(batch_params) != len(input_data):
                raise RuntimeError('If batch_params is list, it must be the same length as input_data. len(batch_params)={} != len(input_data)={}'.format(len(batch_params), len(input_data)))
            param_dict_list = batch_params
        elif isinstance(batch_params, dict):
            batch_params.update(readcsv_getMeta_fetch_kwargs)
            param_dict_list = []
            for i in range(len(input_data)):
                param_dict_list.append(batch_params)
        
        # Read and process each MiniSEED file
        for i, file in enumerate(input_data):
            if isinstance(file, obspy.core.stream.Stream):
                warnings.warn('Reading in a list of Obspy streams is not currently supported, but may be implemented in the future', FutureWarning)
                pass 
            else:
                param_dict_list[i]['datapath'] = file

    hvsr_metaDict = {}
    zfillDigs = len(str(len(param_dict_list))) #Get number of digits of length of param_dict_list
    i=0
    for i, param_dict in enumerate(param_dict_list):
        # Read the data file into a Stream object
        input_params_kwargs = {k: v for k, v in locals()['readcsv_getMeta_fetch_kwargs'].items() if k in input_params.__code__.co_varnames}
        input_params_kwargs2 = {k: v for k, v in param_dict.items() if k in input_params.__code__.co_varnames}
        input_params_kwargs.update(input_params_kwargs2)

        params = input_params(**input_params_kwargs)

        fetch_data_kwargs = {k: v for k, v in locals()['readcsv_getMeta_fetch_kwargs'].items() if k in fetch_data.__code__.co_varnames}
        fetch_data_kwargs2 = {k: v for k, v in param_dict.items() if k in fetch_data.__code__.co_varnames[0:7]}
        fetch_data_kwargs.update(fetch_data_kwargs2)
        
        try:
            params = fetch_data(params=params, **fetch_data_kwargs)
        except:
            params['ProcessingStatus']['FetchDataStatus']=False
            params['ProcessingStatus']['OverallStatus'] = False            
        
        if verbose and params['ProcessingStatus']['FetchDataStatus']:
            print("\t  {}".format(params['site']))
            if verboseStatement !=[]:
                for item in verboseStatement[i]:
                    print(item)
        elif verbose and not params['ProcessingStatus']['FetchDataStatus']:
            print("\t  {} not read correctly. Processing will not be carried out.".format(params['site']))
                
        params['batch'] = True

        if params['site'] == default_dict['site']: #If site was not designated
            params['site'] = "{}_{}".format(params['site'], str(i).zfill(zfillDigs))
            i+=1
        hvsr_metaDict[params['site']] = params

    hvsr_metaDict = HVSRBatch(hvsr_metaDict)

    return hvsr_metaDict

#Just for testing
def test_function():
    print('is this working?')

#BATCH FUNCTIONS: various functions that are used to help the regular functions handle batch data
#Helper function for batch processing of check_peaks
def _check_peaks_batch(**check_peaks_kwargs):
    try:
        hvsr_data = check_peaks(**check_peaks_kwargs)
        if check_peaks_kwargs['verbose']:
            print('\t{} succesfully completed check_peaks()'.format(hvsr_data['input_params']['site']))    
    except:
        warnings.warn(f"Error in check_peaks({check_peaks_kwargs['hvsr_data']['input_params']['site']}, **check_peaks_kwargs)", RuntimeWarning)
        hvsr_data = check_peaks_kwargs['hvsr_data']
        
    return hvsr_data

#Support function for running batch
def _generate_ppsds_batch(**generate_ppsds_kwargs):
    try:
        params = generate_ppsds(**generate_ppsds_kwargs)
        if generate_ppsds_kwargs['verbose']:
            print('\t{} successfully completed generate_ppsds()'.format(params['site']))
    except Exception as e:
        print(e)
        warnings.warn(f"Error in generate_ppsds({generate_ppsds_kwargs['params']['site']}, **generate_ppsds_kwargs)", RuntimeWarning)
        params = generate_ppsds_kwargs['params']
        
    return params

#Helper function for batch processing of get_report
def _get_report_batch(**get_report_kwargs):

    try:
        hvsr_results = get_report(**get_report_kwargs)
        #Print if verbose, but selected report_format was not print
        print('\n\n\n') #add some 'whitespace'
        if get_report_kwargs['verbose']:
            if 'print' in get_report_kwargs['report_format']:
                pass
            else:
                get_report_kwargs['report_format'] = 'print'
                get_report(**get_report_kwargs)
        
    except:
        warnMsg = f"Error in get_report({get_report_kwargs['hvsr_results']['input_params']['site']}, **get_report_kwargs)"
        if get_report_kwargs['verbose']:
            print('\t'+warnMsg)
        else:
            warnings.warn(warnMsg, RuntimeWarning)
        hvsr_results = get_report_kwargs['hvsr_results']
        
    return hvsr_results

#Helper function for batch procesing of remove_noise
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

#Batch function for plot_hvsr()
def _hvsr_plot_batch(**hvsr_plot_kwargs):
    try:
        hvsr_data = plot_hvsr(**hvsr_plot_kwargs)
    except:
        warnings.warn(f"Error in plotting ({hvsr_plot_kwargs['hvsr_data']['input_params']['site']}, **hvsr_plot_kwargs)", RuntimeWarning)
        hvsr_data = hvsr_plot_kwargs['hvsr_data']
        
    return hvsr_data

#Helper function for batch version of process_hvsr()
def _process_hvsr_batch(**process_hvsr_kwargs):
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

#Special helper function that checks the processing status at each stage of processing to help determine if any processing steps were skipped
def _check_processing_status(hvsr_data, start_time=datetime.datetime.now(), func_name='', verbose=False):
    """Internal function to check processing status, used primarily in the sprit.run() function to allow processing to continue if one site is bad.

    Parameters
    ----------
    hvsr_data : sprit.HVSRData
        Data being processed

    Returns
    -------
    sprit.HVSRData
        Data being processed, with updated the 'OverallStatus' key of the attribute ProcessingStatus updated.
    """
    #Convert HVSRData to same format as HVSRBatch so same code works the same on both
    if isinstance(hvsr_data, HVSRData):
        siteName = hvsr_data['site']
        hvsr_interim = {siteName: hvsr_data}
    else:
        hvsr_interim = hvsr_data
    
    # Check overall processing status on all (or only 1 if HVSRData) site(s)
    for sitename in hvsr_interim.keys():
        statusOK = True
        for status_type, status_value in hvsr_interim[sitename]['ProcessingStatus'].items():
            if not status_value and (status_type != 'RemoveNoiseStatus' and status_type!='RemoveOutlierCurvesStatus'):
                statusOK = False
                
        if statusOK:
            hvsr_interim[sitename]['ProcessingStatus']['OverallStatus'] = True
        else:
            hvsr_interim[sitename]['ProcessingStatus']['OverallStatus'] = False

    # Get back original data in HVSRData format, if that was the input
    if isinstance(hvsr_data, HVSRData):
        hvsr_data = hvsr_interim[siteName]
    
    # Print how long it took to perform function
    if verbose:
        elapsed = (datetime.datetime.now()-start_time)
        print(f"\t\t{func_name} completed in  {str(elapsed)[:-3]}")
    return hvsr_data

#HELPER functions for fetch_data() and get_metadata()
#Read in metadata .inv file, specifically for RaspShake
def _update_shake_metadata(filepath, params, write_path=''):
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

    network = params['net']
    station = params['sta']
    optKeys = ['longitude', 'latitude', 'elevation', 'depth']
    for k in optKeys:
        if k not in params.keys():
            params[k] = '0'
    xcoord = str(params['longitude'])
    ycoord = str(params['latitude'])
    elevation = str(params['elevation'])
    depth = str(params['depth'])
    
    startdate = str(datetime.datetime(year=2023, month=2, day=15)) #First day sprit code worked :)
    enddate=str(datetime.datetime.today())

    filepath = sprit_utils.checkifpath(filepath)
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
            if write_path.isdir():
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
        #Create temporary file for reading into obspy
        tpf = tempfile.NamedTemporaryFile(delete=False)
        stringRoot = ET.tostring(root, encoding='UTF-8', method='xml')
        tpf.write(stringRoot)

        inv = obspy.read_inventory(tpf.name, format='STATIONXML', level='response')
        tpf.close()

        os.remove(tpf.name)
    params['inv'] = inv
    params['params']['inv'] = inv
    return params

#Support function for get_metadata()
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
        sprit_utils.checkifpath(params['metapath'])
        inv = obspy.read_inventory(params['metapath'], format='STATIONXML', level='response')
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
        inv = sprit_utils.checkifpath(inv)
        inv = obspy.read_inventory(params['metapath'], format='STATIONXML', level='response')
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

#Helper function to sort channels
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

#Trim data 
def _trim_data(input, stream=None, export_dir=None, export_format=None, source=None, **kwargs):
    """Function to trim data to start and end time

        Trim data to start and end times so that stream being analyzed only contains wanted data.
        Can also export data to specified directory using a specified site name and/or export_format

        Parameters
        ----------
            input  : HVSRData
                HVSR Data class containing input parameters for trimming
            stream  : obspy.stream object  
                Obspy stream to be trimmed
            export_dir: str or pathlib obj   
                Output filepath to export trimmed data to. If not specified, does not export. 
            export_format  : str or None, default=None  
                If None, and export_dir is specified, format defaults to .mseed. Otherwise, exports trimmed stream using obspy.core.stream.Stream.write() method, with export_format being passed to the format argument. 
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

    if export_format is None:
        export_format = '.mseed'

    #Format export filepath, if exporting
    if export_dir is not None:
        if site is None:
            site=''
        else:
            site = site+'_'
        if '.' not in export_format:
            export_format = '.'+export_format
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

        export_dir = sprit_utils.checkifpath(export_dir)
        export_dir = str(export_dir)
        export_dir = export_dir.replace('\\', '/')
        export_dir = export_dir.replace('\\'[0], '/')

        if type(export_format) is str:
            filename = site+net+'.'+sta+'.'+loc+'.'+yr+'.'+doy+'_'+strtD+'_'+strtT+'-'+endT+export_format
        elif type(export_format) is bool:
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

#Helper function to detrend data
def __detrend_data(input, detrend, detrend_order, verbose, source):
    """Helper function to detrend data, specifically formatted for the HVSRData and HVSRBatch objects"""
    if source!='batch':
        input = {'SITENAME': {'stream':input}} #Make same structure as batch

    for key in input.keys():
        dataIN = input[key]['stream']
        if detrend==False:
            pass
        elif detrend==True:
            #By default, do a spline removal
            for tr in dataIN:
                tr.detrend(type='spline', order=detrend_order, dspline=1000)        
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
                        tr.detrend(type=detrend, order=detrend_order)   
                if str(detrend).lower()=='spline':
                    for tr in dataIN:
                        tr.detrend(type=detrend, order=int(detrend_order), dspline=1000)       
            except:
                dataIN = data_undetrended
                if verbose:
                    warnings.warn("Detrend error, data not detrended", UserWarning)
        
        input[key]['stream'] = dataIN

    if source=='batch':
        #Return a dict
        output = input
    else:
        #Return a stream otherwise
        output = input[key]['stream']
    return output

#Read data from raspberry shake
def __read_RS_file_struct(datapath, source, year, doy, inv, params, verbose=False):
    """"Private function used by fetch_data() to read in Raspberry Shake data"""
    from obspy.core import UTCDateTime
    fileList = []
    folderPathList = []
    filesinfolder = False
    datapath = sprit_utils.checkifpath(datapath)
    #Read RS files
    if source=='raw': #raw data with individual files per trace
        if datapath.is_dir():
            for child in datapath.iterdir():
                if child.is_file() and child.name.startswith('AM') and str(doy).zfill(3) in child.name and str(year) in child.name:
                    filesinfolder = True
                    folderPathList.append(datapath)
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
                    print('Reading files: \n\t{}\n\t{}\n\t{}'.format(fileList[0].name, fileList[1].name, fileList[2].name))

            traceList = []
            for i, f in enumerate(fileList):
                with warnings.catch_warnings():
                    warnings.filterwarnings(action='ignore', message='^readMSEEDBuffer()')
                    st = obspy.read(str(f), starttime=UTCDateTime(params['starttime']), endtime=UTCDateTime(params['endtime']), nearest_sample=False)
                    st.merge()
                    tr = (st[0])
                    #tr= obspy.Trace(tr.data,header=meta)
                    traceList.append(tr)
            rawDataIN = obspy.Stream(traceList)
            with warnings.catch_warnings():
                warnings.filterwarnings(action='ignore', message='Found more than one matching response.*')
                rawDataIN.attach_response(inv)
        else:
            rawDataIN = obspy.read(str(datapath), starttime=UTCDateTime(params['starttime']), endttime=UTCDateTime(params['endtime']), nearest_sample=True)
            rawDataIN.attach_response(inv)
    elif source=='dir': #files with 3 traces, but may be several in a directory or only directory name provided
        obspyFormats = ['AH','ALSEP_PSE','ALSEP_WTH','ALSEP_WTN','CSS','DMX','GCF','GSE1','GSE2','KINEMETRICS_EVT','MSEED','NNSA_KB_CORE','PDAS','PICKLE','Q','REFTEK130','RG16','SAC','SACXY','SEG2','SEGY','SEISAN','SH_ASC','SLIST','SU','TSPAIR','WAV','WIN','Y']
        for file in datapath.iterdir():
            ext = file.suffix[1:]
            rawFormat = False
            if ext.isnumeric():
                if float(ext) >= 0 and float(ext) < 367:
                    rawFormat=True
            
            if ext.upper() in obspyFormats or rawFormat:
                filesinfolder = True
                folderPathList.append(datapath)
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
        rawDataIN.attach_response(inv)  
        if type(rawDataIN) is list and len(rawDataIN)==1:
            rawDataIN = rawDataIN[0]
    elif source=='file':
        rawDataIN = obspy.read(str(datapath), starttime=UTCDateTime(params['starttime']), endttime=UTCDateTime(params['endtime']), nearest=True)
        rawDataIN.merge()   
        rawDataIN.attach_response(inv)
    elif type(source) is list or type(datapath) is list:
        pass #Eventually do something
        rawDataIN.attach_response(inv)

    return rawDataIN

#Read data from Tromino
def __read_tromino_files(datapath, params, verbose=False):
    """Function to read data from tromino. Specifically, this has been lightly tested on Tromino 3G+ machines

    Parameters
    ----------
    datapath : str, pathlib.Path()
        The input parameter _datapath_ from sprit.input_params()
    params : HVSRData or HVSRBatch
        The parameters as read in from input_params() and and fetch_data()
    verbose : bool, optional
        Whether to print results to terminal, by default False

    Returns
    -------
    obspy.Stream
        An obspy.Stream object containing the trace data from the Tromino instrument
    """
    dPath = datapath

    strucSizes = {'c':1, 'b':1,'B':1, '?':1,
                'h':2,'H':2,'e':2,
                'i':4,'I':4,'l':4,'L':4,'f':4,
                'q':8,'Q':8,'d':8,
                'n':8,'N':8,'s':16,'p':16,'P':16,'x':16}

    #H (pretty sure it's Q) I L or Q all seem to work (probably not Q?)
    structFormat = 'H'
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

    startByte=24576
    comp1 = dataArr[startByte::3] - medVal
    comp2 = dataArr[startByte+1::3] - medVal
    comp3 = dataArr[startByte+2::3] - medVal
    headerBytes = dataArr[:startByte]

    #fig, ax = plt.subplots(3, sharex=True, sharey=True)
    #ax[0].plot(comp1, linewidth=0.1, c='k')
    #ax[1].plot(comp2, linewidth=0.1, c='k')
    #ax[2].plot(comp3, linewidth=0.1, c='k')

    sTime = obspy.UTCDateTime(params['acq_date'].year, params['acq_date'].month, params['acq_date'].day,
                              params['starttime'].hour, params['starttime'].minute,
                              params['starttime'].second,params['starttime'].microsecond)
    eTime = sTime + (((len(comp1))/128)/60)*60

    traceHeader1 = {'sampling_rate':128,
            'calib' : 1,
            'npts':len(comp1),
            'network':'AM',
            'location':'00',
            'station' : 'TRMNO',
            'channel':'BHE',
            'starttime':sTime}
    
    traceHeader2=traceHeader1.copy()
    traceHeader3=traceHeader1.copy()
    traceHeader2['channel'] = 'BHN'
    traceHeader3['channel'] = 'BHZ'

    trace1 = obspy.Trace(data=comp1, header=traceHeader1)
    trace2 = obspy.Trace(data=comp2, header=traceHeader2)
    trace3 = obspy.Trace(data=comp3, header=traceHeader3)

    st = obspy.Stream([trace1, trace2, trace3])    
    return st

##Helper functions for remove_noise()
#Helper function for removing gaps
def __remove_gaps(stream, window_gaps_obspy):
    """Helper function for removing gaps"""
    #combine overlapping windows
    overlapList = []
    for i in range(len(window_gaps_obspy)-2):
        if window_gaps_obspy[i][1] > window_gaps_obspy[i+1][0]:
            overlapList.append(i)

    for i, t in enumerate(overlapList):
        if i < len(window_gaps_obspy)-2:
            window_gaps_obspy[i][1] = window_gaps_obspy[i+1][1]
            window_gaps_obspy.pop(i+1)

    #Add streams
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

#Helper function for getting windows to remove noise using stalta antitrigger method
def __remove_anti_stalta(stream, sta, lta, thresh, show_plot=False):
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
        Two-item list or tuple with the thresholds for the stalta antitrigger. Reads from remove_noise() function. The first value (index [0]) is the lower threshold, the second value (index [1] is the upper threshold), by default [0.5,5]
    show_plot : bool
        If True, will plot the trigger and stalta values. Reads from remove_noise() function, by default False.

    Returns
    -------
    outStream : obspy.core.stream.Stream object
        Stream with a masked array for the data where 'noise' has been removed

    """
    from obspy.signal.trigger import classic_sta_lta

    sampleRate = float(stream[0].stats.delta)

    sta_samples = sta / sampleRate #Convert to samples
    lta_samples = lta / sampleRate #Convert to samples
    staltaStream = stream.copy()

    for tr in staltaStream:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=UserWarning)
            characteristic_fun = classic_sta_lta(tr, nsta=sta_samples, nlta=lta_samples)

    if show_plot:
        obspy.signal.trigger.plot_trigger(tr, characteristic_fun, thresh[1], thresh[0])
    windows_samples = obspy.signal.trigger.trigger_onset(characteristic_fun, thresh[1], thresh[0])
    
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

#Remove noise saturation
def __remove_noise_saturate(stream, sat_percent, min_win_size):
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

#Helper function for removing data using the noise threshold input from remove_noise()
def __remove_noise_thresh(stream, noise_percent=0.8, lta=30, min_win_size=1):
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

    #Make sure we're not removing single indices (we only want longer than min_win_size)
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

#Helper function for removing data during warmup (when seismometers are still initializing) and "cooldown" (when there may be noise from deactivating seismometer) time, if desired
def __remove_warmup_cooldown(stream, warmup_time = 0, cooldown_time = 0):
    sampleRate = float(stream[0].stats.delta)
    outStream = stream.copy()

    warmup_samples = int(warmup_time / sampleRate) #Convert to samples
    windows_samples=[]
    for tr in stream:
        totalSamples = len(tr.data)-1#float(tr.stats.endtime - tr.stats.starttime) / tr.stats.delta
        cooldown_samples = int(totalSamples - (cooldown_time / sampleRate)) #Convert to samples
    windows_samples = [[0, warmup_samples],[cooldown_samples, totalSamples]]
    if cooldown_time==0:
        windows_samples.pop(1)
    if warmup_time==0:
        windows_samples.pop(0)

    if windows_samples == []:
        pass
    else:
        startT = stream[0].stats.starttime
        endT = stream[-1].stats.endtime
        window_UTC = []
        window_MPL = []
        window_UTC.append([startT, startT])

        for w, win in enumerate(windows_samples):
            for j, tm in enumerate(win):

                if j == 0:
                    window_UTC.append([])
                    window_MPL.append([])
                tSec = tm * sampleRate
                window_UTC[w+1].append(startT+tSec)
                window_MPL[w].append(window_UTC[w][j].matplotlib_date)
        window_UTC.append([endT, endT])

        #window_MPL[w].append(window_UTC[w][i].matplotlib_date)
        outStream = __remove_gaps(stream, window_UTC)
    return outStream

#Plot noise windows
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
    
    fig, ax = _plot_specgram_stream(stream=hvsr_data['stream'], params=hvsr_data, fig=fig, ax=ax, component='Z', stack_type='linear', detrend='mean', fill_gaps=fill_gaps, dbscale=True, return_fig=True, cmap_per=[0.1,0.9])
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

#Helper function for manual window selection 
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

#Helper function for manual window selection to draw boxes to deslect windows for removal
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

#Helper function for updating the canvas and drawing/deleted the boxes
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

#Helper function for getting click event information
def __on_click(event):
    """Helper function for getting click event information"""
    global clickNo
    global x0
    if event.button is MouseButton.RIGHT:
        __remove_on_right(event, xWindows, pathList, windowDrawn, winArtist, lineArtist, fig, ax)

    if event.button is MouseButton.LEFT:            
        clickNo, x0 = __draw_boxes(event, clickNo, xWindows, pathList, windowDrawn, winArtist, lineArtist, x0, fig, ax)    

#Function to select windows using original stream specgram/plots
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
            fig, ax = plot_hvsr(hvsr_data=input, plot_type='spec', returnfig=True, cmap='turbo')
        else:
            hvsr_data = input#.copy()
            input_stream = hvsr_data['stream']
    
    if isinstance(input_stream, obspy.core.stream.Stream):
        fig, ax = _plot_specgram_stream(input_stream, component=['Z'])
    elif isinstance(input_stream, obspy.core.trace.Trace):
        fig, ax = _plot_specgram_stream(input_stream)

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

    hvsr_data['xwindows_out'] = xWindows
    hvsr_data['fig_noise'] = fig
    hvsr_data['ax_noise'] = ax
    return hvsr_data

#Support function to help select_windows run properly
def _on_fig_close(event):
    global fig_closed
    fig_closed = True
    return

#Shows windows with None on input plot
def _get_removed_windows(input, fig=None, ax=None, lineArtist =[], winArtist = [], existing_lineArtists=[], existing_xWindows=[], exist_win_format='matplotlib', keep_line_artists=True, time_type='matplotlib',show_plot=False):
    """This function is for getting Nones from masked arrays and plotting them as windows"""
    if fig is None and ax is None:
        fig, ax = plt.subplots()

    if isinstance(input, (dict, HVSRData)):
        stream = input['stream'].copy()
    elif isinstance(input, (obspy.core.Trace.trace, obspy.core.stream.Stream)):
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

#Helper function for removing windows from data, leaving gaps
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

##Helper functions for process_hvsr()
#Get diffuse field assumption data
def _dfa(params, verbose=False):#, equal_interval_energy, median_daily_psd, verbose=False):
    """Function for performing Diffuse Field Assumption (DFA) analysis
    
        This feature is not yet implemented.
    """
    # Use equal energy for daily PSDs to give small 'events' a chance to contribute
    # the same as large ones, so that P1+P2+P3=1

    x_values=params['ppsds']['Z']['period_bin_centers']

    method=params['method']

    methodList = ['<placeholder>', 'Diffuse Field Assumption', 'Arithmetic Mean', 'Geometric Mean', 'Vector Summation', 'Quadratic Mean', 'Maximum Horizontal Value']
    dfaList = ['dfa', 'diffuse field', 'diffuse field assumption']
    if type(method) is int:
        method = methodList[method]

    if method.lower() in dfaList:
        if verbose:
            print('[Using Diffuuse Field Assumption (DFA)', flush=True)
        params['dfa'] = {}
        params['dfa']['sum_ns_power'] = list()
        params['dfa']['sum_ew_power'] = list()
        params['dfa']['sum_z_power'] = list()
        params['dfa']['time_int_psd'] = {'Z':{}, 'E':{}, 'N':{}}
        params['dfa']['time_values'] = list()
        params['dfa']['equal_interval_energy'] = {'Z':{}, 'E':{}, 'N':{}}

        # Make sure we have all 3 components for every time sample
        for i, t_int in enumerate(params['ppsds']['Z']['current_times_used']):#day_time_values):
            #if day_time not in (day_time_psd[0].keys()) or day_time not in (day_time_psd[1].keys()) or day_time not in (day_time_psd[2].keys()):
            #    continue
            
            #Currently the same as day_time, and probably notneeded to redefine
            time_int = str(t_int)#day_time.split('T')[0]
            if time_int not in params['dfa']['time_values']:
                params['dfa']['time_values'].append(time_int)

            # Initialize the PSDs.
            if time_int not in params['dfa']['time_int_psd']['Z'].keys():
                params['dfa']['time_int_psd']['Z'][time_int] = list()
                params['dfa']['time_int_psd']['E'][time_int] = list()
                params['dfa']['time_int_psd']['N'][time_int] = list()

            params['dfa']['time_int_psd']['Z'][time_int].append(params['ppsds']['Z']['psd_values'][i])
            params['dfa']['time_int_psd']['E'][time_int].append(params['ppsds']['E']['psd_values'][i])
            params['dfa']['time_int_psd']['N'][time_int].append(params['ppsds']['N']['psd_values'][i])

        # For each time_int equalize energy
        for time_int in params['dfa']['time_values']:

            # Each PSD for the time_int
            for k in range(len(params['dfa']['time_int_psd']['Z'][time_int])):
                Pz = list()
                P1 = list()
                P2 = list()
                sum_pz = 0
                sum_p1 = 0
                sum_p2 = 0

                # Each sample of the PSD , convert to power
                for j in range(len(x_values) - 1):
                    pz = __get_power([params['dfa']['time_int_psd']['Z'][time_int][k][j], params['dfa']['time_int_psd']['Z'][time_int][k][j + 1]], [x_values[j], x_values[j + 1]])
                    Pz.append(pz)
                    sum_pz += pz
                    p1 = __get_power([params['dfa']['time_int_psd']['E'][time_int][k][j], params['dfa']['time_int_psd']['E'][time_int][k][j + 1]], [x_values[j], x_values[j + 1]])
                    P1.append(p1)
                    sum_p1 += p1
                    p2 = __get_power([params['dfa']['time_int_psd']['N'][time_int][k][j], params['dfa']['time_int_psd']['N'][time_int][k][j + 1]], [x_values[j], x_values[j + 1]])
                    P2.append(p2)
                    sum_p2 += p2

                sum_power = sum_pz + sum_p1 + sum_p2  # total power

                # Mormalized power
                for j in range(len(x_values) - 1):
                    # Initialize if this is the first sample of the time_int
                    if k == 0:
                        params['dfa']['sum_z_power'].append(Pz[j] / sum_power)
                        params['dfa']['sum_ns_power'].append(P1[j] / sum_power)
                        params['dfa']['sum_ew_power'].append(P2[j] / sum_power)
                    else:
                        params['dfa']['sum_z_power'][j] += (Pz[j] / sum_power)
                        params['dfa']['sum_ns_power'][j] += (P1[j] / sum_power)
                        params['dfa']['sum_ew_power'][j] += (P2[j] / sum_power)
            # Average the normalized daily power
            for j in range(len(x_values) - 1):
                params['dfa']['sum_z_power'][j] /= len(params['dfa']['time_int_psd']['Z'][time_int])
                params['dfa']['sum_ns_power'][j] /= len(params['dfa']['time_int_psd']['Z'][time_int])
                params['dfa']['sum_ew_power'][j] /= len(params['dfa']['time_int_psd']['Z'][time_int])

            params['dfa']['equal_interval_energy']['Z'][time_int] = params['dfa']['sum_z_power']
            params['dfa']['equal_interval_energy']['E'][time_int] = params['dfa']['sum_ns_power']
            params['dfa']['equal_interval_energy']['N'][time_int] = params['dfa']['sum_ew_power']

    return params

#Helper function for smoothing across frequencies
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

        newTPSD = list(np.stack(hvsr_out['hvsr_df'][colName]))
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
        hvsr_out['hvsr_df'][colName] = pd.Series(list(newTPSD), index=hvsr_out['hvsr_df'].index)


    return hvsr_out

#Get an HVSR curve, given an array of x values (freqs), and a dict with psds for three components
def __get_hvsr_curve(x, psd, method, hvsr_data, verbose=False):
    """ Get an HVSR curve from three components over the same time period/frequency intervals

    Parameters
    ----------
        x   : list or array_like
            x value (frequency or period)
        psd : dict
            Dictionary with psd values for three components. Usually read in as part of hvsr_data from process_hvsr
        method : int or str
            Integer or string, read in from process_hvsr method parameter
    
    Returns
    -------
        tuple
         (hvsr_curve, hvsr_tSteps), both np.arrays. hvsr_curve is a numpy array containing H/V ratios at each frequency/period in x.
         hvsr_tSteps only used with diffuse field assumption method. 

    """
    hvsr_curve = []
    hvsr_tSteps = []

    params = hvsr_data
    if method==1 or method =='dfa' or method =='Diffuse Field Assumption':
        warnings.warn('WARNING: DFA method is currently experimental and not supported')
        for j in range(len(x)-1):
            for time_interval in params['ppsds']['Z']['current_times_used']:
                hvsr_curve_tinterval = []
                params = _dfa(params, verbose=verbose)
                eie = params['dfa']['equal_interval_energy']
                if time_interval in list(eie['Z'].keys()) and time_interval in list(eie['E'].keys()) and time_interval in list(eie['N'].keys()):
                    hvsr = math.sqrt(
                        (eie['Z'][str(time_interval)][j] + eie['N'][str(time_interval)][j]) / eie['Z'][str(time_interval)][j])
                    hvsr_curve_tinterval.append(hvsr)
                else:
                    if verbose > 0:
                        print('WARNING: '+ time_interval + ' missing component, skipped!')
                    continue
            #Average overtime
            hvsr_curve.append(np.mean(hvsr_curve_tinterval))
            hvsr_tSteps.append(hvsr_curve_tinterval)
    else:
        for j in range(len(x)-1):
            psd0 = [psd['Z'][j], psd['Z'][j + 1]]
            psd1 = [psd['E'][j], psd['E'][j + 1]]
            psd2 = [psd['N'][j], psd['N'][j + 1]]
            f =    [x[j], x[j + 1]]

            hvsr = __get_hvsr(psd0, psd1, psd2, f, use_method=method)
            
            #hvsr_curve.append(hvsr)
            hvsr_curve.append(hvsr)
        hvsr_tSteps= None #Only used for DFA

    return np.array(hvsr_curve), hvsr_tSteps

#Get HVSR
def __get_hvsr(_dbz, _db1, _db2, _x, use_method=4):
    """
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
    _p2 = __get_power(_db2, _x)
    
    _hz = math.sqrt(_pz)
    _h1 = math.sqrt(_p1)
    _h2 = math.sqrt(_p2)

    _h = {  2: (_h1 + _h2) / 2.0, #Arithmetic mean
            3: math.sqrt(_h1 * _h2), #Geometric mean
            4: math.sqrt(_p1 + _p2), #Vector summation
            5: math.sqrt((_p1 + _p2) / 2.0), #Quadratic mean
            6: max(_h1, _h2)} #Max horizontal value
    
    _hvsr = _h[use_method] / _hz
    return _hvsr

#For converting dB scaled data to power units
def __get_power(_db, _x):
    """Calculate HVSR

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

#Remove decibel scaling
def __remove_db(_db_value):
    """convert dB power to power"""
    _values = list()
    for _d in _db_value:
        _values.append(10 ** (float(_d) / 10.0))
    #FIX THIS
    if _values[1]==0:
       _values[1]=10e-300
    return _values

#Find peaks in the hvsr ccruve
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

#Get additional HVSR params for later calcualtions
def __gethvsrparams(hvsr_out):
    """Private function to get HVSR parameters for later calculations (things like standard deviation, etc)"""

    hvsrp2 = {}
    hvsrm2 = {}
    
    peak_water_level_p=[]
    hvsrp2=[]
    hvsrm=[]
    peak_water_level_m=[]
    
    hvsr_log_std = {}


    hvsr=hvsr_out['hvsr_curve']
    hvsrDF = hvsr_out['hvsr_df']
    if hvsr_out['ind_hvsr_curves'].shape[0] > 0:
        #With arrays, original way of doing it
        hvsr_log_std = np.nanstd(np.log10(hvsr_out['ind_hvsr_curves']), axis=0)

        #With dataframe, updated way to use DF for all time-step tasks, still testing
        stackedData = np.stack(hvsr_out['hvsr_df']['HV_Curves'])
        logStackedata = np.log10(stackedData).tolist()
        for i, r in enumerate(logStackedata):
            logStackedata[i] = np.array(r)

        hvsr_out['hvsr_df']['HV_Curves_Log10'] = logStackedata
        hvsr_log_std = np.nanstd(np.stack(hvsr_out['hvsr_df']['HV_Curves_Log10'][hvsrDF['Use']]), axis=0)

        #The componenets are already calculated, don't need to recalculate aren't calculated at the time-step level
        hvsrp = np.add(hvsr_out['hvsr_curve'], hvsr_out['ind_hvsr_stdDev'])
        hvsrm = np.subtract(hvsr_out['hvsr_curve'], hvsr_out['ind_hvsr_stdDev'])
        hvsrp2 = np.multiply(hvsr, np.exp(hvsr_log_std))
        hvsrm2 = np.divide(hvsr, np.exp(hvsr_log_std))


    newKeys = ['hvsr_log_std', 'hvsrp','hvsrm', 'hvsrp2','hvsrm2']
    newVals = [hvsr_log_std,    hvsrp,  hvsrm,   hvsrp2,  hvsrm2]
    for i, nk in enumerate(newKeys):
        hvsr_out[nk] = np.array(newVals[i])

    return hvsr_out

##Helper Functions for plotting
#Plot hvsr curve, private supporting function for plot_hvsr
def _plot_hvsr(hvsr_data, plot_type, xtype='frequency', fig=None, ax=None, save_dir=None, save_suffix='', show=True, **kwargs):
    """Private function for plotting hvsr curve (or curves with components)
    """
    if 'kwargs' in kwargs.keys():
        kwargs = kwargs['kwargs']

    if fig is None and ax is None:
        fig, ax = plt.subplots()

    if 'xlim' not in kwargs.keys():
        xlim = hvsr_data['hvsr_band']
    else:
        xlim = kwargs['xlim']
    
    if 'ylim' not in kwargs.keys():
        ylim = [0, max(hvsr_data['hvsrp2'])]
        if ylim[1] > 20:
            ylim = [0, max(hvsr_data['hvsr_curve']+1)]

    else:
        ylim = kwargs['ylim']
    
    if 'grid' in kwargs.keys():
        plt.grid(which=kwargs['grid'], alpha=0.25)

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
    
    plotSuff=''
    legendLoc = 'upper right'
    
    plotHVSR = False
    for item in plot_type:
        if item.lower()=='hvsr':
            plotHVSR=True
            ax.plot(x, y, color='k', label='H/V Ratio', zorder=1000)
            plotSuff='HVSRCurve_'
            if '-s' not in plot_type:
                ax.fill_between(x, hvsr_data['hvsrm2'], hvsr_data['hvsrp2'], color='k', alpha=0.2, label='StDev',zorder=997)
                ax.plot(x, hvsr_data['hvsrm2'], color='k', alpha=0.25, linewidth=0.5, zorder=998)
                ax.plot(x, hvsr_data['hvsrp2'], color='k', alpha=0.25, linewidth=0.5, zorder=999)
            else:
                plotSuff = plotSuff+'noStdDev_'
            break

    ax.semilogx()
    ax.set_ylim(ylim)
    ax.set_xlim(xlim)
    ax.set_ylabel('H/V Ratio'+'\n['+hvsr_data['method']+']', fontsize='small',)
    ax.tick_params(axis='x', labelsize=8)
    ax.tick_params(axis='y', labelsize=5)
    ax.set_title(hvsr_data['input_params']['site'])

    #print("label='comp'" in str(ax.__dict__['_axes']))
    for k in plot_type:   
        if k=='p' and 'all' not in plot_type:
            plotSuff=plotSuff+'BestPeak_'
            
            bestPeakScore = 0
            for i, p in enumerate(hvsr_data['PeakReport']):
                if p['Score'] > bestPeakScore:
                    bestPeakScore = p['Score']
                    bestPeak = p

            ax.axvline(bestPeak['f0'],color='k', linestyle='dotted', label='Peak')          
            if 'ann' in plot_type:
                xLoc = bestPeak['f0']
                yLoc = ylim[0] + (ylim[1] - ylim[0]) * 0.008
                ax.text(x=xLoc, y=yLoc, s="Peak at "+str(round(bestPeak['f0'],2))+'Hz',
                            fontsize='xx-small', horizontalalignment='center', verticalalignment='bottom', 
                            bbox=dict(facecolor='w', edgecolor='none', alpha=0.8, pad=0.1))
                plotSuff = plotSuff+'ann_'

        elif k=='p'  and 'all' in plot_type:
            plotSuff = plotSuff+'allPeaks_'

            ax.vlines(hvsr_data['hvsr_peak_freqs'], ax.get_ylim()[0], ax.get_ylim()[1], colors='k', linestyles='dotted', label='Peak')          
            if 'ann' in plot_type:
                for i, p in enumerate(hvsr_data['hvsr_peak_freqs']):
                    y = hvsr_data['hvsr_curve'][hvsr_data['hvsr_peak_indices'][i]]
                    ax.annotate('Peak at '+str(round(p,2))+'Hz', (p, 0.1), xycoords='data', 
                                    horizontalalignment='center', verticalalignment='bottom', 
                                    bbox=dict(facecolor='w', edgecolor='none', alpha=0.8, pad=0.1))
                plotSuff=plotSuff+'ann_'

        if 't' in k:
            plotSuff = plotSuff+'allTWinCurves_'

            if k=='tp':
                for j, t in enumerate(hvsr_data['ind_hvsr_peak_indices']):
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
            for t in hvsr_data['ind_hvsr_curves']:
                ax.plot(x, t, color='k', alpha=0.15, linewidth=0.8, linestyle=':')

        if 'c' in k: #Spectrogram uses a different function, so c is unique to the component plot flag
            plotSuff = plotSuff+'IndComponents_'
            
            if 'c' not in plot_type[0]:#This is part of the hvsr axis
                #fig.tight_layout()
                axis2 = ax.twinx()
                compAxis = axis2
                #axis2 = plt.gca()
                #fig = plt.gcf()
                compAxis.set_ylabel('Amplitude'+'\n[m2/s4/Hz] [dB]')
                compAxis.set_facecolor([0,0,0,0])
                legendLoc2 = 'upper left'
                
            else:
                ax.set_title('') #Remove title
                ax.sharex(kwargs['axes']['hvsr'])
                compAxis = ax
                legendLoc2 = 'upper right'
                
            minY = []
            maxY = []
            for key in hvsr_data['psd_values_tavg']:
                minY.append(min(hvsr_data['ppsd_std_vals_m'][key]))
                maxY.append(max(hvsr_data['ppsd_std_vals_p'][key]))
            minY = min(minY)
            maxY = max(maxY)
            if maxY > 20:
                maxY=20
            rng = maxY-minY
            pad = rng * 0.05
            ylim = [minY-pad, maxY+pad]
        
            compAxis.set_ylabel('COMPONENTS\nAmplitude\n[m2/s4/Hz] [dB]')
            compAxis.set_ylim(ylim)
            yLoc = min(ylim) - abs(ylim[1]-ylim[0]) * 0.05
            ax.text(x=xlim[0], y=yLoc, s=xlabel, 
                        fontsize='x-small', horizontalalignment='right', verticalalignment='top', 
                        bbox=dict(facecolor='w', edgecolor='none', alpha=0.8, pad=0.1))
            #Modify based on whether there are multiple charts
            if plotHVSR:
                linalpha = 0.2
                stdalpha = 0.05
            else:
                linalpha=1
                stdalpha=0.2
            
            #Plot individual components
            y={}
            for key in hvsr_data['psd_values_tavg']:
                y[key] = hvsr_data['psd_values_tavg'][key][:-1]

                if key == 'Z':
                    pltColor = 'k'
                elif key =='E':
                    pltColor = 'b'
                elif key == 'N':
                    pltColor = 'r'

                compAxis.plot(x, y[key], c=pltColor, label=key, alpha=linalpha)
                if '-s' not in plot_type:
                    compAxis.fill_between(x, hvsr_data['ppsd_std_vals_m'][key][:-1], hvsr_data['ppsd_std_vals_p'][key][:-1], color=pltColor, alpha=stdalpha)
                if plot_type[0] != 'c':
                    compAxis.legend(loc=legendLoc2)
            else:
                pass#ax.legend(loc=legendLoc)
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
                        show=show)
    
    return fig, ax

#Private function to help for when to show and format and save plots
def __plot_current_fig(save_dir, filename, fig, ax, plot_suffix, user_suffix, show):
    """Private function to support plot_hvsr, for plotting and showing plots"""
    #plt.gca()
    #plt.gcf()
    #fig.tight_layout() #May need to uncomment this

    #plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)

    if save_dir is not None:
        outFile = save_dir+'/'+filename+'_'+plot_suffix+str(datetime.datetime.today().date())+'_'+user_suffix+'.png'
        fig.savefig(outFile, bbox_inches='tight', pad_inches=0.2)
    if show:
        fig.canvas.draw()#.show()
        #fig.tight_layout()
        #plt.ion()
    return

#Plot specgtrogram, private supporting function for plot_hvsr
def _plot_specgram_hvsr(hvsr_data, fig=None, ax=None, save_dir=None, save_suffix='',**kwargs):
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

    # Setup
    ppsds = hvsr_data['ppsds']#[k]['current_times_used']
    import matplotlib.dates as mdates
    anyKey = list(ppsds.keys())[0]
    
    # Get data
    psdArr = np.stack(hvsr_data['hvsr_df']['HV_Curves'].apply(np.flip))
    useArr = np.array(hvsr_data['hvsr_df']['Use'])
    useArr = np.tile(useArr, (psdArr.shape[1], 1)).astype(int)
    useArr = np.clip(useArr, a_min=0.15, a_max=1)

    # Get times
    xmin = hvsr_data['hvsr_df']['TimesProcessed_MPL'].min()
    xmax = hvsr_data['hvsr_df']['TimesProcessed_MPL'].max()

    #Format times
    tTicks = mdates.MinuteLocator(byminute=range(0,60,5))
    ax.xaxis.set_major_locator(tTicks)
    tTicks_minor = mdates.SecondLocator(bysecond=[0])
    ax.xaxis.set_minor_locator(tTicks_minor)

    tLabels = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(tLabels)
    ax.tick_params(axis='both', labelsize='x-small')

    #Get day label for bottom of chart
    if hvsr_data['hvsr_df'].index[0].date() != hvsr_data['hvsr_df'].index[-1].date():
        day = str(hvsr_data['hvsr_df'].index[0].date())+' - '+str(hvsr_data['hvsr_df'].index[-1].date())
    else:
        day = str(hvsr_data['hvsr_df'].index[0].date())

    #Get extents
    ymin = hvsr_data['input_params']['hvsr_band'][0]
    ymax = hvsr_data['input_params']['hvsr_band'][1]

    freqticks = np.flip(hvsr_data['x_freqs'][anyKey])
    yminind = np.argmin(np.abs(ymin-freqticks))
    ymaxind = np.argmin(np.abs(ymax-freqticks))
    freqticks = freqticks[yminind:ymaxind]
    freqticks = np.logspace(np.log10(freqticks[0]), np.log10(freqticks[-1]), num=999)

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
    im = ax.imshow(linear_arr.T, origin='lower', extent=extList, aspect='auto', alpha=useArr, **kwargs)
    ax.tick_params(left=True, right=True, top=True)

    if peak_plot:
        ax.axhline(hvsr_data['BestPeak']['f0'], c='k',  linestyle='dotted', zorder=1000)

    if annotate:
        if float(hvsr_data['BestPeak']['f0']) < 1:
            boxYPerc = 0.998
            vertAlign = 'top'
        else:
            boxYPerc = 0.002
            vertAlign = 'bottom'
        xLocation = float(xmin) + (float(xmax)-float(xmin))*0.99
        yLocation = hvsr_data['input_params']['hvsr_band'][0] + (hvsr_data['input_params']['hvsr_band'][1]-hvsr_data['input_params']['hvsr_band'][0])*(boxYPerc)
        ann = ax.text(x=xLocation, y=yLocation, fontsize='x-small', s=f"Peak at {hvsr_data['BestPeak']['f0']:0.2f} Hz", ha='right', va=vertAlign, 
                      bbox={'alpha':0.8, 'edgecolor':None, 'linewidth':0, 'fc':'w', 'pad':0.3})


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


#Plot spectrogram from stream
def _plot_specgram_stream(stream, params=None, component='Z', stack_type='linear', detrend='mean', dbscale=True, fill_gaps=None,fig=None, ax=None, cmap_per=[0.1,0.9], ylimstd=5, show_plot=False, return_fig=True,  **kwargs):
    """Function for plotting spectrogram in a nice matplotlib chart from an obspy.stream

    For more details on main function being called, see https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.specgram.html 

    Parameters
    ----------
    stream : obspy.core.stream.Stream object
        Stream for which to plot spectrogram
    params : dict, optional
        If dict, will read the hvsr_band from the a dictionary with a key ['hvsr_band'] (like the parameters dictionary). Otherwise, can read in the hvsr_band as a two-item list. Or, if None, defaults to [0.4,40], by default None.
    component : str or list, default='Z'
        If string, should be one character long component, by default 'Z.' If list, can contain 'E', 'N', 'Z', and will stack them per stack_type and stream.stack() method in obspy to make spectrogram.
    stack_type : str, default = 'linear'
        Parameter to be read directly into stack_type parameter of Stream.stack() method of obspy streams, by default 'linear'. See https://docs.obspy.org/packages/autogen/obspy.core.stream.Stream.stack.html
        Only matters if more than one component used.
    detrend : str, default = 'mean'
        Parameter to be read directly into detrend parameter of matplotlib.pyplot.specgram, by default 'mean'. See: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.specgram.html
    dbscale : bool, default = True
        If True, scale parameter of matplotlib.pyplot.specgram set to 'dB', by default True
    return_fig : bool, default = True
        Whether to return the figure from the function or just show it, by default True
    cmap_per : list, default = [0.1, 0.9]
        Two-item list wwith clip limits as percentage of values of colormap, so extremes do not taint colormap, by default [0.1,0.9]

    Returns
    -------
    fig
        If return_fig is True, matplotlib figure is returned
    ax
        If return_fig is True, matplotlib axis is returned
    """ 
    og_stream = stream.copy()

    #Get the latest start time and earliest end times of all components
    traceList = []
    maxStartTime = obspy.UTCDateTime(-1e10) #Go back pretty far (almost 400 years) to start with
    minEndTime = obspy.UTCDateTime(1e10)
    for comp in ['E', 'N', 'Z']:
        #Get all traces from selected component in comp_st
        if isinstance(stream[0].data, np.ma.masked_array):
            stream = stream.split() 
        comp_st = stream.select(component=comp).copy()
        stream.merge()
        
        if comp in component:
            for tr in comp_st:
                #Get all traces specified for use in one list
                traceList.append(tr)

            if stream[0].stats.starttime > maxStartTime:
                maxStartTime = stream[0].stats.starttime
            if stream[0].stats.endtime < minEndTime:
                minEndTime = stream[0].stats.endtime

            if isinstance(comp_st[0].data, np.ma.masked_array):
                comp_st = comp_st.split()  

    #Trim all traces to the same start/end time for total
    for tr in traceList:
        tr.trim(starttime=maxStartTime, endtime=minEndTime)
    og_stream.trim(starttime=maxStartTime, endtime=minEndTime)      

    #Combine all traces into single, stacked trace/stream
    stream = obspy.Stream(traceList)
    stream.merge()
    if len(stream)>1:
        stream.stack(group_by='all', npts_tol=200, stack_type=stack_type)  

    newFig= False
    if fig is None and ax is None:
        #Organize the chart layout
        mosaic = [['spec'],
                  ['spec'],
                  ['spec'],
                  ['spec'],
                  ['spec'],
                  ['spec'],
                  ['signalz'],
                  ['signalz'], 
                  ['signaln'], 
                  ['signale']]
        fig, ax = plt.subplot_mosaic(mosaic, sharex=True, gridspec_kw={'hspace':0.3})
        #fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True)
        newFig = True

    
    data = stream[0].data
    if isinstance(data, np.ma.MaskedArray) and fill_gaps is not None:
        data = data.filled(fill_gaps)
    sample_rate = stream[0].stats.sampling_rate

    if 'cmap' in kwargs.keys():
        cmap=kwargs['cmap']
    else:
        cmap='turbo'

    if params is None:
        hvsr_band = [0.4, 40]
    else:
        hvsr_band = params['hvsr_band']
    ymin = hvsr_band[0]
    ymax = hvsr_band[1]

    if dbscale:
        scale='dB'
    else:
        scale=None
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=RuntimeWarning)
        spec, freqs, times, im = ax['spec'].specgram(x=data, Fs=sample_rate, detrend=detrend, scale_by_freq=True, scale=scale)
    im.remove()

    difference_array = freqs-ymin
    for i, d in enumerate(difference_array):
        if d > 0:
            if i-1 < 0:
                i=1
            minfreqInd = i-1
            break
            
    difference_array = freqs-ymax
    for i, d in enumerate(difference_array):
        if d > 0:
            maxfreqInd = i-1
            break

    array_displayed = spec[minfreqInd:maxfreqInd,:]
    #freqs_displayed = freqs[minfreqInd:maxfreqInd]
    #im.set_data(array_displayed)
    vmin = np.nanpercentile(array_displayed, cmap_per[0]*100)
    vmax = np.nanpercentile(array_displayed, cmap_per[1]*100)
  
    
    decimation_factor = 10

    sTime = stream[0].stats.starttime
    timeList = {}
    mplTimes = {}
    
    if isinstance(og_stream[0].data, np.ma.masked_array):
        og_stream = og_stream.split()      
    og_stream.decimate(decimation_factor)
    og_stream.merge()

    for tr in og_stream:
        key = tr.stats.component
        timeList[key] = []
        mplTimes[key] = []
        for t in np.ma.getdata(tr.times()):
            newt = sTime + t
            timeList[key].append(newt)
            mplTimes[key].append(newt.matplotlib_date)
    
    #Ensure that the min and max times for each component are the same
    for i, k in enumerate(mplTimes.keys()):
        currMin = np.min(list(map(np.min, mplTimes[k])))
        currMax = np.max(list(map(np.max, mplTimes[k])))

        if i == 0:
            xmin = currMin
            xmax = currMax
        else:
            if xmin > currMin:
                xmin = currMin
            if xmax < currMax:
                xmax = currMax     
    
    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    im = ax['spec'].imshow(array_displayed, norm=norm, cmap=cmap, aspect='auto', interpolation=None, extent=[xmin,xmax,ymax,ymin])

    ax['spec'].set_xlim([xmin, xmax])
    ax['spec'].set_ylim([ymin, ymax])
    ax['spec'].semilogy() 
    
    #cbar = plt.colorbar(mappable=im)
    #cbar.set_label('Power Spectral Density [dB]')
    #stream.spectrogram(samp_rate=sample_rate, axes=ax, per_lap=0.75, log=True, title=title, cmap='turbo', dbscale=dbscale, show=False)
    
    ax['spec'].xaxis_date()
    ax['signalz'].xaxis_date()
    ax['signaln'].xaxis_date()
    ax['signale'].xaxis_date()
    #tTicks = mdates.MinuteLocator(interval=5)
    #ax[0].xaxis.set_major_locator(tTicks)
    ax['signale'].xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0,60,5)))
    ax['signale'].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax['signale'].xaxis.set_minor_locator(mdates.MinuteLocator(interval=1))
    ax['signale'].tick_params(axis='x', labelsize=8)
    
    ax['signalz'].plot(mplTimes['Z'],og_stream.select(component='Z')[0].data, color='k', linewidth=0.25)
    ax['signaln'].plot(mplTimes['N'],og_stream.select(component='N')[0].data, color='k', linewidth=0.1)
    ax['signale'].plot(mplTimes['E'],og_stream.select(component='E')[0].data, color='k', linewidth=0.1)

    ax['spec'].set_ylabel('Spectrogram: {}'.format(component))
    ax['signalz'].set_ylabel('Z')
    ax['signaln'].set_ylabel('N')
    ax['signale'].set_ylabel('E')
    
    for comp in mplTimes.keys():
        stD = np.abs(np.nanstd(np.ma.getdata(og_stream.select(component=comp)[0].data)))
        dmed = np.nanmedian(np.ma.getdata(og_stream.select(component=comp)[0].data))
        key = 'signal'+comp.lower()
        ax[key].set_ylim([dmed-ylimstd*stD, dmed+ylimstd*stD])
    
    if params is None:
        fig.suptitle('HVSR Site: Spectrogram and Data')
    elif 'title' in kwargs.keys():
        fig.suptitle(kwargs['title'])
    else:
        if 'input_params' in params.keys():
            sitename = params['input_params']['site']
        else:
            sitename = params['site']
        fig.suptitle('{}\nSpectrogram and Data'.format(sitename))
    
    day = "{}-{}-{}".format(stream[0].stats.starttime.year, stream[0].stats.starttime.month, stream[0].stats.starttime.day)
    ax['signale'].set_xlabel('UTC Time \n'+day)

    if newFig:
        ogFigsize = matplotlib.rcParams['figure.figsize']
        fig = plt.gcf()
        matplotlib.rcParams['figure.figsize'] = (40, 4)
        #plt.rcParams['figure.dpi'] = 100
        #plt.rcParams['figure.figsize'] = (5,4)
        #fig.tight_layout()
        plt.rcParams['figure.figsize'] = ogFigsize
        
    fig.canvas.draw()

    if show_plot:
        plt.show()
    
    if return_fig:
        return fig, ax
    
    return


# HELPER functions for checking peaks
# Initialize peaks
def __init_peaks(_x, _y, _index_list, _hvsr_band, peak_freq_range=[0.4, 40], _min_peak_amp=1):
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
def __check_curve_reliability(hvsr_data, _peak):
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
    window_len = (hvsr_data['ppsds'][anyKey]['len'] * delta) #Window length in seconds
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
                    if hvsr_data['hvsr_log_std'][i] >= compVal:
                        test3=False
                        failCount +=1

                else: #if peak freq is less than 0.5
                    compVal = 3
                    if hvsr_data['hvsr_log_std'][i] >= compVal:
                        test3=False
                        failCount +=1

        if test1:
            _peak[_i]['Report']['Lw'] = f'{round(peakFreq,3)} > {10/int(window_len):0.3} (10 / {int(window_len)})  {sprit_utils.check_mark()}'
        else:
            _peak[_i]['Report']['Lw'] = f'{round(peakFreq,3)} > {10/int(window_len):0.3} (10 / {int(window_len)})  {sprit_utils.x_mark()}'

        if test2:
            _peak[_i]['Report']['Nc'] = f'{int(nc)} > 200  {sprit_utils.check_mark()}'
        else:
            _peak[_i]['Report']['Nc'] = f'{int(nc)} > 200  {sprit_utils.x_mark()}'

        if test3:
            _peak[_i]['Report']['σ_A(f)'] = f'H/V Amp. St.Dev. for {peakFreq*0.5:0.3f}-{peakFreq*2:0.3f}Hz < {compVal}  {sprit_utils.check_mark()}'
        else:
            _peak[_i]['Report']['σ_A(f)'] = f'H/V Amp. St.Dev. for {peakFreq*0.5:0.3f}-{peakFreq*2:0.3f}Hz < {compVal}  {sprit_utils.x_mark()}'

        _peak[_i]['PassList']['WindowLengthFreq.'] = test1
        _peak[_i]['PassList']['SignificantCycles'] = test2
        _peak[_i]['PassList']['LowCurveStDevOverTime'] = test3
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
        _peak[_i]['f-'] = sprit_utils.x_mark()
        _peak[_i]['Report']['A(f-)'] = f"H/V curve > {_peak[_i]['A0']/2:0.2f} for all {_peak[_i]['A0']/4:0.2f} Hz-{_peak[_i]['A0']:0.3f} Hz {sprit_utils.x_mark()}"
        _peak[_i]['PassList']['PeakProminenceBelow'] = False #Start with assumption that it is False until we find an instance where it is True
        for _j in range(jstart, -1, -1):
            # There exist one frequency f-, lying between f0/4 and f0, such that A0 / A(f-) > 2.
            if (float(_peak[_i]['f0']) / 4.0 <= _x[_j] < float(_peak[_i]['f0'])) and float(_peak[_i]['A0']) / _y[_j] > 2.0:
                _peak[_i]['Score'] += 1
                _peak[_i]['f-'] = '%10.3f %1s' % (_x[_j], sprit_utils.check_mark())
                _peak[_i]['Report']['A(f-)'] = f"Amp. of H/V Curve @{_x[_j]:0.3f}Hz ({_y[_j]:0.3f}) < {_peak[_i]['A0']/2:0.3f} {sprit_utils.check_mark()}"
                _peak[_i]['PassList']['PeakProminenceBelow'] = True
                break
            else:
                pass
    
    if do_rank:
        max_rank += 1
    for _i in range(len(_peak)):
        #Initialize as False
        _peak[_i]['f+'] = sprit_utils.x_mark()
        _peak[_i]['Report']['A(f+)'] = f"H/V curve > {_peak[_i]['A0']/2:0.2f} for all {_peak[_i]['A0']:0.2f} Hz-{_peak[_i]['A0']*4:0.3f} Hz {sprit_utils.x_mark()}"
        _peak[_i]['PassList']['PeakProminenceAbove'] = False
        for _j in range(len(_x) - 1):

            # There exist one frequency f+, lying between f0 and 4*f0, such that A0 / A(f+) > 2.
            if float(_peak[_i]['f0']) * 4.0 >= _x[_j] > float(_peak[_i]['f0']) and \
                    float(_peak[_i]['A0']) / _y[_j] > 2.0:
                _peak[_i]['Score'] += 1
                _peak[_i]['f+'] = f"{_x[_j]:0.3f} {sprit_utils.check_mark()}"
                _peak[_i]['Report']['A(f+)'] = f"H/V Curve at {_x[_j]:0.2f} Hz: {_y[_j]:0.2f} < {_peak[_i]['A0']/2:0.2f} (f0/2) {sprit_utils.check_mark()}"
                _peak[_i]['PassList']['PeakProminenceAbove'] = True
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
            _peak[_i]['Report']['A0'] = f"Amplitude of peak ({_peak[_i]['A0']:0.2f}) > {int(_a0)} {sprit_utils.check_mark()}"
            _peak[_i]['Score'] += 1
            _peak[_i]['PassList']['PeakAmpClarity'] = True
        else:
            _peak[_i]['Report']['A0'] = '%0.2f > %0.1f %1s' % (_peak[_i]['A0'], _a0, sprit_utils.x_mark())
            _peak[_i]['PassList']['PeakAmpClarity'] = False

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
    _found_m = list()
    for _i in range(len(_peak)):
        _dx = 1000000.
        _found_m.append(False)
        _peak[_i]['Report']['P-'] = sprit_utils.x_mark()
        for _j in range(len(_peakm)):
            if abs(_peakm[_j]['f0'] - _peak[_i]['f0']) < _dx:
                _index = _j
                _dx = abs(_peakm[_j]['f0'] - _peak[_i]['f0'])
            if _peak[_i]['f0'] * 0.95 <= _peakm[_j]['f0'] <= _peak[_i]['f0'] * 1.05:
                _peak[_i]['Report']['P-'] = f"{_peakm[_j]['f0']:0.2f} Hz within ±5% of {_peak[_i]['f0']:0.2f} Hz {sprit_utils.check_mark()}"
                _found_m[_i] = True
                break
        if _peak[_i]['Report']['P-'] == sprit_utils.x_mark():
            _peak[_i]['Report']['P-'] = f"{_peakm[_j]['f0']:0.2f} Hz within ±5% of {_peak[_i]['f0']:0.2f} Hz {sprit_utils.x_mark()}"

    # Then Check above
    _found_p = list()
    for _i in range(len(_peak)):
        _dx = 1000000.
        _found_p.append(False)
        _peak[_i]['Report']['P+'] = sprit_utils.x_mark()
        for _j in range(len(_peakp)):
            if abs(_peakp[_j]['f0'] - _peak[_i]['f0']) < _dx:

                _dx = abs(_peakp[_j]['f0'] - _peak[_i]['f0'])
            if _peak[_i]['f0'] * 0.95 <= _peakp[_j]['f0'] <= _peak[_i]['f0'] * 1.05:
                if _found_m[_i]:
                    _peak[_i]['Report']['P+'] = f"{_peakp[_j]['f0']:0.2f} Hz within ±5% of {_peak[_i]['f0']:0.2f} Hz {sprit_utils.check_mark()}"
                    _peak[_i]['Score'] += 1
                    _peak[_i]['PassList']['FreqStability'] = True
                else:
                    _peak[_i]['Report']['P+'] = f"{_peakp[_j]['f0']:0.2f} Hz within ±5% of {_peak[_i]['f0']:0.2f} Hz {sprit_utils.x_mark()}"
                    _peak[_i]['PassList']['FreqStability'] = False
                break
            else:
                _peak[_i]['Report']['P+'] = f"{_peakp[_j]['f0']:0.2f} Hz within ±5% of {_peak[_i]['f0']:0.2f} Hz {sprit_utils.x_mark()}"
                _peak[_i]['PassList']['FreqStability'] = False                
        if _peak[_i]['Report']['P+'] == sprit_utils.x_mark() and len(_peakp) > 0:
            _peak[_i]['Report']['P+'] = f"{_peakp[_j]['f0']:0.2f} Hz within ±5% of {_peak[_i]['f0']:0.2f} Hz {sprit_utils.x_mark()}"

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
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils.check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['PeakStability_FreqStD'] = True
            else:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils.x_mark()}"
                _this_peak['PassList']['PeakStability_FreqStD'] = False

            _t = 0.48
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils.check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['PeakStability_AmpStD'] = True
            else:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils.check_mark()}"
                _this_peak['PassList']['PeakStability_AmpStD'] = False

        elif 0.2 <= _this_peak['f0'] < 0.5:
            _e = 0.2
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils.check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['PeakStability_FreqStD'] = True
            else:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils.x_mark()}"
                _this_peak['PassList']['PeakStability_FreqStD'] = False

            _t = 0.40
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils.check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['PeakStability_AmpStD'] = True
            else:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils.check_mark()}"
                _this_peak['PassList']['PeakStability_AmpStD'] = False

        elif 0.5 <= _this_peak['f0'] < 1.0:
            _e = 0.15
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils.check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['PeakStability_FreqStD'] = True
            else:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils.x_mark()}"
                _this_peak['PassList']['PeakStability_FreqStD'] = False

            _t = 0.3
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils.check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['PeakStability_AmpStD'] = True
            else:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils.check_mark()}"
                _this_peak['PassList']['PeakStability_AmpStD'] = False

        elif 1.0 <= _this_peak['f0'] <= 2.0:
            _e = 0.1
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils.check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['PeakStability_FreqStD'] = True
            else:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils.x_mark()}"
                _this_peak['PassList']['PeakStability_FreqStD'] = False

            _t = 0.25
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils.check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['PeakStability_AmpStD'] = True
            else:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils.check_mark()}"
                _this_peak['PassList']['PeakStability_AmpStD'] = False

        elif _this_peak['f0'] > 0.2:
            _e = 0.05
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils.check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['PeakStability_FreqStD'] = True
            else:
                _peak[_i]['Report']['Sf'] = f"St.Dev. of Peak Freq. ({_stdf[_i]:0.2f}) < {(_e * _this_peak['f0']):0.3f} {sprit_utils.x_mark()}"
                _this_peak['PassList']['PeakStability_FreqStD'] = False

            _t = 0.2
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils.check_mark()}"
                _this_peak['Score'] += 1
                _this_peak['PassList']['PeakStability_AmpStD'] = True
            else:
                _peak[_i]['Report']['Sa'] = f"St.Dev. of Peak Amp. ({_hvsr_log_std[_i]:0.3f}) < {_t:0.2f} {sprit_utils.check_mark()}"
                _this_peak['PassList']['PeakStability_FreqStD'] = False

    return _peak


# Get frequency standard deviation
def __get_stdf(x_values, indexList, hvsrPeaks):
    """Private function to get frequency standard deviation, from multiple time-step HVSR curves"""
    stdf = list()
    for index in indexList:
        point = list()
        for j in range(len(hvsrPeaks)):
            p = None
            for k in range(len(hvsrPeaks.iloc[j])):
                if p is None:
                    p = hvsrPeaks.iloc[j][k]
                else:
                    # Find closest peak in current time to (current) hvsr peak
                    if abs(index - hvsrPeaks.iloc[j][k]) < abs(index - p):
                        p = hvsrPeaks.iloc[j][k]
                        # p = hvsrPeaks[j][k]
                        # print(p=p1, p, p1)
            if p is not None:
                point.append(p)
        point.append(index)
        v = list()
        for pl in range(len(point)):
            v.append(x_values[point[pl]])
        stdf.append(np.std(v))
    return stdf

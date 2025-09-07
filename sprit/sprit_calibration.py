"""
This module will be used for calibration of the ambient HVSR data acquired near wells 
to derive a relation between the resonant frequency and the depth to bedrock beneath the subsurface.

"""
import importlib
import inspect
import numbers
import os
import pathlib
from warnings import warn

import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

try:  # For distribution
    from sprit import sprit_hvsr
    from sprit import sprit_plot
except Exception as e:  # For testing
    import sprit_hvsr
    import sprit_plot

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

RESOURCE_DIR = pathlib.Path(str(importlib.resources.files('sprit'))).joinpath('resources')
sample_data_dir = RESOURCE_DIR.joinpath("sample_data")
sampleFileName = {'sample_1': sample_data_dir.joinpath("SampleHVSRSite1_2024-06-13_1633-1705.csv")}

def __get_ip_df_params():
    ip_params = inspect.signature(sprit_hvsr.input_params).parameters
    fd_params = inspect.signature(sprit_hvsr.fetch_data).parameters
    return ip_params, fd_params

models = ["ISGS_All", "ISGS_North", "ISGS_Central", "ISGS_Southeast", "ISGS_Southwest",
                    "ISGS_North_Central", "ISGS_SW_SE", "Minnesota_All", 
                    "Minnesota_Twin_Cities", "Minnesota_South_Central", 
                    "Minnesota_River_Valleys", "Rhine_Graben",
                    "Ibsvon_A", "Ibsvon_B","Delgado_A", "Delgado_B", 
                    "Parolai", "Hinzen", "Birgoren", "Ozalaybey", "Harutoonian",
                    "Fairchild", "DelMonaco", "Tun", "Thabet_A", "Thabet_B",
                    "Thabet_C", "Thabet_D"]

swave = ["shear", "swave", "shearwave", "rayleigh", "rayleighwave", "vs"]

model_list = list(map(lambda x : x.casefold(), models))

model_parameters = {"ISGS_All" : (141.81, 1.582), "ISGS_North" : (142.95,1.312), "ISGS_Central" : (119.17, 1.21), "ISGS_Southeast" : (67.973,1.166),
                    "ISGS_Southwest": (61.238,1.003), "ISGS_North_Central" : (117.44, 1.095), "ISGS_SW_SE" : (62.62, 1.039),
                    "Minnesota_All" : (121, 1.323), "Minnesota_Twin_Cities" : (129, 1.295), "Minnesota_South_Central" : (135, 1.248),
                    "Minnesota_River_Valleys" : (83, 1.232), "Rhine_Graben" : (96, 1.388), 
                    "Ibsvon_A" : (96, 1.388), "Ibsvon_B" : (146, 1.375), "Delgado_A" : (55.11, 1.256), 
                    "Delgado_B" : (55.64, 1.268), "Parolai" : (108, 1.551), "Hinzen" : (137, 1.19), "Birgoren" : (150.99, 1.153), 
                    "Ozalaybey" : (141, 1.270), "Harutoonian" : (73, 1.170), "Fairchild" : (90.53, 1), "DelMonaco" : (53.461, 1.01), 
                    "Tun" : (136, 1.357), "Thabet_A": (117.13, 1.197), "Thabet_B":(105.14, 0.899), "Thabet_C":(132.67, 1.084), "Thabet_D":(116.62, 1.169)}


def power_law(f, a, b):
    return a*(f**-b)


def calculate_depth(freq_input,
                    depth_model="ISGS_All",
                    freq_col="Peak",
                    calculate_depth_in_feet=False,
                    calculate_elevation=True,
                    show_depth_curve=True,
                    surface_elevation_data='Elevation',
                    bedrock_elevation_column="BedrockElevation",
                    depth_column="BedrockDepth",
                    verbose=False,    # if verbose is True, display warnings otherwise not
                    export_path=None,
                    swave_velocity=563.0,
                    decimal_places=3,
                    depth_model_in_latex=False,
                    fig=None,
                    ax=None,
                    #group_by = "County", -> make a kwarg
                    **kwargs):
    """Calculate depth(s) based on a frequency input (usually HVSRData or HVSRBatch oject) and a frequency-depth depth_model (usually a power law relationship).

    Parameters
    ----------
    freq_input : HVSRData, HVSRBatch, float, int, or filepath, optional
        Input with frequency information, by default {sprit_hvsr.HVSRData, sprit_hvsr.HVSRBatch, float, os.PathLike}
    depth_model : str, tuple, list, or dict, optional
        Model describing a relationship between frequency and depth, by default "ISGS_All"
    calculate_depth_in_feet : bool, optional
        Whether to calculate depth in feet (in addition to meters, which is done by default)
    freq_col : str, optional
        Name of the column containing the frequency information of the peak, by default "Peak" (per HVSRData.Table_Report output)
    calculate_elevation : bool, optional
        Whether or not to calculate elevation, by default True
    surface_elevation_data : str or numeric, optional
        The name of the column or a manually specified numeric value to use for the surface elevation value, by default "Elevation"
    bedrock_elevation_column : str, optional
        The name of the column in the TableReport for the bedrock elevation of the point.
        This can be either the name of a column in a table (i.e., Table_Report) or a numeric value, by default "BedrockElevation"
    depth_column : str, optional
        _description_, by default "BedrockDepth"
    verbose : bool, optional
        Whether or not to print information about the processing to the terminal, by default False
    export_path : _type_, optional
        _description_, by default None
    swave_velocity : float, optional
        Shear wave velocity to use for depth calculations in meters/second, 
        if using the quarter wavelength shear wave velocity method, by default 563.0
    decimal_places : int, optional
        Number of decimal places to round depth results, by default 3

    Returns
    -------
    HVSRBatch or list if those are input; otherwise, HVSRData object
        The returns are the same type as freq_input, except filepath which returns pandas.DataFrame

    """
    orig_args = locals()
    ip_params, fd_params = __get_ip_df_params()

    # Break out if list (of random or not) items
    if isinstance(freq_input, (list, tuple)):
        outputList = []
        for item in freq_input:
            if 'freq_input' in orig_args:
                orig_args.pop('freq_input')
            calc_depth_kwargs = orig_args
            outputList.append(calculate_depth(freq_input=item, **calc_depth_kwargs))
        return outputList
    
    # Break out for Batch data
    if isinstance(freq_input, sprit_hvsr.HVSRBatch):
        newBatchList = []
        # Iterate through each site/HVSRData object and run calculate_depth()
        for site in freq_input:
            if 'freq_input' in orig_args:
                orig_args.pop('freq_input')
            calc_depth_kwargs = orig_args
            newBatchList.append(calculate_depth(freq_input=freq_input[site], **calc_depth_kwargs))
        return sprit_hvsr.HVSRBatch(newBatchList, df_as_read=freq_input.input_df)    
    
    # initialize values
    a = 0
    b = 0
    params = None

    # Fetch parameters for frequency-depth model
    if isinstance(depth_model, (tuple, list, dict)):
        (a, b) = depth_model
        if a == 0 or b == 0:
            raise ValueError(f"Model parameters (a, b)={depth_model} cannot be zero, check model inputs.")
    elif isinstance(depth_model, str):

        if depth_model.casefold() in list(map(str.casefold, model_parameters)):
            for k, v in model_parameters.items():
                if depth_model.casefold() == k.casefold():
                    (a, b) = v
                    break

        elif depth_model.casefold() in swave:
            params = depth_model.casefold()

        elif depth_model.casefold() == "all":
            params = depth_model.casefold()

        else:   # parameters a and b could be passed in as a parsable string
            params = depth_model.split(',')
            # Work on re update[int(s) for s in re.findall(r"[-+]?(?:\d*\.*\d+)", 
            # depth_model)]  #figure this out later for floating points; works for integers
            (a, b) = params
            if a == 0 or b == 0:
                raise ValueError("Parameters cannot be zero, check model inputs")            

    if b < 0:
        b = b * -1

    # Get frequency input
    # Checking if freq_input is HVSRData object
    if isinstance(freq_input, (sprit_hvsr.HVSRData, str, bytes, os.PathLike, float, int)):
        # Get the table report
        # If not HVSRData object, let's make a dummy one
        if not isinstance(freq_input, sprit_hvsr.HVSRData):
            # Check if freq_input is float/int, convert to HVSRData (use kwargs too)
            if isinstance(freq_input, (float, int)):
                if freq_input <= 0:
                    raise ValueError("Peak Frequency cannot be zero or negative")
                
                if isinstance(surface_elevation_data, numbers.Number):
                    surface_elevation_col = 'Elevation'
                else:
                    surface_elevation_col = surface_elevation_data
                
                tableReport = pd.DataFrame(columns=['Site Name',
                                                    'Acq_Date',
                                                    'XCoord',
                                                    'YCoord',
                                                    surface_elevation_col,
                                                    freq_col,
                                                    'Peak_StDev'
                                                    'PeakPasses'])
                tableReport.loc[0, freq_col] = freq_input
                
                # Get extra parameters read in via kwargs, if applicable
                paramDict = {'input_data': "from_user"}
                if isinstance(surface_elevation_data, numbers.Number):
                    kwargs[surface_elevation_col] = surface_elevation_data
                    surface_elevation_data = 'Elevation'
                
                for kw, val in kwargs.items():
                    if kw.lower() in [col.lower() for col in tableReport.columns]:
                        colInd = [col.lower() for col in tableReport.columns].index(kw.lower())
                        tableReport.iloc[0, colInd] = val
                        
                    if kw in ip_params or kw in fd_params:
                        paramDict[kw] = val
                paramDict['Table_Report'] = tableReport
                freq_input = sprit_hvsr.HVSRData(paramDict)
            # Otherwise, assume it is a file to read in
            else:
                if pathlib.Path(freq_input).is_dir():
                    filepathGlob = pathlib.Path(freq_input).glob('*.hvsr')
                    batchList = []
                    for hvsrfile in filepathGlob:
                        batchList.append(sprit_hvsr.import_data(hvsrfile))
                    
                    batchArgs = orig_args.copy()
                    try:
                        del batchArgs['freq_input']
                    except KeyError:
                        pass
                    
                    hvDataOutList = []
                    for hvData in batchList:
                        hvDataOutList.append(calculate_depth(freq_input=hvData,
                                                             **batchArgs))
                    return sprit_hvsr.HVSRBatch(hvDataOutList)
                # First, check if it is a filepath
                freqDataPath = pathlib.Path(freq_input)
                if not freqDataPath.exists():
                    raise RuntimeError(f"Specified filepath for frequency data does not exist: freq_input={freq_input}")
                
                if 'hvsr' not in freqDataPath.suffix.lower():
                    if verbose:
                        print('Assuming file is a table readable by pandas.read_csv(), with column containing frequency data specified by freq_col={freq_col}')
                    tableReport = pd.read_csv(freqDataPath)
                                    
                    # Get parameters from table
                    param_dict_list = [{'input_data': freq_input,
                                        "Table_Report": tableReport}] * tableReport.shape[0]
                
                    # Get parameters directly from table
                    tableCols = tableReport.columns
                    for col in tableCols:
                        if col.lower() in ip_params or col.lower() in fd_params:
                            for i, (ind, row) in enumerate(tableReport.iterrows()):
                                param_dict_list[i][col.lower()] = row[col]
                    
                    # Get/overwrite table parameters with directly input parameters
                    hvdList = []
                    for parDict in param_dict_list:
                        for kw, val in kwargs.items():
                            if kw in ip_params or kw in fd_params:
                                parDict[kw] = val
                        hvdList.append(sprit_hvsr.HVSRData(parDict))

                    # Either make HVSRData or HVSRBatch object
                    if len(hvdList) > 1:
                        freq_input = sprit_hvsr.HVSRBatch(hvdList, df_as_read=pd.DataFrame(param_dict_list))
                    else:
                        freq_input = hvdList[0]

                else:
                    if verbose:
                        print('Assuming file with .*hvsr* suffix is an HVSR data file created by SpRIT.')
                    freq_input = sprit_hvsr.import_data(freqDataPath)
                    tableReport = freq_input.Table_Report
        elif isinstance(freq_input, sprit_hvsr.HVSRData):
            if not hasattr(freq_input, 'Table_Report'):
                if verbose:
                    warn("Passed HVSRData Object has no attribute Table_Report, attempting to generate one.")
                tableReport = sprit_hvsr.get_report(freq_input, report_format='csv')
            else:
                tableReport = freq_input.Table_Report

        # Break out for Batch data (in case it was generated during readin of file, for example)
        if isinstance(freq_input, sprit_hvsr.HVSRBatch):
            newBatchList = []
            # Iterate through each site/HVSRData object and run calculate_depth()
            for site in freq_input:
                if 'freq_input' in orig_args:
                    orig_args.pop('freq_input')
                calc_depth_kwargs = orig_args
                newBatchList.append(calculate_depth(freq_input=freq_input[site], **calc_depth_kwargs))
            return sprit_hvsr.HVSRBatch(newBatchList, df_as_read=freq_input.input_df)

        # Calibrate data
        pf_values = tableReport[freq_col].values

        calib_data = []
        depthModelList = []
        depthModelTypeList = []

        for site_peak_freq in pf_values:
            try:
                if depth_model in swave:
                    calib_data.append(swave_velocity/(4*site_peak_freq))
                    
                    if depth_model_in_latex:
                        dModelStr = f"$\\frac{{{swave_velocity}}}{{4\\times{site_peak_freq}}}$"
                    else:
                        dModelStr = f"{swave_velocity}/(4 * {site_peak_freq})"
                    depthModelList.append(dModelStr)
                    depthModelTypeList.append('Quarter Wavelength')
                else:
                    if depth_model == "all":
                        a_list = []
                        b_list = []
                        for name, model_params in model_parameters.items():
                            a_list.append(model_params[0])
                            b_list.append(model_params[1])
                        (a, b) = (np.nanmean(a_list), np.nanmean(b_list))

                    calib_data.append(a*(site_peak_freq**-b))
                    if hasattr(freq_input, 'x_freqs'):
                        freq_input['x_depth_m'] = {'Z': np.around([a*(f**-b) for f in freq_input["x_freqs"]['Z']], decimal_places),
                                                   'E': np.around([a*(f**-b) for f in freq_input["x_freqs"]['E']], decimal_places),
                                                   'N': np.around([a*(f**-b) for f in freq_input["x_freqs"]['N']], decimal_places)}

                        # Calculate depth in feet
                        freq_input['x_depth_ft'] = {'Z': np.around(freq_input['x_depth_m']['Z']*3.281, decimal_places),
                                                    'E': np.around(freq_input['x_depth_m']['E']*3.281, decimal_places),
                                                    'N': np.around(freq_input['x_depth_m']['N']*3.281, decimal_places)}
                             
                    if depth_model_in_latex:
                        dModelStr = f"{a} \\times {{{site_peak_freq}}}^{{-{b}}}"
                    else:
                        dModelStr = f"{a} * {site_peak_freq}^-{b}"
                    depthModelList.append(dModelStr)
                    depthModelTypeList.append('Power Law')

            except Exception as e:
                raise ValueError("Error in calculating depth, check HVSRData object for empty values or missing columns") from e

        # Record depth data in table
        tableReport[depth_column] = np.around(calib_data, decimal_places)
        
        # Calculate elevation data
        if calculate_elevation and surface_elevation_data in tableReport.columns:
            tableReport[bedrock_elevation_column] = np.around((float(tableReport.loc[0, surface_elevation_data]) - float(tableReport.loc[0, depth_column])), decimal_places)
            if hasattr(freq_input, 'x_depth_m'):
                freq_input['x_elev_m'] = {'Z': np.around([float(tableReport[surface_elevation_data].values[0]) - float(f) for f in freq_input["x_depth_m"]['Z']], decimal_places),
                                          'E': np.around([float(tableReport[surface_elevation_data].values[0]) - float(f) for f in freq_input["x_depth_m"]['E']], decimal_places),
                                          'N': np.around([float(tableReport[surface_elevation_data].values[0]) - float(f) for f in freq_input["x_depth_m"]['N']], decimal_places)}

        if calculate_depth_in_feet:
            tableReport[depth_column+'_ft'] = np.around(calib_data*3.281,
                                                     decimals=decimal_places)
            if calculate_elevation and surface_elevation_data in tableReport.columns:
                tableReport[bedrock_elevation_column+'_ft'] = np.around(tableReport[bedrock_elevation_column] * 3.281,
                                                                decimals=decimal_places)
                if hasattr(freq_input, 'x_elev_m') and not hasattr(freq_input['x_depth_ft']):
                    # Calculate depth in feet
                    freq_input['x_depth_ft'] = {'Z': np.around(freq_input['x_depth_m']['Z']*3.281, decimal_places),
                                                'E': np.around(freq_input['x_depth_m']['E']*3.281, decimal_places),
                                                'N': np.around(freq_input['x_depth_m']['N']*3.281, decimal_places)}

        tableReport["DepthModel"] = depthModelList
        tableReport["DepthModelType"] = depthModelTypeList

        # Do plotting work
        if fig is None and ax is None:
            fig, ax = plt.subplots()
        elif fig is not None:
            ax = fig.get_axes()
            if len(ax) == 1:
                ax = ax[0]

        if hasattr(freq_input, 'hvsr_curve'):
            pdc_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(sprit_plot.plot_depth_curve).parameters.keys())}
            freq_input = sprit_plot.plot_depth_curve(hvsr_results=freq_input,
                                                     show_depth_curve=show_depth_curve,
                                                     fig=fig, ax=ax,
                                                     **pdc_kwargs)
        else:
            surfElevVal = tableReport.loc[0, surface_elevation_col]
            brElevVal = tableReport.loc[0, bedrock_elevation_column]
            if np.isnan(surfElevVal):
                surfElevVal = 0
                
            if np.isnan(brElevVal):
                brElevVal = tableReport.loc[0, depth_column]
                yLIMITS = [brElevVal*1.1, brElevVal*-0.1]
            else:
                yLIMITS = [0, brElevVal - ((surfElevVal-brElevVal) * 0.1)]

            ax.axhline(0, xmin=-0.1, xmax=1, c='k')
            ax.plot([0, 0], [0, brElevVal], linestyle='dotted', c='k')
            
            ax.scatter(x=0, y=surfElevVal, c='k', marker='v')
            ax.scatter(x=0, y=brElevVal, c='k', marker='^')
            
            spc = " "
            ax.text(x=0, y=brElevVal, 
                    s=f"  Depth: {brElevVal}m {spc}({tableReport.loc[0, freq_col]} Hz)",
                    va='top')
            
            ax.set_xlim([-0.1, 1])
            ax.set_ylim(yLIMITS)
            
            ax.set_ylabel('Depth [m]')
            ax.set_xticks([])
            titleText = f'Calibrated Depth from Input Frequency'
            fig.suptitle(titleText)
            if isinstance(depth_model, (tuple, list)):
                aText = depth_model[0]
                bText = np.sqrt(depth_model[1]**2)*-1
                ax.text(x=0,
                        y=surfElevVal, va='bottom',
                        s=f"  Depth Model: ${aText:.2f} * f_0 ^{{{bText:0.3f}}}$")
            
        plt.sca(ax)
        if show_depth_curve:
            plt.show()
        else:
            plt.close()
        
        # Export as specified
        if export_path is not None and os.path.exists(export_path):
            if export_path == freq_input:
                tableReport.to_csv(freq_input)
                if verbose:
                    print("Saving data in the original file")

            else:
                if "/" in export_path:
                    temp = os.path.join(export_path+ "/"+ site + ".csv")
                    tableReport.to_csv(temp)
                
                else:
                    temp = os.path.join(export_path+"\\"+ site + ".csv")
                    tableReport.to_csv(temp)

                if verbose:
                    print("Saving data to the path specified")
        
        
        freq_input.Table_Report = tableReport
        return freq_input
            
    else:
        raise RuntimeError(f"The freq_input parameter is not the correct type:\n\ttype(freq_input)={type(freq_input)}")


def calibrate(calib_filepath, calib_type="power", peak_freq_col="PeakFrequency", calib_depth_col="Bedrock_Depth", 
            outlier_radius=None, xcoord_col='xcoord', ycoord_col='ycoord', bedrock_type=None,
            show_calibration_plot=True):
    
    """The calibrate function allows input of table with f0 and known depths to generate a power-law regression relationship.

    Parameters
    ----------
    calib_filepath : pathlike object
        Path to file readable by pandas.read_csv() with a column for frequencies
        and a column for depths.
    calib_type : str, optional
        Which calibration to use. Currently only power-law is supported, by default "power"
    outlier_radius : None or float, optional
        Radius (in CRS of coordinates) within which to use the points for calibration, by default None.
        Not currently supported.
    bedrock_type : str or None, optional
        Bedrock type by which to select which points to use for calibration, by default None.
        Not currently supported.
    peak_freq_col : str, optional
        Which column in calib_filepath to use for fundamental frequency values, by default "PeakFrequency"
    calib_depth_col : str, optional
        Which column in calib_filepath to use for depth values, by default "Bedrock_Depth"
    show_calibration_plot : bool, optional
        Whether to show the calibration plot, by default True

    Returns
    -------
    tuple
        Tuple (a, b) containing the parameters used for calibration regression.
    """

    calib_data = None
    calib_types = ["Power", "swave_velocity", "Matrix"]
    calib_type_list = list(map(lambda x : x.casefold(), calib_types))
    power_list = ["power", 'power law', 'powerlaw', 'power-law', "pow", 'p']
    bedrock_types = ["shale", "limestone", "dolomite",
                     "sedimentary", "igneous", "metamorphic"]
   
    freq_columns_names = ["PeakFrequency", "ResonanceFrequency", "peak_freq",
                "res_freq", "Peakfrequency", "Resonancefrequency", "PF", "RF", "pf", "rf"]
    bedrock_depth_names = ["BedrockDepth", "DepthToBedrock", "bedrock_depth",
                            "depth_bedrock", "depthtobedrock", "bedrockdepth"]

    #if calib_type.lower() in power_list:

    depthDataDF = pd.read_csv(calib_filepath)

    depths = depthDataDF[calib_depth_col]
    freqs = depthDataDF[peak_freq_col]

    def hvsrPowerLaw(f0, a, b):
        return a*f0**b

    popt, pcov = curve_fit(hvsrPowerLaw, freqs, depths)

    if show_calibration_plot:
        plt.loglog(sorted(freqs), sorted(hvsrPowerLaw(freqs, popt[0], popt[1]), reverse=True), 
                    linestyle='dotted', linewidth=0.5,
                    label=f"${popt[0]:.2f} * f_0 ^{{{popt[1]:0.3f}}}$")
        plt.scatter(freqs, depths, label=f"a = {popt[0]:0.2f}\nb = {popt[1]:0.3f}", zorder=100)
        ax = plt.gca()

        plt.legend()
        plt.title(f'Frequency-Depth Calibration')
        plt.xlabel('Frequency\n[Hz]')
        plt.ylabel('Depth [m]')
        tickList = [0.01, 0.1, 1, 10, 100, 1000]

        for i, t in enumerate(tickList):
            if min(freqs) > t and min(freqs) <= tickList[i+1]:
                minX = t
            if i!=0 and max(freqs) > tickList[i-1] and max(freqs) <= t:
                maxX = t                
        
        for i, t in enumerate(tickList):
            if min(depths) > t and min(depths) <= tickList[i+1]:
                minY = t
            if i !=0 and max(depths) > tickList[i-1] and max(depths) <= t:
                maxY = t

        plt.grid(True, which='both', axis='both', linewidth=0.5, zorder=-1)

        if maxX > 100:
            xArr = [0.1, 1, 10, 100, 1000]
            xTick = ['$10^-1$', '$10^0$', '$10^1$', '$10^2$', '$10^3$']
        elif maxX > 10:
            xArr = [0.1, 1, 10, 100]
            xTick = ['$10^-1$', '$10^0$', '$10^1$', '$10^2$']
        elif maxX > 1:
            xArr = [0.1, 1, 10]
            xTick = ['$10^-1$', '$10^0$', '$10^1$']
        else:
            xArr = [0.1, 1, 10, 100]
            xTick = ['$10^-1$', '$10^0$', '$10^1$', '$10^2$']

        if minX > 0.1:
            xTick = xTick[1:]
            xArr = xArr[1:]
        if minX > 1:
            xTick = xTick[1:]
            xArr = xArr[1:]
        if minX > 10:
            xTick = xTick[1:]
            xArr = xArr[1:]

        if maxY > 100:
            yArr = [1, 10, 100, 1000]
            yTick = ['$10^0$', '$10^1$', '$10^2$', '$10^3$']
        elif maxY > 10:
            yArr = [1, 10, 100]
            yTick = ['$10^0$', '$10^1$', '$10^2$']
        elif maxY > 11:
            yArr = [1, 10, 100]
            yTick = ['$10^0$', '$10^1$']
        else:
            yArr = [1, 10, 100]
            yTick = ['$10^0$', '$10^1$', '$10^2$']

        if minY > 1:
            yTick = yTick[1:]
            yArr = yArr[1:]
        if minY > 10:
            yTick = yTick[1:]
            yArr = yArr[1:]
        if minY > 100:
            yTick = yTick[1:]
            yArr = yArr[1:]

        # Set major ticks
        plt.xticks(xArr, xTick)
        plt.yticks(yArr, yTick)

        # Add minor ticks
        ax = plt.gca()
        ax.xaxis.set_minor_locator(LogLocator(subs=(2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)))
        ax.yaxis.set_minor_locator(LogLocator(subs=(2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)))

        plt.xlim([xArr[0]-0.001*xArr[0], xArr[-1]+0.005*xArr[-1]])
        plt.ylim([yArr[0]-0.005*yArr[0], yArr[-1]+0.005*yArr[-1]])
        plt.show()
    
    calibration_vals = tuple(popt)

    return calibration_vals

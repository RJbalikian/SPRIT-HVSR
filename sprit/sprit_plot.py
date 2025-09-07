import datetime
import inspect
import math
import numbers
import os
import pathlib
import webbrowser

from zoneinfo import available_timezones

import ipywidgets as widgets
from IPython.display import display, clear_output
import kaleido
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from obspy import UTCDateTime
import obspy
import pandas as pd
import plotly.express as px
from plotly.graph_objs import Heatmap as goHeatmap
from plotly.express import timeline as pxTimeline
from plotly.express import scatter as pxScatter
import plotly.graph_objs as go
import plotly.subplots as subplots
from plotly.subplots import make_subplots
from scipy import signal, interpolate
import shapely
import warnings

try:
    import sprit_hvsr
    import sprit_calibration
except:
    import sprit.sprit_hvsr as sprit_hvsr
    import sprit.sprit_calibration as sprit_calibration


HVSR_BAND = [0.1, 50 ]# sprit_hvsr.DEFAULT_BAND


# Plot cross section
def plot_cross_section(hvsr_data,  title=None, fig=None, ax=None, use_elevation=True, show_feet=False, primary_unit='m', 
                       show_curves=True, annotate_curves=False, curve_alignment='peak',
                       grid_size='auto', orientation='WE', 
                       interpolation_type='cloughtocher', interpolate_log_values=True,
                       surface_elevations=None, show_peak_points=True, smooth_bedrock_surface=False,
                       depth_limit=150, minimum_elevation=None, show_bedrock_surface=True,
                       return_data_batch=True, show_cross_section=True, verbose=False,
                       **kwargs):
    """Function to plot a cross section given an HVSRBatch or similar object

    Parameters
    ----------
    hvsr_data : HVSRBatch, list, or similar
        HVSRBatch (intended usage) object with HVSRData objects to show in profile/cross section view
    title : str, optional
        Title to use for plot, by default None
    fig : matplotlib.Figure, optional
        Figure to use for plot, by default None
    ax : matplotlib.Axis, optional
        Axis to use for plot, by default None
    use_elevation : bool, optional
        Whether to use elevation (if True) or depth (if False), by default True
    show_feet : bool, optional
        Whether to show feet (if True) or meters (if False), by default False
    primary_unit : str, optional
        Primary unit to use ('m' or 'ft'), by default 'm'
    show_curves : bool, optional
        Whether to also show curves on plot, by default True
    annotate_curves : bool, optional
        Whether to annotate curves by plotting site names next to them, by default False
    curve_alignment : str, optional
        How to horizontally align the curve. 
        If "peak" the curve will be aligned so that the peak is at the correct latitude or longitude.
        If "max" will align the maximum point of the curve to the correct location.
        If any other value, will align at the surface (i.e., highest frequency). By default 'peak'.
    grid_size : list, optional
        Two item list with height and width of grid for interpolation.
        If "auto" this will be calculated based on the data, by default 'auto'.
    orientation : str, optional
        The orientation of the cross section. 
        Should be either "WE", "EW", "NS", or "SN", by default 'WE'.
    interpolation_type : str, optional
        Interpolation type to use. Uses scipy.interpolation.
        Options include: 'cloughtocher', 'nearest neighbor', 'linear', 
        or 'radial basis function', by default 'cloughtocher'.
    interpolate_log_values : bool, optional
        Whether to use log values of the H/V curve for interpolation (can be useful for better normalizing data)
    surface_elevations : shapely.LineString, optional
        A shapely.LineString object containing surface elevation coordinates along cross section path.
        If None, uses elevation data in HVSRBatch specified by hvsr_data, by default None.
    show_peak_points : bool, optional
        Whether to plot small triangles where peaks were picked, by default True
    smooth_bedrock_surface : bool, optional
        Whether to smooth the bedrock surface when plotting, by default False
    depth_limit : int, optional
        Depth limit for the plot, by default 150
    minimum_elevation : _type_, optional
        Minimum elevation of the plot, by default None
    show_bedrock_surface : bool, optional
        Whether to show the bedrock surface, by default True
    return_data_batch : bool, optional
        Whether to return the HVSRBatch object, by default True
    show_cross_section : bool, optional
        Whether to show the cross section plot, by default True
    verbose : bool, optional
        Whether to print information about the process to terminal, by default False

    Returns
    -------
    figure
        Currently only matplotlib figure supported
    """
    if verbose:
        print("Getting cross section plot configuration")
        
    if fig is None and ax is None:
        fig, ax = plt.subplots()
    elif ax is None and fig is not None:
        fig = fig
        ax = fig.get_axes()[0]
    elif fig is None and ax is not None:
        ax = ax
        fig = plt.figure()
        fig.axes.append(ax)
    else:
        fig = fig
        ax = ax
    plt.sca(ax)
    
    if verbose:
        print("Getting data batch for cross section plot")
    batchExt = None
    if isinstance(hvsr_data, (str, os.PathLike, pathlib.Path)):
        if pathlib.Path(hvsr_data).exists() and pathlib.Path(hvsr_data).is_dir():
            batchExt = 'hvsr'
    hvDataBatch = sprit_hvsr.HVSRBatch(hvsr_data, batch_ext=batchExt)
    
    if verbose:
        print("Sorting and Orienting data")
    # Get orientation/order of data
    nsList = ['ns', "north-south", 'northsouth', 'south', 's']
    snList = ['sn', "south-north", 'southnorth', 'north', 'n']
    weList = ['we', "west-east", 'westeast', 'east', 'e']
    ewList = ['ew', "east-west", 'eastwest', 'west', 'w']

    if str(orientation).lower() in nsList:
        ordercoord = 'latitude'
        order = 'descending'
        profile_direction = 'north-south'
    elif str(orientation).lower() in snList:
        ordercoord = 'latitude'
        order = 'ascending'
        profile_direction  = 'south-north'
    elif str(orientation).lower() in weList:
        ordercoord = 'longitude'
        order = 'ascending'
        profile_direction = 'west-east'
    elif str(orientation).lower() in ewList:
        ordercoord = 'longitude'
        order = 'descending'
        profile_direction = 'east-west'
    else:
        if verbose:
            print(f"Value for orientation={orientation} is not recognized. Using West-East orientation.")
        order = 'ascending'
        ordercoord='longitude'
        profile_direction = 'west-east (default)'

    # Get data in correct order, as specified by orientation parameter
    reverseit = (order == 'descending')
    sorted_sites = sorted(hvDataBatch, key=lambda site: hvDataBatch[site][ordercoord], reverse=reverseit)
    hvDataSorted = [hvDataBatch[h] for h in sorted_sites]

    if verbose:
        print(f'Plotting {len(hvDataBatch.sites)} sites, {profile_direction}.')
        [print(f"\t{hvdata.site[:12]:<12}: {hvdata.longitude:>8.4f}, {hvdata.latitude:>8.4f}, {hvdata.elevation:<6.1f}") for hvdata in hvDataSorted]

    # Get cross section profile
    shapelyPoints = []
    interpData = []
    interpCoords = {'longitude':[], 'latitude':[], 'elevation':[]}
    for i, hvData in enumerate(hvDataSorted):
        if not hasattr(hvData, 'x_elev_m'):
            calc_depth_kwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(sprit_calibration.calculate_depth).parameters.keys())}
            hvData = sprit_calibration.calculate_depth(hvData, **calc_depth_kwargs, verbose=verbose)
        
        # Create shapely Point objects at each profile location
        x = hvData['longitude']
        y = hvData['latitude']
        z = hvData['elevation']

        shapelyPoints.append(shapely.Point(x, y, z))

        # Points arranged for interpolation
        if interpolate_log_values:
            interpData.extend(list(np.log10(hvData.hvsr_curve)))
        else:
            interpData.extend(list(hvData.hvsr_curve))
        for i, pt in enumerate(hvData.hvsr_curve):
            interpCoords['longitude'].append(x)
            interpCoords['latitude'].append(y)
            interpCoords['elevation'].append(hvData['x_elev_m']['Z'][i])

        # Since already doing loop, ensure hvData has all depth/elev info it needs
        if not hasattr(hvData, 'x_elev_m'):
            calc_depth_kwargs = {k: v for k, v in kwargs.items()
                                      if k in tuple(inspect.signature(sprit_calibration.calculate_depth).parameters.keys())}
            if 'calculate_depth_in_feet' not in calc_depth_kwargs:
                calc_depth_kwargs['calculate_depth_in_feet'] = True
            hvDataSorted[i] = sprit_calibration.calculate_depth(hvData, **calc_depth_kwargs, verbose=verbose)

    xSectionProfile = shapely.LineString(shapelyPoints)
    profileXs, profileYs = xSectionProfile.xy
    
    orderCoordValues = profileXs
    if ordercoord == 'latitude':
        orderCoordValues = profileYs

    minX = min(profileXs)
    minY = min(profileYs)
    maxX = max(profileXs)
    maxY = max(profileYs)

    # Generate grid
    if verbose:
        print("Generating Grid: ", end='')
    xSectionLength = xSectionProfile.length
    if grid_size == 'auto':
        grid_size=(50, 100)

        cellHNumber = grid_size[0]
        cellWNumber = grid_size[1]
    elif isinstance(grid_size, (list, tuple)):
        cellHNumber = grid_size[0]
        cellWNumber = grid_size[1]
    else:
        grid_size=(50, 100)

        cellHNumber = grid_size[0]
        cellWNumber = xSectionLength/grid_size[1]

        if verbose:
            print(f'grid_size value ({grid_size} not recognized, using grid 100 cells wide and 50 cells high: grid_size=(50, 100))')

    cellWSize = xSectionLength/cellWNumber
    
    max_surf_elev = max([hvd.elevation for hvd in hvDataSorted])
    min_br_elev = min([hvd.Table_Report['Peak'][0] for hvd in hvDataSorted])
    elev_range = max_surf_elev - min_br_elev

    max_grid_elev = math.ceil(max_surf_elev)

    # Minimum grid elevation is determined by depth_limit and minimum_elevation
    if str(minimum_elevation).lower() == 'auto':
        min_grid_elev = min_br_elev - (elev_range) * 0.1
    elif isinstance(minimum_elevation, numbers.Number):
        min_grid_elev = minimum_elevation
    elif minimum_elevation is None:
        min_grid_elev = max_grid_elev - depth_limit
    
    xSectionDepth = max_grid_elev - min_grid_elev
    cellHSize = xSectionDepth/cellHNumber

    # Get grid coordinates (all coords in z direction (depth/elev))
    gridZcoords = np.linspace(min_grid_elev, max_grid_elev, cellHNumber)

    gridXDists = np.linspace(0, xSectionProfile.length, cellWNumber)
    gridXcoords = [] # All coords in the "x" direction (along profile)
    for xdist in gridXDists:
        x, y = xSectionProfile.interpolate(xdist).xy
        if 'east' in profile_direction:
            gridXcoords.append(x[0])
        else:
            gridXcoords.append(y[0])
    gridXcoords = np.array(gridXcoords)
    if verbose:
        print(f'Grid generated ({cellWNumber*cellHNumber} cells)\n\tx-range: {xSectionLength:.5f} ({cellWNumber:d} cells, each {cellWSize:.5f} units in size)\n\tz-range: {xSectionDepth:.2f} ({cellHNumber:d} cells, each {cellHSize:.5f} units in size)')

    #print('x', len(interpCoords['longitude']))
    #print('y', len(interpCoords['latitude']))
    #print('z', len(interpCoords['elevation']))
    #print('interp', np.array(interpData).shape)
    if verbose:
        print(f'Beginning interpolation ({interpolation_type})... ', end='')
    
    ctList = ['cloughtocher2dinterpolator', 'cloughtocher', 'ct', 'clough-tocher', 'clough tocher', 'cubic', 'c']
    nearList = ['nearestnd', 'nearest', 'near', 'n']
    linList = ['linearnd', 'linear', 'lin', 'l']
    rbfList = ['radial basis function', 'rbf', 'rbfinterpolator']
    
    if str(interpolation_type).lower() in ctList:
        interp = interpolate.CloughTocher2DInterpolator(list(zip(interpCoords[ordercoord], interpCoords['elevation'])), interpData)
    elif str(interpolation_type).lower() in rbfList:
        interp = interpolate.RBFInterpolator(list(zip(interpCoords[ordercoord], interpCoords['elevation'])), interpData)        
    elif str(interpolation_type).lower() in linList:
        interp = interpolate.LinearNDInterpolator(list(zip(interpCoords[ordercoord], interpCoords['elevation'])), interpData)
    else: # elif str(interpolation_type).lower() in nearList:
        interp = interpolate.NearestNDInterpolator(list(zip(interpCoords[ordercoord], interpCoords['elevation'])), interpData)
        
    xx, zz = np.meshgrid(gridXcoords, gridZcoords)
    interpData = interp(xx, zz)
    interpDataflat = interpData[:-1, :-1]
    if verbose:
        print('Data interpolated')
        print('Plotting colormesh')
    
    # kwargs-defined pcolormesh kwargs
    pcolormeshKwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(plt.pcolormesh).parameters.keys())}
    
    # Set defaults for cmap and shading (if not overriden in kwargs)
    if 'cmap' not in pcolormeshKwargs:
        pcolormeshKwargs['cmap'] = 'nipy_spectral'
    if 'shading' not in pcolormeshKwargs:
        pcolormeshKwargs['shading'] = 'flat'
                
    ax.pcolormesh(xx, zz, interpDataflat, zorder=0, **pcolormeshKwargs)
    
    if show_curves:
        if verbose:
            print('Plotting curves')
        norm_div = 1
        normal_factor = np.diff(orderCoordValues)
        normal_factor = np.nanmedian(normal_factor[normal_factor != 0]) / norm_div
        
        zAttr = 'x_depth_m'
        if use_elevation:
            zAttr = 'x_elev_m'

        for hvData in hvDataSorted:
            hvData['Normalized_HVCurve'] = (hvData['hvsr_curve'] / np.nanmax(hvData['hvsr_curve'])) * normal_factor
            locatedCurve = hvData['Normalized_HVCurve'] + hvData[ordercoord]
            if curve_alignment.lower() == 'peak':
                normal_peak_factor = (hvData["BestPeak"]['HV']['A0'] / np.nanmax(hvData['hvsr_curve'])) * normal_factor
                locatedCurve = locatedCurve  - normal_peak_factor
            elif curve_alignment.lower() == 'max':
                locatedCurve = locatedCurve  - normal_factor
            else:
                pass
            
            if max(locatedCurve) > max(gridXcoords):
                locatedCurve = locatedCurve - (max(locatedCurve) - max(gridXcoords))
            if min(locatedCurve) < min(gridXcoords):
                locatedCurve = locatedCurve + (min(gridXcoords) - min(locatedCurve))
                
            ax.plot(locatedCurve, hvData[zAttr]['Z'][:-1], c='k', linewidth=0.5, zorder=3)

    if annotate_curves:
        for hvData in hvDataSorted:
            if len(hvData.site) > 10:
                sitename = hvData.site[:8]+ '...'
            else:
                sitename = hvData.site
            ax.text(hvData[ordercoord], y=min_grid_elev, s=sitename, ha='right', va='bottom', rotation='vertical')
    
    if smooth_bedrock_surface:
        show_bedrock_surface = True

    if show_peak_points or show_bedrock_surface:
        brX = []
        brZ = []
        for hvData in hvDataSorted:
            if 'BedrockElevation' in hvData['Table_Report'].columns:
                brX.append(hvData[ordercoord])
                brZ.append(hvData['Table_Report'].loc[0,'BedrockElevation'][()])
        if show_peak_points:
            ax.scatter(brX, brZ, zorder=5, c='k', marker='v')

        
        if smooth_bedrock_surface:
            #brSurfZ = scipy.signal.savgol(brZ, window_length=len(brZ))
            if brX[0] > brX[-1]:
                brX = np.flip(brX)
                brZ = np.flip(brZ)
                doFlip=True
            else:
                doFlip=False
                
            newX = np.sort(gridXcoords)
            brSurfZ = np.interp(newX, brX, brZ)
            brSurfX = newX
        else:
            brSurfX = brX
            brSurfZ = brZ
        
        zMinPts = list(np.array(brSurfZ) * 0 + min(gridZcoords))
        
        if show_bedrock_surface:
            ax.fill_between(brSurfX, brSurfZ, zMinPts,facecolor='w', alpha=0.5, zorder=1)
            ax.plot(brSurfX, brSurfZ, c='k', zorder=2)

    # Plot surfaces
    if verbose:
        print('Plotting surfaces')
    
    if surface_elevations is None:
        surfPts_shapely = []
        surfPtsX = []
        surfPtsZ = []
        
        surface_elevations = shapely.LineString([shapely.Point(hvData['longitude'], 
                                                               hvData["latitude"], 
                                                               hvData["elevation"]) 
                                                 for hvData in hvDataSorted])
    
    xPts = []
    zPts = []
    for surf_pt in surface_elevations.coords:
        surfPtDict = {'longitude':surf_pt[0], 
                      'latitude': surf_pt[1],
                      'elevation': surf_pt[2]}
        xPts.append(surfPtDict[ordercoord])
        zPts.append(surfPtDict['elevation'])
    
    zMaxPts = list(np.array(zPts) * 0 + max_grid_elev)

    # Fill in above surface so interpolation is cleaner and surface topo shape is clear
    ax.fill_between(xPts, zPts, zMaxPts, facecolor='w', zorder=1000)

    # Plot surface topography
    ax.plot(xPts, zPts, c='g', linewidth=1.5, zorder=1001)

    # Plot configuration
    if verbose:
        print('Configuring plot')
    ax.set_xlim([min(gridXcoords), max(gridXcoords)])
    ax.set_ylim([min_grid_elev, max_grid_elev])
    
    ax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False)
    ax.set_xlabel(str(ordercoord).title())
    ax.xaxis.set_label_position('top')
    ax.set_ylabel('Elevation [Meters]')
    if title is None:
        title = 'HVSR Cross Section Profile'
    ax.set_title(title)
    
    # Display orientation of cross section profile
    # Calculate angle
    profile_angle = math.degrees(math.atan2(shapelyPoints[-1].y - shapelyPoints[0].y, shapelyPoints[-1].x - shapelyPoints[0].x))
    
    # Convert angle to geographic coordinates
    profile_angle = (profile_angle * -1) + 90
    if profile_angle < 0:
        profile_angle += 360

    if verbose:
        print(f"Calculated profile angle to be {profile_angle:.3f} degrees.")
    # Calculate angle name of cross section profile
    if profile_angle < -11.25 + 22.5 * 1:
        profileStart = 'S'
        profileEnd = 'N'
    elif profile_angle < -11.25 + 22.5 * 2:
        profileEnd = 'NNE'
        profileStart = 'SSW'        
    elif profile_angle < -11.25 + 22.5 * 3:
        profileEnd = 'NE'
        profileStart = 'SW'
    elif profile_angle < -11.25 + 22.5 * 4:
        profileEnd = 'ENE'
        profileStart = 'WSW'        
    elif profile_angle < -11.25 + 22.5 * 5:
        profileEnd = 'E'
        profileStart = 'W'        
    elif profile_angle < -11.25 + 22.5 * 6:
        profileEnd = 'ESE'
        profileStart = 'WNW'
    elif profile_angle < -11.25 + 22.5 * 7:
        profileEnd = 'SE'
        profileStart = 'NW'
    elif profile_angle < -11.25 + 22.5 * 8:
        profileEnd = 'SSE'
        profileStart = 'NNW'
    elif profile_angle < -11.25 + 22.5 * 9:
        profileEnd = 'S'
        profileStart = 'N'
    elif profile_angle < -11.25 + 22.5 * 10:
        profileEnd = 'SSW'
        profileStart = 'NNE'        
    elif profile_angle < -11.25 + 22.5 * 11:
        profileEnd = 'SW'
        profileStart = 'NE'
    elif profile_angle < -11.25 + 22.5 * 12:
        profileEnd = 'WSW'
        profileStart = 'ENE'
    elif profile_angle < -11.25 + 22.5 * 13:
        profileEnd = 'W'
        profileStart = 'E'
    elif profile_angle < -11.25 + 22.5 * 14:
        profileEnd = 'WNW'
        profileStart = 'ESE'
    elif profile_angle < -11.25 + 22.5 * 15:
        profileEnd = 'NW'
        profileStart = 'SE'
    elif profile_angle < -11.25 + 22.5 * 16:
        profileEnd = 'NNW'
        profileStart = 'SSE'
    elif profile_angle <= 360:
        profileEnd = 'N'
        profileStart = 'S'

    # Always orient north and east to the right
    if 'north' in profile_direction[:5] or 'east' in profile_direction[:5]:
        ax.invert_xaxis()

    plt.sca(ax)
    plt.figtext(0.1,0.95, s=profileStart)
    plt.figtext(0.9,0.95, s=profileEnd)

    if show_cross_section:
        if verbose:
            print('Displaying plot')
        plt.sca(ax)
        plt.show()
        
    if return_data_batch:
        hvBatch = sprit_hvsr.HVSRBatch(hvDataSorted)
        hvBatch['Cross_Section_Plot'] = fig
        return hvBatch
            
    return fig


# Plot depth curve
def plot_depth_curve(hvsr_results, use_elevation=True, show_feet=False, normalize_curve=True, 
                     depth_limit=250, depth_model=None,
                     annotate=True, depth_plot_export_path=None, 
                     fig=None, ax=None, show_depth_curve=True):
    """Function to plot depth curves, given hvsr_results with depth_model specified.

    Parameters
    ----------
    hvsr_results : sprit.HVSRData or sprit.HVSRBatch
        HVSRData object with depth information (or `depth_model` specified).
    use_elevation : bool, optional
        Whether to use elevation (True) or just depth (False), by default True
    show_feet : bool, optional
        Whether to show elevation/depth in feet on Y axis, by default False
    normalize_curve : bool, optional
        Whether to normalize amplitude of H/V curve (x-axis) using maximum/minimum amplitudes, by default True
    depth_limit : int, optional
        Depth limit at which to cut off plot, by default 250 (meters)
    depth_model : None or tuple, optional
        If depth_model not already specified, this can be used to run sprit.calculate_depth() before generating plot.
    annotate : bool, optional
        Whether to annotate plot, by default True
    depth_plot_export_path : filepath-like object, optional
        If specified, will export depth plot to location specifed, by default None
    fig : matplotlib.figure.Figure, optional
        Maplotlib Figure to use for plotting, by default None (new one will be created)
    ax : matplotlib.axis.Axis, optional
        Maplotlib Axis to use for plotting, by default None (new one will be created)
    show_depth_curve : bool, optional
        Whether to diplay the depth curve chart after generating it, by default True

    Returns
    -------
    HVSRData
        HVSRData object with additional property for Depth_Plot
    """


    if fig is None and ax is None:
        fig, ax = plt.subplots(layout='constrained')#, figsize=(5, 15))
        fig.suptitle(hvsr_results['site'])
        ax.set_title('Calibrated Depth to Interface', size='small')
    ax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False)
    
    if depth_model is not None:
        hvsr_results = sprit_calibration.calculate_depth(hvsr_results, depth_model=depth_model, show_depth_curve=False)

    surfElev = hvsr_results.Table_Report['Elevation'][0]
    bedrockElev = hvsr_results.Table_Report['BedrockElevation'][0]
    bedrockDepth = hvsr_results.Table_Report['BedrockDepth'][0]
    curveRange = max(hvsr_results.hvsr_curve) - min(hvsr_results.hvsr_curve)

    if normalize_curve:
        curvePlot = (hvsr_results.hvsr_curve - min(hvsr_results.hvsr_curve)) / curveRange
        xBase = 0
        xCap = 1
        xLims = [-0.25, 1.25]
        ax.set_xticks([0, 1])
    else:
        curvePlot = hvsr_results.hvsr_curve
        xBase = min(hvsr_results.hvsr_curve)
        xCap = hvsr_results.BestPeak['HV']['A0']#max(hvsr_results.hvsr_curve)
        xLims = [xBase-(0.15*curveRange), xCap+(0.15*curveRange)]
 
    if use_elevation:
        yLims = [hvsr_results.x_elev_m['Z'][0] - depth_limit,
              hvsr_results.x_elev_m['Z'][0]]
        yVals = hvsr_results.x_elev_m['Z'][:-1]
        ax.set_ylabel('Elevation [m]')
        bedrockVal = bedrockElev
        if annotate:
            #Annotate surface elevation
            ax.text(x=xLims[0],
                    y=surfElev,
                    s=str(round(float(surfElev), 2))+'m',
                    ha='right',
                    va='bottom',
                    size='x-small')

            # Annotate bedrock elevation
            ax.text(x=xBase,
                    y=bedrockElev,
                    s=' ' + str(round(float(bedrockElev), 2))+'m\n elevation',
                    ha='left',
                    va='center',
                    size='x-small')
            
            # Annotate bedrock depth
            ax.text(x=xBase,
                    y=max(yLims),
                    s=str(round(float(bedrockDepth), 2))+'m deep ',
                    ha='right',
                    va='top',
                    size='x-small',
                    rotation='vertical')
    else:
        yLims = [depth_limit, hvsr_results.x_depth_m['Z'][0]]
        yVals = hvsr_results.x_depth_m['Z'][:-1]
        ax.set_ylabel('Depth [m]')
        bedrockVal = bedrockDepth
        if annotate:
            # Annotate surface elevation
            ax.text(x=xLims[0],
                    y=0,
                    s=str(round(float(surfElev), 2))+'m',
                    ha='right',
                    va='bottom',
                    size='x-small')
            
            # Annotate Bedrock elevation
            ax.text(x=xBase,
                    y=bedrockVal,
                    s=str(round(float(bedrockElev), 2))+'m\nelevation',
                    ha='center',
                    va='center',
                    size='x-small')

            # Annotate Bedrock depth
            ax.text(x=xBase,
                    y=(min(yLims)+float(bedrockDepth))/2,
                    s=str(round(float(bedrockDepth), 2))+'m deep',
                    ha='right',
                    va='top',
                    size='x-small',
                    rotation='vertical')

    # Plot curve
    ax.fill_betweenx(y=yVals, x1=xBase, x2=curvePlot, alpha=0.2, facecolor='k')
    ax.plot(curvePlot, yVals, c='k', linewidth=0.5)
    if show_feet:
        ax_ft = ax.twinx()
        ax_ft.plot(curvePlot, yVals*3.281, alpha=0)
        ax_ft.set_ylim(yLims[0]*3.281, yLims[1]*3.281)
        ax_ft.set_ylabel('Elevation [ft]')
        if not use_elevation:
            ax_ft.set_ylabel('Depth [ft]')
        
    # Plot peak location
    ax.axhline(y=bedrockVal,
               linestyle='dotted', c='k', linewidth=0.5)
    ax.scatter(xBase, y=bedrockVal, c='k', s=0.5)
    ax.scatter(xCap, y=bedrockVal, c='k', s=0.5)
    
    # Plot "base" line
    ax.axvline(x=xBase, linestyle='dotted', c='k', linewidth=0.5)

    ax.set_ylim(yLims)
    ax.set_xlim(xLims)
    
    xlabel = "H/V Ratio"
    if normalize_curve:
        xlabel += '\n(Normalized)'
        ax.set_xticks([])

    ax.set_xlabel('H/V Ratio')
    ax.xaxis.set_label_position('top')

    ax.set_title(hvsr_results['site'])

    plt.sca(ax)
    fig.set_size_inches(4, 8)
    if show_depth_curve:
        plt.show()
    else:
        plt.close()
        
    if depth_plot_export_path is not None:
        if isinstance(depth_plot_export_path, os.PathLike):
            fig.savefig(depth_plot_export_path)
        else:
            print(f'Please specify a valid path for depth_plot_export_path, not {depth_plot_export_path}')
    
    hvsr_results['Depth_Plot'] = fig
    return hvsr_results


# Plot input stream
def plot_input_stream(hv_data, stream=None, input_fig=None, plot_engine='plotly',
                        spectrogram_component='Z', decimate=True,
                        show_plot=True, return_fig=False, **kwargs):

    """Function to plot input stream using plotly.
    
    Parameters
    ----------
    hv_data : HVSRData
    stream : obspy.stream.Stream
        Can explictly specify stream instead of using hv_data object.
    input_fig : plotly.Figure
        Plotly figure to plot input stream on. If None, creates new one. Default is None.
    spectrogram_component : str, default='Z'
        Which component to use for the spectrogram
    show_plot : bool, default=True
        Whether to show plot or just generate it.
    return_fig : bool, default=False
        Whether to return figure

    Returns
    -------
    plotly figure
        Only returned if return_fig is True
    """

    plotlyList = ['plotly', 'pltly', 'plty', 'p']
    mplList = ['matplotlib', 'pyplot', 'plt', 'mpl', 'm']

    if str(plot_engine).lower() in plotlyList:
        return _plot_input_stream_plotly(hv_data=hv_data, stream=stream, input_fig=input_fig,
                                         spectrogram_component=spectrogram_component,
                                         show_plot=show_plot, return_fig=return_fig)
    elif str(plot_engine).lower() in mplList:
        return _plot_input_stream_mpl(hv_data, stream, input_fig, decimate=True, spectrogram_component='Z', show_plot=True, return_fig=False, **kwargs)
    else:
        try:
            return _plot_simple_stream_mpl(hv_data, stream, fig=None, axes=None, show_plot=False, ylim_std=0.75, return_fig=True)
        except:
            return _plot_simple_stream_obspy()


# Plot outlier curves
def plot_outlier_curves(hvsr_data, plot_engine='plotly', plotly_module='go', remove_outliers_during_plot=False,
                        outlier_threshold=0.98, use_percentile=True, use_hv_curves=False, 
                        from_roc=False, show_plot=True, verbose=False, discarded_curves=None):
    """Function to plot outlier curves, including which have been excluded

    Parameters
    ----------
    hvsr_data : HVSRData
        Input data object
    plot_engine : str = {'plotly', 'matplotlib'}
        Which plotting library to use, by default 'plotly'
    plotly_module : str = {'go', 'px'}
        Which plotly module to use if applicable, by default 'go'
    remove_outliers_during_plot : bool, optional
        Whether curves should also be removed when plotted. During sprit.run(), removal happens separately, so this is False.
    outlier_threshold : float, optional
        RMSE threshold (for removing outliers), by default 0.98
    use_percentile : bool, optional
        Whether to use percentile or raw value, by default True
    use_hv_curves : bool, optional
        Whether to perform analysis on HV curves (if True) or PSD curves (if False), by default False
    from_roc : bool, optional
        Helper parameter to determine if this is being called from sprit.remove_outlier_curves function, by default False
    show_plot : bool, optional
        Whether to show plot, by default True
    verbose : bool, optional
        Whether to print information to terminal, by default False

    Returns
    -------
    plotly figure
        Figure type depends on plotly_module
    """
    orig_args = locals().copy()    
    
    hv_data = hvsr_data
    
    plotlyList = ['plotly', 'plty', 'p']
    mplList = ['matplotlib', 'mpl', 'pyplot', 'mtpltlb', 'm']
    
    if outlier_threshold < 1:
        outlier_threshold = outlier_threshold * 100
    
    roc_kwargs = {'outlier_threshold':outlier_threshold,
                    'use_percentile':True,
                    'use_hv_curves':use_hv_curves,
                    'show_outlier_plot':False,
                    'plot_engine':'None',
                    'verbose':verbose
                    }
    
    if str(plot_engine).lower() in plotlyList:
        #outlier_fig = go.FigureWidget()
        pxList = ['px', 'express', 'exp', 'plotly express', 'plotlyexpress']
        if str(plotly_module).lower() in pxList:
            return __plotly_outlier_curves_px(**orig_args)
        
        outlier_fig = go.Figure()
        
        titleText = 'Outlier Curve Plot'
        if use_hv_curves:
            titleText += ' (H/V Curves)'
        else:
            titleText += ' PSD Curves'
        outlier_fig = go.Figure()
            
        if 'generate_psds_status' in hvsr_data.processing_status.keys() and hvsr_data.processing_status['generate_psds_status']:
            #log_textArea.value += f"\n\n{datetime.datetime.now()}\nremove_outlier_curves():\n'{roc_kwargs}"    
            #hvsr_data = sprit_hvsr.remove_outlier_curves(hvsr_data, **roc_kwargs)
            pass
        else:
            #log_textArea.value += f"\n\n{datetime.datetime.now()}\nremove_outlier_curves() attempted, but not completed. hvsr_data.processing_status['generate_psds_status']=False\n'{roc_kwargs}"
            return outlier_fig

        if roc_kwargs['use_hv_curves']:
            no_subplots = 1
            if hasattr(hvsr_data, 'hvsr_windows_df') and 'HV_Curves' in hvsr_data.hvsr_windows_df.columns:
                outlier_fig.data = []
                outlier_fig.update_layout(grid=None)  # Clear the existing grid layout
                outlier_subp = subplots.make_subplots(rows=no_subplots, cols=1, horizontal_spacing=0.01, vertical_spacing=0.1)
                outlier_fig.update_layout(grid={'rows': 1})
                #outlier_fig = go.FigureWidget(outlier_subp)
                outlier_fig = go.Figure(outlier_subp)

                x_data = hvsr_data['x_freqs']['Z']
                curve_traces = []
                for ind, (i, hv) in enumerate(hvsr_data.hvsr_windows_df.iterrows()):
                    nameLabel = f"Window starting at {i.strftime('%H:%M:%S')}<br>Window #{ind}"
                    curve_traces.append(go.Scatter(x=x_data, y=hv['HV_Curves'], 
                                hovertemplate=nameLabel, line=dict(color='rgba(0,0,0,0.1)', width=0.75),
                                showlegend=False))
                outlier_fig.add_traces(curve_traces)
                
                # Calculate a median curve, and reshape so same size as original
                medCurve = np.nanmedian(np.stack(hvsr_data.hvsr_windows_df['HV_Curves']), axis=0)
                outlier_fig.add_trace(go.Scatter(x=x_data, y=medCurve, line=dict(color='rgba(0,0,0,1)', width=1.5),showlegend=False))
                
                minY = np.nanmin(np.stack(hvsr_data.hvsr_windows_df['HV_Curves']))
                maxY = np.nanmax(np.stack(hvsr_data.hvsr_windows_df['HV_Curves']))
                totalWindows = hvsr_data.hvsr_windows_df.shape[0]
                #medCurveArr = np.tile(medCurve, (curr_data.shape[0], 1))

        else:
            no_subplots = 3
            outlier_fig.data = []
            outlier_fig.update_layout(grid=None)  # Clear the existing grid layout
            outlier_subp = subplots.make_subplots(rows=no_subplots, cols=1, horizontal_spacing=0.01, vertical_spacing=0.02,
                                                    row_heights=[1, 1, 1])
            outlier_fig.update_layout(grid={'rows': 3})
            #outlier_fig = go.FigureWidget(outlier_subp)
            outlier_fig = go.Figure(outlier_subp)

            if hasattr(hvsr_data, 'hvsr_windows_df'):
                rowDict = {'Z':1, 'E':2, 'N':3}
                showTLabelsDict={'Z':False, 'E':False, 'N':True}
                def comp_rgba(comp, a):
                    compstr = ''
                    if comp=='Z':
                        compstr = f'rgba(0, 0, 0, {a})'
                    if comp=='E':
                        compstr = f'rgba(50, 50, 250, {a})'
                    if comp=='N':
                        compstr = f'rgba(250, 50, 50, {a})'
                    return compstr                         
                compNames = ['Z', 'E', 'N']
                rmse_to_plot=[]
                med_traces=[]

                noRemoved = 0
                indRemoved = []
                for i, comp in enumerate(compNames):
                    if hasattr(hvsr_data, 'x_freqs'):
                        x_data = hvsr_data['x_freqs'][comp]
                    else:
                        x_data = [1/p for p in hvsr_data['ppsds'][comp]['period_xedges'][1:]]                    
                    column = 'psd_values_'+comp
                    # Retrieve data from dataframe (use all windows, just in case)
                    curr_data = np.stack(hvsr_data['hvsr_windows_df'][column])
                    
                    # Calculate a median curve, and reshape so same size as original
                    medCurve = np.nanmedian(curr_data, axis=0)
                    medCurveArr = np.tile(medCurve, (curr_data.shape[0], 1))
                    medTrace = go.Scatter(x=x_data, y=medCurve, line=dict(color=comp_rgba(comp, 1), width=1.5), 
                                                    name=f'{comp} Component', showlegend=True)
                    # Calculate RMSE
                    rmse = np.sqrt(((np.subtract(curr_data, medCurveArr)**2).sum(axis=1))/curr_data.shape[1])

                    rmse_threshold = np.percentile(rmse, roc_kwargs['outlier_threshold'])
                    
                    # Retrieve index of those RMSE values that lie outside the threshold
                    timeIndex = hvsr_data['hvsr_windows_df'].index
                    for j, curve in enumerate(curr_data):
                        if rmse[j] > rmse_threshold:
                            badTrace = go.Scatter(x=x_data, y=curve,
                                                line=dict(color=comp_rgba(comp, 1), width=1.5, dash='dash'),
                                                #marker=dict(color=comp_rgba(comp, 1), size=3),
                                                name=str(hvsr_data.hvsr_windows_df.index[j]), showlegend=False)
                            outlier_fig.add_trace(badTrace, row=rowDict[comp], col=1)
                            if j not in indRemoved:
                                indRemoved.append(j)
                            noRemoved += 1
                        else:
                            goodTrace = go.Scatter(x=x_data, y=curve,
                                                    line=dict(color=comp_rgba(comp, 0.01)), name=str(hvsr_data.hvsr_windows_df.index[j]), showlegend=False)
                            outlier_fig.add_trace(goodTrace, row=rowDict[comp], col=1)

                    #timeIndRemoved = pd.DatetimeIndex([timeIndex[ind] for ind in indRemoved])
                    #hvsr_data['hvsr_windows_df'].loc[timeIndRemoved, 'Use'] = False

                    outlier_fig.add_trace(medTrace, row=rowDict[comp], col=1)
                    
                    outlier_fig.update_xaxes(showticklabels=False, row=1, col=1)
                    outlier_fig.update_yaxes(title={'text':'Z'}, row=1, col=1)
                    outlier_fig.update_xaxes(showticklabels=False, row=2, col=1)
                    outlier_fig.update_yaxes(title={'text':'E'}, row=2, col=1)
                    outlier_fig.update_xaxes(showticklabels=True, row=3, col=1)
                    outlier_fig.update_yaxes(title={'text':'N'}, row=3, col=1)

                    outlier_fig.update_layout(margin={"l":10, "r":10, "t":30, 'b':0}, showlegend=True,
                                    title=f"{hvsr_data['site']} Outliers")
                    if comp == 'N':
                        minY = np.nanmin(curr_data)
                        maxY = np.nanmax(curr_data)
                    totalWindows = curr_data.shape[0]
                
                outlier_fig.add_annotation(
                    text=f"{len(indRemoved)}/{totalWindows} outlier windows removed",
                    x=np.log10(max(x_data)) - (np.log10(max(x_data))-np.log10(min(x_data))) * 0.01,
                    y=minY+(maxY-minY)*0.01,
                    xanchor="right", yanchor="bottom",#bgcolor='rgba(256,256,256,0.7)',
                    showarrow=False,row=no_subplots, col=1)


        outlier_fig.update_xaxes(type='log')
        outlier_fig.update_layout(paper_bgcolor='white', plot_bgcolor='white',
                                font_color='black', 
                                title=dict(font_color='black',
                                text=titleText))
        #with outlier_graph_widget:
        #    clear_output(wait=True)
        #    display(outlier_fig)
        if show_plot:
            outlier_fig.show()        
    else: # Matplotlib outlier plot
        #if discarded_curves is not None:
        #    for i, b in enumerate(hvsr_data['hvsr_windows_df'].index[pd.Series(discarded_curves)]):
        #        print('DSCURVES', discarded_curves)
        #        print(b)

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
    
        spMosaic = []
        if use_hv_curves:
            spMosaic.append(['HV Curve'])
            fSize = (8.5, 6)
        else:
            for c in compNames:
                spMosaic.append([c])
            fSize = (8.5, len(compNames) * 2)

            # Intialize to only get unique labels
            rem_label_got = False
            keep_label_got = False

        outlier_fig, ax = plt.subplot_mosaic(spMosaic, sharex=True, figsize=fSize)
            
        # Loop through each component, and determine which curves are outliers
        bad_rmse = []
        for i, column in enumerate(colNames):
            if column in compNames:
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

            # Iterate through each curve to determine if it's rmse is outside threshold, for plot
            keep_label_got = False
            rem_label_got = False
            for j, curve in enumerate(curr_data):
                label = None
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
                if not use_hv_curves:
                    if 'x_freqs' in hvsr_data.keys():
                        ax[compNames[i]].plot(hvsr_data.x_freqs[compNames[i]], curve, linewidth=linewidth, c=linecolor, linestyle=linestyle, alpha=alpha, label=label)
                    else:
                        ax[compNames[i]].plot(1/hvsr_data.ppsds[compNames[i]]['period_bin_centers'], curve, linewidth=linewidth, c=linecolor, linestyle=linestyle, alpha=alpha, label=label)
                else:
                    if 'x_freqs' in hvsr_data.keys():
                        ax["HV Curve"].plot(hvsr_data.x_freqs['Z'][:-1], curve, linewidth=linewidth, c=linecolor, linestyle=linestyle, alpha=alpha, label=label)
                    else:
                        ax["HV Curve"].plot(1/(hvsr_data.ppsds['Z']['period_bin_centers'][:-1]), curve, linewidth=linewidth, c=linecolor, linestyle=linestyle, alpha=alpha, label=label)                    
            
            # Plot the median curve
            if 'HV_Curves' in compNames[i]:
                axName = 'HV Curve'
                keyName = 'Z'
            else:
                axName = keyName = compNames[i]
            
            if not use_hv_curves:
                if 'x_freqs' in hvsr_data.keys():
                    ax[compNames[i]].plot(hvsr_data.x_freqs[compNames[i]], medCurve, linewidth=1, color='k', label='Median Curve')
                else:
                    ax[compNames[i]].plot(1/hvsr_data.ppsds[compNames[i]]['period_bin_centers'],medCurve, linewidth=1, color='k', label='Median Curve')
            else:
                if 'x_freqs' in hvsr_data.keys():
                    ax['HV Curve'].plot(hvsr_data.x_freqs['Z'][:-1], medCurve, linewidth=1, color='k', label='Median Curve')
                else:
                    ax['HV Curve'].plot(1/hvsr_data.ppsds['Z']['period_bin_centers'][:-1],medCurve, linewidth=1, color='k', label='Median Curve')


            # Format axis
            ax[axName].set_ylabel(f"{compNames[i]}")
            ax[axName].legend(fontsize=10, labelspacing=0.1)
            ax[axName].semilogx()

        outlier_fig.suptitle(f"{hvsr_data['site']}\n Curves Removed from Analysis")
        outlier_fig.set_layout_engine('constrained')
                
        hvsr_data['Outlier_Plot'] = outlier_fig 
    
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    if remove_outliers_during_plot:
        bad_rmse = np.unique(bad_rmse)
        if len(bad_rmse) > 0:
            hvsr_data['hvsr_windows_df']['Use'] = hvsr_data['hvsr_windows_df']['Use'] * (rmse_threshold > hvsr_data['hvsr_windows_df']['RMSE_'+column])

    
    hvsr_data['Outlier_Plot'] = outlier_fig 
    return outlier_fig


# Parse plot string
def parse_plot_string(plot_string):
    """Function to parse a plot string into a list readable by plotting functions

    Parameters
    ----------
    plot_string : str
        Plot string used by sprit.plot_hvsr to define results plot

    Returns
    -------
    list
        A list readable by various sprit plotting functions to show what to include in the results plot.
    """
    plot_list = plot_string.split()

    hvsrList = ['hvsr', 'hv', 'h']
    compList = ['component', 'comp', 'c']
    compPlus = [item + '+' for item in compList]
    specList = ['spectrogram', 'specgram', 'spec','sg', 's']

    hvInd = np.nan
    compInd = np.nan
    specInd = np.nan

    hvIndFound = False
    compIndFound = False
    specIndFound = False

    for i, item in enumerate(plot_list):
        if item.lower() in hvsrList and not hvIndFound:
            # assign the index
            hvInd = i
            hvIndFound = True
        if (item.lower() in compList or item.lower() in compPlus) and not compIndFound:
            # assign the index
            compInd = i
            compIndFound = True
        if item.lower() in specList and not specIndFound:
            # assign the index
            specInd = i
            specIndFound = True

    # Get individual plot lists (should already be correctly ordered)
    if hvInd is np.nan:
        hvsr_plot_list = ['HVSR']

    if compInd is np.nan:
        comp_plot_list = []
        if specInd is np.nan:
            if hvInd is not np.nan:
                hvsr_plot_list = plot_list
            spec_plot_list = []
        else:
            if hvInd is not np.nan:
                hvsr_plot_list = plot_list[hvInd:specInd]
            spec_plot_list = plot_list[specInd:]
    else:
        if hvInd is not np.nan:
            hvsr_plot_list = plot_list[hvInd:compInd]
        
        if specInd is np.nan:
            comp_plot_list = plot_list[compInd:]
            spec_plot_list = []
        else:
            comp_plot_list = plot_list[compInd:specInd]
            spec_plot_list = plot_list[specInd:]

    # Figure out how many subplots there will be
    plot_list_list = [hvsr_plot_list, comp_plot_list, spec_plot_list]

    return plot_list_list


# Parse the SPEC part of the plot string
def plot_results_plotly(hv_data, plot_string='HVSR p ann C+ p SPEC ann', azimuth='HV',
                results_fig=None, results_graph_widget=None, use_figure_widget=False,
                return_fig=False, show_results_plot=False, html_plot=False,
                verbose=False,):
    
    """Function to plot results using plotly

    Parameters
    ----------
    hv_data : sprit.HVSRData
        Data object to use for plotting
    plot_string : str, optional
        String for designating what to include in plot(s), by default 'HVSR p ann C+ p SPEC ann'
    results_fig : pyplot figure, optional
        Which pyplot figure to plot data onto. If None, makes new figure, by default None.
    results_graph_widget : plotly graph object widget, optional
        Which pyplot figure to plot data onto. If None, makes new widget, if applicable, by default None.
    use_figure_widget : bool, optional
        Whether to use figure widget, by default False
    return_fig : bool, optional
        Whether to return figure, by default False
    show_results_plot : bool, optional
        Wheather to show plot, by default False
    html_plot : bool, optional
        Whether to create an HTML version of the plot, by default False
    verbose : bool, optional
        Whether to print information to terminal, by default False

    Returns
    -------
    plotly figure
        Only if return_fig is True.
    """

    if results_fig is None:
        results_fig = go.FigureWidget()

    hvsr_data = hv_data

    plotymax = max(hvsr_data.hvsrp2['HV']) + (max(hvsr_data.hvsrp2['HV']) - max(hvsr_data.hvsr_curve))
    if plotymax > hvsr_data.BestPeak['HV']['A0'] * 1.5:
        plotymax = hvsr_data.BestPeak['HV']['A0'] * 1.5
    ylim = [0, plotymax]
    if isinstance(hvsr_data, sprit_hvsr.HVSRBatch):
        hvsr_data = hvsr_data[0]

    hvsrDF = hvsr_data.hvsr_windows_df

    plot_list = parse_plot_string(plot_string)

    combinedComp = False
    # By default there 3 subplots
    noSubplots = 3
    # Remove any subplots that are not indicated by plot_type parameter
    noSubplots = noSubplots - plot_list.count([])
    
    # Now, check if comp plot is combined with HV
    if plot_list[1] != [] and '+' not in plot_list[1][0]:
        combinedComp = True
        noSubplots -= 1
    
    # Get all data for each plotted item
    # Get subplot numbers based on plot_list
    spec = []
    if plot_list[0]==[]:
        # if for some reason, HVSR plot was not indicated, add it
        hv_plot_row = 1 # Default first row to hv (may change later)
        noSubplots += 1
        if plot_list[1] == []:
            comp_plot_row = None
            if plot_list[2] == []:
                spec_plot_row = None
                hv_plot_row = 1 #If nothing specified, do basic h/v plot
            else:
                spec_plot_row = 1 # If only spec specified
        else:
            comp_plot_row = 1 # If no HV specified by comp is, comp is subplot 1

            if plot_list[2] == []:
                spec_plot_row = None
            else:
                spec_plot_row = 2 # If only comp and spec specified comp first then spec
    else:
        hv_plot_row = 1 # HV specified explicitly
        if plot_list[1] == []:
            comp_plot_row = None
            if plot_list[2] == []:
                spec_plot_row = None
            else:
                spec_plot_row = 2 # if no comp specified, spec is 2nd subplot
        else:
            if combinedComp:
                comp_plot_row = 1
                if plot_list[2] == []:
                    spec_plot_row = None
                else:
                    spec_plot_row = 2
            else:
                comp_plot_row = 2
                if plot_list[2] == []:
                    spec_plot_row = None
                else:
                    spec_plot_row = 3       

    specList = []
    rHeights = [1]
    if hv_plot_row == 1:
        if comp_plot_row == 1:
            specList.append([{'secondary_y': True}])
            if spec_plot_row == 2:
                specList.append([{'secondary_y': False}])
    else:
        specList.append([{'secondary_y': False}])

        if noSubplots >= 2:
            specList.append([{'secondary_y': False}])
            rHeights = [1.5,1]
        if noSubplots == 3:
            specList.append([{'secondary_y': False}])
            rHeights = [2,1.5,1]
    
    # Failsafes
    while len(specList)<noSubplots:
        specList.append([{}])

    while len(rHeights)<noSubplots:
        rHeights.append(1)

    # Re-initialize results_fig
    results_fig.data = []
    results_fig.update_layout(grid=None)  # Clear the existing grid layout, in case applicable

    results_fig = make_subplots(rows=noSubplots, cols=1, horizontal_spacing=0.01, vertical_spacing=0.07,
                                specs=specList,
                                row_heights=rHeights)
    results_fig.update_layout(grid={'rows': noSubplots})

    if use_figure_widget:
        results_fig = go.FigureWidget(results_fig)

    if plot_list[1] != []:
        results_fig = _parse_comp_plot_list(hvsr_data, results_fig=results_fig, 
                                           comp_plot_list=plot_list[1])
        results_fig.update_xaxes(title_text='Frequency [Hz]',
                                 row=comp_plot_row, col=1)

    # HVSR Plot (plot this after COMP so it is on top COMP and to prevent deletion with no C+)
    results_fig = _parse_hv_plot_list(hvsr_data, hvsr_plot_list=plot_list, results_fig=results_fig)

    # Will always plot the HV Curve
    results_fig.add_trace(go.Scatter(x=hvsr_data.x_freqs['Z'], y=hvsr_data.hvsr_curve,
                        line={'color':'black', 'width':1.5}, marker=None, name='HVSR Curve'),
                        row=1, col='all')

    # SPEC plot
    if plot_list[2] != []:
        results_fig = _parse_spec_plot_list(hvsr_data, spec_plot_list=plot_list[2], subplot_num=spec_plot_row, azimuth=azimuth, results_fig=results_fig)

    # Final figure updating
    resultsFigWidth = 650

    components_HV_on_same_plot = (plot_list[1]==[] or '+' not in plot_list[1][0])
    if components_HV_on_same_plot:
        compxside = 'bottom'
        secondaryY = True
        showHVTickLabels = True
        showComptickLabels = True
    else:
        compxside = 'bottom'
        secondaryY = False
        showHVTickLabels = True
        showComptickLabels = True
    
    # Update H/V Plot
    results_fig.update_xaxes(type='log', title_text='Frequency [Hz]', title_standoff=0,
                    range=[np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1])],
                    side='bottom', showticklabels=showHVTickLabels,
                    row=1, col=1)
    results_fig.update_yaxes(title_text='H/V Ratio', row=1, col=1, 
                             secondary_y=False, range=ylim)

    # Update Component plot
    results_fig.update_xaxes(type='log', overlaying='x', showticklabels=showComptickLabels, title_standoff=0,
                             range=[np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1])],
                             side=compxside, row=comp_plot_row, col=1)    
    results_fig.update_yaxes(title_text="PPSD Amp\n[m2/s4/Hz][dB]", secondary_y=secondaryY, row=comp_plot_row, col=1)

    # Update Spec plot
    results_fig.update_yaxes(title_text='H/V Over Time', row=noSubplots, col=1)

    # Update entire figure
    titleString = f"{hvsr_data['site']} Results"
    results_fig.update_layout(margin={"l":40, "r":10, "t":35, 'b':0},
                            showlegend=False, autosize=False, width=resultsFigWidth, height=resultsFigWidth*0.7,
                            title=titleString)
    
    # Reset results_graph_widget and display 
    #if results_graph_widget is not None:
    #    with results_graph_widget:
    #        clear_output(wait=True)
    #        display(results_fig)

    if show_results_plot:
        if html_plot:
            results_fig.write_html(titleString.replace(' ', '_') + 'plot.html', auto_open=True)
        else:
            results_fig.show()
    
    if return_fig:
        return results_fig


# Parse the HVSR part of the plot string
def _parse_hv_plot_list(hv_data, hvsr_plot_list, results_fig=None, azimuth='HV'):
    """Function to plot the internal list used by the "HV" subplot of the restults plot

    Parameters
    ----------
    hv_data : HVSRData object
        _description_
    hvsr_plot_list : list
        List produced by parse_plot_string
    results_fig : matplotlib.Figure, optional
        Matplotlib Figure object to plot data onto. If None, new Figure created, by default None
    azimuth : str, optional
        Azimuth to use for calculation, by default 'HV'

    Returns
    -------
    matplotlib.figure.Figure
        Figure with HV plot per input hvsr_plot_list
    """
    hvsr_data = hv_data
    hv_plot_list = hvsr_plot_list[0]
    x_data = hvsr_data.x_freqs['Z']
    hvsrDF = hvsr_data.hvsr_windows_df

    plotymax = max(hvsr_data.hvsrp2['HV']) + (max(hvsr_data.hvsrp2['HV']) - max(hvsr_data.hvsr_curve))
    ylim = [0, plotymax]


    if results_fig is None:
        results_fig = go.Figure()

    if azimuth == 'HV':
        HVCol = 'HV_Curves'
    else:
        HVCol = 'HV_Curves_'+azimuth

    if 'tp' in hv_plot_list:
        allpeaks = []
        for row in hvsrDF[hvsrDF['Use']]['CurvesPeakFreqs_'+azimuth].values:
            for peak in row:
                allpeaks.append(peak)
        allInd = []
        for row, peakList in enumerate(hvsrDF[hvsrDF['Use']]['CurvesPeakIndices_'+azimuth].values):
            for ind in peakList:
                allInd.append((row, ind))
        x_vals = []
        y_vals = []
        y_max = np.nanmax(hvsr_data.hvsrp[azimuth])
        hvCurveInd = list(hvsrDF.columns).index(HVCol)

        for i, tp in enumerate(allpeaks):
            x_vals.extend([tp, tp, None]) # add two x values and a None
            y_vals.extend([0, hvsrDF.iloc[allInd[i][0], hvCurveInd][allInd[i][1]], None]) # add the first and last y values and a None            

        results_fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines',
                                        line=dict(width=4, dash="solid", 
                                        color="rgba(128,0,0,0.1)"), 
                                        name='Best Peaks Over Time'),
                                        row=1, col=1)

    if 't' in hv_plot_list:
        alltimecurves = np.stack(hvsrDF[hvsrDF['Use']][HVCol])
        for i, row in enumerate(alltimecurves):
            if i==0:
                showLeg = True
            else:
                showLeg= False
            results_fig.add_trace(go.Scatter(x=x_data[:-1], y=row, mode='lines',
                                        line=dict(width=0.5, dash="solid", 
                                        color="rgba(100, 110, 100, 0.8)"), 
                                        showlegend=showLeg,
                                        name='Ind. time win. curve', 
                                        hoverinfo='none'),
                                        row=1, col=1)

    if 'all' in hv_plot_list:
        for i, p in enumerate(hvsr_data['hvsr_peak_freqs'][azimuth]):
            if i==0:
                showLeg = True
            else:
                showLeg= False

            results_fig.add_trace(go.Scatter(
                x=[p, p, None], # set x to None
                y=[0, np.nanmax(np.stack(hvsrDF[HVCol])),None], # set y to None
                mode="lines", # set mode to lines
                line=dict(width=1, dash="dot", color="gray"), # set line properties
                name="All checked peaks", # set legend name
                showlegend=showLeg),
                row=1, col=1)

    if 'fr' in hv_plot_list:
        lowX = [hvsr_data.hvsr_band[0], hvsr_data.hvsr_band[0]]
        lowWinX = [hvsr_data.peak_freq_range[0], hvsr_data.peak_freq_range[0]]
        hiWinX = [hvsr_data.peak_freq_range[1], hvsr_data.peak_freq_range[1]]
        hiX =  [hvsr_data.hvsr_band[1], hvsr_data.hvsr_band[1]]
        
        yPts = ylim
        
        # Show windows where peak_freq_range is
        results_fig.add_trace(go.Scatter(x=lowWinX, y=yPts,
                                line={'color':'black', 'width':0.1}, marker=None,
                                fill='tozerox', fillcolor="rgba(128, 100, 100, 0.6)",
                                showlegend=False, name='Peak Frequency exclusion range',
                                hoverinfo='none'),
                                row=1, col=1)
        
        results_fig.add_trace(go.Scatter(x=hiWinX, y=yPts,
                                line={'color':'black', 'width':0.1},marker=None, 
                                showlegend=False,
                                hoverinfo='none'),
                                row=1, col=1)
        
        results_fig.add_trace(go.Scatter(x=hiX, y=yPts,
                                line=None, marker=None,
                                fill='tonextx', fillcolor="rgba(128, 100, 100, 0.6)",
                                name='Peak frequency exclusion range', hoverinfo='none'),
                                row=1, col=1)        

    if '-s' not in hv_plot_list:
        # Show standard deviation
        results_fig.add_trace(go.Scatter(x=x_data, y=hvsr_data.hvsrp2[azimuth],
                                line={'color':'black', 'width':0.1},marker=None, 
                                showlegend=False, name='Log. St.Dev. Upper',
                                hoverinfo='none'),
                                row=1, col=1)
        
        results_fig.add_trace(go.Scatter(x=x_data, y=hvsr_data.hvsrm2[azimuth],
                                line={'color':'black', 'width':0.1},marker=None,
                                fill='tonexty', fillcolor="rgba(128, 128, 128, 0.6)",
                                name='Log. St.Dev.', hoverinfo='none'),
                                row=1, col=1)
            
    if 'p' in hv_plot_list:
        results_fig.add_trace(go.Scatter(
            x=[hvsr_data['BestPeak'][azimuth]['f0'], hvsr_data['BestPeak'][azimuth]['f0'], None], # set x to None
            y=[0,np.nanmax(np.stack(hvsrDF['HV_Curves'])),None], # set y to None
            mode="lines", # set mode to lines
            line=dict(width=1, dash="dash", color="black"), # set line properties
            name="Best Peak"),
            row=1, col=1)

    if 'ann' in hv_plot_list:
        # Annotate best peak
        results_fig.add_annotation(x=np.log10(hvsr_data['BestPeak'][azimuth]['f0']),
                                y=0, yanchor='bottom', xanchor='center',
                                text=f"{hvsr_data['BestPeak'][azimuth]['f0']:.3f} Hz",
                                bgcolor='rgba(255, 255, 255, 0.7)',
                                showarrow=False,
                                row=1, col=1)
    results_fig.update_yaxes(range=ylim, row=1, col=1)
    return results_fig


# Parse the COMPONENT part of the plot string
def _parse_comp_plot_list(hv_data, comp_plot_list, plot_with_hv=False, results_fig=None, azimuth='HV'):
    """Function to plot the internal list used by the "Components" subplot of the results plot

    Parameters
    ----------
    hv_data : HVSRData object
        _description_
    comp_plot_list : list
        List produced by parse_plot_string
    plot_with_hv : bool, default=False
        Whether to plot in same subplot as HV curve
    results_fig : matplotlib.Figure, optional
        Matplotlib Figure object to plot data onto. If None, new Figure created, by default None
    azimuth : str, optional
        Azimuth to use for calculation, by default 'HV'

    Returns
    -------
    matplotlib.figure.Figure
        Figure with Components plot per input comp_plot_list
    """    
    hvsr_data = hv_data
    if results_fig is None:
        results_fig=go.Figure()

    # Initial setup
    x_data = hvsr_data.x_freqs['Z']
    hvsrDF = hvsr_data.hvsr_windows_df
    
    same_plot = False
    if plot_with_hv:
        same_plot = True
    else:
        same_plot = ((comp_plot_list != []) and ('+' not in comp_plot_list[0]))

    if same_plot:
        yaxis_to_use = 'y2'
        use_secondary = True
        transparency_modifier = 0.5
    else:
        yaxis_to_use = 'y'
        use_secondary=False
        transparency_modifier = 1

    # Keep components if azimuth is used, but make them lighter
    if len(hvsr_data.hvsr_az.keys()) > 0:
        h_transparency_modifier = transparency_modifier * 0.5
    else:
        h_transparency_modifier = transparency_modifier
        
    v_transparency_modifier = transparency_modifier
    az_transparency_modifier = transparency_modifier

        
    h_alpha = 0.4 * h_transparency_modifier
    v_alpha = 0.4 * v_transparency_modifier
    az_alpha = 0.4 * az_transparency_modifier
    components = ['Z', 'E', 'N']

    compColor_semi_light = {'Z':f'rgba(128,128,128,{v_alpha})',
                'E':f'rgba(0,0,128,{h_alpha})',
                'N':f'rgba(128,0,0,{h_alpha})'}

    h_alpha = 0.7 * h_transparency_modifier
    v_alpha = 0.7 * v_transparency_modifier
    az_alpha = 0.7 * az_transparency_modifier    
    compColor_semi = {'Z':f'rgba(128,128,128,{v_alpha})',
                    'E':f'rgba(100,100,128,{h_alpha})', 
                    'N':f'rgba(128,100,100,{h_alpha})'}

    compColor = {'Z':f'rgba(128,128,128,{v_alpha})', 
                'E':f'rgba(100,100,250,{h_alpha})', 
                'N':f'rgba(250,100,100,{h_alpha})'}

    for az in hvsr_data.hvsr_az.keys():
        components.append(az)
        compColor_semi_light[az] = f'rgba(0,128,0,{az_alpha})'
        compColor_semi[az] = f'rgba(100,128,100,{az_alpha})'
        compColor[az] = f'rgba(100,250,100,{az_alpha})'

    # Whether to plot in new subplot or not
    if same_plot:
        compRow=1
    else:
        compRow=2

    # Whether to plot individual time curves
    if 't' in comp_plot_list:
        for comp in components:
            alltimecurves = np.stack(hvsrDF[hvsrDF['Use']]['psd_values_'+comp])
            for i, row in enumerate(alltimecurves):
                if i==0:
                    showLeg = True
                else:
                    showLeg= False
                
                results_fig.add_trace(go.Scatter(x=x_data[:-1], y=row, mode='lines',
                                line=dict(width=0.5, dash="solid", 
                                color=compColor_semi[comp]),
                                name='Ind. time win. curve',
                                showlegend=False,
                                hoverinfo='none',
                                yaxis=yaxis_to_use),
                                secondary_y=use_secondary,
                                row=compRow, col=1)

    # Code to plot standard deviation windows, if not removed
    if '-s' not in comp_plot_list:
        for comp in components:
            # Show standard deviation
            results_fig.add_trace(go.Scatter(x=x_data, y=hvsr_data.ppsd_std_vals_p[comp],
                                    line={'color':compColor_semi_light[comp], 'width':0.1},marker=None, 
                                    showlegend=False, name='Log. St.Dev. Upper',
                                    hoverinfo='none',    
                                    yaxis=yaxis_to_use),
                                    secondary_y=use_secondary,
                                    row=compRow, col=1)
            
            results_fig.add_trace(go.Scatter(x=x_data, y=hvsr_data.ppsd_std_vals_m[comp],
                                    line={'color':compColor_semi_light[comp], 'width':0.1},marker=None,
                                    fill='tonexty', fillcolor=compColor_semi_light[comp],
                                    name=f'St.Dev. [{comp}]', hoverinfo='none', showlegend=False, 
                                    yaxis=yaxis_to_use),
                                    secondary_y=use_secondary,
                                    row=compRow, col=1)
            
    # Code to plot location of best peak
    if 'p' in comp_plot_list:
        minVal = 10000
        maxVal = -10000
        for comp in components:
            currPPSDCurve = hvsr_data['psd_values_tavg'][comp]
            if np.nanmin(currPPSDCurve) < minVal:
                minVal = np.nanmin(currPPSDCurve)
            if np.nanmax(currPPSDCurve) > maxVal:
                maxVal = np.nanmax(currPPSDCurve)

        results_fig.add_trace(go.Scatter(
            x=[hvsr_data['BestPeak'][azimuth]['f0'], hvsr_data['BestPeak'][azimuth]['f0'], None], # set x to None
            y=[minVal,maxVal,None], # set y to None
            mode="lines", # set mode to lines
            line=dict(width=1, dash="dash", color="black"), # set line properties
            name="Best Peak",
            yaxis=yaxis_to_use),
            secondary_y=use_secondary,
            row=compRow, col=1)
        
    # Code to annotate value of best peak
    if 'ann' in comp_plot_list:
        minVal = 1e6 # A high number to compare against (comparer should always be lower)
        for comp in components:
            currPPSDCurve = hvsr_data['ppsd_std_vals_m'][comp]
            if np.nanmin(currPPSDCurve) < minVal:
                minVal = np.nanmin(currPPSDCurve)
        results_fig.add_annotation(x=np.log10(hvsr_data['BestPeak'][azimuth]['f0']),
                        y=minVal,
                        text=f"{hvsr_data['BestPeak'][azimuth]['f0']:.3f} Hz",
                        bgcolor='rgba(255, 255, 255, 0.7)',
                        showarrow=False,
                        yref=yaxis_to_use,
                        secondary_y=use_secondary,
                        row=compRow, col=1)

    # Plot the main averaged component PPSDs
    for comp in components:
        results_fig.add_trace(go.Scatter(x=hvsr_data.x_freqs[comp],
                                        y=hvsr_data['psd_values_tavg'][comp],
                                        line=dict(width=2, dash="solid", 
                                        color=compColor[comp]),marker=None, 
                                        name='PPSD Curve '+comp,    
                                        yaxis=yaxis_to_use), 
                                        secondary_y=use_secondary,
                                        row=compRow, col='all')

    # If new subplot, update accordingly
    if compRow==2:
        results_fig.update_xaxes(type='log',
                        range=[np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1])],
                        row=compRow, col=1)
    return results_fig


# Parse the SPEC part of the plot string
def _parse_spec_plot_list(hv_data, spec_plot_list, subplot_num, results_fig=None, azimuth='HV'):
    """Function to plot the internal list used by the "Spectrogram" subplot of the results plot

    Parameters
    ----------
    hv_data : HVSRData object
        _description_
    spec_plot_list : list
        List produced by parse_plot_string
    subplot_num : bool, default=False
        Which subplot to plot the spectrogram style plot in
    results_fig : matplotlib.Figure, optional
        Matplotlib Figure object to plot data onto. If None, new Figure created, by default None
    azimuth : str, optional
        Azimuth to use for calculation, by default 'HV'

    Returns
    -------
    matplotlib.figure.Figure
        Figure with specgram plot per input spec_plot_list
    """   
    
    hvsr_data = hv_data

    if results_fig is None:
        results_fig=go.Figure()

    if azimuth == 'HV':
        HVCol = 'HV_Curves'
    else:
        HVCol = 'HV_Curves_'+azimuth

    # Initial setup
    hvsrDF = hvsr_data.hvsr_windows_df
    specAxisTimes = np.array([dt.isoformat() for dt in hvsrDF.index.to_pydatetime()])
    y_data = hvsr_data.x_freqs['Z'][1:]
    image_data = np.stack(hvsrDF[HVCol]).T

    maxZ = np.percentile(image_data, 100)
    minZ = np.percentile(image_data, 0)

    use_mask = hvsr_data.hvsr_windows_df.Use.values
    use_mask = np.tile(use_mask, (image_data.shape[0],1))
    use_mask = np.where(use_mask is False, np.nan, use_mask)

    hmap = go.Heatmap(z=image_data,
                x=specAxisTimes,
                y=y_data,
                colorscale='Turbo',
                showlegend=False,
                #opacity=0.7,
                hovertemplate='Time [UTC]: %{x}<br>Frequency [Hz]: %{y:.2f}<br>H/V Amplitude: %{z:.2f}<extra></extra>',
                zmin=minZ,zmax=maxZ, showscale=False, name='HV Curve Amp. over Time')
    results_fig.add_trace(hmap, row=subplot_num, col=1)

    data_used = go.Heatmap(
        x=specAxisTimes,
        y=y_data,
        z=use_mask.astype(bool),
        showlegend=False,
        colorscale=[[0, 'rgba(0,0,0,0.66)'], [0.25, 'rgba(0,0,0,0.66)'], [1, 'rgba(250,250,250,0)']],
        showscale=False, name='Used')
    results_fig.add_trace(data_used, row=subplot_num, col=1)


    # tp currently is not being added to spec_plot_list
    if 'tp' in spec_plot_list:
        yvals = []
        for row in hvsrDF[HVCol].values:
            maxInd = np.argmax(row)
            yvals.append(y_data[maxInd])
        tp_trace = go.Scatter(x=specAxisTimes, y=yvals, mode='markers',
                                line=None, marker=dict(color='white', size=2, line=dict(color='black', width=0.1)), name='Individual H/V Peaks')
        results_fig.add_trace(tp_trace, row=subplot_num, col='all')

    if 'p' in spec_plot_list:
        results_fig.add_hline(y=hvsr_data['BestPeak'][azimuth]['f0'], line_width=1, line_dash='dash', line_color='black', row=subplot_num, col='all')

    if 'ann' in spec_plot_list:
        results_fig.add_annotation(x=specAxisTimes[-1],
                                y=hvsr_data['hvsr_band'][1],
                                text=f"Peak: {hvsr_data['BestPeak'][azimuth]['f0']:.3f} Hz",
                                bgcolor='rgba(255, 255, 255, 0.7)',
                                showarrow=False, xanchor='right', yanchor='top',
                                row=subplot_num, col='all')

    if 'leg' in spec_plot_list:
        pass

    results_fig.update_yaxes(type='log',
                    range=[np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1])],
                    row=subplot_num, col=1)

    results_fig.add_annotation(
        text=f"{hvsrDF['Use'].astype(bool).sum()}/{hvsrDF.shape[0]} windows used",
        x=max(specAxisTimes),
        y=np.log10(min(y_data))+(np.log10(max(y_data))-np.log10(min(y_data)))*0.01,
        xanchor="right", yanchor="bottom",bgcolor='rgba(256,256,256,0.7)',
        showarrow=False,row=subplot_num, col=1)

    return results_fig


# Helper function to get the array of values using the "Use" column (or equivalent of hvsr_windows_df)
def _get_use_array(hvsr_data, stream=None, f=None, timeWindowArr=None, psdArr=None):
    
    if stream is None and hasattr(hvsr_data, 'stream_edited'):
        streamEdit = hvsr_data.stream_edited.copy()
    elif stream is None and hvsr_data is not None:
        streamEdit = hvsr_data.stream.copy()
    else:
        streamEdit = stream.copy()

    earliestStart = UTCDateTime(3000, 12, 31)
    for trace in streamEdit:
        if trace.stats.starttime < earliestStart:
            earliestStart = trace.stats.starttime

    zList = []
    eList = []
    nList = []
    streamEdit = streamEdit.split()
    for trace in streamEdit:
        traceSTime = trace.stats.starttime
        traceETime = trace.stats.endtime

        if trace.stats.component == 'Z':
            zList.append([traceSTime, traceETime])
        if trace.stats.component == 'E':
            eList.append([traceSTime, traceETime])
        if trace.stats.component == 'N':
            nList.append([traceSTime, traceETime])

    gapListUTC = []
    for i, currWindow in enumerate(zList):
        if i > 0:
            prevWindow = zList[i-1]

            gapListUTC.append([prevWindow[1], currWindow[0]])

    gapList = [[np.datetime64(gTimeUTC.datetime) for gTimeUTC in gap] for gap in gapListUTC]

    if hasattr(hvsr_data, 'hvsr_windows_df'):
        hvdf = hvsr_data.hvsr_windows_df
        tps = pd.Series(hvdf.index.copy(), name='TimesProcessed_Start', index=hvdf.index)
        hvdf["TimesProcessed_Start"] = tps
        useArrShape = f.shape[0]
    else:
        useSeries = pd.Series([True]*(timeWindowArr.shape[0]-1), name='Use')
        sTimeSeries = pd.Series(timeWindowArr[:-1], name='TimesProcessed')
        eTimeSeries = pd.Series(timeWindowArr[1:], name='TimesProcessed_End')

        hvdf = pd.DataFrame({'TimesProcessed': sTimeSeries,
                             'TimesProcessed_End': eTimeSeries,
                             'Use': useSeries})

        hvdf.set_index('TimesProcessed', inplace=True, drop=True)
        hvdf['TimesProcessed_Start'] = timeWindowArr[:-1]
        
        useArrShape = psdArr.shape[0]

    if 'TimesProcessed_Obspy' not in hvdf.columns:
        hvdf['TimesProcessed_Obspy'] = [UTCDateTime(dt64) for dt64 in sTimeSeries]
        hvdf['TimesProcessed_ObspyEnd'] = [UTCDateTime(dt64) for dt64 in eTimeSeries]

    # Do processing
    if len(gapListUTC) > 0:
        for gap in gapListUTC:

            stOutEndIn = hvdf['TimesProcessed_Obspy'].gt(gap[0]) & hvdf['TimesProcessed_Obspy'].lt(gap[1])
            stInEndOut = hvdf['TimesProcessed_ObspyEnd'].gt(gap[0]) & hvdf['TimesProcessed_ObspyEnd'].lt(gap[1])
            bothIn = hvdf['TimesProcessed_Obspy'].lt(gap[0]) & hvdf['TimesProcessed_ObspyEnd'].gt(gap[1])
            bothOut = hvdf['TimesProcessed_Obspy'].gt(gap[0]) & hvdf['TimesProcessed_ObspyEnd'].lt(gap[1])

            hvdf.loc[hvdf[stOutEndIn | stInEndOut | bothIn | bothOut].index, 'Use'] = False

    return hvdf, useArrShape


# Plot Obspy Trace in axis using matplotlib
def _plot_simple_stream_obspy(stream, hv_data=None, fig=None, axes=None, decimate=True, show_plot=False, ylim_std=0.75, return_fig=True):
    """Function to plot a stream of data with Z, E, N components using matplotlib. Similar to obspy.Stream.Plot(), but will be formatted differently and eventually more customizable.
    This is also used in various functions throughout the package.

    Parameters
    ----------
    stream : obspy.core.Stream.stream
        Obpsy stream of data with Z, E, N componenents
    hv_data : HVSRData or HVSRBatch
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
        fig, axes = plt.subplot_mosaic([['Z'],['N'],['E']], sharex=True, sharey=False, figsize=(17, 7))

    if isinstance(stream, sprit_hvsr.HVSRData) and hv_data is None:
        hv_data = stream
        stream = hv_data.stream
    
    new_stream = stream.copy()
    #axis.plot(trace.times, trace.data)
    
    sTime = stream[0].stats.starttime
    timeList = {}
    mplTimes = {}

    #In case data is masked, need to split, decimate, then merge back together
    if isinstance(new_stream[0].data, np.ma.masked_array):
        new_stream = new_stream.split()
    
    if decimate:
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
                pColor='k'
            elif key=='N':
                pColor='r'
            else:
                pColor='b'
            axes[key].plot(mplTimes[key], tr.data, color=pColor, linewidth=0.15)


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
            if hasattr(hv_data, 'hvsr_band'):
                xmin = hv_data['hvsr_band'][0]
            else:
                xmin = HVSR_BAND[0]
        axes[comp].set_xlim([xmin, xmax])

    if hasattr(hv_data, 'site'):
        supTitle = hv_data['site']
    else:
        supTitle = f'Input seismic data for {stream.merge()[0].id[:-4]}'
    fig.suptitle(supTitle)
    
    day = "{}-{}-{}".format(stream[0].stats.starttime.year, stream[0].stats.starttime.month, stream[0].stats.starttime.day)
    axes['E'].set_xlabel('UTC Time \n'+ day)

    #plt.rcParams['figure.dpi'] = 100
    #plt.rcParams['figure.figsize'] = (5,4)
    
    #fig.tight_layout()
    fig.canvas.draw()

    if show_plot:
        plt.show()

    if return_fig:
        return fig
    return                 


# Helper function to plot the input stream using plotly
def _plot_input_stream_plotly(hv_data=None, stream=None, input_fig=None,
                        spectrogram_component='Z', decimate=True,
                        show_plot=True, return_fig=False):
    
        hvsr_data = hv_data

        if stream is None and hasattr(hv_data, 'stream'):
            stream = hv_data.stream


        specKey = str(spectrogram_component).upper()

        no_subplots = 5
        if input_fig is None:
            input_fig = make_subplots(rows=no_subplots, cols=1,
                                    row_heights=[0.5, 0.02, 0.16, 0.16, 0.16],
                                    shared_xaxes=True,
                                    horizontal_spacing=0.01,
                                    vertical_spacing=0.01
                                    )

        # Windows PSD and Used
        zStream = stream.select(component='Z').merge()
        zTraces = zStream.split()
        zTrace = zStream[0]

        eStream = stream.select(component='E').merge()
        eTraces = eStream.split()
        eTrace = eStream[0]

        nStream = stream.select(component='N').merge()
        nTraces = nStream.split()
        nTrace = nStream[0]
        

        sTimeZ = zTrace.stats.starttime
        sTimeE = eTrace.stats.starttime
        sTimeN = nTrace.stats.starttime        
        # Z
        for i, zTr in enumerate(zTraces):
            if i == 0:
                xTraceTimesZ = [np.datetime64((sTimeZ + tT).datetime) for tT in zTr.times()]
                xTraceTimesAppZ = [[np.datetime64((sTimeZ + tT).datetime) for tT in zTr.times()]]
            else:
                xTraceTimesAppZ.append([np.datetime64((sTimeZ + tT).datetime) for tT in zTr.times()])
                xTraceTimesZ.extend([np.datetime64((sTimeZ + tT).datetime) for tT in zTr.times()])
        
        # E
        for i, eTr in enumerate(eTraces):
            if i == 0:
                xTraceTimesE = [np.datetime64((sTimeE + tT).datetime) for tT in eTr.times()]
                xTraceTimesAppE = [[np.datetime64((sTimeE + tT).datetime) for tT in eTr.times()]]
            else:
                xTraceTimesAppE.append([np.datetime64((sTimeE + tT).datetime) for tT in eTr.times()])
                xTraceTimesE.extend([np.datetime64((sTimeE + tT).datetime) for tT in eTr.times()])

        # N
        for i, nTr in enumerate(nTraces):
            if i == 0:
                xTraceTimesN = [np.datetime64((sTimeN + tT).datetime) for tT in nTr.times()]
                xTraceTimesAppN = [[np.datetime64((sTimeN + tT).datetime) for tT in nTr.times()]]
            else:
                xTraceTimesAppN.append([np.datetime64((sTimeN + tT).datetime) for tT in nTr.times()])
                xTraceTimesN.extend([np.datetime64((sTimeN + tT).datetime) for tT in nTr.times()])


        if specKey == 'N':
            specTrace = nTrace
        elif specKey == 'E':
            specTrace = eTrace
        else:
            specTrace = zTrace

        f, specTimes, psdArr = signal.spectrogram(x=specTrace.data,
                                fs=specTrace.stats.sampling_rate,
                                mode='magnitude')

        stream_spec_freqs = f
        stream_spec_times = specTimes
        psdArr = psdArr

        if f[0] == 0:
            f[0] = f[1] / 10  # Fix so bottom number is not 0

        specTimes = list(specTimes)
        specTimes.insert(0, 0)
        timeWindowArr = np.array([np.datetime64((sTimeZ + tT).datetime) for tT in specTimes])
        
        if hasattr(hvsr_data, 'hvsr_band'):
            hvsrBand = hvsr_data['hvsr_band']
        else:
            hvsrBand = HVSR_BAND

        minz = np.percentile(psdArr, 1)
        maxz = np.percentile(psdArr, 99)

        hmap = goHeatmap(z=psdArr,
                        x=timeWindowArr[:-1],
                        y=f,
                        colorscale='Turbo', #opacity=0.8,
                        showlegend=False,
                        hovertemplate='Time [UTC]: %{x}<br>Frequency [Hz]: %{y:.2f}<br>Spectrogram Magnitude: %{z:.2f}<extra></extra>',
                        zmin=minz, zmax=maxz, showscale=False, name=f'{specKey} Component Spectrogram')
        input_fig.add_trace(hmap, row=1, col=1)
        input_fig.update_yaxes(type='log', range=[np.log10(hvsrBand[0]), np.log10(hvsrBand[-1])], row=1, col=1)
        input_fig.update_yaxes(title={'text':f'Spectrogram ({specKey})'}, row=1, col=1)

        # Get Use Array and hvdf
        hvdf, useArrShape = _get_use_array(hvsr_data, stream=stream, f=f, timeWindowArr=timeWindowArr, psdArr=psdArr)

        timelineFig = pxTimeline(data_frame=hvdf,
                                 x_start='TimesProcessed_Start',
                                 x_end='TimesProcessed_End',
                                 y=['Used']*hvdf.shape[0],
                                 color='Use',
                                 color_discrete_map={True: 'rgba(0,255,0,1)',
                                                    False: 'rgba(255,0,0,1)'})
        for timelineTrace in timelineFig.data:
            input_fig.add_trace(timelineTrace, row=2, col=1)

        useArr = np.tile(hvdf.Use, (useArrShape, 1))
        useArr = np.where(useArr is True, np.ones_like(useArr), np.zeros_like(useArr)).astype(int)

        specOverlay = goHeatmap(z=useArr,
                            x=hvdf['TimesProcessed_Start'],
                            y=f,
                            colorscale=[[0, 'rgba(0,0,0,0.8)'], [0.1, 'rgba(255,255,255, 0.00001)'], [1, 'rgba(255,255,255, 0.00001)']],
                            showlegend=False,
                            #hovertemplate='Time [UTC]: %{x}<br>Frequency [Hz]: %{y:.2f}<br>Spectrogram Magnitude: %{z:.2f}<extra></extra>',
                            showscale=False, name=f'{specKey} Component Spectrogram')
        input_fig.add_trace(specOverlay, row=1, col=1)
        
        # Get min and max of all traces to scale consistently
        minTraceData = min(min(zTrace.data), min(eTrace.data), min(nTrace.data))
        maxTraceData = max(max(zTrace.data), max(eTrace.data), max(nTrace.data))

        streamOverlay = goHeatmap(z=useArr,
                        x=hvdf['TimesProcessed_Start'],
                        y=np.linspace(minTraceData, maxTraceData, useArr.shape[0]),
                        colorscale=[[0, 'rgba(0,0,0,0.8)'], [0.1, 'rgba(255,255,255, 0.00001)'], [1, 'rgba(255,255,255, 0.00001)']],
                        showlegend=False,
                        #hovertemplate='Time [UTC]: %{x}<br>Frequency [Hz]: %{y:.2f}<br>Spectrogram Magnitude: %{z:.2f}<extra></extra>',
                        showscale=False, name=f'{specKey} Component Spectrogram')
        input_fig.add_trace(streamOverlay, row=3, col=1)
        input_fig.add_trace(streamOverlay, row=4, col=1)
        input_fig.add_trace(streamOverlay, row=5, col=1)

        input_fig.update_yaxes(type='log', range=[np.log10(hvsrBand[0]), np.log10(hvsrBand[-1])], row=1, col=1)
        input_fig.update_yaxes(title={'text':f'Spectrogram ({specKey})'}, row=1, col=1)

        # Data traces
        # Z Traces
        for i, zTr in enumerate(zTraces):
            if i == 0:
                zDataFig = pxScatter(x=xTraceTimesAppZ[i], y=zTr.data)
            else:
                zTempFig = pxScatter(x=xTraceTimesAppZ[i])
                for zFigTrace in zTempFig.data:
                    zDataFig.add_trace(zFigTrace)
        
        zDataFig.update_traces(mode='markers+lines',
                            marker=dict(size=1, color='rgba(0,0,0,1)'),
                            line=dict(width=1, color='rgba(0,0,0,1)'),
                            selector=dict(mode='markers'))
        for zTrace in zDataFig.data:
            input_fig.add_trace(zTrace, row=3, col=1)

        # E Traces
        for i, eTr in enumerate(eTraces):
            if i == 0:
                eDataFig = pxScatter(x=xTraceTimesAppE[i], y=eTr.data)
            else:
                eTempFig = pxScatter(x=xTraceTimesAppE[i])
                for eFigTrace in eTempFig.data:
                    eDataFig.add_trace(eFigTrace)
        
        eDataFig.update_traces(mode='markers+lines',
                            marker=dict(size=1, color='rgba(0,0,255,1)'),
                            line=dict(width=1, color='rgba(0,0,255,1)'),
                            selector=dict(mode='markers'))
        for eTrace in eDataFig.data:
            input_fig.add_trace(eTrace, row=4, col=1)

        # N Traces
        for i, nTr in enumerate(nTraces):
            if i == 0:
                nDataFig = pxScatter(x=xTraceTimesAppN[i], y=nTr.data)
            else:
                nTempFig = pxScatter(x=xTraceTimesAppN[i])
                for nFigTrace in nTempFig.data:
                    nDataFig.add_trace(nFigTrace)
        
        nDataFig.update_traces(mode='markers+lines',
                            marker=dict(size=1, color='rgba(255,0,0,1)'),
                            line=dict(width=1, color='rgba(255,0,0,1)'),
                            selector=dict(mode='markers'))

        for nTrace in nDataFig.data:
            input_fig.add_trace(nTrace, row=5, col=1)

        input_fig.update_layout(title_text="Frequency and Data values over time", 
                            height=650, showlegend=False)

        input_fig.update_xaxes(type='date', range=[xTraceTimesZ[0], xTraceTimesZ[-1]])

        hvsr_data['Input_Plot'] = input_fig # not currently using

        if show_plot:
            input_fig.show()

        if return_fig:
            return input_fig
        else:
            return hvsr_data


# Plot input from stream using matplotlib
def _plot_input_stream_mpl(stream, hv_data=None, component='Z', stack_type='linear', detrend='mean', decimate=True, dbscale=True, fill_gaps=None, fig=None, ax=None, cmap_per=[0.1, 0.9], ylimstd=5, show_plot=False, return_fig=True,  **kwargs):
    """Function for plotting spectrogram in a nice matplotlib chart from an obspy.stream

    For more details on main function being called, see https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.specgram.html 

    Parameters
    ----------
    stream : obspy.core.stream.Stream object
        Stream for which to plot spectrogram
    hv_data : dict, optional
        If dict, will read the hvsr_band from the a dictionary with a key ['hvsr_band'] (like the parameters dictionary). Otherwise, can read in the hvsr_band as a two-item list. Or, if None, defaults to [0.1,50], by default None.
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
        Two-item list wwith clip limits as percentage of values of colormap, so extremes do not taint colormap, by default [0.1, 0.9]

    Returns
    -------
    fig
        If return_fig is True, matplotlib figure is returned
    ax
        If return_fig is True, matplotlib axis is returned
    """ 
    og_stream = stream.copy()

    # Get the latest start time and earliest end times of all components
    traceList = []
    maxStartTime = obspy.UTCDateTime(-1e10) #Go back pretty far (almost 400 years) to start with
    minEndTime = obspy.UTCDateTime(1e10)
    for comp in ['E', 'N', 'Z']:
        # Get all traces from selected component in comp_st
        if isinstance(stream.select(component=comp).merge()[0].data, np.ma.masked_array):
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

    # Trim all traces to the same start/end time for total
    for tr in traceList:
        tr.trim(starttime=maxStartTime, endtime=minEndTime)
    og_stream.trim(starttime=maxStartTime, endtime=minEndTime)      

    # Merge stream and stack if necessary
    stream = obspy.Stream(traceList)
    stream.merge()

    if len(stream) > 1:
        stream.stack(group_by='all', npts_tol=200, stack_type=stack_type)  

    newFig= False
    if fig is None and ax is None:
        # Organize the chart layout
        mosaic = [['spec'],
                  ['spec'],
                  ['spec'],
                  ['spec'],
                  ['signalz'], 
                  ['signaln'], 
                  ['signale']]

        if 'figsize' in kwargs:
            fSize = kwargs['figsize']
        else:
            fSize = (17, 7)
        fig, ax = plt.subplot_mosaic(mosaic, sharex=True, gridspec_kw={'hspace': 0.3}, figsize=fSize)
        #fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True)
        newFig = True

    data = stream[0].data
    if isinstance(data, np.ma.MaskedArray) and fill_gaps is not None:
        data = data.filled(fill_gaps)
    sample_rate = stream[0].stats.sampling_rate

    if 'cmap' in kwargs.keys():
        cmap = kwargs['cmap']
    else:
        cmap = 'turbo'

    if hv_data is None:
        hvsr_band = DEFAULT_BAND
    else:
        hvsr_band = hv_data['hvsr_band']
    ymin = hvsr_band[0]
    ymax = hvsr_band[1]

    if dbscale:
        scale = 'dB'
    else:
        scale = None

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=RuntimeWarning)
        spec, freqs, times, im = ax['spec'].specgram(x=data, Fs=sample_rate, detrend=detrend, scale_by_freq=True, scale=scale)
    im.remove()

    minfreqInd = 0
    difference_array = freqs - ymin
    for i, d in enumerate(difference_array):
        if d > 0:
            if i-1 < 0:
                i=1
            minfreqInd = i-1
            break
    
    maxfreqInd = -1
    difference_array = freqs - ymax
    for i, d in enumerate(difference_array):
        if d > 0:
            maxfreqInd = i-1
            break

    array_displayed = spec[minfreqInd:maxfreqInd, :]

    vmin = np.nanpercentile(array_displayed, cmap_per[0]*100)
    vmax = np.nanpercentile(array_displayed, cmap_per[1]*100)
  
    if decimate:
        decimation_factor = 5

    sTime = stream[0].stats.starttime
    timeList = {}
    mplTimes = {}
    
    if isinstance(og_stream[0].data, np.ma.masked_array):
        og_stream = og_stream.split()      
    #og_stream.decimate(decimation_factor)
    #og_stream.detrend('spline', order=2, dspline=500)
    og_stream.merge()

    for tr in og_stream:
        key = tr.stats.component
        timeList[key] = []
        mplTimes[key] = []
        for t in np.ma.getdata(tr.times()[::decimation_factor]):
            newt = sTime + t
            timeList[key].append(newt)
            mplTimes[key].append(newt.matplotlib_date)
    
    # Ensure that the min and max times for all charts are the same
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
    #stream.spectrogram(samp_rate=sample_rate, axes=ax, per_lap=0.75, log=True, title=title, cmap='turbo', dbscale=dbscale, show_plot=False)
    
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
    
    ax['signalz'].plot(mplTimes['Z'], og_stream.select(component='Z')[0].data[::decimation_factor], color='k', linewidth=0.15)
    ax['signaln'].plot(mplTimes['N'], og_stream.select(component='N')[0].data[::decimation_factor], color='k', linewidth=0.15)
    ax['signale'].plot(mplTimes['E'], og_stream.select(component='E')[0].data[::decimation_factor], color='k', linewidth=0.15)

    # Get all components plotted on the same y
    zMax = np.nanmax(np.abs(og_stream.select(component='Z')[0].data))
    eMax = np.nanmax(np.abs(og_stream.select(component='E')[0].data))
    nMax = np.nanmax(np.abs(og_stream.select(component='E')[0].data))
    totMax = np.nanmax([zMax, eMax, nMax])
    
    perClip = 0.05

    yLimComps = [-totMax + (totMax * perClip), totMax - (totMax * perClip)]

    ax['signalz'].set_ylim(yLimComps)
    ax['signale'].set_ylim(yLimComps)
    ax['signaln'].set_ylim(yLimComps)
    
    ax['spec'].set_ylabel('Spectrogram: {}'.format(component))
    ax['signalz'].set_ylabel('Z')
    ax['signaln'].set_ylabel('N')
    ax['signale'].set_ylabel('E')
    
    #for comp in mplTimes.keys():
    #    stD = np.abs(np.nanstd(np.ma.getdata(og_stream.select(component=comp)[0].data)))
    #    dmed = np.nanmedian(np.ma.getdata(og_stream.select(component=comp)[0].data))
    #    key = 'signal'+comp.lower()
    #    ax[key].set_ylim([dmed-ylimstd*stD, dmed+ylimstd*stD])
    
    if hv_data is None:
        fig.suptitle('HVSR Site: Spectrogram and Data')
    elif 'title' in kwargs.keys():
        fig.suptitle(kwargs['title'])
    else:
        if 'input_params' in hv_data.keys():
            sitename = hv_data['input_params']['site']
        else:
            sitename = hv_data['site']
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
        
    if show_plot:
        fig.canvas.draw()
        plt.show()
    
    if return_fig:
        return fig
    
    return


# Plot input from stream using matplotlib
def _plot_simple_stream_mpl(hv_data, stream=None, input_fig=None, decimate=True, spectrogram_component='Z', show_plot=True, return_fig=False):
    """Helper function/alternative to plot_input_stream

    Parameters
    ----------
    hv_data : HVSRData
    stream : obspy.stream.Stream
        Can explictly specify stream instead of using hv_data object.
    input_fig : plotly.Figure
        Plotly figure to plot input stream on. If None, creates new one. Default is None.
    spectrogram_component : str, default='Z'
        Which component to use for the spectrogram
    show_plot : bool, default=True
        Whether to show plot or just generate it.
    return_fig : bool, default=False
        Whether to return figure

    Returns
    -------
    plotly figure
        Only returned if return_fig is True

    """
    if input_fig is None:
        preview_subp = subplots.make_subplots(rows=4, cols=1, shared_xaxes=True, horizontal_spacing=0.01, vertical_spacing=0.01, row_heights=[3,1,1,1])
        #input_fig = go.FigureWidget(preview_subp)
        input_fig = go.Figure(preview_subp)

    input_fig.data = []
    
    hvsr_data = hv_data
    if isinstance(hvsr_data, sprit_hvsr.HVSRBatch):
        hvsr_data=hvsr_data[0]

    if stream is not None:
        # This is only used for fetch_data, which ['stream'] has not yet been defined
        hvsr_data['stream'] = stream

    if isinstance(hvsr_data, (sprit_hvsr.HVSRData, dict)):
        stream_z = hvsr_data['stream'].select(component='Z').merge()
        stream_e = hvsr_data['stream'].select(component='E').merge()
        stream_n = hvsr_data['stream'].select(component='N').merge()
        hvsrBand = hvsr_data['hvsr_band']
        siteName = hvsr_data['site']
    else:
        # This is in case data is an obspy stream
        stream_z = hvsr_data.select(component='Z').merge()
        stream_e = hvsr_data.select(component='E').merge()
        stream_n = hvsr_data.select(component='N').merge()
        hvsrBand = [0.4, 40]
        siteName = 'HVSRSite'

    # Get iso_times and datetime.datetime
    utcdt = stream_z[0].times(type='utcdatetime')
    iso_times=[]
    dt_times = []
    for t in utcdt:
        if t is not np.ma.masked:
            iso_times.append(t.isoformat())
            dt_times.append(datetime.datetime.fromisoformat(t.isoformat()))
        else:
            iso_times.append(np.nan)
    iso_times=np.array(iso_times)
    dt_times = np.array (dt_times)

    # Generate spectrogram
    specKey=spectrogram_component.upper()
    specStreamDict = {'Z':stream_z[0],
                      'E':stream_e[0],
                      'N':stream_n[0]}
    f, t, Sxx = signal.spectrogram(x=specStreamDict[specKey].data, fs=specStreamDict[specKey].stats.sampling_rate, mode='magnitude')
    
    # Get times for the axis (one time per window)
    axisTimes = []
    for tpass in t:
        axisTimes.append((dt_times[0]+datetime.timedelta(seconds=tpass)).isoformat())

    # Add data to input_fig
    # Add spectrogram of Z component
    minz = np.percentile(Sxx, 1)
    maxz = np.percentile(Sxx, 99)
    hmap = go.Heatmap(z=Sxx,
                x=axisTimes,
                y=f,
                colorscale='Turbo',
                showlegend=False,
                hovertemplate='Time [UTC]: %{x}<br>Frequency [Hz]: %{y:.2f}<br>Spectrogram Magnitude: %{z:.2f}<extra></extra>',
                zmin=minz, zmax=maxz, showscale=False, name=f'{specKey} Component Spectrogram')
    input_fig.add_trace(hmap, row=1, col=1)
    input_fig.update_yaxes(type='log', range=[np.log10(hvsrBand[0]), np.log10(hvsrBand[1])], row=1, col=1)
    input_fig.update_yaxes(title={'text':f'Spectrogram ({specKey})'}, row=1, col=1)

    # Add raw traces
    dec_factor = 1
    if decimate:
        dec_factor = 5 #This just makes the plotting go faster, by "decimating" the data
    input_fig.add_trace(go.Scatter(x=iso_times[::dec_factor], y=stream_z[0].data[::dec_factor],
                                    line={'color':'black', 'width':0.5},marker=None, name='Z component data'), row=2, col='all')
    input_fig.update_yaxes(title={'text':'Z'}, row=2, col=1)
    input_fig.add_trace(go.Scatter(x=iso_times[::dec_factor], y=stream_e[0].data[::dec_factor],
                                    line={'color':'blue', 'width':0.5},marker=None, name='E component data'),row=3, col='all')
    input_fig.update_yaxes(title={'text':'E'}, row=3, col=1)
    input_fig.add_trace(go.Scatter(x=iso_times[::dec_factor], y=stream_n[0].data[::dec_factor],
                                    line={'color':'red', 'width':0.5},marker=None, name='N component data'), row=4, col='all')
    input_fig.update_yaxes(title={'text':'N'}, row=4, col=1)
    
    #input_fig.add_trace(p)
    input_fig.update_layout(margin={"l":10, "r":10, "t":30, 'b':0}, showlegend=False,
                                title=f"{siteName} Data Preview")

    if show_plot:
        input_fig.show()

    if return_fig:
        return input_fig


# Helper function for plotting outlier curves using the express module of plotly
def __plotly_outlier_curves_px(hvsr_data, **input_args):
    """Support function for using plotly express to make outlier curves chart. Intended for use with streamlit API

    Returns
    -------
    plotly.express figure
    """
    #input_args: hvsr_data, plot_engine='plotly', plotly_module='go', outlier_threshold=0.98, use_percentile=True, use_hv_curves=False, from_roc=False, show_plot=True, verbose=False
    hvData = input_args['hvsr_data']
    x_data = hvsr_data['x_freqs']
   
    
    if input_args['use_hv_curves']:
        no_subplots = 1
        outlierFig = subplots.make_subplots(rows=no_subplots, cols=1,
                                            shared_xaxes=True, horizontal_spacing=0.01,
                                            vertical_spacing=0.1)
        scatterFig = px.scatter()
        scatter_traces = []
        line_traces = []
        for row, hv_data in enumerate(hvsr_data.hvsr_windows_df['HV_Curves']):
            scatterArray = np.array(list(hv_data)[::10])
            x_data_Scatter = np.array(list(x_data)[::10])
            scatter_traces.append(px.scatter(x=x_data_Scatter, y=scatterArray))
            line_traces.append(px.line(x=x_data, y=hv_data))


        for tr in scatter_traces:
            for trace in tr.data:
                outlierFig.add_traces(trace, rows=1, cols=1)
                
        for tr in line_traces:
            for trace in tr.data:
                outlierFig.add_traces(trace, rows=1, cols=1)
                #pass

        outlierFig.update_xaxes(title='Frequency [Hz]', type="log", row=1, col=1)
        outlierFig.update_yaxes(title='H/V Ratio', row=1, col=1)
    
    else:
        subplots = 3
    
    return outlierFig


# Helper function for plotting the input data stream (preview chart) using plotly
def __plotly_express_preview(hvDataIN):
    """
    Create a multi-plot visualization of seismic data using Plotly Express.
    
    Parameters:
    -----------
    hvDataIN : dict
        Dictionary containing seismic stream data
    times : numpy.ndarray
        Time values for x-axis
    
    Returns:
    --------
    plotly.graph_objs.Figure
        Configured figure with spectrogram and line plots
    """
    # Extract data for different components
    z_data = hvDataIN['stream'].select(component='Z')[0].data
    e_data = hvDataIN['stream'].select(component='E')[0].data
    n_data = hvDataIN['stream'].select(component='N')[0].data
    
    times = hvDataIN.stream[0].times()

    # Create DataFrame for plotting
    df_z = pd.DataFrame({
        'Time': times,
        'Amplitude': z_data,
        'Color': 'black'
    })
    
    df_e = pd.DataFrame({
        'Time': times,
        'Amplitude': e_data,
        'Color': 'blue'
    })
    
    df_n = pd.DataFrame({
        'Time': times,
        'Amplitude': n_data,
        'Color': ['r']*n_data.shape[0]
    })
    
    # Combine DataFrames
    df_combined = pd.concat([df_z, df_e, df_n])
    
    cdm = {'r':'red', 'black':'black', 'blue':'blue'}
    # Create line plot
    figZ = px.line(
        df_z, 
        x='Time', 
        y='Amplitude', 
        color='Color',
        title='Z Component Data',
        color_discrete_map=cdm
    )
    
    # Create line plot
    figE = px.line(
        df_e, 
        x='Time', 
        y='Amplitude', 
        color='Color',
        title='E Component Data',
        color_discrete_map=cdm
    )

    # Create line plot
    figN= px.line(
        df_n, 
        x='Time', 
        y='Amplitude', 
        color='Color',
        title='N Component Data',
        color_discrete_map=cdm
    )

    # Generate spectrogram using scipy (more accurate and efficient)
    f, t, Sxx = signal.spectrogram(z_data, fs=100, nperseg=1000, noverlap=0.5, mode='magnitude')
    
    # Create spectrogram figure directly from NumPy arrays
    fig_spectrogram = px.imshow(
        Sxx,  # Use the spectrogram magnitude directly
        labels=dict(x='Time', y='Frequency', color='Magnitude'),
        title='Spectrogram',
        color_continuous_scale='Viridis',
        aspect='auto',
        origin='lower',
        zmin=np.percentile(Sxx, 2), zmax=np.percentile(Sxx, 98)
    )
    
    # Modify spectrogram y-axis to be logarithmic
    fig_spectrogram.update_yaxes(type='log')
    

    return fig_spectrogram, (figZ, figE, figN)

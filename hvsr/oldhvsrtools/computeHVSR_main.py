import datetime
import sys
import os
import math
import time
import urllib
import xml.etree.ElementTree as ET


import matplotlib
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText
import obspy

import hvsr.oldhvsrtools.fileLib as fileLib
import hvsr.oldhvsrtools.msgLib as msgLib
import hvsr.oldhvsrtools.hvsrCalcs as hvsrCalcs
import hvsr.oldhvsrtools.ioput as ioput
import hvsr.oldhvsrtools.powspecdens as powspecdens
import hvsr.oldhvsrtools.readhvsr as readhvsr
import hvsr.oldhvsrtools.setParams as setParams
import hvsr.oldhvsrtools.utilities as utilities

#args=setParams.args #From original, not needed anyore

def __sortchannels(channels=['EHZ', 'EHN', 'EHE']):
    """"
    Sort channels. Z/vertical should be first, horizontal order doesn't matter, but N 2nd and E 3rd is default
        ----------------
        Parameters
            channels    : list = ['EHZ', 'EHN', 'EHE']
    """
    channel_order = {'Z': 0, '1': 1, 'N': 1, '2': 2, 'E': 2}

    sorted_channel_list = channels.copy()
    for channel in channels:
        sorted_channel_list[channel_order[channel[2]]] = channel
    return sorted_channel_list

def __formatTime(inputDT, tzone='utc', dst=True):
    if type(inputDT) is str:
        #tzone = 'America/Chicago'
        #Format string to datetime obj
        if "/" in inputDT:
            div = '/'
        elif '-' in inputDT:
            div = '/'

        if ':' in inputDT:
            hasTime = True
        else:
            hasTime = False

        if len(inputDT.split(div)[0])>2:
            year = inputDT.split(div)[0]
            month = inputDT.split(div)[1]
            day = inputDT.split(div)[2]
        elif len(inputDT.split(div)[2])>2:
            if int(inputDT.split(div)[0])>12:
                #dateStr = '%d'+div+'%m'+div+'%Y'   
                year = inputDT.split(div)[2]
                month = inputDT.split(div)[1]
                day = inputDT.split(div)[0]                             
            else:
                year = inputDT.split(div)[2]
                month = inputDT.split(div)[0]
                day = inputDT.split(div)[1]     
                #dateStr = '%m'+div+'%d'+div+'%Y'
        elif int(inputDT.split(div)[0])>31:
            #dateStr = '%y'+div+'%m'+div+'%d'
            year = inputDT.split(div)[0]
            if year < datetime.datetime.today().year:
                year = '20'+year
            else:
                year = '19'+year
            month = inputDT.split(div)[1]
            day = inputDT.split(div)[2]            
        elif int(inputDT.split(div)[2])>31:
            if int(inputDT.split(div)[0])>12:
                #dateStr = '%d'+div+'%m'+div+'%y'       
                year = inputDT.split(div)[2]
                if year < datetime.datetime.today().year:
                    year = '20'+year
                else:
                    year = '19'+year
                month = inputDT.split(div)[1]
                day = inputDT.split(div)[0]                           
            else:
                #dateStr = '%m'+div+'%d'+div+'%y'
                year = inputDT.split(div)[2]
                if year < datetime.datetime.today().year:
                    year = '20'+year
                else:
                    year = '19'+year
                month = inputDT.split(div)[0]
                day = inputDT.split(div)[1]                  

        hour=0
        minute=0
        sec=0
        microS=0
        if hasTime:
            timeStr = inputDT.split(div)[2]
            if 'T' in timeStr:
                timeStr=timeStr.split('T')[1]
            elif ' ' in timeStr:
                timeStr=timeStr.split(' ')[1]

            timeStrList = timeStr.split(':')
            if len(timeStrList[0])>2:
                timeStrList[0] = timeStrList[0][-2:]
            elif int(timeStrList[0]) > 23:
                timeStrList[0] = timeStrList[0][-1:]
            
            if '.' in timeStrList[2]:
                microS = int(timeStrList[2].split('.')[1])
                timeStrList[2] = timeStrList[2].split('.')[0]

            hour = int(timeStrList[0])
            minute=int(timeStrList[1])
            sec = int(timeStrList[2])


        outputTimeObj = datetime.datetime(year=year,month=month, day=day,
                                hour=hour, minute=minute, second=sec, microsecond=microS)

    elif type(inputDT) is datetime.datetime:
        outputTimeObj = inputDT

    if tzone is int: #Plus/minus needs to be correct there
        #pass ##FINISH WITH UTC offset
        outputTimeObj = outputTimeObj+datetime.timedelta(hours=tzone)
    elif type(tzone) is str:
        if tzone != 'utc':
            utc_time = datetime.datetime.utcnow()
            localTime = datetime.datetime.now()
            utcOffset = utc_time-localTime
            outputTimeObj=outputTimeObj+utcOffset
            utcOffset = utc_time-localTime
            outputTimeObj = outputTimeObj+utcOffset
        if dst:
            outputTimeObj = outputTimeObj-datetime.timedelta(hours=1)
    return outputTimeObj

def __checkifnone(param):
    if param is None:
        msgLib.error('{} not defined!'.format(param), 1)
        sys.exit() 
    return

#This may not be needed, but uses baseline to remove outlier data
def  __removeoutliers(network, station, location, channel, verbose, psd_values):
    try:
        baselineFile = open(
            os.path.join(setParams.baselineDirectory, fileLib.baselineFileName(network, station, location, channel)),
            'r')
    except Exception as e:
        msgLib.error('Failed to read baseline file {}\n'
                    'Use the getStationChannelBaseline.py script to generate the baseline file or '
                    'set the parameter removeoutliers=0.'.
                    format(os.path.join(setParams.baselineDirectory, fileLib.baselineFileName(network,
                                                                                        station,
                                                                                        location,
                                                                                        channel))), 1)
        sys.exit()
    x_values = list()
    pct_low = list()
    pct_high = list()
    pct_mid = list()

    lines = baselineFile.read()
    baseline = lines.split('\n')
    for index_value in range(0, len(baseline)):
        if len(baseline[index_value].strip()) == 0:
            continue
        if baseline[index_value].strip().startswith('#'):
            values = baseline[index_value].strip().split()
            percent_low = values[1]
            percent_mid = values[3]
            percent_high = values[5]
            continue

        values = baseline[index_value].split()

        x_values.append(float(values[0]))
        pct_low.append(float(values[1]))
        pct_mid.append(float(values[2]))
        pct_high.append(float(values[3]))
    baselineFile.close()

    if verbose:
        msgLib.info('CLEAN UP ' + str(len(psd_values)) + ' PSDs')
    (ok, notok) = utilities.check_y_range(psd_values, pct_low, pct_high)

    return ok, notok

# Get daily PSDs from MUSTANG
#This probably won't be used
def __getmustangpsds(time_list, verbose, start_hour, end_hour, target, start_time, end_time, plot):
    day_values = list()
    day_time_values = list()
    psd_values = list()

    # Limit PSD segments starting between starttime (inclusive) and endtime (exclusive)
    pdf_x = list()
    pdf_y = list()
    pdfP = list()
    for date_index in range(len(time_list) - 1):
        msgLib.info('Doing {}{} to {}{}'.format(time_list[date_index], start_hour, time_list[date_index + 1], end_hour))
        URL = '{}target={}&starttime={}{}&endtime={}{}&format=xml&correct=true'.format(setParams.mustangPsdUrl, target,
                                                                                    time_list[date_index],
                                                                                    start_hour,
                                                                                    time_list[date_index + 1],
                                                                                    end_hour)
        if verbose >= 0:
            msgLib.info('requesting: {}'.format(URL))
            t0 = utilities.time_it(t0)
        try:
            link = urllib.request.urlopen(URL)
        except Exception as _e:
            msgLib.error('\n\nReceived HTTP Error code: {}\n{}'.format(_e.code, _e.reason), 1)
            if _e.code == 404:
                msgLib.error('Error 404: No PSDs found in the range {}{} to {}{} when requested:\n\n{}'.format(
                    time_list[date_index], start_hour, time_list[date_index + 1], end_hour, URL), 1)
                continue
            elif _e.code == 413:
                print('Note: Either use the run argument "n" to split the requested date range to smaller intervals'
                    '\nCurrent "n"" value is: {}. Or request a shorter time interval.'.format(n), flush=True)
                sys.exit(1)
            msgLib.error('failed on target {} {}'.format(target, URL), 1)

        if verbose:
            msgLib.info('PSD waiting for reply....')

        tree = ET.parse(link)
        link.close()
        root = tree.getroot()

        if verbose:
            requestStart = root.find('RequestedDateRange').find('Start').text
            requestEnd = root.find('RequestedDateRange').find('End').text

        psds = root.find('Psds')

        all_psds = psds.findall('Psd')
        if verbose:
            msgLib.info('PSD: {}'.format(str(len(all_psds))))
            t0 = utilities.time_it(t0)

        for psd in all_psds:
            day = psd.attrib['start'].split('T')[0]
            psdTime = time.strptime(day, '%Y-%m-%d')
            if (start_time != end_time and (psdTime < start_time or psdTime >= end_time)) or \
                    (start_time == end_time and psdTime != start_time):
                if verbose >= 0:
                    msgLib.warning(sys.argv[0], 'Rejected, PSD of {} is outside the  window {} to {}'.
                                format(psd.attrib['start'],
                                        time.strftime('%Y-%m-%dT%H:%M:%S', start_time),
                                        time.strftime('%Y-%m-%dT%H:%M:%S', end_time)))
                continue
            allValues = psd.findall('value')

            X = list()
            Y = list()
            for value in allValues:
                X.append(float(value.attrib['freq']))
                Y.append(float(value.attrib['power']))

            # We follow a simple logic, the X values must match. We take the first one to be the sequence we want.
            if not x_values:
                x_values = list(X)
            if X != x_values:
                if verbose:
                    msgLib.warning(sys.argv[0], 'Rejected {} {} {} for bad X'.format(target, time_list[date_index],
                                                                                    time_list[date_index + 1]))
            else:
                # Store the PSD values and at the same time keep track of their day and time.
                day_values.append(day)
                day_time_values.append(psd.attrib['start'])
                psd_values.append(Y)
        plot_pdf = plot[3]
        if plot_pdf:
            (thisX, thisY, thisP) = hvsrCalcs.get_pdf('{}target={}&starttime={}{}&endtime={}{}&format=text'.format(
                setParams.mustangPdfUrl, target, time_list[date_index], start_hour, time_list[date_index + 1],
                end_hour), verbose)
            pdf_x += thisX
            pdf_y += thisY
            pdfP += thisP
            if verbose:
                msgLib.info('PDF: {}'.format(len(pdf_y)))

        # Must have PSDs.
        if not psd_values:
            msgLib.error('no PSDs found to process between {} and {}'.format(
                time_list[date_index], time_list[date_index + 1]), 1)
            sys.exit()
        else:
            if verbose >= 0:
                msgLib.info('total PSDs:' + str(len(psd_values)))
                t0 = utilities.time_it(t0)

    return day_values, day_time_values, psd_values, pdf_x, pdf_y, pdfP

#Set up PSD Plot
def __setupPSDPlot(channel_index, plot, verbose, label, plotRows):
    show_plot=plot[0]
    
    # PSDs:
    # Initial settings: Set up plot with first channel pass
    if channel_index == 0:
        if show_plot:
            if verbose >= 0:
                msgLib.info('PLOT PSD')

            fig = plt.figure(figsize=setParams.imageSize, facecolor='white')
            ax = list()
            fig.canvas.set_window_title(label)
            ax.append(plt.subplot(plotRows, 1, channel_index + 1))

    else:
        #If we are plotting, just add channels
        if show_plot:
            ax.append(plt.subplot(plotRows, 1, channel_index + 1, sharex=ax[0]))
    return fig, ax

#Function to plotPSDS
def plotPSDs(fig, ax, plot, channel_index, network, station, location, channel,
            ok, notok, verbose, x_values, psd_values, remove_outliers, pqlx, pdf_x, pdf_y, pdfP, xtype,
            pct_high, pct_mid, pct_low, percent_high, percent_mid, percent_low):
    show_plot = plot[0]
    plot_nnm = plot[1]
    plot_psd = plot[2]
    plot_pdf = plot[3]
    plot_bad = plot[4]
    if show_plot:
            from obspy.imaging.cm import pqlx
            from obspy.signal.spectral_estimation import get_nlnm, get_nhnm
            # Plot the 'bad' PSDs in gray.
            if plot_psd and plot_bad:
                msgLib.info('[INFO] Plot {} BAD PSDs'.format(len(notok)))
                for i, index in enumerate(notok):
                    if i == 0:
                        plt.semilogx(np.array(x_values), psd_values[index], c='gray', label='Rejected')
                    else:
                        plt.semilogx(np.array(x_values), psd_values[index], c='gray')
                if verbose >= 0:
                    t0 = utilities.time_it(t0)

            if plot_psd:
                # Plot the 'good' PSDs in green.
                if verbose:
                    msgLib.info('[INFO] Plot {} GOOD PSDs'.format(len(ok)))
                for i, index in enumerate(ok):
                    if i == 0:
                        plt.semilogx(np.array(x_values), psd_values[index], c='green', label='PSD')
                    else:
                        plt.semilogx(np.array(x_values), psd_values[index], c='green')
                if verbose >= 0:
                    t0 = utilities.time_it(t0)
            if plot_pdf:
                cmap = pqlx

                ok = list()
                im = plt.scatter(pdf_x, pdf_y, c=pdfP, s=46.5, marker='_', linewidth=setParams.lw, edgecolor='face', cmap=cmap,
                                alpha=setParams.alpha)
                ax[channel_index].set_xscale('log')

            if verbose:
                msgLib.info('Tune plots.')
            if verbose >= 0:
                t0 = utilities.time_it(t0)
            if remove_outliers:
                plt.semilogx(np.array(x_values), pct_high, c='yellow', label='{}%'.format(percent_high))
                plt.semilogx(np.array(x_values), pct_mid, c='red', label='{}%'.format(percent_mid))
                plt.semilogx(np.array(x_values), pct_low, c='orange', label='{}%'.format(percent_low))
            plt.semilogx((setParams.hvsrXlim[0], setParams.hvsrXlim[0]), setParams.yLim, c='black')
            plt.semilogx((setParams.hvsrXlim[1], setParams.hvsrXlim[1]), setParams.yLim, c='black')
            p1 = plt.axvspan(setParams.xLim[xtype][0], setParams.hvsrXlim[0], facecolor='#909090', alpha=0.5)
            p2 = plt.axvspan(setParams.hvsrXlim[1], setParams.xLim[xtype][1], facecolor='#909090', alpha=0.5)
            # plt.title(' '.join([target,start,'to',end]))
            plt.ylim(setParams.yLim)
            plt.xlim(setParams.xLim[xtype])
            plt.ylabel(setParams.yLabel)

            if len(ok) <= 0:
                anchored_text = AnchoredText(
                    ' '.join(['.'.join([network, station, location, channel]), '{:,d}'.format(len(psd_values)), 'PSDs']),
                    loc=2)
            else:
                anchored_text = AnchoredText(' '.join(
                    ['.'.join([network, station, location, channel]), '{:,d}'.format(len(ok)), 'out of',
                    '{:,d}'.format(len(psd_values)), 'PSDs']), loc=2)
            ax[channel_index].add_artist(anchored_text)

            if plot_nnm:
                nlnm_x, nlnm_y = get_nlnm()
                nhnm_x, nhnm_y = get_nhnm()
                if xtype != 'period':
                    nlnm_x = 1.0 / nlnm_x
                    nhnm_x = 1.0 / nhnm_x
                plt.plot(nlnm_x, nlnm_y, lw=2, ls='--', c='k', label='NLNM, NHNM')
                plt.plot(nhnm_x, nhnm_y, lw=2, ls='--', c='k')

            plt.legend(prop={'size': 6}, loc='lower left')

            # Create a second axes for the colorbar.
            if plot_pdf and ax2 is None:
                ax2 = fig.add_axes([0.92, 0.4, 0.01, 0.4])
                cbar = fig.colorbar(im, ax2, orientation='vertical')
                cbar.set_label('Probability (%)', size=9, rotation=270, labelpad=6)
                plt.clim(setParams.pMin, setParams.pMax)
    return

def hvsr_setup(start, end, tzone='utc', dst=True,
                network='AM', station='RAC84', location='00', channels=['EHZ', 'EHN', 'EHE'], 
                nSegments=256, method=4, minrank=2, water_level=1.8, outlier_rem=True, verbose=False,
                plot=True, xtype='frequency', hvsrband=[0.2, 15], hvsr_ymax = 10,
                **kwargs):
    """ Main function to setup data for HVSR calculation
    -------------------
    Parameters:
        start       : str or datetime obj. If string, preferred format is YYYY-mm-ddTHH:MM:SS.f (Y=year, m=month, d=day, ). Will be converted to UTC
        end         : str or datetime obj
        tzone       : str='utc', or int  If str, 'utc' is easiest, otherwise, will use local timezone of processing computer; if int, offset from UTC in hours
        dst         : bool=True     True if daylight savings time when data was collected (usualyl True in summers           network     : str='AM'
        station     : str='RAC84'
        location    : str='00'
        channels    : list=['EHZ', 'EHN', 'EHE']     
        nSegments   : int=256       Number of segments to break the signal into
        method      : int or str. Method for combining the horizontal components. If integer, the following 
        minrank     : float=2 (or int?)
        water_level : float=1.8
        outlier_rem : bool = True        
        verbose     : bool = False
        plot        : bool, list, or dict
                        If bool, just says whether or not to plot
                        If list, should be list of bools saying whether to plot (in the following order):
                            [0] : Whether to plot anything
                            [1] : Whether to plot nnm
                            [2] : Whether to plot Power Spectral Densities
                            [3] : Whether to plot Probability density functions for each freq. bin (?)
                            [4] : Whether to plot bad points (?)
        xtype       : str {'frequency', 'period'} ('freq', 'f', 'Hz', will also work for frequency; 'per', 'p', or 'T' will also work for period)
        hvsrband    : tuple or 2-item list (?)
        hvsr_ymax   : float = 10
        report      : bool=True Whether to print report information to file
        **kwargs    : Keyword arguments, primarily to be passed as matplotlib plotting parameters
    """
    t0 = time.time()
    display = True
    plotRows = 4
    report_information = int(utilities.get_param(args, 'report_information', msgLib, 1, be_verbose=verbose))

    # See if we want to reject suspect PSDs.
    remove_outliers = outlier_rem #from original: bool(int(utilities.get_param(args, 'removeoutliers', msgLib, False)))
    if verbose:
        msgLib.info('remove_outliers: {}'.format(remove_outliers))

    # Minimum SESAME 2004 rank to be accepted.
    min_rank = minrank #from original: float(utilities.get_param(args, 'minrank', msgLib, setParams.minrank))

    # network, station, and location to process.
    #From original: network = utilities.get_param(args, 'net', msgLib, None)
    __checkifnone(param=start)
    __checkifnone(param=end)
    __checkifnone(param=location)
    __checkifnone(param=network)
    __checkifnone(param=station)
    __checkifnone(param=location)

    #Reformat start and end of time window
    startTimeObj = __formatTime(inputTime=start, tzone=tzone, dst=dst)
    start_hour = startTimeObj.hour
    start_time = startTimeObj.time

    endTimeObj = __formatTime(inputTime=end, tzone=tzone, dst=dst)
    end_hour = endTimeObj.hour
    end_time = endTimeObj.time

    n = nSegments
    
    #PROBABLY DON"T NEED THIS (ONLY FOR MUSTANG CALL)
    time_list = utilities.time_range(start, end, n)

    # Method for combining horizontal components h1 & h2.
    method = setParams.getHComboMethod(method) 
    if method == 'Diffuse Field Assumption':
        dfa=True
    else:
        dfa=False

    plotParams = setParams.plotparameters(plot) #returns a dictionary with keys below
    show_plot = plotParams[0] #from original: int(utilities.get_param(args, 'showplot', msgLib, setParams.plot))
    plot_nnm = plotParams[1] #from original: int(utilities.get_param(args, 'plotnnm', msgLib, setParams.plotnnm))
    plot_psd = plotParams[2] #from original: int(utilities.get_param(args, 'plotpsd', msgLib, setParams.plotpsd))
    plot_pdf = plotParams[3] #from original: int(utilities.get_param(args, 'plotpdf', msgLib, setParams.plotpdf))
    plot_bad = plotParams[4] #from original: int(utilities.get_param(args, 'plotbad', msgLib, setParams.plotbad))

    day_values_passed = [[], [], []]
    #From original: water_level = float(utilities.get_param(args, 'waterlevel', msgLib, setParams.waterlevel))
    #hvsr_ylim = setParams.hvsrylim
    hvsr_ylim = [0, 10]
    hvsr_ylim[1] = hvsr_ymax #from originalfloat(utilities.get_param(args, 'ymax', msgLib, setParams.hvsrylim[1]))
    #From original: xtype = utilities.get_param(args, 'xtype', msgLib, setParams.xtype)
    #From original: hvsr_band = utilities.get_param(args, 'hvsrband', msgLib, setParams.hvsrband)

    sorted_channel_list = __sortchannels(channels)

    #Get and format header information and plot title info
    report_header = '.'.join([network, station, location, '-'.join(sorted_channel_list)])
    station_header = report_header
    station_header = '{} {} {}'.format(station_header, start, end)
    report_header += ' {} from {} to {}\nusing {}'.format(report_header, start, end, setParams.methodList[method])
    plot_title = report_header
    report_header = '{}\n\n'.format(report_header)

    #Plotting stuff!
    # Turn off the display requirement if not needed.
    if not show_plot:
        if verbose >= 0:
            msgLib.info('Plot Off')
        matplotlib.use('agg')
    else:
        from obspy.imaging.cm import pqlx
        from obspy.signal.spectral_estimation import get_nlnm, get_nhnm

    ax2 = None
    # Do one channel at a time.
    channel_index = -1
    for channel in sorted_channel_list:
        channel_index += 1
        x_values = list()
        psd_values = list()
        day_values = list()
        day_time_values = list()
        pct_low = list()
        pct_high = list()
        pct_mid = list()

        target = '.'.join([network, station, location, channel, '*'])
        label = '.'.join([network, station, location, 'PSDs'])
        label_hvsr = '.'.join([network, station, location, 'HVSR'])
        if verbose >= 0:
            msgLib.info('requesting {} from {} to {}'.format(target, start, end))

        # Baseline files are required if we will remove the outliers. We assume the baseline file has all the periods,
        # so we use it as a reference.

        day_values, day_time_values, psd_values, pdf_x, pdf_y, pdfP = __getmustangpsds(time_list, verbose, start_hour, end_hour, target, start_time, end_time, plot)

        if remove_outliers:
            ok, notok = __removeoutliers(network, station, location, channel, verbose, psd_values)
        else:
            # No cleanup needed, mark them all as OK!
            notok = list()
            ok = range(len(psd_values))

        fig, ax = __setupPSDPlot(channel_index, plot, verbose, label, plotRows)

        # [chanZ[day],chan1[day],chan2[day]]
        daily_psd = [{}, {}, {}]
        day_time_psd = [{}, {}, {}]
        median_daily_psd = [{}, {}, {}]
        equal_daily_energy = [{}, {}, {}]
        

        info = ' '.join(
            ['Channel', channel, str(len(psd_values)), 'PSDs,', str(len(ok)), 'accepted and', str(len(notok)), 'rejected',
            '\n'])
        report_header += info
        print ('[INFO]', info)

        if verbose and notok:
            t0 = utilities.time_it(t0)
            msgLib.info('Flag BAD PSDs')
        for i, index in enumerate(ok):
            # DAY,DAYTIME: 2018-01-01 2018-01-01T00:00:00.000Z
            day = day_values[index]
            day_time = day_time_values[index]
            psd = psd_values[index]

            # Preserve the individual PSDs (day_time)
            day_time_psd[channel_index][day_time] = psd

            # Group PSDs into daily bins
            if day not in daily_psd[channel_index].keys():
                daily_psd[channel_index][day] = list()
            daily_psd[channel_index][day].append(psd)

            # Keep track of individual days
            if day_values[index] not in day_values_passed[channel_index]:
                day_values_passed[channel_index].append(day)
        if verbose and notok:
            t0 = utilities.time_it(t0)

        #Plot PSDs, if plot is True
        plotPSDs(fig, ax, plot, channel_index, network, station, location, channel,
            ok, notok, verbose, x_values, psd_values, remove_outliers, pqlx, xtype)
            #pdf_x, pdf_y, pdfP, pct_high, pct_mid, pct_low, percent_high, percent_mid, percent_low)

        # Compute and save the median daily PSD for HVSR computation
        # for non-DFA computation.
        # daily_psd[channel_index][day] is a list of individual PSDs for that channel and day. We compute median
        # along axis=0 to get median of individual frequencies.

        if not dfa:
            if verbose:
                msgLib.info('Save Median Daily')
            for day in (day_values_passed[channel_index]):
                if display:
                    print('[INFO] calculating median_daily_psd', flush=True)
                    display = False
                median_daily_psd[channel_index][day] = np.percentile(daily_psd[channel_index][day], 50, axis=0)
    return 

def dfa_calc(method, day_time_values, day_time_psd, x_values, equal_daily_energy, median_daily_psd, verbose):
    # Are we doing DFA?
    # Use equal energy for daily PSDs to give small 'events' a chance to contribute
    # the same as large ones, so that P1+P2+P3=1

    if method == 'Diffuse Field Assumption':
        if display:
            print('[INFO] DFA', flush=True)
            display = False
        sum_ns_power = list()
        sum_ew_power = list()
        sum_z_power = list()
        daily_psd = [{}, {}, {}]
        day_values = list()

        # Make sure we have all 3 components for every time sample
        for day_time in day_time_values:
            if day_time not in (day_time_psd[0].keys()) or day_time not in (day_time_psd[1].keys()) or day_time not in (
            day_time_psd[2].keys()):
                continue
            day = day_time.split('T')[0]
            if day not in day_values:
                day_values.append(day)

            # Initialize the daily PSDs.
            if day not in daily_psd[0].keys():
                daily_psd[0][day] = list()
                daily_psd[1][day] = list()
                daily_psd[2][day] = list()

            daily_psd[0][day].append(day_time_psd[0][day_time])
            daily_psd[1][day].append(day_time_psd[1][day_time])
            daily_psd[2][day].append(day_time_psd[2][day_time])

        # For each day equalize energy
        for day in day_values:

            # Each PSD for the day
            for i in range(len(daily_psd[0][day])):
                Pz = list()
                P1 = list()
                P2 = list()
                sum_pz = 0
                sum_p1 = 0
                sum_p2 = 0

                # Each sample of the PSD , convert to power
                for j in range(len(x_values) - 1):
                    pz = hvsrCalcs.get_power([daily_psd[0][day][i][j], daily_psd[0][day][i][j + 1]], [x_values[j], x_values[j + 1]])
                    Pz.append(pz)
                    sum_pz += pz
                    p1 = hvsrCalcs.get_power([daily_psd[1][day][i][j], daily_psd[1][day][i][j + 1]], [x_values[j], x_values[j + 1]])
                    P1.append(p1)
                    sum_p1 += p1
                    p2 = hvsrCalcs.get_power([daily_psd[2][day][i][j], daily_psd[2][day][i][j + 1]], [x_values[j], x_values[j + 1]])
                    P2.append(p2)
                    sum_p2 += p2

                sum_power = sum_pz + sum_p1 + sum_p2  # total power

                # Mormalized power
                for j in range(len(x_values) - 1):
                    # Initialize if this is the first sample of the day
                    if i == 0:
                        sum_z_power.append(Pz[j] / sum_power)
                        sum_ns_power.append(P1[j] / sum_power)
                        sum_ew_power.append(P2[j] / sum_power)
                    else:
                        sum_z_power[j] += (Pz[j] / sum_power)
                        sum_ns_power[j] += (P1[j] / sum_power)
                        sum_ew_power[j] += (P2[j] / sum_power)
            # Average the normalized daily power
            for j in range(len(x_values) - 1):
                sum_z_power[j] /= len(daily_psd[0][day])
                sum_ns_power[j] /= len(daily_psd[0][day])
                sum_ew_power[j] /= len(daily_psd[0][day])

            equal_daily_energy[0][day] = sum_z_power
            equal_daily_energy[1][day] = sum_ns_power
            equal_daily_energy[2][day] = sum_ew_power

    return 

def hvsr_compute(network, station, location, start, end, method, 
                x_values, plot, water_level, hvsr_band, hvsr_ylim,
                median_daily_psd, equal_daily_energy, verbose):
    
    show_plot = plot[0]
    plot_nnm = plot[1]
    plot_psd = plot[2]
    plot_pdf = plot[3]
    plot_bad = plot[4]
    
    # HVSR computation
    if verbose:
        msgLib.info('HVSR computation')
    if verbose >= 0:
        t0 = utilities.time_it(t0)

    # Find the unique days between all channels
    d = day_values_passed[0]
    for i in range(1, len(day_values_passed)):
        d += day_values_passed[i]
    day_values_passed = set(d)  # unique days

    hvsr = list()
    peak_water_level = list()
    hvsrp = list()
    peak_water_level_p = list()
    hvsrp2 = list()
    hvsrm = list()
    water_level_m = list()
    peak_water_level_m = list()
    hvsr_m2 = list()
    hvsr_std = list()
    hvsr_log_std = list()

    path = ''.join(['M', str(method)])
    fileLib.mkdir(setParams.hvsrDirectory, path)
    out_file_name = os.path.join(setParams.hvsrDirectory, path, fileLib.hvsrFileName(network, station, location, start, end))

    outFile = open(out_file_name, 'w')
    msgLib.info(f'Output file: {out_file_name}')
    count = -1

    # compute one x-value (period or frequency) at a time to also compute standard deviation
    outFile.write('frequency HVSR HVSR+1STD HVSR-1STD\n')
    for j in range(len(x_values) - 1):
        missing = 0
        hvsr_tmp = list()

        for day in sorted(day_values_passed):

            # must have all 3 channels, compute HVSR for that day
            if method == 'Diffuse Field Assumption':
                if day in equal_daily_energy[0].keys() and day in equal_daily_energy[1].keys() and day in \
                        equal_daily_energy[2].keys():
                    hvsr0 = math.sqrt(
                        (equal_daily_energy[1][day][j] + equal_daily_energy[2][day][j]) / equal_daily_energy[0][day][j])
                    hvsr_tmp.append(hvsr0)
                else:
                    if verbose > 0:
                        msgLib.warning(sys.argv[0], day + ' missing component, skipped!')
                    missing += 1
                    continue
            else:
                if day in median_daily_psd[0].keys() and day in median_daily_psd[1].keys() and day in \
                        median_daily_psd[2].keys():
                    psd0 = [median_daily_psd[0][day][j], median_daily_psd[0][day][j + 1]]
                    psd1 = [median_daily_psd[1][day][j], median_daily_psd[1][day][j + 1]]
                    psd2 = [median_daily_psd[2][day][j], median_daily_psd[2][day][j + 1]]
                    hvsr0 = hvsrCalcs.get_hvsr(psd0, psd1, psd2, [x_values[j], x_values[j + 1]], use_method=method)
                    hvsr_tmp.append(hvsr0)
                else:
                    if verbose > 0:
                        msgLib.warning(sys.argv[0], day + ' missing component, skipped!')
                    missing += 1
                    continue
        count += 1
        peak_water_level.append(water_level)
        if len(hvsr_tmp) > 0:
            hvsr.append(np.mean(hvsr_tmp))
            hvsr_std.append(np.std(hvsr_tmp))
            hvsr_log_std.append(np.std(np.log10(hvsr_tmp)))
            hvsrp.append(hvsr[-1] + hvsr_std[-1])
            peak_water_level_p.append(water_level + hvsr_std[-1])
            hvsrp2.append(hvsr[-1] * math.exp(hvsr_log_std[count]))
            hvsrm.append(hvsr[-1] - hvsr_std[-1])
            peak_water_level_m.append(water_level - hvsr_std[-1])
            hvsr_m2.append(hvsr[-1] / math.exp(hvsr_log_std[-1]))
            # outFile.write(str(x_values[count])+'  '+str(hvsr[-1])+'  '+str(hvsrp[-1])+'  '+str(hvsrm[-1])+'\n')
            outFile.write(
                '%s %0.3f %0.3f %0.3f\n' % (str(x_values[count]), float(hvsr[-1]), float(hvsrp[-1]), float(str(hvsrm[-1]))))
    outFile.close()

    # Compute day at a time to also compute frequency standard deviation
    missing = 0

    # This holds the peaks for individual HVSRs that will contribute to the final HVSR. It will be used to find Sigmaf.
    hvsrPeaks = list()

    for day in sorted(day_values_passed):
        hvsr_tmp = list()
        for j in range(len(x_values) - 1):
            if method == 'Diffuse Field Assumption':
                if day in equal_daily_energy[0].keys() and day in equal_daily_energy[1].keys() and day in \
                        equal_daily_energy[2].keys():
                    hvsr0 = math.sqrt(
                        (equal_daily_energy[1][day][j] + equal_daily_energy[2][day][j]) / equal_daily_energy[0][day][j])
                    hvsr_tmp.append(hvsr0)
                else:
                    if verbose > 0:
                        msgLib.warning(sys.argv[0], day + ' missing component, skipped!')
                    missing += 1
                    continue
            else:
                if day in median_daily_psd[0].keys() and day in median_daily_psd[1].keys() and day in \
                        median_daily_psd[2].keys():
                    psd0 = [median_daily_psd[0][day][j], median_daily_psd[0][day][j + 1]]
                    psd1 = [median_daily_psd[1][day][j], median_daily_psd[1][day][j + 1]]
                    psd2 = [median_daily_psd[2][day][j], median_daily_psd[2][day][j + 1]]
                    hvsr0 = hvsrCalcs.get_hvsr(psd0, psd1, psd2, [x_values[j], x_values[j + 1]], use_method=method)
                    hvsr_tmp.append(hvsr0)
                else:
                    if verbose > 0:
                        msgLib.warning(sys.argv[0], day + ' missing component, skipped!')
                    missing += 1
                    continue
        if not np.isnan(np.sum(hvsr_tmp)):
            hvsrPeaks.append(hvsrCalcs.find_peaks(hvsr_tmp))

    report_header += '\n'
    report_header += ' '.join([str(missing), 'PSDs are missing one or more components\n'])

    # Find  the relative extrema of hvsr
    if not np.isnan(np.sum(hvsr)):
        indexList = hvsrCalcs.find_peaks(hvsr)
    else:
        indexList = list()

    stdf = list()
    for index in indexList:
        point = list()
        for j in range(len(hvsrPeaks)):
            p = None
            for k in range(len(hvsrPeaks[j])):
                if p is None:
                    p = hvsrPeaks[j][k]
                else:
                    if abs(index - hvsrPeaks[j][k]) < abs(index - p):
                        p = hvsrPeaks[j][k]
            if p is not None:
                point.append(p)
        point.append(index)
        v = list()
        for l in range(len(point)):
            v.append(x_values[point[l]])
        stdf.append(np.std(v))

    peak = hvsrCalcs.init_peaks(x_values, hvsr, indexList, hvsr_band, peak_water_level)
    peak = hvsrCalcs.check_clarity(x_values, hvsr, peak, True)

    # Find  the relative extrema of hvsrp (hvsr + 1 standard deviation)
    if not np.isnan(np.sum(hvsrp)):
        index_p = hvsrCalcs.find_peaks(hvsrp)
    else:
        index_p = list()

    peakp = hvsrCalcs.init_peaks(x_values, hvsrp, index_p, hvsr_band, peak_water_level_p)
    peakp = hvsrCalcs.check_clarity(x_values, hvsrp, peakp)

    # Find  the relative extrema of hvsrp (hvsr - 1 standard deviation)
    if not np.isnan(np.sum(hvsrm)):
        index_m = hvsrCalcs.find_peaks(hvsrm)
    else:
        index_m = list()

    peakm = hvsrCalcs.init_peaks(x_values, hvsrm, index_m, hvsr_band, peak_water_level_m)
    peakm = hvsrCalcs.check_clarity(x_values, hvsrm, peakm)

    peak = hvsrCalcs.check_stability(stdf, peak, hvsr_log_std, True)
    peak = hvsrCalcs.check_freq_stability(peak, peakm, peakp)

    if show_plot > 0 and len(hvsr) > 0:
        nx = len(x_values) - 1
        plt.suptitle(plot_title)
        if plot_pdf or plot_psd:
            ax.append(plt.subplot(plotRows, 1, 4))
        else:
            ax.append(plt.subplot(1, 1, 1))

        plt.semilogx(np.array(x_values[0:nx]), hvsr, lw=1, c='blue', label='HVSR')
        plt.semilogx(np.array(x_values[0:nx]), hvsrp, c='red', lw=1, ls='--',
                    label='{} {}'.format(utilities.get_char(u'\u00B11'), utilities.get_char(u'\u03C3')))
        plt.semilogx(np.array(x_values[0:nx]), hvsrm, c='red', lw=1, ls='--')
        # plt.semilogx(np.array(x_values),hvsrp2,c='r',lw=1,ls='--')
        # plt.semilogx(np.array(x_values),hvsr_m2,c='r',lw=1,ls='--')
        plt.ylabel(setParams.hvsrYlabel)
        plt.legend(loc='upper left')

        plt.xlim(setParams.hvsrXlim)
        ax[-1].set_ylim(hvsr_ylim)
        plt.xlabel(setParams.xLabel[xtype])

        for i in range(len(peak)):
            plt.semilogx(peak[i]['f0'], peak[i]['A0'], marker='o', c='r')
            plt.semilogx((peak[i]['f0'], peak[i]['f0']), (hvsr_ylim[0], peak[i]['A0']), c='red')
            if stdf[i] < float(peak[i]['f0']):
                dz = stdf[i]
                plt.axvspan(float(peak[i]['f0']) - dz, float(peak[i]['f0']) + dz, facecolor='#909090', alpha=0.5)
                plt.semilogx((peak[i]['f0'], peak[i]['f0']), (hvsr_ylim[0], hvsr_ylim[1]), c='#dcdcdc', lw=0.5)

        plt.savefig(
            os.path.join(setParams.imageDirectory + '/' + fileLib.hvsrFileName(network, station, location, start, end)).replace(
                '.txt', '.png'), dpi=setParams.imageDpi, transparent=True, bbox_inches='tight', pad_inches=0.1)
    if not dfa:
        ioput.print_peak_report(station_header, report_header, peak, report_information, min_rank)

    if show_plot:
        if verbose >= 0:
            msgLib.info('SHOW PLOT')
        plt.show()

    return

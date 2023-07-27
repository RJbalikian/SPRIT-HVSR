"""
This module contains all the functions needed to run the HVSR analysis
"""
import datetime
import math
import os
import pathlib
import pkg_resources
import tempfile
import warnings
import xml.etree.ElementTree as ET

import matplotlib
from matplotlib.backend_bases import MouseButton
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import scipy

#Main variables
greek_chars = {'sigma': u'\u03C3', 'epsilon': u'\u03B5', 'teta': u'\u03B8'}
channel_order = {'Z': 0, '1': 1, 'N': 1, '2': 2, 'E': 2}
separator_character = '='

t0 = datetime.datetime.now().time()
max_rank = 0
plotRows = 4

def run(datapath, source='file', kind='auto', method=4, hvsr_band=[0.4, 40], plot_type=False, verbose=False, **kwargs):

    #Get the input parameters
    input_params_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in input_params.__code__.co_varnames}
    params = input_params(datapath=datapath, hvsr_band=hvsr_band, **input_params_kwargs)

    #Get metadata
    get_metadata_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in get_metadata.__code__.co_varnames}
    params = get_metadata(params=params, **get_metadata_kwargs)

    #Fetch Data
    fetch_data_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in fetch_data.__code__.co_varnames}
    dataIN = fetch_data(params=params, source=source, **fetch_data_kwargs)    

    #Remove Noise
    remove_noise_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in remove_noise.__code__.co_varnames}
    dataIN = remove_noise(input=dataIN, kind=kind, **remove_noise_kwargs)   

    #Generate PPSDs
    generate_ppsds_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in generate_ppsds.__code__.co_varnames}
    from obspy.signal.spectral_estimation import PPSD
    PPSDkwargs = {k: v for k, v in locals()['kwargs'].items() if k in PPSD.__init__.__code__.co_varnames}
    generate_ppsds_kwargs.update(PPSDkwargs)
    ppsd_data = generate_ppsds(params=dataIN, **generate_ppsds_kwargs)
    
    #Process HVSR Curves
    process_hvsr_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in process_hvsr.__code__.co_varnames}
    hvsr_results = process_hvsr(params=ppsd_data, method=method, **process_hvsr_kwargs)
    
    #Check peaks
    check_peaks_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in check_peaks.__code__.co_varnames}
    hvsr_results = check_peaks(hvsr_dict=hvsr_results, hvsr_band = hvsr_band, **check_peaks_kwargs)
    
    #Check if results are good
    #Curve pass?
    curvePass = (hvsr_results['Best Peak']['Pass List']['Window Length Freq.'] +
                         hvsr_results['Best Peak']['Pass List']['Significant Cycles']+
                         hvsr_results['Best Peak']['Pass List']['Low Curve StDev. over time']) > 2
    
    #Peak Pass?
    peakPass = ( hvsr_results['Best Peak']['Pass List']['Peak Freq. Clarity Below'] +
                hvsr_results['Best Peak']['Pass List']['Peak Freq. Clarity Above']+
                hvsr_results['Best Peak']['Pass List']['Peak Amp. Clarity']+
                hvsr_results['Best Peak']['Pass List']['Freq. Stability']+
                hvsr_results['Best Peak']['Pass List']['Peak Stability (freq. std)']+
                hvsr_results['Best Peak']['Pass List']['Peak Stability (amp. std)']) >= 5
        
    if verbose:
        get_report(hvsr_results=hvsr_results, format='print')
        
    if plot_type != False:
        if plot_type == True:
            plot_type = 'HVSR p ann t c+ ann p Spec'
        hvplot_kwargs = {k: v for k, v in locals()['kwargs'].items() if k in hvplot.__code__.co_varnames}
        hvsr_results['HV_Plot'] = hvplot(hvsr_results, plot_type=plot_type, **hvplot_kwargs)

    return hvsr_results

def check_mark():
    """The default Windows terminal is not able to display the check mark character correctly.
       This function returns another displayable character if platform is Windows"""
    #This does not seem to be a problem for my system at least, so am not using it currently
    check = get_char(u'\u2714')
    #if sys.platform == 'win32':
    #    check = get_char(u'\u039E')
    return check

def get_char(in_char):
    """Outputs character with proper encoding/decoding"""
    if in_char in greek_chars.keys():
        out_char = greek_chars[in_char].encode(encoding='utf-8')
    else:
        out_char = in_char.encode(encoding='utf-8')
    return out_char.decode('utf-8')

def time_it(_t):
    """Computes elapsed time since the last call."""
    t1 = datetime.datetime.now().time()
    dt = t1 - _t
    t = _t
    if dt > 0.05:
        #print(f'[TIME] {dt:0.1f} s', flush=True)
        t = t1
    return t

##msgLib functions
#Post message
def message(post_message):
    """Prints a run message"""
    bar = "*" * 12
    print("%s %s %s" % (bar, post_message, bar))

#Post error
def error(err_message, code):
    """Prints an error message"""
    print("\n[ERR] %s\n" % err_message, flush=True)
    return code

#Post warning
def warning(sender, warn_message):
    """Print a warning message"""
    print("[WARN] from %s: %s" % (sender, warn_message), flush=True)

#Post info message
def info(info_message):
    """Prints an informative message"""
    print("[INFO] %s" % info_message, flush=True)
    return

#Converts filepaths to pathlib paths, if not already
def checkifpath(filepath):
    """Support function to check if a filepath is a pathlib.Path object and tries to convert if not

    Parameters
    ----------
    filepath : str or pathlib.Path, or anything
        Filepath to check. If not a valid filepath, will not convert and raises error

    Returns
    -------
    filepath : pathlib.Path
        pathlib.Path of filepath
    """

    # checks if the variable is any instance of pathlib
    if isinstance(filepath, pathlib.PurePath):
        pass
    else:
        try:
            filepath = pathlib.Path(filepath)
            #print('Converted string to pathlib path') #Assume a string was input rather than pathlib object
        except:
            error('Input cannot be converted to pathlib path', 0)
    return filepath

#Formats time into desired output
def __formatTime(inputDT, tzone='UTC'):
    """Private function to format time, used in other functions

    Formats input time to datetime objects in utc

    Parameters
    ----------
    inputDT : str or datetime obj 
        Input datetime. Can include date and time, just date (time inferred to be 00:00:00.00) or just time (if so, date is set as today)
    tzone   : str='utc' or int {'utc', 'local'} 
        Timezone of data entry. 
            If string and not utc, assumed to be timezone of computer running the process.
            If int, assumed to be offset from UTC (e.g., CST in the United States is -6; CDT in the United States is -5)

    Returns
    -------
    outputTimeObj : datetime object in UTC
        Output datetime.datetime object, now in UTC time.

    """
    if type(inputDT) is str:
        #tzone = 'America/Chicago'
        #Format string to datetime obj
        div = '-'
        timeDiv = 'T'
        if "/" in inputDT:
            div = '/'
            hasDate = True
        elif '-' in inputDT:
            div = '-'
            hasDate = True
        else:
            hasDate= False
            year = datetime.datetime.today().year
            month = datetime.datetime.today().month
            day = datetime.datetime.today().day

        if ':' in inputDT:
            hasTime = True
            if 'T' in inputDT:
                timeDiv = 'T'
            else:
                timeDiv = ' '
        else:
            hasTime = False
        
        if hasDate:
            #If first number is 4-dig year (assumes yyyy-dd-mm is not possible)
            if len(inputDT.split(div)[0])>2:
                year = inputDT.split(div)[0]
                month = inputDT.split(div)[1]
                day = inputDT.split(div)[2].split(timeDiv)[0]

            #If last number is 4-dig year            
            elif len(inputDT.split(div)[2].split(timeDiv)[0])>2:
                #..and first number is day
                if int(inputDT.split(div)[0])>12:
                    #dateStr = '%d'+div+'%m'+div+'%Y'   
                    year = inputDT.split(div)[2].split(timeDiv)[0]
                    month = inputDT.split(div)[1]
                    day = inputDT.split(div)[0]
                #...and first number is month (like American style)                             
                else:
                    year = inputDT.split(div)[2].split(timeDiv)[0]
                    month = inputDT.split(div)[0]
                    day = inputDT.split(div)[1]     
            
            #Another way to catch if first number is (2-digit) year
            elif int(inputDT.split(div)[0])>31:
                #dateStr = '%y'+div+'%m'+div+'%d'
                year = inputDT.split(div)[0]
                #Assumes anything less than current year is from this century
                if year < datetime.datetime.today().year:
                    year = '20'+year
                else:#...and anything more than current year is from last century
                    year = '19'+year
                #assumes day will always come last in this instance, as above
                month = inputDT.split(div)[1]
                day = inputDT.split(div)[2].split(timeDiv)[0]

            #If last digit is (2 digit) year           
            elif int(inputDT.split(div)[2].split(timeDiv)[0])>31:
                #...and first digit is day
                if int(inputDT.split(div)[0])>12:
                    #dateStr = '%d'+div+'%m'+div+'%y'       
                    year = inputDT.split(div)[2].split(timeDiv)[0]
                    if year < datetime.datetime.today().year:
                        year = '20'+year
                    else:
                        year = '19'+year
                    month = inputDT.split(div)[1]
                    day = inputDT.split(div)[0]                           
                else: #...and second digit is day
                    #dateStr = '%m'+div+'%d'+div+'%y'
                    year = inputDT.split(div)[2].split(timeDiv)[0]
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
            if hasDate:
                timeStr = inputDT.split(timeDiv)[1]
            else:
                timeStr = inputDT
            
            if 'T' in timeStr:
                timeStr=timeStr.split('T')[1]
            elif ' ' in timeStr:
                timeStr=timeStr.split(' ')[1]

            timeStrList = timeStr.split(':')
            if len(timeStrList[0])>2:
                timeStrList[0] = timeStrList[0][-2:]
            elif int(timeStrList[0]) > 23:
                timeStrList[0] = timeStrList[0][-1:]
            
            if len(timeStrList) == 3:
                if '.' in timeStrList[2]:
                    microS = int(timeStrList[2].split('.')[1])
                    timeStrList[2] = timeStrList[2].split('.')[0]
            elif len(timeStrList) == 2:
                timeStrList.append('00')

            hour = int(timeStrList[0])
            minute=int(timeStrList[1])
            sec = int(timeStrList[2])

        outputTimeObj = datetime.datetime(year=int(year),month=int(month), day=int(day),
                                hour=int(hour), minute=int(minute), second=int(sec), microsecond=int(microS))

    elif type(inputDT) is datetime.datetime or type(inputDT) is datetime.time:
        outputTimeObj = inputDT

    #Add timezone info
    if outputTimeObj.tzinfo is not None and outputTimeObj.tzinfo.utcoffset(outputTimeObj) is not None:
        #This is already timezone aware
        pass
    elif type(tzone) is int:
        outputTimeObj = outputTimeObj-datetime.timedelta(hours=tzone)
    elif type(tzone) is str:
        import zoneinfo
        if tzone.lower() in list(map(str.lower, zoneinfo.available_timezones())):
            outputTimeObj = outputTimeObj.replace(tzinfo=zoneinfo.ZoneInfo(tzone))
        else:
            print("ERROR: Timezone {} is not in official list.".format(tzone))
    elif isinstance(tzone, zoneinfo.ZoneInfo):
        outputTimeObj = outputTimeObj.replace(tzinfo=tzone)
    else:
        print("ERROR: Timezone must be either str or int")
    
    #Convert to UTC
    outputTimeObj = outputTimeObj.astimezone(datetime.timezone.utc)   

    return outputTimeObj

#Sort Channels later
def __sortchannels(channels=['Z', 'N', 'E']):
    """"Private function to sort channels. Not currently used
    
    Sort channels. Z/vertical should be first, horizontal order doesn't matter, but N 2nd and E 3rd is default
    
    Parameters
    ----------
        channels    : list, default = ['Z', 'N', 'E']
    
    Returns
    -------
        sorted_channel_list : list
            Input list, sorted according to: Z, N, E

    """
    channel_order = {'Z': 0, '1': 1, 'N': 1, '2': 2, 'E': 2}

    sorted_channel_list = channels.copy()
    for channel in channels:
        sorted_channel_list[channel_order[channel[2]]] = channel
    return sorted_channel_list

#Define input parameters
def input_params(datapath,
                site='HVSR Site',
                network='AM', 
                station='RAC84', 
                loc='00', 
                channels=['EHZ', 'EHN', 'EHE'],
                acq_date=str(datetime.datetime.now().date()),
                starttime = '00:00:00.00',
                endtime = '23:59:59.999',
                tzone = 'UTC',
                xcoord = -88.2290526,
                ycoord =  40.1012122,
                elevation = 755,
                depth = 0,
                instrument = 'Raspberry Shake',
                metapath = '',
                hvsr_band = [0.4, 40] 
                ):
    """Function for designating input parameters for reading in and processing data
    
    Parameters
    ----------
     datapath : str or pathlib.Path object
        Filepath of data. This can be a directory or file, but will need to match with what is chosen later as the source parameter in fetch_data()
    site : str
        Site name as designated by scientist for ease of reference. Used for plotting titles, etc.
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
        Start time of data stream. This is necessary for Raspberry Shake data. Format can be either 'HH:MM:SS.micros' or 'HH:MM' at minimum.
    endtime : str, time obejct, or datetime object, default='23:59:99.99'
        End time of data stream. This is necessary for Raspberry Shake data. Same format as starttime
    tzone : str or int, default = 'UTC'
        Timezone of input data. If string, 'UTC' will use the time as input directly. Any other string value needs to be a TZ identifier in the IANA database, a wikipedia page of these is available here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones.
        If int, should be the int value of the UTC offset (e.g., for American Eastern Standard Time: -5). 
        This is necessary for Raspberry Shake data.
    xcoord : float, default=-88.2290526
        Longitude of data point. Not currently used, but will likely be used in future.
    ycoord : float, default=40.1012122
        Latitude of data point. Not currently used, but will likely be used in the future.
    elevation : float, default=755
        Surface elevation of data point. Not currently used, but will likely be used in the future.
    depth : float, default=0
        Depth of seismometer. Not currently used, but will likely be used in the future.
    instrument : str or list {'Raspberry Shake')
        Instrument from which the data was acquired. 
    metapath : str or pathlib.Path object, default=''
        Filepath of metadata, in format supported by obspy.read_inventory. If default value of '', will read from resources folder of repository (only supported for Raspberry Shake).
    hvsr_band : list, default=[0.4, 40]
        Two-element list containing low and high "corner" frequencies for processing. This can specified again later.
    
    Returns
    -------
    inputParamDict : dict
        Dictionary containing input parameters, including data file path and metadata path. This will be used as an input to other functions.

    """

    #Declare obspy here instead of at top of file for (for example) colab, where obspy first needs to be installed on environment
    global obspy
    import obspy

    #Make Sure metapath is all good
    if not pathlib.Path(metapath).exists() or metapath=='':
        if metapath == '':
            pass
            #print('No metadata file specified!')
        else:
            print('Specified metadata file cannot be read!')
        repoDir = pathlib.Path(os.path.dirname(__file__))
        metapath = pathlib.Path(pkg_resources.resource_filename(__name__, 'resources/rs3dv7_metadata.inv'))
        #print('Using default metadata file for Raspberry Shake v.7 distributed with package')
    else:
        if isinstance(metapath, pathlib.PurePath):
            metapath = metapath.as_posix()
        else:
            metapath = pathlib.Path(metapath).as_posix()

    #Reformat times
    if type(acq_date) is datetime.datetime:
        date = str(acq_date.date())
    elif type(acq_date) is datetime.date:
        date=str(acq_date)
    elif type(acq_date) is str:
        date = acq_date
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
    
    starttime = date+"T"+starttime
    starttime = obspy.UTCDateTime(__formatTime(starttime, tzone=tzone))
    
    if type(endtime) is str:
        if 'T' in endtime:
            date=endtime.split('T')[0]
            endtime = endtime.split('T')[1]
    elif type(endtime) is datetime.datetime:
        date = str(endtime.date())
        endtime = str(endtime.time())
    elif type(endtime) is datetime.time():
        endtime = str(endtime)

    endtime = date+"T"+endtime
    endtime = obspy.UTCDateTime(__formatTime(endtime, tzone=tzone))

    acq_date = datetime.date(year=int(date.split('-')[0]), month=int(date.split('-')[1]), day=int(date.split('-')[2]))
    raspShakeInstNameList = ['raspberry shake', 'shake', 'raspberry', 'rs', 'rs3d', 'rasp. shake', 'raspshake']
    
    #Raspberry shake stationxml is in the resources folder, double check we have right path
    if instrument.lower() in  raspShakeInstNameList:
        if metapath == r'resources/rs3dv7_metadata.inv':
            metapath = pathlib.Path(pkg_resources.resource_filename(__name__, 'resources/rs3dv7_metadata.inv'))
            #metapath = pathlib.Path(os.path.realpath(__file__)).parent.joinpath('/resources/rs3dv7_metadata.inv')

    #Add key/values to input parameter dictionary
    inputParamDict = {'net':network,'sta':station, 'loc':loc, 'cha':channels, 'instrument':instrument,
                    'acq_date':acq_date,'starttime':starttime,'endtime':endtime, 'timezone':'UTC',
                    'longitude':xcoord,'latitude':ycoord,'elevation':elevation,'depth':depth, 'site':site,
                    ' datapath': datapath, 'metapath':metapath, 'hvsr_band':hvsr_band
                    }

    return inputParamDict

#Read in metadata .inv file, specifically for RaspShake
def update_shake_metadata(filepath, params, write_path=''):
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

    filepath = checkifpath(filepath)

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
            print('write_path not recognized as filepath, not writing')
            write_path=''

    if write_path=='':
        #Create temporary file for reading into obspy
        tpf = tempfile.NamedTemporaryFile(delete=False)
        stringRoot = ET.tostring(root, encoding='UTF-8', method='xml')
        tpf.write(stringRoot)

        inv = obspy.read_inventory(tpf.name, format='STATIONXML', level='response')
        tpf.close()

        os.remove(tpf.name)
    
    params['inv'] = inv
    return params

#Launch the gui
def gui():
    """Function to open a window with a graphical user interface (gui)
    
    No parameters, no returns; just opens the gui window.
    """
    import pkg_resources
    #guiPath = pathlib.Path(os.path.realpath(__file__))
    #print(guiPath.joinpath('gui/tkgui.py').as_posix())
    from sprit.sprit_gui import App
    import tkinter as tk

    def on_gui_closing():
        plt.close('all')
        gui_root.quit()
        gui_root.destroy()

    gui_root = tk.Tk()
    icon_path = pathlib.Path(pkg_resources.resource_filename(__name__, 'resources/sprit_icon_alpha.ico'))
    gui_root.iconbitmap(icon_path)
    App(master=gui_root) #Open the app with a tk.Tk root

    gui_root.protocol("WM_DELETE_WINDOW", on_gui_closing)    
    gui_root.mainloop() #Run the main loop
    
#Support function for get_metadata()
def _read_RS_Metadata(params):
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
    inv = params['inv']

    if isinstance(inv, pathlib.PurePath) or type(inv) is str:
        inv = checkifpath(inv)
        tree = ET.parse(inv)
        root = tree.getroot()

    station = params['sta']
    network = params['net']
    channels = params['cha']

    if isinstance(inv, pathlib.PurePath):
        inv = checkifpath(inv)
        tree = ET.parse(inv)
        root = tree.getroot()
    else:
        #Create temporary file from inventory object
        tpf = tempfile.NamedTemporaryFile(delete=False)
        inv.write(tpf.name, format='STATIONXML')

        #Read data into xmlTree
        tree = ET.parse(tpf.name)
        root = tree.getroot()

        #Close and remove temporary file
        tpf.close()
        os.remove(tpf.name)

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
    return params

#Gets the metadata for Raspberry Shake, specifically for 3D v.7
def get_metadata(params, write_path=''):
    """Get metadata and calculate or get paz parameter needed for PPSD

    Parameters
    ----------
    params : dict
        Dictionary containing all the input and other parameters needed for processing
            Ouput from input_params() function
    write_path : str
        String with output filepath of where to write updated inventory or metadata file
            If not specified, does not write file 

    Returns
    -------
    params : dict
        Modified input dictionary with additional key:value pair containing paz dictionary (key = "paz")
    """
    invPath = params['metapath']
    raspShakeInstNameList = ['raspberry shake', 'shake', 'raspberry', 'rs', 'rs3d', 'rasp. shake', 'raspshake']
    if params['instrument'].lower() in  raspShakeInstNameList:
        params = update_shake_metadata(filepath=invPath, params=params, write_path=write_path)
        params = _read_RS_Metadata(params)
    else:
        print('{} not currently supported\n Returning input params dictionary.'.format(params['instrument']))
        return params
    
    return params

#Check that input strema has Z, E, N channels
def has_required_channels(stream):
    channel_set = set()
    
    # Extract the channel codes from the traces in the stream
    for trace in stream:
        channel_set.add(trace.stats.channel)
    
    # Check if Z, E, and N channels are present
    return {'Z', 'E', 'N'}.issubset(channel_set)

#Reads in traces to obspy stream
def fetch_data(params, inv=None, source='file', trim_dir=None, export_format='mseed', detrend='spline', detrend_order=2, verbose=False):
    """Fetch ambient seismic data from a source to read into obspy stream
        
        Parameters
        ----------
        params  : dict
            Dictionary containing all the necessary params to get data.
                Parameters defined using input_params() function.
        inv     : obspy inventory object, default=None
            Obspy inventory object containing metadata for instrument that collected data to be fetched. By default, the inventory object is read from params['inv'], but this can be manually specified here too.
        source  : str, {'raw', 'dir', 'file'}
            String indicating where/how data file was created. For example, if raw data, will need to find correct channels.
                'raw' finds raspberry shake data, from raw output copied using scp directly from Raspberry Shake, either in folder or subfolders; 
                'dir' is used if the day's 3 component files (currently Raspberry Shake supported only) are all 3 contained in a directory by themselves.
                'file' is used if the datapath specified in input_params() is the direct filepath to a single file to be read directly into an obspy stream.
        trim_dir : None or str or pathlib obj, default=None
            If None (or False), data is not trimmed in this function.
            Otherwise, this is the directory to save trimmed and exported data.
        export_format: str='mseed'
            If trim_dir is not False, this is the format in which to save the data
        detrend : str or bool, default='spline'
            If False, data is not detrended.
            Otherwise, this should be a string accepted by the type parameter of the obspy.core.trace.Trace.detrend method: https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.detrend.html
        detrend_order : int, default=2
            If detrend parameter is 'spline' or 'polynomial', this is passed directly to the order parameter of obspy.core.trace.Trace.detrend method.
        
        Returns
        -------
        params : dict
            Same dict as params parameter, but with an additional "strea" key with an obspy data stream with 3 traces: Z (vertical), N (North-south), and E (East-west)
        
        """
    datapath = params[' datapath']
    if inv is None:
        inv = params['inv'], 
    date=params['acq_date']

    if '}' in str(datapath):
        datapath = datapath.as_posix().replace('{','')
        datapath = datapath.split('}')
    
    if isinstance(datapath,list):
        for i, d in enumerate(datapath):
            datapath[i] = checkifpath(str(d).strip())
    else:
        datapath = checkifpath(datapath)

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
            error('First item in date tuple must be day of year (0-366)', 0)
        elif date[1] > datetime.datetime.now().year:
            error('Second item in date tuple should be year, but given item is in the future', 0)
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
            info("Preferred date format is 'yyyy-mm-dd' or 'yyyy/mm/dd'. Will attempt to parse date.")
            date = datetime.datetime(int(dateSplit[2]), int(dateSplit[0]), int(dateSplit[1]))
            doy = date.timetuple().tm_yday
            year = date.year
        else:
            info("Preferred date format is 'yyyy-mm-dd' or 'yyyy/mm/dd'. Cannot parse date.")
    elif type(date) is int:
        doy = date
        year = datetime.datetime.today().year
    else: #FOR NOW, need to update
        date = datetime.datetime.now()
        doy = date.timetuple().tm_yday
        year = date.year
        print("Did not recognize date, using year {} and day {}".format(year, doy))

    #Select which instrument we are reading from (requires different processes for each instrument)
    raspShakeInstNameList = ['raspberry shake', 'shake', 'raspberry', 'rs', 'rs3d', 'rasp. shake', 'raspshake']
    if source=='raw':
        if inst.lower() in raspShakeInstNameList:
            rawDataIN = __read_RS_file_struct(datapath, source, year, doy, inv, params)
    elif source=='dir':
        if inst.lower() in raspShakeInstNameList:
            rawDataIN = __read_RS_file_struct(datapath, source, year, doy, inv, params)
    elif source=='file':
        if isinstance(datapath, list) or isinstance(datapath, tuple):
            rawTraces = []
            for datafile in datapath:
                rawTrace = obspy.read(datafile)
                rawTrace = rawTrace
                rawTraces.append(rawTrace)
            
            for i, trace in enumerate(rawTraces):
                if i == 0:
                    rawDataIN = trace
                else:
                    rawDataIN = rawDataIN + trace
        else:
            rawDataIN = obspy.read(datapath)#, starttime=obspy.core.UTCDateTime(params['starttime']), endttime=obspy.core.UTCDateTime(params['endtime']), nearest_sample =True)
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=UserWarning)
            rawDataIN.attach_response(inv)
    elif source=='batch':
        print("Batch read not yet supported")
        if isinstance(datapath, list) or isinstance(datapath, tuple):
            for d in datapath:
                pass
        else:
            print('datapath parameter should be list or tuple if batch mode is selected, not {}.'.format(type(datapath)))
    else:
        try:
            rawDataIN = obspy.read(datapath)
            rawDataIN.attach_response(inv)
        except:
            print('Read or source error')

    if rawDataIN is None:
        return
    elif isinstance(rawDataIN, obspy.core.stream.Stream):
        #Make sure z component is first
        if 'Z' in rawDataIN[0].stats['channel']:#).split('.')[3]:#[12:15]:
            dataIN = rawDataIN
        else:
            dataIN = rawDataIN.sort(['channel'], reverse=True) #z, n, e order
    else:
        dataIN = []
        for i, st in enumerate(rawDataIN):
            if 'Z' in st[0].stats['channel']:#).split('.')[3]:#[12:15]:
                dataIN.append(rawDataIN[i])
            else:
                dataIN.append(rawDataIN[i].sort(['channel'], reverse=True)) #z, n, e order            
        
    if not trim_dir:
        pass
    else:
        dataIN = trim_data(stream=dataIN, params=params, export_dir=trim_dir, export_format=export_format)

    
    if isinstance(dataIN[0].data, np.ma.masked_array):
        dataIN = dataIN.split()
        #Need to test to see if this works ok with lots of little windows

    if detrend==False:
        pass
    elif detrend==True:
        #By default, do a spline removal
        for tr in dataIN:
            tr.detrend(type='spline', order=detrend_order, dspline=1000)        
    else:
        data_undetrended = dataIN.copy()
        try:
            if detrend=='simple':
                for tr in dataIN:
                    tr.detrend(type=detrend)
            if detrend=='linear':
                for tr in dataIN:
                    tr.detrend(type=detrend)
            if detrend=='constant' or detrend=='demean':
                for tr in dataIN:
                    tr.detrend(type=detrend)                
            if detrend=='polynomial':
                for tr in dataIN:
                    tr.detrend(type=detrend, order=detrend_order)   
            if detrend=='spline':
                for tr in dataIN:
                    tr.detrend(type=detrend, order=detrend_order, dspline=1000)       
        except:
            dataIN = data_undetrended
            if verbose:
                print("Detrend error, data not detrended")

    dataIN = dataIN.merge(method=1)
    params['stream'] = dataIN

    return params

def __read_from_RS(dest, src='SHAKENAME@HOSTNAME:/opt/data/archive/YEAR/AM/STATION/', opts='az', username='myshake', password='shakeme',hostname='rs.local', year='2023', sta='RAC84',sleep_time=0.1, verbose=True, save_progress=True, method='scp'):
    src = src.replace('SHAKENAME', username)
    src = src.replace('SHAKENAME', hostname)
    src = src.replace('YEAR', year)
    src = src.replace('STATION', sta)

    if method == 'src':
        """This does not work from within a virtual environment!!!!"""
        #import pexpect
        import sys
        #from pexpect import popen_spawn
        import time
        import wexpect

        scp_command = 'scp -r {} "{}"'.format(src, dest)

        print('Command:', scp_command)
        child = wexpect.spawn(scp_command, timeout=5)

        child.expect("password:")
        child.sendline(password)

        child.expect(wexpect.EOF)

        print("Files have been successfully transferred to {}!".format(dest))
    elif method=='rsync':
        if verbose:
            opts = opts + 'v'
        if save_progress:
            opts = opts + 'p'   

        #import subprocess
        #subprocess.run(["rsync", "-"+opts, src, dest])
        #subprocess.run(["rsync", "-"+opts, src, dest])

        import pty
        #Test, from https://stackoverflow.com/questions/13041732/ssh-password-through-python-subprocess
        command = [
            'rsync',
            "-"+opts,
            src,
            dest
            #'{0}@{1}'.format(shakename, hostname),
            #'-o', 'NumberOfPasswordPrompts=1',
            #'sleep {0}'.format(sleep_time),
        ]

        # PID = 0 for child, and the PID of the child for the parent    
        pid, child_fd = pty.fork()

        if not pid: # Child process
            # Replace child process with our SSH process
            os.execv(command[0], command)

        while True:
            output = os.read(child_fd, 1024).strip()
            lower = output.lower()
            # Write the password
            if lower.endswith('password:'):
                os.write(child_fd, password + '\n')
                break
            elif 'are you sure you want to continue connecting' in lower:
                # Adding key to known_hosts
                os.write(child_fd, 'yes\n')
            elif 'company privacy warning' in lower:
                pass # This is an understood message
            else:
                print("SSH Connection Failed",
                    "Encountered unrecognized message when spawning "
                    "the SSH tunnel: '{0}'".format(output))

    return dest

#Read data from raspberry shake
def __read_RS_file_struct(datapath, source, year, doy, inv, params):
    """"Private function used by fetch_data() to read in Raspberry Shake data"""
    from obspy.core import UTCDateTime
    fileList = []
    folderPathList = []
    filesinfolder = False
    datapath = checkifpath(datapath)

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

            if len(fileList) !=3:
                error('3 channels needed! {} found.'.format(len(folderPathList)), 1)
            else:
                fileList.sort(reverse=True) # Puts z channel first
                folderPathList.sort(reverse=True)
                print('Reading files: \n\t{}\n\t{}\n\t{}'.format(fileList[0].name, fileList[1].name, fileList[2].name))

            if len(fileList) == 0:
                info('No file found for specified parameters. The following days/files exist for specified year in this directory')
                doyList = []
                for j, folder in enumerate(folderPathList):
                    for i, file in enumerate(folder.iterdir()):
                        if j ==0:
                            doyList.append(str(year) + ' ' + str(file.name[-3:]))
                            print(datetime.datetime.strptime(doyList[i], '%Y %j').strftime('%b %d'), '| Day of year:' ,file.name[-3:])
                return None
            
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

def batch_data_read(input_filelist, input_params_list=None, verbose=False):
    """Function to read list of files and parameters

    Parameters
    ----------
    input_filelist : list
        List of filepaths to read using obspy.read()
    input_params_list : list, optional
        List of dictionary with select read parameters, by default None
    verbose : bool, default = False
        Whether to print results 

    Returns
    -------
    stream_dict : dict
        Dictionary contiaining unique streams
    """

    # Dictionary to store the stream objects
    stream_dict = {}

    # Read and process each MiniSEED file
    for i, file in enumerate(input_filelist):
        if input_params_list is None:
            pass
        else:
            read_params = input_params_list[i]
        
        # Read the MiniSEED file into a Stream object
        if isinstance(read_params, dict):
            stream = obspy.read(file, **read_params)
        else:
            stream = obspy.read(file)

        # Get the network, station, and location codes
        network = stream[0].stats.network
        station = stream[0].stats.station
        location = stream[0].stats.location
        
        # Create a unique identifier for the network-station-location combination
        stream_id = f"{network}.{station}.{location}"

        # Check if the stream has a single trace
        if len(stream) == 1:

            # Check if the stream ID exists in the dictionary
            if stream_id in stream_dict:
                if stream[0].stats.channel == 'Z':
                    stream_dict[stream_id][0] = stream[0]
                elif stream[0].stats.channel == 'E':
                    stream_dict[stream_id][1] = stream[0]
                elif stream[0].stats.channel == 'N':
                    stream_dict[stream_id][2] = stream[0]
            else:
                # Create a new stream object with the first trace and assign Z, E, and N channels
                new_stream = obspy.Stream(traces=[None, None, None])
                if stream[0].stats.channel == 'Z':
                    new_stream[0] = stream[0]
                elif stream[0].stats.channel == 'E':
                    new_stream[1] = stream[0]
                elif stream[0].stats.channel == 'N':
                    new_stream[2] = stream[0]
                # Assign network, station, location, etc. to the new_stream as required
                stream_dict[stream_id] = new_stream
        else:
            # Check if the stream has required channels and add it directly to stream_dict
            if has_required_channels(stream):
                stream_dict[stream_id] = stream

    # Validate the channels for each stream in stream_dict
    for stream_id, stream in stream_dict.items():
        if not has_required_channels(stream):
            if verbose:
                print(f"Stream {stream_id} does not have all required channels, removing.")
            del stream_dict[stream_id]

    if verbose:
        print("Streams:\n")
        print(stream_dict.keys())
        #for k in stream_dict.keys():
        #    print(k)

    return stream_dict

#Trim data 
def trim_data(params, stream=None, export_dir=None, export_format=None, **kwargs):
    """Function to trim data to start and end time

        Trim data to start and end times so that stream being analyzed only contains wanted data.
        Can also export data to specified directory using a specified site name and/or export_format

        Parameters
        ----------
            params  : dict
                Dictionary containing input parameters for trimming
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
    if 'starttime' in kwargs.keys():
        start = kwargs['starttime']
    else:
        start = params['starttime']
    
    if 'endtime' in kwargs.keys():
        end = kwargs['endtime']
    else:
        end = params['endtime']
        
    if 'site' in kwargs.keys():
        site = kwargs['site']
    else:
        site = params['site']

    if stream is not None:
        st_trimmed = stream.copy()
    elif 'stream' in params.keys():
        st_trimmed = params['stream'].copy()
    else:
        raise UnboundLocalError("stream not specified. Must either be specified using stream parameter or as a key in the params parameters (params['stream'])")
        
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

        export_dir = checkifpath(export_dir)
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

#Function to select windows using original stream specgram/plots
def select_windows(input):
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

    if type(input) is dict:
        if 'hvsr_curve' in input.keys():
            fig, ax = hvplot(hvsr_dict=input, plot_type='spec', returnfig=True, cmap='turbo')
        else:
            params = input.copy()
            input = input['stream']
    
    if isinstance(input, obspy.core.stream.Stream):
        fig, ax = plot_specgram_stream(input, component=['Z'])
    elif isinstance(input, obspy.core.trace.Trace):
        fig, ax = plot_specgram_stream(input)

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

    params['xwindows_out'] = xWindows
    params['fig'] = fig
    params['ax'] = ax
    return params

#Support function to help select_windows run properly
def _on_fig_close(event):
    global fig_closed
    fig_closed = True
    return

#Function to remove noise windows from data
def remove_noise(input, kind='auto', sat_percent=0.995, noise_percent=0.80, sta=2, lta=30, stalta_thresh=[0.5,5], warmup_time=0, cooldown_time=0, min_win_size=1):
    """Function to remove noisy windows from data, using various methods.
    
    Methods include 
    - Manual window selection (by clicking on a chart with spectrogram and stream data), 
    - Auto window selection, which does the following two in sequence (these can also be done indepently):
        - A sta/lta "antitrigger" method (using stalta values to automatically remove triggered windows where there appears to be too much noise)
        - A noise threshold method, that cuts off all times where the noise threshold equals more than (by default) 99.5% of the highest amplitude noise sample.

    Parameters
    ----------
    input : dict, obspy.Stream, or obspy.Trace
        Dictionary containing all the data and parameters for the HVSR analysis
    kind : str, {'auto', 'manual', 'stalta'/'antitrigger', 'saturation', 'noise threshold', 'warmup'/'cooldown'/'buffer'}
        The different methods for removing noise from the dataset. See descriptions above for what how each method works. By default 'auto.'
    noise_percent : float, default=0.995
        Percentage (between 0 and 1), to use as the threshold at which to remove data. This is used in the noise threshold method. By default 0.995. 
        If a value is passed that is greater than 1, it will be divided by 100 to obtain the percentage.
    sta : int, optional
        Short term average (STA) window (in seconds), by default 2.
    lta : int, optional
        Long term average (STA) window (in seconds), by default 30.
    stalta_thresh : list, default=[0.5,5]
        Two-item list or tuple with the thresholds for the stalta antitrigger. The first value (index [0]) is the lower threshold, the second value (index [1] is the upper threshold), by default [0.5,5]
    show_plot : bool, default=False
        If True, will plot the trigger and stalta values (if stalta antitrigger method), or the data with the new windows removed (if noise threshold), by default False. Does not apply to 'manual' method.
    warmup_time : int, default=0
        Time in seconds to allow for warmup of the instrument. This will renove any data before this time, by default 0.

    Returns
    -------
    output : dict
        Dictionary similar to input, but containing modified data with 'noise' removed
    """
    
    manualList = ['manual', 'man', 'm', 'window', 'windows', 'w']
    autoList = ['auto', 'automatic', 'all', 'a']
    antitrigger = ['stalta', 'anti', 'antitrigger', 'trigger', 'at']
    saturationThresh = ['saturation threshold', 'saturation', 'sat', 's']
    noiseThresh = ['noise threshold', 'noise', 'threshold', 'n']
    warmup_cooldown=['warmup', 'cooldown', 'warm', 'cool', 'buffer', 'warmup-cooldown', 'warmup_cooldown', 'wc', 'warm_cool', 'warm-cool']

    if isinstance(input,dict):
        if 'stream_edited' in input.keys():
            inStream = input['stream_edited'].copy()
        else:
            inStream = input['stream'].copy()
        output = input.copy()
    elif isinstance(input, obspy.core.stream.Stream) or isinstance(input, obspy.core.trace.Trace):
        inStream = input.copy()
        output = inStream.copy()
    else:
        print("ERROR: input is not expected type")
    
    if kind.lower() in manualList:
        if isinstance(output, dict):
            if 'xwindows_out' in output.keys():
                pass
            else:
                output = select_windows(output)
            window_list = output['xwindows_out']

        if isinstance(inStream, obspy.core.stream.Stream):
            if window_list is not None:
                output['stream_edited'] = __remove_windows(inStream, window_list, warmup_time)
            else:
                output = select_windows(output)
        elif type(output) is dict:
            pass
        else:
            print('ERROR: Using anything other than an obspy stream is not currently supported for this noise removal method.')
            
    elif kind.lower() in autoList:
        outStream = __remove_noise_thresh(inStream, noise_percent=noise_percent, lta=lta, min_win_size=min_win_size)
        outStream = __remove_anti_stalta(outStream, sta=sta, lta=lta, thresh=stalta_thresh)
        outStream = __remove_noise_saturate(outStream, sat_percent=sat_percent, min_win_size=min_win_size)
        outStream = __remove_warmup_cooldown(stream=outStream, warmup_time=warmup_time, cooldown_time=cooldown_time)
    elif kind.lower() in antitrigger:
        outStream = __remove_anti_stalta(inStream, sta=sta, lta=lta, thresh=stalta_thresh)
    elif kind.lower() in saturationThresh:
        outStream = __remove_noise_saturate(inStream, sat_percent=sat_percent, min_win_size=min_win_size)
    elif kind.lower() in noiseThresh:
        outStream = __remove_noise_thresh(inStream, noise_percent=noise_percent, lta=lta, min_win_size=min_win_size)
    elif kind.lower() in warmup_cooldown:
        outStream = __remove_warmup_cooldown(stream=inStream, warmup_time=warmup_time, cooldown_time=cooldown_time)
    else:
        print("kind parameter is not recognized. Please choose one of the following: 'manual', 'auto', 'antitrigger', 'noise threshold', 'warmup_cooldown")
        return

    if isinstance(input, dict):
        output['stream_edited'] = outStream
    elif isinstance(input, obspy.core.stream.Stream) or isinstance(input, obspy.core.trace.Trace):
        output = outStream
    return output

#Shows windows with None on input plot
def get_removed_windows(input, fig=None, ax=None, lineArtist =[], winArtist = [], existing_lineArtists=[], existing_xWindows=[], exist_win_format='matplotlib', keep_line_artists=True, time_type='matplotlib'):
    """This function is solely for getting Nones from masked arrays and plotting them as windows"""
    if fig is None and ax is None:
        fig, ax = plt.subplots()

    if type(input) is dict:
        if 'stream_edited' in input.keys():
            stream = input['stream_edited'].copy()
        else:
            stream = input['stream'].copy()
    else:
        stream = input.copy()


    samplesList = ['sample', 'samples', 's']
    utcList = ['utc', 'utcdatetime', 'obspy', 'u', 'o']
    matplotlibList = ['matplotlib', 'mpl', 'm']    
    
    #Get masked indices of trace(s)
    trace = stream[0]
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

        #if existing_xWindows != []:
        #    windows = windows + existing_xWindows
        #    existWinTypeList = ['removed'] * len(existing_xWindows)
        #    winTypeList = winTypeList + existWinTypeList

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
                    print('match')
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
                    print('time_type error')
                
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

    return fig, ax, lineArtist, winArtist

def plot_noise_windows(hvsr_dict, fig=None, ax=None, clear_fig=False, fill_gaps=None,
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
            ax=self.ax_noise
            fig=self.fig_noise
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
    
    fig, ax = plot_specgram_stream(stream=hvsr_dict['stream'], params=hvsr_dict, fig=fig, ax=ax, component='Z', stack_type='linear', detrend='mean', fill_gaps=fill_gaps, dbscale=True, return_fig=True, cmap_per=[0.1,0.9])
    fig.canvas.draw()

    #Reset edited data every time plot_noise_windows is run
    hvsr_dict['stream_edited'] = hvsr_dict['stream'].copy()

    #Set initial input
    input = hvsr_dict['stream']

    #print(input[0].stats.starttime)
    if do_stalta:
        hvsr_dict['stream_edited'] = remove_noise(input=input, kind='stalta', sta=sta, lta=lta, stalta_thresh=stalta_thresh)
        input = hvsr_dict['stream_edited']

    if do_pctThresh:
        hvsr_dict['stream_edited'] = remove_noise(input=input, kind='saturation',  sat_percent=sat_percent, min_win_size=min_win_size)
        input = hvsr_dict['stream_edited']

    if do_noiseWin:
        hvsr_dict['stream_edited'] = remove_noise(input=input, kind='noise', noise_percent=noise_percent, lta=lta, min_win_size=min_win_size)
        input = hvsr_dict['stream_edited']

    if do_warmup:
        hvsr_dict['stream_edited'] = remove_noise(input=input, kind='warmup', warmup_time=warmup_time, cooldown_time=cooldown_time)

    fig, ax, noise_windows_line_artists, noise_windows_window_artists = get_removed_windows(input=hvsr_dict, fig=fig, ax=ax, time_type='matplotlib')
    
    fig.canvas.draw()
    plt.show()
    if return_dict:
        hvsr_dict['Windows_Plot'] = (fig, ax)
        return hvsr_dict
    return 

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
                print("ERROR: Overlapping windows. Please reselect windows to be removed or use a different noise removal method.")
                print(w[1], '>', sorted_window_list[i+1][0])
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

#Helper function for removing gaps
def __remove_gaps(stream, window_gaps_obspy):
    """Helper function for removing gaps"""
    #combine overlapping windows
    #THIS PART NEEDS WORK!!!!! #!#
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
        endT = stream[0].stats.endtime
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

#Generate PPSDs for each channel
#def generate_ppsds(params, stream, ppsd_length=60, **kwargs):
def generate_ppsds(params, remove_outliers=True, outlier_std=3, verbose=False, **ppsd_kwargs):
    """Generates PPSDs for each channel

        Channels need to be in Z, N, E order
        Info on PPSD creation here: https://docs.obspy.org/packages/autogen/obspy.signal.spectral_estimation.PPSD.html
        
        Parameters
        ----------
        params : dict
            Dictionary containing all the parameters and other data of interest (stream and paz, for example)
        remove_outliers : bool, default=True
            Whether to remove outlier h/v curves. This is recommended, particularly if remove_noise() has been used.
        outlier_std :  float, default=3
            The standard deviation value to use as a threshold for determining whether a curve is an outlier. 
            This averages over the entire curve so that curves with very abberant data (often occurs when using the remove_noise() method), can be identified.
        **kwargs : dict
            Dictionary with keyword arguments that are passed directly to obspy.signal.PPSD.
            If the following keywords are not specified, their defaults are amended in this function from the obspy defaults for its PPSD function. Specifically:
                - ppsd_length defaults to 60 (seconds) here instead of 3600
                - skip_on_gaps defaults to True instead of False
                - period_step_octaves defaults to 0.03125 instead of 0.125

        Returns
        -------
            ppsds   :   dict
                Dictionary containing entries with ppsds for each channel
    """
    paz=params['paz']
    stream = params['stream']

    #Set defaults here that are different than obspy defaults
    if 'ppsd_length' not in ppsd_kwargs:
        ppsd_kwargs['ppsd_length'] = 60
    if 'skip_on_gaps' not in ppsd_kwargs:
        ppsd_kwargs['skip_on_gaps'] = True
    if 'period_step_octaves' not in ppsd_kwargs:
        ppsd_kwargs['period_step_octaves'] = 0.03125

    from obspy.signal import PPSD

    eStream = stream.select(component='E')
    estats = eStream.traces[0].stats
    ppsdE = PPSD(estats, paz['E'],  **ppsd_kwargs)
    #ppsdE = PPSD(stream.select(component='E').traces[0].stats, paz['E'], ppsd_length=ppsd_length, kwargs=kwargs)
    ppsdE.add(stream, verbose=verbose)

    nStream = stream.select(component='N')
    nstats = nStream.traces[0].stats
    ppsdN = PPSD(nstats, paz['N'], **ppsd_kwargs)
    ppsdN.add(stream, verbose=verbose)

    zStream = stream.select(component='Z')
    zstats = zStream.traces[0].stats
    ppsdZ = PPSD(zstats, paz['Z'], **ppsd_kwargs)
    ppsdZ.add(stream, verbose=verbose)

    ppsds = {'Z':ppsdZ, 'N':ppsdN, 'E':ppsdE}

    #Add to the input dictionary, so that some items can be manipulated later on, and original can be saved
    params['ppsds_obspy'] = ppsds
    params['ppsds'] = {}
    anyKey = list(params['ppsds_obspy'].keys())[0]
    
    #Get ppsd class members
    members = [mems for mems in dir(params['ppsds_obspy'][anyKey]) if not callable(mems) and not mems.startswith("_")]
    params['ppsds']['Z'] = {}
    params['ppsds']['E'] = {}
    params['ppsds']['N'] = {}
    
    #Get lists that we may need to manipulate later and copy everything over to main 'ppsds' subdictionary (convert lists to np.arrays for consistency)
    listList = ['times_data', 'times_gaps', 'times_processed','current_times_used', 'psd_values']
    for m in members:
        params['ppsds']['Z'][m] = getattr(params['ppsds_obspy']['Z'], m)
        params['ppsds']['E'][m] = getattr(params['ppsds_obspy']['E'], m)
        params['ppsds']['N'][m] = getattr(params['ppsds_obspy']['N'], m)
        if m in listList:
            params['ppsds']['Z'][m] = np.array(params['ppsds']['Z'][m])
            params['ppsds']['E'][m] = np.array(params['ppsds']['E'][m])
            params['ppsds']['N'][m] = np.array(params['ppsds']['N'][m])

    #Create dict entry to keep track of how many outlier hvsr curves are removed (2-item list with [0]=current number, [1]=original number of curves)
    params['tsteps_used'] = [params['ppsds']['Z']['times_processed'].shape[0], params['ppsds']['Z']['times_processed'].shape[0]]
    
    #Remove outlier ppsds (those derived from data within the windows to be removed)
    if remove_outliers and 'xwindows_out' in params.keys():
        params = remove_outlier_ppsds(params, outlier_std=outlier_std, ppsd_length=ppsd_kwargs['ppsd_length'])
    params['tsteps_used'][0] = params['ppsds']['Z']['current_times_used'].shape[0]
    
    return params

#Remove outlier ppsds
def remove_outlier_ppsds(params, outlier_std=3, ppsd_length=60):
    """Function used in generate_ppsds() to remove outliers. May also be used independently.
    
    This uses the mean value of the entirety of each ppsd curve. This is not very robust, but it is intended only to remove curves who are well outside of the what would be expected.
    These abberant curves often occur due to the remove_noise() function.

    Parameters
    ----------
    params : dict
        Input dictionary containing all the values and parameters of interest
    outlier_std :  float, default=3
        The standard deviation value to use as a threshold for determining whether a curve is an outlier. 
        This averages over the entire curve so that curves with very abberant data (often occurs when using the remove_noise() method), can be identified.
    ppsd_length : float, optional
        Length of data segments passed to psd in seconds, by default 60.

    Returns
    -------
    params : dict
        Input dictionary with values modified based on work of function.
    """
    
    ppsds = params['ppsds']
    newPPsds = {}
    stds = {}
    psds_to_rid = []


    for k in ppsds:
        psdVals = np.array(ppsds[k]['psd_values'])
        meanArr = np.nanmean(psdVals, axis=1)
        newPPsds[k] = []
        totMean = np.nanmean(meanArr)
        stds[k] = np.std(meanArr)

        for i, m in enumerate(meanArr):
            if m > totMean + outlier_std*stds[k] or m < totMean - outlier_std*stds[k]:
                psds_to_rid.append(i)

        curr_times_mpl = []
        for i, t in enumerate(ppsds[k]['current_times_used']):
            curr_times_mpl.append(t.matplotlib_date)

        #Get ppsd length in seconds in matplotlib format
        ppsd_length_mpl = ppsd_length/86400

        ##UPDATE THIS NOT TO USE xWindows_out (calculate from mask)
        #Check if any times fall in excluded zone
        for i, t in enumerate(curr_times_mpl):
            nextT = t + ppsd_length_mpl
            for w, win in enumerate(params['xwindows_out']):
                if t > win[0] and t < win[1]:
                    psds_to_rid.append(i)
                elif nextT > win[0] and nextT < win[1]:
                    psds_to_rid.append(i)
    
    psds_to_rid = np.unique(psds_to_rid)

    for k in params['ppsds']:
        for i, r in enumerate(psds_to_rid):
            index = int(r-i)
            params['ppsds'][k]['psd_values'] = np.delete(params['ppsds'][k]['psd_values'], index, axis=0)
            params['ppsds'][k]['current_times_used'] = np.delete(params['ppsds'][k]['current_times_used'], index, axis=0)
    return params

#Check the x-values for each channel, to make sure they are all the same length
def __check_xvalues(ppsds):
    """Check x_values of PPSDS to make sure they are all the same length"""
    xLengths = []
    for k in ppsds.keys():
        xLengths.append(len(ppsds[k]['period_bin_centers']))
    if len(set(xLengths)) <= 1:
        pass #This means all channels have same number of period_bin_centers
    else:
        print('X-values (periods or frequencies) do not have the same values. \n This may result in computational errors')
        #Do stuff to fix it?
    return ppsds

#Check to make the number of time-steps are the same for each channel
def __check_tsteps(hvsr_dict):
    """Check time steps of PPSDS to make sure they are all the same length"""
    ppsds = hvsr_dict['ppsds']
    tSteps = []
    for k in ppsds.keys():
        tSteps.append(np.array(ppsds[k]['psd_values']).shape[0])
    if len(set(tSteps)) <= 1:
        pass #This means all channels have same number of period_bin_centers
        minTStep=tSteps[0]
    else:
        print('There is a different number of time-steps used to calculate HVSR curves. \n This may result in computational errors. Trimming longest.')
        minTStep = min(tSteps)
    return minTStep

def dfa(params, verbose=False):#, equal_interval_energy, median_daily_psd, verbose=False):
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
            print('[INFO] Diffuse Field Assumption', flush=True)
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

#Main function for processing HVSR Curve
def process_hvsr(params, method=3, smooth=True, freq_smooth='konno ohmachi', f_smooth_width=40, resample=True, remove_outlier_curves=True, outlier_curve_std=1.75, verbose=False):
    """Process the input data and get HVSR data
    
    This is the main function that uses other (private) functions to do 
    the bulk of processing of the HVSR data and the data quality checks.

    Parameters
    ----------
    params  : dict
        Dictionary containing all the parameters input by the user
    method  : int or str
        Method to use for combining the horizontal components
            1) Diffuse field assumption, or 'DFA' (not currently implemented)
            2) 'Arithmetic Mean': H ≡ (HN + HE)/2
            3) 'Geometric Mean': H ≡ √HN · HE, recommended by the SESAME project (2004)
            4) 'Vector Summation': H ≡ √H2 N + H2 E
            5) 'Quadratic Mean': H ≡ √(H2 N + H2 E )/2
            6) 'Maximum Horizontal Value': H ≡ max {HN, HE}
    smooth  : bool=True
        bool or int. 
            If True, default to smooth H/V curve to using savgoy filter with window length of 51 (works well with default resample of 1000 pts)
            If int, the length of the window in the savgoy filter.
    freq_smooth : str {'konno ohmachi', 'constant', 'proportional'}
        Which frequency smoothing method to use. By default, uses the 'konno ohmachi' method.
            - The Konno & Ohmachi method uses the obspy.signal.konnoohmachismoothing.konno_ohmachi_smoothing() function: https://docs.obspy.org/packages/autogen/obspy.signal.konnoohmachismoothing.konno_ohmachi_smoothing.html
            - The constant method
        See here for more information: https://www.geopsy.org/documentation/geopsy/hv-processing.html
    f_smooth_width : int, default = 40
        - For 'konno ohmachi': passed directly to the bandwidth parameter of the konno_ohmachi_smoothing() function, determines the width of the smoothing peak, with lower values resulting in broader peak. Must be > 0.
        - For 'constant': the size of a triangular smoothing window in the number of frequency steps
        - For 'proportional': the size of a triangular smoothing window in percentage of the number of frequency steps (e.g., if 1000 frequency steps/bins and f_smooth_width=40, window would be 400 steps wide)
    resample  : bool, default = True
        bool or int. 
            If True, default to resample H/V data to include 1000 frequency values for the rest of the analysis
            If int, the number of data points to interpolate/resample/smooth the component psd/HV curve data to.
    remove_outlier_curves : bool, default = True
        Whether to remove outlier h/v curves. Recommend to be repeated even after using in generate_ppsds() if remove_noise() is used.
    outlier_curve_std : float, default = 1.75
        Standard deviation of mean of each H/V curve to use as cuttoff for whether an H/V curve is considered an 'outlier'

    Returns
    -------
        hvsr_out    : dict
            Dictionary containing all the information about the data, including input parameters

    """
    ppsds = params['ppsds'].copy()#[k]['psd_values']
    ppsds = __check_xvalues(ppsds)

    methodList = ['<placeholder_0>', 'Diffuse Field Assumption', 'Arithmetic Mean', 'Geometric Mean', 'Vector Summation', 'Quadratic Mean', 'Maximum Horizontal Value']
    x_freqs = {}
    x_periods = {}

    psdValsTAvg = {}
    stDev = {}
    stDevValsP = {}
    stDevValsM = {}
    psdRaw={}
    currTimesUsed={}
    
    for k in ppsds:
        #if reasmpling has been selected
        if resample is True or type(resample) is int:
            if resample is True:
                resample = 1000 #Default smooth value

            xValMin = min(ppsds[k]['period_bin_centers'])
            xValMax = max(ppsds[k]['period_bin_centers'])

            #Resample period bin values
            x_periods[k] = np.logspace(np.log10(xValMin), np.log10(xValMax), num=resample)

            if smooth or type(smooth) is int:
                if smooth:
                    smooth = 51 #Default smoothing window
                elif smooth%2==0:
                    smooth = smooth+1

            #Resample raw ppsd values
            for i, t in enumerate(ppsds[k]['psd_values']):
                if i==0:
                    psdRaw[k] = np.interp(x_periods[k], ppsds[k]['period_bin_centers'], t)
                    if smooth is not False:
                        psdRaw[k] = scipy.signal.savgol_filter(psdRaw[k], smooth, 3)

                else:
                    psdRaw[k] = np.vstack((psdRaw[k], np.interp(x_periods[k], ppsds[k]['period_bin_centers'], t)))
                    if smooth is not False:
                        psdRaw[k][i] = scipy.signal.savgol_filter(psdRaw[k][i], smooth, 3)

        else:
            #If no resampling desired
            x_periods[k] = np.array(ppsds[k]['period_bin_centers'])
            psdRaw[k] = np.array(ppsds[k]['psd_values'])

        #Get average psd value across time for each channel (used to calc main H/V curve)
        psdValsTAvg[k] = np.nanmean(np.array(psdRaw[k]), axis=0)
        x_freqs[k] = np.divide(np.ones_like(x_periods[k]), x_periods[k]) 

        stDev[k] = np.std(psdRaw[k], axis=0)
        stDevValsM[k] = np.array(psdValsTAvg[k] - stDev[k])
        stDevValsP[k] = np.array(psdValsTAvg[k] + stDev[k])

        currTimesUsed[k] = ppsds[k]['current_times_used']

    #Get string of method type
    if type(method) is int:
        methodInt = method
        method = methodList[method]
    params['method'] = method

    #This gets the main hvsr curve averaged from all time steps
    anyK = list(x_freqs.keys())[0]
    hvsr_curve, _ = __get_hvsr_curve(x=x_freqs[anyK], psd=psdValsTAvg, method=methodInt, hvsr_dict=params, verbose=verbose)
    origPPSD = params['ppsds_obspy'].copy()

    #Add some other variables to our output dictionary
    hvsr_out = {'input_params':params.copy(),
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
                'tsteps_used': params['tsteps_used'].copy()
                }

    #This is if manual editing was used (should probably be updated at some point to just use masks)
    if 'xwindows_out' in params.keys():
        hvsr_out['xwindows_out'] = params['xwindows_out']
    else:
        hvsr_out['xwindows_out'] = []

    #These are in other places in the hvsr_out dict, so are redudant
    del hvsr_out['input_params']['ppsds_obspy']
    del hvsr_out['input_params']['ppsds']
    del hvsr_out['input_params']['tsteps_used']

    freq_smooth_ko = ['konno ohmachi', 'konno-ohmachi', 'konnoohmachi', 'konnohmachi', 'ko', 'k']
    freq_smooth_constant = ['constant', 'const', 'c']
    freq_smooth_proport = ['proportional', 'proportion', 'prop', 'p']

    #Frequency Smoothing
    if freq_smooth is False:
        print('No frequency smoothing is being applied. This is not recommended for noisy datasets.')
    elif freq_smooth is True or freq_smooth.lower() in freq_smooth_ko:
        from obspy.signal import konnoohmachismoothing
        for k in hvsr_out['psd_raw']:
            ppsd_data = hvsr_out['psd_raw'][k]
            freqs = hvsr_out['x_freqs'][k]
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=UserWarning) #Filter out UserWarning for just this method, since it throws up a UserWarning that doesn't really matter about dtypes often
                smoothed_ppsd_data = konnoohmachismoothing.konno_ohmachi_smoothing(ppsd_data, freqs, bandwidth=f_smooth_width, normalize=True)
            hvsr_out['psd_raw'][k] = smoothed_ppsd_data
    elif freq_smooth.lower() in freq_smooth_constant:
        hvsr_out = __freq_smooth_window(hvsr_out, f_smooth_width, kind_freq_smooth='constant')
    elif freq_smooth.lower() in freq_smooth_proport:
        hvsr_out = __freq_smooth_window(hvsr_out, f_smooth_width, kind_freq_smooth='proportional')
    else:
        print('No frequency smoothing is being applied. This is not recommended for noisy datasets.')

    #Get hvsr curve from three components at each time step
    anyK = list(hvsr_out['psd_raw'].keys())[0]
    if method==1 or method =='dfa' or method =='Diffuse Field Assumption':
        pass ###UPDATE HERE NEXT???__get_hvsr_curve(x=hvsr_out['x_freqs'][anyK], psd=tStepDict, method=methodInt, hvsr_dict=hvsr_out, verbose=verbose)
    else:
        hvsr_tSteps = []
        for tStep in range(len(hvsr_out['psd_raw'][anyK])):
            tStepDict = {}
            for k in hvsr_out['psd_raw']:
                tStepDict[k] = hvsr_out['psd_raw'][k][tStep]
            hvsr_tstep, _ = __get_hvsr_curve(x=hvsr_out['x_freqs'][anyK], psd=tStepDict, method=methodInt, hvsr_dict=hvsr_out, verbose=verbose)
            hvsr_tSteps.append(hvsr_tstep) #Add hvsr curve for each time step to larger list of arrays with hvsr_curves

    hvsr_out['ind_hvsr_curves'] = np.array(hvsr_tSteps)
    
    #use the standard deviation of each individual curve to determine if it overlapped
    if remove_outlier_curves:
        stdT = np.std(hvsr_out['ind_hvsr_curves'], axis=1)
        std_stdT= np.std(stdT)
        avg_stdT= np.nanmean(stdT)

        psds_to_rid = []
        for i,t in enumerate(hvsr_out['ind_hvsr_curves']):
            if stdT[i] < avg_stdT - std_stdT*outlier_curve_std or stdT[i] > avg_stdT + std_stdT*outlier_curve_std:
                psds_to_rid.append(i)

        for i, r in enumerate(psds_to_rid):
            index = int(r-i)
            hvsr_out['ind_hvsr_curves'] = np.delete(hvsr_out['ind_hvsr_curves'], index, axis=0)

            for k in hvsr_out['ppsds']:
                hvsr_out['psd_raw'][k] = np.delete(hvsr_out['psd_raw'][k], index, axis=0)         
                hvsr_out['current_times_used'][k] = np.delete(hvsr_out['current_times_used'][k], index)
        hvsr_out['tsteps_used'][0] = hvsr_out['ppsds'][k]['current_times_used'].shape[0]

    hvsr_out['ind_hvsr_stdDev'] = np.nanstd(hvsr_out['ind_hvsr_curves'], axis=0)

    #Get peaks for each time step
    tStepPeaks = []
    for tStepHVSR in hvsr_tSteps:
        tStepPeaks.append(__find_peaks(tStepHVSR))
    hvsr_out['ind_hvsr_peak_indices'] = tStepPeaks
    #Get peaks of main HV curve
    hvsr_out['hvsr_peak_indices'] = __find_peaks(hvsr_out['hvsr_curve'])
    
    #Get frequency values at HV peaks in main curve
    hvsrPF=[]
    for p in hvsr_out['hvsr_peak_indices']:
        hvsrPF.append(hvsr_out['x_freqs'][anyK][p])
    hvsr_out['hvsr_peak_freqs'] = np.array(hvsrPF)


    #Get other HVSR parameters (i.e., standard deviations, water levels, etc.)
    hvsr_out = __gethvsrparams(hvsr_out)

    #Include the original obspy stream in the output
    hvsr_out['stream'] = params['stream']

    return hvsr_out

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
        print('Oops, typo somewhere')

    for k in hvsr_out['psd_raw']:
        newTPSD = list(np.ones_like(hvsr_out['psd_raw'][k]))
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
    
    return hvsr_out

#Get an HVSR curve, given an array of x values (freqs), and a dict with psds for three components
def __get_hvsr_curve(x, psd, method, hvsr_dict, verbose=False):
    """ Get an HVSR curve from three components over the same time period/frequency intervals

    Parameters
    ----------
        x   : list or array_like
            x value (frequency or period)
        psd : dict
            Dictionary with psd values for three components. Usually read in as part of hvsr_dict from process_hvsr
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

    params = hvsr_dict
    if method==1 or method =='dfa' or method =='Diffuse Field Assumption':
        print('WARNING: DFA method is currently experimental and not supported')
        for j in range(len(x)-1):
            for time_interval in params['ppsds']['Z']['current_times_used']:
                hvsr_curve_tinterval = []
                params = dfa(params, verbose=verbose)
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
    
    peak_water_level = []
    peak_water_level_p=[]
    hvsrp2=[]
    hvsrm=[]
    peak_water_level_m=[]
    water_level=1.8 #Make this an input parameter eventually!!!****
    
    hvsr_log_std = {}

    peak_water_level.append(water_level)

    hvsr=hvsr_out['hvsr_curve']
    if hvsr_out['ind_hvsr_curves'].shape[0] > 0:
        hvsrp = np.add(hvsr_out['hvsr_curve'], hvsr_out['ind_hvsr_stdDev'])
        hvsrm = np.subtract(hvsr_out['hvsr_curve'], hvsr_out['ind_hvsr_stdDev'])

        hvsr_log_std = np.std(np.log10(hvsr_out['ind_hvsr_curves']), axis=0)
        hvsrp2 = np.multiply(hvsr, np.exp(hvsr_log_std))
        hvsrm2 = np.divide(hvsr, np.exp(hvsr_log_std))

        peak_water_level_p = water_level + hvsr_out['ind_hvsr_stdDev']
        peak_water_level_m = water_level - hvsr_out['ind_hvsr_stdDev']

    newKeys = ['hvsr_log_std', 'peak_water_level', 'peak_water_level_p', 'peak_water_level_m','hvsrp','hvsrm', 'hvsrp2','hvsrm2']
    newVals = [hvsr_log_std,    peak_water_level,   peak_water_level_p,   peak_water_level_m,  hvsrp,  hvsrm,   hvsrp2,  hvsrm2]
    for i, nk in enumerate(newKeys):
        hvsr_out[nk] = np.array(newVals[i])

    return hvsr_out

#Plot Obspy Trace in axis using matplotlib
def plot_stream(stream, params, fig=None, axes=None, return_fig=True):
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

        axes[comp].set_ylim([dmed-0.75*stD, dmed+0.75*stD])
        axes[comp].set_xlim([xmin, xmax])

    fig.suptitle(params['site'])
    
    day = "{}-{}-{}".format(stream[0].stats.starttime.year, stream[0].stats.starttime.month, stream[0].stats.starttime.day)
    axes['E'].set_xlabel('UTC Time \n'+ day)

    #plt.rcParams['figure.dpi'] = 100
    #plt.rcParams['figure.figsize'] = (5,4)
    
    #fig.tight_layout()
    fig.canvas.draw()

    if return_fig:
        return fig, axes
    return                 

def hvplot(hvsr_dict, plot_type='HVSR ann p C+ ann p SPEC', use_subplots=True, xtype='freq', fig=None, ax=None, return_fig=False,  save_dir=None, save_suffix='', show=True, clear_fig=True,**kwargs):
    """Function to plot HVSR data

    Parameters
    ----------
    hvsr_dict : dict                  
        Dictionary containing output from process_hvsr function
    plot_type : str='HVSR' or list    
        The plot_type of plot(s) to plot. If list, will plot all plots listed
        'HVSR' : Standard HVSR plot, including standard deviation
        - '[HVSR] p' : HVSR plot with best peaks shown
        - '[HVSR] p' : HVSR plot with best picked peak shown                
        - '[HVSR] p* all' : HVSR plot with all picked peaks shown                
        - '[HVSR] p* t' : HVSR plot with peaks from all time steps in background                
        - '[HVSR p* ann] : Annotates plot with peaks
        - '[HVSR] -s' : HVSR plots don't show standard deviation
        - '[HVSR] t' : HVSR plot with individual hv curves for each time step shown
        - '[HVSR] c' : HVSR plot with each components' spectra. Recommended to do this last (or just before 'specgram'), since doing c+ can make the component chart its own chart
        'Specgram' : Combined spectrogram of all components
        - '[spec]' : basic spectrogram plot of H/V curve
    use_subplots : bool, default = True
        Whether to output the plots as subplots (True) or as separate plots (False)
    xtype : str, default = 'freq'    
        String for what to use, between frequency or period
            For frequency, the following are accepted (case does not matter): 'f', 'Hz', 'freq', 'frequency'
            For period, the following are accepted (case does not matter): 'p', 'T', 's', 'sec', 'second', 'per', 'period'
    return_fig   : bool
        Whether to return figure and axis objects
    save_dir     : str or None
        Directory in which to save figures
    save_suffix  : str
        Suffix to add to end of figure filename(s), if save_dir is used
    show    : bool
        Whether to show plot
    **kwargs    : keyword arguments
        Keyword arguments for matplotlib.pyplot

    Returns
    -------
    fig, ax : matplotlib figure and axis objects
        Returns figure and axis matplotlib.pyplot objects if return_fig=True, otherwise, simply plots the figures
    """

    if clear_fig and fig is not None and ax is not None: #Intended use for tkinter
        #Clear everything
        for key in ax:
            ax[key].clear()
        fig.clear()


    compList = ['c', 'comp', 'component', 'components']
    specgramList = ['spec', 'specgram', 'spectrogram']
    hvsrList = ['hvsr', 'hv', 'h']

    hvsrInd = np.nan
    compInd = np.nan
    specInd = np.nan

    kList = plot_type.split(' ')
    for i, k in enumerate(kList):
        kList[i] = k.lower()

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
        indListCopy[firstInd] = 99 #high number

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
            fig, ax = plt.subplot_mosaic(mosaicPlots)
            axis = ax[p]
        elif use_subplots:
            ax[p].clear()
            axis = ax[p]
        else:
            fig, axis = plt.subplots()
                
        if p == 'hvsr':
            plot_hvsr(hvsr_dict, fig=fig, ax=axis, plot_type=plotComponents, xtype='x_freqs')
        elif p=='comp':
            plotComponents[0] = plotComponents[0][:-1]
            plot_hvsr(hvsr_dict, fig=fig, ax=axis, plot_type=plotComponents, xtype='x_freqs')
        elif p=='spec':
            plot_specgram_hvsr(hvsr_dict, fig=fig, ax=axis, colorbar=False)
        else:
            print('Error')    
    
    fig.canvas.draw()
    if return_fig:
        return fig, ax
    return

#Plot HVSR data (OLD)
def __old_hvplot(hvsr_dict, plot_type='HVSR', xtype='freq', return_fig=False,  save_dir=None, save_suffix='', show=True,**kwargs):
    """Function to plot HVSR data

        Parameters
        ----------
        hvsr_dict : dict                  
            Dictionary containing output from process_hvsr function
        plot_type : str='HVSR' or list    
            The plot_type of plot(s) to plot. If list, will plot all plots listed
            'HVSR' : Standard HVSR plot, including standard deviation
            - '[HVSR] p' : HVSR plot with best peaks shown
            - '[HVSR] p' : HVSR plot with best picked peak shown                
            - '[HVSR] p* all' : HVSR plot with all picked peaks shown                
            - '[HVSR] p* t' : HVSR plot with peaks from all time steps in background                
            - '[HVSR p* ann] : Annotates plot with peaks
            - '[HVSR] -s' : HVSR plots don't show standard deviation
            - '[HVSR] t' : HVSR plot with individual hv curves for each time step shown
            - '[HVSR] c' : HVSR plot with each components' spectra. Recommended to do this last (or just before 'specgram'), since doing c+ can make the component chart its own chart
            'Specgram' : Combined spectrogram of all components
            - '[spec]' : basic spectrogram plot of H/V curve
        xtype : str, default = 'freq'    
            String for what to use, between frequency or period
                For frequency, the following are accepted (case does not matter): 'f', 'Hz', 'freq', 'frequency'
                For period, the following are accepted (case does not matter): 'p', 'T', 's', 'sec', 'second', 'per', 'period'
        return_fig   : bool
            Whether to return figure and axis objects
        save_dir     : str or None
            Directory in which to save figures
        save_suffix  : str
            Suffix to add to end of figure filename(s), if save_dir is used
        show    : bool
            Whether to show plot
        **kwargs    : keyword arguments
            Keyword arguments for matplotlib.pyplot

        Returns
        -------
        fig, ax : matplotlib figure and axis objects
            Returns figure and axis matplotlib.pyplot objects if return_fig=True, otherwise, simply plots the figures
    """
    #plt.rcParams['figure.dpi'] = 500
    #plt.rcParams['figure.figsize'] = (12, 3)

    freqList = ['F', 'HZ', 'FREQ', 'FREQUENCY']
    perList = 'P', 'T', 'S', 'SEC', 'SECOND' 'PER', 'PERIOD'

    if xtype.upper() in freqList:
        xtype='x_freqs'
    elif xtype.upper() in perList:
        xtype='x_period'
    else:
        print('xtype not valid')
        return
    
    specgramList = ['spec', 'specgram', 'spectrogram']
    hvsrList = ['hvsr', 'hv', 'h']

    kList = plot_type.split(' ')
    chartStr = []
    i = 0
    for k in kList:
        k = k.strip().lower()
        if i == 0 and (k in hvsrList or k in specgramList):
            chartType = k        
        if '+' in k or (k in hvsrList and i > 0) or (k in specgramList and i > 0):
            if chartType in specgramList:
                fig, ax = plot_specgram_hvsr(hvsr_dict, savedir=save_dir, save_suffix=save_suffix, show=show, kwargs=kwargs)
                i=0
            else:
                fig, ax = plot_hvsr(hvsr_dict, plot_type=chartStr, xtype=xtype,  savedir=save_dir, save_suffix=save_suffix, show=show, kwargs=kwargs)                
                i=0

            if '+' in k:
                k = k.replace('+', '')    
                chartStr = [k]
                fig, ax = plot_hvsr(hvsr_dict, plot_type=chartStr, xtype=xtype,  savedir=save_dir, save_suffix=save_suffix, show=show, kwargs=kwargs)
            chartStr = [k]
        else:
            i+=1
            chartStr.append(k)
            
    if len(chartStr) > 0:
        if i == 0 and (k in hvsrList or k in specgramList):
            chartType = k     

        if chartType in specgramList:
            fig, ax = plot_specgram_hvsr(hvsr_dict,  savedir=save_dir, save_suffix=save_suffix, show=show, kwargs=kwargs)
        else:
            fig, ax = plot_hvsr(hvsr_dict, plot_type=chartStr, xtype=xtype,  savedir=save_dir, save_suffix=save_suffix, show=show, kwargs=kwargs)

    if return_fig:
        return fig, ax
    
    return
    
#Plot hvsr curve, private supporting function for hvplot
def plot_hvsr(hvsr_dict, plot_type, xtype, fig=None, ax=None, save_dir=None, save_suffix='', show=True, **kwargs):
    """Private function for plotting hvsr curve (or curves with components)
    """
    if 'kwargs' in kwargs.keys():
        kwargs = kwargs['kwargs']

    if fig is None and ax is None:
        fig, ax = plt.subplots()

    if 'xlim' not in kwargs.keys():
        xlim = hvsr_dict['hvsr_band']
    else:
        xlim = kwargs['xlim']
    
    if 'ylim' not in kwargs.keys():
        ylim = [0, max(hvsr_dict['hvsrp2'])]
    else:
        ylim = kwargs['ylim']
    
    if 'grid' in kwargs.keys():
        plt.grid(which=kwargs['grid'], alpha=0.25)

    if xtype=='x_freqs':
        xlabel = 'Frequency [Hz]'
    else:
        xlabel = 'Period [s]'

    if save_dir is not None:
        filename = hvsr_dict['input_params']['site']
    else:
        filename = ""

    #ax = plt.gca()
    #fig = plt.gcf()

    anyKey = list(hvsr_dict[xtype].keys())[0]
    x = hvsr_dict[xtype][anyKey][:-1]
    y = hvsr_dict['hvsr_curve']
    
    plotSuff=''
    legendLoc = 'upper right'
    
    plotHVSR = False
    for item in plot_type:
        if item.lower()=='hvsr':
            plotHVSR=True
            ax.plot(x, y, color='k', label='H/V Ratio', zorder=1000)
            plotSuff='HVSRCurve_'
            if '-s' not in plot_type:
                ax.fill_between(x, hvsr_dict['hvsrm2'], hvsr_dict['hvsrp2'], color='k', alpha=0.2, label='StDev',zorder=997)
                ax.plot(x, hvsr_dict['hvsrm2'], color='k', alpha=0.25, linewidth=0.5, zorder=998)
                ax.plot(x, hvsr_dict['hvsrp2'], color='k', alpha=0.25, linewidth=0.5, zorder=999)
            else:
                plotSuff = plotSuff+'noStdDev_'
            break

    ax.semilogx()
    ax.set_ylim(ylim)
    ax.set_xlim(xlim)
    ax.set_xlabel(xlabel)
    ax.set_ylabel('H/V Ratio'+'\n['+hvsr_dict['method']+']')
    ax.set_title(hvsr_dict['input_params']['site'])


    for k in plot_type:   
        if k=='p' and 'all' not in plot_type:
            plotSuff=plotSuff+'BestPeak_'
            
            bestPeakScore = 0
            for i, p in enumerate(hvsr_dict['Peak Report']):
                if p['Score'] > bestPeakScore:
                    bestPeakScore = p['Score']
                    bestPeak = p

            ax.axvline(bestPeak['f0'],color='k', linestyle='dotted', label='Peak')          
            if 'ann' in plot_type:
                ax.annotate('Peak at '+str(round(bestPeak['f0'],2))+'Hz', (bestPeak['f0'], ax.get_ylim()[0]), xycoords='data', 
                                horizontalalignment='center', verticalalignment='bottom', 
                                bbox=dict(facecolor='w', edgecolor='none', alpha=0.8, pad=0.1))
                plotSuff = plotSuff+'ann_'

        elif k=='p'  and 'all' in plot_type:
            plotSuff = plotSuff+'allPeaks_'

            ax.vlines(hvsr_dict['hvsr_peak_freqs'], ax.get_ylim()[0], ax.get_ylim()[1], colors='k', linestyles='dotted', label='Peak')          
            if 'ann' in plot_type:
                for i, p in enumerate(hvsr_dict['hvsr_peak_freqs']):
                    y = hvsr_dict['hvsr_curve'][hvsr_dict['hvsr_peak_indices'][i]]
                    ax.annotate('Peak at '+str(round(p,2))+'Hz', (p, 0.1), xycoords='data', 
                                    horizontalalignment='center', verticalalignment='bottom', 
                                    bbox=dict(facecolor='w', edgecolor='none', alpha=0.8, pad=0.1))
                plotSuff=plotSuff+'ann_'

        if 't' in k:
            plotSuff = plotSuff+'allTWinCurves_'

            if k=='tp':
                for j, t in enumerate(hvsr_dict['ind_hvsr_peak_indices']):
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
            for t in hvsr_dict['ind_hvsr_curves']:
                ax.plot(x, t, color='k', alpha=0.15, linewidth=0.8, linestyle=':')

        if 'c' in k:
            plotSuff = plotSuff+'IndComponents_'
            
            if plot_type[0] != 'c':
                fig.tight_layout()
                axis2 = ax.twinx()
                compAxis = axis2
                #axis2 = plt.gca()
                #fig = plt.gcf()
                compAxis.set_ylabel('Amplitude'+'\n[m2/s4/Hz] [dB]')
                compAxis.set_facecolor([0,0,0,0])
                legendLoc2 = 'upper left'
                
            else:
                ax.set_title(hvsr_dict['input_params']['site']+': Individual Components')
                #ax = plt.gca()
                #fig = plt.gcf()
                compAxis = ax
                legendLoc2 = 'upper right'
                
            minY = []
            maxY = []
            for key in hvsr_dict['psd_values_tavg']:
                minY.append(min(hvsr_dict['ppsd_std_vals_m'][key]))
                maxY.append(max(hvsr_dict['ppsd_std_vals_p'][key]))
            minY = min(minY)
            maxY = max(maxY)
            rng = maxY-minY
            pad = rng * 0.05
            ylim = [minY-pad, maxY+pad]
        
            compAxis.set_ylabel('Amplitude'+'\n[m2/s4/Hz] [dB]')
            compAxis.set_ylim(ylim)

            #Modify based on whether there are multiple charts
            if plotHVSR:
                linalpha = 0.2
                stdalpha = 0.05
            else:
                linalpha=1
                stdalpha=0.2
            
            #Plot individual components
            y={}
            for key in hvsr_dict['psd_values_tavg']:
                y[key] = hvsr_dict['psd_values_tavg'][key][:-1]

                if key == 'Z':
                    pltColor = 'k'
                elif key =='E':
                    pltColor = 'b'
                elif key == 'N':
                    pltColor = 'r'

                compAxis.plot(x, y[key], c=pltColor, label=key, alpha=linalpha)
                if '-s' not in plot_type:
                    compAxis.fill_between(x, hvsr_dict['ppsd_std_vals_m'][key][:-1], hvsr_dict['ppsd_std_vals_p'][key][:-1], color=pltColor, alpha=stdalpha)
                if plot_type[0] != 'c':
                    compAxis.legend(loc=legendLoc2)
            else:
                pass#ax.legend(loc=legendLoc)

    bbox = ax.get_window_extent()
    bboxStart = bbox.__str__().find('Bbox(',0,50)+5
    bboxStr = bbox.__str__()[bboxStart:].split(',')[:4]
    axisbox = []
    for i in bboxStr:
        i = i.split('=')[1]
        if ')' in i:
            i = i[:-1]
        axisbox.append(float(i))
    #print(axisbox)
    #print(ax.get_position())

    ax.legend(loc=legendLoc)

    __plot_current_fig(save_dir=save_dir, 
                        filename=filename, 
                        fig=fig, ax=ax,
                        plot_suffix=plotSuff, 
                        user_suffix=save_suffix, 
                        show=show)
    
    return fig, ax

#Private function to help for when to show and format and save plots
def __plot_current_fig(save_dir, filename, fig, ax, plot_suffix, user_suffix, show):
    """Private function to support hvplot, for plotting and showing plots"""
    #plt.gca()
    #plt.gcf()
    #fig.tight_layout() #May need to uncomment this

    #plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)

    if save_dir is not None:
        outFile = save_dir+'/'+filename+'_'+plot_suffix+str(datetime.datetime.today().date())+'_'+user_suffix+'.png'
        fig.savefig(outFile, bbox_inches='tight', pad_inches=0.2)
    if show:
        fig.canvas.draw()#.show()
        fig.tight_layout()
        #plt.ion()
    return

#Plot specgtrogram, private supporting function for hvplot
def plot_specgram_hvsr(hvsr_dict, fig=None, ax=None, save_dir=None, save_suffix='',**kwargs):
    """Private function for plotting average spectrogram of all three channels from ppsds
    """
    if fig is None and ax is None:
        fig, ax = plt.subplots()    

    if 'kwargs' in kwargs.keys():
        kwargs = kwargs['kwargs']

    if 'peak_plot' in kwargs.keys():
        peak_plot=True
        del kwargs['peak_plot']
    else:
        peak_plot=False
        

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

    ppsds = hvsr_dict['ppsds']#[k]['current_times_used']
    import matplotlib.dates as mdates
    anyKey = list(ppsds.keys())[0]

    psdHList =[]
    psdZList =[]
    for k in hvsr_dict['psd_raw']:
        if 'z' in k.lower():
            psdZList.append(hvsr_dict['psd_raw'][k])    
        else:
            psdHList.append(hvsr_dict['psd_raw'][k])
    
    #if detrend:
    #    psdArr = np.subtract(psdArr, np.median(psdArr, axis=0))
    psdArr = hvsr_dict['ind_hvsr_curves'].T

    xmin = datetime.datetime.strptime(min(hvsr_dict['ppsds'][anyKey]['current_times_used'][:-1]).isoformat(), '%Y-%m-%dT%H:%M:%S.%f')
    xmax = datetime.datetime.strptime(max(hvsr_dict['ppsds'][anyKey]['current_times_used'][:-1]).isoformat(), '%Y-%m-%dT%H:%M:%S.%f')
    xmin = mdates.date2num(xmin)
    xmax = mdates.date2num(xmax)

    tTicks = mdates.MinuteLocator(byminute=range(0,60,5))
    ax.xaxis.set_major_locator(tTicks)
    tTicks_minor = mdates.SecondLocator(bysecond=[0])
    ax.xaxis.set_minor_locator(tTicks_minor)

    tLabels = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(tLabels)
    ax.tick_params(axis='x', labelsize=8)

    if hvsr_dict['ppsds'][anyKey]['current_times_used'][0].date != hvsr_dict['ppsds'][anyKey]['current_times_used'][-1].date:
        day = str(hvsr_dict['ppsds'][anyKey]['current_times_used'][0].date)+' - '+str(hvsr_dict['ppsds'][anyKey]['current_times_used'][1].date)
    else:
        day = str(hvsr_dict['ppsds'][anyKey]['current_times_used'][0].date)

    ymin = hvsr_dict['input_params']['hvsr_band'][0]
    ymax = hvsr_dict['input_params']['hvsr_band'][1]

    extList = [xmin, xmax, ymin, ymax]
  
    #ax = plt.gca()
    #fig = plt.gcf()

    freqticks = np.flip(hvsr_dict['x_freqs'][anyKey])
    yminind = np.argmin(np.abs(ymin-freqticks))
    ymaxind = np.argmin(np.abs(ymax-freqticks))
    freqticks = freqticks[yminind:ymaxind]

    #Set up axes, since data is already in semilog
    axy = ax.twinx()
    axy.set_yticks([])
    axy.zorder=0
    ax.zorder=1
    ax.set_facecolor('#ffffff00') #Create transparent background for front axis
    #plt.sca(axy)  
    im = ax.imshow(psdArr, origin='lower', extent=extList, aspect='auto', interpolation='nearest', **kwargs)
    ax.tick_params(left=False, right=False)
    #plt.sca(ax)
    if peak_plot:
        ax.hlines(hvsr_dict['Best Peak']['f0'], xmin, xmax, colors='k', linestyles='dashed', alpha=0.5)

    #FreqTicks =np.arange(1,np.round(max(hvsr_dict['x_freqs'][anyKey]),0), 10)
    ax.set_title(hvsr_dict['input_params']['site']+': Spectrogram')
    ax.set_xlabel('UTC Time \n'+day)
    
    if colorbar:
        cbar = plt.colorbar(mappable=im)
        cbar.set_label('H/V Ratio')

    ax.set_ylabel(ylabel)
    ax.set_yticks(freqticks)
    ax.semilogy()
    ax.set_ylim(hvsr_dict['input_params']['hvsr_band'])

    #plt.rcParams['figure.dpi'] = 500
    #plt.rcParams['figure.figsize'] = (12,4)
    fig.canvas.draw()
    #fig.tight_layout()
    #plt.show()
    return fig, ax

#Plot spectrogram from stream
def plot_specgram_stream(stream, params=None, component='Z', stack_type='linear', detrend='mean', dbscale=True, fill_gaps=None, return_fig=True, fig=None, ax=None, cmap_per=[0.1,0.9], **kwargs):
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

    if fig is None and ax is None:
        #Organize the chart layout
        mosaic = [['spec'],['spec'],['spec'],
                ['spec'],['spec'],['spec'],
                ['signalz'],['signalz'], ['signaln'], ['signale']]
        fig, ax = plt.subplot_mosaic(mosaic, sharex=True)  
        #fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True)  
    
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
    vmin = np.percentile(array_displayed, cmap_per[0]*100)
    vmax = np.percentile(array_displayed, cmap_per[1]*100)
    
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
        ax[key].set_ylim([dmed-5*stD, dmed+5*stD])
    
    if params is None:
        fig.suptitle('HVSR Site: Spectrogram and Data')
    elif 'title' in kwargs.keys():
        fig.suptitle(kwargs['title'])
    else:
        if 'input_params' in params.keys():
            sitename = params['input_params']['site']
        else:
            sitename = params['site']
        fig.suptitle('{}: Spectrogram and Data'.format(sitename))
    
    day = "{}-{}-{}".format(stream[0].stats.starttime.year, stream[0].stats.starttime.month, stream[0].stats.starttime.day)
    ax['signale'].set_xlabel('UTC Time \n'+day)

    #plt.rcParams['figure.dpi'] = 100
    #plt.rcParams['figure.figsize'] = (5,4)
    
    #fig.tight_layout()
    fig.canvas.draw()
    
    if return_fig:
        return fig, ax
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

#Quality checks, stability tests, clarity tests
#def check_peaks(hvsr, x, y, index_list, peak, peakm, peakp, hvsr_peaks, stdf, hvsr_log_std, rank, hvsr_band=[0.4, 40], peak_water_level=1.8, do_rank=False):
def check_peaks(hvsr_dict, hvsr_band=[0.4, 40], peak_water_level=1.8):
    """Function to run tests on HVSR peaks to find best one and see if it passes quality checks

        Parameters
        ----------
        hvsr_dict : dict
            Dictionary containing all the calculated information about the HVSR data (i.e., hvsr_out returned from process_hvsr)
        hvsr_band  : tuple or list, default=[0.4, 40]
            2-item tuple or list with lower and upper limit of frequencies to analyze
        peak_water_level: float, default=1.8
            Value of peak water level

        Returns
        -------
        hvsr_dict   : dict
            Dictionary containing previous input data, plus information about Peak tests
    """

    if not hvsr_band:
        hvsr_band = [0.4,40]
    hvsr_dict['hvsr_band'] = hvsr_band

    anyK = list(hvsr_dict['x_freqs'].keys())[0]
    x = hvsr_dict['x_freqs'][anyK]
    y = hvsr_dict['hvsr_curve']
    index_list = hvsr_dict['hvsr_peak_indices']
    peak_water_level  = hvsr_dict['peak_water_level']
    hvsrp = hvsr_dict['hvsrp']
    peak_water_level_p  = hvsr_dict['peak_water_level_p']
    hvsrm = hvsr_dict['hvsrm']
    hvsrPeaks = hvsr_dict['ind_hvsr_peak_indices']
    hvsr_log_std = hvsr_dict['hvsr_log_std']

    #Do for hvsr
    peak = __init_peaks(x, y, index_list, hvsr_band, peak_water_level)

    peak = __check_curve_reliability(hvsr_dict, peak)
    peak = __check_clarity(x, y, peak, do_rank=True)

    #Do for hvsrp
    # Find  the relative extrema of hvsrp (hvsr + 1 standard deviation)
    if not np.isnan(np.sum(hvsrp)):
        index_p = __find_peaks(hvsrp)
    else:
        index_p = list()

    peakp = __init_peaks(x, hvsrp, index_p, hvsr_band, peak_water_level_p)
    peakp = __check_clarity(x, hvsrp, peakp, do_rank=True)

    #Do for hvsrm
    # Find  the relative extrema of hvsrm (hvsr - 1 standard deviation)
    if not np.isnan(np.sum(hvsrm)):
        index_m = __find_peaks(hvsrm)
    else:
        index_m = list()

    peak_water_level_m  = hvsr_dict['peak_water_level_m']

    peakm = __init_peaks(x, hvsrm, index_m, hvsr_band, peak_water_level_m)
    peakm = __check_clarity(x, hvsrm, peakm, do_rank=True)

    stdf = __get_stdf(x, index_list, hvsrPeaks)

    peak = __check_freq_stability(peak, peakm, peakp)
    peak = __check_stability(stdf, peak, hvsr_log_std, rank=True)

    hvsr_dict['Peak Report'] = peak

    #Iterate through peaks and 
    #   Get the best peak based on the peak score
    #   Calculate whether each peak passes enough tests
    curveTests = ['Window Length Freq.','Significant Cycles', 'Low Curve StDev. over time']
    peakTests = ['Peak Freq. Clarity Below', 'Peak Freq. Clarity Above', 'Peak Amp. Clarity', 'Freq. Stability', 'Peak Stability (freq. std)', 'Peak Stability (amp. std)']
    bestPeakScore = 0
    for p in hvsr_dict['Peak Report']:
        #Get best peak
        if p['Score'] > bestPeakScore:
            bestPeakScore = p['Score']
            bestPeak = p

        #Calculate if peak passes criteria
        cTestsPass = 0
        pTestsPass = 0
        for testName in p['Pass List'].keys():
            if testName in curveTests:
                if p['Pass List'][testName]:
                    cTestsPass += 1
            elif testName in peakTests:
                if p['Pass List'][testName]:
                    pTestsPass += 1

        if cTestsPass == 3 and pTestsPass >= 5:
            p['Peak Passes'] = True
        else:
            p['Peak Passes'] = False
        
    #Designate best peak in output dict
    if len(hvsr_dict['Peak Report']) == 0:
        bestPeak={}
        print('No Best Peak identified')

    hvsr_dict['Best Peak'] = bestPeak
    return hvsr_dict

#Initialize peaks
def __init_peaks(_x, _y, _index_list, _hvsr_band, _peak_water_level):
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
            Two-item list with low and high frequency to limit assessment extent
        _peak_water_level : float
            Peak water level value
        
        Returns
        -------
        _peak               : list 
            List of dictionaries, one for each input peak
    """
    _peak = list()
    for _i in _index_list:
        if _y[_i] > _peak_water_level[0] and (_hvsr_band[0] <= _x[_i] <= _hvsr_band[1]):
            _peak.append({'f0': float(_x[_i]), 'A0': float(_y[_i]), 
                          'f-': None, 'f+': None, 'Sf': None, 'Sa': None,
                          'Score': 0, 
                          'Report': {'Lw':'', 'Nc':'', 'σ_A(f)':'', 'A(f-)':'', 'A(f+)':'', 'A0': '', 'P+': '', 'P-': '', 'Sf': '', 'Sa': ''},
                          'Pass List':{},
                          'Peak Passes':False})
    return _peak

#Check reliability of HVSR of curve
def __check_curve_reliability(hvsr_dict, _peak):
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
    hvsr_dict   : dict
        Dictionary containing all important information generated about HVSR curve
    _peak       : list
        A list of dictionaries, with each dictionary containing information about each peak

    Returns
    -------
    _peak   : list
        List of dictionaries, same as above, except with information about curve reliability tests added
    """
    anyKey = list(hvsr_dict['ppsds'].keys())[0]#Doesn't matter which channel we use as key

    delta = hvsr_dict['ppsds'][anyKey]['delta']
    window_len = (hvsr_dict['ppsds'][anyKey]['len'] * delta) #Window length in seconds
    window_num = np.array(hvsr_dict['psd_raw'][anyKey]).shape[0]

    for _i in range(len(_peak)):
        peakFreq= _peak[_i]['f0']
        test1 = peakFreq > 10/window_len

        nc = window_len * window_num * peakFreq
        test2 = nc > 200

        halfF0 = peakFreq/2
        doublef0 = peakFreq*2
        
        test3 = True
        failCount = 0
        for i, freq in enumerate(hvsr_dict['x_freqs'][anyKey][:-1]):
            ###IS THIS RIGHT???
            if freq >= halfF0 and freq <doublef0:
                if peakFreq >= 0.5:
                    if hvsr_dict['hvsr_log_std'][i] >= 2:
                        test3=False
                        failCount +=1
                else: #if peak freq is less than 0.5
                    if hvsr_dict['hvsr_log_std'][i] >= 3:
                        test3=False
                        failCount +=1

        if test1:
            _peak[_i]['Report']['Lw'] = '{} > 10 / {}  {}'.format(round(peakFreq,3), int(window_len), check_mark())
        else:
            _peak[_i]['Report']['Lw'] = '{} > 10 / {}  {}'.format(round(peakFreq,3), int(window_len), '✘')

        if test2:
            _peak[_i]['Report']['Nc'] = '{} > 200  {}'.format(round(nc,0), check_mark())
        else:
            _peak[_i]['Report']['Nc'] = '{} > 200  {}'.format(round(nc,0), '✘')

        if test3:
            if peakFreq >= 0.5:
                compVal = 2
            else:
                compVal = 3
            _peak[_i]['Report']['σ_A(f)'] = 'σ_A for all freqs {}-{} < {}  {}'.format(round(peakFreq*0.5, 3), round(peakFreq*2, 3), compVal, check_mark())
        else:
            _peak[_i]['Report']['σ_A(f)'] = 'σ_A for all freqs {}-{} < {}  {}'.format(round(peakFreq*0.5, 3), round(peakFreq*2, 3), compVal, '✘')

        _peak[_i]['Pass List']['Window Length Freq.'] = test1
        _peak[_i]['Pass List']['Significant Cycles'] = test2
        _peak[_i]['Pass List']['Low Curve StDev. over time'] = test3
    return _peak

#Check clarity of peaks
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
        _peak[_i]['f-'] = '✘'
        _peak[_i]['Report']['A(f-)'] = 'No A_h/v in freqs {}-{} < {}  {}'.format(round(_peak[_i]['A0']/4, 3), round(_peak[_i]['A0'], 3), round(_peak[_i]['A0']/2, 3), '✘')
        _peak[_i]['Pass List']['Peak Freq. Clarity Below'] = False #Start with assumption that it is False until we find an instance where it is True
        for _j in range(jstart, -1, -1):
            # There exist one frequency f-, lying between f0/4 and f0, such that A0 / A(f-) > 2.
            if (float(_peak[_i]['f0']) / 4.0 <= _x[_j] < float(_peak[_i]['f0'])) and float(_peak[_i]['A0']) / _y[_j] > 2.0:
                _peak[_i]['Score'] += 1
                _peak[_i]['f-'] = '%10.3f %1s' % (_x[_j], check_mark())
                _peak[_i]['Report']['A(f-)'] = 'A({}): {} < {}  {}'.format(round(_x[_j], 3), round(_y[_j], 3), round(_peak[_i]['A0']/2,3), check_mark())
                _peak[_i]['Pass List']['Peak Freq. Clarity Below'] = True
                break
            else:
                pass
    
    if do_rank:
        max_rank += 1
    for _i in range(len(_peak)):
        #Initialize as False
        _peak[_i]['f+'] = '✘'
        _peak[_i]['Report']['A(f+)'] = 'No A_h/v in freqs {}-{} < {}  {}'.format(round(_peak[_i]['A0'], 3), round(_peak[_i]['A0']*4, 3), round(_peak[_i]['A0']/2, 3), '✘')
        _peak[_i]['Pass List']['Peak Freq. Clarity Above'] = False
        for _j in range(len(_x) - 1):

            # There exist one frequency f+, lying between f0 and 4*f0, such that A0 / A(f+) > 2.
            if float(_peak[_i]['f0']) * 4.0 >= _x[_j] > float(_peak[_i]['f0']) and \
                    float(_peak[_i]['A0']) / _y[_j] > 2.0:
                _peak[_i]['Score'] += 1
                _peak[_i]['f+'] = '%10.3f %1s' % (_x[_j], check_mark())
                _peak[_i]['Report']['A(f+)'] = 'A({}): {} < {}  {}'.format(round(_x[_j], 3), round(_y[_j], 3), round(_peak[_i]['A0']/2,3), check_mark())
                _peak[_i]['Pass List']['Peak Freq. Clarity Above'] = True
                break
            else:
                pass
#        if False in clarityPass:
#            _peak[_i]['Pass List']['Peak Freq. Clarity Below'] = False
#        else:
#            _peak[_i]['Pass List']['Peak Freq. Clarity Above'] = True

    #Amplitude Clarity test
    # Only peaks with A0 > 2 pass
    if do_rank:
        max_rank += 1
    _a0 = 2.0
    for _i in range(len(_peak)):

        if float(_peak[_i]['A0']) > _a0:
            _peak[_i]['Report']['A0'] = '%10.2f > %0.1f %1s' % (_peak[_i]['A0'], _a0, check_mark())
            _peak[_i]['Score'] += 1
            _peak[_i]['Pass List']['Peak Amp. Clarity'] = True
        else:
            _peak[_i]['Report']['A0'] = '%10.2f > %0.1f %1s' % (_peak[_i]['A0'], _a0, '✘')
            _peak[_i]['Pass List']['Peak Amp. Clarity'] = False

    return _peak

#Check the stability of the frequency peak
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

    #
    # check σf and σA
    #
    max_rank += 1

    #First check below
    _found_m = list()
    for _i in range(len(_peak)):
        _dx = 1000000.
        _found_m.append(False)
        _peak[_i]['Report']['P-'] = '✘'
        for _j in range(len(_peakm)):
            if abs(_peakm[_j]['f0'] - _peak[_i]['f0']) < _dx:
                _index = _j
                _dx = abs(_peakm[_j]['f0'] - _peak[_i]['f0'])
            if _peak[_i]['f0'] * 0.95 <= _peakm[_j]['f0'] <= _peak[_i]['f0'] * 1.05:
                _peak[_i]['Report']['P-'] = '%0.3f within ±5%s of %0.3f %1s' % (_peakm[_j]['f0'], '%',
                                                                                 _peak[_i]['f0'], check_mark())
                _found_m[_i] = True
                break
        if _peak[_i]['Report']['P-'] == '✘':
            _peak[_i]['Report']['P-'] = '%0.3f within ±5%s of %0.3f %1s' % (_peakm[_j]['f0'], '%', ##changed i to j
                                                                             _peak[_i]['f0'], '✘')

    #Then Check above
    _found_p = list()
    for _i in range(len(_peak)):
        _dx = 1000000.
        _found_p.append(False)
        _peak[_i]['Report']['P+'] = '✘'
        for _j in range(len(_peakp)):
            if abs(_peakp[_j]['f0'] - _peak[_i]['f0']) < _dx:
                _index = _j
                _dx = abs(_peakp[_j]['f0'] - _peak[_i]['f0'])
            if _peak[_i]['f0'] * 0.95 <= _peakp[_j]['f0'] <= _peak[_i]['f0'] * 1.05:
                if _found_m[_i]:
                    _peak[_i]['Report']['P+'] = '%0.3f within ±5%s of %0.3f %1s' % (
                        _peakp[_j]['f0'], '%', _peak[_i]['f0'], check_mark())
                    _peak[_i]['Score'] += 1
                    _peak[_i]['Pass List']['Freq. Stability'] = True
                else:
                    _peak[_i]['Report']['P+'] = '%0.3f within ±5%s of %0.3f %1s' % (
                        _peakp[_j]['f0'], '%', _peak[_i]['f0'], '✘')
                    _peak[_i]['Pass List']['Freq. Stability'] = False
                break
            else:
                _peak[_i]['Report']['P+'] = '%0.3f within ±5%s of %0.3f %1s' % (_peakp[_j]['f0'], '%', _peak[_i]['f0'], '✘')
                _peak[_i]['Pass List']['Freq. Stability'] = False                
        if _peak[_i]['Report']['P+'] == '✘' and len(_peakp) > 0:
            _peak[_i]['Report']['P+'] = '%0.3f within ±5%s of %0.3f %1s' % (
                _peakp[_j]['f0'], '%', _peak[_i]['f0'], '✘')###changed i to j

    return _peak

#Check stability
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

    peakPassList = []
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
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s' % (_stdf[_i], _e, _this_peak['f0'],
                                                                            check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (freq. std)'] = True

            else:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f  %1s' % (_stdf[_i], _e, _this_peak['f0'], '✘')
                _this_peak['Pass List']['Peak Stability (freq. std)'] = False

            _t = 0.48
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f %1s' % (_hvsr_log_std[_i], _t,
                                                                    check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (amp. std)'] = True
            else:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f  %1s' % (_hvsr_log_std[_i], _t, '✘')
                _this_peak['Pass List']['Peak Stability (amp. std)'] = False

        elif 0.2 <= _this_peak['f0'] < 0.5:
            _e = 0.2
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s' % (_stdf[_i], _e, _this_peak['f0'],
                                                                            check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (freq. std)'] = True
            else:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f  %1s' % (_stdf[_i], _e, _this_peak['f0'], '✘')
                _this_peak['Pass List']['Peak Stability (freq. std)'] = False

            _t = 0.40
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f %1s' % (_hvsr_log_std[_i], _t,
                                                                    check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (amp. std)'] = True
            else:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f  %1s' % (_hvsr_log_std[_i], _t, '✘')
                _this_peak['Pass List']['Peak Stability (amp. std)'] = False

        elif 0.5 <= _this_peak['f0'] < 1.0:
            _e = 0.15
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s' % (_stdf[_i], _e, _this_peak['f0'],
                                                                            check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (freq. std)'] = True
            else:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f  %1s' % (_stdf[_i], _e, _this_peak['f0'], '✘')
                _this_peak['Pass List']['Peak Stability (freq. std)'] = False

            _t = 0.3
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f %1s' % (_hvsr_log_std[_i], _t, check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (amp. std)'] = True
            else:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f  %1s' % (_hvsr_log_std[_i], _t, '✘')
                _this_peak['Pass List']['Peak Stability (amp. std)'] = False

        elif 1.0 <= _this_peak['f0'] <= 2.0:
            _e = 0.1
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s' % (_stdf[_i], _e, _this_peak['f0'],
                                                                            check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (freq. std)'] = True
            else:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s ' % (_stdf[_i], _e, _this_peak['f0'], '✘')
                _this_peak['Pass List']['Peak Stability (freq. std)'] = False

            _t = 0.25
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f %1s' % (_hvsr_log_std[_i], _t, check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (amp. std)'] = True
            else:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f  %1s' % (_hvsr_log_std[_i], _t, '✘')
                _this_peak['Pass List']['Peak Stability (amp. std)'] = False

        elif _this_peak['f0'] > 0.2:
            _e = 0.05
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s' % (_stdf[_i], _e, _this_peak['f0'],
                                                                            check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (freq. std)'] = True
            else:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f  %1s' % (_stdf[_i], _e, _this_peak['f0'], '✘')
                _this_peak['Pass List']['Peak Stability (freq. std)'] = False

            _t = 0.2
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f %1s' % (_hvsr_log_std[_i], _t, check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (amp. std)'] = True
            else:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f  %1s' % (_hvsr_log_std[_i], _t, '✘')
                _this_peak['Pass List']['Peak Stability (freq. std)'] = False

    return _peak

#Get frequency standard deviation
def __get_stdf(x_values, indexList, hvsrPeaks):
    """Private function to get frequency standard deviation, from multiple time-step HVSR curves"""
    stdf = list()
    for index in indexList:
        point = list()
        for j in range(len(hvsrPeaks)):
            p = None
            for k in range(len(hvsrPeaks[j])):
                if p is None:
                    p = hvsrPeaks[j][k]
                else:
                    #Find closest peak in current time to (current) main hvsr peak
                    if abs(index - hvsrPeaks[j][k]) < abs(index - p):
                        p = hvsrPeaks[j][k]
            if p is not None:
                point.append(p)
        point.append(index)
        v = list()
        for l in range(len(point)):
            v.append(x_values[point[l]])
        stdf.append(np.std(v))
    return stdf

#Get or print report
def get_report(hvsr_results, export='', format='print', plot_type='HVSR p ann C+ p ann Spec', return_results=False, save_figs=None):
    """Print a report of the HVSR analysis (not currently implemented)
        
    Parameters
    ----------
    hvsr_results : dict
        Dictionary containing all the information about the processed hvsr data
    format : {'csv', 'print', 'docx'}
        Format in which to print or export the report.
    export : str
        Filepath path for export. If not specified, report name is generated automatically and placed in current directory
    include : str or list, default='peak'
        What to include in the report. By default includes all the following
            - Site name
            - Acquisition Date
            - Longitude
            - Latitude
            - Elevation
            - Primary peak frequency
            - Whether passed quality tests (x6)
        For docx (not yet implemented), the following are also included:
            - Figure with spectrogram
            - Figure with HVSR curve
            - Figure with 3 components
    """
    #print statement
    #Check if results are good
    #Curve pass?
    curvePass = (hvsr_results['Best Peak']['Pass List']['Window Length Freq.'] +
                         hvsr_results['Best Peak']['Pass List']['Significant Cycles']+
                         hvsr_results['Best Peak']['Pass List']['Low Curve StDev. over time']) > 2
    
    #Peak Pass?
    peakPass = ( hvsr_results['Best Peak']['Pass List']['Peak Freq. Clarity Below'] +
                hvsr_results['Best Peak']['Pass List']['Peak Freq. Clarity Above']+
                hvsr_results['Best Peak']['Pass List']['Peak Amp. Clarity']+
                hvsr_results['Best Peak']['Pass List']['Freq. Stability']+
                hvsr_results['Best Peak']['Pass List']['Peak Stability (freq. std)']+
                hvsr_results['Best Peak']['Pass List']['Peak Stability (amp. std)']) >= 5
        
    
    if format=='print':
        #Print results
        print('Site:',hvsr_results['input_params']['site'])
        print('Acquisition Date:', hvsr_results['input_params']['acq_date'])
        print('Site Location:', hvsr_results['input_params']['longitude'], hvsr_results['input_params']['latitude'])
        print('Elevation:',hvsr_results['input_params']['elevation'])
        print()
        print('{0:.3f} Hz Peak Frequency'.format(hvsr_results['Best Peak']['f0']))        
        if curvePass and peakPass:
            print('✔ Curve at {0:.3f} Hz passed quality checks! :D'.format(hvsr_results['Best Peak']['f0']))
        else:
            print('✘ Peak at {0:.3f} Hz did NOT pass quality checks :('.format(hvsr_results['Best Peak']['f0']))            

        #Print individual results
        print('\tCurve Tests:')
        print('\t\t', hvsr_results['Best Peak']['Report']['Lw'][-1], 'Length of processing windows:', hvsr_results['Best Peak']['Report']['Lw'])
        print('\t\t', hvsr_results['Best Peak']['Report']['Nc'][-1], 'Number of significant cycles:', hvsr_results['Best Peak']['Report']['Nc'])
        print('\t\t', hvsr_results['Best Peak']['Report']['σ_A(f)'][-1], 'Low StDev. of H/V Curve over time:', hvsr_results['Best Peak']['Report']['σ_A(f)'])


        print('\tPeak Tests:')
        print('\t\t', hvsr_results['Best Peak']['Report']['A(f-)'][-1], 'Clarity Below Peak Frequency:', hvsr_results['Best Peak']['Report']['A(f-)'])
        print('\t\t', hvsr_results['Best Peak']['Report']['A(f+)'][-1], 'Clarity Above Peak Frequency:',hvsr_results['Best Peak']['Report']['A(f+)'])
        print('\t\t', hvsr_results['Best Peak']['Report']['A0'][-1], 'Clarity of Peak Amplitude:',hvsr_results['Best Peak']['Report']['A0'])
        if hvsr_results['Best Peak']['Pass List']['Freq. Stability']:
            res = '✔'
        else:
            res = '✘'
        print('\t\t', res, 'Stability of Peak Freq. Over time:', hvsr_results['Best Peak']['Report']['P-'][:5] + ' and ' + hvsr_results['Best Peak']['Report']['P+'][:-1], res)
        print('\t\t', hvsr_results['Best Peak']['Report']['Sf'][-1], 'Stability of Peak (Freq. StDev):', hvsr_results['Best Peak']['Report']['Sf'])
        print('\t\t', hvsr_results['Best Peak']['Report']['Sa'][-1], 'Stability of Peak (Amp. StDev):', hvsr_results['Best Peak']['Report']['Sa'])

    elif format=='csv':
        import pandas as pd
        pdCols = ['Site Name', 'Acqusition Date', 'Longitude', 'Latitide', 'Elevation', 'Peak Frequency', 
                  'Window Length Freq.','Significant Cycles','Low Curve StDev. over time',
                  'Peak Freq. Clarity Below','Peak Freq. Clarity Above','Peak Amp. Clarity','Freq. Stability', 'Peak Stability (freq. std)','Peak Stability (amp. std)', 'Peak Passes']
        d = hvsr_results
        criteriaList = []
        for p in hvsr_results['Best Peak']["Pass List"]:
            criteriaList.append(hvsr_results['Best Peak']["Pass List"][p])
        criteriaList.append(hvsr_results['Best Peak']["Peak Passes"])
        dfList = [[d['input_params']['site'], d['input_params']['acq_date'], d['input_params']['longitude'], d['input_params']['latitude'], d['input_params']['elevation'], round(d['Best Peak']['f0'], 3)]]
        dfList[0].extend(criteriaList)
        outDF = pd.DataFrame(dfList, columns=pdCols)
        if export=='':
            inFile = pathlib.Path(hvsr_results['input_params'][' datapath'])
            if inFile.is_dir():
                inFile = inFile.as_posix()
                if inFile[-1]=='/':
                    pass
                else:
                    inFile = inFile + '/'
                fname = hvsr_results['input_params']['site']+'_'+str(hvsr_results['input_params']['acq_date'])+'_'+str(hvsr_results['input_params']['starttime'].time)[:5]+'-'+str(hvsr_results['input_params']['endtime'].time)[:5]
                inFile = inFile + fname +'.csv'
            elif inFile.is_file():
                export = inFile.with_suffix('.csv')
        outDF.to_csv(export, index_label='ID')
        return outDF
    elif format=='plot':
        hvsr_results['HV_Plot']=hvplot(hvsr_results, plot_type=plot_type)
        if return_results:
            return hvsr_results

    if export:
        pass
        #code to write to output file
    return
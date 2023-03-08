"""
This module contains all the functions needed to run the HVSR analysis
"""


import datetime
import math
import os
import pathlib
import sys
import tempfile
import warnings
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy

#Main variables
greek_chars = {'sigma': u'\u03C3', 'epsilon': u'\u03B5', 'teta': u'\u03B8'}
channel_order = {'Z': 0, '1': 1, 'N': 1, '2': 2, 'E': 2}
separator_character = '='

t0 = datetime.datetime.now().time()
max_rank = 0
plotRows = 4


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
def __formatTime(inputDT, tzone='utc', dst=True):
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
    dst     : bool=True 
        If any string aside from 'utc' is specified for tzone, this will adjust according to daylight savings time. 
            If tzone is int, no adjustment is made

    Returns
    -------
    outputTimeObj   : datetime object in UTC

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
            
            if '.' in timeStrList[2]:
                microS = int(timeStrList[2].split('.')[1])
                timeStrList[2] = timeStrList[2].split('.')[0]

            hour = int(timeStrList[0])
            minute=int(timeStrList[1])
            sec = int(timeStrList[2])

        outputTimeObj = datetime.datetime(year=int(year),month=int(month), day=int(day),
                                hour=int(hour), minute=int(minute), second=int(sec), microsecond=int(microS))

    elif type(inputDT) is datetime.datetime or type(inputDT) is datetime.time:
        outputTimeObj = inputDT

    if type(tzone) is int: #Plus/minus needs to be correct there
        outputTimeObj = outputTimeObj-datetime.timedelta(hours=tzone)
    elif type(tzone) is str:
        if tzone != 'utc':
            utc_time = datetime.datetime.utcnow()
            localTime = datetime.datetime.now()
            utcOffset = utc_time-localTime
            outputTimeObj=outputTimeObj+utcOffset
            utcOffset = utc_time-localTime
            outputTimeObj = outputTimeObj+utcOffset
            if dst:
                outputTimeObj = outputTimeObj+datetime.timedelta(hours=1)

    return outputTimeObj

#Sort Channels later
def __sortchannels(channels=['EHZ', 'EHN', 'EHE']):
    """"Private function to sort channels. Not currently used
    
    Sort channels. Z/vertical should be first, horizontal order doesn't matter, but N 2nd and E 3rd is default
        Parameters
        ----------
        channels    : list = ['EHZ', 'EHN', 'EHE']
    """
    channel_order = {'Z': 0, '1': 1, 'N': 1, '2': 2, 'E': 2}

    sorted_channel_list = channels.copy()
    for channel in channels:
        sorted_channel_list[channel_order[channel[2]]] = channel
    return sorted_channel_list

#Define input parameters
def input_param( site,
                        network='AM', 
                        station='RAC84', 
                        loc='00', 
                        channels=['EHZ', 'EHN', 'EHE'],
                        acq_date=str(datetime.datetime.now().date()),
                        starttime = '00:00:00.00',
                        endtime = '23:59:59.999',
                        tzone = 'UTC',
                        dst = True,
                        lon = -88.2290526,
                        lat =  40.1012122,
                        elevation = 755,
                        depth = 0,
                        instrument = 'Raspberry Shake',
                        dataPath = '',
                        metaPath = '',
                        hvsr_band = [0.4, 40] 
                        ):
    """Function for designating input parameters for reading in and processing data
    
    Parameters
    ----------
    site : str
        Site name as designated by scientist for ease of reference.
    network : str, default='AM'
        The network designation of the seismometer. This is necessary for data from Raspberry Shakes.
    station : str, default='RAC84'
        The station name of the seismometer. This is necessary for data from Raspberry Shakes.
    loc : str, default='00'
        Location information of the seismometer.
    channels : list, default=['EHZ', 'EHN', 'EHE']
        The three channels used in this analysis, as a list of strings. Preferred that Z component is first, but not necessary
    acq_date : str, int, date object, or datetime object
        If string, preferred format is 'YYYY-MM-DD'. 
        If int, this will be interpreted as the day of year of current year (e.g., 33 would be Feb 2 of current year)
        If date or datetime object, this will be the date. Make sure to account for time change when converting to UTC.
    starttime : str, time object, or datetime object, default='00:00:00.00'
        Start time of data stream. This is necessary for Raspberry Shake data.
    endttime : str, time obejct, or datetime object, default='23:59:99.99'
        End time of data stream. This is necessary for Raspberry Shake data.
    tzone : str or int, default = 'UTC'
        Timezone of input data. If string, 'UTC' will use the time as input directly. Any other value will assume local time of computer.
        If int, should be the int value of the UTC offset (e.g., for American Eastern Standard Time: -5). 
        This is necessary for Raspberry Shake data.
    dst : bool, default=True
        If str used for timezone, this will adjust for daylight savings time. This is necessary for Raspberry Shake data.
    lon : float, default=-88.2290526
        Longitude of data point
    lat : float, default=40.1012122
        Latitude of data point
    elevation : float, default=755
        Surface elevation of data point.
    depth : float, default=0
        Depth of seismometer.
    instrument : str or list {'Raspberry Shake')
        Instrument from which the data was acquired. If multiple points are analyzed, a list can designate between different instrument types.
    dataPath : str or pathlib.Path object
        Filepath of data
    metaPath : str or pathlib.Path object
        Filepath of metadata, in format supported by obspy.read_inventory
    hvsr_band : list, default=[0.4, 40]
        Two-element list containing low and high frequencies of processing. This can also be changed later.
    
    Returns
    -------
    inputParamDict : dict
        Dictionary containing input parameters, including data file path and metadata path. This will be used as an input to other functions.

    """
    global obspy
    import obspy

    #Make Sure metapath is all good
    if not pathlib.Path(metaPath).exists() or metaPath=='':
        if metaPath == '':
            print('No metadata file specified!')
        else:
            print('Specified metadata file cannot be read!')
        repoDir = str(pathlib.Path.cwd())
        repoDir = repoDir.replace('\\', '/').replace('\\'[0], '/')
        metaPath=repoDir+'/resources/raspshake_metadata.inv'
        print('Using default metadata file for Raspberry Shake v.7 contained in repository at\n', metaPath)
    else:
        metaPath = str(metaPath)

    #Reformat time
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
            date=starttime.split('T')[0]
            starttime = starttime.split('T')[1]
    elif type(starttime) is datetime.datetime:
        date = str(starttime.date())
        starttime = str(starttime.time())
    elif type(starttime) is datetime.time():
        starttime = str(starttime)
    
    starttime = date+"T"+starttime
    starttime = obspy.UTCDateTime(__formatTime(starttime, tzone=tzone, dst=dst))

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
    endtime = obspy.UTCDateTime(__formatTime(endtime, tzone=tzone, dst=dst))

    acq_date = datetime.date(year=int(date.split('-')[0]), month=int(date.split('-')[1]), day=int(date.split('-')[2]))
    raspShakeInstNameList = ['raspberry shake', 'shake', 'raspberry', 'rs', 'rs3d', 'rasp. shake', 'raspshake']
    if instrument.lower() in  raspShakeInstNameList:
        if metaPath == r'resources/raspshake_metadata.inv':
            metadir = str(pathlib.Path(os.getcwd())).replace('\\', '/')
            metadir = metadir.replace('\\'[0], '/')
            metaPath = str(pathlib.Path(os.getcwd()))+'/'+metaPath

    inputParamDict = {'net':network,'sta':station, 'loc':loc, 'cha':channels, 'instrument':instrument,
                    'acq_date':acq_date,'starttime':starttime,'endtime':endtime, 'timezone':'UTC',
                    'longitude':lon,'latitude':lat,'elevation':elevation,'depth':depth, 'site':site,
                    'dataPath':dataPath, 'metaPath':metaPath, 'hvsr_band':hvsr_band
                    }

    return inputParamDict

#Read in metadata .inv file, specifically for RaspShake
def update_shake_metadata(filepath, params, write_path=''):
    """Reads static metadata file provided for Rasp Shake and updates with input parameters

        PARAMETERS
        ----------
        filepath    : str or pathlib.Path object
            Filepath to Raspberry Shake metadata file 
        params      : dict
            Dictionary containing necessary keys/values for updating
                Necessary keys: 'net', 'sta', 
                Optional keys: 'longitude', 'latitude', 'elevation', 'depth'
        write_path   : str, optional
            If specified, filepath to write to updated inventory file to

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
    lon = str(params['longitude'])
    lat = str(params['latitude'])
    elevation = str(params['elevation'])
    depth = str(params['depth'])
    
    startdate = str(datetime.datetime(year=2023, month=2, day=15)) #First day with working code
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
        item.text = lat

    for item in root.iter(prefix+'Longitude'):
        item.text = lon

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
        tree.write(write_path, xml_declaration=True, method='xml',encoding='UTF-8')
        inv = obspy.read_inventory(write_path, format='STATIONXML', level='response')
    else:
        #Create temporary file for reading into obspy
        tpf = tempfile.NamedTemporaryFile(delete=False)
        stringRoot = ET.tostring(root, encoding='UTF-8', method='xml')
        tpf.write(stringRoot)

        inv = obspy.read_inventory(tpf.name, format='STATIONXML', level='response')
        tpf.close()

        os.remove(tpf.name)
    params['inv'] = inv
    return params

#Code to help setup environment in Google Colab
def setup_colab(option='', repo_dir=''):
    """Function to help set up Google Colab environment
    
    This needs to be run twice, and at the beginning of the Google Colab notebook. 

    """
    import datetime
    import math
    import os
    import pathlib
    import time
    import sys
    import subprocess

    import matplotlib.pyplot as plt
    import numpy as np
    import scipy

    from google.colab import files
    from zipfile import ZipFile
    #%matplotlib #Run this line if you want interactive plots
    #https://github.com/googlecolab/colabtools/blob/main/google/colab/_system_commands.py
    from google.colab import _system_commands
    pyvers = _system_commands._run_command('python --version', False)
    pyvers = pyvers.output.split(' ')#+pyvers.output.split('.')[1]
    pyvers = pyvers[0].lower()+pyvers[1].split('.')[0]+'.'+pyvers[1].split('.')[1]

    packPath = '/usr/local/lib/'+pyvers+'/dist-packages'
    packPath = pathlib.Path(packPath)
    
    #Make directories
    dataDir = '/content/Data/'
    outputDir = '/content/Output'
    if not os.path.exists(dataDir):
        os.makedirs(dataDir)
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)    
    
    obspyInstalled=False
    for f in packPath.iterdir():
        if 'obspy' in f.name:
            obspyInstalled=True
            global obspy
            import obspy
            break
        
    if 'obspy' in option or option=='':
        if not obspyInstalled:
            print('Installing Obspy')
            _system_commands._run_command('pip install obspy', False)
            print("Runtime will now be reset to properly load obspy")
            print('Please run setup_colab() to upload data and enter code environment.')
            os.kill(os.getpid(), 9)
        else:
            global obspy
            import obspy
            print('Obspy has been imported.') 
    elif 'data' in option:
        global obspy
        import obspy
        print('Obspy has been installed imported.')

        os.chdir(dataDir)
        print('\nUpload data file(s): \n(file(s) will be placed in '+dataDir+')')
        files.upload() #Upload the 3 data files to be used
        if repo_dir == '':
            repo_dir='/content/SPRIT'
        os.chdir(repo_dir)
    return

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
    invPath = params['metaPath']
    raspShakeInstNameList = ['raspberry shake', 'shake', 'raspberry', 'rs', 'rs3d', 'rasp. shake', 'raspshake']
    if params['instrument'].lower() in  raspShakeInstNameList:
        params = update_shake_metadata(filepath=invPath, params=params, write_path=write_path)
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

    c=channels[0]
    pzList = [str(n) for n in list(range(7))]
    s=pzList[0]

    prefix= "{http://www.fdsn.org/xml/station/1}"

    sensitivityPath = "./"+prefix+"Network[@code='"+network+"']/"+prefix+"Station[@code='"+station+"']/"+prefix+"Channel[@code='"+c+"']/"+prefix+"Response/"+prefix+"InstrumentSensitivity/"+prefix+"Value"
    gainPath = "./"+prefix+"Network[@code='"+network+"']/"+prefix+"Station[@code='"+station+"']/"+prefix+"Channel[@code='"+c+"']/"+prefix+"Response/"+prefix+"Stage[@number='1']/"+prefix+"StageGain/"+prefix+"Value"

    #paz = []
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

        paz[str(c)] = channelPaz
        params['paz'] = paz
    return params

#Reads in traces to obspy stream
def fetch_data(params, inv=None, source='raw', trim_dir=False, export_format='mseed'):
    """Fetch ambient seismic data from a source to read into obspy stream
        
        Parameters
        ----------
        params  : dict
            Dictionary containing all the necessary params to get data.
                Parameters defined using input_params() function.
        inv     : obspy inventory object 
            Obspy inventory object containing metadata for instrument that collected data to be fetched
        source  : str, {'raw', 'dir', 'file'}
            String indicating where/how data file was created. For example, if raw data, will need to find correct channels.
                'raw' finds raspberry shake data, either in folder or subfolders; 'direct' reads filepath directly
        trim_dir : bool=False or str or pathlib obj
            If false, data is not trimmed in this function.
            Otherwise, this is the directory to save the trimmed and exported data
        export_format: str='mseed'
            If trim_dir is not False, this is the format in which to save the data
        
        Returns
        -------
        dataIN : obspy stream
            Obspy data stream with 3 traces: Z (vertical), N (North-south), and E (East-west)
        
        """
    datapath = params['dataPath']
    if inv is None:
        inv = params['inv'], 
    date=params['acq_date']
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

    print('Day of Year:', doy)

    #Select which instrument we are reading from (requires different processes for each instrument)
    raspShakeInstNameList = ['raspberry shake', 'shake', 'raspberry', 'rs', 'rs3d', 'rasp. shake', 'raspshake']
    if source=='raw':
        if inst.lower() in raspShakeInstNameList:
            rawDataIN = __read_RS_data(datapath, source, year, doy, inv, params)
    elif source=='dir':
        if inst.lower() in raspShakeInstNameList:
            rawDataIN = __read_RS_data(datapath, source, year, doy, inv, params)        
    elif source=='file':
        rawDataIN = obspy.read(datapath, starttime=obspy.core.UTCDateTime(params['starttime']), endttime=obspy.core.UTCDateTime(params['endtime']), nearest=True)
        rawDataIN.attach_response(inv)

    if type(rawDataIN) is not list:
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

    return dataIN

#Read data from raspberry shake
def __read_RS_data(datapath, source, year, doy, inv, params):
    """"Private function used by fetch_data() to read in Raspberry Shake data"""
    from obspy.core import UTCDateTime
    fileList = []
    folderPathList = []
    filesinfolder = False
    
    #Read RS files
    if source=='raw': #raw data with individual files per trace
        for child in datapath.iterdir():
            if child.is_file() and 'AM' in child.name and str(doy).zfill(3) in child.name and str(year) in child.name:
                filesinfolder = True
                folderPathList.append(datapath)
                fileList.append(child.name)
            elif child.is_dir() and child.name.startswith('EH') and not filesinfolder:
                folderPathList.append(child.name)
                for c in child.iterdir():
                    if c.is_file() and c.name.startswith('AM') and c.name.endswith(str(doy).zfill(3)) and str(year) in c.name:
                        fileList.append(c.name)

        if len(folderPathList) !=3:
            error('3 channels needed!', 1)

        fileList.sort(reverse=True) # Puts z channel first
        folderPathList.sort(reverse=True)

        if len(filepaths) == 0:
            info('No file found for specified parameters. The following days/files exist for specified year in this directory')
            doyList = []
            for j, folder in enumerate(folderPathList):
                for i, file in enumerate(folder.iterdir()):
                    if j ==0:
                        doyList.append(str(year) + ' ' + str(file.name[-3:]))
                        print(datetime.datetime.strptime(doyList[i], '%Y %j').strftime('%b %d'), '| Day of year:' ,file.name[-3:])

        traceList = []
        for i, f in enumerate(filepaths):
            with warnings.catch_warnings():
                warnings.filterwarnings(action='ignore', message='^readMSEEDBuffer()')
                st = obspy.read(str(f), starttime=UTCDateTime(params['starttime']), endttime=UTCDateTime(params['endtime']), nearest=True)
                tr = (st[0])
                #tr= obspy.Trace(tr.data,header=meta)
                traceList.append(tr)
        rawDataIN = obspy.Stream(traceList)
        rawDataIN.attach_response(inv)
        
    elif source=='dir': #files with 3 traces, but may be several in a directory or only directory name provided
        obspyFormats = ['AH','ALSEP_PSE','ALSEP_WTH','ALSEP_WTN','CSS','DMX','GCF','GSE1','GSE2','KINEMETRICS_EVT','MSEED','NNSA_KB_CORE','PDAS','PICKLE','Q','REFTEK130','RG16','SAC','SACXY','SEG2','SEGY','SEISAN','SH_ASC','SLIST','SU','TSPAIR','WAV','WIN','Y']
        for file in datapath.iterdir():
            ext = file.suffix[1:]
            rawFormat = False
            if ext.isnumeric():
                if ext > 0 and ext < 367:
                    rawFormat=True
            
            if ext.upper() in obspyFormats or rawFormat:
                filesinfolder = True
                folderPathList.append(datapath)
                fileList.append(file.name)
                        
        filepaths = []
        rawDataIN = []
        for i, f in enumerate(fileList):
            folderPathList[i] = str(folderPathList[i]).replace('\\', '/')
            folderPathList[i] = str(folderPathList[i]).replace('\\'[0], '/')
            filepaths.append(str(folderPathList[i])+'/'+f)
            filepaths[i] = pathlib.Path(filepaths[i])

            currData = obspy.read(filepaths[i])

            rawDataIN.append(currData)
            rawDataIN[i].attach_response(inv)  

        if type(rawDataIN) is list and len(rawDataIN)==1:
            rawDataIN = rawDataIN[0]
    elif source=='file':
        rawDataIN = obspy.read(str(datapath), starttime=UTCDateTime(params['starttime']), endttime=UTCDateTime(params['endtime']), nearest=True)       
        rawDataIN.attach_response(inv)
    elif type(source) is list or type(datapath) is list:
        pass #Eventually do something
        rawDataIN.attach_response(inv)
    return rawDataIN

#Trim data 
def trim_data(stream, params, export_dir=None, export_format=None):
    """Function to trim data to start and end time

        Trim data to start and end times so that stream being analyzed only contains wanted data.
        Can also export data to specified directory using a specified site name and/or export_format

        Parameters
        ----------
            stream  : obspy.stream object  
                Obspy stream to be trimmed
            params  : dict
                Dictionary containing input parameters for trimming
            export_dir: str or pathlib obj   
                Output file to export trimmed data to            
            export_format  : str or True    
                If not specified, does not export. 
                    Otherwise, exports trimmed stream using obspy write function in format provided as string.
                If specified as True, defaults to .mseed
            outfile : str                   
                Exact filename to output
                    If not designated, uses default parameters (from input filename in standard seismic file format)
        
        Returns
        -------
            st_trimmed  : obspy.stream object 
                Obpsy Stream trimmed to start and end times
    """
    start = params['starttime']
    end = params['endtime']
    site = params['site']

    st_trimmed = stream.copy()

    trimStart = obspy.UTCDateTime(start)
    trimEnd = obspy.UTCDateTime(end)
    if trimStart > st_trimmed[0].stats.endtime or trimEnd < st_trimmed[0].stats.starttime:
        print('No trim performed on {}, please check start/end times.'.format(params['site']))
    else:
        st_trimmed.trim(starttime=trimStart, endtime=trimEnd)

    #Format export filepath, if exporting
    if export_format is not None and site is not None and export_dir is not None:
        if site is None:
            site=''
        else:
            site = site+'_'
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

        st_trimmed.write(filename=exportFile)
    else:
        pass

    return st_trimmed

#Generate PPSDs for each channel
#def generate_ppsds(params, stream, ppsd_length=60, **kwargs):
def generate_ppsds(params, stream, **kwargs):
    """Generates PPSDs for each channel

        Channels need to be in Z, N, E order
        Info on PPSD creation here: https://docs.obspy.org/packages/autogen/obspy.signal.spectral_estimation.PPSD.html
        
        Parameters
        ----------
            stream  :   obspy.stream object 
                Obspy data stream from which to pull data
            paz     :   dict
                Dictionary containing dictionaries containing poles and zeros (paz) info for each channel, from inventory file or other metadata
            ppsd_length :  int
                length of data passed to psd, in seconds. Per obspy: Longer segments increase the upper limit of analyzed periods but decrease the number of analyzed segments.
            **kwargs : dict
                Dictionary with keyword arguments that can be passed to obspy.signal.PPSD

        Returns
        -------
            ppsds   :   dict
                Dictionary containing entries with ppsds for each channel
    """
    paz=params['paz']

    from obspy.imaging.cm import viridis_white_r
    from obspy.signal import PPSD
    ppsdE = PPSD(stream.select(channel='EHE').traces[0].stats, paz['EHE'], **kwargs)
    #ppsdE = PPSD(stream.select(channel='EHE').traces[0].stats, paz['EHE'], ppsd_length=ppsd_length, kwargs=kwargs)
    ppsdE.add(stream, verbose=False)

    ppsdN = PPSD(stream.select(channel='EHN').traces[0].stats, paz['EHN'], **kwargs)
    ppsdN.add(stream, verbose=False)

    ppsdZ = PPSD(stream.select(channel='EHZ').traces[0].stats, paz['EHZ'], **kwargs)
    ppsdZ.add(stream, verbose=False)

    ppsds = {'EHZ':ppsdZ, 'EHN':ppsdN, 'EHE':ppsdE}
    params['ppsds'] = ppsds
    return params

#Check the x-values for each cahnnel, to make sure they are all the same length
def __check_xvalues(ppsds):
    """Check x_values of PPSDS to make sure they are all the same length"""
    xLengths = []
    for k in ppsds.keys():
        xLengths.append(len(ppsds[k].period_bin_centers))
    if len(set(xLengths)) <= 1:
        pass #This means all channels have same number of period_bin_centers
    else:
        print('X-values (periods or frequencies) do not have the same values. \n This may result in computational errors')
        #Do stuff to fix it?
    return ppsds

#Check to make the number of time-steps are the same for each channel
def __check_tsteps(ppsds):
    """Check time steps of PPSDS to make sure they are all the same length"""
    tSteps = []
    for k in ppsds.keys():
        tSteps.append(np.array(ppsds[k].psd_values).shape[0])
    if len(set(tSteps)) <= 1:
        pass #This means all channels have same number of period_bin_centers
        minTStep=tSteps[0]
    else:
        print('There is a different number of time-steps used to calculate HVSR curves. \n This may result in computational errors. Trimming longest.')
        minTStep = min(tSteps)
    return minTStep

#Main function for processing HVSR Curve
def process_hvsr(params, method=4, smooth=True, resample=True):
    """Process the input data and get HVSR data
    
    This is the main function that uses other (private) functions to do 
    the bulk of processing of the HVSR data and the data quality checks.

    Parameters
    ----------
        params  : dict
            Dictionary containing all the parameters input by the user
        method  : int or str
            Method to use for combining the horizontal components
                0) Diffuse field assumption, or 'DFA' (not currently supported)
                1) 'Arithmetic Mean': H ≡ (HN + HE)/2
                2) 'Geometric Mean': H ≡ √HN · HE, recommended by the SESAME project (2004)
                3) 'Vector Summation': H ≡ √H2 N + H2 E
                4) 'Quadratic Mean': H ≡ √(H2 N + H2 E )/2
                5) 'Maximum Horizontal Value': H ≡ max {HN, HE}
        smooth  : bool=True
            bool or int. 
                If True, default to smooth hvsr curve to using savgoy filter with window length of 51 (works well with default resample of 1000 pts)
                If int, the length of the window in the savgoy filter. 
        resample  : bool=True
            bool or int. 
                If True, default to resample data to include 1000 frequency values for the rest of the analysis
                If int, the number of data points to interpolate/resample/smooth the component psd/HV curve data to.

    Returns
    -------
        hvsr_out    : dict
            Dictionary containing all the information about the data, including input parameters

    """
    ppsds=params['ppsds']
    ppsds = __check_xvalues(ppsds)
    resample=True

    methodList = ['Diffuse Field Assumption', 'Arithmetic Mean', 'Geometric Mean', 'Vector Summation', 'Quadratic Mean', 'Maximum Horizontal Value']
    x_freqs = {}
    x_periods = {}

    psdVals = {}
    stDev = {}
    stDevValsP = {}
    stDevValsM = {}
    psdRaw={}    
    
    for k in ppsds:
        if resample or type(resample) is int:
            if resample:
                resample = 1000 #Default smooth value

            xValMin = min(ppsds[k].period_bin_centers)
            xValMax = max(ppsds[k].period_bin_centers)

            #Resample period bin values
            x_periods[k] = np.logspace(np.log10(xValMin), np.log10(xValMax), num=resample)

            if smooth or type(smooth) is int:
                if smooth:
                    smooth = 51 #Default smoothing window
                elif smooth%2==0:
                    smooth = smooth+1


            #Resample raw ppsd values
            for i, t in enumerate(ppsds[k].psd_values):
                if i==0:
                    psdRaw[k] = np.interp(x_periods[k], ppsds[k].period_bin_centers, t)
                    if smooth > 0 :
                        psdRaw[k] = scipy.signal.savgol_filter( psdRaw[k], smooth, 3)

                else:
                    psdRaw[k] = np.vstack((psdRaw[k], np.interp(x_periods[k], ppsds[k].period_bin_centers, t)))
                    if smooth > 0:
                        psdRaw[k][i] = scipy.signal.savgol_filter( psdRaw[k][i], smooth, 3)

                #print(psdRaw[k].shape)
        else:
            #If no resampling desired
            x_periods[k] = np.array(ppsds[k].period_bin_centers)
            psdRaw[k] = np.array(ppsds[k].psd_values)

        #Get average psd value across time for each channel (used to calc H/V curve)
        psdVals[k] = np.mean(np.array(psdRaw[k]), axis=0)
        x_freqs[k] = np.divide(np.ones_like(x_periods[k]), x_periods[k]) 

        stDev[k] = np.std(psdRaw[k], axis=0)
        stDevValsM[k] = np.array(psdVals[k] - stDev[k])
        stDevValsP[k] = np.array(psdVals[k] + stDev[k])

    #This gets the hvsr curve averaged from all time steps
    anyK = list(x_freqs.keys())[0]
    hvsr_curve = __get_hvsr_curve(x=x_freqs[anyK], psd=psdVals, method=4)
    
    #Get string of method type
    if type(method) is int:
        method = methodList[method]

    #Add some other variables to our output dictionary
    hvsr_out = {'input_params':params,
                'x_freqs':x_freqs,
                'hvsr_curve':hvsr_curve,
                'x_period':x_periods,
                'psd_values':psdVals,
                'psd_raw':psdRaw,
                'ppsd_std':stDev,
                'ppsd_std_vals_m':stDevValsM,
                'ppsd_std_vals_p':stDevValsP,
                'method':method,
                'ppsds':ppsds
                }
    
    #Get hvsr curve from three components at each time step
    hvsr_tSteps = []
    anyK = list(hvsr_out['psd_raw'].keys())[0]
    for tStep in range(len(hvsr_out['psd_raw'][anyK])):
        tStepDict = {}
        for k in hvsr_out['psd_raw']:
            tStepDict[k] = hvsr_out['psd_raw'][k][tStep]
        hvsr_tSteps.append(__get_hvsr_curve(x=hvsr_out['x_freqs'][anyK], psd=tStepDict, method=method))
    hvsr_tSteps = np.array(hvsr_tSteps)
    
    hvsr_out['ind_hvsr_curves'] = hvsr_tSteps
    hvsr_out['ind_hvsr_stdDev'] = np.std(hvsr_tSteps, axis=0)
    #hvsr_out['ind_hvsr_stdDev_median'] = np.median(hvsr_tSteps, axis=0)


    tStepPeaks = []
    for tStepHVSR in hvsr_tSteps:
        tStepPeaks.append(__find_peaks(tStepHVSR))
    #tStepPeaks = np.array(tStepPeaks) #This is a list of lists, and the individual lists are different sizes

    hvsr_out['ind_hvsr_peak_indices'] = tStepPeaks
    hvsr_out['hvsr_peak_indices'] = __find_peaks(hvsr_out['hvsr_curve'])
    hvsrPF=[]
    for p in hvsr_out['hvsr_peak_indices']:
        hvsrPF.append(hvsr_out['x_freqs'][anyK][p])
    hvsr_out['hvsr_peak_freqs'] = np.array(hvsrPF)

    #Get other HVSR parameters (i.e., standard deviations, water levels, etc.)
    hvsr_out = __gethvsrparams(hvsr_out)

    return hvsr_out

#Diffuse field assumption, not currently implemented
def dfa(params, day_time_values, day_time_psd, x_values, equal_daily_energy, median_daily_psd, verbose):
    """Function for performing Diffuse Field Assumption (DFA) analysis
    
        This feature is not yet implemented.
    """
    # Are we doing DFA?
    # Use equal energy for daily PSDs to give small 'events' a chance to contribute
    # the same as large ones, so that P1+P2+P3=1
    
    method=params['method']
    
    methodList = ['Diffuse Field Assumption', 'Arithmetic Mean', 'Geometric Mean', 'Vector Summation', 'Quadratic Mean', 'Maximum Horizontal Value']
    dfaList = ['dfa', 'diffuse field', 'diffuse field assumption']
    if type(method) is int:
        method = methodList[method]
        
    if method in dfaList:
        if verbose:
            print('[INFO] Diffuse Field Assumption', flush=True)
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
                    pz = __get_power([daily_psd[0][day][i][j], daily_psd[0][day][i][j + 1]], [x_values[j], x_values[j + 1]])
                    Pz.append(pz)
                    sum_pz += pz
                    p1 = __get_power([daily_psd[1][day][i][j], daily_psd[1][day][i][j + 1]], [x_values[j], x_values[j + 1]])
                    P1.append(p1)
                    sum_p1 += p1
                    p2 = __get_power([daily_psd[2][day][i][j], daily_psd[2][day][i][j + 1]], [x_values[j], x_values[j + 1]])
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

    
    return

#Get an HVSR curve, given an array of x values (freqs), and a dict with psds for three components
def __get_hvsr_curve(x, psd, method):
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
        hvsr_curve  : list
            List containing H/V ratios at each frequency/period in x
    """
    if method==0 or method =='dfa' or method=='Diffuse Field Assumption':
        pass
    hvsr_curve = []
    for j in range(len(x)-1):
        psd0 = [psd['EHZ'][j], psd['EHZ'][j + 1]]
        psd1 = [psd['EHE'][j], psd['EHE'][j + 1]]
        psd2 = [psd['EHN'][j], psd['EHN'][j + 1]]
        f =    [x[j], x[j + 1]]

        hvsr = __get_hvsr(psd0, psd1, psd2, f, use_method=4)
        hvsr_curve.append(hvsr)  

    return np.array(hvsr_curve)

#Get additional HVSR params for later calcualtions
def __gethvsrparams(hvsr_out):
    """Private function to get HVSR parameters for later calculations (things like standard deviation, etc)"""
    count=0
    #SOMETHING VERY WRONG IS GOING ON HERE!!!!
    hvsrp2 = {}
    hvsrm2 = {}
    
    peak_water_level = []
    hvsr_std=[]
    #hvsr_log_std=[]
    peak_water_level_p=[]
    hvsrp2=[]
    hvsrm=[]
    peak_water_level_m=[]
    water_level=1.8 #Make this an input parameter eventually!!!****
    
    count += 1
    hvsr_log_std = {}

    peak_water_level.append(water_level)

    hvsr=hvsr_out['hvsr_curve']
    if hvsr_out['ind_hvsr_curves'].shape[0] > 0:
        hvsrp = np.add(hvsr_out['hvsr_curve'], hvsr_out['ind_hvsr_stdDev'])
        hvsrm = np.subtract(hvsr_out['hvsr_curve'], hvsr_out['ind_hvsr_stdDev'])

        #ppsd_std = hvsr_out['ppsd_std']
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

#Plot HVSR data
def hvplot(hvsr_dict, kind='HVSR', xtype='freq', returnfig=False,  save_dir=None, save_suffix='', show=True,**kwargs):
    """Function to plot HVSR data

        Parameters
        ----------
        hvsr_dict   : dict                  
            Dictionary containing output from process_hvsr function
        kind        : str='HVSR' or list    
            The kind of plot(s) to plot. If list, will plot all plots listed
            'HVSR'  : Standard HVSR plot, including standard deviation
            - '[HVSR] c' :HVSR plot with each components' spectra
            - '[HVSR] p' :HVSR plot with best peaks shown
            - '[HVSR] p' : HVSR plot with best picked peak shown                
            - '[HVSR] p* all' : HVSR plot with all picked peaks shown                
            - '[HVSR] p* t' : HVSR plot with peaks from all time steps in background                
            - '[HVSR p* ann]  : Annotates plot with peaks
            - '[HVSR] -s' : HVSR plots don't show standard deviation
            - '[HVSR] t'  : HVSR plot with individual hv curves for each time step shown
            'Specgram': Combined spectrogram of all components
        xtype       : str='freq'    
            String for what to use between frequency or period
                For frequency, the following are accepted (case does not matter): 'f', 'Hz', 'freq', 'frequency'
                For period, the following are accepted (case does not matter): 'p', 'T', 's', 'sec', 'second', 'per', 'period'
        returnfig   : bool
            Whether to return figure and axis objects
        save_dir     : str or None
            Directory in which to save figures
        save_suffix  : str
            Suffix to add to end of figure filename(s), if save_dir is used
        show    : bool
            Whether to show plot
        **kwargs    : keyword arguments
            Keyword arguments for matplotlib.pyplot (still working on this)

        Returns
        -------
        fig, ax : matplotlib figure and axis objects
            Returns figure and axis matplotlib.pyplot objects if returnfig=True, otherwise, simply plots the figures
    """
    plt.rcParams['figure.dpi'] = 500
    plt.rcParams['figure.figsize'] = (12, 3)

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

    kList = kind.split(' ')
    chartStr = []
    i = 0
    for k in kList:
        k = k.strip().lower()
        if i == 0 and (k in hvsrList or k in specgramList):
            chartType = k        
        if '+' in k or (k in hvsrList and i > 0) or (k in specgramList and i > 0):
            if chartType in specgramList:
                fig, ax = __plot_specgram(hvsr_dict, savedir=save_dir, save_suffix=save_suffix, show=show, kwargs=kwargs)
                i=0
            else:
                fig, ax = __plot_hvsr(hvsr_dict, kind=chartStr, xtype=xtype,  savedir=save_dir, save_suffix=save_suffix, show=show, kwargs=kwargs)                
                i=0

            if '+' in k:
                k = k.replace('+', '')    
                chartStr = [k]
                fig, ax = __plot_hvsr(hvsr_dict, kind=chartStr, xtype=xtype,  savedir=save_dir, save_suffix=save_suffix, show=show, kwargs=kwargs)
            chartStr = [k]
        else:
            i+=1
            chartStr.append(k)
            
    if len(chartStr) > 0:
        if i == 0 and (k in hvsrList or k in specgramList):
            chartType = k     

        if chartType in specgramList:
            fig, ax = __plot_specgram(hvsr_dict,  savedir=save_dir, save_suffix=save_suffix, show=show, kwargs=kwargs)
        else:
            fig, ax = __plot_hvsr(hvsr_dict, kind=chartStr, xtype=xtype,  savedir=save_dir, save_suffix=save_suffix, show=show, kwargs=kwargs)

    if returnfig:
        return fig, ax
    
    return
    
#Plot hvsr curve, private supporting function for hvplot
def __plot_hvsr(hvsr_dict, kind, xtype, save_dir=None, save_suffix='', show=True, **kwargs):
    """Private function for plotting hvsr curve (or curves with components)
    """
    kwargs = kwargs['kwargs']

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

    axis = plt.gca()
    fig = plt.gcf()

    anyKey = list(hvsr_dict[xtype].keys())[0]
    x = hvsr_dict[xtype][anyKey][:-1]
    y = hvsr_dict['hvsr_curve']
    
    plotSuff=''
    legendLoc = 'upper right'
    
    plotHVSR = False
    for item in kind:
        if item.lower()=='hvsr':
            plotHVSR=True
            axis.plot(x, y, color='k', label='H/V Ratio', zorder=1000)
            plotSuff='HVSRCurve_'
            if '-s' not in kind:
                axis.fill_between(x, hvsr_dict['hvsrm2'], hvsr_dict['hvsrp2'], color='k', alpha=0.2, label='StDev')
            else:
                plotSuff = plotSuff+'noStdDev_'
            break

    plt.semilogx()
    plt.ylim(ylim)
    plt.xlim(xlim)
    plt.xlabel(xlabel)
    plt.ylabel('H/V Ratio'+'\n['+hvsr_dict['method']+']')
    plt.title(hvsr_dict['input_params']['site'])


    for k in kind:   
        if k=='p' and 'all' not in kind:
            plotSuff=plotSuff+'BestPeak_'
            
            bestPeakScore = 0
            for i, p in enumerate(hvsr_dict['Peak Report']):
                if p['Score'] > bestPeakScore:
                    bestPeakScore = p['Score']
                    bestPeak = p

            axis.vlines(bestPeak['f0'], 0, 50, colors='k', linestyles='dotted', label='Peak')          
            if 'ann' in kind:
                axis.annotate('Peak at '+str(round(bestPeak['f0'],2))+'Hz', (bestPeak['f0'], 0.1), xycoords='data', 
                                horizontalalignment='center', verticalalignment='bottom', 
                                bbox=dict(facecolor='w', edgecolor='none', alpha=0.8, pad=0.1))
                plotSuff = plotSuff+'ann_'

        elif k=='p'  and 'all' in kind:
            plotSuff = plotSuff+'allPeaks_'

            axis.vlines(hvsr_dict['hvsr_peak_freqs'], 0, 50, colors='k', linestyles='dotted', label='Peak')          
            if 'ann' in kind:
                for i, p in enumerate(hvsr_dict['hvsr_peak_freqs']):
                    y = hvsr_dict['hvsr_curve'][hvsr_dict['hvsr_peak_indices'][i]]
                    axis.annotate('Peak at '+str(round(p,2))+'Hz', (p, 0.1), xycoords='data', 
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
                            axis.fill_betweenx(ylim,v-width,v+width, color='r', alpha=0.05, label='Individual H/V Peaks')
                        else:
                           axis.fill_betweenx(ylim,v-width,v+width, color='r', alpha=0.05)
            for t in hvsr_dict['ind_hvsr_curves']:
                axis.plot(x, t, color='gray', alpha=0.3, linewidth=0.8)

        if k=='c':
            plotSuff = plotSuff+'IndComponents_'
            
            if len(kind) > 1:
                plt.tight_layout()
                axis2 = ax.twinx()
                axis2 = plt.gca()
                fig = plt.gcf()
                axis2.set_ylabel('Amplitude'+'\n[m2/s4/Hz] [dB]')
                legendLoc2 = 'upper left'
            else:
                plt.title(hvsr_dict['input_params']['site']+': Individual Components')
                axis = plt.gca()
                fig = plt.gcf()
            minY = []
            maxY = []
            for k in hvsr_dict['psd_values']:
                minY.append(min(hvsr_dict['ppsd_std_vals_m'][k]))
                maxY.append(max(hvsr_dict['ppsd_std_vals_p'][k]))
            minY = min(minY)
            maxY = max(maxY)
            rng = maxY-minY
            pad = rng * 0.05
            ylim = [minY-pad, maxY+pad]
        
            axis.set_ylabel('Amplitude'+'\n[m2/s4/Hz] [dB]')
            plt.ylim(ylim)

            #Modify based on whether there are multiple charts
            if plotHVSR:
                linalpha = 0.2
                stdalpha = 0.05
            else:
                linalpha=1
                stdalpha=0.2
            
            #Plot individual components
            y={}
            for k in hvsr_dict['psd_values']:
                y[k] = hvsr_dict['psd_values'][k][:-1]

                if k == 'EHZ':
                    pltColor = 'k'
                elif k =='EHE':
                    pltColor = 'b'
                elif k == 'EHN':
                    pltColor = 'r'

                if len(kind) > 1:
                    axis2.plot(x, y[k], c=pltColor, label=k, alpha=linalpha)
                    axis2.fill_between(x, hvsr_dict['ppsd_std_vals_m'][k][:-1], hvsr_dict['ppsd_std_vals_p'][k][:-1], color=pltColor, alpha=stdalpha)
                else:
                    axis.plot(x, y[k], c=pltColor, label=k, alpha=linalpha)
                    axis.fill_between(x, hvsr_dict['ppsd_std_vals_m'][k][:-1], hvsr_dict['ppsd_std_vals_p'][k][:-1], color=pltColor, alpha=stdalpha)
            if len(kind) > 1:
                axis2.legend(loc=legendLoc2)
            else:
                pass#axis.legend(loc=legendLoc)

    bbox = axis.get_window_extent()
    bboxStart = bbox.__str__().find('Bbox(',0,50)+5
    bboxStr = bbox.__str__()[bboxStart:].split(',')[:4]
    axisbox = []
    for i in bboxStr:
        i = i.split('=')[1]
        if ')' in i:
            i = i[:-1]
        axisbox.append(float(i))
    #print(axisbox)
    #print(axis.get_position())

    axis.legend(loc=legendLoc)

    __plot_current_fig(save_dir=save_dir, 
                        filename=filename, 
                        plot_suffix=plotSuff, 
                        user_suffix=save_suffix, 
                        show=show)
    
    return fig, ax

def __plot_current_fig(save_dir, filename, plot_suffix, user_suffix, show):
    """Private function to support hvplot, for plotting and showing plots"""
    plt.gca()
    plt.gcf()
    plt.tight_layout()

    plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)

    if save_dir is not None:
        outFile = save_dir+'/'+filename+'_'+plot_suffix+str(datetime.datetime.today().date())+'_'+user_suffix+'.png'
        plt.savefig(outFile, bbox_inches='tight', pad_inches=0.2)
    if show:
        plt.show()
        plt.ion()
    return

#Plot specgtrogram, private supporting function for hvplot
def __plot_specgram(hvsr_dict, save_dir=None, save_suffix='',**kwargs):
    """Private function for plotting average spectrogram of all three channels from ppsds
    """
    fig, ax = plt.subplots()

    kwargs = kwargs['kwargs']

    if 'peak_plot' in kwargs.keys():
        peak_plot=True
        del kwargs['peak_plot']
    else:
        peak_plot=False
        

    if 'grid' in kwargs.keys():
        plt.grid(which=kwargs['grid'], alpha=0.25)
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

    if 'cmap' in kwargs.keys():
        pass
    else:
        kwargs['cmap'] = 'afmhot'

    ppsds = hvsr_dict['ppsds']
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

    xmin = datetime.datetime.strptime(min(ppsds[anyKey].current_times_used[:-1]).isoformat(), '%Y-%m-%dT%H:%M:%S.%f')
    xmax = datetime.datetime.strptime(max(ppsds[anyKey].current_times_used[:-1]).isoformat(), '%Y-%m-%dT%H:%M:%S.%f')
    xmin = mdates.date2num(xmin)
    xmax = mdates.date2num(xmax)

    tTicks = mdates.MinuteLocator(byminute=range(0,60,5))
    ax.xaxis.set_major_locator(tTicks)
    tTicks_minor = mdates.SecondLocator(bysecond=[0])
    ax.xaxis.set_minor_locator(tTicks_minor)

    tLabels = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(tLabels)
    plt.tick_params(axis='x', labelsize=8)

    if ppsds[anyKey].current_times_used[0].date != ppsds[anyKey].current_times_used[0-1].date:
        day = str(ppsds[anyKey].current_times_used[0].date)+' - '+str(ppsds[anyKey].current_times_used[1].date)
    else:
        day = str(ppsds[anyKey].current_times_used[0].date)

    ymin = hvsr_dict['input_params']['hvsr_band'][0]
    ymax = hvsr_dict['input_params']['hvsr_band'][1]

    extList = [xmin, xmax, ymin, ymax]
  
    ax = plt.gca()
    fig = plt.gcf()

    freqticks = np.flip(hvsr_dict['x_freqs'][anyKey])
    yminind = np.argmin(np.abs(ymin-freqticks))
    ymaxind = np.argmin(np.abs(ymax-freqticks))
    freqticks = freqticks[yminind:ymaxind]

    #Set up axes, since data is already in semilog
    axy = ax.twinx()
    axy.zorder=0
    ax.zorder=1
    ax.set_facecolor('#ffffff00') #Create transparent background for front axis
    plt.sca(axy)
    im = plt.imshow(psdArr, origin='lower', extent=extList, aspect='auto', interpolation='nearest', **kwargs)
    plt.tick_params(left=False, right=False)
    plt.yticks([], labels='')
    plt.sca(ax)
    if peak_plot:
        ax.hlines(hvsr_dict['Best Peak']['f0'], xmin,xmax, colors='k', linestyles='dashed', alpha=0.5)

    #FreqTicks =np.arange(1,np.round(max(hvsr_dict['x_freqs'][anyKey]),0), 10)
    plt.title(hvsr_dict['input_params']['site']+': Spectrogram')
    plt.xlabel('UTC Time \n'+day)
    cbar = plt.colorbar(mappable=im)
    cbar.set_label('H/V Ratio')

    plt.ylabel(ylabel)
    #plt.yticks(freqticks)
    plt.semilogy()
    plt.ylim(hvsr_dict['input_params']['hvsr_band'])

    plt.rcParams['figure.dpi'] = 500
    plt.rcParams['figure.figsize'] = (12,4)
    fig.tight_layout()
    plt.show()
    return fig, ax

#Get HVSR
def __get_hvsr(_dbz, _db1, _db2, _x, use_method=4):
    """
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

    _h = {  2: (_h1 + _h2) / 2.0, 
            3: math.sqrt(_h1 * _h2), 
            4: math.sqrt(_p1 + _p2), 
            5: math.sqrt((_p1 + _p2) / 2.0),
            6: max(_h1, _h2)}

    _hvsr = _h[use_method] / _hz
    return _hvsr

#Remove decibel scaling
def __remove_db(_db_value):
    """convert dB power to power"""
    _values = list()
    for _d in _db_value:
        _values.append(10 ** (float(_d) / 10.0))
    return _values

#For converting dB scaled data to power units
def __get_power(_db, _x):
    """Calculate HVSR

      We will undo setp 6 of MUSTANG processing as outlined below:
          1. Dividing the window into 13 segments having 75% overlap
          2. For each segment:
             2.1 Removing the trend and mean
             2.2 Apply a 10% sine taper
             2.3 FFT
          3. Calculate the normalized PSD
          4. Average the 13 PSDs & scale to compensate for tapering
          5. Frequency-smooth the averaged PSD over 1-octave intervals at 1/8-octave increments
          6. Convert power to decibels

    Parameters
    ----------
    _db : float
        Individual power value in decibels
    _x : float
        Individual x value (either frequency or period)
    
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
     compute area
    """
    #print(_db)
    _dx = abs(np.diff(_x)[0])
    #print(_dx)
    _p = np.multiply(np.mean(__remove_db(_db)), _dx)
    #print(_p)
    return _p

#Find peaks in the hvsr ccruve
def __find_peaks(_y):
    """Finds peaks on hvsr curve"""
    _index_list = scipy.signal.argrelextrema(np.array(_y), np.greater)

    return _index_list[0]

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

    bestPeakScore = 0
    for i, p in enumerate(hvsr_dict['Peak Report']):
        if p['Score'] > bestPeakScore:
            bestPeakScore = p['Score']
            bestPeak = p
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
                          'Report': {'A0': '', 'P+': '', 'P-': '', 'Sf': '', 'Sa': ''},
                          'Pass List':{}})
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
    anyKey = list(hvsr_dict['psd_raw'].keys())[0]#Doesn't matter which channel we use as key

    delta = hvsr_dict['ppsds'][anyKey].delta
    window_len = (hvsr_dict['ppsds'][anyKey].len * delta) #Window length in seconds
    window_num = np.array(hvsr_dict['psd_raw'][anyKey]).shape[0]

    for _i in range(len(_peak)):
        peakFreq= _peak[_i]['f0']
        test1 = peakFreq > 10/window_len
        test2 = window_len * window_num * peakFreq > 200

        halfF0 = peakFreq/2
        doublef0 = peakFreq*2
        
        test3 = True
        failCount = 0
        for i, freq in enumerate(hvsr_dict['x_freqs'][anyKey]):
            if freq >= halfF0 and freq <doublef0:
                if peakFreq >= 0.5:
                    if hvsr_dict['hvsr_log_std'][i] >= 2:
                        test3=False
                        failCount +=1
                else: #if peak freq is less than 0.5
                    if hvsr_dict['hvsr_log_std'][i] >= 3:
                        test3=False
                        failCount +=1
        _peak[_i]['Pass List']['Window Length Freq.'] = test1
        _peak[_i]['Pass List']['Significant Cycles'] = test2
        _peak[_i]['Pass List']['Low Curve StDev. over time'] = test3
    return _peak

#Check clarity of peaks
def __check_clarity(_x, _y, _peak, do_rank=False):
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
    for _i in range(len(_peak)):
        #Initialize as False
        _peak[_i]['f-'] = 'X'
        _peak[_i]['Pass List']['Peak Freq. Clarity Below'] = False
        for _j in range(len(_x) - 1, -1, -1):

            # There exist one frequency f-, lying between f0/4 and f0, such that A0 / A(f-) > 2.
            if (float(_peak[_i]['f0']) / 4.0 <= _x[_j] < float(_peak[_i]['f0'])) and \
                    float(_peak[_i]['A0']) / _y[_j] > 2.0:
                _peak[_i]['f-'] = '%10.3f %1s' % (_x[_j], check_mark())
                _peak[_i]['Score'] += 1
                _peak[_i]['Pass List']['Peak Freq. Clarity Below'] = True
                break
            else:
                pass
    
    if do_rank:
        max_rank += 1
    for _i in range(len(_peak)):
        #Initialize as False
        _peak[_i]['f+'] = 'X'
        _peak[_i]['Pass List']['Peak Freq. Clarity Above'] = False
        for _j in range(len(_x) - 1):

            # There exist one frequency f+, lying between f0 and 4*f0, such that A0 / A(f+) > 2.
            if float(_peak[_i]['f0']) * 4.0 >= _x[_j] > float(_peak[_i]['f0']) and \
                    float(_peak[_i]['A0']) / _y[_j] > 2.0:
                _peak[_i]['f+'] = '%10.3f %1s' % (_x[_j], check_mark())
                _peak[_i]['Score'] += 1
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
            _peak[_i]['Report']['A0'] = '%10.2f > %0.1f %1s' % (_peak[_i]['A0'], _a0, 'X')
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
        _peak[_i]['Report']['P-'] = 'X'
        for _j in range(len(_peakm)):
            if abs(_peakm[_j]['f0'] - _peak[_i]['f0']) < _dx:
                _index = _j
                _dx = abs(_peakm[_j]['f0'] - _peak[_i]['f0'])
            if _peak[_i]['f0'] * 0.95 <= _peakm[_j]['f0'] <= _peak[_i]['f0'] * 1.05:
                _peak[_i]['Report']['P-'] = '%0.3f within ±5%s of %0.3f %1s' % (_peakm[_j]['f0'], '%',
                                                                                 _peak[_i]['f0'], check_mark())
                _found_m[_i] = True
                break
        if _peak[_i]['Report']['P-'] == 'X':
            _peak[_i]['Report']['P-'] = '%0.3f within ±5%s of %0.3f %1s' % (_peakm[_j]['f0'], '%', ##changed i to j
                                                                             _peak[_i]['f0'], 'X')

    #Then Check above
    _found_p = list()
    for _i in range(len(_peak)):
        _dx = 1000000.
        _found_p.append(False)
        _peak[_i]['Report']['P+'] = 'X'
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
                        _peakp[_j]['f0'], '%', _peak[_i]['f0'], 'X')
                    _peak[_i]['Pass List']['Freq. Stability'] = False
                break
        if _peak[_i]['Report']['P+'] == 'X' and len(_peakp) > 0:
            _peak[_i]['Report']['P+'] = '%0.3f within ±5%s of %0.3f %1s' % (
                _peakp[_j]['f0'], '%', _peak[_i]['f0'], 'X')###changed i to j

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
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f  %1s' % (_stdf[_i], _e, _this_peak['f0'], 'X')
                _this_peak['Pass List']['Peak Stability (freq. std)'] = False

            _t = 0.48
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f %1s' % (_hvsr_log_std[_i], _t,
                                                                    check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (amp. std)'] = True
            else:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f  %1s' % (_hvsr_log_std[_i], _t, 'X')
                _this_peak['Pass List']['Peak Stability (amp. std)'] = False

        elif 0.2 <= _this_peak['f0'] < 0.5:
            _e = 0.2
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s' % (_stdf[_i], _e, _this_peak['f0'],
                                                                            check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (freq. std)'] = True
            else:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f  %1s' % (_stdf[_i], _e, _this_peak['f0'], 'X')
                _this_peak['Pass List']['Peak Stability (freq. std)'] = False

            _t = 0.40
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f %1s' % (_hvsr_log_std[_i], _t,
                                                                    check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (amp. std)'] = True
            else:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f  %1s' % (_hvsr_log_std[_i], _t, 'X')
                _this_peak['Pass List']['Peak Stability (amp. std)'] = False

        elif 0.5 <= _this_peak['f0'] < 1.0:
            _e = 0.15
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s' % (_stdf[_i], _e, _this_peak['f0'],
                                                                            check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (freq. std)'] = True
            else:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f  %1s' % (_stdf[_i], _e, _this_peak['f0'], 'X')
                _this_peak['Pass List']['Peak Stability (freq. std)'] = False

            _t = 0.3
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f %1s' % (_hvsr_log_std[_i], _t, check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (amp. std)'] = True
            else:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f  %1s' % (_hvsr_log_std[_i], _t, 'X')
                _this_peak['Pass List']['Peak Stability (amp. std)'] = False

        elif 1.0 <= _this_peak['f0'] <= 2.0:
            _e = 0.1
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s' % (_stdf[_i], _e, _this_peak['f0'],
                                                                            check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (freq. std)'] = True
            else:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s ' % (_stdf[_i], _e, _this_peak['f0'], 'X')
                _this_peak['Pass List']['Peak Stability (freq. std)'] = False

            _t = 0.25
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f %1s' % (_hvsr_log_std[_i], _t, check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (amp. std)'] = True
            else:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f  %1s' % (_hvsr_log_std[_i], _t, 'X')
                _this_peak['Pass List']['Peak Stability (amp. std)'] = False

        elif _this_peak['f0'] > 0.2:
            _e = 0.05
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s' % (_stdf[_i], _e, _this_peak['f0'],
                                                                            check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (freq. std)'] = True
            else:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f  %1s' % (_stdf[_i], _e, _this_peak['f0'], 'X')
                _this_peak['Pass List']['Peak Stability (freq. std)'] = False

            _t = 0.2
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f %1s' % (_hvsr_log_std[_i], _t, check_mark())
                _this_peak['Score'] += 1
                _this_peak['Pass List']['Peak Stability (amp. std)'] = True
            else:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f  %1s' % (_hvsr_log_std[_i], _t, 'X')
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
def print_report(hvsr_data, export='', format='print', include='peak'):
    """Print a report of the HVSR analysis (not currently implemented)
    
    Parameters
    ----------
    hvsr_data : dict
        Dictionary containing all the information about the processed hvsr data
    format : {'csv', 'print', 'docx'}
        Format in which to print or export the report.
    export : str
        Filepath path for export. If not specified, report name is generated automatically and placed in current directory
    include : str or list, default='peak'
        What to include in the report. By default includes all the following
            - Site name
            - Filename
            - Longitude
            - Latitude
            - Elevation
            - Primary peak frequency
            - Primary peak amplitude
            - Whether passed quality tests (x6)
        For docx (not yet implemented), the following are also included:
            - Figure with spectrogram
            - Figure with HVSR curve
            - Figure with 3 components
    """
    #print statement
    if format=='print':
        print(hvsr_data['Peak Report'])
        hvplot(hvsr_data, kind='HVSR p tp ann')
        hvplot(hvsr_data, kind='HVSR c')
        hvplot(hvsr_data, kind='spec')
    if export:
        pass
        #code to write to output file
    return
import datetime
import warnings
import pathlib
import xml.etree.ElementTree as ET
import os
import sys
import tempfile

import obspy

import hvsr.hvsrtools.msgLib as msgLib

"""
This file contains all the updated functions needed
"""
##msgLib functions
#Post message
def message(post_message):
    """print a run message"""
    bar = "*" * 12
    print("%s %s %s" % (bar, post_message, bar))

#Post error
def error(err_message, code):
    """print an error message"""
    print("\n[ERR] %s\n" % err_message, flush=True)
    return code

#Post warning
def warning(sender, warn_message):
    """print a warning message"""
    print("[WARN] from %s: %s" % (sender, warn_message), flush=True)

#Post info message
def info(info_message):
    """print an informative message"""
    print("[INFO] %s" % info_message, flush=True)
    return

#Converts filepaths to pathlib paths, if not already
def checkifpath(filepath):
    # checks if the variable is any instance of pathlib
    if isinstance(filepath, pathlib.PurePath):
        pass
    else:
        try:
            filepath = pathlib.Path(filepath)
            #print('Converted string to pathlib path') #Assume a string was input rather than pathlib object
        except:
            msgLib.error('Input cannot be converted to pathlib path', 0)
    return filepath

#Formats time into desired output
def __formatTime(inputDT, tzone='utc', dst=True):
    """
    Formats input time to datetime objects in utc
    --------------
    Parameters:
        inputDT : str or datetime obj input datetime. Can include date and time, just date (time inferred to be 00:00:00.00) or just time (if so, date is set as today)
        tzone   : str='utc' or int {'utc', 'local'} timezone of data entry. 
                    If string and not utc, assumed to be timezone of computer running the process.
                    If int, assumed to be offset from UTC (e.g., CST in the United States is -6; CDT in the United States is -5)
        dst     : bool=True If any string aside from 'utc' is specified for tzone, this will adjust according to daylight savings time. If tzone is int, no adjustment made

    --------------
    Returns:
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
#Define input parameters
def input_param(network='AM', 
                        station='RAC84', 
                        loc='00', 
                        channels=['EHZ', 'EHN', 'EHE'],
                        date=str(datetime.datetime.now().date()),
                        starttime = '00:00:00.00',
                        endtime = '23:59:99.99',
                        tzone = 'America/Chicago', #or 'UTC'
                        dst = True,
                        lon = -88.2290526,
                        lat =  40.1012122,
                        elevation = 755,
                        depth = 0,
                        dataPath = '',
                        metaPath = r'resources\raspshake_metadata.inv'
                        ):
    #day_of_year = 1#Get day of year
    #Reformat time
    if type(date) is datetime.datetime:
        date = str(date.date())
    elif type(date) is datetime.date:
        date=str(date)

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
    starttime = __formatTime(starttime, tzone=tzone, dst=dst)

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
    endtime = __formatTime(endtime, tzone=tzone, dst=dst)

    date = datetime.date(year=int(date.split('-')[0]), month=int(date.split('-')[1]), day=int(date.split('-')[2]))

    if metaPath == r'resources\raspshake_metadata.inv':
        metaPath = str(pathlib.Path(os.getcwd()))+'\\'+metaPath

    inputParamDict = {'net':network,'sta':station, 'loc':loc, 'cha':channels,
                    'date':date,'starttime':starttime,'endtime':endtime, 'timezone':'UTC',
                    'longitude':lon,'latitude':lat,'elevation':elevation,'depth':depth,
                    'dataPath':dataPath, 'metaPath':metaPath
                    }

    return inputParamDict

#Read in metadata .inv file, specifically for RaspShake
def updateShakeMetadata(filepath, network='AM', station='RAC84', channels=['EHZ', 'EHN', 'EHE'], 
                    startdate=str(datetime.datetime(2022,1,1)), enddate=str(datetime.datetime.today()), 
                    lon = '-88.2290526', lat = '40.1012122', elevation = '755', depth='0', write=True):
    """
    Reads static metadata file provided for Rasp Shake and updates with input parameters
        --------------
        PARAMETERS
            filepath
            network
            station
            channels
            startdate
            enddate
            lon
            lat
            elevation
            depth
        -------------
        Returns
        
        updated tree, output filepath
    """
    filepath = checkifpath(filepath)

    parentPath = filepath.parent
    filename = filepath.stem

    tree = ET.parse(str(filepath))
    root = tree.getroot()

    prefix= "{http://www.fdsn.org/xml/station/1}"

    #metadata  = list(root)#.getchildren()

    for item in root.iter(prefix+'Channel'):
        item.attrib['endDate'] = enddate

    for item in root.iter(prefix+'Station'):
        item.attrib['code'] = station
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
    filetag = '_'+str(datetime.datetime.today().date())

    outfile = str(parentPath)+'\\'+filename+filetag+'.inv'

    if write:
        tree.write(outfile, xml_declaration=True, method='xml',encoding='UTF-8')

    #Create temporary file for reading into obspy
    tpf = tempfile.NamedTemporaryFile(delete=False)
    stringRoot = ET.tostring(root, encoding='UTF-8', method='xml')
    tpf.write(stringRoot)
    tpf.close()

    inv = obspy.read_inventory(tpf.name, format='STATIONXML', level='response')

    os.remove(tpf.name)

    return inv

#Gets the metadata for Raspberry Shake, specifically for 3D v.7
def getShakeMetadata(inv, station='RAC84', network='AM', channels = ['EHZ', 'EHN', 'EHE']):
    """Get Shake metadata and output as paz parameter needed for PPSD
    Parameters:
        inv     : file, file object or obspy inventory object
        station : str           station name (must be the same as in the inv object or file)
        network : str           network name (must be the same as in the inv object or file)
        channels: list of str   channel names (must be the same as in the inv object or file)
    """
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
    return paz

#Reads in traces to obspy stream
def fetchdata(datapath, inv, date=datetime.datetime.today(), inst='raspshake'):

    """Fetch ambient seismic data from a source to read into obspy stream
        Parameters
        ----------
        datapath : str or pathlib path
            Path to directory containing data. For Raspberry Shakes, 
            this is the directory where the channel folders are located.
        inv     : obspy inventory object containing metadata for instrument that collected data to be fetched
        date : str, tuple, or date object
            Date for which to read in the data traces. 
            If string, will attempt to decode to convert to a date format.
            If tuple, assumes first item is day of year (DOY) and second item is year 
            If date object, will read it in directly.
        inst : str {'raspshake}
            The type of instrument from which the data is reading. Currently, only raspberry shake supported
        
        Returns
        ---------
        rawDataIN : obspy data stream with 3 traces: Z (vertical), N (North-south), and E (East-west)
        
        """

    datapath = checkifpath(datapath)

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
            msgLib.error('First item in date tuple must be day of year (0-366)', 0)
        elif date[1] > datetime.datetime.now().year:
            msgLib.error('Second item in date tuple should be year, but given item is in the future', 0)
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
            msgLib.info("Preferred date format is 'yyyy-mm-dd' or 'yyyy/mm/dd'. Will attempt to parse date.")
            date = datetime.datetime(int(dateSplit[2]), int(dateSplit[0]), int(dateSplit[1]))
            doy = date.timetuple().tm_yday
            year = date.year
        else:
            msgLib.info("Preferred date format is 'yyyy-mm-dd' or 'yyyy/mm/dd'. Cannot parse date.")
    else: #FOR NOW, need to update
        date = datetime.datetime.now()
        doy = date.timetuple().tm_yday
        year = date.year
        print("Did not recognize date, using year {} and day {}".format(year, doy))

    print('Day of Year:', doy)

    if inst=='raspshake':
        folderList = []
        folderPathList = []
        for child in datapath.iterdir():
            if child.is_dir():
                folderPathList.append(child)
                folderList.append(child.stem.split('.')[0])
        folderList.sort(reverse=True) #Channels in Z, N, E order

        if len(folderList) !=3:
            msgLib.error('3 channels needed!', 1)
        else:
            filepaths = []
            for folder in folderPathList:
                for file in folder.iterdir():
                    if str(doy) in str(file.name) and str(year) in str(file.name):
                        filepaths.append(file)

            if len(filepaths) == 0:
                msgLib.info('No file found for specified day/year. The following days/files exist for specified year in this directory')
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
                    st = obspy.read(str(f))
                    tr = (st[0])
                    #tr= obspy.Trace(tr.data,header=meta)
                    traceList.append(tr)
            rawDataIN = obspy.Stream(traceList)
            rawDataIN.attach_response(inv)
    if 'Z' in str(rawDataIN.traces[0])[12:15]:
        pass
    else:
        rawDataIN = rawDataIN.sort(['channel'], reverse=True) #z, n, e order
    return rawDataIN

#Trim data 
def trimdata(stream, start, end):
    """Function to trim data to start and end time
        -------------------
        Parameters:
            stream  : obspy.stream object   Stream to be trimmed
            start   : datetime object   Start time of trim, in UTC
            end     : datetime object   End time of trim, in UTC
        ---------------------
        Returns:
            st_trimmed  : obspy.stream object Obpsy Stream trimmed to start and end times
    """
    st_trimmed = stream.copy()

    trimStart = obspy.UTCDateTime(start)
    trimEnd = obspy.UTCDateTime(end)
    st_trimmed.trim(starttime=trimStart, endtime=trimEnd)

    return st_trimmed

#Generate PPSDs for each channel
def generatePPSDs(stream, paz, ppsd_length=60, **kwargs):
    """Generates PPSDs for each channel
        Channels need to be in Z, N, E order
        Info on PPSD creation here: https://docs.obspy.org/packages/autogen/obspy.signal.spectral_estimation.PPSD.html
        ---------------------
        Parameters:
            stream  :   obspy stream object from which to pull data
            paz     :   dictionary of dictionaries    a dictionary with dictionaries containing poles and zeros (paz) info for each channel, from inv file
            ppsd_length:  length of data passed to psd, in seconds. Per obspy: Longer segments increase the upper limit of analyzed periods but decrease the number of analyzed segments.
            **kwargs:   keyword arguments that can be passed to obspy.signal.PPSD

        ----------------------
        Returns:
            ppsds   :   dictionary containing entries with ppsds for each channel
    """
    from obspy.imaging.cm import viridis_white_r
    from obspy.signal import PPSD
    ppsdE = PPSD(stream.select(channel='EHE').traces[0].stats, paz['EHE'], ppsd_length=ppsd_length, kwargs=kwargs)
    ppsdE.add(stream, verbose=False)

    ppsdN = PPSD(stream.select(channel='EHN').traces[0].stats, paz['EHN'], ppsd_length=ppsd_length, kwargs=kwargs)
    ppsdN.add(stream, verbose=False)

    ppsdZ = PPSD(stream.select(channel='EHZ').traces[0].stats, paz['EHZ'], ppsd_length=ppsd_length, kwargs=kwargs)
    ppsdZ.add(stream, verbose=False)

    ppsds = {'EHZ':ppsdZ, 'EHN':ppsdN, 'EHE':ppsdE}
    return ppsds

def process_hvsr():
    """
    This function will have all the stuff needed to process HVSR, as updated from local data
    Based on the notebook
    """


    return
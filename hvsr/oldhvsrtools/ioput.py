'''
Functions for reading in data
'''
import sys
import os
import datetime
import pathlib
import warnings
import xml.etree.ElementTree as ET

import obspy

import hvsr.oldhvsrtools.utilities as utilities
import hvsr.oldhvsrtools.fileLib as fileLib
import hvsr.oldhvsrtools.msgLib as msgLib
import hvsr.oldhvsrtools.setParams as setParams

#utilities.get_args(sys.argv) #This is for command-line?
#args = setParams.args()

args= { 'net':'AM',
        'sta':'RAC84',
        'loc':'00',
        'cha':['EHE', 'EHN', 'EHZ']
        }

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

#Reads in traces to obspy stream
def fetchdata(datapath, inv, filestart='00:00:00.0', date=datetime.datetime.today(), args=args, inst='raspshake'):
    """Fetch ambient seismic data from a source to read into obspy stream
        Parameters
        ----------
        datapath : str or pathlib path
            Path to directory containing data. For Raspberry Shakes, 
            this is the directory where the channel folders are located.
        starttime : str or time object
            Start time for the data traces/streams
        date : str, tuple, or date object
            Date for which to read in the data traces. 
            If string, will attempt to decode to convert to a date format.
            If tuple, assumes first item is day of year (DOY) and second item is year 
            If date object, will read it in directly.
        args : dict, optional in some cases
            For raspberry shakes using EHZ, EHN, EHE channels, this is not needed.
            Otherwise, use the following keys:
                net : the station's network (AM for raspberry shakes)
                sta : the station name (unique per raspberry shake)
                loc : two-digit integer; by default 00
                cha : channel names in a list. By default, raspberry shake should be ['EHE', 'EHN', 'EHZ']
                d   : unknown designator. For raspberry shake, this will always be "D"
                year: integer year
                doy : integer day of year
        inst : str {'raspshake}
            The type of instrument from which the data is reading. Currently, only raspberry shake supported
        Returns
        -------
        rawDataIN : obspy data stream with 3 traces: Z (vertical), N (North-south), and E (East-west)
        
        """

    datapath = checkifpath(datapath)

    #Need to put dates and times in right formats first
    if type(date) is datetime.datetime:
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

    filestart = datetime.datetime(date.year, date.month, date.day,
                                int(filestart.split(':')[0]), int(filestart.split(':')[1]), int(float(filestart.split(':')[2])))

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
                    meta = {'station': args['sta'], 
                            'network': args['net'], 
                            'channel': args['cha'][i],
                            'location':'00',
                            'starttime':filestart,
                            'delta':1/100
                            }
                    st = obspy.read(str(f))
                    tr = (st[0])
                    #tr= obspy.Trace(tr.data,header=meta)
                    traceList.append(tr)
            rawDataIN = obspy.Stream(traceList)
            rawDataIN.attach_response(inv)

    return rawDataIN

#Read in metadata .inv file, specifically for RaspShake
def updateShakeMetadata(filepath, network='AM', station='RAC84', channels=['EHZ', 'EHN', 'EHE'], 
                    startdate=str(datetime.datetime(2022,1,1)), enddate=str(datetime.datetime.today()), 
                    lon = '-88.2290526', lat = '40.1012122', elevation = '755', depth='0'):
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


    tree.write(outfile, xml_declaration=True, method='xml',encoding='UTF-8')
    return outfile

def print_peak_report(_station_header, _report_header, _peak, _reportinfo, _min_rank):
    """print a report of peak parameters"""
    _index = list()
    _rank = list()

    if report_information:
        report_file_name = os.path.join(setParams.reportDirectory, fileLib.baselineFileName(
            network, station, location, channel))

        # In mac(python 3) the following statement works perfectly with just open without encoding, but
        # in windows(w10, python3) this is is not an option and we have to include the encoding='utf-8' param.
        report_file = open(report_file_name, 'w', encoding='utf-8')

        # Write the report to the report file.
        report_file.write('\n\nPeaks:\n'
                          'Parameters and ranking (A0: peak amplitude, f0: peak frequency, {}: satisfied):\n\n'
                          '\t- amplitude clarity conditions:\n'
                          '\t\t. there exist one frequency f-, lying between f0/4 and f0, such that A0 / A(f-) > 2\n'
                          '\t\t. there exist one frequency f+, lying between f0 and 4*f0, such that A0 / A(f+) > 2\n'
                          '\t\t. A0 > 2\n\n'
                          '\t- amplitude stability conditions:\n'
                          '\t\t. peak appear within +/-5% on HVSR curves of mean +/- one standard deviation (f0+/f0-)\n'
                          '\t\t. {}f lower than a frequency dependent threshold {}(f)\n'
                          '\t\t. {}A lower than a frequency dependent threshold log {}(f)\n'.
                          format(utilities.check_mark(), utilities.get_char('sigma'), utilities.get_char('epsilon'), utilities.get_char('sigma'), 
                                 utilities.get_char('teta')))

        # Also output the report to the terminal.
        print('\n\nPeaks:\n'
              'Parameters and ranking (A0: peak amplitude, f0: peak frequency, {}: satisfied)):\n\n'
              '\t- amplitude clarity conditions:\n'
              '\t\t. there exist one frequency f-, lying between f0/4 and f0, such that A0 / A(f-) > 2\n'
              '\t\t. there exist one frequency f+, lying between f0 and 4*f0, such that A0 / A(f+) > 2\n'
              '\t\t. A0 > 2\n\n'
              '\t- amplitude stability conditions:\n'
              '\t\t. peak appear within +/-5% on HVSR curves of mean +/- one standard deviation (f0+/f0-)\n'
              '\t\t. {}f lower than a frequency dependent threshold {}(f)\n'
              '\t\t. {}A lower than a frequency dependent threshold log {}(f)\n'.
              format(utilities.check_mark(), utilities.get_char('sigma'), utilities.get_char('epsilon'), utilities.get_char('sigma'), utilities.get_char('teta')), 
              flush=True)

    for _i, _peak_value in enumerate(_peak):
        _index.append(_i)
        _rank.append(_peak_value['Score'])
    _list = list(zip(_rank, _index))
    _list.sort(reverse=True)

    if report_information:
        report_file.write('\n%47s %10s %22s %12s %12s %32s %32s %27s %22s %17s'
                          % ('Net.Sta.Loc.Chan', '    f0    ', '        A0 > 2        ', '     f-      ', '    f+     ',
                             '     f0- within ±5% of f0 &     ', '     f0+ within ±5% of f0       ',
                             utilities.get_char('sigma') +
                             'f < ' + utilities.get_char('epsilon') + ' * f0      ', utilities.get_char('sigma') + 'log HVSR < log' +
                             utilities.get_char('teta') + '    ', '   Score/Max.    \n'))
        report_file.write('%47s %10s %22s %12s %12s %32s %32s %27s %22s %17s\n'
                          % (47 * utilities.utilities.separator_character, 10 * utilities.utilities.separator_character, 22 * utilities.utilities.separator_character,
                             12 * utilities.separator_character, 12 * utilities.separator_character, 32 * utilities.separator_character,
                             32 * utilities.separator_character, 27 * utilities.separator_character, 22 * utilities.separator_character,
                             7 * utilities.separator_character))

        print('\n%47s %10s %22s %12s %12s %32s %32s %27s %22s %17s'
                          % ('Net.Sta.Loc.Chan', '    f0    ', '        A0 > 2        ', '     f-      ', '    f+     ',
                             '     f0- within ±5% of f0 &     ', '     f0+ within ±5% of f0       ',
                             utilities.get_char('sigma') +
                             'f < ' + utilities.get_char('epsilon') + ' * f0      ', utilities.get_char('sigma') + 'log HVSR < log' +
                             utilities.get_char('teta') + '    ', '   Score/Max.    \n'), flush=True)

        print('%47s %10s %22s %12s %12s %32s %32s %27s %22s %17s\n'
              % (47 * utilities.separator_character, 10 * utilities.separator_character, 22 * utilities.separator_character,
                 12 * utilities.separator_character, 12 * utilities.separator_character, 32 * utilities.separator_character,
                 32 * utilities.separator_character, 27 * utilities.separator_character, 22 * utilities.separator_character,
                 7 * utilities.separator_character), flush=True)

    _peak_visible = list()
    for _i, _list_value in enumerate(_list):
        _index = _list_value[1]
        _peak_found = _peak[_index]
        if float(_peak_found['Score']) < _min_rank:
            continue
        else:
            _peak_visible.append(True)

        report_file.write('%47s %10.3f %22s %12s %12s %32s %32s %27s %22s %12d/%0d\n' %
              (_station_header, _peak_found['f0'], _peak_found['Report']['A0'], _peak_found['f-'], _peak_found['f+'],
               _peak_found['Report']['P-'], _peak_found['Report']['P+'], _peak_found['Report']['Sf'],
               _peak_found['Report']['Sa'], _peak_found['Score'], utilities.max_rank))

        print('%47s %10.3f %22s %12s %12s %32s %32s %27s %22s %12d/%0d\n' %
              (_station_header, _peak_found['f0'], _peak_found['Report']['A0'], _peak_found['f-'], _peak_found['f+'],
               _peak_found['Report']['P-'], _peak_found['Report']['P+'], _peak_found['Report']['Sf'],
               _peak_found['Report']['Sa'], _peak_found['Score'], utilities.max_rank), flush=True)

    if len(_list) <= 0 or len(_peak_visible) <= 0:
        report_file.write('%47s\n' % _station_header)
        report_file.close()

        print('%47s\n' % _station_header, flush=True)
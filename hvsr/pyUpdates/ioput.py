'''
Functions for reading in data
'''
import sys
import os
import datetime
import pathlib

import obspy

import hvsr.pyUpdates.utilities as utilities
import hvsr.pyUpdates.fileLib as fileLib
import hvsr.pyUpdates.msgLib as msgLib
import hvsr.pyUpdates.setParams as setParams

#utilities.get_args(sys.argv) #This is for command-line?
args = setParams.args

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
            print('Converted string to pathlib path') #Assume a string was input rather than pathlib object
        except:
            msgLib.error('Input cannot be converted to pathlib path', 0)
    return filepath

#Reads in traces to obspy stream
def fetchdata(datapath, starttime, endtime, date=datetime.datetime.today(), doy='', year='', args=args, inst='raspshake'):
    """Fetch ambient seismic data from a source to read into obspy stream
        Parameters
        ----------
        datapath : str or pathlib path
            Path to directory containing data. For Raspberry Shakes, 
            this is the directory where the channel folders are located.
        starttime : str or time object
            Start time for the data traces/streams
        endtime : str or time object
            End time for the data traces/streams
        date : str, int, or date object
            Date for which to read in the data traces. 
            If string, will attempt to decode to convert to a date format.
            If int, assumes it is day of year (DOY).
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

    if type(date) is int:
        doy = date
        year = datetime.datetime.now().year()
        print('Assuming current year')
    else: #FOR NOW, need to update
        date = datetime.datetime.now()
        doy = date.timetuple().tm_yday
        year = date.year()

    if inst=='raspshake':
        folderList = []
        folderPathList = []
        for child in datapath.iterdir():
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
            
            traceList = []
            for i, f in enumerate(filepaths):
                meta = {'station': args['sta'], 'network': args['net'], 'channel': args['cha'][i]}

                tr = obspy.read(str(f), format='MSEED')
                tr= obspy.Trace(header=meta)
                traceList.append(tr)
                
            rawDataIN = obspy.Stream(traceList)

    return rawDataIN

report_information = int(utilities.get_param(args, 'report_information', msgLib, 1, be_verbose=setParams.verbose))

# network, station, and location to process.
network = utilities.get_param(args, 'net', msgLib, None)
if network is None:
    msgLib.error('network not defined!', 1)
    sys.exit()
station = utilities.get_param(args, 'sta', msgLib, None)
if station is None:
    msgLib.error('station not defined!', 1)
    sys.exit()
location = utilities.get_param(args, 'loc', msgLib, '*')
if location is None:
    msgLib.error('location not defined!', 1)
    sys.exit()

channel='NEED TO DEFINE CHANNEL'#########################################




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
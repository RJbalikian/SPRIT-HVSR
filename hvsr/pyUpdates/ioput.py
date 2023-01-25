'''
Functions for reading in data
'''

import utilities
import fileLib
import msgLib
import setParams

import sys
import os

args = utilities.get_args(sys.argv)
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
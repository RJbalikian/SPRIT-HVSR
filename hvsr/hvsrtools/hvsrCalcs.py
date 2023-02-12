
import math
import urllib
import sys

import numpy as np
from scipy.signal import argrelextrema


import hvsr.hvsrtools.msgLib as msgLib
import hvsr.hvsrtools.powspecdens as powspecdens
import hvsr.hvsrtools.utilities as utilities
import hvsr.hvsrtools.setParams as setParams

args = utilities.get_args(sys.argv)
#target = '.'.join([network, station, location, channel, '*'])
xtype = utilities.get_param(args, 'xtype', msgLib, setParams.xtype)



def check_y_range(_y, _low, _high):
    """check the PSD values to see if they are within the range"""
    _ok = list()
    _not_ok = list()

    # use subtract operator to see if y and _low/_high are crossing
    for _i, _value in enumerate(_y):
        _l = [_a - _b for _a, _b in zip(_value, _low)]
        if min(_l) < 0:
            _not_ok.append(_i)
            continue

        _h = [_a - _b for _a, _b in zip(_value, _high)]
        if max(_h) > 0:
            _not_ok.append(_i)
            continue

        _ok.append(_i)

    return _ok, _not_ok

def __get_hvsr_original(_dbz, _db1, _db2, _x, use_method=4):
    """
    H is computed based on the selected use_method see: https://academic.oup.com/gji/article/194/2/936/597415
        use_method:
           (1) DFA
           (2) arithmetic mean, that is, H ≡ (HN + HE)/2
           (3) geometric mean, that is, H ≡ √HN · HE, recommended by the SESAME project (2004)
           (4) vector summation, that is, H ≡ √H2 N + H2 E
           (5) quadratic mean, that is, H ≡ √(H2 N + H2 E )/2
           (6) maximum horizontal value, that is, H ≡ max {HN, HE}
    """
    _pz = powspecdens.get_power(_dbz, _x)
    _p1 = powspecdens.get_power(_db1, _x)
    _p2 = powspecdens.get_power(_db2, _x)

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

def get_hvsr(_dbz, _db1, _db2, _x, use_method=4):
    """
    H is computed based on the selected use_method see: https://academic.oup.com/gji/article/194/2/936/597415
        use_method:
           (1) DFA
           (2) arithmetic mean, that is, H ≡ (HN + HE)/2
           (3) geometric mean, that is, H ≡ √HN · HE, recommended by the SESAME project (2004)
           (4) vector summation, that is, H ≡ √H2 N + H2 E
           (5) quadratic mean, that is, H ≡ √(H2 N + H2 E )/2
           (6) maximum horizontal value, that is, H ≡ max {HN, HE}
    """
    _pz = get_power(_dbz, _x)
    _p1 = get_power(_db1, _x)
    _p2 = get_power(_db2, _x)
    #_dx = np.diff(_x)[0]

    #_pz = np.mean(_dbz)
    #_p1 = np.mean(_db1)
    #_p2 = np.mean(_db2)

    #_pz = _dbz #powspecdens.get_power(_dbz, _x)
    #_p1 = _db1 #powspecdens.get_power(_db1, _x)
    #_p2 = _db2 #powspecdens.get_power(_db2, _x)

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

def remove_db(_db_value):
    """convert dB power to power"""
    _values = list()
    for _d in _db_value:
        _values.append(10 ** (float(_d) / 10.0))
    return _values

def get_power(_db, _x):
    """calculate HVSR
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

    NOTE: PSD is equal to the power divided by the width of the bin
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
    _dx = np.diff(_x)[0]
    #print(_dx)
    #_p = np.mean(remove_db(_db))
    _p = abs(np.multiply(np.mean(remove_db(_db)), _dx))
    #_p = np.multiply(np.mean(remove_db(_db)), _dx)
    #print(_p)
    return _p

def find_peaks(_y):
    """find peaks"""
    _index_list = argrelextrema(np.array(_y), np.greater)

    return _index_list[0]

def init_peaks(_x, _y, _index_list, _hvsr_band, _peak_water_level):
    """initialize peaks"""
    _peak = list()
    for _i in _index_list:
        if _y[_i] > _peak_water_level[_i] and (_hvsr_band[0] <= _x[_i] <= _hvsr_band[1]):
            _peak.append({'f0': float(_x[_i]), 'A0': float(_y[_i]), 'f-': None, 'f+': None, 'Sf': None, 'Sa': None,
                          'Score': 0, 'Report': {'A0': '', 'Sf': '', 'Sa': '', 'P+': '', 'P-': ''}})
    return _peak

def check_clarity(_x, _y, _peak, do_rank=False):
    """
       test peaks for satisfying amplitude clarity conditions as outlined by SESAME 2004:
           - there exist one frequency f-, lying between f0/4 and f0, such that A0 / A(f-) > 2
           - there exist one frequency f+, lying between f0 and 4*f0, such that A0 / A(f+) > 2
           - A0 > 2
    """
    global max_rank

    # Peaks with A0 > 2.
    if do_rank:
        max_rank += 1
    _a0 = 2.0
    for _i in range(len(_peak)):

        if float(_peak[_i]['A0']) > _a0:
            _peak[_i]['Report']['A0'] = '%10.2f > %0.1f %1s' % (_peak[_i]['A0'], _a0, utilities.check_mark())
            _peak[_i]['Score'] += 1
        else:
            _peak[_i]['Report']['A0'] = '%10.2f > %0.1f  ' % (_peak[_i]['A0'], _a0)

    # Test each _peak for clarity.
    if do_rank:
        max_rank += 1
    for _i in range(len(_peak)):
        _peak[_i]['f-'] = '-'
        for _j in range(len(_x) - 1, -1, -1):

            # There exist one frequency f-, lying between f0/4 and f0, such that A0 / A(f-) > 2.
            if (float(_peak[_i]['f0']) / 4.0 <= _x[_j] < float(_peak[_i]['f0'])) and \
                    float(_peak[_i]['A0']) / _y[_j] > 2.0:
                _peak[_i]['f-'] = '%10.3f %1s' % (_x[_j], utilities.check_mark())
                _peak[_i]['Score'] += 1
                break

    if do_rank:
        max_rank += 1
    for _i in range(len(_peak)):
        _peak[_i]['f+'] = '-'
        for _j in range(len(_x) - 1):

            # There exist one frequency f+, lying between f0 and 4*f0, such that A0 / A(f+) > 2.
            if float(_peak[_i]['f0']) * 4.0 >= _x[_j] > float(_peak[_i]['f0']) and \
                    float(_peak[_i]['A0']) / _y[_j] > 2.0:
                _peak[_i]['f+'] = '%10.3f %1s' % (_x[_j], utilities.check_mark())
                _peak[_i]['Score'] += 1
                break

    return _peak

def check_freq_stability(_peak, _peakm, _peakp):
    """
       test peaks for satisfying stability conditions as outlined by SESAME 2004:
           - the _peak should appear at the same frequency (within a percentage ± 5%) on the H/V
             curves corresponding to mean + and – one standard deviation.
    """
    global max_rank

    #
    # check σf and σA
    #
    max_rank += 1

    _found_m = list()
    for _i in range(len(_peak)):
        _dx = 1000000.
        _found_m.append(False)
        _peak[_i]['Report']['P-'] = '- &'
        for _j in range(len(_peakm)):
            if abs(_peakm[_j]['f0'] - _peak[_i]['f0']) < _dx:
                _index = _j
                _dx = abs(_peakm[_j]['f0'] - _peak[_i]['f0'])
            if _peak[_i]['f0'] * 0.95 <= _peakm[_j]['f0'] <= _peak[_i]['f0'] * 1.05:
                _peak[_i]['Report']['P-'] = '%0.3f within ±5%s of %0.3f %1s' % (_peakm[_j]['f0'], '%',
                                                                                 _peak[_i]['f0'], '&')
                _found_m[_i] = True
                break
        if _peak[_i]['Report']['P-'] == '-':
            _peak[_i]['Report']['P-'] = '%0.3f within ±5%s of %0.3f %1s' % (_peakm[_i]['f0'], '%',
                                                                             _peak[_i]['f0'], '&')

    _found_p = list()
    for _i in range(len(_peak)):
        _dx = 1000000.
        _found_p.append(False)
        _peak[_i]['Report']['P+'] = '-'
        for _j in range(len(_peakp)):
            if abs(_peakp[_j]['f0'] - _peak[_i]['f0']) < _dx:
                _index = _j
                _dx = abs(_peakp[_j]['f0'] - _peak[_i]['f0'])
            if _peak[_i]['f0'] * 0.95 <= _peakp[_j]['f0'] <= _peak[_i]['f0'] * 1.05:
                if _found_m[_i]:
                    _peak[_i]['Report']['P+'] = '%0.3f within ±5%s of %0.3f %1s' % (
                        _peakp[_j]['f0'], '%', _peak[_i]['f0'], utilities.check_mark())
                    _peak[_i]['Score'] += 1
                else:
                    _peak[_i]['Report']['P+'] = '%0.3f within ±5%s of %0.3f %1s' % (
                        _peakp[_i]['f0'], '%', _peak[_i]['f0'], ' ')
                break
        if _peak[_i]['Report']['P+'] == '-' and len(_peakp) > 0:
            _peak[_i]['Report']['P+'] = '%0.3f within ±5%s of %0.3f %1s' % (
                _peakp[_i]['f0'], '%', _peak[_i]['f0'], ' ')

    return _peak

def check_stability(_stdf, _peak, _hvsr_log_std, rank):
    """
    test peaks for satisfying stability conditions as outlined by SESAME 2004:
       - σf lower than a frequency dependent threshold ε(f)
       - σA (f0) lower than a frequency dependent threshold θ(f),
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
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s' % (_stdf[_i], _e, _this_peak['f0'],
                                                                            utilities.check_mark())
                _this_peak['Score'] += 1
            else:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f  ' % (_stdf[_i], _e, _this_peak['f0'])

            _t = 0.48
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f %1s' % (_hvsr_log_std[_i], _t,
                                                                    utilities.check_mark())
                _this_peak['Score'] += 1
            else:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f  ' % (_hvsr_log_std[_i], _t)

        elif 0.2 <= _this_peak['f0'] < 0.5:
            _e = 0.2
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s' % (_stdf[_i], _e, _this_peak['f0'],
                                                                            utilities.check_mark())
                _this_peak['Score'] += 1
            else:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f  ' % (_stdf[_i], _e, _this_peak['f0'])

            _t = 0.40
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f %1s' % (_hvsr_log_std[_i], _t,
                                                                    utilities.check_mark())
                _this_peak['Score'] += 1
            else:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f  ' % (_hvsr_log_std[_i], _t)

        elif 0.5 <= _this_peak['f0'] < 1.0:
            _e = 0.15
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s' % (_stdf[_i], _e, _this_peak['f0'],
                                                                            utilities.check_mark())
                _this_peak['Score'] += 1
            else:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f  ' % (_stdf[_i], _e, _this_peak['f0'])

            _t = 0.3
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f %1s' % (_hvsr_log_std[_i], _t, utilities.check_mark())
                _this_peak['Score'] += 1
            else:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f  ' % (_hvsr_log_std[_i], _t)

        elif 1.0 <= _this_peak['f0'] <= 2.0:
            _e = 0.1
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s' % (_stdf[_i], _e, _this_peak['f0'],
                                                                            utilities.check_mark())
                _this_peak['Score'] += 1
            else:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f  ' % (_stdf[_i], _e, _this_peak['f0'])

            _t = 0.25
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f %1s' % (_hvsr_log_std[_i], _t, utilities.check_mark())
                _this_peak['Score'] += 1
            else:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f  ' % (_hvsr_log_std[_i], _t)

        elif _this_peak['f0'] > 0.2:
            _e = 0.05
            if _stdf[_i] < _e * _this_peak['f0']:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f %1s' % (_stdf[_i], _e, _this_peak['f0'],
                                                                            utilities.check_mark())
                _this_peak['Score'] += 1
            else:
                _peak[_i]['Report']['Sf'] = '%10.4f < %0.2f * %0.3f  ' % (_stdf[_i], _e, _this_peak['f0'])

            _t = 0.2
            if _hvsr_log_std[_i] < _t:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f %1s' % (_hvsr_log_std[_i], _t, utilities.check_mark())
                _this_peak['Score'] += 1
            else:
                _peak[_i]['Report']['Sa'] = '%10.4f < %0.2f  ' % (_hvsr_log_std[_i], _t)
    return _peak

def get_pdf(_url, _verbose):
    """get PDF"""
    _x_values = list()
    _y_values = list()
    _x = list()
    _y = list()
    _p = list()

    if _verbose >= 0:
        msgLib.info('requesting:' + _url)
    try:
        _link = urllib.request.urlopen(_url)
    except Exception as _e:
        msgLib.error('\n\nReceived HTTP Error code: {}\n{}'.format(_e.code, _e.reason), 1)
        if _e.code == 404:
            _url_items = _url.split('&')
            _starttime = [x for x in _url_items if x.startswith('starttime')]
            _endtime = [x for x in _url_items if x.startswith('endtime')]
            msgLib.error('Error 404: PDF not found in the range {} and {} when requested:\n{}'.format(
                _starttime.split('=')[1], _endtime.split('=')[1], _url), 1)
        elif _e.code == 413:
            #print('Note: Either use the run argument "n" to split the requested date range to smaller intervals'
            #      '\nCurrent "n"" value is: {}. Or request a shorter time interval.'.format(n), flush=True)
            sys.exit(1)
        #msgLib.error('failed on target {} {}'.format(target, URL), 1) #fIX THIS?
        return _x, _y, _p

    if _verbose >= 0:
        msgLib.info('PDF waiting for reply....')

    _data = _link.read().decode()
    _link.close()
    _lines = _data.split('\n')
    _last_frequency = ''
    _line_count = 0
    _non_blank_last_line = 0
    _hits_list = list()
    _power_list = list()
    if len(_lines[-1].strip()) <= 0:
        _non_blank_last_line = 1
    for _line in _lines:
        _line_count += 1
        if len(_line.strip()) <= 0:
            continue
        if _line[0] == '#' or ',' not in _line:
            continue
        (_freq, _power, _hits) = _line.split(',')
        if _last_frequency == '':
            _last_frequency = _freq.strip()
            _power_list = list()
            _power_list.append(float(_power))
            _hits_list = list()
            _hits_list.append(int(_hits))
        elif _last_frequency == _freq.strip():
            _power_list.append(float(_power))
            _hits_list.append(int(_hits))
        if _last_frequency != _freq.strip() or _line_count == len(_lines) - _non_blank_last_line:
            _total_hits = sum(_hits_list)
            _y_values.append(np.array(_hits_list) * 100.0 / _total_hits)
            if xtype == 'period':
                last_x = 1.0 / float(_last_frequency)
                _x_values.append(last_x)
            else:
                last_x = float(_last_frequency)
                _x_values.append(last_x)
            for _i in range(len(_hits_list)):
                _y.append(float(_power_list[_i]))
                _p.append(float(_hits_list[_i]) * 100.0 / float(_total_hits))
                _x.append(last_x)

            _last_frequency = _freq.strip()
            _power_list = list()
            _power_list.append(float(_power))
            _hits_list = list()
            _hits_list.append(int(_hits))
    return _x, _y, _p
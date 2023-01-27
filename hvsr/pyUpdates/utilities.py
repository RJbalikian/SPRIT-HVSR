'''
Various functions to do various necessary, behind-the-scenes stuff
'''
import time
import sys
from datetime import datetime


import hvsr.pyUpdates.msgLib as msgLib

#Main variables
greek_chars = {'sigma': u'\u03C3', 'epsilon': u'\u03B5', 'teta': u'\u03B8'}
channel_order = {'Z': 0, '1': 1, 'N': 1, '2': 2, 'E': 2}
separator_character = '='

t0 = time.time()
display = True
max_rank = 0
plotRows = 4


def check_mark():
    """The default Windows terminal is not able to display the check mark character correctly.
       This function returns another displayable character if platform is Windows"""
    check = get_char(u'\u2714')
    if sys.platform == 'win32':
        check = get_char(u'\u039E')
    return check

def get_char(in_char):
    """Output character with proper encoding/decoding"""
    if in_char in greek_chars.keys():
        out_char = greek_chars[in_char].encode(encoding='utf-8')
    else:
        out_char = in_char.encode(encoding='utf-8')
    return out_char.decode('utf-8')


def time_it(_t):
    """Compute elapsed time since the last call."""
    t1 = time.time()
    dt = t1 - _t
    t = _t
    if dt > 0.05:
        print(f'[TIME] {dt:0.1f} s', flush=True)
        t = t1
    return t

def date_range(_start, _end, _interval):
    """Break an interval to date ranges
       this is used to avoid large requests that get rejected.
    """
    if _interval <= 1:
        _date_list = [_start, _end]
    else:
        _date_list = list()
        start_t = datetime.strptime(_start, '%Y-%m-%d')
        end_t = datetime.strptime(_end, '%Y-%m-%d')
        diff = (end_t - start_t) / _interval
        if diff.days <= 1:
            _date_list = [_start, _end]
        else:
            for _index in range(_interval):
                _date_list.append((start_t + diff * _index).strftime('%Y-%m-%d'))
            _date_list.append(end_t.strftime('%Y-%m-%d'))
    return _date_list

def get_args(_arg_list):
    """get the run arguments"""
    _args = {}
    for _i in range(1, len(_arg_list)):
        try:
            _key, _value = _arg_list[_i].split('=')
            _args[_key] = _value
        except Exception as _e:
            msgLib.error('Bad parameter: {}, will use the default\n{}'.format(_arg_list[_i], _e), 1)
            continue
    return _args


def get_param(_args, _key, _msg_lib, _value, be_verbose=-1):
    """get a run argument for the given _key"""
    if _key in _args.keys():
        if be_verbose >= 0:
            print (_key, _args[_key])
        return _args[_key]
    elif _value is not None:
        return _value
    else:
        _msg_lib.error('missing parameter {}'.format(_key), 1)
        #usage()
        #sys.exit()
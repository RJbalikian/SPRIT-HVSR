import numpy as np
'''
Functions that work directly on getting the psd
'''

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
    _dx = np.diff(_x)[0]
    _p = np.multiply(np.mean(remove_db(_db)), _dx)
    return _p
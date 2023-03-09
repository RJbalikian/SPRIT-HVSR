#__init__.py
"""
This module analysis ambient seismic data using the Horizontal to Vertical Spectral Ratio (HVSR) technique
"""

import sprit

from sprit.sprit import(
    check_mark,
    get_char,
    time_it,
    message,
    error,
    warning,
    info,
    checkifpath,
    input_param,
    update_shake_metadata,
    setup_colab,
    get_metadata,
    fetch_data,
    trim_data,
    generate_ppsds,
    process_hvsr,
    hvplot,
    check_peaks,
    print_report
)

__all__ =('sprit',
    'check_mark',
    'get_char',
    'time_it',
    'message',
    'error',
    'warning',
    'info',
    'checkifpath',
    'input_param',
    'update_shake_metadata',
    'setup_colab',
    'get_metadata',
    'fetch_data',
    'trim_data',
    'generate_ppsds',
    'process_hvsr',
    'hvplot',
    'check_peaks',
    'print_report'
)

__author__ = 'Riley Balikian'
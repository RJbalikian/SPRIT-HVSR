#__init__.py
"""
This module analysis ambient seismic data using the Horizontal to Vertical Spectral Ratio (HVSR) technique
"""
try:
    import sprit.sprit_utils as sprit_utils
    import sprit.sprit_tkinter_ui as sprit_tkinter_ui
    import sprit.sprit_hvsr as sprit_hvsr
    import sprit.sprit_jupyter_UI as sprit_jupyter_UI
    import sprit.sprit_plot as sprit_plot    
    import sprit.sprit_calibration as sprit_calibration
except Exception as e:
    import sprit_utils
    import sprit.sprit_tkinter_ui as sprit_tkinter_ui
    import sprit_hvsr
    import sprit_jupyter_UI
    import sprit_plot
    import sprit_calibration

from sprit.sprit_hvsr import(
    run,
    calculate_azimuth,
    export_data,
    export_settings,
    import_data,
    import_settings,
    input_params,
    gui,
    get_metadata,
    fetch_data,
    batch_data_read,
    generate_psds,
    process_hvsr,
    plot_azimuth,
    plot_hvsr,
    read_tromino_files,
    remove_noise,
    remove_outlier_curves,
    check_peaks,
    get_report,
    update_elevation,
    HVSRData,
    HVSRBatch,
)

from sprit.sprit_utils import(
    assert_check,
    check_gui_requirements,
    checkifpath,
    check_mark,
    check_tsteps,
    check_xvalues,
    format_time,
    get_char,
    get_default_args,
    has_required_channels,
    make_it_classy,
    read_from_RS,
    time_it,
    x_mark
)

from sprit.sprit_tkinter_ui import(
    catch_errors
)

from sprit.sprit_jupyter_UI import(
    create_jupyter_ui
    )

from sprit.sprit_plot import(
    plot_preview,
    plot_results,
    plot_outlier_curves,
    parse_plot_string,
    plot_depth_curve,
    plot_cross_section,
    )
from sprit.sprit_calibration import(
    calculate_depth,
    calibrate,
)


__all__ =('sprit_hvsr',
            'run',
            'calculate_azimuth',
            'check_mark',
            'get_char',
            'time_it',
            'checkifpath',
            'export_data',
            'export_settings',
            'import_data',
            'import_settings',
            'input_params',
            'gui',
            'get_metadata',
            'has_required_channels',
            'fetch_data',
            'batch_data_read',
            'generate_psds',
            'process_hvsr',
            'plot_azimuth',
            'plot_hvsr',
            'read_tromino_files',
            'remove_noise',
            'remove_outlier_curves',
            'check_peaks',
            'get_report',
            'update_elevation',
            'HVSRData',
            'HVSRBatch',
        'sprit_utils',
            'assert_check',
            'check_gui_requirements',
            'checkifpath',
            'check_mark',
            'check_tsteps',
            'check_xvalues',
            'format_time',
            'get_char',
            'get_default_args',
            'has_required_channels',
            'make_it_classy',
            'read_from_RS',
            'time_it',
            'x_mark',
        'sprit_tkinter_ui',
            'catch_errors',
        'sprit_jupyter_UI',
            'create_jupyter_ui',
        'sprit_plot',
            'plot_preview',
            'plot_results',
            'plot_outlier_curves',
            'parse_plot_string',
            'plot_depth_curve',
            'plot_cross_section',
        'sprit_calibration',
            'calculate_depth',
            'calibrate',
            )


run.__doc__ = sprit_utils._run_docstring()
__author__ = 'Riley Balikian'
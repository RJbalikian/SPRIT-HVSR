#__init__.py
"""
This module enables analysis of ambient seismic data using the Horizontal to Vertical Spectral Ratio (HVSR) technique.
"""

__version__ = "2.6.5"

try:
    import sprit.sprit_utils as sprit_utils
    import sprit.sprit_tkinter_ui as sprit_tkinter_ui
    import sprit.sprit_hvsr as sprit_hvsr
    import sprit.sprit_jupyter_UI as sprit_jupyter_UI
    import sprit.sprit_plot as sprit_plot    
    import sprit.sprit_calibration as sprit_calibration
except Exception:
    import sprit_utils
    import sprit.sprit_tkinter_ui as sprit_tkinter_ui
    import sprit_hvsr
    import sprit_jupyter_UI
    import sprit_plot
    import sprit_calibration

from sprit.sprit_hvsr import (
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
    HVSRData,
    HVSRBatch,
)

from sprit.sprit_jupyter_UI import (
    create_jupyter_ui
    )

from sprit.sprit_plot import (
    parse_plot_string,
    plot_input_stream,
    plot_outlier_curves,
    plot_results,
    plot_depth_curve,
    plot_cross_section,
    )

from sprit.sprit_calibration import (
    calculate_depth,
    calibrate,
)


__all__ = ('sprit_hvsr',
            'run',
            'calculate_azimuth',
            'export_data',
            'export_settings',
            'import_data',
            'import_settings',
            'input_params',
            'gui',
            'get_metadata',
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
            'HVSRData',
            'HVSRBatch',
        'sprit_utils',
        'sprit_tkinter_ui',
        'sprit_jupyter_UI',
            'create_jupyter_ui',
        'sprit_plot',
            'plot_input_stream',
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
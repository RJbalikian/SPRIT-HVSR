#__init__.py
"""
This module enables analysis of ambient seismic data using the Horizontal to Vertical Spectral Ratio (HVSR) technique.
"""

__version__ = "3.0.1"

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
    export_hvsr,
    export_report,
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
    update_resp_file,
    HVSRData,
    HVSRBatch,
)

from sprit.sprit_jupyter_UI import (
    create_jupyter_ui
    )

from sprit.sprit_plot import (
    plot_cross_section,
    plot_depth_curve,
    plot_input_stream,
    plot_outlier_curves,
    parse_plot_string,
    plot_results_plotly,
    )

from sprit.sprit_calibration import (
    calculate_depth,
    calibrate,
)


__all__ = ('sprit_hvsr',
            'run',
            'calculate_azimuth',
            'export_data',
            'export_hvsr',
            'export_report',
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
            'update_elevation',
            'update_resp_file',
            'HVSRData',
            'HVSRBatch',
        'sprit_utils',
        'sprit_tkinter_ui',
        'sprit_jupyter_UI',
            'create_jupyter_ui',
        'sprit_plot',
            'plot_cross_section',
            'plot_depth_curve',
            'plot_input_stream',
            'plot_outlier_curves',
            'parse_plot_string',
            'plot_results_plotly',
        'sprit_calibration',
            'calculate_depth',
            'calibrate',
            )


run.__doc__ = sprit_utils._run_docstring()
__author__ = 'Riley Balikian'
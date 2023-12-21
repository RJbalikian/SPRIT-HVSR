"""Functions to create jupyter notebook widget UI
"""

import datetime
import inspect
from zoneinfo import available_timezones

import ipywidgets as widgets
from IPython.display import display
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
import plotly.subplots as subplots
from scipy import signal

try: #For distribution
    from sprit import sprit_utils
    from sprit import sprit_hvsr
except: #For local testing
    import sprit_hvsr 
    import sprit_utils


OBSPY_FORMATS =  ['AH', 'ALSEP_PSE', 'ALSEP_WTH', 'ALSEP_WTN', 'CSS', 'DMX', 'GCF', 'GSE1', 'GSE2', 'KINEMETRICS_EVT', 'KNET', 'MSEED', 'NNSA_KB_CORE', 'PDAS', 'PICKLE', 'Q', 'REFTEK130', 'RG16', 'SAC', 'SACXY', 'SEG2', 'SEGY', 'SEISAN', 'SH_ASC', 'SLIST', 'SU', 'TSPAIR', 'WAV', 'WIN', 'Y']

def get_default(func, param):
    return inspect.signature(func).parameters[param].default

def create_jupyter_ui():

    ui_width = 20
    ui_height= 12

    # INPUT TAB
    # Create a VBox for the accordions
    input_accordion_box = widgets.VBox()
    input_accordion = widgets.Accordion()

    # Metadata accordion
    metadata_grid = widgets.GridspecLayout(6, 10)
    network_textbox = widgets.Text(description='Network:',
                                    placeholder=get_default(sprit_hvsr.input_params, 'network'),
                                    value=get_default(sprit_hvsr.input_params, 'network'),
                                    tooltip="input_params(network)")
    metadata_grid[0,0] = network_textbox

    station_textbox = widgets.Text(description='Station:',
                                    placeholder=get_default(sprit_hvsr.input_params, 'station'),
                                    value=get_default(sprit_hvsr.input_params, 'station'))
    metadata_grid[1,0] = station_textbox

    location_textbox = widgets.Text(description='Location:',
                                    placeholder=get_default(sprit_hvsr.input_params, 'loc'),
                                    value=get_default(sprit_hvsr.input_params, 'loc'))
    metadata_grid[2,0] = location_textbox

    z_channel_textbox = widgets.Text(description='Z Channel:',
                                    placeholder=get_default(sprit_hvsr.input_params, 'channels')[0],
                                    value=get_default(sprit_hvsr.input_params, 'channels')[0])
    metadata_grid[3,0] = z_channel_textbox

    e_channel_textbox = widgets.Text(description='E Channel:',
                                    placeholder=get_default(sprit_hvsr.input_params, 'channels')[2],
                                    value=get_default(sprit_hvsr.input_params, 'channels')[2])
    metadata_grid[4,0] = e_channel_textbox

    n_channel_textbox = widgets.Text(description='N Channel:',
                                    placeholder=get_default(sprit_hvsr.input_params, 'channels')[1],
                                    value=get_default(sprit_hvsr.input_params, 'channels')[1])
    metadata_grid[5,0] = n_channel_textbox


    # Acquisition Accordion
    instrument_grid = widgets.GridspecLayout(5, 10)
    # Date Picker labelled "Acquisition Date"
    acquisition_date_picker = widgets.DatePicker(description='Acq.Date:',
                                            placeholder=datetime.datetime.today().date(),
                                            value=datetime.datetime.today().date())
    instrument_grid[0,0] = acquisition_date_picker

    # Label that shows the Date currently selected in the Date Picker
    acquisition_doy = widgets.FloatText(description='DOY',
                                                placeholder=f"{acquisition_date_picker.value.timetuple().tm_yday}",
                                                value=f"{acquisition_date_picker.value.timetuple().tm_yday}",
                                                layout=widgets.Layout(width='auto'))
    instrument_grid[0,1] = acquisition_doy

    # Time selector (hour and minute) labelled "Start Time".
    start_time_picker = widgets.TimePicker(description='Start Time:',
                                            placeholder=datetime.time(0,0,0),
                                            value=datetime.time(0,0,0),
                                            layout=widgets.Layout(width='auto'))
    instrument_grid[1,0] = start_time_picker

    # Time selector (hour and minute) labelled "End Time". Same as Start Time otherwise.
    end_time_picker = widgets.TimePicker(description='End Time:',
                                        placeholder=datetime.time(23,59),
                                        value=datetime.time(23,59),
                                        layout=widgets.Layout(width='auto'))
    instrument_grid[2,0] = end_time_picker

    tzlist = list(available_timezones())
    tzlist.sort()
    tzlist.remove('UTC')
    tzlist.remove('US/Central')
    tzlist.insert(0, 'US/Central')
    tzlist.insert(0, 'UTC')
    # A dropdown list with all the items from zoneinfo.available_timezones(), default 'UTC'
    time_zone_dropdown = widgets.Dropdown(options=tzlist,value=get_default(sprit_hvsr.input_params, 'tzone'),
                                            description='Time Zone:',layout=widgets.Layout(width='fill'))
    instrument_grid[3,0] = time_zone_dropdown


    # LOCATION ACCORDION
    location_grid = widgets.GridspecLayout(4, 10)
    # X coordinate input
    xcoord_textbox = widgets.FloatText(description='X Coordinate:', tooltip='xcoord',
                                        value=get_default(sprit_hvsr.input_params, 'xcoord'), 
                                        placeholder=get_default(sprit_hvsr.input_params, 'xcoord'),
                                        layout=widgets.Layout(width='auto'))
    location_grid[0, 0] = xcoord_textbox

    # Y coordinate input
    ycoord_textbox = widgets.FloatText(description='Y Coordinate', tooltip='ycoord:',
                                        value=get_default(sprit_hvsr.input_params, 'ycoord'), 
                                        placeholder=get_default(sprit_hvsr.input_params, 'ycoord'),
                                        layout=widgets.Layout(width='auto'))
    location_grid[1, 0] = ycoord_textbox

    # Z coordinate input
    zcoord_textbox = widgets.FloatText(description='Z Coordinate', tooltip='elevation:',
                                        value=get_default(sprit_hvsr.input_params, 'elevation'),
                                        placeholder=get_default(sprit_hvsr.input_params, 'elevation'),                                     
                                        layout=widgets.Layout(width='auto'))
    location_grid[2, 0] = zcoord_textbox

    # Z coordinate unit input
    elevation_unit_textbox = widgets.Dropdown(options=[('Feet', 'feet'), ('Meters', 'meters')],
                                                value=get_default(sprit_hvsr.input_params, 'elev_unit'),
                                                description='Z Unit:', tooltip='elev_unit',
                                                layout=widgets.Layout(width='auto'))
    location_grid[2, 1] = elevation_unit_textbox

    # Input CRS input
    input_crs_textbox = widgets.Text(description='Input CRS:',
                                        layout=widgets.Layout(width='auto'),
                                        placholder=get_default(sprit_hvsr.input_params, 'input_crs'),
                                        value=get_default(sprit_hvsr.input_params, 'input_crs'))
    location_grid[3, 0] = input_crs_textbox

    # Output CRS input
    output_crs_textbox = widgets.Text(description='Output CRS:',
                                        layout=widgets.Layout(width='auto'),
                                        placholder=get_default(sprit_hvsr.input_params, 'output_crs'),
                                        value=get_default(sprit_hvsr.input_params, 'output_crs'))
    location_grid[3, 1] = output_crs_textbox

    # IO PARAMS ACCORDION
    ioparam_grid = widgets.GridspecLayout(5, 10)

    # Data format (for obspy format to use to read in)
    data_format_dropdown = widgets.Dropdown(
            options=OBSPY_FORMATS,
            value='MSEED',
            description='Data Formats:', layout=widgets.Layout(width='auto'))
    ioparam_grid[0,0] = data_format_dropdown

    hvsr_band_min_box = widgets.FloatText(description='HVSR Band [Hz]', 
                                          placeholder=get_default(sprit_hvsr.input_params, 'hvsr_band')[0], 
                                          value=get_default(sprit_hvsr.input_params, 'hvsr_band')[0])
    hvsr_band_max_box = widgets.FloatText(placeholder=get_default(sprit_hvsr.input_params, 'hvsr_band')[1], 
                                          value=get_default(sprit_hvsr.input_params, 'hvsr_band')[1])
    hvsr_band_hbox = widgets.HBox([hvsr_band_min_box, hvsr_band_max_box],layout=widgets.Layout(width='auto'))
    ioparam_grid[1,:5] = hvsr_band_hbox


    peak_freq_range_min_box = widgets.FloatText(description='Peak Range [Hz]',placeholder=get_default(sprit_hvsr.input_params, 'peak_freq_range')[0], 
                                                value=get_default(sprit_hvsr.input_params, 'peak_freq_range')[0],layout=widgets.Layout(width='auto'))
    peak_freq_range_max_box = widgets.FloatText(placeholder=get_default(sprit_hvsr.input_params, 'peak_freq_range')[1], 
                                                value=get_default(sprit_hvsr.input_params, 'peak_freq_range')[1],layout=widgets.Layout(width='auto'))
    peak_freq_range_hbox = widgets.HBox([peak_freq_range_min_box, peak_freq_range_max_box],layout=widgets.Layout(width='auto'))
    ioparam_grid[2,:5] = peak_freq_range_hbox


    # A dropdown labeled "Detrend type" with "Spline", "Polynomial", or "None"
    detrend_type_dropdown = widgets.Dropdown(options=['Spline', 'Polynomial', 'None'],
                            description='Detrend Type:',  layout=widgets.Layout(width='auto'))
    detrend_order = widgets.FloatText(description='Order:', tooltip='detrend_order', placeholder=get_default(sprit_hvsr.fetch_data, 'detrend_order'), 
                                      value=get_default(sprit_hvsr.fetch_data, 'detrend_order'),layout=widgets.Layout(width='auto'))
    ioparam_grid[3,:1] = detrend_type_dropdown
    ioparam_grid[3,1] = detrend_order

    # A text to specify the trim directory
    trim_directory = widgets.Text(description='Trim Dir.:', value="None",#pathlib.Path().home().as_posix(),
                                    layout=widgets.Layout(width='auto'))
    trim_export_dropdown = widgets.Dropdown(
                options=OBSPY_FORMATS,
                value='MSEED',
                description='Trim Format:', layout=widgets.Layout(width='auto'))
    trim_directory_upload = widgets.FileUpload(
                            accept='', 
                            multiple=False, layout=widgets.Layout(width='auto'))
    ioparam_grid[4,:6] = trim_directory
    ioparam_grid[4, 6:8] = trim_export_dropdown
    ioparam_grid[4, 8] = trim_directory_upload


    # PYTHON API ACCORDION
    inputAPI_grid = widgets.GridspecLayout(2, 10)
    # A text label with "input_params()"
    input_params_prefix = widgets.HTML(value='<style>p {word-wrap: break-word}</style> <p>' + 'input_params' + '</p>', 
                                       layout=widgets.Layout(width='fill', justify_content='flex-end',align_content='flex-start'))
    input_params_call = widgets.HTML(value='<style>p {word-wrap: break-word}</style> <p>' + '()' + '</p>',
                                     layout=widgets.Layout(width='fill', justify_content='flex-start',align_content='flex-start'),)
    #input_params_call =  widgets.Label(value='input_params()', layout=widgets.Layout(width='auto'))
    inputAPI_grid[0, 0] = input_params_prefix
    inputAPI_grid[0, 1:] = input_params_call

    # A text label with "fetch_data()"
    fetch_data_prefix = widgets.HTML(value='<style>p {word-wrap: break-word}</style> <p>' + 'fetch_data' + '</p>', 
                                       layout=widgets.Layout(width='fill', justify_content='flex-end',align_content='flex-start'))
    fetch_data_call = widgets.HTML(value='<style>p {word-wrap: break-word}</style> <p>' + '()' + '</p>',
                                     layout=widgets.Layout(width='fill', justify_content='flex-start',align_content='flex-start'),)
    inputAPI_grid[1, 0] = fetch_data_prefix
    inputAPI_grid[1, 1:] = fetch_data_call

    # Set it all in place
    input_accordion.children = [metadata_grid, instrument_grid, location_grid, ioparam_grid, inputAPI_grid]
    input_accordion.titles = ["Instrument Metadata", "Acquisition Information", "Location Information", "I/O and Parameters", "See Python API Call"]

    input_accordion.layout.width = '99%'


    # ADD THE REST OF THE WIDGETS AROUND THE ACCORDIONS
    # A text box for the site name
    site_name = widgets.Text(description='Site Name:',
                            value='HVSR_Site',
                            placeholder='HVSR_Site',
                            style={'description_width': 'initial'}, layout=widgets.Layout(width='30%'))

    tenpct_spacer = widgets.Button(description='', layout=widgets.Layout(width='20%', visibility='hidden'))

    # Dropdown with different source types 
    data_source_type = widgets.Dropdown(options=[('File', 'file'), ('Raw', 'raw'), ('Batch', 'batch'), ('Directory', 'dir')],
                                            description='Data Source type:',
                                            value='file',orientation='horizontal', 
                                            style={'description_width': 'initial'},
                                            layout=widgets.Layout(width='20%'))

    # Dropdown labeled "Instrument" with options "Raspberry Shake", "Tromino", "Other"
    instrument_dropdown = widgets.Dropdown(options=['Raspberry Shake', 'Tromino', 'Other'],
                                        style={'description_width': 'initial'},
                                        description='Instrument:',layout=widgets.Layout(width='20%'))

    # Whether to print to terminal
    verbose_check = widgets.Checkbox(description='Verbose', value=False, disabled=False, indent=False,
                                    layout=widgets.Layout(width='10%', justify_content='flex-end'))

    # A text box labeled Data Filepath
    data_filepath = widgets.Text(description='Data Filepath:',
                                    placeholder='sample', value='sample',
                                    style={'description_width': 'initial'},layout=widgets.Layout(width='95%'))

    # A button next to it labeled "Browse"
    browse_data_button = widgets.FileUpload(accept='', description='Browse',
                                            multiple=True,layout=widgets.Layout(width='5%'))

    # A text box labeled Metadata Filepath
    metadata_filepath = widgets.Text(description='Metadata Filepath:',
                                        style={'description_width': 'initial'},layout=widgets.Layout(width='95%'))

    # A button next to it labeled "Browse"
    browse_metadata_button = widgets.FileUpload(accept='', description='Browse',
                                            multiple=False,layout=widgets.Layout(width='5%'))

    # A progress bar
    progress_bar = widgets.FloatProgress(value=0.0,min=0.0,max=1.0,
                                    bar_style='info',
                                    orientation='horizontal',layout=widgets.Layout(width='85%'))

    # A dark yellow button labeled "Read Data"
    read_data_button = widgets.Button(description='Read Data',
                                    button_style='warning',layout=widgets.Layout(width='10%'))


    # A forest green button labeled "Process HVSR"
    process_hvsr_button = widgets.Button(description='Run',
                                            button_style='success',layout=widgets.Layout(width='5%'))

    # Update input_param call
    input_param_text = f"""(datapath='{data_filepath.value}', metapath='{metadata_filepath.value}', site='{site_name.value}', network='{network_textbox.value}',
                    station='{station_textbox.value}', loc='{location_textbox.value}', channels={[z_channel_textbox.value, e_channel_textbox.value, n_channel_textbox.value]},
                    acq_date='{acquisition_date_picker.value}', starttime='{start_time_picker.value}', endtime='{end_time_picker.value}', tzone='{time_zone_dropdown.value}',
                    xcoord={xcoord_textbox.value}, ycoord={ycoord_textbox.value}, elevation={zcoord_textbox.value}, depth=0
                    input_crs='{input_crs_textbox.value}', output_crs='{output_crs_textbox.value}', elev_unit='{elevation_unit_textbox.value}',
                    instrument='{instrument_dropdown.value}', hvsr_band={[hvsr_band_min_box.value, hvsr_band_max_box.value]}, 
                    peak_freq_range={[peak_freq_range_min_box.value, peak_freq_range_max_box.value]}, verbose={verbose_check.value})"""
    input_params_call.value='<style>p {word-wrap: break-word}</style> <p>' + input_param_text + '</p>'
    
    # Update fetch_data call
    fetch_data_text = f"""(params=hvsr_data, source={data_source_type.value}, trim_dir={trim_directory.value},
                            export_format={trim_export_dropdown.value}, detrend={detrend_type_dropdown.value}, detrend_order={detrend_order.value}, verbose={verbose_check.value})"""
    fetch_data_call.value='<style>p {word-wrap: break-word}</style> <p>' + fetch_data_text + '</p>'

    site_hbox = widgets.HBox()
    site_hbox.children = [site_name, tenpct_spacer, tenpct_spacer, data_source_type, instrument_dropdown, verbose_check]
    datapath_hbox = widgets.HBox()
    datapath_hbox.children = [data_filepath, browse_data_button]
    metadata_hbox = widgets.HBox()
    metadata_hbox.children = [metadata_filepath, browse_metadata_button]
    progress_hbox = widgets.HBox()
    progress_hbox.children = [progress_bar, read_data_button, process_hvsr_button]

    input_params_vbox = widgets.VBox()
    input_params_vbox.children = [site_hbox,datapath_hbox,metadata_hbox,progress_hbox]

    input_accordion_box.children = [input_accordion]

    # Create a GridBox with 12 rows and 20 columns
    input_tab = widgets.GridBox(layout=widgets.Layout(grid_template_columns='repeat(10, 1)',
                                                grid_template_rows='repeat(12, 1)'))

    # Add the VBox to the GridBox
    input_tab.children = [site_hbox,
                            datapath_hbox,
                            metadata_hbox,
                            input_accordion_box,
                            progress_hbox]

    def get_input_params():
        input_params_kwargs={
            'datapath':data_filepath.value,
            'metapath':metadata_filepath.value,
            'site':site_name.value,
            'instrument':instrument_dropdown.value,
            'network':network_textbox.value, 'station':station_textbox.value, 'loc':location_textbox.value, 
            'channels':[z_channel_textbox.value, e_channel_textbox.value, n_channel_textbox.value],
            'starttime':start_time_picker.value,
            'endtime':end_time_picker.value,
            'tzone':time_zone_dropdown.value,
            'xcoord':xcoord_textbox.value,
            'ycoord':ycoord_textbox.value,
            'elevation':zcoord_textbox.value, 'elev_unit':elevation_unit_textbox.value,'depth':0,
            'input_crs':input_crs_textbox.value,'output_crs':output_crs_textbox.value,
            'hvsr_band':[hvsr_band_min_box.value, hvsr_band_max_box.value],
            'peak_freq_range':[peak_freq_range_min_box.value, peak_freq_range_max_box.value]}
        return input_params_kwargs

    def get_fetch_data_params():
        fetch_data_kwargs = {
            'source':data_source_type.value, 
            'trim_dir':trim_directory.value,
            'export_format':data_format_dropdown.value,
            'detrend':detrend_type_dropdown.value,
            'detrend_order':detrend_order.value}
        return fetch_data_kwargs

    def read_data(button):
        ip_kwargs = get_input_params()
        hvsr_data = sprit_hvsr.input_params(**ip_kwargs, verbose=verbose_check.value)
        if button.description=='Read Data':
            progress_bar.value=0.333
        else:
            progress_bar.value=0.1
        fd_kwargs = get_fetch_data_params()
        hvsr_data = sprit_hvsr.fetch_data(hvsr_data, **fd_kwargs, verbose=verbose_check.value)
        if button.description=='Read Data':
            progress_bar.value=0.666
        else:
            progress_bar.value=0.2
        
        update_preview_fig(hvsr_data, preview_fig)

        if button.description=='Read Data':
            sprit_widget.selected_index=1
            progress_bar.value=0
        any_update()
        return hvsr_data
    
    read_data_button.on_click(read_data)

    def get_remove_noise_kwargs():
        def get_remove_method():
            remove_method_list=[]
            do_stalta = stalta_check.value
            do_sat_pct = max_saturation_check.value
            do_noiseWin=noisy_windows_check.value
            do_warmcool=warmcool_check.value
            
            if auto_remove_check.value:
                remove_method_list=['stalta', 'saturation', 'noise', 'warmcool']
            else:
                if do_stalta:
                    remove_method_list.append('stalta')
                if do_sat_pct:
                    remove_method_list.append('saturation')
                if do_noiseWin:
                    remove_method_list.append('noise')
                if do_warmcool:
                    remove_method_list.append('warmcool')
            
            if not remove_method_list:
                remove_method_list = None
            return remove_method_list
        
        remove_noise_kwargs = {'remove_method':get_remove_method(),
                                'sat_percent':max_saturation_pct.value, 
                                'noise_percent':max_window_pct.value,
                                'sta':sta.value,
                                'lta':lta.value, 
                                'stalta_thresh':[stalta_thresh_low.value, stalta_thresh_hi.value], 
                                'warmup_time':warmup_time.value,
                                'cooldown_time':cooldown_time.value,
                                'min_win_size':noisy_window_length.value,
                                'remove_raw_noise':raw_data_remove_check.value}
        return remove_noise_kwargs

    def get_generate_ppsd_kwargs():
        ppsd_kwargs = {
            'skip_on_gaps':skip_on_gaps.value,
            'db_bins':[db_bins_min.value, db_bins_max.value, db_bins_step.value],
            'ppsd_length':ppsd_length.value,
            'overlap':overlap_pct.value,
            'special_handling':special_handling_dropdown.value,
            'period_smoothing_width_octaves':period_smoothing_width.value,
            'period_step_octaves':period_step_octave.value,
            'period_limits':[period_limits_min.value, period_limits_max.value],
            }
        return ppsd_kwargs

    def get_remove_outlier_curve_kwargs():
        roc_kwargs = {
                'use_percentile':rmse_pctile_check.value,
                'rmse_thresh':rmse_thresh.value,
                'use_hv_curve':False#use_hv_curve_rmse.value
            }
        return roc_kwargs

    def get_process_hvsr_kwargs():
        if smooth_hv_curve_bool.value:
            smooth_value = smooth_hv_curve.value
        else:
            smooth_value = smooth_hv_curve_bool.value

        if resample_hv_curve_bool.value:
            resample_value = resample_hv_curve.value
        else:
            resample_value =resample_hv_curve_bool.value

        ph_kwargs={'method':h_combine_meth.value,
                   'smooth':smooth_value,
                   'freq_smooth':freq_smoothing.value,
                   'f_smooth_width':freq_smooth_width.value,
                   'resample':resample_value,
                   'outlier_curve_rmse_percentile':use_hv_curve_rmse.value}
        return ph_kwargs

    def get_check_peaks_kwargs():
        cp_kwargs = {'hvsr_band':[hvsr_band_min_box.value, hvsr_band_max_box.value],
                    'peak_freq_range':[peak_freq_range_min_box.value, peak_freq_range_max_box.value],
                    'peak_selection':peak_selection_type.value}
        return cp_kwargs

    def get_get_report_kwargs():
        def get_formatted_plot_str():
            # Initialize plot string
            hvsr_plot_str = ''
            comp_plot_str = ''
            spec_plot_str = ''

            # Whether to use each plot
            if use_plot_hv.value:
                hvsr_plot_str=hvsr_plot_str + "HVSR"
            if use_plot_comp.value:
                comp_plot_str=comp_plot_str + "C"
            if use_plot_spec.value:
                spec_plot_str=spec_plot_str + "SPEC"

            # Whether components be on the same plot as HV curve?
            if not combine_hv_comp.value:
                comp_plot_str=comp_plot_str + "+"

            # Whether to show (log) standard deviations
            if not show_std_hv.value:
                hvsr_plot_str=hvsr_plot_str + " -s"
            if not show_std_comp.value:
                comp_plot_str=comp_plot_str + " -s"                

            # Whether curves from each time window are shown
            if show_all_curves_hv.value:
                hvsr_plot_str=hvsr_plot_str + " t"
            if show_all_curves_comp.value:
                comp_plot_str=comp_plot_str + " t"

            # Whether the best peak is displayed
            if show_best_peak_hv.value:
                hvsr_plot_str=hvsr_plot_str + " p"
            if show_best_peak_comp.value:
                comp_plot_str=comp_plot_str + " p"
            if show_best_peak_spec.value:
                spec_plot_str=spec_plot_str + " p"

            # Whether best peak value is annotated
            if ann_best_peak_hv.value:
                hvsr_plot_str=hvsr_plot_str + " ann"
            if ann_best_peak_comp.value:
                comp_plot_str=comp_plot_str + " ann"
            if ann_best_peak_spec.value:
                spec_plot_str=spec_plot_str + " ann"

            # Whether peaks from individual time windows are shown
            if show_ind_peaks_hv.value:
                hvsr_plot_str=hvsr_plot_str + " tp"            

            # Whether to show legend
            if show_legend_hv.value:
                hvsr_plot_str=hvsr_plot_str + " leg"
            if ann_best_peak_comp.value:
                show_legend_comp=comp_plot_str + " leg"
            if show_legend_spec.value:
                spec_plot_str=spec_plot_str + " leg"            

            # Combine string into one
            plot_str = hvsr_plot_str + ' ' + comp_plot_str+ ' ' + spec_plot_str
            return plot_str

        gr_kwargs = {'report_format':['print','csv'],
                     'plot_type':get_formatted_plot_str(),
                     'export_path':None,
                     'return_results':False, 
                     'csv_overwrite_opt':'overwrite',
                     'no_output':False
                     }
        return gr_kwargs

    def process_data(button):
        hvsr_data = read_data(button)

        remove_noise_kwargs = get_remove_noise_kwargs()
        hvsr_data = sprit_hvsr.remove_noise(hvsr_data, **remove_noise_kwargs, verbose=verbose_check.value)
        progress_bar.value = 0.3

        generate_ppsd_kwargs = get_generate_ppsd_kwargs()
        hvsr_data = sprit_hvsr.generate_ppsds(hvsr_data, **generate_ppsd_kwargs, verbose=verbose_check.value)
        progress_bar.value = 0.5

        roc_kwargs = get_remove_outlier_curve_kwargs()
        hvsr_data = sprit_hvsr.remove_outlier_curves(hvsr_data, **roc_kwargs, verbose=verbose_check.value)
        progress_bar.value = 0.6

        ph_kwargs = get_process_hvsr_kwargs()
        hvsr_data = sprit_hvsr.process_hvsr(hvsr_data, **ph_kwargs, verbose=verbose_check.value)
        progress_bar.value = 0.85

        cp_kwargs = get_check_peaks_kwargs()
        hvsr_data = sprit_hvsr.check_peaks(hvsr_data, **cp_kwargs, verbose=verbose_check.value)
        progress_bar.value = 0.9

        gr_kwargs = get_get_report_kwargs()
        hvsr_data = sprit_hvsr.get_report(hvsr_data, **gr_kwargs, verbose=verbose_check.value)
        progress_bar.value = 0.95

        update_results_fig(hvsr_data, results_fig, gr_kwargs['plot_type'])
        progress_bar.value = 1
        progress_bar.value = 0
        
    def parse_plot_string(plot_string):
        plot_list = plot_string.split()

        hvsrList = ['hvsr', 'hv', 'h']
        compList = ['component', 'comp', 'c']
        compPlus = [item + '+' for item in compList]
        specList = ['spectrogram', 'specgram', 'spec','sg', 's']

        hvInd = np.nan
        compInd = np.nan
        specInd = np.nan

        hvIndFound = False
        compIndFound = False
        specIndFound = False

        for i, item in enumerate(plot_list):
            if item.lower() in hvsrList and not hvIndFound:
                # assign the index
                hvInd = i
                hvIndFound = True
            if (item.lower() in compList or item.lower() in compPlus) and not compIndFound:
                # assign the index
                compInd = i
                compIndFound = True
            if item.lower() in specList and not specIndFound:
                # assign the index
                specInd = i
                specIndFound = True

        # Get individual plot lists (should already be correctly ordered)
        if hvInd is np.nan:
            hvsr_plot_list = ['HVSR']

        if compInd is np.nan:
            comp_plot_list = []
            if specInd is np.nan:
                if hvInd is not np.nan:
                    hvsr_plot_list = plot_list
                spec_plot_list = []
            else:
                if hvInd is not np.nan:
                    hvsr_plot_list = plot_list[hvInd:specInd]
                spec_plot_list = plot_list[specInd:]
        else:
            if hvInd is not np.nan:
                hvsr_plot_list = plot_list[hvInd:compInd]
            
            if specInd is np.nan:
                comp_plot_list = plot_list[compInd:]
                spec_plot_list = []
            else:
                comp_plot_list = plot_list[compInd:specInd]
                spec_plot_list = plot_list[specInd:]

        # Figure out how many subplots there will be
        plot_list_list = [hvsr_plot_list, comp_plot_list, spec_plot_list]

        return plot_list_list

    def parse_hv_plot_list(hvsr_data, hvsr_plot_list, results_fig):
        x_data = hvsr_data.x_freqs['Z']
        hvsrDF = hvsr_data.hvsr_df

        if 'tp' in hvsr_plot_list:
            allpeaks = []
            for row in hvsrDF[hvsrDF['Use']]['CurvesPeakFreqs'].values:
                for peak in row:
                    allpeaks.append(peak)
            x_vals = []
            y_vals = []
            y_max = np.nanmax(hvsr_data.hvsrp)
            for tp in allpeaks:
                x_vals.extend([tp, tp, None]) # add two x values and a None
                y_vals.extend([0, y_max, None]) # add the first and last y values and a None            

            results_fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines',
                                            line=dict(width=4, dash="solid", 
                                            color="rgba(128,0,0,0.1)"), 
                                            name='Best Peaks Over Time'),
                                            row=1, col=1)

        if 't' in hvsr_plot_list:
            alltimecurves = np.stack(hvsrDF[hvsrDF['Use']]['HV_Curves'])
            for i, row in enumerate(alltimecurves):
                if i==0:
                    showLeg = True
                else:
                    showLeg= False
                results_fig.add_trace(go.Scatter(x=x_data[:-1], y=row, mode='lines',
                                            line=dict(width=0.5, dash="solid", 
                                            color="rgba(100, 110, 100, 0.8)"), 
                                            showlegend=showLeg, 
                                            name='Ind. time win. curve', 
                                            hoverinfo='none'),
                                            row=1, col=1)

        if 'all' in hvsr_plot_list:
            for i, p in enumerate(hvsr_data['hvsr_peak_freqs']):
                if i==0:
                    showLeg = True
                else:
                    showLeg= False

                results_fig.add_trace(go.Scatter(
                    x=[p, p, None], # set x to None
                    y=[0, np.nanmax(np.stack(hvsrDF['HV_Curves'])),None], # set y to None
                    mode="lines", # set mode to lines
                    line=dict(width=1, dash="dot", color="gray"), # set line properties
                    name="All checked peaks", # set legend name
                    showlegend=showLeg),
                    row=1, col=1)

        if '-s' not in hvsr_plot_list:
            # Show standard deviation
            results_fig.add_trace(go.Scatter(x=x_data, y=hvsr_data.hvsrp2,
                                    line={'color':'black', 'width':0.1},marker=None, 
                                    showlegend=False, name='Log. St.Dev. Upper',
                                    hoverinfo='none'),
                                    row=1, col=1)
            
            results_fig.add_trace(go.Scatter(x=x_data, y=hvsr_data.hvsrm2,
                                    line={'color':'black', 'width':0.1},marker=None,
                                    fill='tonexty', fillcolor="rgba(128, 128, 128, 0.6)",
                                    name='Log. St.Dev.', hoverinfo='none'),
                                    row=1, col=1)
                
        if 'p' in hvsr_plot_list:
            results_fig.add_trace(go.Scatter(
                x=[hvsr_data['BestPeak']['f0'], hvsr_data['BestPeak']['f0'], None], # set x to None
                y=[0,np.nanmax(np.stack(hvsrDF['HV_Curves'])),None], # set y to None
                mode="lines", # set mode to lines
                line=dict(width=1, dash="dash", color="black"), # set line properties
                name="Best Peak"),
                row=1, col=1)

        if 'ann' in hvsr_plot_list:
            # Annotate best peak
            results_fig.add_annotation(x=hvsr_data['BestPeak']['f0'],
                                    y=0, 
                                    text=f"{hvsr_data['BestPeak']['f0']:.3f} Hz",
                                    bgcolor='rgba(255, 255, 255, 0.7)',
                                    showarrow=False,
                                    row=1, col=1)
        return results_fig

    def parse_comp_plot_list(hvsr_data, comp_plot_list, results_fig):

        # Initial setup
        x_data = hvsr_data.x_freqs['Z']
        hvsrDF = hvsr_data.hvsr_df
        same_plot = (comp_plot_list != [] and '+' not in comp_plot_list[0])
        if same_plot:
            yaxis_to_use = 'y2'
            use_secondary = True
            transparency_modifier = 0.5
        else:
            yaxis_to_use = 'y'
            use_secondary=False
            transparency_modifier = 1

        alpha = 0.4 * transparency_modifier
        components = ['Z', 'E', 'N']
        compColor_semi_light = {'Z':f'rgba(128,128,128,{alpha})',
                    'E':f'rgba(0,0,128,{alpha})',
                    'N':f'rgba(128,0,0,{alpha})'}

        alpha = 0.7 * transparency_modifier
        compColor_semi = {'Z':f'rgba(128,128,128,{alpha})', 
                        'E':f'rgba(100,100,128,{alpha})', 
                        'N':f'rgba(128,100,100,{alpha})'}

        compColor = {'Z':f'rgba(128,128,128,{alpha})', 
                    'E':f'rgba(100,100,250,{alpha})', 
                    'N':f'rgba(250,100,100,{alpha})'}

        # Whether to plot in new subplot or not
        if '+' in comp_plot_list[0]:
            compRow=2
        else:
            compRow=1

        # Whether to plot individual time curves
        if 't' in comp_plot_list:
            for comp in components:
                alltimecurves = np.stack(hvsrDF[hvsrDF['Use']]['psd_values_'+comp])
                for i, row in enumerate(alltimecurves):
                    if i==0:
                        showLeg = True
                    else:
                        showLeg= False
                    
                    results_fig.add_trace(go.Scatter(x=x_data[:-1], y=row, mode='lines',
                                    line=dict(width=0.5, dash="solid", 
                                    color=compColor_semi[comp]),
                                    name='Ind. time win. curve',
                                    showlegend=False,
                                    hoverinfo='none',
                                    yaxis=yaxis_to_use),
                                    secondary_y=use_secondary,
                                    row=compRow, col=1)

        # Code to plot standard deviation windows, if not removed
        if '-s' not in comp_plot_list:
            for comp in components:
                # Show standard deviation
                results_fig.add_trace(go.Scatter(x=x_data, y=hvsr_data.ppsd_std_vals_p[comp],
                                        line={'color':compColor_semi_light[comp], 'width':0.1},marker=None, 
                                        showlegend=False, name='Log. St.Dev. Upper',
                                        hoverinfo='none',    
                                        yaxis=yaxis_to_use),
                                        secondary_y=use_secondary,
                                        row=compRow, col=1)
                
                results_fig.add_trace(go.Scatter(x=x_data, y=hvsr_data.ppsd_std_vals_m[comp],
                                        line={'color':compColor_semi_light[comp], 'width':0.1},marker=None,
                                        fill='tonexty', fillcolor=compColor_semi_light[comp],
                                        name=f'St.Dev. [{comp}]', hoverinfo='none', showlegend=False, 
                                        yaxis=yaxis_to_use),
                                        secondary_y=use_secondary,
                                        row=compRow, col=1)
                
        # Code to plot location of best peak
        if 'p' in comp_plot_list:
            minVal = 10000
            maxVal = -10000
            for comp in components:
                currPPSDCurve = hvsr_data['psd_values_tavg'][comp]
                if np.nanmin(currPPSDCurve) < minVal:
                    minVal = np.nanmin(currPPSDCurve)
                if np.nanmax(currPPSDCurve) > maxVal:
                    maxVal = np.nanmax(currPPSDCurve)

            results_fig.add_trace(go.Scatter(
                x=[hvsr_data['BestPeak']['f0'], hvsr_data['BestPeak']['f0'], None], # set x to None
                y=[minVal,maxVal,None], # set y to None
                mode="lines", # set mode to lines
                line=dict(width=1, dash="dash", color="black"), # set line properties
                name="Best Peak",
                yaxis=yaxis_to_use),
                secondary_y=use_secondary,
                row=compRow, col=1)
            
        # Code to annotate value of best peak
        if 'ann' in comp_plot_list:
            minVal = 10000
            for comp in components:
                currPPSDCurve = hvsr_data['psd_values_tavg'][comp]
                if np.nanmin(currPPSDCurve) < minVal:
                    minVal = np.nanmin(currPPSDCurve)

            results_fig.add_annotation(x=np.log10(hvsr_data['BestPeak']['f0'],), 
                            y=minVal, 
                            text=f"{hvsr_data['BestPeak']['f0']:.3f} Hz",
                            bgcolor='rgba(255, 255, 255, 0.7)',
                            showarrow=False,
                            yref=yaxis_to_use,
                            secondary_y=use_secondary,
                            row=compRow, col=1)

        # Plot the main averaged component PPSDs
        for comp in components:
            results_fig.add_trace(go.Scatter(x=hvsr_data.x_freqs[comp],
                                            y=hvsr_data['psd_values_tavg'][comp],
                                            line=dict(width=2, dash="solid", 
                                            color=compColor[comp]),marker=None, 
                                            name='PPSD Curve '+comp,    
                                            yaxis=yaxis_to_use), 
                                            secondary_y=use_secondary,
                                        row=compRow, col='all')

        # If new subplot, update accordingly
        if compRow==2:
            results_fig.update_xaxes(type='log', 
                            range=[np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1])], 
                            row=compRow, col=1)

        return results_fig

    def parse_spec_plot_list(hvsr_data, spec_plot_list, subplot_num, results_fig):

        # Initial setup
        hvsrDF = hvsr_data.hvsr_df
        specAxisTimes = np.array([dt.isoformat() for dt in hvsrDF.index.to_pydatetime()])
        y_data = hvsr_data.x_freqs['Z'][1:]
        image_data = np.stack(hvsrDF['HV_Curves']).T

        
        maxZ = np.percentile(image_data, 100)
        minZ = np.percentile(image_data, 0)

        use_mask = hvsr_data.hvsr_df.Use.values
        use_mask = np.tile(use_mask, (image_data.shape[0],1))#.astype(int)
        use_mask = np.where(use_mask is False, np.nan, use_mask)
        data_used = go.Heatmap(
            x=specAxisTimes,
            y=y_data,
            z=use_mask,
            showlegend=False,
            colorscale=[[0, 'rgba(0,0,0,1)'], [1, 'rgba(250,250,250,0)']],
            showscale=False, name='Used')
        results_fig.add_trace(data_used, row=subplot_num, col=1)

        hmap = go.Heatmap(z=image_data,
                    x=specAxisTimes,
                    y=y_data,
                    colorscale='Turbo',
                    showlegend=False,
                    opacity=0.7,
                    hovertemplate='Time [UTC]: %{x}<br>Frequency [Hz]: %{y:.2f}<br>H/V Amplitude: %{z:.2f}<extra></extra>',
                    zmin=minZ,zmax=maxZ, showscale=False, name='HV Curve Amp. over Time')
        results_fig.add_trace(hmap, row=subplot_num, col=1)

        results_fig.update_yaxes(type='log', 
                        range=[np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1])],
                        row=subplot_num, col=1)

        results_fig.add_annotation(
            text=f"{hvsrDF['Use'].sum()}/{hvsrDF.shape[0]} windows used",
            x=max(specAxisTimes), 
            y=np.log10(min(y_data))+(np.log10(max(y_data))-np.log10(min(y_data)))*0.01,
            xanchor="right", yanchor="bottom",bgcolor='rgba(256,256,256,0.7)',
            showarrow=False,row=subplot_num, col=1)

        #results_fig.update_layout(legend=dict(traceorder='original'),
        #                          row=subplot_num, col=1) 

        return results_fig

    def update_results_fig(hvsr_data, results_fig, plot_string):
        results_fig.data = []

        if isinstance(hvsr_data, sprit_hvsr.HVSRBatch):
            hvsr_data=hvsr_data[0]

        hvsrDF = hvsr_data.hvsr_df

        plot_list = parse_plot_string(plot_string)

        noSubplots = 3 - plot_list.count([])
        if plot_list[1] != [] and '+' not in plot_list[1][0]:
            noSubplots -= 1


        # Re-initialize results_fig
        results_fig.update_layout(grid={'rows': noSubplots, 'xgap': 0.01, 'ygap': 0.01})

        # Get all data for each plotted item
        # HVSR Plot
        results_fig = parse_hv_plot_list(hvsr_data, hvsr_plot_list=plot_list[0], results_fig=results_fig)
        # Will always plot the HV Curve
        results_fig.add_trace(go.Scatter(x=hvsr_data.x_freqs['Z'],y=hvsr_data.hvsr_curve,
                            line={'color':'black', 'width':1.5},marker=None, name='HVSR Curve'), row=1, col='all')

        # COMP Plot
        # Figure out which subplot is which
        if plot_list[1] == [] or '+' not in plot_list[1][0]:
            spec_plot_row = 2
        else:
            spec_plot_row = 3

        results_fig = parse_comp_plot_list(hvsr_data, comp_plot_list=plot_list[1], results_fig=results_fig)

        # SPEC plot
        results_fig = parse_spec_plot_list(hvsr_data, spec_plot_list=plot_list[2], subplot_num=spec_plot_row, results_fig=results_fig)

        # Final figure updating
        showtickLabels = (plot_list[1]==[] or '+' not in plot_list[1][0])
        if showtickLabels:
            side='bottom'
        else:
            side='top'
        results_fig.update_xaxes(type='log',
                        range=[np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1])],
                        #showticklabels=showtickLabels,
                        side=side,
                        row=1, col=1)
    
        results_fig.update_layout(margin={"l":10, "r":10, "t":30, 'b':0}, 
                                showlegend=False,
                                title=hvsr_data['site'])
        results_fig.show()
        sprit_widget.selected_index=3

    process_hvsr_button.on_click(process_data)

    # PREVIEW TAB
    preview_graph_tab = widgets.GridspecLayout(ui_height-1, ui_width)
    preview_noise_tab = widgets.GridspecLayout(ui_height-1, ui_width)
    preview_tab = widgets.Tab([preview_graph_tab, preview_noise_tab])
    preview_tab.set_title(0, "Data Preview")
    preview_tab.set_title(1, "Noise Removal")

    #Initialize plot
    subp = subplots.make_subplots(rows=4, cols=1, shared_xaxes=True, horizontal_spacing=0.01, vertical_spacing=0.01, row_heights=[3,1,1,1])
    preview_fig = go.FigureWidget(subp)
    preview_graph_widget = widgets.Output()  

    # Initialize tab
    preview_graph_tab[:,:]=preview_graph_widget
    with preview_graph_widget:
        display(preview_fig)

    def update_preview_fig(hvsr_data, preview_fig):
        preview_fig.data = []

        if isinstance(hvsr_data, sprit_hvsr.HVSRBatch):
            hvsr_data=hvsr_data[0]

        stream_z = hvsr_data['stream'].select(component='Z') #may be np.ma.masked_array
        stream_e = hvsr_data['stream'].select(component='E') #may be np.ma.masked_array
        stream_n = hvsr_data['stream'].select(component='N') #may be np.ma.masked_array

        # Get iso_times and datetime.datetime
        utcdt = stream_z[0].times(type='utcdatetime')
        iso_times=[]
        dt_times = []
        for t in utcdt:
            if t is not np.ma.masked:
                iso_times.append(t.isoformat())
                dt_times.append(datetime.datetime.fromisoformat(t.isoformat()))
            else:
                iso_times.append(np.nan)
        iso_times=np.array(iso_times)
        dt_times = np.array (dt_times)

        # Generate spectrogram
        f, t, Sxx = signal.spectrogram(x=stream_z[0].data, fs=stream_z[0].stats.sampling_rate, mode='magnitude')
        
        # Get times for the axis (one time per window)
        axisTimes = []
        for tpass in t:
            axisTimes.append((dt_times[0]+datetime.timedelta(seconds=tpass)).isoformat())

        # Add data to preview_fig
        # Add spectrogram of Z component
        minz = np.percentile(Sxx, 1)
        maxz = np.percentile(Sxx, 99)
        hmap = go.Heatmap(z=Sxx,
                    x=axisTimes,
                    y=f,
                    colorscale='Turbo',
                    showlegend=False,
                    hovertemplate='Time [UTC]: %{x}<br>Frequency [Hz]: %{y:.2f}<br>Spectrogram Magnitude: %{z:.2f}<extra></extra>',
                    zmin=minz, zmax=maxz, showscale=False, name='Z Component Spectrogram')
        preview_fig.add_trace(hmap, row=1, col=1)
        preview_fig.update_yaxes(type='log', range=[np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1])], row=1, col=1)
        preview_fig.update_yaxes(title={'text':'Spectrogram (Z)'}, row=1, col=1)

        # Add raw traces
        dec_factor=5 #This just makes the plotting go faster, by "decimating" the data
        preview_fig.add_trace(go.Scatter(x=iso_times[::dec_factor], y=stream_z[0].data[::dec_factor],
                                        line={'color':'black', 'width':0.5},marker=None, name='Z component data'), row=2, col='all')
        preview_fig.update_yaxes(title={'text':'Z'}, row=2, col=1)
        preview_fig.add_trace(go.Scatter(x=iso_times[::dec_factor], y=stream_e[0].data[::dec_factor],
                                        line={'color':'blue', 'width':0.5},marker=None, name='E component data'),row=3, col='all')
        preview_fig.update_yaxes(title={'text':'E'}, row=3, col=1)
        preview_fig.add_trace(go.Scatter(x=iso_times[::dec_factor], y=stream_n[0].data[::dec_factor],
                                        line={'color':'red', 'width':0.5},marker=None, name='N component data'), row=4, col='all')
        preview_fig.update_yaxes(title={'text':'N'}, row=4, col=1)

        #preview_fig.add_trace(p)
        preview_fig.update_layout(margin={"l":10, "r":10, "t":30, 'b':0}, showlegend=False,
                                  title=hvsr_data['site'])

    #STA/LTA Antitrigger
    stalta_check = widgets.Checkbox(value=False, disabled=False, indent=False, description='STA/LTA Antitrigger')
    sta = widgets.FloatText(description='STA [s]',  style={'description_width': 'initial'}, placeholder=5, value=5,layout=widgets.Layout(height='auto', width='auto'))
    lta = widgets.FloatText(description='LTA [s]',  style={'description_width': 'initial'}, placeholder=30, value=30,layout=widgets.Layout(height='auto', width='auto'))
    stalta_thresh_low = widgets.FloatText(description='STA/LTA Thresholds (low, high)',  style={'description_width': 'initial'}, placeholder=0.5, value=0.5,layout=widgets.Layout(height='auto', width='auto'))
    stalta_thresh_hi = widgets.FloatText(style={'description_width': 'initial'}, placeholder=5, value=5,layout=widgets.Layout(height='auto', width='auto'))

    #% Saturation Threshold
    max_saturation_check = widgets.Checkbox(description='Percentage Threshold (Instantaneous)', value=False, disabled=False, indent=False)
    max_saturation_pct = widgets.FloatText(description='Max Saturation %:',  style={'description_width': 'initial'}, placeholder=0.995, value=0.995,layout=widgets.Layout(height='auto', width='auto'))

    #Noise Windows
    noisy_windows_check = widgets.Checkbox(description='Noisy Windows', value=False, disabled=False, indent=False)
    max_window_pct = widgets.FloatText(description='Max Window %:',  style={'description_width': 'initial'}, placeholder=0.8, value=0.8,layout=widgets.Layout(height='auto', width='auto'))
    noisy_window_length = widgets.FloatText(description='Window Length [s]:',  style={'description_width': 'initial'}, placeholder=30, value=30,layout=widgets.Layout(height='auto', width='auto'))

    #Warmup/cooldown
    warmcool_check = widgets.Checkbox(description='Warmup & Cooldown Time', value=False, disabled=False, indent=False)
    warmup_time = widgets.FloatText(description='Warmup time [s]:',  style={'description_width': 'initial'}, placeholder=0, value=0,layout=widgets.Layout(height='auto', width='auto'))
    cooldown_time = widgets.FloatText(description='Cooldown time [s]:',  style={'description_width': 'initial'}, placeholder=0, value=0,layout=widgets.Layout(height='auto', width='auto'))

    #STD Ratio
    std_ratio_check = widgets.Checkbox(description='Standard Deviation Antitrigger (not yet implemented)', value=False, disabled=True, indent=False)
    std_ratio_text = widgets.FloatText(description='StdDev Ratio:',  style={'description_width': 'initial'}, placeholder=0, value=0,layout=widgets.Layout(height='auto', width='auto'), disabled=True)
    std_window_length_text = widgets.FloatText(description='Moving window Length [s]:',  style={'description_width': 'initial'}, placeholder=0, value=0,layout=widgets.Layout(height='auto', width='auto'),disabled=True)

    #Autoremove
    auto_remove_check = widgets.Checkbox(description='Use Auto Remove', value=False, disabled=False, indent=False)

    #Remove from raw data
    raw_data_remove_check = widgets.Checkbox(description='Remove Noise From Raw Data', value=False, disabled=False, indent=False)

    #remove_noise call
    remove_noise_call = widgets.Label(value=f"remove_noise()")

    #progress bar (same as above)
    # A progress bar
    progress_bar_preview = widgets.FloatProgress(value=0.0,min=0.0,max=1.0,
                                    bar_style='info',
                                    orientation='horizontal',layout=widgets.Layout(height='auto', width='auto'))
    #Update noise windows
    update_noise_windows_button = widgets.Button(description='Update Noise Windows',button_style='info',layout=widgets.Layout(height='auto', width='auto'))

    # A forest green button labeled "Process HVSR"
    process_hvsr_button_preview = widgets.Button(description='Run',
                                         button_style='success',layout=widgets.Layout(height='auto', width='auto'))

    # Add it all in to the tab
    preview_noise_tab[0,1:5] = stalta_check
    preview_noise_tab[0,5:7] = sta
    preview_noise_tab[0,7:9] = lta
    preview_noise_tab[0,9:13] = stalta_thresh_low
    preview_noise_tab[0,13:15] = stalta_thresh_hi

    preview_noise_tab[1,1:5] = max_saturation_check
    preview_noise_tab[1,6:8] = max_saturation_pct

    preview_noise_tab[2,1:5] = noisy_windows_check
    preview_noise_tab[2,6:9] = max_window_pct
    preview_noise_tab[2,10:13] = noisy_window_length

    preview_noise_tab[3,1:5] = warmcool_check
    preview_noise_tab[3,6:9] = warmup_time
    preview_noise_tab[3,10:13] = cooldown_time

    preview_noise_tab[4,1:5] = std_ratio_check
    preview_noise_tab[4,6:9] = std_ratio_text
    preview_noise_tab[4,10:13] = std_window_length_text

    preview_noise_tab[6,:] = auto_remove_check
    preview_noise_tab[7,:] = raw_data_remove_check

    preview_noise_tab[9,:] = remove_noise_call

    preview_noise_tab[10,:15] = progress_bar_preview
    preview_noise_tab[10,15:19] = update_noise_windows_button
    preview_noise_tab[10,19] = process_hvsr_button_preview

    # SETTINGS TAB
    ppsd_settings_tab = widgets.GridspecLayout(ui_height-1, ui_width)
    outlier_settings_tab = widgets.GridspecLayout(ui_height-1, ui_width)
    hvsr_settings_tab = widgets.GridspecLayout(ui_height-1, ui_width)
    plot_settings_tab = widgets.GridspecLayout(18, ui_width)
    settings_tab = widgets.Tab([ppsd_settings_tab, outlier_settings_tab, hvsr_settings_tab, plot_settings_tab])
    settings_tab.set_title(0, "PPSD Settings")
    settings_tab.set_title(1, "Outlier Settings")
    settings_tab.set_title(2, "HVSR Settings")
    settings_tab.set_title(3, "Plot Settings")

    # PPSD SETTINGS SUBTAB
    ppsd_length_label = widgets.Label(value='Window Length for PPSDs:')
    ppsd_length = widgets.FloatText(style={'description_width': 'initial'}, 
                                    placeholder=20, value=20,layout=widgets.Layout(height='auto', width='auto'), disabled=False)
    
    overlap_pct_label = widgets.Label(value='Overlap %:')
    overlap_pct = widgets.FloatText(style={'description_width': 'initial'}, 
                                    placeholder=0.5, value=0.5, layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    period_step_label = widgets.Label(value='Period Step Octaves:')
    period_step_octave = widgets.FloatText(style={'description_width': 'initial'}, 
                                           placeholder=0.0625, value=0.0625, layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    skip_on_gaps_label = widgets.Label(value='Skip on gaps:')
    skip_on_gaps = widgets.Checkbox(value=False, disabled=False, indent=False)

    db_step_label = widgets.Label(value='dB bins:')
    db_bins_min = widgets.FloatText(description='Min. dB', style={'description_width': 'initial'},
                                    placeholder=-200, value=-200, layout=widgets.Layout(height='auto', width='auto'), disabled=False)
    db_bins_max = widgets.FloatText(description='Max. dB', style={'description_width': 'initial'},
                                    placeholder=-50, value=-50, layout=widgets.Layout(height='auto', width='auto'), disabled=False)
    db_bins_step = widgets.FloatText(description='dB Step', style={'description_width': 'initial'},
                                    placeholder=1, value=1, layout=widgets.Layout(height='auto', width='auto'), disabled=False)
    
    period_limit_label = widgets.Label(value='Period Limits:')
    minPLim = round(1/(hvsr_band_max_box.value),2)
    maxPLim = round(1/(hvsr_band_min_box.value),2)
    period_limits_min = widgets.FloatText(description='Min. Period Limit', style={'description_width': 'initial'},
                                    placeholder=minPLim, value=minPLim, layout=widgets.Layout(height='auto', width='auto'), disabled=False)
    period_limits_max = widgets.FloatText(description='Max. Period Limit', style={'description_width': 'initial'},
                                    placeholder=maxPLim, value=maxPLim, layout=widgets.Layout(height='auto', width='auto'), disabled=False)
    period_smoothing_width = widgets.FloatText(description='Period Smoothing Width', style={'description_width': 'initial'},
                                    placeholder=1, value=1, layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    special_handling_dropdown = widgets.Dropdown(description='Special Handling', value=None,
                                                options=[('None', None), ('Ringlaser', 'ringlaser'), ('Hydrophone', 'hydrophone')],
                                            style={'description_width': 'initial'},  layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    generate_ppsd_call = widgets.Label(value='generate_ppsds()')

    obspy_ppsd_call = widgets.Label(value='obpsy...PPSD()')

    # Set up grid for ppsd_settings subtab
    ppsd_settings_tab[0, 0:5] = ppsd_length_label
    ppsd_settings_tab[0, 5:8] = ppsd_length

    ppsd_settings_tab[1, 0:5] = overlap_pct_label
    ppsd_settings_tab[1, 5:8] = overlap_pct

    ppsd_settings_tab[2, 0:5] = period_step_label
    ppsd_settings_tab[2, 5:8] = period_step_octave

    ppsd_settings_tab[3, 0:5] = skip_on_gaps_label
    ppsd_settings_tab[3, 5:8] = skip_on_gaps

    ppsd_settings_tab[4, 0:5] = db_step_label
    ppsd_settings_tab[4, 5:7] = db_bins_min
    ppsd_settings_tab[4, 7:10] = db_bins_max
    ppsd_settings_tab[4, 10:12] = db_bins_step

    ppsd_settings_tab[5, 0:5] = period_limit_label
    ppsd_settings_tab[5, 5:8] = period_limits_min
    ppsd_settings_tab[5, 8:11] = period_limits_max
    ppsd_settings_tab[5, 11:] = period_smoothing_width

    ppsd_settings_tab[6, 0:8] = special_handling_dropdown

    ppsd_settings_tab[7:9, :] = generate_ppsd_call
    ppsd_settings_tab[9:11, :] = obspy_ppsd_call

    # OUTLIER SETTINGS SUBTAB
    rmse_pctile_check = widgets.Checkbox(description='Value is percentile', layout=widgets.Layout(height='auto', width='auto'), style={'description_width': 'initial'}, value=True)
    rmse_thresh = widgets.FloatText(description='RMSE Threshold', style={'description_width': 'initial'},
                                    placeholder=98, value=98, layout=widgets.Layout(height='auto', width='auto'), disabled=False)
    use_hv_curve_rmse = widgets.Checkbox(description='Use HV Curve Outliers', layout=widgets.Layout(height='auto', width='auto'), style={'description_width': 'initial'}, value=True)

    outlier_settings_tab[0, :5] = rmse_pctile_check
    outlier_settings_tab[0, 5:10] = rmse_thresh
    outlier_settings_tab[1, :5] = use_hv_curve_rmse

    # HVSR SETTINGS SUBTAB
    h_combine_meth = widgets.Dropdown(description='Horizontal Combination Method', value=3,
                                    options=[('1. Differential Field Assumption (not implemented)', 1), 
                                             ('2. Arithmetic Mean |  H = (N + E)/2', 2), 
                                             ('3. Geometric Mean | H = √(N * E) (SESAME recommended)', 3),
                                             ('4. Vector Summation | H = √(N^2 + E^2)', 4),
                                             ('5. Quadratic Mean | H = √(N^2 + E^2)/2', 5),
                                             ('6. Maximum Horizontal Value | H = max(N, E)', 6)],
                                    style={'description_width': 'initial'},  layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    freq_smoothing = widgets.Dropdown(description='Frequency Smoothing Operations', value='ko',
                                    options=[('Konno-Ohmachi', 'ko'),
                                             ('Constant','constant'),
                                             ('Proportional', 'proportional'),
                                             ('None', None)],
                                    style={'description_width': 'initial'},  layout=widgets.Layout(height='auto', width='auto'), disabled=False)
    freq_smooth_width = widgets.FloatText(description='Freq. Smoothing Width', style={'description_width': 'initial'},
                                    placeholder=40, value=40, layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    resample_hv_curve_bool = widgets.Checkbox(layout=widgets.Layout(height='auto', width='auto'), style={'description_width': 'initial'}, value=True)
    resample_hv_curve = widgets.FloatText(description='Resample H/V Curve', style={'description_width': 'initial'},
                                    placeholder=500, value=500, layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    smooth_hv_curve_bool = widgets.Checkbox(layout=widgets.Layout(height='auto', width='auto'), style={'description_width': 'initial'}, value=True)
    smooth_hv_curve = widgets.FloatText(description='Smooth H/V Curve', style={'description_width': 'initial'},
                                    placeholder=51, value=51, layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    #hvsr_band_min_box_hvsrSet = widgets.FloatText(description='HVSR Band:', style={'description_width': 'initial'}, 
    #                                              placeholder=hvsr_band_min_box.value, value=hvsr_band_min_box.value,
    #                                              layout=widgets.Layout(height='auto', width='auto'))
    #hvsr_band_max_box_hvsrSet = widgets.FloatText(placeholder=hvsr_band_max_box.value, value=hvsr_band_max_box.value,
    #                                              layout=widgets.Layout(height='auto', width='auto'))
    hvsr_band_hbox_hvsrSet = widgets.HBox([hvsr_band_min_box, hvsr_band_max_box],layout=widgets.Layout(height='auto', width='auto'))

    #peak_freq_range_min_box_hvsrSet = widgets.FloatText(description='Peak Freq. Range:',  style={'description_width': 'initial'},
    #                                                    placeholder=peak_freq_range_min_box.value, value=peak_freq_range_min_box.value,
    #                                                    layout=widgets.Layout(height='auto', width='auto'))
    #peak_freq_range_max_box_hvsrSet = widgets.FloatText(placeholder=peak_freq_range_max_box.value, value=peak_freq_range_max_box.value,
    #                                                    layout=widgets.Layout(height='auto', width='auto'))
    peak_freq_range_hbox_hvsrSet = widgets.HBox([peak_freq_range_min_box, peak_freq_range_max_box],layout=widgets.Layout(height='auto', width='auto'))

    peak_selection_type = widgets.Dropdown(description='Peak Selection Method', value='max',
                                    options=[('Highest Peak', 'max'),
                                             ('Best Scored','scored')],
                                    style={'description_width': 'initial'},  layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    process_hvsr_call = widgets.Label(value='process_hvsr()')

    check_peaks_call = widgets.Label(value='check_peaks()')

    # Set up grid for ppsd_settings subtab
    hvsr_settings_tab[0, 1:] = h_combine_meth

    hvsr_settings_tab[1, 1:12] = freq_smoothing
    hvsr_settings_tab[1, 12:17] = freq_smooth_width

    hvsr_settings_tab[2, 0] = resample_hv_curve_bool
    hvsr_settings_tab[2, 1:6] = resample_hv_curve

    hvsr_settings_tab[3, 0] = smooth_hv_curve_bool
    hvsr_settings_tab[3, 1:6] = smooth_hv_curve

    hvsr_settings_tab[4, 1:] = hvsr_band_hbox_hvsrSet

    hvsr_settings_tab[5, 1:] = peak_freq_range_hbox_hvsrSet

    hvsr_settings_tab[6, 1:] = peak_selection_type

    hvsr_settings_tab[7:9, 1:] = process_hvsr_call

    hvsr_settings_tab[9:11, 1:] = check_peaks_call

    # PLOT SETTINGS SUBTAB
    hv_plot_label = widgets.Label(value='HVSR Plot', layout=widgets.Layout(height='auto', width='auto', justify_content='center'))
    component_plot_label = widgets.Label(value='Component Plot', layout=widgets.Layout(height='auto', width='auto', justify_content='center'))
    spec_plot_label = widgets.Label(value='Spectrogram Plot', layout=widgets.Layout(height='auto', width='auto', justify_content='center'))

    use_plot_label = widgets.Label(value='Use Plot', layout=widgets.Layout(height='auto', width='auto', justify_content='flex-end', align_items='center'))
    use_plot_hv = widgets.Checkbox(value=True, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})
    use_plot_comp = widgets.Checkbox(value=True, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})
    use_plot_spec = widgets.Checkbox(value=True, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})

    comibne_plot_label = widgets.Label(value='Combine HV and Comp. Plot', layout=widgets.Layout(height='auto', width='auto', justify_content='flex-end', align_items='center'))
    combine_hv_comp = widgets.Checkbox(value=False, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})

    show_peak_label = widgets.Label(value='Show Best Peak', layout=widgets.Layout(height='auto', width='auto', justify_content='flex-end', align_items='center'))
    show_best_peak_hv = widgets.Checkbox(value=True, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})
    show_best_peak_comp = widgets.Checkbox(value=False, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})
    show_best_peak_spec = widgets.Checkbox(value=False, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})

    annotate_peak_label = widgets.Label(value='Annotate Best Peak', layout=widgets.Layout(height='auto', width='auto', justify_content='flex-end', align_items='center'))
    ann_best_peak_hv = widgets.Checkbox(value=True, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})
    ann_best_peak_comp = widgets.Checkbox(value=True, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})
    ann_best_peak_spec = widgets.Checkbox(value=True, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})

    show_all_peaks_label = widgets.Label(value='Show All Peaks', layout=widgets.Layout(height='auto', width='auto', justify_content='flex-end', align_items='center'))
    show_all_peaks_hv = widgets.Checkbox(value=False, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})

    show_all_curves_label = widgets.Label(value='Show All Curves', layout=widgets.Layout(height='auto', width='auto', justify_content='flex-end', align_items='center'))
    show_all_curves_hv = widgets.Checkbox(value=False, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})
    show_all_curves_comp = widgets.Checkbox(value=False, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})

    show_ind_peaks_label = widgets.Label(value='Show Individual Peaks', layout=widgets.Layout(height='auto', width='auto', justify_content='flex-end', align_items='center'))
    show_ind_peaks_hv = widgets.Checkbox(value=False, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})

    show_std_label = widgets.Label(value='Show Standard Deviation', layout=widgets.Layout(height='auto', width='auto', justify_content='flex-end', align_items='center'))
    show_std_hv = widgets.Checkbox(value=True, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})
    show_std_comp = widgets.Checkbox(value=True, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})

    show_legend_label = widgets.Label(value='Show Legend', layout=widgets.Layout(height='auto', width='auto', justify_content='flex-end', align_items='center'))
    show_legend_hv = widgets.Checkbox(value=False, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})
    show_legend_comp = widgets.Checkbox(value=False, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})
    show_legend_spec = widgets.Checkbox(value=False, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})

    x_type_label = widgets.Label(value='X Type', layout=widgets.Layout(height='auto', width='auto', justify_content='flex-end', align_items='center'))
    x_type = widgets.Dropdown(options=[('Frequency', 'freq'), ('Period', 'period')],
                              layout=widgets.Layout(height='auto', width='auto'), style={'description_width': 'initial'})

    plotly_kwargs_label = widgets.Label(value='Plotly Kwargs', layout=widgets.Layout(height='auto', width='auto', justify_content='flex-end', align_items='center'))
    plotly_kwargs = widgets.Text(style={'description_width': 'initial'},
                                layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    mpl_kwargs_label = widgets.Label(value='Matplotlib Kwargs', layout=widgets.Layout(height='auto', width='auto', justify_content='flex-end', align_items='center'))
    mpl_kwargs = widgets.Text(style={'description_width': 'initial'},
                                layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    plot_hvsr_call = widgets.Label(value='plot_hvsr()')

    # Set up grid for ppsd_settings subtab
    plot_settings_tab[0, 5:10]   = hv_plot_label
    plot_settings_tab[0, 10:15]  = component_plot_label
    plot_settings_tab[0, 15:] = spec_plot_label

    plot_settings_tab[1, :] = widgets.HTML('<hr>', layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'))

    plot_settings_tab[2, :5] = use_plot_label
    plot_settings_tab[2, 5:10] = use_plot_hv
    plot_settings_tab[2, 10:15] = use_plot_comp
    plot_settings_tab[2, 15:] = use_plot_spec

    plot_settings_tab[3, :] = widgets.HTML('<hr>', layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'))

    plot_settings_tab[4, :5] = comibne_plot_label
    plot_settings_tab[4, 10:15] =combine_hv_comp

    plot_settings_tab[5, :5] = show_peak_label
    plot_settings_tab[5, 5:10] = show_best_peak_hv
    plot_settings_tab[5, 10:15] = show_best_peak_comp
    plot_settings_tab[5, 15:] = show_best_peak_spec

    
    plot_settings_tab[6, :5] = annotate_peak_label
    plot_settings_tab[6, 5:10] = ann_best_peak_hv
    plot_settings_tab[6, 10:15] = ann_best_peak_comp
    plot_settings_tab[6, 15:] = ann_best_peak_spec

    plot_settings_tab[7, :5] = show_all_peaks_label
    plot_settings_tab[7, 5:10] = show_all_peaks_hv

    plot_settings_tab[8, :5] = show_all_curves_label
    plot_settings_tab[8, 5:10] = show_all_curves_hv
    plot_settings_tab[8, 10:15] = show_all_curves_comp

    plot_settings_tab[9, :5] = show_ind_peaks_label
    plot_settings_tab[9, 5:10] = show_ind_peaks_hv

    plot_settings_tab[10, :5] = show_std_label
    plot_settings_tab[10, 5:10] = show_std_hv
    plot_settings_tab[10, 10:15] = show_std_comp

    plot_settings_tab[11, :5] = show_legend_label
    plot_settings_tab[11, 5:10] = show_legend_hv
    plot_settings_tab[11, 10:15] = show_legend_comp
    plot_settings_tab[11, 15:] = show_legend_spec

    plot_settings_tab[12, :] = widgets.HTML('<hr>', layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'))

    plot_settings_tab[13, :5] = x_type_label
    plot_settings_tab[13, 6:] = x_type

    plot_settings_tab[14, :5] = plotly_kwargs_label
    plot_settings_tab[14, 6:] = plotly_kwargs

    plot_settings_tab[15, :5] = mpl_kwargs_label
    plot_settings_tab[15, 6:] = mpl_kwargs

    plot_settings_tab[16, :] = widgets.HTML('<hr>', layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'))

    plot_settings_tab[17, :] = plot_hvsr_call

    # LOG TAB - not currently using
    #log_tab = widgets.GridspecLayout(ui_height, ui_width)
    #log_tab = widgets.Output()

    # RESULTS TAB
    subp = subplots.make_subplots(rows=3, cols=1, horizontal_spacing=0.01, vertical_spacing=0.01, row_heights=[2,1,1])
    results_fig = go.FigureWidget(subp)
    results_graph_widget = widgets.Output()    
    results_tab = widgets.GridspecLayout(12, 20)

    results_label = widgets.Label(value='test')

    results_tab[:,:15] = results_graph_widget
    results_tab[:,15:] = results_label

    with results_graph_widget:
        display(results_fig)

    # SPRIT WIDGET
    # Add all  a tab and add the grid to it
    sprit_widget = widgets.Tab([input_tab, preview_tab, settings_tab,results_tab])
    sprit_widget.set_title(0, "Input")
    sprit_widget.set_title(1, "Preview")
    sprit_widget.set_title(2, "Settings")
    sprit_widget.set_title(3, "Results")

    def any_update():
        pass

    # Display the tab
    display(sprit_widget)

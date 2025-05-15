"""Functions to create jupyter notebook widget UI
"""

import datetime
import inspect
import os
import pathlib
import tkinter as tk
from tkinter import filedialog
import webbrowser

from zoneinfo import available_timezones

import ipywidgets as widgets
from IPython.display import display, clear_output
import numpy as np
import pandas as pd
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

global hvsr_data
    
OBSPY_FORMATS =  ['AH', 'ALSEP_PSE', 'ALSEP_WTH', 'ALSEP_WTN', 'CSS', 'DMX', 'GCF', 'GSE1', 'GSE2', 'KINEMETRICS_EVT', 'KNET', 'MSEED', 'NNSA_KB_CORE', 'PDAS', 'PICKLE', 'Q', 'REFTEK130', 'RG16', 'SAC', 'SACXY', 'SEG2', 'SEGY', 'SEISAN', 'SH_ASC', 'SLIST', 'SU', 'TSPAIR', 'WAV', 'WIN', 'Y']

def _get_default(func, param):
    return inspect.signature(func).parameters[param].default

def create_jupyter_ui():
    """Function that generates the user interface for Jupyter Notebooks.
    
    This interface uses ipywidgets, plotly, and IPython to create a user interface for processing data in a Jupyter notebook. 
    
    As of version 2.6.5, this is broken but there are plans to fix in the near future.

    """
    global hvsr_data

    ui_width = 20
    ui_height= 12
    global results_fig
    global log_textArea
    log_textArea = widgets.Textarea(value="SESSION LOG", disabled=True, layout={'height': '300px','width': '99%', 'overflow': 'scroll'})

    # INPUT TAB
    # Create a VBox for the accordions
    input_HBox = widgets.HBox()
    input_accordion_label_box = widgets.VBox()
    input_accordion_box = widgets.VBox()
    input_accordion = widgets.Accordion()

    # Metadata accordion
    metadata_grid = widgets.GridspecLayout(7, 10)
    network_textbox = widgets.Text(description='Network:',
                                    placeholder=_get_default(sprit_hvsr.input_params, 'network'),
                                    value=_get_default(sprit_hvsr.input_params, 'network'),
                                    tooltip="input_params(network)")

    station_textbox = widgets.Text(description='Station:',
                                    placeholder=_get_default(sprit_hvsr.input_params, 'station'),
                                    value=_get_default(sprit_hvsr.input_params, 'station'))

    location_textbox = widgets.Text(description='Location:',
                                    placeholder=_get_default(sprit_hvsr.input_params, 'location'),
                                    value=_get_default(sprit_hvsr.input_params, 'location'))

    z_channel_textbox = widgets.Text(description='Z Channel:',
                                    placeholder=_get_default(sprit_hvsr.input_params, 'channels')[0],
                                    value=_get_default(sprit_hvsr.input_params, 'channels')[0])

    e_channel_textbox = widgets.Text(description='E Channel:',
                                    placeholder=_get_default(sprit_hvsr.input_params, 'channels')[2],
                                    value=_get_default(sprit_hvsr.input_params, 'channels')[2])

    n_channel_textbox = widgets.Text(description='N Channel:',
                                    placeholder=_get_default(sprit_hvsr.input_params, 'channels')[1],
                                    value=_get_default(sprit_hvsr.input_params, 'channels')[1])


    # Instrument Settings
    inst_settings_text = widgets.Text(placeholder='Instrument Settings Filepath', layout=widgets.Layout(width='55%'))
    instrument_read_button = widgets.Button(icon='fa-file-import',button_style='success',
                                            layout=widgets.Layout(width='4%'))
    instrument_settings_button = widgets.Button(description='Select .inst file',
                                            layout=widgets.Layout(width='10%'))
    inst_settings_hbox = widgets.HBox([inst_settings_text,instrument_read_button, instrument_settings_button])
    
    def select_inst(event):
        try:
            if event.description == 'Select .inst file':
                root = tk.Tk()
                root.wm_attributes('-topmost', True)
                root.withdraw()
                inst_files = filedialog.askopenfilenames(defaultextension='.inst', filetypes=[('Inst', '.inst')],
                                                                    title="Select Instrument Settings File")
                if isinstance(inst_files, tuple):
                    pass
                else:
                    inst_files = tuple(inst_files)
                root.destroy()
            else:
                inst_files = tuple([inst_settings_text.value])

            for i, inst_f in enumerate(inst_files):
                inst_settings_text.value = pathlib.Path(inst_f).as_posix()
                inst_settings = sprit_hvsr.import_settings(settings_import_path=pathlib.Path(inst_f).as_posix(), settings_import_type='instrument')
                
                # Go through all items and add them
                if 'instrument' in inst_settings.keys():
                    if inst_settings['instrument'] not in instrument_dropdown.options:
                        instrument_dropdown.options.append(inst_settings['instrument'])
                    instrument_dropdown.value = inst_settings['instrument']
                
                if 'net' in inst_settings.keys():
                    network_textbox.value = inst_settings['net']

                if 'sta' in inst_settings.keys():
                    station_textbox.value = inst_settings['sta']

                if 'location' in inst_settings.keys():
                    location_textbox.value = inst_settings['location']

                if 'cha' in inst_settings.keys():
                    for c in inst_settings['cha']:
                        if c.lower()[2]=='z':
                            z_channel_textbox.value = c
                        if c.lower()[2]=='e':
                            e_channel_textbox.value = c
                        if c.lower()[2] =='n':
                            n_channel_textbox.value = c
                
                if 'metapath' in inst_settings.keys():
                    metadata_filepath.value = inst_settings['metapath']

                if 'hvsr_band' in inst_settings.keys():
                    hvsr_band_min_box.value = inst_settings['hvsr_band'][0]
                    hvsr_band_max_box.value = inst_settings['hvsr_band'][1]

        except Exception as e:
            print(e)
            instrument_settings_button.disabled=True
            instrument_settings_button.description='Use Text Field'
    
    instrument_settings_button.on_click(select_inst)
    instrument_read_button.on_click(select_inst)

    metadata_grid[0,:] = inst_settings_hbox
    metadata_grid[1,0] = network_textbox
    metadata_grid[2,0] = station_textbox
    metadata_grid[3,0] = location_textbox
    metadata_grid[4,0] = z_channel_textbox
    metadata_grid[5,0] = e_channel_textbox
    metadata_grid[6,0] = n_channel_textbox

    # Acquisition Accordion
    instrument_grid = widgets.GridspecLayout(5, 10)
    # Date Picker labelled "Acquisition Date"
    acquisition_date_picker = widgets.DatePicker(description='Acq.Date:',
                                            placeholder=datetime.datetime.today().date(),
                                            value=datetime.datetime.today().date())

    # Label that shows the Date currently selected in the Date Picker
    acquisition_doy = widgets.IntText(description='DOY',
                                                placeholder=f"{acquisition_date_picker.value.timetuple().tm_yday}",
                                                value=f"{acquisition_date_picker.value.timetuple().tm_yday}",
                                                layout=widgets.Layout(width='auto'))

    def on_acq_date_change(change):
        acquisition_doy.value = acquisition_date_picker.value.timetuple().tm_yday
    acquisition_date_picker.observe(on_acq_date_change)

    def on_doy_change(change):
        curr_year = datetime.datetime.today().year
        if acquisition_doy.value > datetime.datetime.today().timetuple().tm_yday:
            curr_year -= 1
        acquisition_date_picker.value = (datetime.datetime(curr_year, 1, 1) + datetime.timedelta(days = acquisition_doy.value-1)).date()
    acquisition_doy.observe(on_doy_change)

    # Time selector (hour and minute) labelled "Start Time".
    try:
        start_time_picker = widgets.TimePicker(description='Start Time:',
                                            placeholder=datetime.time(0,0,0),
                                            value=datetime.time(0,0,0),
                                            layout=widgets.Layout(width='auto'))
    except Exception as e:
        start_time_picker = widgets.Text(description='Start Time:',
                                        placeholder='00:00',
                                        value='00:00',
                                        layout=widgets.Layout(width='auto'))

    # Time selector (hour and minute) labelled "End Time". Same as Start Time otherwise.
    try:
        end_time_picker = widgets.TimePicker(description='End Time:',
                                        placeholder=datetime.time(23,59),
                                        value=datetime.time(23,59),
                                        layout=widgets.Layout(width='auto'))
    except Exception as e:
        end_time_picker = widgets.Text(description='End Time:',
                                        placeholder='23:59:59.999999',
                                        value='23:59:59.999999',
                                        layout=widgets.Layout(width='auto'))

    tzlist = list(available_timezones())
    tzlist.sort()
    tzlist.remove('UTC')
    tzlist.remove('US/Central')
    tzlist.insert(0, 'US/Central')
    tzlist.insert(0, 'UTC')
    # A dropdown list with all the items from zoneinfo.available_timezones(), default 'UTC'
    time_zone_dropdown = widgets.Dropdown(options=tzlist,value=_get_default(sprit_hvsr.input_params, 'tzone'),
                                            description='Time Zone:',layout=widgets.Layout(width='fill'))

    instrument_grid[0,0] = acquisition_date_picker
    instrument_grid[0,1] = acquisition_doy
    instrument_grid[1,0] = start_time_picker
    instrument_grid[2,0] = end_time_picker
    instrument_grid[3,0] = time_zone_dropdown

    # LOCATION ACCORDION
    location_grid = widgets.GridspecLayout(4, 10)
    # X coordinate input
    xcoord_textbox = widgets.FloatText(description='X Coordinate:', tooltip='xcoord',
                                        value=_get_default(sprit_hvsr.input_params, 'xcoord'), 
                                        placeholder=_get_default(sprit_hvsr.input_params, 'xcoord'),
                                        layout=widgets.Layout(width='auto'))
    location_grid[0, 0] = xcoord_textbox

    # Y coordinate input
    ycoord_textbox = widgets.FloatText(description='Y Coordinate', tooltip='ycoord:',
                                        value=_get_default(sprit_hvsr.input_params, 'ycoord'), 
                                        placeholder=_get_default(sprit_hvsr.input_params, 'ycoord'),
                                        layout=widgets.Layout(width='auto'))
    location_grid[1, 0] = ycoord_textbox

    # Z coordinate input
    zcoord_textbox = widgets.FloatText(description='Z Coordinate', tooltip='elevation:',
                                        value=_get_default(sprit_hvsr.input_params, 'elevation'),
                                        placeholder=_get_default(sprit_hvsr.input_params, 'elevation'),                                     
                                        layout=widgets.Layout(width='auto'))
    location_grid[2, 0] = zcoord_textbox

    # Z coordinate unit input
    elevation_unit_textbox = widgets.Dropdown(options=[('Feet', 'feet'), ('Meters', 'meters')],
                                                value=_get_default(sprit_hvsr.input_params, 'elev_unit'),
                                                description='Z Unit:', tooltip='elev_unit',
                                                layout=widgets.Layout(width='auto'))
    location_grid[2, 1] = elevation_unit_textbox

    # Input CRS input
    input_crs_textbox = widgets.Text(description='Input CRS:',
                                        layout=widgets.Layout(width='auto'),
                                        placholder=_get_default(sprit_hvsr.input_params, 'input_crs'),
                                        value=_get_default(sprit_hvsr.input_params, 'input_crs'))
    location_grid[3, 0] = input_crs_textbox

    # Output CRS input
    output_crs_textbox = widgets.Text(description='Output CRS:',
                                        layout=widgets.Layout(width='auto'),
                                        placholder=_get_default(sprit_hvsr.input_params, 'output_crs'),
                                        value=_get_default(sprit_hvsr.input_params, 'output_crs'))
    location_grid[3, 1] = output_crs_textbox

    # IO PARAMS ACCORDION
    ioparam_grid = widgets.GridspecLayout(6, 10)

    # Data format (for obspy format to use to read in)
    data_format_dropdown = widgets.Dropdown(
            options=OBSPY_FORMATS,
            value='MSEED',
            description='Data Formats:', layout=widgets.Layout(width='auto'))

    hvsr_band_min_box = widgets.FloatText(description='HVSR Band [Hz]', style={'description_width': 'initial'},
                                          placeholder=_get_default(sprit_hvsr.input_params, 'hvsr_band')[0],
                                          value=_get_default(sprit_hvsr.input_params, 'hvsr_band')[0])
    hvsr_band_max_box = widgets.FloatText(placeholder=_get_default(sprit_hvsr.input_params, 'hvsr_band')[1],
                                          value=_get_default(sprit_hvsr.input_params, 'hvsr_band')[1])
    hvsr_band_hbox = widgets.HBox([hvsr_band_min_box, hvsr_band_max_box],layout=widgets.Layout(width='auto'))


    peak_freq_range_min_box = widgets.FloatText(description='Peak Range [Hz]',placeholder=_get_default(sprit_hvsr.input_params, 'peak_freq_range')[0], 
                                                value=_get_default(sprit_hvsr.input_params, 'peak_freq_range')[0],
                                                style={'description_width': 'initial'}, layout=widgets.Layout(width='auto'))
    peak_freq_range_max_box = widgets.FloatText(placeholder=_get_default(sprit_hvsr.input_params, 'peak_freq_range')[1], 
                                                value=_get_default(sprit_hvsr.input_params, 'peak_freq_range')[1],layout=widgets.Layout(width='auto'))
    peak_freq_range_hbox = widgets.HBox([peak_freq_range_min_box, peak_freq_range_max_box],layout=widgets.Layout(width='auto'))


    # A dropdown labeled "Detrend type" with "Spline", "Polynomial", or "None"
    detrend_type_dropdown = widgets.Dropdown(options=[('Spline', 'spline'), ('Polynomial', 'polynomial'), ('None', 'none')],
                            description='Detrend Type:',  layout=widgets.Layout(width='auto'))
    detrend_options = widgets.FloatText(description='Order:', tooltip='detrend_options', placeholder=_get_default(sprit_hvsr.fetch_data, 'detrend_options'), 
                                      value=_get_default(sprit_hvsr.fetch_data, 'detrend_options'),layout=widgets.Layout(width='auto'))

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

    # Processing Settings
    proc_settings_text = widgets.Text(placeholder='Instrument Settings Filepath', layout=widgets.Layout(width='55%'))
    proc_settings_read_button = widgets.Button(icon='fa-file-import',button_style='success',
                                            layout=widgets.Layout(width='4%'))
    proc_settings_browse_button = widgets.Button(description='Select .proc file',
                                            layout=widgets.Layout(width='10%'))
    proc_settings_hbox = widgets.HBox([proc_settings_text, proc_settings_read_button, proc_settings_browse_button])
    
    excluded_params = ['hvsr_data', 'params', 'hvsr_results']
    funcList = [sprit_hvsr.fetch_data, sprit_hvsr.remove_noise,
                sprit_hvsr.generate_psds, sprit_hvsr.process_hvsr,
                sprit_hvsr.remove_outlier_curves, sprit_hvsr.check_peaks,
                sprit_hvsr.get_report]

    def select_proc(event):
        try:
            if event.description == 'Select .proc file':
                root = tk.Tk()
                root.wm_attributes('-topmost', True)
                root.withdraw()
                proc_files = filedialog.askopenfilenames(defaultextension='.proc', filetypes=[('PROC', '.proc')],
                                                                    title="Select Processing Settings File")
                if isinstance(proc_files, tuple):
                    pass
                else:
                    proc_files = tuple(proc_files)
                root.destroy()
            else:
                proc_files = tuple([proc_settings_text.value])

            for i, proc_f in enumerate(proc_files):
                proc_settings_text.value = pathlib.Path(proc_f).as_posix()
                proc_settings = sprit_hvsr.import_settings(settings_import_path=pathlib.Path(proc_f).as_posix(), settings_import_type='processing')
                
                for func, params in proc_settings.items():
                    if func in widget_param_dict.keys():
                        for prm, val in params.items():
                            if prm in widget_param_dict[func].keys():
                                #print(prm, ':', widget_param_dict[func][prm],' |  ', val)
                                if val is None or val=='None':
                                    val='none'
                                if prm == 'export_format':
                                    val = val.upper()
                                if prm == 'smooth':
                                    if val is True:
                                        val = 51
                                if prm == 'resample':
                                    if val is True:
                                        val = 1000
                                if isinstance(widget_param_dict[func][prm], list):
                                    for i, item in enumerate(widget_param_dict[func][prm]):
                                        item.value = val[i]
                                else:
                                    widget_param_dict[func][prm].value = val
        except Exception as e:
            print(e)
            proc_settings_browse_button.disabled=True
            proc_settings_browse_button.description='Use Text Field'
    
    proc_settings_read_button.on_click(select_proc)
    proc_settings_browse_button.on_click(select_proc)

    ioparam_grid[0,:] = proc_settings_hbox
    ioparam_grid[1,0] = data_format_dropdown
    ioparam_grid[2,:5] = hvsr_band_hbox
    ioparam_grid[3,:5] = peak_freq_range_hbox
    ioparam_grid[4,:1] = detrend_type_dropdown
    ioparam_grid[4,1] = detrend_options
    ioparam_grid[5,:6] = trim_directory
    ioparam_grid[5, 6:8] = trim_export_dropdown
    ioparam_grid[5, 8] = trim_directory_upload

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
    metaLabel = widgets.Label('Instrument', layout=widgets.Layout(height='20%', align_content='center', justify_content='flex-end'))
    instLabel = widgets.Label('Acquisition', layout=widgets.Layout(height='20%', align_content='center', justify_content='flex-end'))
    locLabel = widgets.Label('Location', layout=widgets.Layout(height='20%', align_content='center', justify_content='flex-end'))
    ioparmLabel = widgets.Label('IO/Params', layout=widgets.Layout(height='20%', align_content='center', justify_content='flex-end'))
    apiLabel = widgets.Label('API Call', layout=widgets.Layout(height='20%', align_content='center', justify_content='flex-end'))
    input_accordion_label_box.children = [metaLabel, instLabel, locLabel, ioparmLabel, apiLabel]
    input_accordion_label_box.layout = widgets.Layout(align_content='space-between', width='5%')

    input_accordion.children = [metadata_grid, instrument_grid, location_grid, ioparam_grid, inputAPI_grid]
    input_accordion.titles = ["Instrument Metadata", "Acquisition Information", "Location Information", "I/O and Parameters", "See Python API Call"]
    input_accordion_box.layout = widgets.Layout(align_content='space-between', width='99%')
    
    input_accordion.layout = widgets.Layout(width='99%')

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
    def on_ds_change(event):
        if data_source_type.value == 'file' or data_source_type.value== 'batch':
            browse_data_button.description = 'Select Files'
        else:
            browse_data_button.description = 'Select Folders'
    data_source_type.observe(on_ds_change)
    # Dropdown labeled "Instrument" with options "Raspberry Shake", "Tromino", "Other"
    instrument_dropdown = widgets.Dropdown(options=['Raspberry Shake', 'Tromino', 'Other'],
                                        style={'description_width': 'initial'},
                                        description='Instrument:',layout=widgets.Layout(width='20%'))

    # Processing Settings
    processing_settings_button = widgets.FileUpload(accept='.proc', description='Processing Settings',
                                            multiple=False,layout=widgets.Layout(width='10%'))

    # Whether to show plots outside of widget
    show_plot_check =  widgets.Checkbox(description='Print Plots', value=False, disabled=False, indent=False,
                                    layout=widgets.Layout(width='10%', justify_content='flex-end'))


    # Whether to print to terminal
    verbose_check = widgets.Checkbox(description='Verbose', value=False, disabled=False, indent=False,
                                    layout=widgets.Layout(width='10%', justify_content='flex-end'))

    # A text box labeled Data Filepath
    data_filepath = widgets.Text(description='Data Filepath:',
                                    placeholder='sample', value='sample',
                                    style={'description_width': 'initial'},layout=widgets.Layout(width='70%'))

    # A button next to it labeled "Browse"
    browse_data_button = widgets.Button(description='Select Files', layout=widgets.Layout(width='10%'))
    def select_datapath(event):
        try:
            root = tk.Tk()
            root.wm_attributes('-topmost', True)
            root.withdraw()
            if data_source_type.value=='file' or data_source_type.value=='batch':
                data_filepath.value = str(filedialog.askopenfilenames(defaultextension='.MSEED', title='Select Data File'))
            else:
                data_filepath.value = str(filedialog.askdirectory(mustexist=True, title="Select Data Directory"))
            root.destroy()
        except Exception as e:
            print(e)
            browse_data_button.disabled=True
            browse_data_button.description='Use Text Field'
    browse_data_button.on_click(select_datapath)

    # A text box labeled Metadata Filepath
    metadata_filepath = widgets.Text(description='Metadata Filepath:',
                                        style={'description_width': 'initial'},layout=widgets.Layout(width='70%'))

    # A button next to it labeled "Browse"
    browse_metadata_button = widgets.Button(description='Select File(s)', layout=widgets.Layout(width='10%'))
    def select_metapath(event):
        try:
            root = tk.Tk()
            root.wm_attributes('-topmost', True)
            root.withdraw()
            metadata_filepath.value = str(filedialog.askopenfilenames(title='Select Metadata File(s)'))
            root.destroy()
        except Exception as e:
            print(e)
            browse_metadata_button.disabled=True
            browse_metadata_button.description='Use Text Field'
    browse_metadata_button.on_click(select_metapath)

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
    def update_input_param_call():
        input_param_text = f"""(input_data='{data_filepath.value}', metapath='{metadata_filepath.value}', site='{site_name.value}', network='{network_textbox.value}',
                    station='{station_textbox.value}', location='{location_textbox.value}', loc='{location_textbox.value}', channels={[z_channel_textbox.value, e_channel_textbox.value, n_channel_textbox.value]},
                    acq_date='{acquisition_date_picker.value}', starttime='{start_time_picker.value}', endtime='{end_time_picker.value}', tzone='{time_zone_dropdown.value}',
                    xcoord={xcoord_textbox.value}, ycoord={ycoord_textbox.value}, elevation={zcoord_textbox.value}, depth=0
                    input_crs='{input_crs_textbox.value}', output_crs='{output_crs_textbox.value}', elev_unit='{elevation_unit_textbox.value}',
                    instrument='{instrument_dropdown.value}', hvsr_band={[hvsr_band_min_box.value, hvsr_band_max_box.value]}, 
                    peak_freq_range={[peak_freq_range_min_box.value, peak_freq_range_max_box.value]}, verbose={verbose_check.value})"""
        input_params_call.value='<style>p {word-wrap: break-word}</style> <p>' + input_param_text + '</p>'
    update_input_param_call()
    
    # Update fetch_data call
    def update_fetch_data_call():
        fetch_data_text = f"""(params=hvsr_data, source={data_source_type.value}, trim_dir={trim_directory.value},
                            export_format={trim_export_dropdown.value}, detrend={detrend_type_dropdown.value}, detrend_options={detrend_options.value}, verbose={verbose_check.value})"""
        fetch_data_call.value='<style>p {word-wrap: break-word}</style> <p>' + fetch_data_text + '</p>'
    update_fetch_data_call()

    site_hbox = widgets.HBox()
    site_hbox.children = [site_name, tenpct_spacer, tenpct_spacer, tenpct_spacer, tenpct_spacer, tenpct_spacer, show_plot_check, verbose_check]
    datapath_hbox = widgets.HBox()
    datapath_hbox.children = [data_filepath, browse_data_button, data_source_type]
    metadata_hbox = widgets.HBox()
    metadata_hbox.children = [metadata_filepath, browse_metadata_button, instrument_dropdown]
    progress_hbox = widgets.HBox()
    progress_hbox.children = [progress_bar, read_data_button, process_hvsr_button]

    input_params_vbox = widgets.VBox()
    input_params_vbox.children = [site_hbox,datapath_hbox,metadata_hbox,progress_hbox]

    input_accordion_box.children = [input_accordion]
    #input_HBox.children = [input_accordion_label_box, input_accordion_box]
    #input_HBox.layout= widgets.Layout(align_content='space-between')

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
            'input_data':data_filepath.value,
            'metapath':metadata_filepath.value,
            'site':site_name.value,
            'instrument':instrument_dropdown.value,
            'network':network_textbox.value, 'station':station_textbox.value, 'location':location_textbox.value, 
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
            'detrend_options':detrend_options.value}
        if str(fetch_data_kwargs['detrend']).lower() == 'none':
            fetch_data_kwargs['detrend'] = None
        
        if str(fetch_data_kwargs['trim_dir']).lower() == 'none':
            fetch_data_kwargs['trim_dir'] = None
        return fetch_data_kwargs

    def read_data(button):
        progress_bar.value = 0
        log_textArea.value += f"\n\nREADING DATA [{datetime.datetime.now()}]"

        ip_kwargs = get_input_params()
        hvsr_data = sprit_hvsr.input_params(**ip_kwargs, verbose=verbose_check.value)
        log_textArea.value += f"\n\n{datetime.datetime.now()}\ninput_params():\n'{ip_kwargs}"
        if button.description=='Read Data':
            progress_bar.value=0.333
        else:
            progress_bar.value=0.1
        fd_kwargs = get_fetch_data_params()
        hvsr_data = sprit_hvsr.fetch_data(hvsr_data, **fd_kwargs, verbose=verbose_check.value)
        log_textArea.value += '\n\n'+str(datetime.datetime.now())+'\nfetch_data():\n\t'+str(fd_kwargs)
        if button.description=='Read Data':
            progress_bar.value=0.666
        else:
            progress_bar.value=0.2
        
        use_hv_curve_rmse.value=False
        use_hv_curve_rmse.disabled=True

        update_preview_fig(hvsr_data, preview_fig)

        if button.description=='Read Data':
            sprit_tabs.selected_index = 1
            progress_bar.value=0
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
                                'remove_raw_noise':raw_data_remove_check.value,
                                'verbose':verbose_check.value}
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
            'verbose':verbose_check.value
            }

        if str(ppsd_kwargs['special_handling']).lower() == 'none':
            ppsd_kwargs['special_handling'] = None        
        return ppsd_kwargs

    def get_remove_outlier_curve_kwargs():
        roc_kwargs = {
                'use_percentile':rmse_pctile_check.value,
                'rmse_thresh':rmse_thresh.value,
                'use_hv_curve':False,
                'verbose':verbose_check.value
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
            resample_value = resample_hv_curve_bool.value

        ph_kwargs={'method':h_combine_meth.value,
                    'smooth':smooth_value,
                    'freq_smooth':freq_smoothing.value,
                    'f_smooth_width':freq_smooth_width.value,
                    'resample':resample_value,
                    'outlier_curve_rmse_percentile':use_hv_curve_rmse.value,
                    'verbose':verbose_check.value}
        return ph_kwargs

    def get_check_peaks_kwargs():
        cp_kwargs = {'hvsr_band':[hvsr_band_min_box.value, hvsr_band_max_box.value],
                    'peak_freq_range':[peak_freq_range_min_box.value, peak_freq_range_max_box.value],
                    'peak_selection':peak_selection_type.value,
                    'verbose':verbose_check.value}
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
            else:
                comp_plot_str=comp_plot_str.replace('+','')

            # Whether to show (log) standard deviations
            if not show_std_hv.value:
                hvsr_plot_str=hvsr_plot_str + " -s"
            if not show_std_comp.value:
                comp_plot_str=comp_plot_str + " -s"                

            # Whether to show all peaks
            if show_all_peaks_hv.value:
                hvsr_plot_str=hvsr_plot_str + " all"

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
            if show_ind_peaks_spec.value:
                spec_plot_str=spec_plot_str + ' tp'
            
            # Whether to show legend
            if show_legend_hv.value:
                hvsr_plot_str=hvsr_plot_str + " leg"
            if ann_best_peak_comp.value:
                comp_plot_str=comp_plot_str + " leg"
            if show_legend_spec.value:
                spec_plot_str=spec_plot_str + " leg"            

            # Combine string into one
            plot_str = hvsr_plot_str + ' ' + comp_plot_str+ ' ' + spec_plot_str
            return plot_str

        gr_kwargs = {'report_format':['print','csv'],
                     'plot_type':get_formatted_plot_str(),
                     'export_path':None,
                     'csv_overwrite_opt':'overwrite',
                     'no_output':False,
                    'verbose':verbose_check.value
                     }
        return gr_kwargs

    def process_data(button):
        startProc=datetime.datetime.now()
        progress_bar.value = 0
        log_textArea.value += f"\n\nPROCESSING DATA [{startProc}]"
        global hvsr_data
        # Read data again only if internal hvsr_data input_data variable is different from what is in the gui
        if not 'hvsr_data' in globals() or not hasattr(hvsr_data, 'input_data') or \
                (pathlib.Path(hvsr_data.input_data).as_posix() != pathlib.Path(data_filepath.value).as_posix()):
            hvsr_data = read_data(button)

        remove_noise_kwargs = get_remove_noise_kwargs()
        hvsr_data = sprit_hvsr.remove_noise(hvsr_data, **remove_noise_kwargs)
        log_textArea.value += f"\n\n{datetime.datetime.now()}\nremove_noise()\n\t{remove_noise_kwargs}"
        progress_bar.value = 0.3

        generate_ppsd_kwargs = get_generate_ppsd_kwargs()
        hvsr_data = sprit_hvsr.generate_psds(hvsr_data, **generate_ppsd_kwargs)
        progress_bar.value = 0.5
        log_textArea.value += f"\n\n{datetime.datetime.now()}\ngenerate_ppsds()\n\t{generate_ppsd_kwargs}"
        
       
        # If this was started by clicking "Generate PPSDs", stop here
        if button.description == 'Generate PPSDs':
            return

        ph_kwargs = get_process_hvsr_kwargs()
        hvsr_data = sprit_hvsr.process_hvsr(hvsr_data, **ph_kwargs)
        log_textArea.value += f"\n\n{datetime.datetime.now()}\nprocess_hvsr()\n\t{ph_kwargs}"
        progress_bar.value = 0.75
        update_outlier_fig()

        roc_kwargs = get_remove_outlier_curve_kwargs()
        hvsr_data = sprit_hvsr.remove_outlier_curves(hvsr_data, **roc_kwargs)
        log_textArea.value += f"\n\n{datetime.datetime.now()}\nremove_outlier_curves()\n\t{roc_kwargs}"
        progress_bar.value = 0.85
        outlier_fig, hvsr_data = update_outlier_fig()

        use_hv_curve_rmse.value=False
        use_hv_curve_rmse.disabled=False

        def get_rmse_range():
            minRMSE = 10000
            maxRMSE = -1
            if roc_kwargs['use_hv_curve']:
                colnames = ['HV_Curves']
            else:
                colnames = ['psd_values_Z',
                            'psd_values_E',
                            'psd_values_N']
            dataList = []
            for col in colnames:
                dataArr = np.stack(hvsr_data.hvsr_windows_df[col])
                medCurveArr = np.nanmedian(dataArr, axis=0)
                rmse = np.sqrt(((np.subtract(dataArr, medCurveArr)**2).sum(axis=1))/dataArr.shape[1])
                if rmse.min() < minRMSE:
                    minRMSE = rmse.min()
                if rmse.max() > maxRMSE:
                    maxRMSE = rmse.max()
            rmse_thresh_slider.min = minRMSE
            rmse_thresh_slider.max = maxRMSE
            rmse_thresh_slider.step = round((maxRMSE-minRMSE)/100, 2)
            rmse_thresh_slider.value = maxRMSE
        get_rmse_range()

        cp_kwargs = get_check_peaks_kwargs()
        hvsr_data = sprit_hvsr.check_peaks(hvsr_data, **cp_kwargs)
        log_textArea.value += f"\n\n{datetime.datetime.now()}\ncheck_peaks()\n\t{cp_kwargs}"
        progress_bar.value = 0.9

        gr_kwargs = get_get_report_kwargs()
        hvsr_data = sprit_hvsr.get_report(hvsr_data, **gr_kwargs)
        log_textArea.value += f"\n\n{datetime.datetime.now()}\nget_report()\n\t{gr_kwargs}\n\n"
        hvsr_data.get_report(report_format='print') # Just in case print wasn't included
        log_textArea.value += hvsr_data['Print_Report']
        printed_results_textArea.value = hvsr_data['Print_Report']
        hvsr_data.get_report(report_format='csv') 
        results_table.value = hvsr_data['CSV_Report'].to_html()
        
        log_textArea.value += f'Processing time: {datetime.datetime.now() - startProc}'
        progress_bar.value = 0.95

        update_results_fig(hvsr_data, gr_kwargs['plot_type'])
        
        progress_bar.value = 1
        global hvsr_results
        hvsr_results = hvsr_data
        return hvsr_results
        
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

    def parse_hv_plot_list(hv_data, hvsr_plot_list, azimuth='HV'):
        hvsr_data = hv_data
        x_data = hvsr_data.x_freqs['Z']
        hvsrDF = hvsr_data.hvsr_windows_df
        if azimuth == 'HV':
            HVCol = 'HV_Curves'
        else:
            HVCol = 'HV_Curves_'+azimuth

        if 'tp' in hvsr_plot_list:
            allpeaks = []
            for row in hvsrDF[hvsrDF['Use']]['CurvesPeakFreqs_'+azimuth].values:
                for peak in row:
                    allpeaks.append(peak)
            allInd = []
            for row, peakList in enumerate(hvsrDF[hvsrDF['Use']]['CurvesPeakIndices_'+azimuth].values):
                for ind in peakList:
                    allInd.append((row, ind))
            x_vals = []
            y_vals = []
            y_max = np.nanmax(hvsr_data.hvsrp[azimuth])
            hvCurveInd = list(hvsrDF.columns).index(HVCol)

            for i, tp in enumerate(allpeaks):
                x_vals.extend([tp, tp, None]) # add two x values and a None
                y_vals.extend([0, hvsrDF.iloc[allInd[i][0], hvCurveInd][allInd[i][1]], None]) # add the first and last y values and a None            

            results_fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines',
                                            line=dict(width=4, dash="solid", 
                                            color="rgba(128,0,0,0.1)"), 
                                            name='Best Peaks Over Time'),
                                            row=1, col=1)

        if 't' in hvsr_plot_list:
            alltimecurves = np.stack(hvsrDF[hvsrDF['Use']][HVCol])
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
            for i, p in enumerate(hvsr_data['hvsr_peak_freqs'][azimuth]):
                if i==0:
                    showLeg = True
                else:
                    showLeg= False

                results_fig.add_trace(go.Scatter(
                    x=[p, p, None], # set x to None
                    y=[0, np.nanmax(np.stack(hvsrDF[HVCol])),None], # set y to None
                    mode="lines", # set mode to lines
                    line=dict(width=1, dash="dot", color="gray"), # set line properties
                    name="All checked peaks", # set legend name
                    showlegend=showLeg),
                    row=1, col=1)

        if '-s' not in hvsr_plot_list:
            # Show standard deviation
            results_fig.add_trace(go.Scatter(x=x_data, y=hvsr_data.hvsrp2[azimuth],
                                    line={'color':'black', 'width':0.1},marker=None, 
                                    showlegend=False, name='Log. St.Dev. Upper',
                                    hoverinfo='none'),
                                    row=1, col=1)
            
            results_fig.add_trace(go.Scatter(x=x_data, y=hvsr_data.hvsrm2[azimuth],
                                    line={'color':'black', 'width':0.1},marker=None,
                                    fill='tonexty', fillcolor="rgba(128, 128, 128, 0.6)",
                                    name='Log. St.Dev.', hoverinfo='none'),
                                    row=1, col=1)
                
        if 'p' in hvsr_plot_list:
            results_fig.add_trace(go.Scatter(
                x=[hvsr_data['BestPeak'][azimuth]['f0'], hvsr_data['BestPeak'][azimuth]['f0'], None], # set x to None
                y=[0,np.nanmax(np.stack(hvsrDF['HV_Curves'])),None], # set y to None
                mode="lines", # set mode to lines
                line=dict(width=1, dash="dash", color="black"), # set line properties
                name="Best Peak"),
                row=1, col=1)

        if 'ann' in hvsr_plot_list:
            # Annotate best peak
            results_fig.add_annotation(x=np.log10(hvsr_data['BestPeak'][azimuth]['f0']),
                                    y=0, yanchor='bottom', xanchor='center',
                                    text=f"{hvsr_data['BestPeak'][azimuth]['f0']:.3f} Hz",
                                    bgcolor='rgba(255, 255, 255, 0.7)',
                                    showarrow=False,
                                    row=1, col=1)
        return results_fig

    def parse_comp_plot_list(hv_data, comp_plot_list, azimuth='HV'):
        
        hvsr_data = hv_data
        # Initial setup
        x_data = hvsr_data.x_freqs['Z']
        hvsrDF = hvsr_data.hvsr_windows_df
        same_plot = ((comp_plot_list != []) and ('+' not in comp_plot_list[0]))

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

        for az in hvsr_data.hvsr_az.keys():
            components.append(az)
            compColor_semi_light[az] = f'rgba(0,128,0,{alpha})'
            compColor_semi[az] = f'rgba(100,128,100,{alpha})'
            compColor[az] = f'rgba(100,250,100,{alpha})'

        # Whether to plot in new subplot or not
        if  comp_plot_list != [] and '+' in comp_plot_list[0]:
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
                x=[hvsr_data['BestPeak'][azimuth]['f0'], hvsr_data['BestPeak'][azimuth]['f0'], None], # set x to None
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
            results_fig.add_annotation(x=np.log10(hvsr_data['BestPeak'][azimuth]['f0']),
                            y=minVal,
                            text=f"{hvsr_data['BestPeak'][azimuth]['f0']:.3f} Hz",
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

    def parse_spec_plot_list(hv_data, spec_plot_list, subplot_num, azimuth='HV'):
        hvsr_data = hv_data
        if azimuth == 'HV':
            HVCol = 'HV_Curves'
        else:
            HVCol = 'HV_Curves_'+azimuth

        # Initial setup
        hvsrDF = hvsr_data.hvsr_windows_df
        specAxisTimes = np.array([dt.isoformat() for dt in hvsrDF.index.to_pydatetime()])
        y_data = hvsr_data.x_freqs['Z'][1:]
        image_data = np.stack(hvsrDF[HVCol]).T

        maxZ = np.percentile(image_data, 100)
        minZ = np.percentile(image_data, 0)

        use_mask = hvsr_data.hvsr_windows_df.Use.values
        use_mask = np.tile(use_mask, (image_data.shape[0],1))
        use_mask = np.where(use_mask is False, np.nan, use_mask)

        hmap = go.Heatmap(z=image_data,
                    x=specAxisTimes,
                    y=y_data,
                    colorscale='Turbo',
                    showlegend=False,
                    #opacity=0.7,
                    hovertemplate='Time [UTC]: %{x}<br>Frequency [Hz]: %{y:.2f}<br>H/V Amplitude: %{z:.2f}<extra></extra>',
                    zmin=minZ,zmax=maxZ, showscale=False, name='HV Curve Amp. over Time')
        results_fig.add_trace(hmap, row=subplot_num, col=1)

        data_used = go.Heatmap(
            x=specAxisTimes,
            y=y_data,
            z=use_mask,
            showlegend=False,
            colorscale=[[0, 'rgba(0,0,0,0.66)'], [0.25, 'rgba(0,0,0,0.66)'], [1, 'rgba(250,250,250,0)']],
            showscale=False, name='Used')
        results_fig.add_trace(data_used, row=subplot_num, col=1)


        # tp currently is not being added to spec_plot_list
        if 'tp' in spec_plot_list:
            yvals = []
            for row in hvsrDF[HVCol].values:
                maxInd = np.argmax(row)
                yvals.append(y_data[maxInd])
            tp_trace = go.Scatter(x=specAxisTimes, y=yvals, mode='markers',
                                    line=None, marker=dict(color='white', size=2, line=dict(color='black', width=0.1)), name='Individual H/V Peaks')
            results_fig.add_trace(tp_trace, row=subplot_num, col='all')

        if 'p' in spec_plot_list:
            results_fig.add_hline(y=hvsr_data['BestPeak'][azimuth]['f0'], line_width=1, line_dash='dash', line_color='black', row=subplot_num, col='all')

        if 'ann' in spec_plot_list:
            results_fig.add_annotation(x=specAxisTimes[-1],
                                    y=hvsr_data['hvsr_band'][1],
                                    text=f"Peak: {hvsr_data['BestPeak'][azimuth]['f0']:.3f} Hz",
                                    bgcolor='rgba(255, 255, 255, 0.7)',
                                    showarrow=False, xanchor='right', yanchor='top',
                                    row=subplot_num, col='all')

        if 'leg' in spec_plot_list:
            pass

        results_fig.update_yaxes(type='log',
                        range=[np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1])],
                        row=subplot_num, col=1)

        results_fig.add_annotation(
            text=f"{hvsrDF['Use'].astype(bool).sum()}/{hvsrDF.shape[0]} windows used",
            x=max(specAxisTimes),
            y=np.log10(min(y_data))+(np.log10(max(y_data))-np.log10(min(y_data)))*0.01,
            xanchor="right", yanchor="bottom",bgcolor='rgba(256,256,256,0.7)',
            showarrow=False,row=subplot_num, col=1)

        return results_fig

    def update_results_fig(hv_data, plot_string):
        global results_fig
        global results_subp
        hvsr_data = hv_data

        if isinstance(hvsr_data, sprit_hvsr.HVSRBatch):
            hvsr_data=hvsr_data[0]

        hvsrDF = hvsr_data.hvsr_windows_df

        plot_list = parse_plot_string(plot_string)

        combinedComp=False
        noSubplots = 3 - plot_list.count([])
        if plot_list[1] != [] and '+' not in plot_list[1][0]:
            combinedComp = True
            noSubplots -= 1
        
        # Get all data for each plotted item
        # COMP Plot
        # Figure out which subplot is which
        if combinedComp:
            comp_plot_row = 1
            spec_plot_row = 2
        else:
            comp_plot_row = 2
            spec_plot_row = 3

        # Re-initialize results_fig
        results_fig.data = []
        results_fig.update_layout(grid=None)  # Clear the existing grid layout
        if not combinedComp: 
            results_subp = subplots.make_subplots(rows=3, cols=1, horizontal_spacing=0.01, vertical_spacing=0.07,
                                                row_heights=[2, 1.5, 1])
        else:
            results_subp = subplots.make_subplots(rows=2, cols=1, horizontal_spacing=0.01, vertical_spacing=0.07,
                                    specs =[[{'secondary_y': True}],
                                            [{'secondary_y': False}]],
                                            row_heights=[1, 1])
        results_fig.update_layout(grid={'rows': noSubplots})
        #del results_fig
        results_fig = go.FigureWidget(results_subp)

        results_fig = parse_comp_plot_list(hvsr_data, comp_plot_list=plot_list[1])

        # HVSR Plot (plot this after COMP so it is on top COMP and to prevent deletion with no C+)
        results_fig = parse_hv_plot_list(hvsr_data, hvsr_plot_list=plot_list[0])
        # Will always plot the HV Curve
        results_fig.add_trace(go.Scatter(x=hvsr_data.x_freqs['Z'],y=hvsr_data.hvsr_curve,
                            line={'color':'black', 'width':1.5},marker=None, name='HVSR Curve'),
                            row=1, col='all')

        # SPEC plot
        results_fig = parse_spec_plot_list(hvsr_data, spec_plot_list=plot_list[2], subplot_num=spec_plot_row)

        # Final figure updating
        showtickLabels = (plot_list[1]==[] or '+' not in plot_list[1][0])
        if showtickLabels:
            side='bottom'
        else:
            side='top'
        results_fig.update_xaxes(type='log',
                        range=[np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1])],
                        side='top',
                        row=1, col=1)
        
        results_fig.update_xaxes(type='log',overlaying='x',
                        range=[np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1])],
                        side='bottom',
                        row=1, col=1)
        if comp_plot_row!=1:
            results_fig.update_xaxes(showticklabels=showtickLabels, row=comp_plot_row, col=1)
        
        if preview_fig.layout.width is None:
            if outlier_fig.layout.width is None:
                chartwidth = 800
            else:
                chartwidth = outlier_fig.layout.width

        else:
            chartwidth = preview_fig.layout.width

        results_fig.update_layout(margin={"l":10, "r":10, "t":35, 'b':0},
                                showlegend=False, autosize=True, height = 1.2 * float(chartwidth),
                                title=f"{hvsr_data['site']} Results")
        results_fig.update_yaxes(title_text='H/V Ratio', row=1, col=1)
        results_fig.update_yaxes(title_text='H/V Over Time', row=noSubplots, col=1)
        if comp_plot_row==1:
            results_fig.update_yaxes(title_text="PPSD Amp\n[m2/s4/Hz][dB]", secondary_y=True, row=comp_plot_row, col=1)
        else:
            results_fig.update_yaxes(title_text="PPSD Amp\n[m2/s4/Hz][dB]", row=comp_plot_row, col=1)
        
        # Reset results_graph_widget and display 
        with results_graph_widget:
            clear_output(wait=True)
            display(results_fig)

        if show_plot_check.value:
            results_fig.show()


        sprit_tabs.selected_index = 4
        log_textArea.value += f"\n\n{datetime.datetime.now()}\nResults Figure Updated: {plot_string}"
      
    process_hvsr_button.on_click(process_data)

    # PREVIEW TAB
    #Initialize plot
    preview_subp = subplots.make_subplots(rows=4, cols=1, shared_xaxes=True, horizontal_spacing=0.01, vertical_spacing=0.01, row_heights=[3,1,1,1])
    preview_fig = go.FigureWidget(preview_subp)

    def update_preview_fig(hv_data, preview_fig):
        preview_fig.data = []
        
        hvsr_data = hv_data
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
                                  title=f"{hvsr_data['site']} Data Preview")

        if show_plot_check.value:
            preview_fig.show()

    # REMOVE NOISE SUBTAB
    # STA/LTA Antitrigger
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
    remove_noise_prefix = widgets.HTML(value='<style>p {word-wrap: break-word}</style> <p>' + 'remove_noise' + '</p>', 
                                       layout=widgets.Layout(width='fill', justify_content='flex-end',align_content='flex-start'))
    remove_noise_call = widgets.HTML(value='()')
    remove_noise_call_hbox = widgets.HBox([remove_noise_prefix, remove_noise_call])

    # Update remove_outlier call
    def update_remove_noise_call():
        rnkwargs = get_remove_noise_kwargs()
        rn_text = f"""(hvsr_data=hvsr_data, remove_method={rnkwargs['remove_method']}, 
                    sat_percent={rnkwargs['sat_percent']}, 
                    noise_percent={rnkwargs['noise_percent']}, 
                    sta={rnkwargs['sta']}, 
                    lta={rnkwargs['lta']}, 
                    stalta_thresh={rnkwargs['stalta_thresh']}, 
                    warmup_time={rnkwargs['warmup_time']}, 
                    cooldown_time={rnkwargs['cooldown_time']}, 
                    min_win_size={rnkwargs['min_win_size']}, 
                    remove_raw_noise={rnkwargs['remove_raw_noise']}, 
                    verbose={verbose_check.value})"""
        remove_noise_call.value='<style>p {word-wrap: break-word}</style> <p>' + rn_text + '</p>'
    update_remove_noise_call()

    #Update noise windows
    update_noise_windows_button = widgets.Button(description='Update Noise Windows',button_style='info',layout=widgets.Layout(height='auto', width='auto'), disabled=True)

    preview_graph_widget = widgets.Output()
    #progress bar (same as above)
    preview_progress_hbox = widgets.HBox(children=[progress_bar, update_noise_windows_button, process_hvsr_button])

    # Add it all in to the tab
    stalta_hbox = widgets.HBox([stalta_check, sta, lta, stalta_thresh_low, stalta_thresh_hi])
    sat_hbox = widgets.HBox([max_saturation_check, max_saturation_pct])
    noise_win_hbox = widgets.HBox([noisy_windows_check, max_window_pct, noisy_window_length])
    warmcool_hbox = widgets.HBox([warmcool_check, warmup_time, cooldown_time])
    std_ratio_hbox = widgets.HBox([std_ratio_check, std_ratio_text, std_window_length_text])
    spacer_hbox = widgets.HBox([tenpct_spacer])

    preview_noise_tab = widgets.VBox([stalta_hbox,
                                      sat_hbox,
                                      noise_win_hbox,
                                      warmcool_hbox,
                                      std_ratio_hbox,
                                      auto_remove_check,
                                      raw_data_remove_check,
                                      spacer_hbox,
                                      remove_noise_call_hbox])

    preview_graph_tab = widgets.VBox(children=[preview_graph_widget])
    preview_subtabs = widgets.Tab([preview_graph_tab, preview_noise_tab])
    preview_tab = widgets.VBox()

    preview_subtabs.set_title(0, "Data Preview")
    preview_subtabs.set_title(1, "Noise Removal")

    preview_tab.children = [preview_subtabs, preview_progress_hbox]
    # Initialize tab
    with preview_graph_widget:
        display(preview_fig)

    # SETTINGS TAB
    plot_settings_tab = widgets.GridspecLayout(18, ui_width)
    settings_progress_hbox = widgets.HBox(children=[progress_bar, tenpct_spacer, process_hvsr_button])

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
    minPLim = round(1/(hvsr_band_max_box.value), 3)
    maxPLim = round(1/(hvsr_band_min_box.value), 3)
    period_limits_min = widgets.FloatText(description='Min. Period Limit', style={'description_width': 'initial'},
                                    placeholder=minPLim, value=minPLim, layout=widgets.Layout(height='auto', width='auto'), disabled=False)
    period_limits_max = widgets.FloatText(description='Max. Period Limit', style={'description_width': 'initial'},
                                    placeholder=maxPLim, value=maxPLim, layout=widgets.Layout(height='auto', width='auto'), disabled=False)
    period_smoothing_width = widgets.FloatText(description='Period Smoothing Width', style={'description_width': 'initial'},
                                    placeholder=1, value=1, layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    special_handling_dropdown = widgets.Dropdown(description='Special Handling', value='none',
                                                options=[('None', 'none'), ('Ringlaser', 'ringlaser'), ('Hydrophone', 'hydrophone')],
                                            style={'description_width': 'initial'},  layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    #remove_noise call
    generate_ppsd_prefix = widgets.HTML(value='<style>p {word-wrap: break-word}</style> <p>' + 'generate_psds' + '</p>', 
                                       layout=widgets.Layout(width='fill', justify_content='flex-end',align_content='flex-start'))
    generate_ppsd_call = widgets.HTML(value='()')
    generate_ppsd_call_hbox = widgets.HBox([generate_ppsd_prefix, generate_ppsd_call])

    # Update generate_psds() call
    def update_generate_ppsd_call():
        gppsdkwargs = get_generate_ppsd_kwargs()
        gppsd_text = f"""(hvsr_data=hvsr_data, 
                        stats=hvsr_data['stream'].select(component='*').traces[0].stats, 
                        metadata=hvsr_data['paz']['*'], 
                        skip_on_gaps={gppsdkwargs['skip_on_gaps']}, 
                        db_bins={gppsdkwargs['db_bins']}, 
                        ppsd_length={gppsdkwargs['ppsd_length']}, 
                        overlap={gppsdkwargs['overlap']}, 
                        special_handling={gppsdkwargs['special_handling']}, 
                        period_smoothing_width_octaves={gppsdkwargs['period_smoothing_width_octaves']}, 
                        period_step_octaves={gppsdkwargs['period_step_octaves']}, 
                        period_limits={gppsdkwargs['period_limits']}, 
                        verbose={verbose_check.value})"""
        generate_ppsd_call.value='<style>p {word-wrap: break-word}</style> <p>' + gppsd_text + '</p>'
    update_generate_ppsd_call()

    ppsd_length_hbox = widgets.HBox([ppsd_length_label, ppsd_length])
    overlap_pct_hbox = widgets.HBox([overlap_pct_label, overlap_pct])
    pstep_hbox = widgets.HBox([period_step_label, period_step_octave])
    skipgaps_hbox = widgets.HBox([skip_on_gaps_label, skip_on_gaps])
    db_bins_hbox = widgets.HBox([db_step_label, db_bins_min, db_bins_max, db_bins_step])
    plim_hbox = widgets.HBox([period_limit_label, period_limits_min, period_limits_max, period_smoothing_width])

    ppsd_settings_tab = widgets.VBox([ppsd_length_hbox,
                                      overlap_pct_hbox,
                                      pstep_hbox,
                                      skipgaps_hbox,
                                      db_bins_hbox,
                                      plim_hbox,
                                      special_handling_dropdown,
                                      generate_ppsd_call_hbox])

    # OUTLIER SETTINGS SUBTAB
    rmse_pctile_check = widgets.Checkbox(description='Using percentile', layout=widgets.Layout(height='auto', width='auto'), style={'description_width': 'initial'}, value=True)
    rmse_thresh = widgets.FloatText(description='RMSE Threshold', style={'description_width': 'initial'},
                                    placeholder=98, value=98, layout=widgets.Layout(height='auto', width='auto'), disabled=False)
    use_hv_curve_rmse = widgets.Checkbox(description='Use HV Curve Outliers (may only be used after they have been calculated during the process_hvsr() step))', layout=widgets.Layout(height='auto', width='auto'), style={'description_width': 'initial'}, value=False, disabled=True)

    outlier_threshbox_hbox = widgets.HBox(children=[rmse_thresh, rmse_pctile_check])
    outlier_params_vbox = widgets.VBox(children=[outlier_threshbox_hbox, use_hv_curve_rmse])

    global outlier_fig
    outlier_fig = go.FigureWidget()
    outlier_graph_widget = widgets.Output()

    outlier_thresh_slider_label = widgets.Label(value='RMSE Thresholds:')
    rmse_thresh_slider = widgets.FloatSlider(value=0, min=0, max=100, step=0.1,description='RMSE Value',layout=widgets.Layout(height='auto', width='auto'),disabled=True)
    rmse_pctile_slider = widgets.FloatSlider(value=_get_default(sprit_hvsr.remove_outlier_curves, 'rmse_thresh'), min=0, max=100, step=0.1, description="Percentile",layout=widgets.Layout(height='auto', width='auto'),)
    
    def calc_rmse(array_2d):
        medArray = np.nanmedian(array_2d, axis=0)
        rmse = np.sqrt(((np.subtract(array_2d, medArray)**2).sum(axis=1))/array_2d.shape[1])
        return rmse
    
    def on_update_rmse_thresh_slider(change):
        if use_hv_curve_rmse.value:
            rmse = calc_rmse(np.stack(hvsr_data.hvsr_windows_df['HV_Curves']))
        else:
            rmsez = calc_rmse(np.stack(hvsr_data.hvsr_windows_df['psd_values_Z']))
            rmsee = calc_rmse(np.stack(hvsr_data.hvsr_windows_df['psd_values_E']))
            rmsen = calc_rmse(np.stack(hvsr_data.hvsr_windows_df['psd_values_N']))

            rmse = np.stack([rmsez, rmsee, rmsen]).flatten()

        if rmse_pctile_check.value:
            rmse_thresh.value = rmse_pctile_slider.value
        else:
            rmse_thresh.value = rmse_thresh_slider.value
            rmse_pctile_slider.value = ((rmse < rmse_thresh_slider.value).sum() / len(rmse)) * 100

    def on_update_rmse_pctile_slider(change):
        if use_hv_curve_rmse.value:
            rmse = calc_rmse(np.stack(hvsr_data.hvsr_windows_df['HV_Curves']))
        else:
            rmsez = calc_rmse(np.stack(hvsr_data.hvsr_windows_df['psd_values_Z']))
            rmsee = calc_rmse(np.stack(hvsr_data.hvsr_windows_df['psd_values_E']))
            rmsen = calc_rmse(np.stack(hvsr_data.hvsr_windows_df['psd_values_N']))

            rmse = np.stack([rmsez, rmsee, rmsen])

        if rmse_pctile_check.value:
            rmse_thresh_slider.value = np.percentile(rmse, rmse_pctile_slider.value)
            rmse_thresh.value = rmse_pctile_slider.value
        else:
            rmse_thresh.value = rmse_thresh_slider.value

    def on_update_rmse_pctile_check(change):
        if rmse_pctile_check.value:
            rmse_pctile_slider.disabled = False
            rmse_thresh_slider.disabled = True
        else:
            rmse_pctile_slider.disabled = True
            rmse_thresh_slider.disabled = False
    
    def on_update_rmse_thresh(change):
        if rmse_pctile_check.value:
            rmse_pctile_slider.value = rmse_thresh.value
        else:
            rmse_thresh_slider.value = rmse_thresh.value

    rmse_pctile_check.observe(on_update_rmse_pctile_check)
    rmse_thresh_slider.observe(on_update_rmse_thresh_slider)
    rmse_pctile_slider.observe(on_update_rmse_pctile_slider)
    rmse_thresh.observe(on_update_rmse_thresh)

    use_hv_curve_label = widgets.Label(value='NOTE: Outlier curves may only be identified after PPSDs have been calculated (during the generate_psds() step)', layout=widgets.Layout(height='auto', width='80%'))
    generate_ppsd_button = widgets.Button(description='Generate PPSDs', layout=widgets.Layout(height='auto', width='20%', justify_content='flex-end'), disabled=False)
    update_outlier_plot_button = widgets.Button(description='Remove Outliers', layout=widgets.Layout(height='auto', width='20%', justify_content='flex-end'), disabled=False)
    outlier_ppsd_hbox = widgets.HBox([use_hv_curve_label, generate_ppsd_button, update_outlier_plot_button])
    remove_outlier_curve_prefix = widgets.HTML(value='<style>p {word-wrap: break-word}</style> <p>' + 'remove_outlier_curves' + '</p>', 
                                       layout=widgets.Layout(width='fill', justify_content='flex-end',align_content='flex-start'))
    remove_outlier_curve_call = widgets.HTML(value='()')
    remove_outlier_hbox = widgets.HBox([remove_outlier_curve_prefix, remove_outlier_curve_call])

    # Update remove_outlier call
    def update_remove_outlier_curve_call():
        roc_text = f"""(hvsr_data=hvsr_data, rmse_thresh={rmse_thresh.value}, use_percentile={rmse_pctile_check.value},
                            use_hv_curve={use_hv_curve_rmse.value}...verbose={verbose_check.value})"""
        remove_outlier_curve_call.value='<style>p {word-wrap: break-word}</style> <p>' + roc_text + '</p>'
    update_remove_outlier_curve_call()

    def update_outlier_fig_button(button):
        outlier_fig, hvsr_data = update_outlier_fig(button)

    generate_ppsd_button.on_click(process_data)

    update_outlier_plot_button.on_click(update_outlier_fig_button)

    outlier_settings_tab = widgets.VBox(children=[outlier_params_vbox,
                                                  outlier_graph_widget,
                                                  outlier_thresh_slider_label,
                                                  rmse_thresh_slider,
                                                  rmse_pctile_slider,
                                                  outlier_ppsd_hbox,
                                                  remove_outlier_hbox])

    with outlier_graph_widget:
        display(outlier_fig)

    def update_outlier_fig(input=None, _rmse_thresh=rmse_pctile_slider.value, _use_percentile=True, _use_hv_curve=use_hv_curve_rmse.value, _verbose=verbose_check.value):
        global outlier_fig
        global hvsr_data
        hv_data = hvsr_data


        roc_kwargs = {'rmse_thresh':rmse_pctile_slider.value,
                        'use_percentile':True,
                        'use_hv_curve':use_hv_curve_rmse.value,
                        'plot_engine':'plotly',
                        'show_plot':False,
                        'verbose':verbose_check.value
                      }
        if 'PPSDStatus' in hvsr_data.ProcessingStatus.keys() and hvsr_data.ProcessingStatus['PPSDStatus']:
            log_textArea.value += f"\n\n{datetime.datetime.now()}\nremove_outlier_curves():\n'{roc_kwargs}"    
            hvsr_data = sprit_hvsr.remove_outlier_curves(hvsr_data, **roc_kwargs)
        else:
            log_textArea.value += f"\n\n{datetime.datetime.now()}\nremove_outlier_curves() attempted, but not completed. hvsr_data.ProcessingStatus['PPSDStatus']=False\n'{roc_kwargs}"
            return outlier_fig, hvsr_data

        if roc_kwargs['use_hv_curve']:
            no_subplots = 1
            if hasattr(hvsr_data, 'hvsr_windows_df') and 'HV_Curves' in hvsr_data.hvsr_windows_df.columns:
                outlier_fig.data = []
                outlier_fig.update_layout(grid=None)  # Clear the existing grid layout
                outlier_subp = subplots.make_subplots(rows=no_subplots, cols=1, horizontal_spacing=0.01, vertical_spacing=0.1)
                outlier_fig.update_layout(grid={'rows': 1})
                outlier_fig = go.FigureWidget(outlier_subp)

                x_data = hvsr_data['x_freqs']
                curve_traces = []
                for hv in hvsr_data.hvsr_windows_df['HV_Curves'].iterrows():
                    curve_traces.append(go.Scatter(x=x_data, y=hv[1]))
                outlier_fig.add_traces(curve_traces)
                
                # Calculate a median curve, and reshape so same size as original
                medCurve = np.nanmedian(np.stack(hvsr_data.hvsr_windows_df['HV_Curves']), axis=0)
                outlier_fig.add_trace(go.Scatter(x=x_data, y=medCurve, line=dict(color='rgba(0,0,0,1)', width=1.5),showlegend=False))
                
                minY = np.nanmin(np.stack(hvsr_data.hvsr_windows_df['HV_Curves']))
                maxY = np.nanmax(np.stack(hvsr_data.hvsr_windows_df['HV_Curves']))
                totalWindows = hvsr_data.hvsr_windows_df.shape[0]
                #medCurveArr = np.tile(medCurve, (curr_data.shape[0], 1))

        else:
            no_subplots = 3
            outlier_fig.data = []
            outlier_fig.update_layout(grid=None)  # Clear the existing grid layout
            outlier_subp = subplots.make_subplots(rows=no_subplots, cols=1, horizontal_spacing=0.01, vertical_spacing=0.02,
                                                    row_heights=[1, 1, 1])
            outlier_fig.update_layout(grid={'rows': 3})
            outlier_fig = go.FigureWidget(outlier_subp)

            if hasattr(hvsr_data, 'hvsr_windows_df'):
                rowDict = {'Z':1, 'E':2, 'N':3}
                showTLabelsDict={'Z':False, 'E':False, 'N':True}
                def comp_rgba(comp, a):
                    compstr = ''
                    if comp=='Z':
                        compstr = f'rgba(0, 0, 0, {a})'
                    if comp=='E':
                        compstr = f'rgba(50, 50, 250, {a})'
                    if comp=='N':
                        compstr = f'rgba(250, 50, 50, {a})'
                    return compstr                         
                compNames = ['Z', 'E', 'N']
                rmse_to_plot=[]
                med_traces=[]

                noRemoved = 0
                indRemoved = []
                for i, comp in enumerate(compNames):
                    if hasattr(hvsr_data, 'x_freqs'):
                        x_data = hvsr_data['x_freqs'][comp]
                    else:
                        x_data = [1/p for p in hvsr_data['ppsds'][comp]['period_xedges'][1:]]                    
                    column = 'psd_values_'+comp
                    # Retrieve data from dataframe (use all windows, just in case)
                    curr_data = np.stack(hvsr_data['hvsr_windows_df'][column])
                    
                    # Calculate a median curve, and reshape so same size as original
                    medCurve = np.nanmedian(curr_data, axis=0)
                    medCurveArr = np.tile(medCurve, (curr_data.shape[0], 1))
                    medTrace = go.Scatter(x=x_data, y=medCurve, line=dict(color=comp_rgba(comp, 1), width=1.5), 
                                                 name=f'{comp} Component', showlegend=True)
                    # Calculate RMSE
                    rmse = np.sqrt(((np.subtract(curr_data, medCurveArr)**2).sum(axis=1))/curr_data.shape[1])

                    rmse_threshold = np.percentile(rmse, roc_kwargs['rmse_thresh'])
                    
                    # Retrieve index of those RMSE values that lie outside the threshold
                    timeIndex = hvsr_data['hvsr_windows_df'].index
                    for j, curve in enumerate(curr_data):
                        if rmse[j] > rmse_threshold:
                            badTrace = go.Scatter(x=x_data, y=curve,
                                                line=dict(color=comp_rgba(comp, 1), width=1.5, dash='dash'),
                                                #marker=dict(color=comp_rgba(comp, 1), size=3),
                                                name=str(hvsr_data.hvsr_windows_df.index[j]), showlegend=False)
                            outlier_fig.add_trace(badTrace, row=rowDict[comp], col=1)
                            if j not in indRemoved:
                                indRemoved.append(j)
                            noRemoved += 1
                        else:
                            goodTrace = go.Scatter(x=x_data, y=curve,
                                                  line=dict(color=comp_rgba(comp, 0.01)), name=str(hvsr_data.hvsr_windows_df.index[j]), showlegend=False)
                            outlier_fig.add_trace(goodTrace, row=rowDict[comp], col=1)

                    timeIndRemoved = pd.DatetimeIndex([timeIndex[ind] for ind in indRemoved])
                    hvsr_data['hvsr_windows_df'].loc[timeIndRemoved, 'Use'] = False

                    outlier_fig.add_trace(medTrace, row=rowDict[comp], col=1)
                    
                    outlier_fig.update_xaxes(showticklabels=False, row=1, col=1)
                    outlier_fig.update_yaxes(title={'text':'Z'}, row=1, col=1)
                    outlier_fig.update_xaxes(showticklabels=False, row=2, col=1)
                    outlier_fig.update_yaxes(title={'text':'E'}, row=2, col=1)
                    outlier_fig.update_xaxes(showticklabels=True, row=3, col=1)
                    outlier_fig.update_yaxes(title={'text':'N'}, row=3, col=1)

                    outlier_fig.update_layout(margin={"l":10, "r":10, "t":30, 'b':0}, showlegend=True,
                                  title=f"{hvsr_data['site']} Outliers")
                    if comp == 'N':
                        minY = np.nanmin(curr_data)
                        maxY = np.nanmax(curr_data)
                    totalWindows = curr_data.shape[0]
                
                outlier_fig.add_annotation(
                    text=f"{len(indRemoved)}/{totalWindows} outlier windows removed",
                    x=np.log10(max(x_data)) - (np.log10(max(x_data))-np.log10(min(x_data))) * 0.01,
                    y=minY+(maxY-minY)*0.01,
                    xanchor="right", yanchor="bottom",#bgcolor='rgba(256,256,256,0.7)',
                    showarrow=False,row=no_subplots, col=1)


        outlier_fig.update_xaxes(type='log')
        with outlier_graph_widget:
            clear_output(wait=True)
            display(outlier_fig)
        
        if show_plot_check.value:
            outlier_fig.show()

        return outlier_fig, hvsr_data

    # HVSR SETTINGS SUBTAB
    h_combine_meth = widgets.Dropdown(description='Horizontal Combination Method', value=3,
                                    options=[('1. Differential Field Assumption (not implemented)', 1), 
                                             ('2. Arithmetic Mean |  H = (N + E)/2', 2), 
                                             ('3. Geometric Mean | H = √(N * E) (SESAME recommended)', 3),
                                             ('4. Vector Summation | H = √(N^2 + E^2)', 4),
                                             ('5. Quadratic Mean | H = √(N^2 + E^2)/2', 5),
                                             ('6. Maximum Horizontal Value | H = max(N, E)', 6)],
                                    style={'description_width': 'initial'},  layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    freq_smoothing = widgets.Dropdown(description='Frequency Smoothing Operations', value='konno ohmachi',
                                    options=[('Konno-Ohmachi', 'konno ohmachi'),
                                             ('Constant','constant'),
                                             ('Proportional', 'proportional'),
                                             ('None', None)],
                                    style={'description_width': 'initial'},  layout=widgets.Layout(height='auto', width='auto'), disabled=False)
    freq_smooth_width = widgets.FloatText(description='Freq. Smoothing Width', style={'description_width': 'initial'},
                                    placeholder=40, value=40, layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    resample_hv_curve_bool = widgets.Checkbox(layout=widgets.Layout(height='auto', width='auto'), style={'description_width': 'initial'}, value=True)
    resample_hv_curve = widgets.IntText(description='Resample H/V Curve', style={'description_width': 'initial'},
                                    placeholder=512, value=512, layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    smooth_hv_curve_bool = widgets.Checkbox(layout=widgets.Layout(height='auto', width='auto'), style={'description_width': 'initial'}, value=True)
    smooth_hv_curve = widgets.IntText(description='Smooth H/V Curve', style={'description_width': 'initial'},
                                    placeholder=51, value=51, layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    hvsr_band_hbox_hvsrSet = widgets.HBox([hvsr_band_min_box, hvsr_band_max_box],layout=widgets.Layout(height='auto', width='auto'))

    peak_freq_range_hbox_hvsrSet = widgets.HBox([peak_freq_range_min_box, peak_freq_range_max_box],layout=widgets.Layout(height='auto', width='auto'))

    peak_selection_type = widgets.Dropdown(description='Peak Selection Method', value='max',
                                    options=[('Highest Peak', 'max'),
                                             ('Best Scored','scored')],
                                    style={'description_width': 'initial'},  layout=widgets.Layout(height='auto', width='auto'), disabled=False)

    process_hvsr_call_prefix = widgets.HTML(value='<style>p {word-wrap: break-word}</style> <p>' + 'process_hvsr' + '</p>', 
                                       layout=widgets.Layout(width='fill', justify_content='flex-end', align_content='flex-start'))
    process_hvsr_call = widgets.HTML(value='()')
    process_hvsr_call_hbox = widgets.HBox([process_hvsr_call_prefix, process_hvsr_call])

    # Update process_hvsr call
    def update_process_hvsr_call():
        ph_kwargs = get_process_hvsr_kwargs()
        ph_text = f"""(hvsr_data=hvsr_data, 
                        method={ph_kwargs['method']}, 
                        smooth={ph_kwargs['smooth']}, 
                        freq_smooth={ph_kwargs['freq_smooth']}, 
                        f_smooth_width={ph_kwargs['f_smooth_width']}, 
                        resample={ph_kwargs['resample']}, 
                        outlier_curve_rmse_percentile={ph_kwargs['outlier_curve_rmse_percentile']}, 
                        verbose={verbose_check.value})"""
        process_hvsr_call.value='<style>p {word-wrap: break-word}</style> <p>' + ph_text + '</p>'
    update_process_hvsr_call()

    check_peaks_call_prefix = widgets.HTML(value='<style>p {word-wrap: break-word}</style> <p>'+'check_peaks' + '</p>',
                                       layout=widgets.Layout(width='fill', justify_content='flex-end',align_content='flex-start'))
    check_peaks_call = widgets.HTML(value='()')
    check_peaks_call_hbox = widgets.HBox([check_peaks_call_prefix, check_peaks_call])

    # Update process_hvsr call
    def update_check_peaks_call():
        cp_kwargs = get_check_peaks_kwargs()
        cp_text = f"""(hvsr_data=hvsr_data, 
                        hvsr_band={cp_kwargs['hvsr_band']}, 
                        peak_selection={cp_kwargs['peak_selection']}, 
                        peak_freq_range={cp_kwargs['peak_freq_range']}, 
                        verbose={verbose_check.value})"""
        check_peaks_call.value='<style>p {word-wrap: break-word}</style> <p>' + cp_text + '</p>'
    update_check_peaks_call()

    freq_smooth_hbox = widgets.HBox([freq_smoothing, freq_smooth_width])
    resample_hbox = widgets.HBox([resample_hv_curve_bool, resample_hv_curve])
    smooth_hbox = widgets.HBox([smooth_hv_curve_bool, smooth_hv_curve])
    
    # Set up vbox for hvsr_settings subtab
    hvsr_settings_tab = widgets.VBox([h_combine_meth,
                                    freq_smooth_hbox,
                                    resample_hbox,
                                    smooth_hbox,
                                    hvsr_band_hbox_hvsrSet,
                                    peak_freq_range_hbox_hvsrSet,
                                    peak_selection_type,
                                    process_hvsr_call_hbox,
                                    check_peaks_call_hbox])

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
    show_best_peak_comp = widgets.Checkbox(value=True, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})
    show_best_peak_spec = widgets.Checkbox(value=False, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})

    annotate_peak_label = widgets.Label(value='Annotate Best Peak', layout=widgets.Layout(height='auto', width='auto', justify_content='flex-end', align_items='center'))
    ann_best_peak_hv = widgets.Checkbox(value=True, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
                                   style={'description_width': 'initial'})
    ann_best_peak_comp = widgets.Checkbox(value=False, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
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
    show_ind_peaks_spec = widgets.Checkbox(value=False, layout=widgets.Layout(height='auto', width='auto', justify_content='center', align_items='center'),
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

    plot_hvsr_call = widgets.Label(value=f"Plot String: '{_get_default(sprit_hvsr.get_report, 'plot_type')}'")
    def update_plot_string():
        plot_hvsr_text = f"""Plot String: {get_get_report_kwargs()['plot_type']}"""
        plot_hvsr_call.value = plot_hvsr_text
    update_plot_string()

    update_plot_button = widgets.Button(description='Update Plot',button_style='info',layout=widgets.Layout(height='auto', width='auto'))
    def manually_update_results_fig(change):
        plot_string = get_get_report_kwargs()['plot_type']
        update_results_fig(hvsr_results, plot_string)
        sprit_tabs.selected_index = 4

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
    plot_settings_tab[4, 10:15] = combine_hv_comp

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
    plot_settings_tab[9, 15:] = show_ind_peaks_spec
   
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

    plot_settings_tab[17, :18] = plot_hvsr_call
    plot_settings_tab[17, 18:] = update_plot_button
    update_plot_button.on_click(manually_update_results_fig)

    # Place everything in Settings Tab
    settings_subtabs = widgets.Tab([ppsd_settings_tab, hvsr_settings_tab, outlier_settings_tab, plot_settings_tab])
    settings_tab = widgets.VBox(children=[settings_subtabs, settings_progress_hbox])
    settings_subtabs.set_title(0, "PPSD Settings")
    settings_subtabs.set_title(1, "HVSR Settings")
    settings_subtabs.set_title(2, "Outlier Settings")
    settings_subtabs.set_title(3, "Plot Settings")

    # LOG TAB - not currently using
    log_tab = widgets.VBox(children=[log_textArea])
    #log_textArea = widgets.Textarea(value="SESSION LOG", disabled=True, layout={'height': '99%','width': '99%', 'overflow': 'scroll'})

    # RESULTS TAB
    # PLOT SUBTAB
    global results_subp
    results_subp = subplots.make_subplots(rows=3, cols=1, horizontal_spacing=0.01, vertical_spacing=0.01, row_heights=[2,1,1])
    results_fig = go.FigureWidget(results_subp)
    global results_graph_widget
    results_graph_widget = widgets.Output()   

    with results_graph_widget:
        display(results_fig)

    global printed_results_textArea
    printed_results_textArea = widgets.Textarea(value="RESULTS", disabled=True, layout={'height': '500px','width': '99%', 'overflow': 'scroll'})

    global results_table
    initialTableCols=['SiteName', 'Acq_Date', 'Longitude', 'Latitude', 'Elevation',
                      'PeakFrequency', 'WindowLengthFreq.', 'SignificantCycles', 'LowCurveStDevOverTime', 
                      'PeakProminenceBelow', 'PeakProminenceAbove', 'PeakAmpClarity', 
                      'FreqStability', 'PeakStability_FreqStD', 'PeakStability_AmpStD', 'PeakPasses']
    results_table = widgets.HTML(value=pd.DataFrame(columns=initialTableCols).to_html())

    # A text box labeled Data Filepath
    export_results_table_filepath = widgets.Text(description='Export Filepath:',
                                    placeholder='', value='',
                                    style={'description_width': 'initial'},layout=widgets.Layout(width='90%'))

    export_results_table_read_button = widgets.Button(description='', icon='fa-file-import',button_style='success',
                                            layout=widgets.Layout(width='10%'))
    export_results_table_browse_button = widgets.Button(description='Export Table',
                                            layout=widgets.Layout(width='10%'))
    def export_results_table(button):
        try:
            if button.value == 'Export Table':
                root = tk.Tk()
                root.wm_attributes('-topmost', True)
                root.withdraw()
                export_results_table_filepath.value = str(filedialog.asksaveasfilename(defaultextension='.csv', title='Save CSV Report'))
                root.destroy()
        except Exception as e:
            print(e)
            export_results_table_browse_button.disabled=True
            export_results_table_browse_button.description='Use Text Field'

        out_path = export_results_table_filepath.value
        sprit_hvsr.get_report(hvsr_results, report_format='csv', export_path=out_path,
                              csv_overwrite_opt='overwrite')

    export_results_table_browse_button.on_click(export_results_table)
    export_results_table_read_button.on_click(export_results_table)

    results_table_export_hbox = widgets.HBox([export_results_table_filepath, export_results_table_read_button, export_results_table_browse_button])
    results_table_vbox = widgets.VBox([results_table, results_table_export_hbox])
    global results_tab
    results_subtabs = widgets.Tab([results_graph_widget, printed_results_textArea, results_table_vbox])
    results_tab = widgets.VBox(children=[results_subtabs])
    results_subtabs.set_title(0, "Plot")
    results_subtabs.set_title(1, "Peak Tests")
    results_subtabs.set_title(2, "Peak Table")

    widget_param_dict = {
        'fetch_data': 
            {'source': data_source_type,
            'trim_dir': trim_directory,
            'export_format': trim_export_dropdown,
            'detrend': detrend_type_dropdown,
            'detrend_options': detrend_options,
            'verbose': verbose_check},
        'remove_noise': 
            {
            'sat_percent': max_saturation_pct,
            'noise_percent': max_window_pct,
            'sta': sta,
            'lta': lta,
            'stalta_thresh': [stalta_thresh_low, stalta_thresh_hi],
            'warmup_time': warmup_time,
            'cooldown_time': cooldown_time,
            'min_win_size': noisy_window_length,
            'remove_raw_noise': raw_data_remove_check,
            'verbose': verbose_check},
        'generate_psds': 
            {'verbose': verbose_check,
             'skip_on_gaps':skip_on_gaps, 
             'db_bins':[db_bins_min, db_bins_max, db_bins_step],
             'ppsd_length':ppsd_length, 
             'overlap':overlap_pct, 
             'special_handling':special_handling_dropdown, 
             'period_smoothing_width_octaves':period_smoothing_width, 
             'period_step_octaves':period_step_octave, 
             'period_limits':[hvsr_band_min_box, hvsr_band_max_box]},
        'process_hvsr': 
            {'method': h_combine_meth,
            'smooth': smooth_hv_curve,
            'freq_smooth': freq_smoothing,
            'f_smooth_width': freq_smooth_width,
            'resample': resample_hv_curve,
            'verbose': verbose_check},
        'remove_outlier_curves': 
            {'rmse_thresh': rmse_thresh,
            'use_percentile': rmse_pctile_check,
            'use_hv_curve': use_hv_curve_rmse,
            'verbose': verbose_check},
        'check_peaks': 
            {'hvsr_band': [hvsr_band_min_box, hvsr_band_max_box],
            'peak_freq_range': [peak_freq_range_min_box, peak_freq_range_max_box],
            'verbose': verbose_check},
        'get_report': 
            {
            'export_path': export_results_table_filepath,
            'verbose': verbose_check}}

    # SPRIT WIDGET
    # Add all  a tab and add the grid to it
    global sprit_tabs
    sprit_tabs = widgets.Tab([input_tab, preview_tab, settings_tab, log_tab, results_tab])
    sprit_tabs.set_title(0, "Input")
    sprit_tabs.set_title(1, "Preview")
    sprit_tabs.set_title(2, "Settings")
    sprit_tabs.set_title(3, "Log")
    sprit_tabs.set_title(4, "Results")

    sprit_title = widgets.Label(value='SPRIT', layout=widgets.Layout(width='150px'))
    sprit_subtitle = widgets.Label(value='Tools for ambient siesmic noise analysis using HVSR',
                                   layout=widgets.Layout(flex='1', justify_content='flex-start', align_content='flex-end'))

    # Function to open a link
    def open_dist(button):
        link = 'https://pypi.org/project/sprit/'
        webbrowser.open_new_tab(link)

    def open_repo(button):
        link = 'https://github.com/RJbalikian/SPRIT-HVSR'
        webbrowser.open_new_tab(link)

    def open_docs(button):
        link = 'https://rjbalikian.github.io/SPRIT-HVSR/main.html'
        webbrowser.open_new_tab(link)

    sourcebutton = widgets.Button(description="PyPI",
                                layout=widgets.Layout(width='4%', justify_content='flex-end',align_content='flex-end'))
    repobutton = widgets.Button(description="Repo",
                                layout=widgets.Layout(width='4%', justify_content='flex-end',align_content='flex-end'))
    docsbutton = widgets.Button(description="Docs",
                                layout=widgets.Layout(width='8%', justify_content='flex-end',align_content='flex-end'))

    # Attach the open_link function to the button's on_click event
    sourcebutton.on_click(open_dist)
    repobutton.on_click(open_repo)
    docsbutton.on_click(open_docs)

    titlehbox = widgets.HBox([sprit_title, sprit_subtitle, repobutton, sourcebutton, docsbutton],
                            layout = widgets.Layout(align_content='space-between'))
    
    title_style = {
        'font_family': 'Arial, sans-serif',
        'font_size': '36px',
        'font_weight': 'bold',
        'color': 'black'
    }

    # Apply the style to the label
    sprit_title.style = title_style

    sprit_widget = widgets.VBox([titlehbox, sprit_tabs])

    def observe_children(widget, callback):
        if hasattr(widget, 'children'):
            for child in widget.children:
                child.observe(callback)
                observe_children(child, callback)

    def any_update(change):
        update_input_param_call()
        update_fetch_data_call()
        update_remove_noise_call()
        update_generate_ppsd_call()
        update_process_hvsr_call()
        update_remove_outlier_curve_call()
        update_check_peaks_call()
        update_plot_string()

    observe_children(sprit_tabs, any_update)

    # Display the tab
    display(sprit_widget)
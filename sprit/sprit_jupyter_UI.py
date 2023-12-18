"""Functions to create jupyter notebook widget UI
"""

import datetime
from zoneinfo import available_timezones

import ipywidgets as widgets
from IPython.display import display
import plotly.graph_objs as go

OBSPY_FORMATS =  ['AH', 'ALSEP_PSE', 'ALSEP_WTH', 'ALSEP_WTN', 'CSS', 'DMX', 'GCF', 'GSE1', 'GSE2', 'KINEMETRICS_EVT', 'KNET', 'MSEED', 'NNSA_KB_CORE', 'PDAS', 'PICKLE', 'Q', 'REFTEK130', 'RG16', 'SAC', 'SACXY', 'SEG2', 'SEGY', 'SEISAN', 'SH_ASC', 'SLIST', 'SU', 'TSPAIR', 'WAV', 'WIN', 'Y']


def create_jupyter_ui():

    ui_width = 20
    ui_height= 12
    # INPUT TAB
    # Radio button labelled Data Source Type with options: "File" "Raw" "Batch" "Directory"
    data_source_type = widgets.Dropdown(options=[('File', 'file'), ('Raw', 'raw'), ('Batch', 'batch'), ('Directory', 'dir')],
                                            description='Data Source type:',
                                            value='file',orientation='horizontal', 
                                            style={'description_width': 'initial'},
                                            layout=widgets.Layout(height='auto', width='auto'))

    # A text box labeled Data Filepath
    data_filepath = widgets.Text(description='Data Filepath:',
                                 placeholder='sample',
                                 style={'description_width': 'initial'},
                                 layout=widgets.Layout(height='auto', width='auto'))

    # A button next to it labeled "Browse"
    browse_data_button = widgets.FileUpload(accept='', description='Browse',
                                            multiple=True, layout=widgets.Layout(height='auto', width='auto'))
    
    # A text box labeled Metadata Filepath
    metadata_filepath = widgets.Text(description='Metadata Filepath:',
                                     style={'description_width': 'initial'},
                                     layout=widgets.Layout(height='auto', width='auto'))

    # A button next to it labeled "Browse"
    browse_metadata_button = widgets.FileUpload(accept='', description='Browse',
                                            multiple=False, layout=widgets.Layout(height='auto', width='auto'))

    # Dropdown labeled "Instrument" with options "Raspberry Shake", "Tromino", "Other"
    instrument_dropdown = widgets.Dropdown(options=['Raspberry Shake', 'Tromino', 'Other'],
                                        style={'description_width': 'initial'},
                                        description='Instrument:',layout=widgets.Layout(height='auto', width='auto'))

    network_textbox = widgets.Text(description='Network:',
                                   placeholder='AM',
                                   value='AM',layout=widgets.Layout(height='auto', width='auto'))

    station_textbox = widgets.Text(description='Station:',
                                   placeholder='RAC84',style={'description_width': 'initial'},
                                   value='RAC84',layout=widgets.Layout(height='auto', width='auto'))

    location_textbox = widgets.Text(description='Location:',
                                   placeholder='00',
                                   value='00',layout=widgets.Layout(height='auto', width='auto'))

    z_channel_textbox = widgets.Text(description='Z Channel:',
                                   placeholder='EHZ',
                                   value='EHZ',layout=widgets.Layout(height='auto', width='auto'))

    e_channel_textbox = widgets.Text(description='E Channel:',
                                   placeholder='EHE',
                                   value='EHE',layout=widgets.Layout(height='auto', width='auto'))

    n_channel_textbox = widgets.Text(description='N Channel:',
                                   placeholder='EHN',
                                   value='EHN',layout=widgets.Layout(height='auto', width='auto'))

    # Date Picker labelled "Acquisition Date"
    acquisition_date_picker = widgets.DatePicker(description='Acq.Date:',
                                            placeholder=datetime.datetime.today().date(),
                                            style={'description_width': 'initial'},
                                            value=datetime.datetime.today().date(),layout=widgets.Layout(height='auto', width='auto'))
 
    # Label that shows the Date currently selected in the Date Picker
    acquisition_doy = widgets.FloatText(description='DOY',
                                               style={'description_width': 'initial'},
                                               placeholder=f"{acquisition_date_picker.value.timetuple().tm_yday}",
                                               value=f"{acquisition_date_picker.value.timetuple().tm_yday}",
                                               layout=widgets.Layout(height='auto', width='auto'))

    # Time selector (hour and minute) labelled "Start Time".
    start_time_picker = widgets.TimePicker(description='Start Time:',
                                           placeholder=datetime.time(0,0,0),
                                           value=datetime.time(0,0,0),
                                           style={'description_width': 'initial'},
                                           layout=widgets.Layout(height='auto', width='auto'))

    # Time selector (hour and minute) labelled "End Time". Same as Start Time otherwise.
    end_time_picker = widgets.TimePicker(description='End Time:',
                                        placeholder=datetime.time(23,59),
                                        value=datetime.time(23,59),
                                        style={'description_width': 'initial'},
                                        layout=widgets.Layout(height='auto', width='auto'))

    tzlist = list(available_timezones())
    tzlist.sort()
    tzlist.remove('UTC')
    tzlist.remove('US/Central')
    tzlist.insert(0, 'US/Central')
    tzlist.insert(0, 'UTC')
    # A dropdown list with all the items from zoneinfo.available_timezones(), default 'UTC'
    time_zone_dropdown = widgets.Dropdown(options=tzlist,value='UTC',style={'description_width': 'initial'},
                                          description='Time Zone:',layout=widgets.Layout(height='auto', width='fill'))

    # Separate textboxes for each of the following labels: "xcoord" ,"ycoord", "zcoord", "Input CRS", "Output CRS", "Elevation Unit", "Network", "Station", "Location", "Z Channel", "H1 Channel", "H2 Channel", "HVSR Band", "Peak Freq. Range"
    xcoord_textbox = widgets.FloatText(description='xcoord:',style={'description_width': 'initial'},
                                       layout=widgets.Layout(height='auto', width='auto'))

    ycoord_textbox = widgets.FloatText(description='ycoord:',style={'description_width': 'initial'},
                                       layout=widgets.Layout(height='auto', width='auto'))

    zcoord_textbox = widgets.FloatText(description='zcoord:',style={'description_width': 'initial'},
                                       layout=widgets.Layout(height='auto', width='auto'))

    elevation_unit_textbox = widgets.Dropdown(options=[('Feet', 'feet'), ('Meters', 'meters')],
                                                value='meters',
                                                description='Z Unit:',style={'description_width': 'initial'},
                                                layout=widgets.Layout(height='auto', width='auto'))

    input_crs_textbox = widgets.Text(description='Input CRS:',style={'description_width': 'initial'},
                                     layout=widgets.Layout(height='auto', width='auto'),
                                      placholder='EPSG:4326',value='EPSG:4326')

    output_crs_textbox = widgets.Text(description='Output CRS:',style={'description_width': 'initial'},
                                      layout=widgets.Layout(height='auto', width='auto'),
                                      placholder='EPSG:4326',value='EPSG:4326')


    hvsr_band_min_box = widgets.FloatText(description='HVSR Band:', style={'description_width': 'initial'}, placeholder=0.4, value=0.4,layout=widgets.Layout(height='auto', width='auto'))
    hvsr_band_max_box = widgets.FloatText(placeholder=40, value=40,layout=widgets.Layout(height='auto', width='auto'))
    hvsr_band_hbox = widgets.HBox([hvsr_band_min_box, hvsr_band_max_box],layout=widgets.Layout(height='auto', width='auto'))

    peak_freq_range_min_box = widgets.FloatText(description='Peak Freq. Range:',  style={'description_width': 'initial'},placeholder=0.4, value=0.4,layout=widgets.Layout(height='auto', width='auto'))
    peak_freq_range_max_box = widgets.FloatText(placeholder=40, value=40,layout=widgets.Layout(height='auto', width='auto'))
    peak_freq_range_hbox = widgets.HBox([peak_freq_range_min_box, peak_freq_range_max_box],layout=widgets.Layout(height='auto', width='auto'))

    data_format_dropdown = widgets.Dropdown(
            options=OBSPY_FORMATS,
            value='MSEED',
            description='Data Formats:', style={'description_width': 'initial'}, layout=widgets.Layout(height='auto', width='auto'))
            
    # A radio selector labeled "Detrend type" with "Spline", "Polynomial", or "None"
    detrend_type_dropdown = widgets.Dropdown(options=['Spline', 'Polynomial', 'None'],
                            description='Detrend type:', style={'description_width': 'initial'}, layout=widgets.Layout(height='auto', width='auto'))
                            
    # A text label with "input_params()"
    input_params_call =  widgets.Label(value='input_params():', style={'description_width': 'initial'}, layout=widgets.Layout(height='auto', width='auto'))

        # A text label with "fetch_data()"
    fetch_data_call = widgets.Label(value='fetch_data():', style={'description_width': 'initial'}, layout=widgets.Layout(height='auto', width='auto'))


    # A progress bar
    progress_bar = widgets.FloatProgress(value=0.0,min=0.0,max=1.0,
                                    bar_style='info',
                                    orientation='horizontal',layout=widgets.Layout(height='auto', width='auto'))

    # A dark yellow button labeled "Read Data"
    read_data_button = widgets.Button(description='Read Data',
                                    button_style='warning',layout=widgets.Layout(height='auto', width='auto'))

    # A forest green button labeled "Process HVSR"
    process_hvsr_button = widgets.Button(description='Run',
                                         button_style='success',layout=widgets.Layout(height='auto', width='auto'))


    
    # Create a 2x2 grid and add the buttons to it
    input_tab = widgets.GridspecLayout(ui_height, ui_width)
    input_tab[0, 10:15] = data_source_type
    input_tab[0, 15:] = instrument_dropdown

    input_tab[1, :18] = data_filepath
    input_tab[1, 18:] = browse_data_button

    input_tab[2, :18] = metadata_filepath
    input_tab[2, 18:] = browse_metadata_button

    input_tab[3, :4] = network_textbox
    input_tab[3, 4:8] = station_textbox
    input_tab[3, 8:11] = location_textbox
    input_tab[3, 11:14] = z_channel_textbox
    input_tab[3, 14:17] = e_channel_textbox
    input_tab[3, 17:] = n_channel_textbox

    input_tab[5, :4] = acquisition_date_picker
    input_tab[5, 4:6] = acquisition_doy
    input_tab[5, 9:13]= start_time_picker
    input_tab[5, 13:17]= end_time_picker
    input_tab[5, 17:] = time_zone_dropdown

    input_tab[6, :4] = xcoord_textbox
    input_tab[6, 4:8] = ycoord_textbox
    input_tab[6, 8:11] = zcoord_textbox
    input_tab[6, 11:14] = elevation_unit_textbox
    input_tab[6, 14:17] = input_crs_textbox
    input_tab[6, 17:20] = output_crs_textbox

    input_tab[7, :10] = hvsr_band_hbox
    input_tab[7, 10:] = peak_freq_range_hbox

    input_tab[8, :10] = data_format_dropdown
    input_tab[8, 10:] = detrend_type_dropdown

    input_tab[9, :] = input_params_call
    input_tab[10, :] = fetch_data_call

    input_tab[11, :17] = progress_bar
    input_tab[11, 17:19] = read_data_button
    input_tab[11, 19:] = process_hvsr_button

    # PREVIEW TAB
    preview_graph_tab = widgets.GridspecLayout(ui_height, ui_width)
    preview_noise_tab = widgets.GridspecLayout(ui_height, ui_width)
    preview_tab = widgets.Tab([preview_graph_tab, preview_noise_tab])
    preview_tab.set_title(0, "Data Preview")
    preview_tab.set_title(1, "Noise Removal")

    preview_fig = go.FigureWidget()
    preview_graph_widget = widgets.Output()
    preview_graph_tab[:,:]=preview_graph_widget
    with preview_graph_widget:
        display(preview_fig)

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
    remove_noise_call = widgets.Label(value=f"removes_noise()")

    #progress bar (same as above)

    #Update noise windows
    update_noise_windows_button = widgets.Button(description='Update Noise Windows',button_style='info',layout=widgets.Layout(height='auto', width='auto'))

    #Run (same as above)

    # Add it all in
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

    # SETTINGS TAB
    settings_tab = widgets.GridspecLayout(ui_height, ui_width)

    # LOG TAB
    log_tab = widgets.GridspecLayout(ui_height, ui_width)

    # RESULTS TAB
    results_tab = widgets.GridspecLayout(ui_height, ui_width)

    # SPRIT WIDGET
    # Add all  a tab and add the grid to it
    sprit_widget = widgets.Tab([input_tab, preview_tab, settings_tab, log_tab, results_tab])
    sprit_widget.set_title(0, "Input")
    sprit_widget.set_title(1, "Preview")
    sprit_widget.set_title(2, "Settings")
    sprit_widget.set_title(3, "Log")
    sprit_widget.set_title(4, "Results")

    # Display the tab
    display(sprit_widget)

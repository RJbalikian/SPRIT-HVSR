"""Functions to create jupyter notebook widget UI
"""

import datetime
from zoneinfo import available_timezones

import ipywidgets as widgets
from IPython.display import display
import numpy as np
import plotly.graph_objs as go
import plotly
from scipy import signal

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
    preview_graph_tab = widgets.GridspecLayout(ui_height-1, ui_width)
    preview_noise_tab = widgets.GridspecLayout(ui_height-1, ui_width)
    preview_tab = widgets.Tab([preview_graph_tab, preview_noise_tab])
    preview_tab.set_title(0, "Data Preview")
    preview_tab.set_title(1, "Noise Removal")

    preview_fig = go.FigureWidget()
    preview_graph_widget = widgets.Output()

    preview_fig2 = plotly.subplots.make_subplots(rows=10, cols=1, shared_xaxes=True)
    

    preview_graph_tab[:,:]=preview_graph_widget
    with preview_graph_widget:
        display(preview_fig)

    def update_preview_fig(hvsr_data, preview_fig):
        stream_z = hvsr_data['stream'].select(component='Z') #np.ma.masked_array

        # Get iso_times
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

        f, t, Sxx = signal.spectrogram(x=stream_z[0].data, fs=stream_z[0].stats.sampling_rate, mode='magnitude')
        axisTimes = []
        for tpass in t:
            axisTimes.append((dt_times[0]+datetime.timedelta(seconds=tpass)).isoformat())

        preview_fig.add_trace(px.imshow(Sxx, x=axisTimes, y=f,  range_color=[0,2500],
                        labels={'x':'Time [UTC]', 'y':'Frequency [Hz]', 'color':'Intensity'}).data[0])

        preview_fig.update_yaxes(type='log')
        preview_fig.update_coloraxes(cmin=0, cmax=3000, colorscale='turbo')
        
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

    preview_noise_tab[6,:] = auto_remove_check
    preview_noise_tab[7,:] = raw_data_remove_check

    preview_noise_tab[9,:] = remove_noise_call

    preview_noise_tab[10,:15] = progress_bar_preview
    preview_noise_tab[10,15:19] = update_noise_windows_button
    preview_noise_tab[10,19] = process_hvsr_button_preview

    # SETTINGS TAB
    ppsd_settings_tab = widgets.GridspecLayout(ui_height-1, ui_width)
    hvsr_settings_tab = widgets.GridspecLayout(ui_height-1, ui_width)
    plot_settings_tab = widgets.GridspecLayout(18, ui_width)
    settings_tab = widgets.Tab([ppsd_settings_tab, hvsr_settings_tab, plot_settings_tab])
    settings_tab.set_title(0, "PPSD Settings")
    settings_tab.set_title(1, "HVSR Settings")
    settings_tab.set_title(2, "Plot Settings")

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
    period_limits_min = widgets.Text(description='Min. Period Limit', style={'description_width': 'initial'},
                                    placeholder='None', value=None, layout=widgets.Layout(height='auto', width='auto'), disabled=False)
    period_limits_max = widgets.Text(description='Max. Period Limit', style={'description_width': 'initial'},
                                    placeholder='None', value=None, layout=widgets.Layout(height='auto', width='auto'), disabled=False)
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
    ppsd_settings_tab[5, 5:8] = period_limits_max
    ppsd_settings_tab[5, 5:8] = period_smoothing_width

    ppsd_settings_tab[6, 0:8] = special_handling_dropdown

    ppsd_settings_tab[7:9, :] = generate_ppsd_call
    ppsd_settings_tab[9:11, :] = obspy_ppsd_call

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

    hvsr_settings_tab[5, 1:] = hvsr_band_hbox_hvsrSet

    hvsr_settings_tab[6, 1:] = peak_freq_range_hbox_hvsrSet

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
    results_tab = widgets.GridspecLayout(ui_height, ui_width)

    results_fig = go.FigureWidget()
    results_graph_widget = widgets.Output()

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

    # Display the tab
    display(sprit_widget)

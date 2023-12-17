"""Functions to create jupyter notebook widget UI
"""

import datetime
from zoneinfo import available_timezones

import ipywidgets as widgets
from IPython.display import display

def create_jupyter_ui():

    # INPUT TAB
    # Radio button labelled Data Source Type with options: "File" "Raw" "Batch" "Directory"
    data_source_type = widgets.RadioButtons(options=['File', 'Raw', 'Batch', 'Directory'],
                                            description='Data Source Type:',
                                            value='File',orientation='horizontal', 
                                            layout=widgets.Layout(height='auto', width='auto'))

    # A text box labeled Data Filepath
    data_filepath = widgets.Text(description='Data Filepath:',
                                 placeholder='sample',layout=widgets.Layout(height='auto', width='auto'))

    # A button next to it labeled "Browse"
    browse_data_button = widgets.Button(description='Browse',layout=widgets.Layout(height='auto', width='auto'))

    # A text box labeled Metadata Filepath
    metadata_filepath = widgets.Text(description='Metadata Filepath:',layout=widgets.Layout(height='auto', width='auto'))

    # A button next to it labeled "Browse"
    browse_metadata_button = widgets.Button(description='Browse',layout=widgets.Layout(height='auto', width='auto'))

    # Dropdown labeled "Instrument" with options "Raspberry Shake", "Tromino", "Other"
    instrument_dropdown = widgets.Dropdown(options=['Raspberry Shake', 'Tromino', 'Other'],
                                        description='Instrument:',layout=widgets.Layout(height='auto', width='auto'))

    # Date Picker labelled "Acquisition Date"
    acquisition_date_picker = widgets.DatePicker(description='Acquisition Date:',
                                            value=datetime.datetime.today().date(),layout=widgets.Layout(height='auto', width='auto'))

    # Label that shows the Date of Year currently selected in the Date Picker
    acquisition_date_label = widgets.FloatText(description='Day of Year', 
                                               placeholder=f"{acquisition_date_picker.value.timetuple().tm_yday}",
                                               value=f"{acquisition_date_picker.value.timetuple().tm_yday}",
                                               layout=widgets.Layout(height='auto', width='auto'))


    # Time selector (hour and minute) labelled "Start Time". This could two separate boxes or if there is a native way to do this.
    start_time_picker = widgets.TimePicker(description='Start Time:',layout=widgets.Layout(height='auto', width='auto'))

    # Time selector (hour and minute) labelled "End Time". Same as Start Time otherwise.
    end_time_picker = widgets.TimePicker(description='End Time:',layout=widgets.Layout(height='auto', width='auto'))

    # A dropdown list with all the items from zoneinfo.available_timezones(), default 'UTC'
    time_zone_dropdown = widgets.Dropdown(options=available_timezones(),value='UTC',description='Time Zone:',layout=widgets.Layout(height='auto', width='auto'))

    # Separate textboxes for each of the following labels: "xcoord" ,"ycoord", "zcoord", "Input CRS", "Output CRS", "Elevation Unit", "Network", "Station", "Location", "Z Channel", "H1 Channel", "H2 Channel", "HVSR Band", "Peak Freq. Range"
    xcoord_textbox = widgets.FloatText(description='xcoord:',layout=widgets.Layout(height='auto', width='auto'))

    ycoord_textbox = widgets.FloatText(description='ycoord:',layout=widgets.Layout(height='auto', width='auto'))

    zcoord_textbox = widgets.FloatText(description='zcoord:',layout=widgets.Layout(height='auto', width='auto'))

    input_crs_textbox = widgets.Text(description='Input CRS:',layout=widgets.Layout(height='auto', width='auto'))

    output_crs_textbox = widgets.Text(description='Output CRS:',layout=widgets.Layout(height='auto', width='auto'))

    elevation_unit_textbox = widgets.FloatText(description='Elevation Unit:',layout=widgets.Layout(height='auto', width='auto'))

    network_textbox = widgets.Text(description='Network:',
                                   placeholder='AM',
                                   value='AM',layout=widgets.Layout(height='auto', width='auto'))

    station_textbox = widgets.Text(description='Station:',
                                   placeholder='RAC84',
                                   value='RAC84',layout=widgets.Layout(height='auto', width='auto'))

    location_textbox = widgets.Text(description='Location:',
                                   placeholder='00',
                                   value='00',layout=widgets.Layout(height='auto', width='auto'))

    z_channel_textbox = widgets.Text(description='Z Channel:',
                                   placeholder='EHZ',
                                   value='EHZ',layout=widgets.Layout(height='auto', width='auto'))

    h1_channel_textbox = widgets.Text(description='H1 Channel:',
                                   placeholder='EHE',
                                   value='EHE',layout=widgets.Layout(height='auto', width='auto'))

    h2_channel_textbox = widgets.Text(description='H2 Channel:',
                                   placeholder='EHN',
                                   value='EHN',layout=widgets.Layout(height='auto', width='auto'))

    hvsr_band_min_box = widgets.FloatText(description='HVSR Band:', placeholder=0.4, value=0.4,layout=widgets.Layout(height='auto', width='auto'))
    hvsr_band_max_box = widgets.FloatText(placeholder=40, value=40,layout=widgets.Layout(height='auto', width='auto'))
    hvsr_band_hbox = widgets.HBox([hvsr_band_min_box, hvsr_band_max_box],layout=widgets.Layout(height='auto', width='auto'))

    peak_freq_range_min_box = widgets.FloatText(description='Peak Freq. Range:', placeholder=0.4, value=0.4,layout=widgets.Layout(height='auto', width='auto'))
    peak_freq_range_max_box = widgets.FloatText(placeholder=40, value=40,layout=widgets.Layout(height='auto', width='auto'))
    peak_freq_range_hbox = widgets.HBox([peak_freq_range_min_box, peak_freq_range_max_box],layout=widgets.Layout(height='auto', width='auto'))

    # A progress bar
    progress_bar = widgets.FloatProgress(value=0.0,min=0.0,max=1.0,
                                    bar_style='info',
                                    orientation='horizontal',layout=widgets.Layout(height='auto', width='auto'))

    # A dark yellow button labeled "Read Data"
    read_data_button = widgets.Button(description='Read Data',
                                    button_style='warning',layout=widgets.Layout(height='auto', width='auto'))

    # A forest green button labeled "Process HVSR"
    process_hvsr_button = widgets.Button(description='Process HVSR',
                                         button_style='success',layout=widgets.Layout(height='auto', width='auto'))

    # Advanced options
    advanced_input_options = widgets.VBox([
        # A dropdown list with all the data formats that Obspy can read
        widgets.Dropdown(
            options=['data format 1', 'data format 2', 'data format 3'],
            description='Data Formats:',layout=widgets.Layout(height='auto', width='auto')),
            
        # A text label with "input_params()"
        widgets.Label(value='input_params():',layout=widgets.Layout(height='auto', width='auto')),

        # A text label with "fetch_data()"
        widgets.Label(value='fetch_data():',layout=widgets.Layout(height='auto', width='auto')),

        # A radio selector labeled "Detrend type" with "Spline", "Polynomial", or "None"
        widgets.RadioButtons(options=['Spline', 'Polynomial', 'None'],
                            description='Detrend type:',layout=widgets.Layout(height='auto', width='auto'))
                            ],layout=widgets.Layout(height='auto', width='auto'))
    
    # Create a 2x2 grid and add the buttons to it
    input_tab = widgets.GridspecLayout(10, 20)
    input_tab[0, 10:] = data_source_type
    input_tab[1, :16] = data_filepath
    input_tab[1, 16:] = browse_data_button
    input_tab[2, :16] = metadata_filepath
    input_tab[2, 16:] = browse_metadata_button    

    # PREVIEW TAB

    # SETTINGS TAB

    # LOG TAB

    # RESULTS TAB

    # SPRIT WIDGET
    # Add all  a tab and add the grid to it
    sprit_widget = widgets.Tab([input_tab])
    sprit_widget.set_title(0, "Input")

    # Display the tab
    display(sprit_widget)

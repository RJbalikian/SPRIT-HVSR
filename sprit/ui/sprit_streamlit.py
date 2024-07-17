import datetime
import inspect
import zoneinfo

import numpy as np
import streamlit as st
import sprit


icon=r"C:\Users\riley\LocalData\Github\SPRIT-HVSR\sprit\resources\icon\sprit_icon_alpha.ico"
icon=":material/ssid_chart:"
aboutStr = """
# About SpRIT
## v1.0.2

SpRIT is developed by Riley Balikian at the Illinois State Geological Survey.

Please visit the following links for any questions:
* [API Documentation](https://sprit.readthedocs.io/en/latest/)
* [Wiki](https://github.com/RJbalikian/SPRIT-HVSR/wiki) 
* [Pypi Repository](https://pypi.org/project/sprit/)

"""

st.set_page_config('SpRIT HVSR',
                   page_icon=icon,
                   layout='wide',
                   menu_items={'Get help': 'https://github.com/RJbalikian/SPRIT-HVSR/wiki',
                                'Report a bug': "https://github.com/RJbalikian/SPRIT-HVSR/issues",
                                'About': aboutStr})

OBSPYFORMATS =  ['AH', 'ALSEP_PSE', 'ALSEP_WTH', 'ALSEP_WTN', 'CSS', 'DMX', 'GCF', 'GSE1', 'GSE2', 'KINEMETRICS_EVT', 'KNET', 'MSEED', 'NNSA_KB_CORE', 'PDAS', 'PICKLE', 'Q', 'REFTEK130', 'RG16', 'SAC', 'SACXY', 'SEG2', 'SEGY', 'SEISAN', 'SH_ASC', 'SLIST', 'SU', 'TSPAIR', 'WAV', 'WIN', 'Y']
bandVals=[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,2,3,4,5,6,7,8,9,10,20,30,40,50,60,70,80,90,100]

def main():
    # Define functions
    @st.experimental_dialog("Update Input Parameters", width='large')
    def open_ip_dialog():
        st.text_input("Site Name", placeholder='HVSR Site')
        st.text_input("Network", placeholder='AM')
        st.text_input("Station", placeholder='RAC84')
        st.text_input("Location", placeholder='00')
        st.text_input("Channels", placeholder='EHZ, EHE, EHN')

        st.date_input('Acquisition Date', format='YYYY-MM-DD')
        st.time_input('Start time', value=datetime.time(0,0,0), step=60)
        st.time_input('End time', value=datetime.time(23, 59, 59), step=60)

        tZoneList=list(zoneinfo.available_timezones())
        tZoneList.sort()
        tZoneList.insert(0, "localtime")
        tZoneList.insert(0, "US/Pacific")
        tZoneList.insert(0, "US/Eastern")
        tZoneList.insert(0, "US/Central")
        tZoneList.insert(0, "UTC")
        st.selectbox('Timezone', options=tZoneList)

        st.select_slider('HVSR Band',  options=bandVals, value=[0.4, 40])
        st.select_slider('Peak Frequency Range',  options=bandVals, value=[0.4, 40])

        st.text_input('X Coordinate', value='0', help='i.e., Longitude or Easting')
        st.text_input('Y Coordinate', value='0', help='i.e., Latitude or Northing')
        st.text_input('Z Coordinate', value='0', help='i.e., Elevation')
        st.selectbox('Z Unit', options=['m', 'ft'], help='i.e., Elevation unit')
        st.text_input('Depth', value='0', help='i.e., Depth of measurement below ground surface (not currently used)')

        st.text_input('CRS of Input Coordinates', value='EPSG:4326', help='Can be EPSG code or anything accepted by pyproj.CRS.from_user_input()')
        st.text_input('CRS for Export', value='EPSG:4326', help='Can be EPSG code or anything accepted by pyproj.CRS.from_user_input()')

        st.text_input('Instrument', value='Raspberry Shake', help='Raspberry Shake and Tromino are currently the only values with special treatment. If a filepath, can use a .inst instrument file (json format)')
        st.text_input('Metadata Filepath', help='Filepath to instrument response file')

    @st.experimental_dialog("Update Parameters to Fetch Data", width='large')
    def open_fd_dialog():
        #source: str = 'file',
        st.text_input('Trim Directory', help='Directory for saving trimmed data')
        st.selectbox('Data format', options=OBSPYFORMATS, index=11)
        st.selectbox('Detrend method', options=['None', 'Simple', 'linear', 'Constant/Demean', 'Polynomial', 'Spline'], index=-1, help='Detrend method use by `type` parameter of obspy.trace.Trace.detrend()')
        st.text_input('Detrend options', value='detrend_order=2', help="Comma separated values with equal sign between key/value of arguments to pass to the **options argument of obspy.trace.Trace.detrend()")

    @st.experimental_dialog("Update Parameters to Generate PPSDs", width='large')
    def open_ppsd_dialog():
        st.toggle('Skip on gaps', value=False, help='Determines whether time segments with gaps should be skipped entirely. Select skip_on_gaps=True for not filling gaps with zeros which might result in some data segments shorter than ppsd_length not used in the PPSD.')
        st.number_input("Minimum Decibel Value", value=-200, step=1)
        st.number_input("Maximum Decibel Value", value=-50, step=1)
        st.number_input("Decibel bin size", value=1.0, step=0.1)
        
        st.number_input('PPSD Length (seconds)', value=30, step=1)
        st.number_input('PPSD Window overlap (%, 0-1)', value=0.5, step=0.01, min_value=0.0, max_value=1.0)
        st.number_input('Period Smoothing Width (octaves)', value=1.0, step=0.1)
        st.number_input('Period Step (octaves)', value=0.125, step=0.005, format="%.3f")
        periodVals=[round(1/x,3) for x in bandVals]
        periodVals.sort()

        st.select_slider('Period Limits (s)', options=periodVals, value=[round(1/40, 3), round(1/0.4, 3)])
        st.selectbox("Special Handling", options=['None', 'Ringlaser', 'Hydrophone'])


    @st.experimental_dialog("Update Parameters to Remove Noise and Outlier Curves", width='large')
    def open_outliernoise_dialog():
        # rmse_thresh=98, 
        # use_percentile=True, 
        # use_hv_curve=False,
        
        # remove_method='auto', 
        # sat_percent=0.995, 
        # noise_percent=0.8, 
        # sta=2, 
        # lta=30, 
        # stalta_thresh=[8, 16], 
        # warmup_time=0, 
        # cooldown_time=0, 
        # min_win_size=1, 
        # remove_raw_noise=False
        pass

    @st.experimental_dialog("Update Parameters to Process HVSR", width='large')
    def open_processHVSR_dialog():
        #peak_selection='max' (or scored)
        #method=3, 
        #smooth=True, 
        #freq_smooth='konno ohmachi', 
        #f_smooth_width=40, 
        #resample=True, 
        #outlier_curve_rmse_percentile=False
        pass

    @st.experimental_dialog("Update Plot Settings", width='large')
    def plot_settings_dialog():
        st.selectbox("Plot Engine", options=['Matplotlib', "Plotly"])
        st.text_input("Plot type (plot string)", value='HVSR p ann C+ p ann Spec p')
        st.multiselect("Charts to show", options=['HVSR', "Components", 'Spectrogram', 'Azimuth'], default=['HVSR', 'Components', "Spectrogram"])
        
        st.header("HVSR Chart", divider='rainbow')
        st.multiselect('Items to plot', options=['Peak Frequency', 'Peak Amplitude', 'Annotation', 'Time windows', "Peaks of Time Windows", 'Standard Deviation',
                                                 'Test 1: Peak > 2x trough below' , "Test 2: Peak > 2x trough above", "Test 3: Peak > 2", "Test 4", "Test 5", "Test 6"],
                                                 default=["Peak Frequency", "Annotation", "Standard Deviation"])

        st.header("Component Chart", divider='rainbow')
        st.multiselect('Items to plot', options=['Peak Frequency', 'Annotation', "Standard Deviation", 'Time windows'],
                                                 default=["Peak Frequency", "Annotation", "Standard Deviation"])
        
        st.header('Spectrogram Chart', divider='rainbow')
        st.multiselect('Items to plot', options=['Peak Frequency', 'Annotation'])


    def open_settings_dialogs(function):
        if hasattr(function, '__name__'):
            funName = function.__name__
        else:
            funName = function
        settingsDialogDict={
            'input_params':open_ip_dialog,
            'fetch_data':open_fd_dialog,
            'generate_ppsds':open_ppsd_dialog,
            'plot_settings':plot_settings_dialog,
            'remove_noise':open_outliernoise_dialog,
            'remove_outlier_curves':open_outliernoise_dialog,
            'process_hvsr':open_processHVSR_dialog,
        }
        settingsDialogDict[funName]()

    top_container = st.sidebar.container()

    # Create top menu
    with top_container:
        spritMenu, setMenu, aboutMenu = st.columns([0.3, 0.45, 0.15])
        with spritMenu:
            with st.popover("SpRIT", use_container_width=True):
                st.write("Read data [not yet supported]")
                st.write("Import instrument settings [not yet supported]")
                st.write("Import processing settings [not yet supported]")
                st.write("Import processing settings [not yet supported]")
                st.write("Export .csv data [not yet supported]")
                st.write("Export .hvsr data [not yet supported]")
                st.write("Export .hvsr data [not yet supported]")

        with setMenu:
            with st.popover("Settings :gear:", use_container_width=True):
                if st.button("Input Parameters", key='ipset'):
                    open_settings_dialogs(sprit.input_params)

                if st.button("Fetch Data Settings", key='fdset'):
                    open_settings_dialogs(sprit.fetch_data)

                if st.button("Remove Noise and Oulier Curve Settings", key='rmnoc'):
                    open_settings_dialogs(sprit.remove_noise)

                if st.button('Generate PPSD Settings', key='gpset'):
                    open_settings_dialogs(sprit.generate_ppsds)

                if st.button('Process HVSR Settings', key='phvsrset'):
                    open_settings_dialogs(sprit.process_hvsr)

                if st.button("Plot Settings", key='plotset'):
                    open_settings_dialogs("plot_settings")


        with aboutMenu:
            with st.popover(":information_source:", use_container_width=True):
                st.markdown(aboutStr)


    # Sidebar content
    st.sidebar.title("SpRIT HVSR")
    st.sidebar.text('No file selected')
    st.sidebar.text_input("Datapath", placeholder='Enter filepath to your data here (or leave blank or use number 1-10 to run with sample datasets)')
    st.sidebar.button(label="Browse")
    st.sidebar.selectbox(label='Source', options=['File', 'Raw', 'Directory', 'Batch'] )
    st.sidebar.button('Read Data')
    st.sidebar.button('Run', type='primary')

    # Main area
    header=st.header('SpRIT HVSR', divider='rainbow')
    dataInfo=st.markdown('No data has been read in yet')
    inputTab, noiseTab, outlierTab, resultsTab = st.tabs(['Input', 'Noise', 'Outliers', 'Results'])
    plotReportTab, strReportTab = resultsTab.tabs(['Plot', 'Report'])

if __name__ == "__main__":
    main()
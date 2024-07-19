import datetime
import inspect
import zoneinfo

import numpy as np
import streamlit as st
import sprit
from obspy import UTCDateTime


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

# SETUP KWARGS

ip_kwargs = {}
fd_kwargs = {}
rn_kwargs = {}
gpppsd_kwargs = {}
phvsr_kwargs = {}
roc_kwargs = {}
cp_kwargs = {}
gr_kwargs = {}
run_kwargs = {}

# Get default values
sigList = [[sprit.input_params, ip_kwargs], [sprit.fetch_data, fd_kwargs],
            [sprit.remove_noise, rn_kwargs], [sprit.generate_ppsds, gpppsd_kwargs], 
            [sprit.process_hvsr, phvsr_kwargs], [sprit.remove_outlier_curves, roc_kwargs],
            [sprit.check_peaks, cp_kwargs], [sprit.get_report, gr_kwargs]]

for fun, kwargs in sigList:
    if len(st.session_state.keys())==0:
        for sig in sigList:
            funSig = inspect.signature(sig[0])
            for arg in funSig.parameters.keys():
                if not (funSig.parameters[arg].default is funSig.parameters[arg].empty):
                    sig[1][arg] = funSig.parameters[arg].default
                    run_kwargs[arg] = funSig.parameters[arg].default
                    st.session_state[arg] = funSig.parameters[arg].default

listItems = ['source', 'tzone', 'elev_unit', 'export_format', 'detrend', 'special_handling', 'peak_selection', 'freq_smooth', 'method']
for arg in st.session_state.keys():
    if arg in listItems:
        arg = [arg]

strItems = ['channels', 'xcoord', 'ycoord', 'elevation']
for arg in st.session_state.keys():
    if arg in strItems:
        if isinstance(st.session_state[arg], (list, tuple)):
            newArg = '['
            for item in st.session_state[arg]:
                newArg = newArg+item+', '
            newArg = newArg[:-2]+']'
            st.session_state[arg] = newArg
        else:
            st.session_state[arg] = str(st.session_state[arg])

dtimeItems=['acq_date', 'starttime', 'endtime']
for arg in st.session_state.keys():
    if arg in dtimeItems:
        if isinstance(st.session_state[arg], str):
            st.session_state[arg] = datetime.datetime.strptime(st.session_state[arg], "%Y-%m-%d")
        elif isinstance(st.session_state[arg], UTCDateTime):
            st.session_state[arg] = st.session_state[arg].datetime

def main():
    # Define functions
    @st.experimental_dialog("Update Input Parameters", width='large')
    def open_ip_dialog():
        st.text_input("Site Name", placeholder='HVSR Site', key='site')
        st.text_input("Network", placeholder='AM', key='network')
        st.text_input("Station", placeholder='RAC84', key='station')
        st.text_input("Location", placeholder='00', key='loc')
        st.text_input("Channels", placeholder='EHZ, EHE, EHN', key='channels')

        st.date_input('Acquisition Date', format='YYYY-MM-DD', key='acq_date')
        st.time_input('Start time', step=60, key='starttime')
        st.time_input('End time', step=60, key='endtime')

        tZoneList=list(zoneinfo.available_timezones())
        tZoneList.sort()
        tZoneList.insert(0, "localtime")
        tZoneList.insert(0, "US/Pacific")
        tZoneList.insert(0, "US/Eastern")
        tZoneList.insert(0, "US/Central")
        tZoneList.insert(0, "UTC")
        st.selectbox('Timezone', options=tZoneList, key='tzone')

        st.select_slider('HVSR Band',  options=bandVals, key='hvsr_band')
        st.select_slider('Peak Frequency Range',  options=bandVals, key='peak_freq_range')

        st.text_input('X Coordinate', help='i.e., Longitude or Easting', key='xcoord')
        st.text_input('Y Coordinate', help='i.e., Latitude or Northing', key='ycoord')
        st.text_input('Z Coordinate', help='i.e., Elevation', key='elevation')
        st.session_state.elev_unit = st.selectbox('Z Unit', options=['m', 'ft'], help='i.e., Elevation unit')
        st.number_input('Depth', help='i.e., Depth of measurement below ground surface (not currently used)', key='depth')

        st.text_input('CRS of Input Coordinates', help='Can be EPSG code or anything accepted by pyproj.CRS.from_user_input()', key='input_crs')
        st.text_input('CRS for Export', help='Can be EPSG code or anything accepted by pyproj.CRS.from_user_input()', key='output_crs')

        st.text_input('Instrument', help='Raspberry Shake and Tromino are currently the only values with special treatment. If a filepath, can use a .inst instrument file (json format)', key='instrument')
        st.text_input('Metadata Filepath', help='Filepath to instrument response file', key='metapath')


    @st.experimental_dialog("Update Parameters to Fetch Data", width='large')
    def open_fd_dialog():
        #source: str = 'file',
        st.text_input('Trim Directory', help='Directory for saving trimmed data', key='trim_dir')
        st.selectbox('Data format', options=OBSPYFORMATS, index=11, key='export_format')
        st.selectbox('Detrend method', options=['None', 'Simple', 'linear', 'Constant/Demean', 'Polynomial', 'Spline'], index=5, help='Detrend method use by `type` parameter of obspy.trace.Trace.detrend()', key='detrend')
        st.text_input('Detrend options', value='detrend_order=2', help="Comma separated values with equal sign between key/value of arguments to pass to the **options argument of obspy.trace.Trace.detrend()", key='detrend_order')


    @st.experimental_dialog("Update Parameters to Generate PPSDs", width='large')
    def open_ppsd_dialog():
        st.toggle('Skip on gaps', value=False, 
                  help='Determines whether time segments with gaps should be skipped entirely. Select skip_on_gaps=True for not filling gaps with zeros which might result in some data segments shorter than ppsd_length not used in the PPSD.',
                  key='skip_on_gaps')
        st.number_input("Minimum Decibel Value", value=-200, step=1, key='max_deb')
        st.number_input("Maximum Decibel Value", value=-50, step=1, key='min_deb')
        st.number_input("Decibel bin size", value=1.0, step=0.1, key='deb_step')
        st.session_state.db_bins = (st.session_state.max_deb, st.session_state.min_deb, st.session_state.deb_step)

        st.number_input('PPSD Length (seconds)', value=30, step=1, key='ppsd_length')
        st.number_input('PPSD Window overlap (%, 0-1)', value=0.5, step=0.01, min_value=0.0, max_value=1.0, key='overlap')
        st.number_input('Period Smoothing Width (octaves)', value=1.0, step=0.1, key='period_smoothing_width_octaves')
        st.number_input('Period Step (octaves)', value=0.125, step=0.005, format="%.3f", key='period_step_octaves')
        periodVals=[round(1/x,3) for x in bandVals]
        periodVals.sort()

        st.select_slider('Period Limits (s)', options=periodVals, value=[round(1/40, 3), round(1/0.4, 3)], key='period_limits')
        st.selectbox("Special Handling", options=['None', 'Ringlaser', 'Hydrophone'], key='special_handling')


    @st.experimental_dialog("Update Parameters to Remove Noise and Outlier Curves", width='large')
    def open_outliernoise_dialog():
        st.number_input("Outlier Threshold", value=98, key='rmse_thresh')
        st.radio('Threshold type', options=['Percentile', 'Value'], key='threshRadio')
        st.session_state.use_percentile = (st.session_state.threshRadio=='Percentile')
        st.radio('Threshold curve', options=['HV Curve', 'Component Curves'], key='curveRadio')
        st.session_state.use_hv_curve = (st.session_state.curveRadio=='HV Curve')

        st.multiselect("Noise Removal Method",
                       options=['Auto', 'Manual', 'Stalta', 'Saturation Threshold', 'Noise Threshold', 'Warmup', 'Cooldown', 'Buffer'], key='remove_method')
        st.number_input('Saturation Percent', min_value=0.0, max_value=1.0, step=0.01, format="%.3f", key='sat_percent')
        st.number_input('Noise Percent', min_value=0.0, max_value=1.0, step=0.1, format="%.2f", key='noise_percent')
        st.number_input('Short Term Average (STA)', step=1.0, format="%.1f", key='sta')
        st.number_input('Long Term Average (LTA)', step=1.0, format="%.1f", key='lta')
        st.select_slider('STA/LTA Thresholds', options=np.arange(0, 101), key='stalta_thresh')
        st.number_input('Warmup Time (seconds)', step=1, key='warmup')
        st.number_input('Cooldown Time (seconds)', step=1, key='cooldown')
        st.number_input('Minimum Window Size (samples)', step=1, key='min_win_size')
        st.toggle("Remove Raw Noise", help='Whether to use the raw input data to remove noise.', key='remove_raw_noise')


    @st.experimental_dialog("Update Parameters to Process HVSR", width='large')
    def open_processHVSR_dialog():
        st.selectbox('Peak Selection Method', options=['Max', 'Scored'], key='peak_selection')
        st.selectbox("Method to combine hoizontal components", 
                     options=['Diffuse Field Assumption', 'Arithmetic Mean', 'Geometric Mean', 'Vector Summation', 'Quadratic Mean', 'Maximum Horizontal Value', 'Azimuth'], 
                     index=2, key='method')
        rList = np.arange(1001).tolist()
        rList[0] = False
        st.selectbox("Curve Smoothing", options=['None', 'Savgoy Filter', 'Konno Ohmachi', "Proportional", "Constant"], index=2, key='freq_smooth')
        st.select_slider("Curve Smoothing Parameter", options=np.arange(1000).tolist(), value=40, key='f_smooth_width')
        st.select_slider("Resample", options=rList, value=1000, key='resample')
        st.select_slider('Outlier Curve Removal', options=rList[:100], key='outlier_curve_rmse_percentile')


    @st.experimental_dialog("Update Plot Settings", width='large')
    def plot_settings_dialog():
        sprit.get_report
        st.selectbox("Plot Engine", options=['Matplotlib', "Plotly"], key='plot_engine')
        st.text_input("Plot type (plot string)", value='HVSR p ann C+ p ann Spec p', key='plot_type')
        st.multiselect("Charts to show", options=['HVSR', "Components", 'Spectrogram', 'Azimuth'], default=['HVSR', 'Components', "Spectrogram"], key='plotPlotStr')
        
        st.header("HVSR Chart", divider='rainbow')
        st.multiselect('Items to plot', options=['Peak Frequency', 'Peak Amplitude', 'Annotation', 'Time windows', "Peaks of Time Windows", 'Standard Deviation',
                                                 'Test 1: Peak > 2x trough below' , "Test 2: Peak > 2x trough above", "Test 3: Peak > 2", "Test 4", "Test 5", "Test 6"],
                                                 default=["Peak Frequency", "Annotation", "Standard Deviation"], key='hvsrPlotStr')

        st.header("Component Chart", divider='rainbow')
        st.multiselect('Items to plot', options=['Peak Frequency', 'Annotation', "Standard Deviation", 'Time windows'],
                                                 default=["Peak Frequency", "Annotation", "Standard Deviation"], key='compPlotStr')
        
        st.header('Spectrogram Chart', divider='rainbow')
        st.multiselect('Items to plot', options=['Peak Frequency', 'Annotation'], str='specPlotStr')

        plotString = ''
        for plot in st.session_state.plotPlotStr:
            if plot=='HVSR':
                plotString=plotString+'HVSR'
                for pc in st.session_state.hvsrPlotStr:
                    plotString = plotString + pc
            if plot=='Components':
                plotString=plotString+' C+'
                for pc in st.session_state.compPlotStr:
                    plotString = plotString + pc
            if plot=='Spectrogram':
                plotString=plotString+' SPEC'
                for pc in st.session_state.specPlotStr:
                    plotString = plotString + pc
            if plot=='Azimuth':
                plotString=plotString+' AZ'

        st.session_state.plot_type = plotString


    def open_settings_dialogs(function):
        if hasattr(function, '__name__'):
            funName = function.__name__
        else:
            funName = function
        print(function.__name__)
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

    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {
                width: 50vw !important; 
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
    st.sidebar.file_uploader('Datapath', accept_multiple_files=True, key='datapath')
    st.session_state.source=st.sidebar.selectbox(label='Source', options=['File', 'Raw', 'Directory', 'Batch'], index=0)

    bottom_container = st.sidebar.container()

    # Create top menu
    with bottom_container:
        resetCol, readCol, runCol = st.columns([0.3, 0.3, 0.4])
        resetCol.button('Reset', disabled=True, use_container_width=True)
        readCol.button('Read', use_container_width=True)
        runCol.button('Run', type='primary', use_container_width=True)

    # Main area
    header=st.header('SpRIT HVSR', divider='rainbow')
    dataInfo=st.markdown('No data has been read in yet')
    inputTab, noiseTab, outlierTab, resultsTab = st.tabs(['Input', 'Noise', 'Outliers', 'Results'])
    plotReportTab, strReportTab = resultsTab.tabs(['Plot', 'Report'])

if __name__ == "__main__":
    main()
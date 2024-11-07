import datetime
import inspect
import pathlib
import sys
import tempfile
import zoneinfo

import numpy as np
import streamlit as st
from obspy import UTCDateTime
from obspy.signal.spectral_estimation import PPSD

try:
    from sprit import sprit_hvsr
except Exception:
    try:
        import sprit_hvsr
    except Exception:
        import sprit

verbose = False

if verbose:
    print('Start of file, session state length: ', len(st.session_state.keys()))
param2print = None# 'period_limits'
def print_param(key=param2print, show_type=True):
    if key is None:
        pass
    elif key in st.session_state.keys():
        print(key, st.session_state[key], 'type:', type(st.session_state[key]))
print_param(param2print)

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
if verbose:
    print('Start setting up page config, session state length: ', len(st.session_state.keys()))
st.set_page_config('SpRIT HVSR',
                page_icon=icon,
                layout='wide',
                menu_items={'Get help': 'https://github.com/RJbalikian/SPRIT-HVSR/wiki',
                                'Report a bug': "https://github.com/RJbalikian/SPRIT-HVSR/issues",
                                'About': aboutStr})

if verbose:
    print('Start setting up constants/variables, session state length: ', len(st.session_state.keys()))
OBSPYFORMATS =  ['AH', 'ALSEP_PSE', 'ALSEP_WTH', 'ALSEP_WTN', 'CSS', 'DMX', 'GCF', 'GSE1', 'GSE2', 'KINEMETRICS_EVT', 'KNET', 'MSEED', 'NNSA_KB_CORE', 'PDAS', 'PICKLE', 'Q', 'REFTEK130', 'RG16', 'SAC', 'SACXY', 'SEG2', 'SEGY', 'SEISAN', 'SH_ASC', 'SLIST', 'SU', 'TSPAIR', 'WAV', 'WIN', 'Y']
bandVals=[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,2,3,4,5,6,7,8,9,10,20,30,40,50,60,70,80,90,100]

# SETUP KWARGS
if verbose:
    print('Start setting up kwargs dicts, session state length: ', len(st.session_state.keys()))

ip_kwargs = {}
fd_kwargs = {}
ca_kwargs = {}
rn_kwargs = {}
gppsd_kwargs = {}
phvsr_kwargs = {}
roc_kwargs = {}
cp_kwargs = {}
gr_kwargs = {}
run_kwargs = {}

if verbose:
    print('Start getting default values, session state length: ', len(st.session_state.keys()))
    print_param(param2print)

# Get default values
sigList = [[sprit_hvsr.input_params, ip_kwargs], [sprit_hvsr.fetch_data, fd_kwargs], [sprit_hvsr.calculate_azimuth, ca_kwargs],
            [sprit_hvsr.remove_noise, rn_kwargs], [sprit_hvsr.generate_psds, gppsd_kwargs], [PPSD, gppsd_kwargs],
            [sprit_hvsr.process_hvsr, phvsr_kwargs], [sprit_hvsr.remove_outlier_curves, roc_kwargs],
            [sprit_hvsr.check_peaks, cp_kwargs], [sprit_hvsr.get_report, gr_kwargs]]


def setup_session_state():
    if "default_params" not in st.session_state.keys():
        # "Splash screen" (only shows at initial startup)
        mainContainerInitText = """
        # SpRIT HVSR
        ## About
        SpRIT HVSR is developed by the Illinois State Geological Survey, part of the Prairie Research Institute at the University of Illinois.
        
        ## Links
        * API Documentation may be accessed [here (hosted by ReadtheDocs)](https://sprit.readthedocs.io/en/latest/) and [here (hosted by Github Pages)](https://rjbalikian.github.io/SPRIT-HVSR/main.html)
        * The Wiki and Tutorials may be accessed [here](https://github.com/RJbalikian/SPRIT-HVSR/wiki)
        * Source Code may be accessed here: [https://github.com/RJbalikian/SPRIT-HVSR](https://github.com/RJbalikian/SPRIT-HVSR)
        * PyPI repository may be accessed [here](https://pypi.org/project/sprit/)

        ## MIT License
        It is licensed under the MIT License:
        > Permission is hereby granted, free of charge, to any person obtaining a copy 
        > of this software and associated documentation files (the "Software"), to deal
        > in the Software without restriction, including without limitation the rights
        > to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        > copies of the Software, and to permit persons to whom the Software is
        > furnished to do so, subject to the following conditions:
        > 
        > The above copyright notice and this permission notice shall be included in all
        > copies or substantial portions of the Software.
        > 
        > THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        > IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        > FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        > AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        > LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        > OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        > SOFTWARE.
        """
        st.markdown(mainContainerInitText, unsafe_allow_html=True)
        if verbose:
            print('Start sig loop, session state length: ', len(st.session_state.keys()))
            print_param(param2print)

        for sig in sigList:
            funSig = inspect.signature(sig[0])
            for arg in funSig.parameters.keys():
                if not (funSig.parameters[arg].default is funSig.parameters[arg].empty):
                    sig[1][arg] = funSig.parameters[arg].default
                    run_kwargs[arg] = funSig.parameters[arg].default

        gppsd_kwargs['ppsd_length'] = run_kwargs['ppsd_length'] = 30
        gppsd_kwargs['skip_on_gaps'] = run_kwargs['skip_on_gaps'] = True
        gppsd_kwargs['period_step_octaves'] = run_kwargs['period_step_octaves'] = 0.03125
        gppsd_kwargs['period_limits'] = run_kwargs['period_limits'] = [1/run_kwargs['hvsr_band'][1], 1/run_kwargs['hvsr_band'][0]]
        if verbose:
            print('Done getting kwargs: ', len(st.session_state.keys()))
            print_param(param2print)

            print('Setting up session state: ', len(st.session_state.keys()))
        #st.session_state["updated_kwargs"] = {}
        for key, value in run_kwargs.items():
            if verbose:
                print(f'Resetting {key} to {value}')
                print_param(param2print)

            #    if key in st.session_state.keys() and (st.session_state[key] != value):
            st.session_state[key] = value

        #listItems = ['source', 'tzone', 'elev_unit', 'data_export_format', 'detrend', 'special_handling', 'peak_selection', 'freq_smooth', 'horizontal_method', 'stalta_thresh']
        ## Convert items to lists
        #for arg, value in st.session_state.items():
        #    if arg in listItems:
        #        valList = [value]
        #        st.session_state[arg] = valList
        #        run_kwargs[arg] = st.session_state[arg]

        strItems = ['channels', 'xcoord', 'ycoord', 'elevation', 'detrend_options', 'horizontal_method']
        # Convert lists and numbers to strings
        for arg, value in st.session_state.items():
            if arg in strItems:
                if isinstance(value, (list, tuple)):
                    newVal = '['
                    for item in value:
                        newVal = newVal+item+', '
                    newVal = newVal[:-2]+']'

                    st.session_state[arg] = newVal
                    run_kwargs[arg] = newVal
                else:
                    st.session_state[arg] = str(value)
                    run_kwargs[arg] = str(value)

        if verbose:
            print_param(param2print)

        dtimeItems = ['acq_date', 'starttime', 'endtime']
        # Convert everything to python datetime objects
        for arg, value in st.session_state.items():
            if arg in dtimeItems:
                if isinstance(value, str):
                    st.session_state[arg] = datetime.datetime.strptime(value, "%Y-%m-%d")
                    run_kwargs[arg] = datetime.datetime.strptime(value, "%Y-%m-%d")
                elif isinstance(st.session_state[arg], UTCDateTime):
                    st.session_state[arg] = value.datetime
                    run_kwargs[arg] = value.datetime
                else:
                    st.session_state[arg] = value
                    run_kwargs[arg] = value
        
        if verbose:
            print_param(param2print)

        # Case matching
        # Add if-statement for docs building
        if len(st.session_state.keys()) > 0:  #print('allkeys', list(st.session_state.keys()))
            st.session_state.data_export_format = run_kwargs['data_export_format'] = st.session_state.data_export_format.upper()
            st.session_state.detrend = run_kwargs['detrend'] = st.session_state.detrend.title()
            st.session_state.remove_method = run_kwargs['remove_method'] = str(st.session_state.remove_method).title()
            st.session_state.peak_selection = run_kwargs['peak_selection'] = st.session_state.peak_selection.title()
            st.session_state.freq_smooth = run_kwargs['freq_smooth'] = st.session_state.freq_smooth.title()
            st.session_state.source = run_kwargs['source'] = st.session_state.source.title()
        
            if verbose:
                print_param(param2print)


            # Default adjustments
            methodDict = {'None':'Geometric Mean', '0':'Diffuse Field Assumption', '1':'Arithmetic Mean', '2':'Geometric Mean', '3':'Vector Summation', '4':'Quadratic Mean', '5':'Maximum Horizontal Value', '6':'Azimuth'}
            st.session_state.horizontal_method = run_kwargs['horizontal_method'] = methodDict[st.session_state.horizontal_method]
            st.session_state.plot_engine = run_kwargs['plot_engine'] = 'Plotly'
            if verbose:
                print_param(param2print)

            
            st.session_state.default_params = run_kwargs
            st.session_state.run_kws = list(run_kwargs.keys())
            
            if verbose:
                for key, value in st.session_state.items():
                    print("session st: ", st.session_state[key], type( st.session_state[key]), '| rkwargs:', value, type(value))


            if verbose:
                print('Done with setup, session state length: ', len(st.session_state.keys()))
                print_param(param2print)

setup_session_state()

def check_if_default():
    if len(st.session_state.keys()) > 0:
        print('Checking defaults, session state length: ', len(st.session_state.keys()))
        print_param(param2print)
if verbose:
    check_if_default()

def text_change(verbose=verbose):
    #Just a function to run so something is done when text changes
    if verbose:
        print('TEXTCHange')

def on_file_upload():
    file = st.session_state.datapath_uploader
    temp_dir = tempfile.mkdtemp()
    path = pathlib.Path(temp_dir).joinpath(file.name)
    with open(path, "wb") as f:
            f.write(file.getvalue())
    if verbose:
        print(file.name)
    st.session_state.input_data = path.as_posix()


def on_run_data():
    mainContainer = st.container()
    inputTab, outlierTab, infoTab, resultsTab = mainContainer.tabs(['Data', 'Outliers', 'Info','Results'])
    plotReportTab, csvReportTab, strReportTab = resultsTab.tabs(['Plot', 'Results Table', 'Print Report'])

    if st.session_state.input_data!='':
        srun = {}
        for key, value in st.session_state.items():
            if key in st.session_state.run_kws and value != st.session_state.default_params[key]:
                srun[key] = value
        # Get plots all right
        srun['plot_engine'] = 'plotly'
        srun['plot_input_stream'] = True
        srun['show_plot'] = False
        srun['verbose'] = False #True
        if verbose:
            print('SPRIT RUN', srun)
        st.toast('Data is processing', icon="⌛")
        with mainContainer:
            spinnerText = 'Data is processing with default parameters.'
            excludedKeys = ['plot_engine', 'plot_input_stream', 'show_plot', 'verbose']
            NOWTIME = datetime.datetime.now()
            secondaryDefaults = {'acq_date':datetime.date(NOWTIME.year, NOWTIME.month, NOWTIME.day),
                                 'hvsr_band':(0.4, 40), 'use_hv_curve':True,
                                 'starttime':datetime.time(0,0,0),
                                 'endtime':datetime.time(23,59,0),
                                 'peak_freq_range':(0.4, 40),
                                 'stalta_thresh':(8, 16),
                                 'period_limits':(0.025, 2.5),
                                 'remove_method':['Auto'],
                                 'elev_unit':'m',
                                 'plot_type':'HVSR p ann C+ p ann Spec p'
                                 }
            nonDefaultParams = False
            for key, value in srun.items():
                if key not in excludedKeys:
                    if key in secondaryDefaults and secondaryDefaults[key] == value:
                        pass
                    else:
                        nonDefaultParams = True
                        spinnerText = spinnerText + f"\n-\t {key} = {value} ({type(value)} is not {st.session_state.default_params[key]}; {type(st.session_state.default_params[key])})"
            if nonDefaultParams:
                spinnerText = spinnerText.replace('default', 'the following non-default')
            with st.spinner(spinnerText):
                st.session_state.hvsr_data = sprit_hvsr.run(input_data=st.session_state.input_data, **srun)
        
        write_to_info_tab(infoTab)
        st.balloons()
        
        inputTab.plotly_chart(st.session_state.hvsr_data['InputPlot'], use_container_width=True)
        outlierTab.plotly_chart(st.session_state.hvsr_data['OutlierPlot'], use_container_width=True)
        plotReportTab.plotly_chart(st.session_state.hvsr_data['HV_Plot'], use_container_width=True)
        csvReportTab.dataframe(data=st.session_state.hvsr_data['CSV_Report'])
        strReportTab.text(st.session_state.hvsr_data['Print_Report'])

    st.session_state.prev_datapath=st.session_state.input_data
    
def write_to_info_tab(info_tab):
    with info_tab:
        st.markdown("# Processing Parameters Used")
        for fun, kwargDict in sigList:
            funSig = inspect.signature(fun)
            #excludeKeys = ['params', 'hvsr_data', 'hvsr_results']
            funMD = ""
            for arg in funSig.parameters.keys():
                if arg in st.session_state.keys():
                    funMD = funMD + f"""\n    * {arg} = {st.session_state[arg]}"""

            with st.expander(f"{fun.__name__}"):
                st.write(funMD, unsafe_allow_html=True)


# DEFINE SIDEBAR
if verbose:
    print('About to start setting up sidebar, session state length: ', len(st.session_state.keys()))
    print_param(param2print)

with st.sidebar:
    if verbose:
        print('Start setting up sidebar, session state length: ', len(st.session_state.keys()))
        print_param(param2print)

    st.header('SpRIT HVSR', divider='rainbow')
    datapathInput = st.text_input("Datapath", key='input_data', placeholder='Enter data filepath (to be read by obspy.core.Stream.read())')    
    # st.file_uploader('Upload data file(s)', type=OBSPYFORMATS, accept_multiple_files=True, key='datapath_uploader', on_change=on_file_upload)
    with st.expander("Click to access data uploader"):
        st.file_uploader("Upload data file(s)", type=OBSPYFORMATS, accept_multiple_files=False, key='datapath_uploader', on_change=on_file_upload)

    bottom_container = st.container()

    # Create top menu
    with bottom_container:

        resetCol, readCol, runCol = st.columns([0.3, 0.3, 0.4])
        resetCol.button('Reset', disabled=True, use_container_width=True)
        readCol.button('Read', use_container_width=True, args=((True, )))
        runCol.button('Run', type='primary', use_container_width=True, on_click=on_run_data)
    
    if verbose:
        print('Done setting up bottom container, session state length: ', len(st.session_state.keys()))
        print_param(param2print)

    # Add if-statement for docs building
    if len(list(st.session_state.keys())) > 0:
        st.header('Settings', divider='gray')
        with st.expander('Expand to modify settings'):
            if verbose:
                print('Setting up sidebar expander, session state length: ', len(st.session_state.keys()))
                print_param(param2print)

            ipSetTab, fdSetTab, rmnocSetTab, gpSetTab, phvsrSetTab, plotSetTab = st.tabs(['Input', 'Data', "Noise", 'PPSDs', 'H/V', 'Plot'])
            #@st.experimental_dialog("Update Input Parameters", width='large')
            #def open_ip_dialog():
            with ipSetTab:
                if verbose:
                    print('Setting up input tab, session state length: ', len(st.session_state.keys()))
                st.text_input("Site Name", placeholder='HVSR Site', on_change=text_change, key='site')

                #with st.expander('Primary Input Parameters', expanded=True):

                st.text_input('Instrument', help='Raspberry Shake and Tromino are currently the only values with special treatment. If a filepath, can use a .inst instrument file (json format)', key='instrument')
                st.text_input('Metadata Filepath', help='Filepath to instrument response file', key='metapath')

                st.select_slider('HVSR Band',  value=st.session_state.hvsr_band, options=bandVals, key='hvsr_band')
                st.select_slider('Peak Frequency Range',  value=st.session_state.peak_freq_range, options=bandVals, key='peak_freq_range')

                # with st.expander('Acquisition Date/Time'):
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


                #with st.expander('Instrument settings'):
                st.text_input("Network", placeholder='AM', key='network')
                st.text_input("Station", placeholder='RAC84', key='station')
                st.text_input("Location", placeholder='00', key='loc')
                st.text_input("Channels", placeholder='EHZ, EHE, EHN', key='channels')

                #with st.expander('Location settings'):
                st.text_input('X Coordinate', help='i.e., Longitude or Easting', key='xcoord')
                st.text_input('Y Coordinate', help='i.e., Latitude or Northing', key='ycoord')
                st.text_input('Z Coordinate', help='i.e., Elevation', key='elevation')
                st.session_state.elev_unit = st.selectbox('Z Unit', options=['m', 'ft'], help='i.e., Elevation unit')
                st.number_input('Depth', help='i.e., Depth of measurement below ground surface (not currently used)', key='depth')

                st.text_input('CRS of Input Coordinates', help='Can be EPSG code or anything accepted by pyproj.CRS.from_user_input()', key='input_crs')
                st.text_input('CRS for Export', help='Can be EPSG code or anything accepted by pyproj.CRS.from_user_input()', key='output_crs')
                if verbose:
                    print_param(param2print)

            #@st.experimental_dialog("Update Parameters to Fetch Data", width='large')
            #def open_fd_dialog():
            with fdSetTab:
                if verbose:
                    print('Setting up fd tab, session state length: ', len(st.session_state.keys()))
                #source: str = 'file',
                st.selectbox('Source', options=['File', 'Raw', 'Directory', "Batch"], index=0, key='source')
                st.text_input('Trim Directory', help='Directory for saving trimmed data', key='trim_dir')
                st.selectbox('Data format', options=OBSPYFORMATS, index=11, key='data_export_format')
                st.selectbox('Detrend horizontal_method', options=['None', 'Simple', 'Linear', 'Constant/Demean', 'Polynomial', 'Spline'], index=5, help='Detrend horizontal_method use by `type` parameter of obspy.trace.Trace.detrend()', key='detrend')
                st.text_input('Detrend options', value='detrend_options=2', help="Comma separated values with equal sign between key/value of arguments to pass to the **options argument of obspy.trace.Trace.detrend()", key='detrend_options')
                if verbose:
                    print_param(param2print)

            
            #@st.experimental_dialog("Update Parameters to Generate PPSDs", width='large')
            #def open_ppsd_dialog():
            with gpSetTab:
                if verbose:
                    print('Setting up ppsd tab, session state length: ', len(st.session_state.keys()))
                st.toggle('Skip on gaps', help='Determines whether time segments with gaps should be skipped entirely. Select skip_on_gaps=True for not filling gaps with zeros which might result in some data segments shorter than ppsd_length not used in the PPSD.',
                        key='skip_on_gaps')
                st.number_input("Minimum Decibel Value", value=-200, step=1, key='min_deb')
                st.number_input("Maximum Decibel Value", value=-50, step=1, key='max_deb')
                st.number_input("Decibel bin size", value=1.0, step=0.1, key='deb_step')
                st.session_state.db_bins = (st.session_state.min_deb, st.session_state.max_deb, st.session_state.deb_step)

                st.number_input('PPSD Length (seconds)', step=1, key='ppsd_length')
                st.number_input('PPSD Window overlap (%, 0-1)', step=0.01, min_value=0.0, max_value=1.0, key='overlap')
                st.number_input('Period Smoothing Width (octaves)', step=0.1, key='period_smoothing_width_octaves')
                st.number_input('Period Step (octaves)', step=0.005, format="%.5f", key='period_step_octaves')
                periodVals=[round(1/x,3) for x in bandVals]
                periodVals.sort()

                st.select_slider('Period Limits (s)', options=periodVals, value=st.session_state.period_limits, key='period_limits')
                st.selectbox("Special Handling", options=['None', 'Ringlaser', 'Hydrophone'], key='special_handling')
                if verbose:
                    print_param(param2print)

            #@st.experimental_dialog("Update Parameters to Remove Noise and Outlier Curves", width='large')
            #def open_outliernoise_dialog():
            with rmnocSetTab:
                if verbose:
                    print('Setting up noise tab, session state length: ', len(st.session_state.keys()))
                st.number_input("Outlier Threshold", value=98, key='rmse_thresh')
                st.radio('Threshold type', options=['Percentile', 'Value'], key='threshRadio')
                st.session_state.use_percentile = st.session_state.threshRadio=='Percentile'
                st.radio('Threshold curve', options=['HV Curve', 'Component Curves'], key='curveRadio')
                st.session_state.use_hv_curve = (st.session_state.curveRadio=='HV Curve')

                st.multiselect("Noise Removal Method",
                                options=['None','Auto', 'Manual', 'Stalta', 'Saturation Threshold', 'Noise Threshold', 'Warmup', 'Cooldown', 'Buffer'], key='remove_method')
                st.number_input('Saturation Percent', min_value=0.0, max_value=1.0, step=0.01, format="%.3f", key='sat_percent')
                st.number_input('Noise Percent', min_value=0.0, max_value=1.0, step=0.1, format="%.2f", key='noise_percent')
                st.number_input('Short Term Average (STA)', step=1.0, format="%.1f", key='sta')
                st.number_input('Long Term Average (LTA)', step=1.0, format="%.1f", key='lta')
                staltaVals = np.arange(0, 51).tolist()
                st.select_slider('STA/LTA Thresholds', value=st.session_state.stalta_thresh, options=staltaVals, key='stalta_thresh')
                st.number_input('Warmup Time (seconds)', step=1, key='warmup')
                st.number_input('Cooldown Time (seconds)', step=1, key='cooldown')
                st.number_input('Minimum Window Size (samples)', step=1, key='min_win_size')
                st.toggle("Remove Raw Noise", help='Whether to use the raw input data to remove noise.', key='remove_raw_noise')
                if verbose:
                    print_param(param2print)

            #@st.experimental_dialog("Update Parameters to Process HVSR", width='large')
            #def open_processHVSR_dialog():
            with phvsrSetTab:
                if verbose:
                    print('Setting up hvsr tab, session state length: ', len(st.session_state.keys()))
                st.selectbox('Peak Selection Method', options=['Max', 'Scored'], key='peak_selection')
                st.selectbox("Method to combine hoizontal components", 
                            options=['Diffuse Field Assumption', 'Arithmetic Mean', 'Geometric Mean', 'Vector Summation', 'Quadratic Mean', 'Maximum Horizontal Value', 'Azimuth'], 
                            index=2, key='horizontal_method')
                rList = np.arange(1001).tolist()
                rList[0] = False
                st.selectbox("Curve Smoothing", options=['None', 'Savgoy Filter', 'Konno Ohmachi', "Proportional", "Constant"], index=2, key='freq_smooth')
                st.select_slider("Curve Smoothing Parameter", options=np.arange(1000).tolist(), value=40, key='f_smooth_width')
                st.select_slider("Resample", options=rList, value=1000, key='resample')
                st.select_slider('Outlier Curve Removal', options=rList[:100], key='outlier_curve_rmse_percentile')
                if verbose:
                    print_param(param2print)

            def update_plot_string():
                plotStringDict={'Peak Frequency':' p', 'Peak Amplitude':' pa', 'Annotation':' ann',
                                'Time windows':' t', "Peaks of Time Windows": ' tp',
                                'Test 1: Peak > 2x trough below':'1', 
                                "Test 2: Peak > 2x trough above":'2',
                                "Test 3: Peak > 2":'3', 
                                "Test 4":'4', "Test 5":'5', "Test 6":'6',
                                }
                
                plotString = ''
                for plot in st.session_state.plotPlotStr:
                    if plot=='HVSR':
                        plotString=plotString+'HVSR'
                        for pc in st.session_state.hvsrPlotStr:
                            if 'test' in pc.lower():
                                if 'test' not in plotString.lower():
                                    plotString = plotString + ' Test'
                                test_end_index = plotString.rfind("Test") + len("Test")
                                nextSpaceIndex = plotString[test_end_index:].rfind(" ")
                                if nextSpaceIndex == -1:
                                    nextSpaceIndex=len(plotString)
                                noString = plotString[test_end_index:nextSpaceIndex]
                                noString = noString + plotStringDict[pc]

                                # Order test numbers correctly
                                testNos = ''.join(sorted(noString))
                                plotString = plotString[:test_end_index] + testNos                             
        
                            else:
                                plotString = plotString + plotStringDict[pc]
                    if plot=='Components':
                        plotString=plotString+' C+'
                        for pc in st.session_state.compPlotStr:
                            plotString = plotString + plotStringDict[pc]
                    if plot=='Spectrogram':
                        plotString=plotString+' SPEC'
                        for pc in st.session_state.specPlotStr:
                            plotString = plotString + plotStringDict[pc]
                    if plot=='Azimuth':
                        plotString=plotString+' AZ'    
                st.session_state.plot_type = plotString


            #@st.experimental_dialog("Update Plot Settings", width='large')
            #def plot_settings_dialog():
            with plotSetTab:
                if verbose:
                    print('Setting up plot tab, session state length: ', len(st.session_state.keys()))

                st.selectbox("Plot Engine (currently only plotly supported)", options=['Matplotlib', "Plotly"], key='plot_engine', disabled=True)
                st.text_input("Plot type (plot string)", value='HVSR p ann C+ p ann Spec p', key='plot_type')
                st.multiselect("Charts to show", options=['HVSR', "Components", 'Spectrogram', 'Azimuth'], default=['HVSR', 'Components', "Spectrogram"], 
                                                on_change=update_plot_string, key='plotPlotStr')
                
                st.header("HVSR Chart", divider='rainbow')
                st.multiselect('Items to plot', options=['Peak Frequency', 'Peak Amplitude', 'Annotation', 'Time windows', "Peaks of Time Windows",
                                                        'Test 1: Peak > 2x trough below' , "Test 2: Peak > 2x trough above", "Test 3: Peak > 2", "Test 4", "Test 5", "Test 6"],
                                                        on_change=update_plot_string,
                                                        default=["Peak Frequency", "Annotation"], key='hvsrPlotStr')

                st.header("Component Chart", divider='rainbow')
                st.multiselect('Items to plot', options=['Peak Frequency', 'Annotation', 'Time windows'], on_change=update_plot_string,
                                                        default=["Peak Frequency", "Annotation"], key='compPlotStr')
                
                st.header('Spectrogram Chart', divider='rainbow')
                st.multiselect('Items to plot', options=['Peak Frequency', 'Annotation'], key='specPlotStr', on_change=update_plot_string)
                if verbose:
                    print_param(param2print)

    if verbose:
        print('Done setting up sidebar, session state length: ', len(st.session_state.keys()))
        print('Done setting up everything (end of main), session state length: ', len(st.session_state.keys()))
        print_param(param2print)
    #if __name__ == "__main__":
    #    main()

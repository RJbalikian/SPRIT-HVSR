try:
    import sprit
except Exception:
    try:
        import sprit_hvsr as sprit
        import sprit_plot
    except Exception:
        from sprit import sprit_hvsr as sprit
        from sprit import sprit_plot

import copy
import datetime
import inspect
import io
import pathlib
import pickle
import pkg_resources
import tempfile
import zoneinfo

import matplotlib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly import subplots
import streamlit as st
from obspy import UTCDateTime
from obspy.signal.spectral_estimation import PPSD
from scipy import signal

try:
    from sprit import sprit_hvsr
except Exception:
    try:
        import sprit_hvsr
    except Exception:
        import sprit as sprit_hvsr

VERBOSE = False

RESOURCE_DIR = pathlib.Path(pkg_resources.resource_filename(__name__, 'resources'))
SAMPLE_DATA_DIR = RESOURCE_DIR.joinpath('sample_data')
SETTINGS_DIR = RESOURCE_DIR.joinpath('settings')

spritLogoPath = RESOURCE_DIR.joinpath("icon").joinpath("SpRITLogo.png")

if VERBOSE:
    print('Start of file, session state length: ', len(st.session_state.keys()))
PARAM2PRINT = None
def print_param(key=PARAM2PRINT, write_key=False):
    if key is None:
        pass
    elif key in st.session_state.keys():
        print(key, st.session_state[key], 'type:', type(st.session_state[key]))
        if write_key:
            st.write(key, st.session_state[key], 'type:', type(st.session_state[key]))
print_param(PARAM2PRINT)

icon=":material/electric_bolt:"
if hasattr(sprit, '__version__'):
    spritversion = sprit.__version__
else:
    spritversion = '2.0+'
aboutStr = """
# About SpRIT
### This app uses SpRIT v0.0.0

SpRIT is developed by Riley Balikian at the Illinois State Geological Survey.

Please visit the following links for any questions:
* [API Documentation](https://sprit.readthedocs.io/en/latest/sprit.html)
* [Wiki](https://github.com/RJbalikian/SPRIT-HVSR/wiki) 
* [Pypi Repository](https://pypi.org/project/sprit/)

"""
aboutStr = aboutStr.replace('0.0.0', spritversion)

if VERBOSE:
    print('Start setting up page config, session state length: ', len(st.session_state.keys()))
st.set_page_config('SpRIT HVSR',
                    page_icon=icon,
                    layout='wide',
                    menu_items={'Get help': 'https://github.com/RJbalikian/SPRIT-HVSR/wiki',
                                'Report a bug': "https://github.com/RJbalikian/SPRIT-HVSR/issues",
                                'About': aboutStr})

if VERBOSE:
    print('Start setting up constants/variables, session state length: ', len(st.session_state.keys()))
OBSPYFORMATS =  ['AH', 'ALSEP_PSE', 'ALSEP_WTH', 'ALSEP_WTN', 'CSS', 'DMX', 'GCF', 'GSE1', 'GSE2', 'KINEMETRICS_EVT', 'KNET', 'MSEED', 'NNSA_KB_CORE', 'PDAS', 'PICKLE', 'Q', 'REFTEK130', 'RG16', 'SAC', 'SACXY', 'SEG2', 'SEGY', 'SEISAN', 'SH_ASC', 'SLIST', 'SU', 'TRC', 'TSPAIR', 'WAV', 'WIN', 'Y']
bandVals=[0.05,0.06,0.07,0.08,0.09,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,2,3,4,5,6,7,8,9,10,20,30,40,50,60,70,80,90,100]

# SETUP KWARGS
if VERBOSE:
    print('Start setting up kwargs dicts, session state length: ', len(st.session_state.keys()))

run_kwargs = {}
ip_kwargs = {}
fd_kwargs = {}
ca_kwargs = {}
rn_kwargs = {}
gpsd_kwargs = {}
phvsr_kwargs = {}
roc_kwargs = {}
cp_kwargs = {}
gr_kwargs = {}
run_kwargs = {}

#spritLogoPath = pathlib.Path(r"C:\Users\riley\LocalData\Repos\SPRIT-HVSR\sprit\resources\icon\SpRITLogo.png")
if spritLogoPath.exists():
    st.logo(spritLogoPath, size='large')

if VERBOSE:
    print('Start getting default values, session state length: ', len(st.session_state.keys()))
    print_param(PARAM2PRINT)

# Get default values
funList = [[sprit.run, run_kwargs], [sprit.input_params, ip_kwargs], [sprit.fetch_data, fd_kwargs], [sprit.calculate_azimuth, ca_kwargs],
            [sprit.remove_noise, rn_kwargs], [sprit.generate_psds, gpsd_kwargs], [PPSD, gpsd_kwargs],
            [sprit.process_hvsr, phvsr_kwargs], [sprit.remove_outlier_curves, roc_kwargs],
            [sprit.check_peaks, cp_kwargs], [sprit.get_report, gr_kwargs]]


# Function to initialize session state variables
def initial_setup_fun(session_state_key, initial_value, running_value='Do not use'):
    if not hasattr(st.session_state, session_state_key):
        st.session_state[session_state_key] = initial_value
    elif running_value != "Do not use":
        st.session_state[session_state_key] = running_value

# Initialize variables
initial_setup_fun('initial_setup', True, False)
initial_setup_fun('tabs_setup', False)
initial_setup_fun('mainContain_setup', False)

def setup_session_state():
    if st.session_state.initial_setup:
        # "Splash screen" (only shows at initial startup)

        mainContainerInitText = """
        # SpRIT HVSR
        ## About
        SpRIT HVSR is developed by the Illinois State Geological Survey, part of the Prairie Research Institute at the University of Illinois.
        
        ### This app is using SpRIT v0.0.0
        ## Links
        * API Documentation may be accessed here: [ReadtheDocs](https://sprit.readthedocs.io/en/latest/sprit.html) and [Github Pages](https://rjbalikian.github.io/SPRIT-HVSR/main.html)
        * The Wiki and Tutorials may be accessed here: [https://github.com/RJbalikian/SPRIT-HVSR/wiki](https://github.com/RJbalikian/SPRIT-HVSR/wiki)
        * Source Code may be accessed here: [https://github.com/RJbalikian/SPRIT-HVSR](https://github.com/RJbalikian/SPRIT-HVSR)
        * PyPI repository may be accessed here: [https://pypi.org/project/sprit/](https://pypi.org/project/sprit/)

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
        mainContainerInitText = mainContainerInitText.replace('0.0.0', spritversion)

        st.markdown(mainContainerInitText, unsafe_allow_html=True)
        if VERBOSE:
            print('Start sig loop, session state length: ', len(st.session_state.keys()))
            print_param(PARAM2PRINT)

        # Get all function defaults
        for fun, funDict in funList:
            funSig = inspect.signature(fun)
            for arg in funSig.parameters.keys():
                if not (funSig.parameters[arg].default is funSig.parameters[arg].empty):
                    funDict[arg] = funSig.parameters[arg].default
                    run_kwargs[arg] = funSig.parameters[arg].default

        gpsd_kwargs['ppsd_length'] = run_kwargs['ppsd_length'] = 30
        gpsd_kwargs['skip_on_gaps'] = run_kwargs['skip_on_gaps'] = True
        gpsd_kwargs['period_step_octaves'] = run_kwargs['period_step_octaves'] = 0.03125
        gpsd_kwargs['period_limits'] = run_kwargs['period_limits'] = [1/run_kwargs['hvsr_band'][1], 1/run_kwargs['hvsr_band'][0]]
        
        if VERBOSE:
            print('Done getting kwargs: ', len(st.session_state.keys()))
            print_param(PARAM2PRINT)

            print('Setting up session state: ', len(st.session_state.keys()))
        #st.session_state["updated_kwargs"] = {}
        for key, value in run_kwargs.items():
            if VERBOSE:
                print('resetting')
                print_param(PARAM2PRINT)
                print(key, ": ", value)
            #    if key in st.session_state.keys() and (st.session_state[key] != value):
            st.session_state[key] = value

        #listItems = ['source', 'tzone', 'elev_unit', 'data_export_format', 'detrend', 'special_handling', 'peak_selection', 'freq_smooth', 'horizontal_method', 'stalta_thresh']
        ## Convert items to lists
        #for arg, value in st.session_state.items():
        #    if arg in listItems:
        #        valList = [value]
        #        st.session_state[arg] = valList
        #        run_kwargs[arg] = st.session_state[arg]

        # Convert lists and numbers to strings
        strItems = ['channels', 'xcoord', 'ycoord', 'elevation', 'detrend_options', 'filter_options', 'horizontal_method']
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

        if VERBOSE:
            print_param(PARAM2PRINT)

        # Convert all times to python datetime objects
        dtimeItems=['acq_date', 'starttime', 'endtime']
        for arg , value in st.session_state.items():
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
        
        if VERBOSE:
            print_param(PARAM2PRINT)

        # Case matching
        st.session_state.data_export_format = run_kwargs['data_export_format'] = st.session_state.data_export_format.upper()
        st.session_state.detrend = run_kwargs['detrend'] = st.session_state.detrend.title()
        st.session_state.azimuth_type = run_kwargs['azimuth_type'] = st.session_state.azimuth_type.title()
        st.session_state.peak_selection = run_kwargs['peak_selection'] = st.session_state.peak_selection.title()
        st.session_state.freq_smooth = run_kwargs['freq_smooth'] = st.session_state.freq_smooth.title()
        st.session_state.source = run_kwargs['source'] = st.session_state.source.title()
        #st.session_state.plot_engine = run_kwargs['plot_engine'] = st.session_state.plot_engine.title()
               
        # Update Nones
        # Remove method
        if st.session_state.remove_method is None:
            st.session_state.remove_method = run_kwargs['remove_method'] = 'None'
        else:
            st.session_state.remove_method = run_kwargs['remove_method'] = st.session_state.remove_method.title()

        # Other updates
        st.session_state.azimuth_unit = run_kwargs['azimuth_unit'] = '°'
        st.session_state.plot_engine = run_kwargs['plot_engine'] = "Plotly"
        

        # Horizontal_method
        methodDict = {'0':'Diffuse Field Assumption', '1':'Arithmetic Mean', '2':'Geometric Mean', '3':'Vector Summation', '4':'Quadratic Mean', '5':'Maximum Horizontal Value', '6':'Azimuth', "None":"Vector Summation"}            
        if st.session_state.horizontal_method is None:
            st.session_state.horizontal_method = run_kwargs['horizontal_method'] = methodDict["3"]            
        else:
            st.session_state.horizontal_method = run_kwargs['horizontal_method'] = methodDict[st.session_state.horizontal_method]

        # Set Defaults
        st.session_state.default_params = run_kwargs

        if VERBOSE:
            print_param(PARAM2PRINT)

        st.session_state.run_kws = list(run_kwargs.keys())
        
        if VERBOSE:
            for key, value in st.session_state.items():
                print("session st: ", st.session_state[key], type( st.session_state[key]), '| rkwargs:', value, type(value))


        if VERBOSE:
            print('Done with setup, session state length: ', len(st.session_state.keys()))
            print_param(PARAM2PRINT)

        st.session_state['NewSessionState'] = copy.copy(st.session_state)

def check_if_default():
    if len(st.session_state.keys()) > 0:
        print('Checking defaults, session state length: ', len(st.session_state.keys()))
        print_param(param2print)

if VERBOSE:
    check_if_default()


def text_change(VERBOSE=VERBOSE):
    #Just a function to run so something is done when text changes
    if VERBOSE:
        print('TEXTCHange')


def on_file_upload():
    file = st.session_state.datapath_uploader
    temp_dir = tempfile.mkdtemp()
    path = pathlib.Path(temp_dir).joinpath(file.name)
    with open(path, "wb") as f:
            f.write(file.getvalue())
    if VERBOSE:
        print(file.name)
    st.session_state.input_data = path.as_posix()

# Set up main container
def setup_main_container(do_setup_tabs=False):
    mainContainer = st.container()
    st.session_state.mainContainer = mainContainer
    dlText, dlPDFReport, dlStream, dlTable, dlPlot, dlHVSR = st.session_state.mainContainer.columns([0.2, 0.16, 0.16, 0.16, 0.16, 0.16])

    st.session_state.dlText = dlText
    st.session_state.dlPDFReport = dlPDFReport
    st.session_state.dlStream = dlStream
    st.session_state.dlTable = dlTable
    st.session_state.dlPlot = dlPlot
    st.session_state.dlHVSR = dlHVSR

    if do_setup_tabs:
        setup_tabs(mainContainer)
    
    st.session_state.mainContain_setup = True

if not st.session_state.initial_setup:
    setup_main_container(do_setup_tabs=False)

# Set up tabs
def setup_tabs(mainContainer):
    inputTab, outlierTab, infoTab, resultsTab = mainContainer.tabs(['Data', 'Outliers', 'Info','Results'])
    plotReportTab, csvReportTab, strReportTab = resultsTab.tabs(['Plot', 'Results Table', 'Print Report'])
    #tabs: st.session_state.inputTab, st.session_state.outlierTab, st.session_state.infoTab, st.session_state.resultsTab, plotReportTab, st.session_state.csvReportTab, st.session_state.strReportTab

    st.session_state.inputTab = inputTab
    st.session_state.outlierTab = outlierTab
    st.session_state.infoTab = infoTab
    st.session_state.resultsTab = resultsTab
    st.session_state.plotReportTab = plotReportTab
    st.session_state.csvReportTab = csvReportTab
    st.session_state.strReportTab = strReportTab

    st.session_state.tabs_setup = True


def on_run_data():
    # Runs sample data if nothing specified
    if st.session_state.input_data == '':
        st.session_state.input_data = 'sample'

    # Now run the data
    if st.session_state.input_data!='':
        srun = {}
        for key, value in st.session_state.items():
            if key in st.session_state.run_kws:
                if value != st.session_state.default_params[key]:
                    if str(value) != str(st.session_state.default_params[key]):
                        srun[key] = value
            
            if key == 'plot_engine':
                srun[key] = value
                
        # Get plots all right
        #srun['plot_engine'] = 'matplotlib'
        srun['plot_input_stream'] = True
        srun['show_plot'] = False
        srun['verbose'] = False #True

        # Update outputs
        srun['report_export_format'] = None
        srun['show_pdf_report'] = False
        srun['show_print_report'] = True
        srun['show_plot_report'] = False
        
        if VERBOSE:
            print('SPRIT RUN', srun)
        st.toast('Data is processing', icon="⌛")
        
        setup_main_container(do_setup_tabs=False)
        with st.session_state.mainContainer:
            spinnerText = 'Data is processing with default parameters.'
            excludedKeys = ['plot_engine', 'plot_input_stream', 'show_plot', 'verbose']
            NOWTIME = datetime.datetime.now()
            secondaryDefaults = {'acq_date': datetime.date(NOWTIME.year, NOWTIME.month, NOWTIME.day),
                                 'hvsr_band':(0.1, 50), 'use_hv_curve':True,
                                 'starttime':datetime.time(0,0,0),
                                 'endtime':datetime.time(23, 59, 0),
                                 'peak_freq_range':(0.1, 50),
                                 'stalta_thresh':(8, 16),
                                 'period_limits':(0.02, 10),
                                 'remove_method':['None'],
                                 'report_export_format':None,
                                 'report_formats':  ['print', 'table', 'plot', 'html', 'pdf'] ,
                                 'show_pdf_report':False,
                                 'show_print_report':True,
                                 'show_plot_report':False,
                                 'elev_unit':'m',
                                 'plot_type':'HVSR p ann C+ p ann Spec p',
                                 'suppress_report_outputs':True
                                 }
            
            nonDefaultParams = False

            srun['report_formats'] = ['print', 'table', 'plot', 'html', 'pdf']
            srun['suppress_report_outputs'] = True

            # Display non-default parameters, if applicable
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
        
        st.balloons()

        st.session_state.stream = st.session_state.hvsr_data['stream']
        st.session_state.stream_edited = st.session_state.hvsr_data['stream_edited']

        display_results()
        st.session_state.prev_datapath = st.session_state.input_data


def on_read_data():
    if 'read_button' not in st.session_state.keys() or not st.session_state.read_button:
        return

    st.session_state.mainContainer = st.container()
    st.session_state.inputTab, st.session_state.infoTab = st.session_state.mainContainer.tabs(['Raw Seismic Data', 'Info'])

    if st.session_state.input_data != '':
        srun = {}
        for key, value in st.session_state.items():
            if key in st.session_state.run_kws:
                if value != st.session_state.default_params[key]:
                    if str(value) != str(st.session_state.default_params[key]):
                        srun[key] = value
            
            if key == 'plot_engine':
                srun[key] = value
    
    ipKwargs = {k: v for k, v in st.session_state.items() if k in tuple(inspect.signature(sprit.input_params).parameters.keys())}
    fdKwargs = {k: v for k, v in st.session_state.items() if k in tuple(inspect.signature(sprit.fetch_data).parameters.keys())}

    #fdKwargs['plot_input_stream'] = True
        
    st.toast('Reading data', icon="⌛")
    with st.spinner(f"Reading data: {ipKwargs['input_data']}"):
        inParams = sprit.input_params(**ipKwargs)
        st.session_state.hvDataIN = sprit.fetch_data(inParams, **fdKwargs)

    st.session_state.input_fig = make_input_fig()
    st.session_state.data_chart_event = st.session_state.inputTab.plotly_chart(st.session_state.input_fig,
                                        on_select=update_data, key='data_plot', 
                                        selection_mode='box', use_container_width=True, theme='streamlit')

    st.session_state.inputTab.write("Select any time window with the Box Selector (see the top right of chart) to remove it from analysis.")
    st.session_state.input_selection_mode = st.session_state.inputTab.pills('Window Selection Mode', options=['Add', "Delete"], key='input_selection_toggle', 
                                                 default='Add', on_change=update_selection_type, disabled=True, 
                                                 help='If in "Add" mode, windows for removal will be added at your selection. If "Delete" mode, these windows will be deleted. Currently only "Add" supported')

    # Print information about the data to Info tab
    infoTab.header("Information About Input Data")
    infoTab.write(f"Acquisition Date: {st.session_state.hvDataIN['acq_date']}")

    recLength = (UTCDateTime(st.session_state.hvDataIN['stream'][0].stats.endtime) - UTCDateTime(st.session_state.hvDataIN['stream'][0].stats.starttime))
    infoTab.write(f"Record Length: {recLength/60:.2f} minutes ({recLength} seconds)")


def on_reset():
    st.toast("Session state cleared")
    st.session_state = st.session_state['NewSessionState']


def _get_use_array(hvsr_data, f=None, timeWindowArr=None, psdArr=None):
    streamEdit = st.session_state.stream_edited.copy()

    earliestStart = UTCDateTime(3000, 12, 31)
    for trace in streamEdit:
        if trace.stats.starttime < earliestStart:
            earliestStart = trace.stats.starttime

    zList = []
    eList = []
    nList = []
    streamEdit = streamEdit.split()
    for trace in streamEdit:
        traceSTime = trace.stats.starttime
        traceETime = trace.stats.endtime

        if trace.stats.component == 'Z':
            zList.append([traceSTime, traceETime])
        if trace.stats.component == 'E':
            eList.append([traceSTime, traceETime])
        if trace.stats.component == 'N':
            nList.append([traceSTime, traceETime])

    gapListUTC = []
    for i, currWindow in enumerate(zList):
        if i > 0:
            prevWindow = zList[i-1]

            gapListUTC.append([prevWindow[1], currWindow[0]])

    gapList = [[np.datetime64(gTimeUTC.datetime) for gTimeUTC in gap] for gap in gapListUTC]

    if hasattr(hvsr_data, 'BLARB'):
        hvdf = hvsr_data.hvsr_windows_df
        tps = pd.Series(hvdf.index.copy(), name='TimesProcessed_Start', index=hvdf.index)
        hvdf["TimesProcessed_Start"] = tps
        useArrShape = f.shape[0]
        
    else:
        useSeries = pd.Series([True]*(timeWindowArr.shape[0]-1), name='Use')
        sTimeSeries = pd.Series(timeWindowArr[:-1], name='TimesProcessed')
        eTimeSeries = pd.Series(timeWindowArr[1:], name='TimesProcessed_End')

        hvdf = pd.DataFrame({'TimesProcessed':sTimeSeries,
                             'TimesProcessed_End':eTimeSeries,
                             'Use':useSeries})

        hvdf.set_index('TimesProcessed', inplace=True, drop=True)
        hvdf['TimesProcessed_Start'] = timeWindowArr[:-1]
        
        useArrShape = psdArr.shape[0]

    if 'TimesProcessed_Obspy' not in hvdf.columns:
        hvdf['TimesProcessed_Obspy'] = [UTCDateTime(dt64) for dt64 in sTimeSeries]
        hvdf['TimesProcessed_ObspyEnd'] = [UTCDateTime(dt64) for dt64 in eTimeSeries]

    # Do processing
    if len(gapListUTC) > 0:
        for gap in gapListUTC:

            stOutEndIn = hvdf['TimesProcessed_Obspy'].gt(gap[0]) & hvdf['TimesProcessed_Obspy'].lt(gap[1])
            stInEndOut = hvdf['TimesProcessed_ObspyEnd'].gt(gap[0]) & hvdf['TimesProcessed_ObspyEnd'].lt(gap[1])
            bothIn = hvdf['TimesProcessed_Obspy'].lt(gap[0]) & hvdf['TimesProcessed_ObspyEnd'].gt(gap[1])
            bothOut = hvdf['TimesProcessed_Obspy'].gt(gap[0]) & hvdf['TimesProcessed_ObspyEnd'].lt(gap[1])

            hvdf.loc[hvdf[stOutEndIn | stInEndOut | bothIn | bothOut].index, 'Use'] = False

    return hvdf, useArrShape

@st.cache_data
def _generate_stream_specgram(_trace):

    return signal.spectrogram(x=_trace.data,
                              fs=_trace.stats.sampling_rate,
                              mode='magnitude')


def make_input_fig():
    no_subplots = 5
    inputFig = subplots.make_subplots(rows=no_subplots, cols=1,
                                      row_heights=[0.5, 0.02, 0.16, 0.16, 0.16],
                                      shared_xaxes=True,
                                      horizontal_spacing=0.01,
                                      vertical_spacing=0.01
                                      )

    hvsr_data = st.session_state.hvsr_data

    # Windows PSD and Used
    #psdArr = np.flip(hvsr_data.ppsds["Z"]['psd_values'].T)
    zTrace = st.session_state.stream.select(component='Z').merge()[0]
    eTrace = st.session_state.stream.select(component='E').merge()[0]
    nTrace = st.session_state.stream.select(component='N').merge()[0]
    specKey = 'Z'

    sTime = zTrace.stats.starttime
    xTraceTimes = [np.datetime64((sTime + tT).datetime) for tT in zTrace.times()]

    f, specTimes, psdArr = _generate_stream_specgram(_trace=zTrace)

    st.session_state.stream_spec_freqs = f
    st.session_state.stream_spec_times = specTimes
    st.session_state.psdArr = psdArr

    if f[0] == 0:
        f[0] = f[1]/10 # Fix so bottom number is not 0

    specTimes = list(specTimes)
    specTimes.insert(0, 0)
    timeWindowArr = np.array([np.datetime64((sTime + tT).datetime) for tT in specTimes])
    
    hvsrBand = hvsr_data['hvsr_band']

    minz = np.percentile(st.session_state.psdArr, 1)
    maxz = np.percentile(st.session_state.psdArr, 99)

    hmap = go.Heatmap(z=st.session_state.psdArr,
                x=timeWindowArr[:-1],
                y=f,
                colorscale='Turbo', #opacity=0.8,
                showlegend=False,
                hovertemplate='Time [UTC]: %{x}<br>Frequency [Hz]: %{y:.2f}<br>Spectrogram Magnitude: %{z:.2f}<extra></extra>',
                zmin=minz, zmax=maxz, showscale=False, name=f'{specKey} Component Spectrogram')
    inputFig.add_trace(hmap, row=1, col=1)
    inputFig.update_yaxes(type='log', range=[np.log10(hvsrBand[0]), np.log10(hvsrBand[-1])], row=1, col=1)
    inputFig.update_yaxes(title={'text':f'Spectrogram ({specKey})'}, row=1, col=1)

    # Get Use Array and hvdf
    hvdf, useArrShape = _get_use_array(hvsr_data, f=f, timeWindowArr=timeWindowArr, psdArr=st.session_state.psdArr)

    timelineFig = px.timeline(data_frame=hvdf,
                            x_start='TimesProcessed_Start',
                            x_end='TimesProcessed_End',
                            y=['Used']*hvdf.shape[0],
                            #y="Use",#range_y=[-20, -10],
                            color='Use',
                            color_discrete_map={True: 'rgba(0,255,0,1)',
                                                False: 'rgba(255,0,0,1)'})
    for timelineTrace in timelineFig.data:
        inputFig.add_trace(timelineTrace, row=2, col=1)

    useArr = np.tile(hvdf.Use, (useArrShape, 1))
    useArr = np.where(useArr == True, np.ones_like(useArr), np.zeros_like(useArr)).astype(int)


    specOverlay = go.Heatmap(z=useArr,
                        x=hvdf['TimesProcessed_Start'],
                        y=f,
                        colorscale=[[0, 'rgba(0,0,0,0.8)'], [0.1, 'rgba(255,255,255, 0.00001)'], [1, 'rgba(255,255,255, 0.00001)']],
                        showlegend=False,
                        #hovertemplate='Time [UTC]: %{x}<br>Frequency [Hz]: %{y:.2f}<br>Spectrogram Magnitude: %{z:.2f}<extra></extra>',
                        showscale=False, name=f'{specKey} Component Spectrogram')
    inputFig.add_trace(specOverlay, row=1, col=1)
    
    minTraceData = min(min(zTrace.data), min(eTrace.data), min(nTrace.data))
    maxTraceData = max(max(zTrace.data), max(eTrace.data), max(nTrace.data))

    streamOverlay = go.Heatmap(z=useArr,
                    x=hvdf['TimesProcessed_Start'],
                    y=np.linspace(minTraceData, maxTraceData, useArr.shape[0]),
                    colorscale=[[0, 'rgba(0,0,0,0.8)'], [0.1, 'rgba(255,255,255, 0.00001)'], [1, 'rgba(255,255,255, 0.00001)']],
                    showlegend=False,
                    #hovertemplate='Time [UTC]: %{x}<br>Frequency [Hz]: %{y:.2f}<br>Spectrogram Magnitude: %{z:.2f}<extra></extra>',
                    showscale=False, name=f'{specKey} Component Spectrogram')
    inputFig.add_trace(streamOverlay, row=3, col=1)
    inputFig.add_trace(streamOverlay, row=4, col=1)
    inputFig.add_trace(streamOverlay, row=5, col=1)

    inputFig.update_yaxes(type='log', range=[np.log10(hvsrBand[0]), np.log10(hvsrBand[-1])], row=1, col=1)
    inputFig.update_yaxes(title={'text':f'Spectrogram ({specKey})'}, row=1, col=1)


    # Data traces
    zDataFig = px.scatter(x=xTraceTimes, y=zTrace.data)
    zDataFig.update_traces(mode='markers+lines',
                        marker=dict(size=1, color='rgba(0,0,0,1)'),
                        line=dict(width=1, color='rgba(0,0,0,1)'),
                        selector=dict(mode='markers'))
    for zTrace in zDataFig.data:
        inputFig.add_trace(zTrace, row=3, col=1)


    eDataFig = px.scatter(x=xTraceTimes, y=eTrace.data)
    eDataFig.update_traces(mode='markers+lines',
                        marker=dict(size=1, color='rgba(0,0,255,1)'),
                        line=dict(width=1, color='rgba(0,0,255,1)'),
                        selector=dict(mode='markers'))
    for eTrace in eDataFig.data:
        inputFig.add_trace(eTrace, row=4, col=1)


    nDataFig = px.scatter(x=xTraceTimes, y=nTrace.data)
    nDataFig.update_traces(mode='markers+lines',
                        marker=dict(size=1, color='rgba(255,0,0,1)'),
                        line=dict(width=1, color='rgba(255,0,0,1)'),
                        selector=dict(mode='markers'))
    for nTrace in nDataFig.data:
        inputFig.add_trace(nTrace, row=5, col=1)

    #inputFig.update_yaxes(title='In Use', row=5, col=1)
    #inputFig.update_xaxes(title='Time', row=5, col=1,
    #                      dtick=1000*60,)
    inputFig.update_layout(title_text="Frequency and Data values over time", 
                        height=650, showlegend=False)

    inputFig.update_xaxes(type='date', range=[xTraceTimes[0], xTraceTimes[-1]])

    st.session_state.input_fig = inputFig

    return inputFig


def update_from_data_selection():
    st.toast("Updating H/V Curve statistics")

    if 'PPSDStatus' in st.session_state.hvsr_data.ProcessingStatus and st.session_state.hvsr_data.ProcessingStatus['PPSDStatus']:
        gpsd_kwargs = {k: v for k, v in st.session_state.items() if k in tuple(inspect.signature(sprit_hvsr.generate_psds).parameters.keys()) and k != 'hvsr_data'}
        st.session_state.hvsr_data = sprit_hvsr.generate_psds(hvsr_data=st.session_state.hvsr_data, **gpsd_kwargs)
        

    prochvsr_kwargs = {k: v for k, v in st.session_state.items() if k in tuple(inspect.signature(sprit_hvsr.process_hvsr).parameters.keys()) and k != 'hvsr_data'}
    checkPeaks_kwargs = {k: v for k, v in st.session_state.items() if k in tuple(inspect.signature(sprit_hvsr.check_peaks).parameters.keys()) and k != 'hvsr_data'}
    getRep_kwargs = {k: v for k, v in st.session_state.items() if k in tuple(inspect.signature(sprit_hvsr.get_report).parameters.keys()) and k != 'hvsr_data'}

    st.session_state.hvsr_data = sprit_hvsr.process_hvsr(hvsr_data=st.session_state.hvsr_data, **prochvsr_kwargs)
    st.session_state.hvsr_data = sprit_hvsr.check_peaks(hvsr_data=st.session_state.hvsr_data, **checkPeaks_kwargs)
    st.session_state.hvsr_data = sprit_hvsr.get_report(hvsr_results=st.session_state.hvsr_data, **getRep_kwargs)

    display_results()


def update_data():
    st.session_state.data_chart_event = st.session_state.data_plot
    specKey = 'Z'
    hvsrBand = st.session_state.hvsr_data.hvsr_band
    # Still figuring stuff out
    
    # This seems to work well at the moment
    windows = []
    if len(st.session_state.data_chart_event['selection']['box']) > 0:
        esb = st.session_state.data_chart_event['selection']['box']
        for b in esb:
            if b['x'][0] > b['x'][1]:
                windows.append((b['x'][1], b['x'][0]))
            else:
                windows.append((b['x'][0], b['x'][1]))

    # Reset the variables (but which one(s)?)
    st.session_state.data_chart_event = {"selection":{"points":[],
                                         "point_indices":[],
                                         'box':[],
                                         'lasso':[]}}

    if 'x_windows_out' not in st.session_state.hvsr_data.keys():
        st.session_state.hvsr_data['x_windows_out'] = []
    
    st.session_state.hvsr_data['x_windows_out'].append(windows)

    # Convert times to obspy.UTCDateTime
    utcdtWin = []
    for currWin in windows:
        for pdtimestamp in currWin:
            utcdtWin.append(UTCDateTime(pdtimestamp))
    
    # Get 
    stream1 = st.session_state.stream_edited.copy()
    stream2 = st.session_state.stream_edited.copy()

    stream1 = stream1.merge()
    stream2 = stream2.merge()
    
    # Trim data
    if st.session_state.input_selection_mode == 'Add':
        stream1.trim(starttime=stream1[0].stats.starttime, endtime=utcdtWin[0])
        stream2.trim(starttime=utcdtWin[1], endtime=stream2[0].stats.endtime)

    # Merge data back
    newStream = (stream1 + stream2).merge()
    st.session_state.hvsr_data['stream_edited'] = newStream
    st.session_state.stream_edited = newStream

    # Use edited data to update location of bars


    # Update useArr
    hvdf, useArrShape = _get_use_array(hvsr_data=st.session_state.hvsr_data,
                                       f=st.session_state.stream_spec_freqs,
                                       timeWindowArr=st.session_state.stream_spec_times,
                                       psdArr=st.session_state.psdArr)
    
    useArr = np.tile(hvdf.Use, (useArrShape, 1))
    useArr = np.where(useArr == True, np.ones_like(useArr), np.zeros_like(useArr)).astype(int)

    newSpecOverlay = go.Heatmap(z = useArr,
                                x = hvdf['TimesProcessed_Start'],
                                y=st.session_state.stream_spec_freqs,
                                colorscale=[[0, 'rgba(0,0,0,0.8)'], [0.1, 'rgba(255,255,255, 0.00001)'], [1, 'rgba(255,255,255, 0.00001)']],
                                showlegend=False,
                                #hovertemplate='Time [UTC]: %{x}<br>Frequency [Hz]: %{y:.2f}<br>Spectrogram Magnitude: %{z:.2f}<extra></extra>',
                                showscale=False,
                                )

    st.session_state.input_fig.add_trace(newSpecOverlay, row=1, col=1)
    st.session_state.input_fig.update_yaxes(type='log', range=[np.log10(hvsrBand[0]), np.log10(hvsrBand[-1])], row=1, col=1)
    st.session_state.input_fig.update_yaxes(title={'text':f'Spectrogram ({specKey})'}, row=1, col=1)
    st.session_state.input_fig.update_layout(showlegend=False)

    display_results()


def update_selection_type():
    st.session_state.input_selection_mode = st.session_state.input_selection_toggle


def display_results():
    # Set up container for output data
    setup_main_container(do_setup_tabs=True)

    # Input data
    st.session_state.input_fig = make_input_fig()
    st.session_state.data_chart_event = st.session_state.inputTab.plotly_chart(st.session_state.input_fig,
                                        on_select=update_data, key='data_plot', 
                                        selection_mode='box', use_container_width=True, theme='streamlit')

    st.session_state.inputTab.write("Select any time window with the Box Selector (see the top right of chart) to remove it from analysis.")
    st.session_state.input_selection_mode = st.session_state.inputTab.pills('Window Selection Mode', options=['Add', "Delete"], key='input_selection_toggle', 
                                                 default='Add', on_change=update_selection_type, disabled=True, 
                                                 help='If in "Add" mode, windows for removal will be added at your selection. If "Delete" mode, these windows will be deleted. Currently only "Add" supported')


    write_to_info_tab(st.session_state.infoTab)
    #st.session_state.inputTab.plotly_chart(st.session_state.hvsr_data['InputPlot'], use_container_width=True)
    outlier_plot_in_tab()
    #outlierEvent = outlierTab.plotly_chart(st.session_state.hvsr_data['OutlierPlot'], use_container_width=True)
    st.session_state.plotReportTab.plotly_chart(st.session_state.hvsr_data['HV_Plot'], use_container_width=True)
    st.session_state.csvReportTab.dataframe(data=st.session_state.hvsr_data['Table_Report'])
    st.session_state.strReportTab.code(st.session_state.hvsr_data['Print_Report'], language=None)

    # Download Buttons
    st.session_state.dlText.text("Download Results: ")

    # Set up variables for download section
    hvData = st.session_state.hvsr_data
    hvID = ''
    if hasattr(hvData, 'hvsr_id'):
        hvID = hvData['hvsr_id']

    nowTimeStr = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # PDF Report download
    @st.cache_data
    def convert_pdf_for_download(_hv_data):
        pdfPath = sprit._generate_pdf_report(_hv_data, return_pdf_path=True)
        with open(pdfPath, "rb") as pdf_file:
            PDFbyte = pdf_file.read()
        return PDFbyte
    
    pdf_byte = convert_pdf_for_download(hvData)

    st.session_state.dlPDFReport.download_button(label="Report (.pdf)",
                data=pdf_byte,
                file_name=f"{hvData.site}_Report_{hvID}_{nowTimeStr}.pdf",
                mime='application/octet-stream',
                icon=":material/summarize:")

    # Data Stream
    strm = io.BytesIO()
    @st.cache_data
    def convert_stream_for_download(_stream):
        _stream.write(strm, format='MSEED')
        return strm.getvalue()
    streamBytes = convert_stream_for_download(hvData.stream)

    st.session_state.dlStream.download_button(
        label='Data (.mseed)',
        data=streamBytes,
        file_name=f"{hvData.site}_DataStream_{hvID}_{nowTimeStr}.mseed",
        icon=":material/graphic_eq:"
    )

    # Table download
    @st.cache_data
    def convert_table_for_download(df):
        return df.to_csv().encode("utf-8")

    csv = convert_table_for_download(st.session_state.hvsr_data['Table_Report'])

    st.session_state.dlTable.download_button(
        label="Table (.csv)",
        data=csv,
        file_name=f"{hvData.site}_TableReport_{hvID}_{nowTimeStr}.csv",
        mime="text/csv",
        icon=":material/table:",
    )

    # Plot
    img = io.BytesIO()
    if st.session_state.plot_engine == 'Matplotlib':
        hvData['HV_Plot'].savefig(img, format='png')
    else:
        img = hvData['HV_Plot'].to_image(format='png')
    
    st.session_state.dlPlot.download_button(
        label="Plot (.png)",
        data=img,
        file_name=f"{hvData.site}_HV-Plot_{hvID}_{nowTimeStr}.png",
        mime="image/png",
        icon=":material/analytics:"
        )


    # HVSR File
    try:
        hvsrPickle = pickle.dumps(st.session_state.hvsr_data)

        st.session_state.dlHVSR.download_button(
            label="Pickled (.hvsr)",
            data=hvsrPickle,
            file_name=f"{hvData.site}_Pickled_{hvID}_{nowTimeStr}.hvsr",
            icon=":material/database:")
    except Exception as e:
        print(e)
        st.session_state.dlHVSR.download_button(
            label=".hvsr not available",
            data='HVSR Data ',
            file_name=f"{hvData.site}_Pickled_{hvID}_{nowTimeStr}.hvsr",
            disabled=True,
            icon=":material/database:")


def write_to_info_tab(infoTab):
    with infoTab:
        st.markdown("# Processing Parameters Used")
        for fun, kwargDict in funList:
            funSig = inspect.signature(fun)
            # excludeKeys = ['params', 'hvsr_data', 'hvsr_results']
            funMD = ""
            for arg in funSig.parameters.keys():
                if arg in st.session_state.keys():
                    funMD = funMD + f"""\n    * {arg} = {st.session_state[arg]}"""

            with st.expander(f"{fun.__name__}"):
                st.write(funMD, unsafe_allow_html=True)


def update_from_outlier_selection():
    """This is intended as a callback for updating the main results tab, etc. after updating outlier curves"""
    
    st.toast("Updating H/V Curve statistics")
    prochvsr_kwargs = {k: v for k, v in st.session_state.items() if k in tuple(inspect.signature(sprit_hvsr.process_hvsr).parameters.keys()) and k != 'hvsr_data'}
    checkPeaks_kwargs = {k: v for k, v in st.session_state.items() if k in tuple(inspect.signature(sprit_hvsr.check_peaks).parameters.keys()) and k != 'hvsr_data'}
    getRep_kwargs = {k: v for k, v in st.session_state.items() if k in tuple(inspect.signature(sprit_hvsr.get_report).parameters.keys()) and k != 'hvsr_data'}

    st.session_state.hvsr_data = sprit_hvsr.process_hvsr(hvsr_data=st.session_state.hvsr_data, **prochvsr_kwargs)
    st.session_state.hvsr_data = sprit_hvsr.check_peaks(hvsr_data=st.session_state.hvsr_data, **checkPeaks_kwargs)
    st.session_state.hvsr_data = sprit_hvsr.get_report(hvsr_results=st.session_state.hvsr_data, **getRep_kwargs)

    display_results()
    #write_to_info_tab(infoTab)
    
    #inputTab.plotly_chart(st.session_state.hvsr_data['InputPlot'], use_container_width=True)
    #outlier_plot_in_tab()
    #plotReportTab.plotly_chart(outlierFig, on_select=update_outlier, key='outlier_plot', use_container_width=True, theme='streamlit')
    #csvReportTab.dataframe(data=st.session_state.hvsr_data['Table_Report'])
    #strReportTab.text(st.session_state.hvsr_data['Print_Report'])

    #st.session_state.outlierTab.write('Navigate to the Results tab to see updated results')


def update_outlier():
    hvDF = st.session_state.hvsr_data['hvsr_windows_df']
    
    st.session_state.outlier_chart_event = st.session_state.outlier_plot
    curves2Remove = np.unique([p['curve_number'] for p in st.session_state.outlier_chart_event['selection']['points']])
    st.session_state.outlier_curves_to_remove = list(curves2Remove)

    if len(st.session_state.outlier_curves_to_remove) > 0:
        
        outlierMsgList = []
        outlierMsgCols = ['Window Number', "Window Start Time"]
        for remCurve in st.session_state.outlier_curves_to_remove:
            currInd = hvDF.iloc[remCurve].name
            outlierMsgList.append([remCurve, currInd])
            hvDF.loc[currInd, "Use"] = False

        statusMsg = "Removing specified outlier curve"
        if len(st.session_state.outlier_curves_to_remove) != 1:
            statusMsg += 's'

        #st.toast(statusMsg)
        statusCol, updateCol = st.columns([0.8, 0.2])
        with statusCol.status(statusMsg):
            st.dataframe(pd.DataFrame(outlierMsgList, columns=outlierMsgCols))
        updateCol.button("Rerun results statistics", on_click=update_from_outlier_selection,
                         type='primary', icon=":material/update:")
    display_results()


def outlier_plot_in_tab():
    hvDF = st.session_state.hvsr_data['hvsr_windows_df']
    x_data = st.session_state.hvsr_data['x_freqs']['Z'][:-1]
    
    no_subplots = 1
    outlierFig = subplots.make_subplots(rows=no_subplots, cols=1,
                                        shared_xaxes=True, horizontal_spacing=0.01,
                                        vertical_spacing=0.1)

    scatterFig = px.scatter()
    scatter_traces = []
    line_traces = []


    for row, hvsr_data in enumerate(hvDF['HV_Curves']):
        currInd = hvDF.iloc[row].name
        if hvDF.loc[currInd, 'Use']:  
            scatterArray = np.array(list(hvsr_data)[::5])
            x_data_Scatter = np.array(list(x_data)[::5])
            currFig = px.scatter(x=x_data_Scatter, y=scatterArray)
            currFig.update_traces(mode='markers+lines',
                            marker=dict(size=1, color='rgba(0,0,0,0.1)'),
                            line=dict(width=1, color='rgba(0,0,0,0.1)'),
                            selector=dict(mode='markers'))
            
            scatter_traces.append(currFig)

        else:
            scatterArray = np.array(list(hvsr_data)[::5])
            x_data_Scatter = np.array(list(x_data)[::5])
            currFig = px.scatter(x=x_data_Scatter, y=scatterArray,
                                opacity=0.5)
            currFig.update_traces(mode='markers+lines',
                                marker=dict(size=1, color='rgba(195,87,0,0.4)'),
                                line=dict(width=1, color='rgba(195,87,0,0.4)'),
                                selector=dict(mode='markers'))
            scatter_traces.append(currFig)


    # Add median line
    medArr = np.nanmedian(np.stack(hvDF['HV_Curves'][hvDF['Use']]), axis=0)
    scatterArray = np.array(list(medArr)[::10])
    x_data_Scatter = np.array(list(x_data)[::10])
    currFig = px.line(x=x_data_Scatter, y=scatterArray,
                    color_discrete_sequence=['red'])
    currFig.update_traces(line=dict(width=3, color='black'))
    scatter_traces.append(currFig)

    for tr in scatter_traces:
        for trace in tr.data:
            outlierFig.add_traces(trace, rows=1, cols=1)


    outlierFig.update_xaxes(title='Frequency [Hz]', type="log", row=1, col=1)
    outlierFig.update_yaxes(title='H/V Ratio', row=1, col=1)
    outlierFig.update_layout(title_text="H/V Curve Outlier Display & Selection")

    st.session_state.outlierTab.write("Select any curve(s) with your cursor or the Box or Lasso Selectors (hover over the top right of chart) to remove from the statistics and analysis of results.")
    # Output figure to correct tab
    st.session_state.outlierTab.plotly_chart(outlierFig, 
                            on_select=update_outlier, 
                            key='outlier_plot', 
                            use_container_width=True, 
                            theme='streamlit') 

def write_to_outlierTab():
    pass


# Initial setup
setup_session_state()


# DEFINE SIDEBAR
if VERBOSE:
    print('About to start setting up sidebar, session state length: ', len(st.session_state.keys()))
    print_param(PARAM2PRINT)

# Set up sidebar
with st.sidebar:
    if VERBOSE:
        print('Start setting up sidebar, session state length: ', len(st.session_state.keys()))
        print_param(PARAM2PRINT)

    st.header('SpRIT HVSR', divider='rainbow')
    inputDataCol, sourceCol = st.columns([0.7, 0.3])
    datapathInput = inputDataCol.text_input("Datapath", key='input_data', 
                                        placeholder='Enter data filepath', 
                                        help="Enter a filepath to be read by obspy.read(). On the web app, a temporary copy of this file will be made.")    
    sourceCol.selectbox('Source', options=['File', 'Raw', 'Directory', "Batch"], index=0, key='source',
                        help='File: a single file for analysis. All the rest are experimental in the web app. Raw is used with Raspberry Shake data to read native file structure. Directory gets all relevant files in a directory. Batch is for loading a .csv file for batch analysis.')

    #st.file_uploader('Upload data file(s)', type=OBSPYFORMATS, accept_multiple_files=True, key='datapath_uploader', on_change=on_file_upload)
    with st.expander("Click to access data uploader"):
        st.file_uploader("Upload data file(s)", type=OBSPYFORMATS, accept_multiple_files=False, key='datapath_uploader', on_change=on_file_upload)

    bottom_container = st.container()

    # Create top menu
    with bottom_container:
        resetCol, readCol, runCol = st.columns([0.3, 0.3, 0.4])

        #resetCol.button('Reset', disabled=True, use_container_width=True)
        #readCol.button('Read', use_container_width=True, args=((True, )))
        
        runLabel = 'Run'
        if st.session_state.input_data == '':
            runLabel = 'Demo Run'

        resetCol.button('Reset', disabled=False, use_container_width=True,
                         on_click=on_reset, key='reset_button')
        readCol.button('Read', disabled=False, use_container_width=True,
                        on_click=on_read_data, key='read_button')
        runCol.button('Run', type='primary', use_container_width=True,
                       on_click=on_run_data, key='run_button')
    

    if VERBOSE:
        print('Done setting up bottom container, session state length: ', len(st.session_state.keys()))
        print_param(PARAM2PRINT)

    st.header('Settings')
    mainSettings = st.container()

    with mainSettings:

        siteNameCol, instCol = st.columns([0.33333, 0.33333])
        siteNameCol.text_input("Site Name", placeholder='HVSR Site', on_change=text_change, key='site')
        #instCol.text_input('Instrument', help='Raspberry Shake and Tromino are currently the only values with special treatment. If a filepath, can use a .inst instrument file (json format)', key='instrument')
        instCol.selectbox('Instrument', key='instrument',
                        options=['Seismometer', 'Raspberry Shake', 'Tromino Yellow', 'Tromino Blue'], 
                        help='Some instruments require special inputs to read in the data correctly. If not one of the instruments listed, or if reading in an obspy-supported file directly, leave as N/A')

        xCoordCol, yCoordCol, inCRSCol = st.columns([0.3333, 0.3333, 0.33333])
        xCoordCol.text_input('X Coordinate', help='i.e., Longitude or Easting', key='xcoord')
        yCoordCol.text_input('Y Coordinate', help='i.e., Latitude or Northing', key='ycoord')
        inCRSCol.text_input('CRS', help='By default, "EPSG:4326". Can be EPSG code or anything accepted by pyproj.CRS.from_user_input()', key='input_crs')        
        
        zCoordCol, elevUnitCol = st.columns([0.666, 0.333])
        zCoordCol.text_input('Z Coordinate (elevation)', help='i.e., Elevation', key='elevation')
        elevUnitCol.selectbox('Elev. (Z) Unit', options=['meters', 'feet'], key='elev_unit', help='i.e., Elevation unit')

        pfrDef = tuple(inspect.signature(sprit.input_params).parameters['peak_freq_range'].default)
        #if "peak_freq_range" not in st.session_state:
        #    st.session_state.peak_freq_range = tuple(pfrDef)
        
        st.session_state.peak_freq_range = st.select_slider('Peak Frequency Range', options=bandVals,
                         value=pfrDef,
                         #key='peak_freq_range'
                         )


    st.header('Additional Settings', divider='gray')
    with st.expander('Expand to modify additional settings'):
        if VERBOSE:
            print('Setting up sidebar expander, session state length: ', len(st.session_state.keys()))
            print_param(PARAM2PRINT)

        ipSetTab, fdSetTab, azSetTab, rmnocSetTab, gpSetTab, phvsrSetTab, plotSetTab = st.tabs(['Input', 'Data', "Azimuths", "Noise", 'PPSDs', 'H/V', 'Plot'])
        #@st.experimental_dialog("Update Input Parameters", width='large')
        #def open_ip_dialog():
        with ipSetTab:
            if VERBOSE:
                print('Setting up input tab, session state length: ', len(st.session_state.keys()))

            #with st.expander('Primary Input Parameters', expanded=True):
            #if "hvsr_band" not in st.session_state:
            #    st.session_state.hvsr_band = [0.4, 40]
            st.session_state.hvsr_band = st.select_slider('HVSR Band', options=bandVals, #key='hvsr_band',
                            value=st.session_state.hvsr_band
                            )

            #st.text_input('Instrument', help='Raspberry Shake and Tromino are currently the only values with special treatment. If a filepath, can use a .inst instrument file (json format)', key='instrument')
            #st.select_slider('HVSR Band',  value=st.session_state.hvsr_band, options=bandVals, key='hvsr_band')
            #st.select_slider('Peak Frequency Range',  value=st.session_state.peak_freq_range, options=bandVals, key='peak_freq_range')

            #with st.expander('Acquisition Date/Time'):
            st.date_input('Acquisition Date', format='YYYY-MM-DD', key='acq_date')
            st.time_input('Start time', step=60, key='starttime')
            st.time_input('End time', step=60, key='endtime')

            tZoneList=list(zoneinfo.available_timezones())
            tZoneList.sort()
            tZoneList.insert(0, "localtime")
            tZoneList.insert(0, "US/Pacific")
            tZoneList.insert(0, "US/Mountain")
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
            #st.text_input('X Coordinate', help='i.e., Longitude or Easting', key='xcoord')
            #st.text_input('Y Coordinate', help='i.e., Latitude or Northing', key='ycoord')
            #st.text_input('Z Coordinate', help='i.e., Elevation', key='elevation')
            #st.session_state.elev_unit = st.selectbox('Z Unit', options=['m', 'ft'], help='i.e., Elevation unit')
            #st.number_input('Depth', help='i.e., Depth of measurement below ground surface (not currently used)', key='depth')

            st.text_input('CRS for Export', help='Can be EPSG code or anything accepted by pyproj.CRS.from_user_input()', key='output_crs')
            if VERBOSE:
                print_param(PARAM2PRINT)

            st.text_input('Metadata Filepath', help='Filepath to instrument response file', key='metapath')


        #@st.experimental_dialog("Update Parameters to Fetch Data", width='large')
        #def open_fd_dialog():
        with fdSetTab:
            if VERBOSE:
                print('Setting up fd tab, session state length: ', len(st.session_state.keys()))
            #source: str = 'file',
            st.text_input('Data export directory', help='Directory for exporting raw/trimmed data', key='data_export_dir')
            st.selectbox('Data export format', options=OBSPYFORMATS, index=11, key='data_export_format')

            # Detrending options
            st.selectbox('Detrend Type', options=['None', 'Simple', 'Linear', 'Constant/Demean', 'Polynomial', 'Spline'], index=5, 
                        help='Detrend Type use by `type` parameter of obspy.trace.Trace.detrend()', key='detrend')
            st.text_input('Detrend options', value='order=2', 
                        help="Value(s) to pass to the **options argument of obspy.trace.Trace.detrend()", 
                        key='detrend_options')

            # Filter options
            st.selectbox('Filter Type', options=['None', 'bandpass', 'bandstop', 
                                                'lowpass', 'highpass', 
                                                'lowpass_cheby_2', 'lowpass_fir', 'remez_fir'], 
                        index=0, 
                        help='Detrend Type use by `type` parameter of obspy.trace.Trace.filter()', key='filter')
            
            st.text_input('Filter options',
                        help="Value(s) to pass to the **options argument of obspy.trace.Trace.filter()", 
                        key='filter_options')

            if VERBOSE:
                print_param(PARAM2PRINT)

        with azSetTab:
            if VERBOSE:
                print('Setting up az tab, session state length: ', len(st.session_state.keys()))

            st.toggle("Calculate Azimuths", value=False,
                      help='Whether to calculate azimuths for data.',
                      key='azimuth_calculation')
            
            az_disabled = True
            if hasattr(st.session_state, 'azimuth_calculation'):
                az_disabled = not st.session_state.azimuth_calculation
        
            st.selectbox('Azimuth type', disabled=az_disabled, options=['Multiple', 'Single'], index=0, key='azimuth_type')

            azAngCol, azUnitCol = st.columns([0.7,0.3])
            azAngCol.number_input("Azimuth angle", value=30, key='azimuth_angle', disabled=az_disabled)
            azUnitCol.selectbox('Azimuth unit', options=['°', 'rad'], index=0, key='azimuth_unit', disabled=az_disabled)

            if VERBOSE:
                print_param(PARAM2PRINT)
        
        #@st.experimental_dialog("Update Parameters to Remove Noise and Outlier Curves", width='large')
        #def open_outliernoise_dialog():
        with rmnocSetTab:
            if VERBOSE:
                print('Setting up noise tab, session state length: ', len(st.session_state.keys()))
            # Set up toggles and options
            remNoiseCol, rawNoiseCol = st.columns([0.55, 0.45])
            remNoiseCol.toggle("Remove Noise", value=False, 
                        help='Whether to remove noise from input data.', key='noise_removal')
            noiseRemDisabled = not st.session_state.noise_removal

            rawNoiseCol.toggle("Raw data", disabled=noiseRemDisabled, help='Whether to use the raw input data to remove noise.', key='remove_raw_noise')

            remNoisePopover = st.popover('Remove Noise options', disabled=noiseRemDisabled, use_container_width=True)
            with remNoisePopover:
                # Auto noise
                st.toggle("Auto Noise Removal", value=False, disabled=noiseRemDisabled, 
                            help='Whether to remove noise from input data.', key='auto_noise_removal')
                            
                st.divider()

                do_stalta = False
                do_sat = False
                do_noise = False
                do_stdev = False
                do_warm = False
                do_cool = False
                do_outCurve = False

                doNoiseRemList = [do_stalta, do_sat, do_noise, do_stdev, do_warm, do_cool]
                autoRemList = [do_stdev, do_sat]

                if not st.session_state.noise_removal:
                    for doNR in doNoiseRemList:
                        doNR = False

                if st.session_state.auto_noise_removal and not any(autoRemList):
                    do_stdev = True
                    do_sat = True

                # Standard devation ratio
                st.toggle("StDev Ratio Noise Detection", value=do_stdev, disabled=noiseRemDisabled, 
                            help='Whether to remove noise from input data.', key='stdev_noise_removal')
                stDevDisabled = (not st.session_state.stdev_noise_removal) or noiseRemDisabled
                #std_ratio_thresh=2.0, std_window_size=20.0, min_std_win=5.0,
                st.number_input('Moving StDev. Threshold', min_value=0.0, max_value=100.0, step=0.1, value=2.0,
                                help='The threshold value of StDev_Moving / StDev_Total to use as a removal threshold',
                                format="%.1f", disabled=stDevDisabled, key='std_ratio_thresh')
                mvStDWinCol, minStDWinCol = st.columns([0.5, 0.5])
                mvStDWinCol.number_input('Moving StDev. Win Size (samples)', value=20, 
                                help='The size of the window to use to calculate the rolling standard deviation',
                                disabled=stDevDisabled, step=1, key='std_window_size')
                minStDWinCol.number_input('Min. Win. Size (samples)', value=5, 
                                help="The minimum number of samples in a row that exceed the ratio threshold for that window to be removed",
                                disabled=stDevDisabled, step=1, key='min_std_win')

                # Saturation threshold
                st.toggle("Saturation Threshold Noise Detection", value=do_sat, disabled=noiseRemDisabled, 
                            help='Whether to remove noise from input data.', key='sat_noise_removal')
                satRemDisabled = (not st.session_state.sat_noise_removal) or noiseRemDisabled


                st.number_input('Saturation Percent', value=0.99, min_value=0.0, max_value=1.0, step=0.01,
                                format="%.2f", disabled=satRemDisabled, key='sat_percent')

                # STALTA
                st.toggle("STALTA Noise Detection", value=do_stalta, disabled=noiseRemDisabled, 
                            help='Whether to remove noise from input data.', key='stalta_noise_removal')
                staltaDisabled = (not st.session_state.stalta_noise_removal) or noiseRemDisabled

                staCol, ltaCol = st.columns([0.5,0.5])
                staCol.number_input('Short Term Average (STA)', step=0.5, value=2.0,
                                help='Length of moving window (in seconds) for calculating STA average',
                                disabled=staltaDisabled, key='sta')
                ltaCol.number_input('Long Term Average (LTA)', value=30.0,
                                help='Length of moving window (in seconds) for calculating LTA average',
                                disabled=staltaDisabled, step=0.5, key='lta')
                staltaVals = np.arange(0, 51).tolist()
                st.select_slider('STA/LTA Thresholds', disabled=staltaDisabled, 
                                help='Trigger thresholds for STA/LTA calculation',
                                value=st.session_state.stalta_thresh, options=staltaVals, key='stalta_thresh')

                # Noise threshold
                st.toggle("Noise Threshold Noise Detection", value=do_noise, disabled=noiseRemDisabled, 
                            help='Whether to remove noise from input data.', key='noise_thresh_noise_removal')
                noiseDisabled = (not st.session_state.noise_thresh_noise_removal) or noiseRemDisabled

                st.number_input('Noise Percent', value=0.8, min_value=0.0, max_value=1.0, step=0.05, 
                                format="%.2f", disabled=noiseDisabled, key='noise_percent')

                st.number_input('Minimum Window Size (samples)', value=1, step=1,
                                disabled=noiseDisabled, key='min_win_size')


                # Warmup
                st.toggle("Warmup Time Removal", value=do_warm, disabled=noiseRemDisabled, 
                            help='Whether to remove noise from input data.', key='warmup_noise_removal')
                warmupDisabled = (not st.session_state.warmup_noise_removal) or noiseRemDisabled

                st.number_input('Warmup Time (seconds)', disabled=warmupDisabled, step=1, key='warmup_time')

                # Cooldown
                st.toggle("Cooldown Time Removal", value=do_cool, disabled=noiseRemDisabled, 
                            help='Whether to remove noise from input data.', key='cooldown_noise_removal')
                cooldownDisabled = (not st.session_state.cooldown_noise_removal) or noiseRemDisabled

                st.number_input('Cooldown Time (seconds)', disabled=cooldownDisabled, step=1, key='cooldown_time')


            st.toggle("Remove Outlier Curves", value=False,
                        help='Whether to remove outlier curves from input data.', key='outlier_curves_removal')
            outlierCurveDisabled = not st.session_state.outlier_curves_removal

            # Outlier curves
            remCurvePopover = st.popover('Remove Outlier Curve Options', disabled=outlierCurveDisabled, use_container_width=True)
            with remCurvePopover:
                st.number_input("Outlier Threshold", disabled=outlierCurveDisabled, value=98, key='rmse_thresh')
                st.radio('Threshold type', horizontal=True, disabled=outlierCurveDisabled, options=['Percentile', 'Value'], key='threshRadio')
                st.session_state.use_percentile = st.session_state.threshRadio=='Percentile'
                st.radio('Threshold curve', horizontal=True, disabled=outlierCurveDisabled, options=['HV Curve', 'Component Curves'], key='curveRadio')
                st.session_state.use_hv_curve = (st.session_state.curveRadio=='HV Curve')



            #noise_rem_method_list = ['None', 'Auto', 'Manual', 'Stalta', 'Saturation Threshold', 'Noise Threshold', 'Warmup', 'Cooldown', 'Buffer']
            #st.multiselect("Noise Removal Method",
            #            options=,
            #            key='remove_method')

            if VERBOSE:
                print_param(PARAM2PRINT)

        #@st.experimental_dialog("Update Parameters to Generate PPSDs", width='large')
        #def open_ppsd_dialog():
        with gpSetTab:
            if VERBOSE:
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
            if VERBOSE:
                print_param(PARAM2PRINT)

        #@st.experimental_dialog("Update Parameters to Process HVSR", width='large')
        #def open_processHVSR_dialog():
        with phvsrSetTab:
            if VERBOSE:
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
            if VERBOSE:
                print_param(PARAM2PRINT)

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
            if VERBOSE:
                print('Setting up plot tab, session state length: ', len(st.session_state.keys()))

            st.selectbox("Plot Engine", options=['Plotly', "Matplotlib"], key='plot_engine', disabled=True, help="Currently, only plotly is supported.")
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
            st.multiselect('Items to plot', options=['Peak Frequency', 'Annotation'], key='specPlotStr', on_change=update_plot_string,
                                            default=["Peak Frequency", "Annotation"])
            if VERBOSE:
                print_param(PARAM2PRINT)

    if VERBOSE:
        print('Done setting up sidebar, session state length: ', len(st.session_state.keys()))
        print('Done setting up everything (end of main), session state length: ', len(st.session_state.keys()))
        print_param(param2print)

#if __name__ == "__main__":
#    main()

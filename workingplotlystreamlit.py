import inspect

import plotly.express as px
from plotly import subplots
import streamlit as st
import numpy as np
from obspy  import UTCDateTime
import pandas as pd
import plotly.graph_objects as go
from scipy import signal

import sprit.sprit_hvsr as sprit

st.set_page_config(layout="wide")

@st.cache_data
def run_data():
    hvsr_data = sprit.run('sample', suppress_report_outputs=True)
    print('hvsrun')
    return hvsr_data
hvsr_data = run_data()

if not hasattr(st.session_state, 'hvsr_data'):
    st.session_state.hvsr_data = hvsr_data
    st.session_state.stream = st.session_state.hvsr_data.stream
    st.session_state.stream_edited = st.session_state.hvsr_data.stream_edited

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

    # Windows PSD and Used
    #psdArr = np.flip(hvsr_data.ppsds["Z"]['psd_values'].T)
    zTrace = st.session_state.stream.select(component='Z').merge()[0]
    eTrace = st.session_state.stream.select(component='E').merge()[0]
    nTrace = st.session_state.stream.select(component='N').merge()[0]
    specKey='Z'

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
                            y='Use',
                            #y="Use",#range_y=[-20, -10],
                            color='Use',
                            color_discrete_map={True: 'rgba(0,255,0,1)',
                                                False: 'rgba(255,0,0,1)'})
    for timelineTrace in timelineFig.data:
        inputFig.add_trace(timelineTrace, row=2, col=1)

    #useColInd = list(hvdf.columns).index('Use')
    ##hvdf.iloc[22:55, useColInd] = False

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
                        height=800)

    inputFig.update_xaxes(type='date', range=[xTraceTimes[0], xTraceTimes[-1]])

    st.session_state.inputFig = inputFig

    return inputFig


def update_data():
    st.session_state.data_chart_event = st.session_state.data_plot
    specKey = 'Z'
    hvsrBand = st.session_state.hvsr_data.hvsr_band
    # Still figuring stuff out
    
    # This seems to work well at the moment
    windows=[]
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

    #Convert times to obspy.UTCDateTime
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
    inputFig.add_trace(newSpecOverlay, row=1, col=1)
    inputFig.update_yaxes(type='log', range=[np.log10(hvsrBand[0]), np.log10(hvsrBand[-1])], row=1, col=1)
    inputFig.update_yaxes(title={'text':f'Spectrogram ({specKey})'}, row=1, col=1)


def update_selection_type():
    st.session_state.input_selection_mode = st.session_state.input_selection_toggle

inputFig = make_input_fig()
event = st.plotly_chart(inputFig, on_select=update_data, key='data_plot', selection_mode='box', use_container_width=True, theme='streamlit')
st.write("Select any time window with the Box Selector (see the top right of chart) to remove it from analysis.")
st.session_state.input_selection_mode = st.pills('Window Selection Mode', options=['Add', "Delete"], key='input_selection_toggle', 
                                                 default='Add', on_change=update_selection_type, disabled=True, 
                                                 help='If in "Add" mode, windows for removal will be added at your selection. If "Delete" mode, these windows will be deleted. Currently only "Add" supported')

st.session_state.event = event

#def update_from_outlier_selection():
#    prochvsr_kwargs = {k: v for k, v in st.session_state.items() if k in tuple(inspect.signature(sprit.process_hvsr).parameters.keys()) and k != 'hvsr_data'}
#    checkPeaks_kwargs = {k: v for k, v in st.session_state.items() if k in tuple(inspect.signature(sprit.process_hvsr).parameters.keys()) and k != 'hvsr_data'}
#    getRep_kwargs = {k: v for k, v in st.session_state.items() if k in tuple(inspect.signature(sprit.process_hvsr).parameters.keys()) and k != 'hvsr_data'}

#    st.session_state.hvsr_data = sprit.process_hvsr(hvsr_data=st.session_state.hvsr_data, **prochvsr_kwargs)
#    st.session_state.hvsr_data = sprit.check_peaks(hvsr_results=st.session_state.hvsr_data, **checkPeaks_kwargs)
#    st.session_state.hvsr_data = sprit.get_report(hvsr_results=st.session_state.hvsr_data, **getRep_kwargs)

#    write_to_info_tab(infoTab)
    
#    inputTab.plotly_chart(st.session_state.hvsr_data['InputPlot'], use_container_width=True)
#    outlierEvent = outlierTab.plotly_chart(st.session_state.hvsr_data['OutlierPlot'], use_container_width=True)
#    plotReportTab.plotly_chart(inputFig, on_select=update_outlier, key='outlier_plot', use_container_width=True, theme='streamlit')
#    csvReportTab.dataframe(data=st.session_state.hvsr_data['CSV_Report'])
#    strReportTab.text(st.session_state.hvsr_data['Print_Report'])


#st.button('Update H/V Curve Analysis', key='update_from_outliers', type='primary', icon=":material/update:")


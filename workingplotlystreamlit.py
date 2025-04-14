import sprit.sprit_hvsr as sprit
import inspect

import plotly.express as px
from plotly import subplots
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import signal

st.set_page_config(layout="wide")

@st.cache_data
def run_data():
    hvsr_data = sprit.run('sample', suppress_report_outputs=True)
    print('hvsrun')
    return hvsr_data
hvsr_data = run_data()

if not hasattr(st.session_state, 'hvsr_data'):
    st.session_state.hvsr_data = hvsr_data

hvDF = st.session_state.hvsr_data['hvsr_windows_df']
x_data = hvsr_data['x_freqs']['Z'][:-1]

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
    zTrace = hvsr_data.select(component='Z').merge()[0]
    eTrace = hvsr_data.select(component='E').merge()[0]
    nTrace = hvsr_data.select(component='N').merge()[0]
    specKey='Z'

    specStreamDict = {'Z':zTrace,
                        'E':eTrace,
                        'N':nTrace}

    sTime = zTrace.stats.starttime
    xTimes = [np.datetime64((sTime + tT).datetime) for tT in zTrace.times()]

    f, t, psdArr = signal.spectrogram(x=specStreamDict[specKey].data,
                                    fs=specStreamDict[specKey].stats.sampling_rate,
                                    mode='magnitude')
    f[0] = f[1]/10 # Fix so bottom number is not 0

    timeWindowList = hvDF.index
    #spectroFig = px.imshow(psdArr,
    ##                       labels=dict(x="Time", y="Frequency [Hz]", color='PSD Value'),
    #                      x=timeWindowList,
    #                      color_continuous_scale='Viridis')

    hvsrBand = hvsr_data['hvsr_band']
    #f=hvsr_data.ppsds["Z"]['psd_frequencies']
    minz = np.percentile(psdArr, 1)
    maxz = np.percentile(psdArr, 99)


    hmap = go.Heatmap(z=psdArr,
                x=timeWindowList,
                y=f,
                colorscale='Turbo',
                showlegend=False,
                hovertemplate='Time [UTC]: %{x}<br>Frequency [Hz]: %{y:.2f}<br>Spectrogram Magnitude: %{z:.2f}<extra></extra>',
                zmin=minz, zmax=maxz, showscale=False, name=f'{specKey} Component Spectrogram')
    inputFig.add_trace(hmap, row=1, col=1)
    inputFig.update_yaxes(type='log', range=[np.log10(hvsrBand[0]), np.log10(hvsrBand[-1])], row=1, col=1)
    inputFig.update_yaxes(title={'text':f'Spectrogram ({specKey})'}, row=1, col=1)

    #for sTrace in spectroFig.data:
    #    inputFig.add_trace(sTrace, row=1, col=1)


    hvdf = hvsr_data.hvsr_windows_df
    timelineFig = px.timeline(data_frame=hvdf,
                            x_start=timeWindowList,
                            x_end='TimesProcessed_End',
                            y=['Used']*hvdf.shape[0],
                            #y="Use",#range_y=[-20, -10],
                            color='Use',
                            color_discrete_map={True: 'rgba(0,255,0,1)',
                                                False: 'rgba(255,255,255,1)'})
    for timelineTrace in timelineFig.data:
        inputFig.add_trace(timelineTrace, row=2, col=1)

    # Data traces
    zDataFig = px.scatter(x=xTimes, y=zTrace.data)
    zDataFig.update_traces(mode='markers+lines',
                        marker=dict(size=1, color='rgba(0,0,0,1)'),
                        line=dict(width=1, color='rgba(0,0,0,1)'),
                        selector=dict(mode='markers'))
    for zTrace in zDataFig.data:
        inputFig.add_trace(zTrace, row=3, col=1)


    eDataFig = px.scatter(x=xTimes, y=eTrace.data)
    eDataFig.update_traces(mode='markers+lines',
                        marker=dict(size=1, color='rgba(0,0,255,1)'),
                        line=dict(width=1, color='rgba(0,0,255,1)'),
                        selector=dict(mode='markers'))
    for eTrace in eDataFig.data:
        inputFig.add_trace(eTrace, row=4, col=1)


    nDataFig = px.scatter(x=xTimes, y=nTrace.data)
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

    inputFig.update_xaxes(type='date', range=[xTimes[0], xTimes[-1]])


    return inputFig



def update_data():
    st.session_state.data_chart_event = st.session_state.data_plot
    # Still figuring stuff out
    print("UPDATE DATA")
    print(st.session_state.data_chart_event)
    
    # This seems to work well at the moment
    windows=[]
    if len(st.session_state.data_chart_event['selection']['box']) > 0:
        esb = st.session_state.data_chart_event['selection']['box']
        for b in esb:
            print(b)
            if b['x'][0] > b['x'][1]:
                windows.append((b['x'][1], b['x'][0]))
            else:
                windows.append((b['x'][0], b['x'][1]))
    


    print('data_plot       ', st.session_state.data_plot['selection']['box'])
    print("data_chart_event", st.session_state.data_chart_event['selection']['box'])

    # Reset the variables (but which one(s)?)
    st.session_state.data_chart_event = {"selection":{"points":[],
                          "point_indices":[],
                          'box':[],
                          'lasso':[]}}



    if len(windows) > 0:
        pass
    print(windows)
    print('---')


def update_selection_type():
    st.session_state.input_selection_mode = st.session_state.input_selection_toggle

#    st.session_state.outlier_chart_event = st.session_state.outlier_plot
#    curves2Remove = np.unique([p['curve_number'] for p in st.session_state.outlier_chart_event['selection']['points']])
#    st.session_state.outlier_curves_to_remove = list(curves2Remove)
#    st.toast(f'Removing curve(s) specified as an outlier')

#    if len(st.session_state.outlier_curves_to_remove)>0:
#        #st.session_state.outliers_updated = True

#        st.write(f'Removing curve(s) specified as an outlier:')
#        for remCurve in st.session_state.outlier_curves_to_remove:
#            currInd = hvDF.iloc[remCurve].name
#            st.write("Curve ", remCurve, ' starting at ', currInd)
#            st.session_state.hvsr_data['hvsr_windows_df'].loc[currInd, "Use"] = False

inputFig = make_input_fig()
event = st.plotly_chart(inputFig, on_select=update_data, key='data_plot', selection_mode='box', use_container_width=True, theme='streamlit')
st.write("Select any time window with the Box Selector (see the top right of chart) to remove it from analysis.")
st.session_state.input_selection_mode = st.pills('Window Selection Mode', options=['Add', "Delete"], key='input_selection_toggle', 
                                                 default='Add', on_change=update_selection_type)

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


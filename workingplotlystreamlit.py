import sprit.sprit_hvsr as sprit

import plotly.express as px
from plotly import subplots
import streamlit as st
import numpy as np

if not hasattr(st.session_state, 'outlier_curves'):
    st.session_state.outlier_curves = []

@st.cache_data
def run_data():
    hvsr_data = sprit.run('sample', suppress_report_outputs=True)
    return hvsr_data
hvsr_data = run_data()

if not hasattr(st.session_state, 'hv_data'):
    st.session_state.hv_data = hvsr_data

hvDF = st.session_state.hv_data['hvsr_windows_df']
x_data = hvsr_data['x_freqs']['Z'][:-1]

for remCurve in st.session_state.outlier_curves:
    print('remCurve', remCurve)
    currInd = hvDF.iloc[remCurve].name
    print(currInd)
    hvDF.loc[currInd, "Use"] = False

if len(st.session_state.outlier_curves) > 0:
    st.session_state.outlier_curves = []

no_subplots = 1
outlierFig = subplots.make_subplots(rows=no_subplots, cols=1,
                                    shared_xaxes=True, horizontal_spacing=0.01,
                                    vertical_spacing=0.1)

scatterFig = px.scatter()
scatter_traces = []
line_traces = []
for row, hv_data in enumerate(hvDF['HV_Curves']):
    currInd = hvDF.iloc[row].name
    if hvDF.loc[currInd, 'Use']:  
        scatterArray = np.array(list(hv_data)[::10])
        x_data_Scatter = np.array(list(x_data)[::10])
        scatter_traces.append(px.scatter(x=x_data_Scatter, y=scatterArray,
                                color_discrete_sequence=['black']))
        line_traces.append(px.line(x=x_data, y=hv_data,
                                color_discrete_sequence=['black']))
    else:
        scatterArray = np.array(list(hv_data)[::10])
        x_data_Scatter = np.array(list(x_data)[::10])
        scatter_traces.append(px.scatter(x=x_data_Scatter, y=scatterArray,
                                color_discrete_sequence=['red']))
        line_traces.append(px.line(x=x_data, y=hv_data,
                                color_discrete_sequence=['red']))

for tr in scatter_traces:
    for trace in tr.data:
        outlierFig.add_traces(trace, rows=1, cols=1)
        

for tr in line_traces:
    for trace in tr.data:
        outlierFig.add_traces(trace, rows=1, cols=1)
        #pass

outlierFig.update_xaxes(title='Frequency [Hz]', type="log", row=1, col=1)
outlierFig.update_yaxes(title='H/V Ratio', row=1, col=1)

def update_outlier():
    curves2Remove = np.unique([p['curve_number'] for p in event['selection']['points']])    
    st.session_state.outlier_curves = list(curves2Remove)

event = st.plotly_chart(outlierFig, on_select=update_outlier, key='outlier_plot', use_container_width=True, theme='streamlit')


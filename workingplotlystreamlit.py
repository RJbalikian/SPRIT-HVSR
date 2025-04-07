import sprit.sprit_hvsr as sprit

import plotly.express as px
from plotly import subplots
import streamlit as st
import numpy as np

@st.cache_data
def run_data():
    hvsr_data = sprit.run('sample', suppress_report_outputs=True)
    print('hvsrun')
    return hvsr_data
hvsr_data = run_data()

if not hasattr(st.session_state, 'hv_data'):
    st.session_state.hv_data = hvsr_data

hvDF = st.session_state.hv_data['hvsr_windows_df']
x_data = hvsr_data['x_freqs']['Z'][:-1]

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
        scatterArray = np.array(list(hv_data)[::5])
        x_data_Scatter = np.array(list(x_data)[::5])
        currFig = px.scatter(x=x_data_Scatter, y=scatterArray)
        currFig.update_traces(mode='markers+lines',
                        marker=dict(size=1, color='rgba(0,0,0,0.1)'),
                        line=dict(width=1, color='rgba(0,0,0,0.1)'),
                        selector=dict(mode='markers'))
         
        scatter_traces.append(currFig)

    else:
        scatterArray = np.array(list(hv_data)[::5])
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



def update_outlier():
    st.session_state.outlier_chart_event = st.session_state.outlier_plot
    curves2Remove = np.unique([p['curve_number'] for p in st.session_state.outlier_chart_event['selection']['points']])
    st.session_state.outlier_curves_to_remove = list(curves2Remove)
    st.toast(f'Removing curve(s) specified as an outlier')

    if len(st.session_state.outlier_curves_to_remove)>0:
        #st.session_state.outliers_updated = True

        st.write(f'Removing curve(s) specified as an outlier:')
        for remCurve in st.session_state.outlier_curves_to_remove:
            currInd = hvDF.iloc[remCurve].name
            st.write("Curve ", remCurve, ' starting at ', currInd)
            st.session_state.hv_data['hvsr_windows_df'].loc[currInd, "Use"] = False

st.plotly_chart(outlierFig, on_select=update_outlier, key='outlier_plot', use_container_width=True, theme='streamlit')
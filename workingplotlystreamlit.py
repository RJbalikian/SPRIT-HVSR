import sprit.sprit_hvsr as sprit

import plotly.express as px
from plotly import subplots
import streamlit as st
import numpy as np

print('start')
if not hasattr(st.session_state, 'outliers_updated'):
    st.session_state.outliers_updated = False

if not hasattr(st.session_state, 'outlier_chart_event'):
    st.session_state.outlier_chart_event = {'selection':{'points':[]}}

print("0 outlier event", st.session_state.outlier_chart_event['selection']['points'])

print("1 outlier event", st.session_state.outlier_chart_event['selection']['points'])

if not hasattr(st.session_state, 'outlierrunCount'):
    st.session_state.outlierrunCount = 0

print("Outliers updated", st.session_state.outliers_updated)
if not hasattr(st.session_state, 'outlier_curves_to_remove'):
    st.session_state.outlier_curves_to_remove = []
st.session_state.outliers_updated = False

print("2 outlier event", st.session_state.outlier_chart_event['selection']['points'])
@st.cache_data
def run_data():
    hvsr_data = sprit.run('sample', suppress_report_outputs=True)
    print('hvsrun')
    return hvsr_data
hvsr_data = run_data()

if not hasattr(st.session_state, 'hv_data'):
    st.session_state.hv_data = hvsr_data

print("3 outlier event", st.session_state.outlier_chart_event['selection']['points'])
hvDF = st.session_state.hv_data['hvsr_windows_df']
x_data = hvsr_data['x_freqs']['Z'][:-1]

if len(st.session_state.outlier_curves_to_remove) > 0:
    st.session_state.outlier_curves_to_remove = []

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
        #line_traces.append(px.line(x=x_data, y=hv_data,
        #                        color_discrete_sequence=['black']))
    else:
        scatterArray = np.array(list(hv_data)[::5])
        x_data_Scatter = np.array(list(x_data)[::5])
        currFig = px.scatter(x=x_data_Scatter, y=scatterArray,
                             opacity=0.5)
        currFig.update_traces(mode='markers+lines',
                              marker=dict(size=1, color='rgba(195,87,0,0.5)'),
                              line=dict(width=1, color='rgba(195,87,0,0.5)'),
                              selector=dict(mode='markers'))
        scatter_traces.append(currFig)
        #line_traces.append(px.line(x=x_data, y=hv_data,
        #                        color_discrete_sequence=['red']))

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
                         #line=dict(width=3),
                         #marker=dict(size=20, ),
                         #opacity=0.7)


#for tr in line_traces:
#    for trace in tr.data:
#        outlierFig.add_traces(trace, rows=1, cols=1)
        #pass

outlierFig.update_xaxes(title='Frequency [Hz]', type="log", row=1, col=1)
outlierFig.update_yaxes(title='H/V Ratio', row=1, col=1)

print("4 outlier event", st.session_state.outlier_chart_event['selection']['points'])


def update_outlier():
    st.write('update outliers run', st.session_state.outlierrunCount)
    st.session_state.outlierrunCount += 1
    st.session_state.outlier_chart_event = st.session_state.outlier_plot
    curves2Remove = np.unique([p['curve_number'] for p in st.session_state.outlier_chart_event['selection']['points']])
    st.session_state.outlier_curves_to_remove = list(curves2Remove)
    
    if len(st.session_state.outlier_curves_to_remove)>0:
        st.session_state.outliers_updated = True

        for remCurve in st.session_state.outlier_curves_to_remove:
            currInd = hvDF.iloc[remCurve].name
            print('Supposedly removing')
            st.session_state.hv_data['hvsr_windows_df'].loc[currInd, "Use"] = False

if len(st.session_state.outlier_chart_event['selection']['points']) > 0:
    print("We got something here a")
    update_outlier()

print("5 outlier event", st.session_state.outlier_chart_event['selection']['points'])
plot_spot = st.empty()

with plot_spot:
    st.plotly_chart(outlierFig, on_select=update_outlier, key='outlier_plot', use_container_width=True, theme='streamlit')
print("6 outlier event", st.session_state.outlier_chart_event['selection']['points'])

if len(st.session_state.outlier_chart_event['selection']['points']) > 0:
    print("We got something here b")
    update_outlier()
    #st.session_state.outlier_chart_event = st.plotly_chart(outlierFig, on_select=update_outlier, key='outlier_plot', use_container_width=True, theme='streamlit')

print('Done\n')
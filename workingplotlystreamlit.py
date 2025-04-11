import sprit.sprit_hvsr as sprit
import inspect

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

if not hasattr(st.session_state, 'hvsr_data'):
    st.session_state.hvsr_data = hvsr_data

hvDF = st.session_state.hvsr_data['hvsr_windows_df']
x_data = hvsr_data['x_freqs']['Z'][:-1]

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
            st.session_state.hvsr_data['hvsr_windows_df'].loc[currInd, "Use"] = False

st.plotly_chart(outlierFig, on_select=update_outlier, key='outlier_plot', use_container_width=True, theme='streamlit')
st.write("Select any curve(s) with your cursor or the Box or Lasso Selectors (see the top right of chart) to remove it from the results statistics and analysis.")

def update_from_outlier_selection():
    prochvsr_kwargs = {k: v for k, v in st.session_state.items() if k in tuple(inspect.signature(sprit.process_hvsr).parameters.keys()) and k != 'hvsr_data'}
    checkPeaks_kwargs = {k: v for k, v in st.session_state.items() if k in tuple(inspect.signature(sprit.process_hvsr).parameters.keys()) and k != 'hvsr_data'}
    getRep_kwargs = {k: v for k, v in st.session_state.items() if k in tuple(inspect.signature(sprit.process_hvsr).parameters.keys()) and k != 'hvsr_data'}

    st.session_state.hvsr_data = sprit.process_hvsr(hvsr_data=st.session_state.hvsr_data, **prochvsr_kwargs)
    st.session_state.hvsr_data = sprit.check_peaks(hvsr_results=st.session_state.hvsr_data, **checkPeaks_kwargs)
    st.session_state.hvsr_data = sprit.get_report(hvsr_results=st.session_state.hvsr_data, **getRep_kwargs)

    write_to_info_tab(infoTab)
    
    inputTab.plotly_chart(st.session_state.hvsr_data['InputPlot'], use_container_width=True)
    outlierEvent = outlierTab.plotly_chart(st.session_state.hvsr_data['OutlierPlot'], use_container_width=True)
    plotReportTab.plotly_chart(outlierFig, on_select=update_outlier, key='outlier_plot', use_container_width=True, theme='streamlit')
    csvReportTab.dataframe(data=st.session_state.hvsr_data['CSV_Report'])
    strReportTab.text(st.session_state.hvsr_data['Print_Report'])


st.button('Update H/V Curve Analysis', key='update_from_outliers', type='primary', icon=":material/update:")

# plotly express functions: https://plotly.com/python-api-reference/plotly.express.html
# This might be good for "spectrogram": https://plotly.com/python-api-reference/generated/plotly.express.imshow.html#plotly.express.imshow
#import plotly.express as px
#import sprit
#hvsrData = sprit.run('sample', suppress_report_output=True)
#hvdf = hvsrData.hvsr_windows_df
#hvdf.columns
#px.timeline(hvdf, pd.Series(hvdf.index), 'TimesProcessed_End', y=[0]*hvdf.shape[0], color='Use', color_discrete_map={True:'rgba(0,255,0,0.1)',False:'rgba(255,255,255,0.5)'})
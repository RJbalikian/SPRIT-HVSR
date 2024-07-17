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

        bandVals=[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,2,3,4,5,6,7,8,9,10,20,30,40,50,60,70,80,90,100]
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
        #detrend: str = 'spline',
        #detrend_order: int = 2,
        #update_metadata: bool = True,
        #plot_input_stream: bool = False,

    @st.experimental_dialog("Update Plot Settings", width='large')
    def plot_settings_dialog():
        st.selectbox("Plot Engine", options=['Matplotlib', "Plotly"])

    def open_settings_dialogs(function):
        if hasattr(function, '__name__'):
            funName = function.__name__
        else:
            funName = function
        settingsDialogDict={
            'input_params':open_ip_dialog,
            'fetch_data':open_fd_dialog,
            'plot_settings':plot_settings_dialog
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

                if st.button("Fetch Data", key='fdset'):
                    open_settings_dialogs(sprit.fetch_data)

                if st.button("Plot Settings", key='plotset'):
                    open_settings_dialogs("plot_settings")

        with aboutMenu:
            with st.popover(":information_source:", use_container_width=True):
                st.markdown(aboutStr)


    # Sidebar content
    st.sidebar.title("SpRIT HVSR")
    st.sidebar.text('No file selected')
    st.sidebar.text_input("Datapath", placeholder='Enter filepath to your data here')
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
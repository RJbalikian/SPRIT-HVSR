import streamlit as st
import sprit
import inspect


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

# Define functions
#@st.experimental_dialog("Dialog")
def open_settings_dialog(function):
    #print(function.__name__)
    pass


def input_params_dialog():
    pass

# Create a thin bar at the top

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
        with st.popover("Settings:gear:", use_container_width=True):
            st.button("Input Parameters", on_click=open_settings_dialog(sprit.input_params))


    with aboutMenu:
        with st.popover(":information_source:", use_container_width=True):
            st.write("About content goes here")


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

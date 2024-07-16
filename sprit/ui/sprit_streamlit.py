import streamlit as st
import sprit
import inspect

# Define functions
@st.experimental_dialog("Dialog")
def open_settings_dialog(function):
    print(function.__name__)

def input_params_dialog():
    pass

# Create a thin bar at the top

top_container = st.container()

# Create top menu
with top_container:
    spritMenu, setMenu, aboutMenu = st.columns([0.3, 0.3, 0.3])
    with spritMenu:
        with st.popover("SpRIT", use_container_width=True):
            st.write("SpRIT content goes here")

    with setMenu:
        with st.popover("Settings", use_container_width=True):
            st.button("Input Parameters", on_click=open_settings_dialog(sprit.input_params))


    with aboutMenu:
        with st.popover("About", use_container_width=True):
            st.write("About content goes here")


st.title("SpRIT HVSR")
st.header('For processing Ambient microtremors', divider='rainbow')

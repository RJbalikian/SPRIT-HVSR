def create_jupyter_ui():
    import ipywidgets as widgets
    from IPython.display import display

    # INPUT TAB
    # Create four buttons
    button1 = widgets.Button(description='Button 1',layout=widgets.Layout(height='auto', width='auto'))
    button2 = widgets.Button(description='Button 2',layout=widgets.Layout(height='auto', width='auto'))
    button3 = widgets.Button(description='Button 3',layout=widgets.Layout(height='auto', width='auto'))

    # Create a 2x2 grid and add the buttons to it
    input_tab = widgets.GridspecLayout(20, 20)
    input_tab[0, :10] = button1
    input_tab[0, 10:] = button2
    input_tab[1, :] = button3

    # PREVIEW TAB

    # SETTINGS TAB

    # LOG TAB

    # RESULTS TAB

    # SPRIT WIDGET
    # Add all  a tab and add the grid to it
    sprit_widget = widgets.Tab([input_tab])
    sprit_widget.set_title(0, "Input")

    # Display the tab
    display(sprit_widget)

import remi.gui as gui
from remi import start, App

class SpRIT_REMI(App):
    def __init__(self, *args):
        super(SpRIT_REMI, self).__init__(*args)

    def main(self):
        # Create a TabBox with two tabs
        spacer50Pct = gui.Label("", width="50%")


        tab_box = gui.TabBox(width='90%', height="90%")
        
        # First tab
        inputVBox = gui.VBox(width='100%', height='100%')
        
        dateTimeHBox = gui.HBox()
        sTimeLabel = gui.Label("Start time:",width='50%', style={'text-align': 'right'})
        sTime = gui.Input(input_type='time', width="100%")
        eTimeLabel = gui.Label("End time: ", width="50%", style={'text-align': 'right'})
        eTime = gui.Input(input_type='time', default_value="23:59:59", width="100%")
        acqDateLabel = gui.Label("Acquisition Date: ", width="50%", style={'text-align': 'right'})
        acq_date_Button = gui.Date("Acq. Date", width="100%")
        #button1 = gui.Button('Input Tab', width='100%', height='100%')

        dateTimeHBox.append(acqDateLabel, "AcqDateLabel")
        dateTimeHBox.append(acq_date_Button, "Acquisition Date")
        dateTimeHBox.append(spacer50Pct, "spacer0")
        dateTimeHBox.append(sTimeLabel, "Start time Label")
        dateTimeHBox.append(sTime, "Start time")
        dateTimeHBox.append(spacer50Pct, "spacer1")
        dateTimeHBox.append(eTimeLabel, "End time Label")
        dateTimeHBox.append(eTime, "End time")

        inputVBox.append(dateTimeHBox, "DatetimeHbox")
        tab_box.append(inputVBox, 'Input')
        
        # Second tab
        button2 = gui.Button('Results Tab', width='100%', height='100%')
        tab_box.add_tab(button2, 'Results', None)
        
        return tab_box

    def on_close_websocket(self):
        # Clean up any resources or perform necessary actions
        # before closing the WebSocket connection
        print("WebSocket connection closed. Goodbye!")

if __name__ == "__main__":
    start(SpRIT_REMI, title="SpRIT HVSR", standalone=False)

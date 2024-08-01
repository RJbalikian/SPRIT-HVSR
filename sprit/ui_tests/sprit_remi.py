from remi import start, App
import remi.gui as gui
try:
    import sprit_hvsr
except:
    from sprit import sprit_hvsr
class SpritApp(App):
    def __init__(self, *args):
        super(SpritApp, self).__init__(*args)

        self.source='file'
    
    input_params_kwargs = {}
    get_report_kwargs = {}



    def main(self):
        # Define App containers
        spritApp = gui.VBox(width='100%', height='100%', margin='0px auto', style={'vertical-align':'top'})
        
        appTopBar = gui.VBox(height="20%", width="100%", margin='5px auto')
        appTabs = gui.TabBox(width="80%", height="80%")
        appSideBar = gui.VBox(width="20%", height="100%")
        appHbox = gui.HBox([appSideBar, appTabs], width="100%", margin='5px auto')
        appVbox = gui.VBox([appTopBar, appHbox], height='98%', width='100%', margin='5px auto')

        fillerLabel = gui.Label()
        fivePctSpace=gui.Label(width="5%")

        # Main menu items
        menu = gui.Menu(width='100%', height='2%', style={'vertical-align':'top'})
        spritMenu = gui.MenuItem('SpRIT', width=100, height=25, style={'vertical-align':'top'})
        settingsMenu = gui.MenuItem('Settings', width=100, height=25, style={'vertical-align':'top'})
        aboutMenu = gui.MenuItem('About', width=100, height=25, style={'vertical-align':'top'})
        
        # SpRIT menu
        spritReadMenu = gui.MenuItem('Read Data', width=100, height=25)
        spritThemeMenu = gui.MenuItem('Theme', width=100, height=25)
        spritThemeMenu.onclick.do(self.menu_open_clicked)
        spritReadFile = gui.MenuItem('Read data from file', width=200, height=25)
        spritReadFile.onclick.do(self.read_data)
        spritReadRaw = gui.MenuItem('Read data in raw format', width=200, height=25)
        spritReadRaw.onclick.do(self.read_data)
        spritReadDir = gui.MenuItem('Read data from a directory', width=200, height=25)
        spritReadDir.onclick.do(self.read_data)
        spritReadBatch = gui.MenuItem('Read batch data', width=200, height=25)
        spritReadBatch.onclick.do(self.read_data)

        spritMenu.append([spritReadMenu, spritThemeMenu])
        spritReadMenu.append([spritReadFile, spritReadRaw, spritReadDir, spritReadBatch])

        # Settings menu
        #settingsMenu.onclick.do(self.menu_view_clicked)
        settingsFetchMenu = gui.MenuItem('Input data settings', width=200, height=25)
        settingsNoiseMenu = gui.MenuItem('Remove noise settings', width=200, height=25)
        settingsAzimuthMenu = gui.MenuItem('Azimuth settings', width=200, height=25)
        settingsPPSDMenu = gui.MenuItem('PPSD settings', width=200, height=25)
        settingsHVMenu = gui.MenuItem('H/V settings', width=200, height=25)
        settingsOutlierMenu = gui.MenuItem('Outlier settings', width=200, height=25)
        settingsCheckPeakMenu = gui.MenuItem('Check peak settings', width=200, height=25)
        settingsReportMenu = gui.MenuItem('Report settings', width=200, height=25)

        settingsFetchMenu.onclick.do(self.settings_menu_do)
        settingsNoiseMenu.onclick.do(self.settings_menu_do)
        settingsAzimuthMenu.onclick.do(self.settings_menu_do)
        settingsPPSDMenu.onclick.do(self.settings_menu_do)
        settingsHVMenu.onclick.do(self.settings_menu_do)
        settingsOutlierMenu.onclick.do(self.settings_menu_do)
        #settingsCheckPeakMenu.onclick.do(self.settings_menu_do)
        #settingsReportMenu.onclick.do(self.settings_menu_do)

        settingsMenuItems = [settingsFetchMenu, settingsNoiseMenu, settingsAzimuthMenu, settingsPPSDMenu,
                             settingsHVMenu, settingsOutlierMenu]#, settingsCheckPeakMenu, settingsReportMenu]

        settingsMenu.append(settingsMenuItems)

        # About menu
        aboutDocs = gui.MenuItem("Documentation")
        aboutDocsRTD = gui.MenuItem("Read the docs", width=100)
        aboutDocsGH = gui.MenuItem("Github Pages", width=100)
        aboutRepo = gui.MenuItem("PyPi Repository")
        aboutGithub = gui.MenuItem("Github Repository")
        aboutWiki = gui.MenuItem("SpRIT Wiki (Tutorials, examples, etc.)", width=250)
        aboutIssues = gui.MenuItem('Report an Issue')
        aboutSpRIT = gui.MenuItem("About SpRIT")

        aboutDocs.append([aboutDocsRTD, aboutDocsGH])
        aboutMenu.append([aboutDocs, aboutRepo, aboutGithub, aboutWiki, aboutIssues, aboutSpRIT])

        # Create menu
        menu.append([spritMenu, settingsMenu, aboutMenu])
        menubar = gui.MenuBar(width='100%', height='20px', style={'vertical-align':'top'})
        menubar.append(menu)

        spritApp.append(menubar)
        spritApp.append(appVbox)

        # CREATE DIALOGS
        # Input data dialog
        #sprit_hvsr.input_params()
        #sprit_hvsr.fetch_data()
        self.input_data_dialog = gui.GenericDialog(title='Input data settings',
                                                   message='Set Parameters for the sprit.input_params() and sprit.fetch_data() functions',
                                                   width='75%')
        inputDataDialog_vbox = gui.VBox(width='90%', height='100%', margin='5%', padding='5px')
        iPLabel = gui.Label('Input Parameters (parameters for sprit.input_params())')

        # Datapath
        datapathLabel = gui.Label("Datapath", width="10%")
        datapathInput = gui.Input(hint='Path to the folder or file', width="80%")
        datapathSelect = gui.Button('Browse', width="10%")

        fileDDitem = gui.DropDownItem('File')
        rawDDitem = gui.DropDownItem('Raw')
        dirDDitem = gui.DropDownItem('Directory')
        batchDDitem = gui.DropDownItem('Batch')
        sourceDropDown = gui.DropDown([fileDDitem, rawDDitem, dirDDitem, batchDDitem], width="10%", margin='25px')

        sourceLabel = gui.Label('Source', width='5%')
        datapathHbox = gui.HBox([datapathLabel, datapathInput, datapathSelect, gui.Label(width="30%"), sourceLabel, sourceDropDown], width='100%', margin="5px")

        # Site
        siteLabel = gui.Label('Site')
        siteInput = gui.TextInput(hint='Site name for current data', margin='10px')
        siteInput.set_value('HVSRSite')
        siteHbox = gui.HBox([siteLabel, siteInput], width='50%', margin='5px')

        #network
        #station
        #loc
        #channels

        #acq_date
        #starttime
        #endtime
        #tzone

        #xcoord
        #ycoord
        #elevation
        #elev_unit
        #input_crs
        #output_crs
        #depth

        #instrument
        #metapath

        #hvsr_band
        #peak_freq_range

        #source
        #trim_dir
        #export_format
        #detrend
        #detrend order
    
        
        
        inputDataDialog_vbox.append(iPLabel)
        self.input_data_dialog.get_child('central_container').append(inputDataDialog_vbox)

        # Process hvsr dialog
        self.process_hvsr_dialog = gui.GenericDialog(title='HVSR settings',
                                                   message='Set Parameters for the sprit.process_hvsr() function',
                                                   width='75%')


        processHVSRDialog_vbox = gui.VBox(width='90%', height='100%', margin='5%', padding='5px')

        # Method
        dfaDDItem = gui.DropDownItem('Diffuse Field Assumption',)
        arithMeanDDItem = gui.DropDownItem('Arithmetic Mean')
        geoMeanDDItem = gui.DropDownItem('Geometric Mean')
        vecSumDDItem = gui.DropDownItem('Vector Summation')
        quadMeanDDItem = gui.DropDownItem('Quadratic Mean')
        maxHValDDItem = gui.DropDownItem('Maximum Horizontal Value')

        hCombineMethodDropDown = gui.DropDown([dfaDDItem, arithMeanDDItem, geoMeanDDItem,
                                               vecSumDDItem, quadMeanDDItem, maxHValDDItem], width='80%')
        methodHBox = gui.HBox([gui.Label('Method to Combine Horizontal Components', width='20%'), hCombineMethodDropDown],
                                margin='5px', width="100%")

        # Smooth
        smoothCheckBox = gui.CheckBox(checked=True, width='1%')
        smoothWidthLabel = gui.Label('Width', width='10%', style={'text-align':'right'})
        smoothWidthInput = gui.TextInput(width="5%")
        smoothWidthInput.set_value('50')
        smoothHBox = gui.HBox([gui.Label('Smooth', width='20%'), smoothCheckBox, smoothWidthLabel,smoothWidthInput],
                                margin='5px', width="100%",style={'justify-content':'flex-start', 'align-items':'flex-start'})

        # Freq Smooth
        freqSmoothCheckBox = gui.CheckBox(checked=True, width='1%')

        koDDItem = gui.DropDownItem('Konno Ohmachi')
        constantDDItem = gui.DropDownItem('Constant')
        proportDDItem = gui.DropDownItem('Proportional')
        noneDDItem = gui.DropDownItem('None')
        freqSmoothDropdown = gui.DropDown([koDDItem, constantDDItem, 
                                           proportDDItem, noneDDItem], width='65%')
        freqSmoothWidthLabel = gui.Label('Width', width='10%', style={'text-align':'right'})
        freqSmoothWidthInput = gui.TextInput(width="5%")
        freqSmoothWidthInput.set_value('40')
        
        freqSmoothHbox = gui.HBox([gui.Label('Frequency Smoothing Method', width='20%'), freqSmoothCheckBox, freqSmoothDropdown,freqSmoothWidthLabel, freqSmoothWidthInput],
                                margin='5px', width="100%")
        # Resample
        resampleCheckBox = gui.CheckBox(checked=True, width='1%')
        resampleWidthLabel = gui.Label('Width', width='10%', style={'text-align':'right'})
        resampleWidthInput = gui.TextInput(width="5%")
        resampleWidthInput.set_value('500')
        resampleHBox = gui.HBox([gui.Label('Resample', width='20%'), resampleCheckBox, resampleWidthLabel,resampleWidthInput],
                                margin='5px', width="100%",style={'justify-content':'flex-start', 'align-items':'flex-start'})
        
        # Add everything to the dialog
        processHVSRDialog_vbox.append(methodHBox, 0)
        processHVSRDialog_vbox.append(smoothHBox, 1)
        processHVSRDialog_vbox.append(freqSmoothHbox, 2)
        processHVSRDialog_vbox.append(resampleHBox, 3)
        self.process_hvsr_dialog.get_child('central_container').append(processHVSRDialog_vbox)

        # TABS
        appTopBar.append(datapathHbox, 0)
        appTopBar.append(siteHbox, 1)
        appTabs.append(fillerLabel)
        appSideBar.append(fillerLabel)

        # CLOSING SCRIPTS
        tag = gui.Tag(_type='script')
        tag.add_child("javascript", """window.onunload=function(e){remi.sendCallback('%s','%s');return "close?";};""" % (
            str(id(self)), "on_window_close"))
        spritApp.add_child("onunloadevent", tag)

        # returning the root widget

        return spritApp

    # LISTENER FUNCTIONS
    def menu_open_clicked(self, widget):
        pass#self.lbl.set_text('Menu clicked: Open')

    def menu_view_clicked(self, widget):
        pass#self.lbl.set_text('Menu clicked: View')
    
    def read_data(self, widget):
        readDict = {'Read data from file':'file',
                    'Read data in raw format':'raw',
                    'Read data from a directory':'dir',
                    'Read batch data':'batch'}
        self.source=readDict[widget.get_text()]

    def open_fetch_data_dialog(self):
        print('dialog opening')
        pass

    def open_remove_noise_dialog(self):
        print('dialog opening')
        pass

    def open_azimuth_dialog(self):
        print('dialog opening')
        pass
    
    def open_ppsd_dialog(self):
        print('dialog opening')
        pass
    
    def open_hv_dialog(self):
        print('dialog opening')
        self.process_hvsr_dialog.show(self)
        
    
    def open_outlier_dialog(self):
        print('dialog opening')
        pass
    
    def open_peak_dialog(self):
        print('dialog opening')
        pass
    
    def open_report_dialog(self):
        print('dialog opening')
        self.infoLabel.set_text("Report got got")
        self.get_report_dialog.show(self)

    
    def settings_menu_do(self, widget):
        settingsDict = {'Input data settings':self.open_fetch_data_dialog,
                        'Remove noise settings':self.open_remove_noise_dialog,
                        'Azimuth settings':self.open_azimuth_dialog,
                        'PPSD settings':self.open_ppsd_dialog,
                        'H/V settings':self.open_hv_dialog,
                        'Outlier settings':self.open_outlier_dialog,
                        'Check peak settings':self.open_peak_dialog,
                        'Report settings':self.open_report_dialog
                        }
        #self.infoLabel.set_text(widget.get_text())
        settingsDict[widget.get_text()]()

    def on_window_close(self):
        # here you can handle the unload
        print("app closing")
        self.close()

if __name__ == "__main__":
    start(SpritApp, debug=True, address='0.0.0.0', port=0)

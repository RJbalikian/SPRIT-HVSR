from remi import start, App
import remi.gui as gui
try:
    import sprit_hvsr
except:
    from sprit import sprit_hvsr
class SpritApp(App):
    def __init__(self, *args):
        super(SpritApp, self).__init__(*args)

    input_params_kwargs = {}
    get_report_kwargs = {}

    def main(self):
        # Define App containers
        spritApp = gui.VBox(width='100%', height='100%', margin='0px auto', style={'vertical-align':'top'})
        
        # Main menu items
        menu = gui.Menu(width='100%', height='25px', style={'vertical-align':'top'})
        spritMenu = gui.MenuItem('SpRIT', width=100, height=25, style={'vertical-align':'top'})
        settingsMenu = gui.MenuItem('Settings', width=100, height=25, style={'vertical-align':'top'})
        aboutMenu = gui.MenuItem('About', width=100, height=25, style={'vertical-align':'top'})
        
        # SpRIT menu
        spritReadMenu = gui.MenuItem('Read Data', width=100, height=25)
        spritThemeMenu = gui.MenuItem('Theme', width=100, height=25)
        spritThemeMenu.onclick.do(self.menu_open_clicked)
        spritReadFile = gui.MenuItem('Read file', width=100, height=25)
        spritReadFile.onclick.do(self.read_file)
        spritReadFolder = gui.MenuItem('Read folder', width=100, height=25)
        spritReadFolder.onclick.do(self.read_folder)
        
        spritMenu.append([spritReadMenu, spritThemeMenu])
        spritReadMenu.append([spritReadFile, spritReadFolder])

        # Settings menu
        #settingsMenu.onclick.do(self.menu_view_clicked)
        settingsFetchMenu = gui.MenuItem('Fetch data settings', width=200, height=25)
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
        
        self.infoLabel = gui.Label('INFORMATION', height='100%', margin='1%')

        spritApp.append(menubar)
        spritApp.append(self.infoLabel)

        # Create dialogs
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
        methodHBox = gui.HBox([gui.Label('Method to Combine Horizontal Components', margin=5, width='20%'), hCombineMethodDropDown],
                                margin='5px', width="100%")

        # Smooth
        smoothCheckBox = gui.CheckBox(checked=True, width='1%')
        smoothHBox = gui.HBox([gui.Label('Smooth', width='20%'), smoothCheckBox],
                                margin='5px', width="100%",style={'justify-content':'flex-start', 'align-items':'flex-start'})

        processHVSRDialog_vbox.append(methodHBox, 0)
        processHVSRDialog_vbox.append(smoothHBox, 1)
        self.process_hvsr_dialog.get_child('central_container').append(processHVSRDialog_vbox)
        #sprit_hvsr.get_report()
        #sprit_hvsr.process_hvsr()


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
    
    def read_file(self, widget):
        pass#self.lbl.set_text('Menu clicked: Save')

    def read_folder(self, widget):
        pass#self.lbl.set_text('Menu clicked: Save As')

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
        settingsDict = {'Fetch data settings':self.open_fetch_data_dialog,
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

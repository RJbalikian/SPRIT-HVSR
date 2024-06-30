from remi import start, App
import remi.gui as gui
class SpritApp(App):
    def __init__(self, *args):
        super(SpritApp, self).__init__(*args)

    def main(self):
        # DEFINE 
        spritApp = gui.VBox(width='100%', height='100%', margin='0px auto', style={'vertical-align':'top'})
        
        menu = gui.Menu(width='100%', height='25px', style={'vertical-align':'top'})
        spritMenu = gui.MenuItem('SpRIT', width=100, height=25, style={'vertical-align':'top'})
        settingsMenu = gui.MenuItem('Settings', width=100, height=25, style={'vertical-align':'top'})
        

        settingsMenu.onclick.do(self.menu_view_clicked)
        m11 = gui.MenuItem('Read Data', width=100, height=25)
        m12 = gui.MenuItem('Open', width=100, height=25)
        m12.onclick.do(self.menu_open_clicked)
        m111 = gui.MenuItem('Read file', width=100, height=25)
        m111.onclick.do(self.read_file)
        m112 = gui.MenuItem('Read folder', width=100, height=25)
        m112.onclick.do(self.read_folder)

        menu.append([spritMenu, settingsMenu])
        spritMenu.append([m11, m12])
        m11.append([m111, m112])

        menubar = gui.MenuBar(width='100%', height='20px', style={'vertical-align':'top'})
        menubar.append(menu)
        
        infoLabel = gui.Label('INFORMATION', height='100%', margin='1%')

        spritApp.append(menubar)
        spritApp.append(infoLabel)

        # CLOSING SCRIPS
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


    def on_window_close(self):
        # here you can handle the unload
        print("app closing")
        self.close()

if __name__ == "__main__":
    start(SpritApp, debug=True, address='0.0.0.0', port=0)

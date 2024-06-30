from remi import start, App
import remi.gui as gui
class SpritApp(App):
    def __init__(self, *args):
        super(SpritApp, self).__init__(*args)

    def main(self):
        # DEFINE 
        spritApp = gui.VBox(width='100%', height='100%', margin='0px auto')
        
        menu = gui.Menu(width='100%', height='25px')
        m1 = gui.MenuItem('File', width=100, height=25)
        m2 = gui.MenuItem('View', width=100, height=25)
        m2.onclick.do(self.menu_view_clicked)
        m11 = gui.MenuItem('Save', width=100, height=25)
        m12 = gui.MenuItem('Open', width=100, height=25)
        m12.onclick.do(self.menu_open_clicked)
        m111 = gui.MenuItem('Save', width=100, height=25)
        m111.onclick.do(self.menu_save_clicked)
        m112 = gui.MenuItem('Save as', width=100, height=25)
        m112.onclick.do(self.menu_saveas_clicked)

        menu.append([m1, m2])
        m1.append([m11, m12])
        m11.append([m111, m112])

        menubar = gui.MenuBar(width='100%', height='20px')
        menubar.append(menu)
        
        spritApp.append(menu)

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
    
    def menu_save_clicked(self, widget):
        self.lbl.set_text('Menu clicked: Save')

    def menu_saveas_clicked(self, widget):
        self.lbl.set_text('Menu clicked: Save As')


    def on_window_close(self):
        # here you can handle the unload
        print("app closing")
        self.close()

if __name__ == "__main__":
    start(SpritApp, debug=True, address='0.0.0.0', port=0)

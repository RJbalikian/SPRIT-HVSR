from remi import start, App
import remi.gui as gui
class MyApp(App):
    def __init__(self, *args):
        super(MyApp, self).__init__(*args)

    def main(self):
        wid = gui.VBox(width=320, height=320, margin='0px auto')
        

        # add the following 3 lines to your app and the on_window_close method to make the console close automatically
        tag = gui.Tag(_type='script')
        tag.add_child("javascript", """window.onunload=function(e){remi.sendCallback('%s','%s');return "close?";};""" % (
            str(id(self)), "on_window_close"))
        wid.add_child("onunloadevent", tag)

        # returning the root widget

        return wid


    def on_window_close(self):
        # here you can handle the unload
        print("app closing")
        self.close()

if __name__ == "__main__":
    start(MyApp, debug=True, address='0.0.0.0', port=0)

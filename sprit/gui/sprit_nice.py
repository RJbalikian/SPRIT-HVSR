# main.py
from nicegui import ui

# Function to handle menu item clicks
def handle_menu_item(menu, item):
    ui.notify(f'Menu item clicked: {menu} -> {item}')

# Function to initialize the UI
def initialize_ui():
    # Create the top-level menu bar

    with ui.row().classes('w-full items-center'):
        result = ui.label().classes('mr-auto')
        with ui.button(icon='menu'):
            with ui.menu() as menu:
                ui.menu_item('Menu item 1', lambda: result.set_text('Selected item 1'))
                ui.menu_item('Menu item 2', lambda: result.set_text('Selected item 2'))
                ui.menu_item('Menu item 3 (keep open)',
                            lambda: result.set_text('Selected item 3'), auto_close=False)
                ui.separator()
                ui.menu_item('Close', menu.close)

    # Create an editable text box
    text_box = ui.input(placeholder='Enter text here')

    # Create a label
    label = ui.label('This is a label')

    # Create a button to browse for files
    def browse_files():
        # Implement your file browsing logic here
        ui.notify('Button clicked: Browse for files')

    ui.button('Browse', on_click=browse_files)

# Run the NiceGUI app
if __name__ in {"__main__", "__mp_main__"}:
    initialize_ui()
    ui.run()

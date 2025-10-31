from taipy.gui import Gui


def start_gui():
    # Initial state variables
    text_input = "Hello Taipy"
    result = "Welcome to Alglab Master!"

    # Simple GUI layout
    page = """
# Alglab Master GUI

## Input Section
<|{text_input}|input|label=Enter text|>

<|Update|button|on_action=on_button_click|>

## Result
<|{result}|text|>
"""

    # Callback function for button click
    def on_button_click(state):
        state.result = f"You entered: {state.text_input}"

    # Create and run the GUI
    gui = Gui(page)
    gui.run(title="Alglab Master", port=5000, dark_mode=False)
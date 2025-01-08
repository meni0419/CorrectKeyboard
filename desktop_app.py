import configparser
import os
import sys
import django
import pyperclip
from time import sleep
from pynput import keyboard
from pynput.keyboard import Controller, Key

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MySQLandDjango.settings')
django.setup()

from employees.views import transliterate_ua_text, transliterate_ru_text
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QComboBox, \
    QMessageBox, QHBoxLayout, QDialog, QLineEdit, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from typing import TextIO

LIGHT_THEME = """
QWidget {
    background-color: #f8f9fa;
    color: #333;
    border-radius: 8px;
}
QLabel {
    color: #333;
    font-size: 14px;
    font-weight: bold;
}
QTextEdit {
    background: rgba(255, 255, 255, 0.8);
    color: #333;
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 8px;
    font-size: 14px;
}
QTextEdit:focus {
    border: 1px solid #007bff;
    background: rgba(255, 255, 255, 0.9);
}
QPushButton {
    background-color: rgba(0, 123, 255, 0.8);
    color: white;
    border-radius: 5px;
    border: none;
    padding: 8px 10px;
    font-size: 14px;
}
QPushButton:hover {
    background-color: rgba(0, 123, 255, 1.0);
}
QComboBox {
    background: #f8f9fa;
    color: #333;
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 5px;
    font-size: 14px;
}
QComboBox:hover {
    background: #e4e6e8;
    border-color: #007bff;
}
"""

DARK_THEME = """
QWidget {
    background-color: #212529;
    color: #f8f9fa;
    border-radius: 8px;
}
QLabel {
    color: #f8f9fa;
    font-size: 14px;
    font-weight: bold;
}
QTextEdit {
    background: rgba(0, 0, 0, 0.5);
    color: #f8f9fa;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 5px;
    padding: 8px;
    font-size: 14px;
}
QTextEdit:focus {
    border: 1px solid #17a2b8;
    background: rgba(0, 0, 0, 0.6);
}
QPushButton {
    background-color: rgba(23, 162, 184, 0.8);
    color: white;
    border-radius: 5px;
    border: none;
    padding: 8px 10px;
    font-size: 14px;
}
QPushButton:hover {
    background-color: rgba(23, 162, 184, 1.0);
}
QComboBox {
    background: rgba(34, 34, 34, 0.8);
    color: #f8f9fa;
    border: 1px solid #555;
    border-radius: 5px;
    padding: 5px;
    font-size: 14px;
}
QComboBox:hover {
    background: rgba(44, 62, 80, 1.0);
    border-color: #17a2b8;
}
"""

CONFIG_FILE = "config.ini"


def save_theme_preference(theme):
    config = configparser.ConfigParser()
    config['Preferences'] = {'theme': theme}
    with open(CONFIG_FILE, 'w') as configfile:  # Type hint configfile explicitly
        configfile: TextIO  # Explicit type hint to satisfy type checkers
        config.write(configfile)


def save_hotkeys(ua_hotkey: str, ru_hotkey: str):
    """
    Save the provided hotkeys for Ukrainian and Russian transliteration to the config file.
    """
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)  # Retain existing settings

    # Add or update the hotkeys in the 'Preferences' section
    if 'Preferences' not in config:
        config['Preferences'] = {}
    config['Preferences']['ua_hotkey'] = ua_hotkey
    config['Preferences']['ru_hotkey'] = ru_hotkey

    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def load_theme_preference() -> str:
    config: configparser.ConfigParser = configparser.ConfigParser()
    if config.read(CONFIG_FILE) and 'Preferences' in config:
        preferences: dict = dict(config['Preferences'])
        return preferences.get('theme', 'Light')
    return 'Light'


def load_hotkeys() -> tuple[str, str]:
    config = configparser.ConfigParser()
    if config.read(CONFIG_FILE) and 'Preferences' in config:
        ua_hotkey = config['Preferences'].get('ua_hotkey', '<alt>+<delete>')  # Default for Ukrainian
        ru_hotkey = config['Preferences'].get('ru_hotkey', '<alt>+<end>')  # Default for Russian
        return ua_hotkey, ru_hotkey
    return '<alt>+<delete>', '<alt>+<end>'  # Default hotkeys


#     # Use translate to transform the input text
#     return input_text.translate(translation_table)
class TransliterationApp(QWidget):
    def __init__(self):
        super().__init__()
        # For theme persistence
        self.current_theme = load_theme_preference()
        # Initialize hotkeys from saved preferences
        self.ua_hotkey, self.ru_hotkey = load_hotkeys()
        # Define instance attributes in __init__
        self.input_text = None
        self.language_selection = None
        self.output_text = None
        self.transliterate_btn = None
        self.clear_btn = None
        self.copy_btn = None
        self.paste_btn = None
        self.theme_switcher = None
        # Initialize hotkeys
        self.hotkeys_listener = None
        self.register_hotkeys()
        # Initialize the UI
        self.init_ui()
        # Add system tray support
        self.tray_icon = None
        self.add_tray_icon()

    def add_tray_icon(self):
        """
        Create a system tray icon with options `Open` and `Exit`.
        """
        # Create a system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('./botico.png'))  # Use your custom icon here
        self.tray_icon.setToolTip("Transliteration App")

        # Create a menu for system tray icon
        tray_menu = QMenu()

        # Add "Open" option to reopen the app
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.show_app)  # When clicked, restore the app
        tray_menu.addAction(open_action)

        # Add "Exit" option to exit the app
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close_app)  # When clicked, exit the app
        tray_menu.addAction(exit_action)

        # Set the menu to tray icon
        self.tray_icon.setContextMenu(tray_menu)

        # Show tray icon
        self.tray_icon.show()

    def show_app(self):
        """
        Restore and bring the app to focus when `Open` is clicked from the tray menu.
        """
        self.showNormal()  # Restore the app window if it is minimized
        self.activateWindow()  # Bring it to focus

    def close_app(self):
        """
        Exit the application when `Exit` is clicked from the tray menu.
        """
        self.hotkeys_listener.stop()  # Stop hotkeys listener if running
        QApplication.quit()  # Close the application

    def closeEvent(self, event):
        """
        Override the close event to hide the app in the system tray instead of quitting.
        """
        event.ignore()  # Ignore the close event
        self.hide()  # Hide the app window instead of closing it
        self.tray_icon.showMessage("Transliteration App",
                                   "Application minimized to tray. Right-click the tray icon for options.",
                                   QSystemTrayIcon.Information,
                                   3000)  # Show a 3-second notification

    def init_ui(self):
        self.setWindowTitle("Transliteration App")
        self.setWindowIcon(QIcon('./botico.png'))
        self.setGeometry(300, 300, 400, 300)

        # Layout
        layout = QVBoxLayout()
        button_layout_t_cp = QHBoxLayout()
        button_layout_p_cl = QHBoxLayout()

        # Input Text
        layout.addWidget(QLabel("Input Text:"))
        self.input_text = QTextEdit()  # Initialize QTextEdit
        layout.addWidget(self.input_text)

        self.paste_btn = QPushButton("Paste from clipboard")  # Initialize QPushButton
        self.paste_btn.clicked.connect(self.past_from_clipboard)
        button_layout_p_cl.addWidget(self.paste_btn)

        self.clear_btn = QPushButton("Clear")  # Initialize QPushButton
        self.clear_btn.clicked.connect(self.clear_fields)
        button_layout_p_cl.addWidget(self.clear_btn)

        layout.addLayout(button_layout_p_cl)

        # Language Selection
        layout.addWidget(QLabel("Choose Target Language:"))
        self.language_selection = QComboBox()  # Initialize QComboBox
        self.language_selection.addItems(["Ukrainian", "Russian"])
        layout.addWidget(self.language_selection)

        # Output Text
        layout.addWidget(QLabel("Transliterated Text:"))
        self.output_text = QTextEdit()  # Initialize QTextEdit
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        # Buttons
        self.transliterate_btn = QPushButton("Transliterate")  # Initialize QPushButton
        self.transliterate_btn.clicked.connect(self.transliterate)
        button_layout_t_cp.addWidget(self.transliterate_btn)

        self.copy_btn = QPushButton("Copy to Clipboard")  # Initialize QPushButton
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout_t_cp.addWidget(self.copy_btn)

        layout.addLayout(button_layout_t_cp)

        # Theme Switcher
        self.theme_switcher = QComboBox()
        self.theme_switcher.addItems(["Light Theme", "Dark Theme"])
        self.theme_switcher.setCurrentIndex(0 if self.current_theme == 'Light' else 1)
        self.theme_switcher.currentIndexChanged.connect(self.switch_theme)
        layout.addWidget(QLabel("Switch Theme:"))
        layout.addWidget(self.theme_switcher)

        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self.open_settings_modal)  # Open the settings modal
        layout.addWidget(settings_btn)
        # Apply current theme
        self.apply_theme(self.current_theme)

        self.setLayout(layout)

    def transliterate(self):
        input_text = self.input_text.toPlainText()
        language = self.language_selection.currentText()

        if not input_text.strip():
            QMessageBox.warning(self, "No Input", "Please enter some text to transliterate.")
            return

        if language == "Ukrainian":
            result = transliterate_ua_text(input_text)
        elif language == "Russian":
            result = transliterate_ru_text(input_text)
        else:
            result = input_text

        self.output_text.setPlainText(result)

    def clear_fields(self):
        self.input_text.clear()
        self.output_text.clear()

    def copy_to_clipboard(self):
        result = self.output_text.toPlainText()
        if result.strip():
            QApplication.clipboard().setText(result)
            QMessageBox.information(self, "Copied", "Transliterated text copied to clipboard.")
        else:
            QMessageBox.warning(self, "No Output", "There's nothing to copy.")

    def past_from_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text()  # Get the clipboard content

        if clipboard_text.strip():  # Check if there's any non-empty content
            self.input_text.setPlainText(clipboard_text)  # Paste the content into the input field
        else:
            QMessageBox.warning(self, "Empty Clipboard", "The clipboard is empty, nothing to paste.")

    def open_settings_modal(self):
        """
        Open a modal window to allow the user to configure hotkeys.
        """
        settings_dialog = HotkeySettingsDialog(self.ua_hotkey, self.ru_hotkey)
        if settings_dialog.exec_():  # Wait for user to press "Save" in dialog
            # Update hotkeys with the chosen values
            self.ua_hotkey = settings_dialog.get_ua_hotkey()
            self.ru_hotkey = settings_dialog.get_ru_hotkey()
            self.register_hotkeys()  # Re-register hotkeys with new values

            # Save the updated hotkeys to the config file
            save_hotkeys(self.ua_hotkey, self.ru_hotkey)

    def switch_theme(self):
        selected_theme = self.theme_switcher.currentText()
        theme = 'Light' if selected_theme == "Light Theme" else 'Dark'
        self.apply_theme(theme)
        save_theme_preference(theme)

    def apply_theme(self, theme):
        if theme == 'Light':
            self.setStyleSheet(LIGHT_THEME)
        else:
            self.setStyleSheet(DARK_THEME)

    def register_hotkeys(self):
        """
        Register or update hotkeys based on the current settings.
        """
        if self.hotkeys_listener:
            self.hotkeys_listener.stop()  # Unregister existing hotkeys

        # Validate and register hotkeys
        try:
            hotkeys_mapping = {
                self.ua_hotkey: lambda: self.transliterate_clipboard("ukrainian"),
                self.ru_hotkey: lambda: self.transliterate_clipboard("russian"),
            }
            self.hotkeys_listener = keyboard.GlobalHotKeys(hotkeys_mapping)
            self.hotkeys_listener.start()  # Start listening for hotkeys
            print(f"Hotkeys registered: Ukrainian = {self.ua_hotkey}, Russian = {self.ru_hotkey}")
        except ValueError as e:
            print(f"Invalid hotkey: {e}")
            QMessageBox.critical(self, "Hotkey Error", f"Failed to register hotkeys: {e}")
            # Provide default fallback hotkeys in case of failure
            self.ua_hotkey = '<alt>+<delete>'
            self.ru_hotkey = '<alt>+<end>'

            QMessageBox.information(self, "Fallback Hotkeys",
                                    f"Fallback hotkeys applied.\nUkrainian: {self.ua_hotkey}\nRussian: {self.ru_hotkey}")
            self.register_hotkeys()

    @staticmethod
    def transliterate_clipboard(lang="ukrainian"):
        """
        Reads selected text from the clipboard, transliterates it,
        and replaces the selected text in the active application.
        """
        keyboard_controller = Controller()

        with keyboard_controller.pressed(Key.ctrl):
            keyboard_controller.press('x')
            keyboard_controller.release('x')

        sleep(0.5)
        input_text = pyperclip.paste()

        if not input_text.strip():
            print("No text found in clipboard, nothing to transliterate!")
            return

        # Transliterate the text
        if lang == "ukrainian":
            result = transliterate_ua_text(input_text)
        elif lang == "russian":
            result = transliterate_ru_text(input_text)
        else:
            result = input_text  # Fallback to input text if language is unknown

        # Write transliterated text back to clipboard
        pyperclip.copy(result)
        print(f"Text replaced with: {result}")
        # Simulate a paste using pynput
        with keyboard_controller.pressed(Key.ctrl):
            keyboard_controller.press('v')
            keyboard_controller.release('v')


class HotkeySettingsDialog(QDialog):
    def __init__(self, current_ua_hotkey, current_ru_hotkey):
        super().__init__()
        self.current_ua_hotkey = current_ua_hotkey
        self.current_ru_hotkey = current_ru_hotkey
        self.new_ua_hotkey = current_ua_hotkey
        self.new_ru_hotkey = current_ru_hotkey

        # Define all instance attributes in __init__ with default values
        self.ua_input = None
        self.ru_input = None

        # Initialize UI
        self.init_ui()

    def init_ui(self):
        """
        Initialize the UI for the Settings modal window.
        """
        self.setWindowTitle("Hotkey Settings")
        self.setMinimumSize(300, 200)

        layout = QVBoxLayout()

        # Instructions
        layout.addWidget(QLabel("Press the new hotkeys for each action and then click Save."))

        # Ukrainian Hotkey
        layout.addWidget(QLabel("Set Ukrainian Transliteration Hotkey:"))
        self.ua_input = QLineEdit(self.current_ua_hotkey)  # Show current hotkey
        layout.addWidget(self.ua_input)
        self.ua_input.keyPressEvent = self.capture_ua_key  # Override key press event

        # Russian Hotkey
        layout.addWidget(QLabel("Set Russian Transliteration Hotkey:"))
        self.ru_input = QLineEdit(self.current_ru_hotkey)  # Show current hotkey
        layout.addWidget(self.ru_input)
        self.ru_input.keyPressEvent = self.capture_ru_key  # Override key press event

        # Save and Cancel buttons
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)  # Close the dialog and save
        layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)  # Close the dialog without saving
        layout.addWidget(cancel_btn)

        self.setLayout(layout)

    def capture_ua_key(self, event):
        """
        Capture key press events for Ukrainian transliteration hotkey input.
        """
        text = self.get_pressed_key(event)
        self.new_ua_hotkey = text
        self.ua_input.setText(text)

    def capture_ru_key(self, event):
        """
        Capture key press events for Russian transliteration hotkey input.
        """
        text = self.get_pressed_key(event)
        self.new_ru_hotkey = text
        self.ru_input.setText(text)

    @staticmethod
    def get_pressed_key(event):
        """
        Convert a PyQt Key Event into a string representing the hotkey.
        """
        modifiers = event.modifiers()
        keys = []

        # Handle modifiers
        if modifiers & Qt.AltModifier:
            keys.append('<alt>')
        if modifiers & Qt.ControlModifier:
            keys.append('<ctrl>')
        if modifiers & Qt.ShiftModifier:
            keys.append('<shift>')

        # Handle special keys and textual keys
        key = event.key()
        if key in [
            Qt.Key_Delete, Qt.Key_End, Qt.Key_Home, Qt.Key_Insert,
            Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Backspace, Qt.Key_Tab,
            Qt.Key_Escape, Qt.Key_Space, Qt.Key_Enter, Qt.Key_Return
        ]:
            # Map special keys to their human-readable names
            special_keys = {
                Qt.Key_Delete: '<delete>',
                Qt.Key_End: '<end>',
                Qt.Key_Home: '<home>',
                Qt.Key_Insert: '<insert>',
                Qt.Key_PageUp: '<pageup>',
                Qt.Key_PageDown: '<pagedown>',
                Qt.Key_Backspace: '<backspace>',
                Qt.Key_Tab: '<tab>',
                Qt.Key_Escape: '<escape>',
                Qt.Key_Space: '<space>',
                Qt.Key_Enter: '<enter>',
                Qt.Key_Return: '<return>',
            }
            keys.append(special_keys[key])
        elif Qt.Key_F1 <= key <= Qt.Key_F35:
            # Handle function keys (F1 to F35)
            keys.append(f"f{key - Qt.Key_F1 + 1}")
        elif Qt.Key_0 <= key <= Qt.Key_9 or Qt.Key_A <= key <= Qt.Key_Z:
            # Handle alphanumeric keys
            keys.append(event.text())
        else:
            # Fallback for unmapped keys (like Numpad keys)
            keys.append(f"key_{key}")

        # Return the hotkey combination as a string
        return "+".join(keys).lower()

    def get_ua_hotkey(self):
        """
        Return the new Ukrainian hotkey.
        """
        return self.new_ua_hotkey

    def get_ru_hotkey(self):
        """
        Return the new Russian hotkey.
        """
        return self.new_ru_hotkey


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        translit_app = TransliterationApp()
        translit_app.show()
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("Application interrupted via keyboard. Exiting gracefully.")
        sys.exit(0)

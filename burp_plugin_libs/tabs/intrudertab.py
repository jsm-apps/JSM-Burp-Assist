from java.awt.event import ActionListener
from javax.swing import (
    JPanel,
    JLabel,
    JButton,
    JFrame
)



class IntruderTab(object):
    def __init__(self, error_callback=None):
        self._error_callback = error_callback
        self._panel = None
        
    def build_ui(self):
        self._panel = JPanel()
        self._panel.setLayout(None)

        label = JLabel("Intruder Panel")
        label.setBounds(10, 10, 200, 25)
        self._panel.add(label)

        add_button = JButton("Add $")
        add_button.setBounds(10, 50, 120, 30)
        self._panel.add(add_button)

        clear_button = JButton("Clear $")
        clear_button.setBounds(10, 70, 120, 30)
        self._panel.add(clear_button)

        return self._panel
from java.awt.event import ActionListener
from javax.swing import (
    JPanel,
    JLabel,
    JButton,
    JScrollPane,
    JTextArea,
    JTextField  
)

class AnalyseTab(object):
    def __init__(self, callbacks, helpers, error_callback=None):
        self.callbacks = callbacks
        self.helpers = helpers
        self._error_callback = error_callback
        self._panel = None
        
    def build_ui(self):
        self._panel = JPanel()
        self._panel.setLayout(None)

        return self._panel
from javax.swing import JPanel, JLabel

class DebugTab(object):
    def __init__(self, error_callback=None):
        self._error_callback = error_callback
        self._panel = None
        
    def build_ui(self):
        self._panel = JPanel()
        self._panel.setLayout(None)

        label = JLabel("Debug Panel")
        label.setBounds(10, 10, 200, 25)
        self._panel.add(label)

        return self._panel
from java.awt.event import ActionListener
from javax.swing import (
    JPanel,
    JLabel,
    JButton,
    JFrame
)

class DiscoveryAction(ActionListener):
    def actionPerformed(self, event):
        frame = JFrame("Discovery")
        frame.setSize(400, 300)
        frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE)
        frame.setLayout(None)

        label = JLabel("Discovery")
        label.setFont(Font("SansSerif", Font.BOLD, 16))
        label.setBounds(20, 20, 200, 30)
        frame.add(label)

        frame.setLocationRelativeTo(None)  # Centre on screen
        frame.setVisible(True)

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

        discovery_button = JButton("Discovery")
        discovery_button.setBounds(10, 50, 120, 30)
        discovery_button.addActionListener(DiscoveryAction())
        self._panel.add(discovery_button)

        return self._panel
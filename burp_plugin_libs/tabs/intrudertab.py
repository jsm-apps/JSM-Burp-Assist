# -*- coding: utf-8 -*-

from java.awt.event import ActionListener
from java.awt import BorderLayout, FlowLayout
from javax.swing import (
    JPanel,
    JLabel,
    JButton,
    JFrame,
    JScrollPane,
    JTextArea,
    JTextField
)




class IntruderWindow(ActionListener):
    def __init__(self, target):
        self.target = target

    def actionPerformed(self, event):
        frame = JFrame("JSM Intruder")
        frame.setSize(400, 300)
        frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE)
        frame.setLayout(BorderLayout())

        north_panel = JPanel()
        north_panel.setLayout(FlowLayout())

        target_label = JLabel("Target : " + self.target)
        btn_start = JButton("Start")
        btn_pause = JButton("Pause")
        btn_unpause = JButton("Resume")
        
        north_panel.add(target_label)
        north_panel.add(btn_start)
        north_panel.add(btn_pause)
        north_panel.add(btn_unpause)

        frame.add(north_panel, BorderLayout.NORTH)

        frame.setLocationRelativeTo(None)  # Centre on screen
        frame.setVisible(True)



MARKER = u"\u00A7"

class AddMarkerAction(ActionListener):
    def __init__(self, text_area):
        self._text_area = text_area

    def actionPerformed(self, event):
        start = self._text_area.getSelectionStart()
        end = self._text_area.getSelectionEnd()

        # Nothing selected
        if start == end:
            return

        selected = self._text_area.getSelectedText()
        replacement = u"%s%s%s" % (MARKER, selected, MARKER)
        
        self._text_area.replaceRange(replacement, start, end)
        self._text_area.select(start, start + len(replacement))

class ClearMarkerAction(ActionListener):
    def __init__(self, text_area):
        self._text_area = text_area

    def actionPerformed(self, event):
        text = self._text_area.getText()
        text = text.replace(u"\u00A7", u"")
        self._text_area.setText(text)

class IntruderTab(object):
    def __init__(self, error_callback=None):
        self._error_callback = error_callback
        self._panel = None
        
    def build_ui(self):
        self._panel = JPanel()
        self._panel.setLayout(None)
        self._details_area = JTextArea()

        label = JLabel("Intruder Panel")
        label.setBounds(10, 10, 200, 25)
        self._panel.add(label)

        target_label = JLabel("Target:")
        target_label.setBounds(10, 50, 60, 25)
        self._panel.add(target_label)

        self._target_field = JTextField()
        self._target_field.setEditable(False)
        self._target_field.setBounds(70, 50, 700, 25)
        self._panel.add(self._target_field)

        delay_label = JLabel("Delay between requests:")
        delay_label.setBounds(10, 90, 150, 25)
        self._panel.add(delay_label)

        self._delay_field = JTextField("0")
        self._delay_field.setBounds(165, 90, 80, 25)
        self._panel.add(self._delay_field)

        milliseconds_label = JLabel("milliseconds")
        milliseconds_label.setBounds(255, 90, 100, 25)
        self._panel.add(milliseconds_label)

        add_button = JButton("Add $")
        add_button.setBounds(10, 130, 120, 30)
        add_button.addActionListener(AddMarkerAction(self._details_area))
        self._panel.add(add_button)

        clear_button = JButton("Clear $")
        clear_button.setBounds(180, 130, 120, 30)
        clear_button.addActionListener(ClearMarkerAction(self._details_area))
        self._panel.add(clear_button)

        self._details_area.setEditable(True)
        self._details_area.setLineWrap(False)
        details_scroll = JScrollPane(self._details_area)
        details_scroll.setBounds(20, 190, 900, 300)
        self._panel.add(details_scroll)

        run_button = JButton("Start Intruder...")
        run_button.setBounds(10, 500, 220, 30)
        run_button.addActionListener(IntruderWindow())
        self._panel.add(run_button)


        return self._panel

    def setHTTPRequestTextAndURL(self, textToShow, url):
        self._details_area.setText(textToShow)
        self._target_field.setText(url)
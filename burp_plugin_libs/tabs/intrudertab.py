# -*- coding: utf-8 -*-

from java.awt.event import ActionListener
from javax.swing import (
    JPanel,
    JLabel,
    JButton,
    JFrame,
    JScrollPane,
    JTextArea
)


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

        add_button = JButton("Add $")
        add_button.setBounds(10, 50, 120, 30)
        add_button.addActionListener(AddMarkerAction(self._details_area))
        self._panel.add(add_button)

        clear_button = JButton("Clear $")
        clear_button.setBounds(180, 50, 120, 30)
        clear_button.addActionListener(ClearMarkerAction(self._details_area))
        self._panel.add(clear_button)

        self._details_area.setEditable(True)
        self._details_area.setLineWrap(False)
        details_scroll = JScrollPane(self._details_area)
        details_scroll.setBounds(10, 150, 900, 300)
        self._panel.add(details_scroll)


        return self._panel

    def setHTTPRequestText(self, textToShow):
        self._details_area.setText(textToShow)
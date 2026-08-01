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
    JTextField,
    JTable,
    
)

from java.lang import Runnable, Thread
from javax.swing import SwingUtilities
from javax.swing.event import ListSelectionListener

from urlparse import urlparse

from burp_plugin_libs.readonlytablemodel import ReadOnlyTableModel
from burp_plugin_libs.api_client import TaskApiClient, ApiClientError

from burp_plugin_libs.intruder.intruderstartaction import IntruderStartAction

MARKER = u"\u00A7"




class PauseWorkerAction(ActionListener):
    def __init__(self, start_action):
        self._start_action = start_action

    def actionPerformed(self, event):
        self._start_action.pause_worker()


class ResumeWorkerAction(ActionListener):
    def __init__(self, start_action):
        self._start_action = start_action

    def actionPerformed(self, event):
        self._start_action.resume_worker()


class IntruderRowSelectionListener(ListSelectionListener):
    def __init__(
        self,
        table,
        table_model,
        request_textarea,
        response_textarea
    ):
        self._table = table
        self._table_model = table_model
        self._request_textarea = request_textarea
        self._response_textarea = response_textarea

    def valueChanged(self, event):
        # Ignore intermediate selection events.
        if event.getValueIsAdjusting():
            return

        selected_view_row = self._table.getSelectedRow()

        if selected_view_row == -1:
            return

        # Required because setAutoCreateRowSorter(True) is enabled.
        selected_model_row = self._table.convertRowIndexToModel(
            selected_view_row
        )

        request_value = self._table_model.getValueAt(
            selected_model_row,
            4
        )

        response_value = self._table_model.getValueAt(
            selected_model_row,
            5
        )

        if request_value is None:
            request_value = ""

        if response_value is None:
            response_value = ""

        self._request_textarea.setText(str(request_value))
        self._response_textarea.setText(str(response_value))

        self._request_textarea.setCaretPosition(0)
        self._response_textarea.setCaretPosition(0)

class IntruderWindow(ActionListener):
    def __init__(self, callbacks, helpers, target, http_request_template):
        self.callbacks = callbacks
        self.helpers = helpers
        self.target = target
        self.http_request_template = http_request_template

    def actionPerformed(self, event):
        frame = JFrame("JSM Intruder")
        frame.setSize(1200, 800)
        frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE)
        frame.setLayout(BorderLayout())

        north_panel = JPanel()
        north_panel.setLayout(FlowLayout())

        target_label = JLabel("Target : " + self.target.getText())
        btn_start = JButton("Start")
        btn_pause = JButton("Pause")
        btn_unpause = JButton("Resume")
        
        north_panel.add(target_label)
        north_panel.add(btn_start)
        north_panel.add(btn_pause)
        north_panel.add(btn_unpause)

        centre_panel = JPanel()
        columns = [
            "#",
            "Payload",
            "Status Code",
            "Response Length",
            "Request",
            "Response"
        ]
        self._table_model = ReadOnlyTableModel(columns, 0)
        self._table = JTable(self._table_model)

        self._table.setAutoCreateRowSorter(True)
        self._table.setFillsViewportHeight(True)
        self._table.setRowSelectionAllowed(True)
        self._table.setColumnSelectionAllowed(False)

        column_model = self._table.getColumnModel()

        # Remove Response first because removing a column changes visible indexes.
        column_model.removeColumn(
            column_model.getColumn(5)
        )

        column_model.removeColumn(
            column_model.getColumn(4)
        )

        scroll = JScrollPane(self._table)
        #scroll.setBounds(10, 10, 1000, 500)

        centre_panel.add(scroll)

        south_panel = JPanel()
        south_panel.setLayout(FlowLayout())

        self._http_request_textarea = JTextArea(15, 40)
        self._http_response_textarea = JTextArea(15, 40)

        self._http_request_textarea.setEditable(False)
        self._http_response_textarea.setEditable(False)
        self._http_request_textarea.setLineWrap(False)
        self._http_response_textarea.setLineWrap(False)

        south_panel.add(JScrollPane(self._http_request_textarea))
        south_panel.add(JScrollPane(self._http_response_textarea))

        selection_model = self._table.getSelectionModel()

        selection_model.addListSelectionListener(
            IntruderRowSelectionListener(
                self._table,
                self._table_model,
                self._http_request_textarea,
                self._http_response_textarea
            )
        )


        frame.add(north_panel, BorderLayout.NORTH)
        frame.add(centre_panel, BorderLayout.CENTER)
        frame.add(south_panel, BorderLayout.SOUTH)

        start_action = IntruderStartAction(
            self.callbacks,
            self.helpers,
            self._table_model,
            self.target,
            self.http_request_template
        )

        btn_start.addActionListener(start_action)
        btn_pause.addActionListener(PauseWorkerAction(start_action))
        btn_unpause.addActionListener(ResumeWorkerAction(start_action))
        
        frame.setLocationRelativeTo(None)  # Centre on screen
        frame.setVisible(True)

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
    def __init__(self, callbacks, helpers, error_callback=None):
        self.callbacks = callbacks
        self.helpers = helpers
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
        run_button.addActionListener(IntruderWindow(self.callbacks, self.helpers, self._target_field, self._details_area))
        self._panel.add(run_button)


        return self._panel

    def setHTTPRequestTextAndURL(self, textToShow, url):
        self._details_area.setText(textToShow)
        self._target_field.setText(url)
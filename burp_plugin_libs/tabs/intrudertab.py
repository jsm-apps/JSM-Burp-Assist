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


MARKER = u"\u00A7"

class AddResultRow(Runnable):
    def __init__(self, table_model, row):
        self._table_model = table_model
        self._row = row

    def run(self):
        self._table_model.addRow(self._row)

from java.lang import Runnable
from java.util.concurrent.locks import ReentrantLock


class IntruderWorker(Runnable):
    def __init__(
        self,
        http_request_template,
        apply_payload,
        make_request,
        results_tablemodel
    ):
        self._http_request_template = http_request_template
        self.client = TaskApiClient()
        self._apply_payload = apply_payload
        self._make_request = make_request
        self._results_tablemodel = results_tablemodel

        self._lock = ReentrantLock()
        self._pause_condition = self._lock.newCondition()

        self._paused = False
        self._stopped = False

    def pause(self):
        self._lock.lock()

        try:
            self._paused = True
        finally:
            self._lock.unlock()

    def resume(self):
        self._lock.lock()

        try:
            self._paused = False
            self._pause_condition.signalAll()
        finally:
            self._lock.unlock()

    def stop(self):
        self._lock.lock()

        try:
            self._stopped = True
            self._paused = False
            self._pause_condition.signalAll()
        finally:
            self._lock.unlock()

    def _wait_if_paused(self):
        self._lock.lock()

        try:
            while self._paused and not self._stopped:
                self._pause_condition.await()

            return not self._stopped

        finally:
            self._lock.unlock()

    def run(self):
        try:
            while not self._stopped:
                if not self._wait_if_paused():
                    return

                payloads = self.client.generate_wordlist()

                for index, payload in enumerate(payloads):
                    if not self._wait_if_paused():
                        return

                    try:
                        raw_request = self._apply_payload(
                            self._http_request_template,
                            payload
                        )

                        (
                            status_code,
                            response_length,
                            request_text,
                            response_text
                        ) = self._make_request(raw_request)

                        row = [
                            index,
                            payload,
                            status_code,
                            response_length,
                            request_text,
                            response_text
                        ]

                    except Exception as ex:
                        row = [
                            index,
                            payload,
                            "Error",
                            0,
                            "",
                            str(ex)
                        ]

                    SwingUtilities.invokeLater(
                        AddResultRow(
                            self._results_tablemodel,
                            row
                        )
                    )

        except Exception as ex:
            print("Intruder worker error: {0}".format(str(ex)))

class IntruderStartAction(ActionListener):
    def __init__(
        self,
        callbacks,
        helpers,
        results_tablemodel,
        target,
        http_request_template
    ):
        self.callbacks = callbacks
        self.helpers = helpers
        self.results_tablemodel = results_tablemodel
        self.target = target
        self.http_request_template = http_request_template

        self.worker = None
        self.worker_thread = None

    def actionPerformed(self, event):
        if (
            self.worker_thread is not None
            and self.worker_thread.isAlive()
        ):
            return

        raw_http_request_template = self.http_request_template.getText()

        self.worker = IntruderWorker(
            http_request_template=raw_http_request_template,
            apply_payload=self.apply_payload,
            make_request=self.makeRequest,
            results_tablemodel=self.results_tablemodel
        )

        self.worker_thread = Thread(
            self.worker,
            "JSM-Intruder-Worker"
        )

        self.worker_thread.start()

    def pause_worker(self):
        if self.worker is not None:
            self.worker.pause()

    def resume_worker(self):
        if self.worker is not None:
            self.worker.resume()

    def stop_worker(self):
        if self.worker is not None:
            self.worker.stop()

    def apply_payload(self, text_block, payload):
        """
        Replace every §...§ placeholder with the same payload.
        Compatible with Jython 2.7.
        """
        if text_block is None:
            return None

        result = []
        position = 0

        while True:
            start = text_block.find(MARKER, position)

            if start == -1:
                result.append(text_block[position:])
                break

            end = text_block.find(MARKER, start + len(MARKER))

            # Unmatched marker: preserve the rest unchanged.
            if end == -1:
                result.append(text_block[position:])
                break

            result.append(text_block[position:start])
            result.append(payload)

            position = end + len(MARKER)

        return u"".join(result)

    def makeRequest(self, http_request):
        baseurl = self.target.getText()
        if not baseurl:
            return

        parsed = urlparse(baseurl)
        protocol = parsed.scheme
        host = parsed.hostname

        if parsed.port:
            port = parsed.port
        elif protocol == "https":
            port = 443
        else:
            port = 80

        service = self.helpers.buildHttpService(host, port, protocol)
        request_bytes = self.helpers.stringToBytes(http_request)
        result = self.callbacks.makeHttpRequest(service, request_bytes)
        response_bytes = result.getResponse()
        if response_bytes is None:
            print("No response received.")
            return

        response_info = self.helpers.analyzeResponse(response_bytes)

        status_code = response_info.getStatusCode()
        response_length = len(response_bytes)

        return status_code, response_length, self.helpers.bytesToString(request_bytes), self.helpers.bytesToString(response_bytes)

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
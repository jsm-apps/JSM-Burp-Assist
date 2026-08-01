from java.awt.event import ActionListener
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
from java.awt import BorderLayout, FlowLayout
from javax.swing.event import ListSelectionListener

from burp_plugin_libs.readonlytablemodel import ReadOnlyTableModel
from burp_plugin_libs.intruder.intruderstartaction import IntruderStartAction

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


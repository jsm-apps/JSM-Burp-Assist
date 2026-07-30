from java.text import SimpleDateFormat
from javax.swing import (
    JPanel,
    JScrollPane,
    JTable,
    JTabbedPane,
    JSplitPane,
    JTextArea,
    SwingUtilities
)
from java.util import Date, UUID
from burp_plugin_libs.readonlytablemodel import ReadOnlyTableModel
from burp_plugin_libs.swingcallback import SwingCallback
from burp_plugin_libs.issueselectionlistener import IssueSelectionListener


def to_unicode(value):
    if value is None:
        return u""
    if isinstance(value, unicode):
        return value
    try:
        return unicode(value, "utf-8")
    except TypeError:
        return unicode(value)
    except UnicodeDecodeError:
        return unicode(value, "utf-8", "replace")

class IssueManager(object):

    def __init__(self, error_callback=None):
        self._error_callback = error_callback

        self._issues = {}
        self._issue_rows = {}

        self._date_formatter = SimpleDateFormat(
            "yyyy-MM-dd HH:mm:ss"
        )

        self._panel = None
        self._table = None
        self._table_model = None
        self._details_area = None

    def build_ui(self):
        self._panel = JPanel()
        self._panel.setLayout(None)

        columns = [
            "Issue ID",
            "URL",
            "Task ID",
            "Created"
        ]

        self._table_model = ReadOnlyTableModel(columns, 0)
        self._table = JTable(self._table_model)

        self._table.setAutoCreateRowSorter(True)
        self._table.setFillsViewportHeight(True)
        self._table.setSelectionMode(0)

        selection_model = self._table.getSelectionModel()
        selection_model.addListSelectionListener(
            IssueSelectionListener(self)
        )

        table_scroll = JScrollPane(self._table)

        self._details_area = JTextArea()
        self._details_area.setEditable(False)
        self._details_area.setLineWrap(True)
        self._details_area.setWrapStyleWord(True)

        details_scroll = JScrollPane(self._details_area)

        split_pane = JSplitPane(
            JSplitPane.VERTICAL_SPLIT,
            table_scroll,
            details_scroll
        )

        split_pane.setDividerLocation(300)
        split_pane.setResizeWeight(0.6)
        split_pane.setBounds(10, 10, 1000, 500)

        self._panel.add(split_pane)

        return self._panel

    def get_panel(self):
        return self._panel

    def add_issue(
        self,
        url,
        details,
        task_id=None,
        issue_id=None
    ):
        if issue_id is None:
            issue_id = str(UUID.randomUUID())

        issue = {
            "issue_id": issue_id,
            "url": url,
            "details": details,
            "task_id": task_id or "",
            "created": self._current_time()
        }

        self._issues[issue_id] = issue
        self._add_issue_row(issue)

        return issue_id

    def get_issue(self, issue_id):
        return self._issues.get(issue_id)

    def get_issues(self):
        return dict(self._issues)

    def get_issue_count(self):
        return len(self._issues)

    def show_selected_issue(self):
        selected_view_row = self._table.getSelectedRow()

        if selected_view_row < 0:
            self._details_area.setText("")
            return

        # The displayed row may differ from the model row after sorting.
        model_row = self._table.convertRowIndexToModel(
            selected_view_row
        )

        issue_id = self._table_model.getValueAt(
            model_row,
            0
        )

        issue = self._issues.get(str(issue_id))

        if issue is None:
            self._details_area.setText(
                "Issue details could not be found."
            )
            return

        details_text = (
            u"URL: {url}\n"
            u"Task ID: {task_id}\n"
            u"Created: {created}\n\n"
            u"Details:\n"
            u"{details}"
        ).format(
            url=to_unicode(issue["url"]),
            task_id=to_unicode(issue["task_id"]),
            created=to_unicode(issue["created"]),
            details=to_unicode(issue["details"])
        )

        self._details_area.setText(details_text)
        self._details_area.setCaretPosition(0)

    def _add_issue_row(self, issue):
        def update():
            row_index = self._table_model.getRowCount()

            row = [
                issue["issue_id"],
                issue["url"],
                issue["task_id"],
                issue["created"]
            ]

            self._table_model.addRow(row)
            self._issue_rows[issue["issue_id"]] = row_index

        self._run_on_edt(update)

    def _current_time(self):
        return self._date_formatter.format(Date())

    def _print_error(self, message):
        if self._error_callback is not None:
            self._error_callback(message)
        else:
            print("[IssueManager] {}".format(message))

    def _run_on_edt(self, function):
        if SwingUtilities.isEventDispatchThread():
            function()
        else:
            SwingUtilities.invokeLater(
                SwingCallback(function)
            )
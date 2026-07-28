from javax.swing import (
    JPanel,
    JScrollPane,
    JTable,
    JTabbedPane,
    JSplitPane,
    JTextArea,
    SwingUtilities
)
from javax.swing.table import DefaultTableModel
from javax.swing.event import ListSelectionListener

from java.lang import Runnable
from java.text import SimpleDateFormat
from java.util import Date, UUID


class SwingCallback(Runnable):
    """
    Wraps a Python callable so it can safely be passed to
    SwingUtilities.invokeLater().
    """

    def __init__(self, callback):
        self.callback = callback

    def run(self):
        self.callback()


class ReadOnlyTableModel(DefaultTableModel):
    """
    Prevent users from editing JTable cells.
    """

    def isCellEditable(self, row, column):
        return False


class TaskManager(object):

    STATUS_PENDING = "Pending"
    STATUS_PROCESSING = "Processing"
    STATUS_COMPLETE = "Complete"
    STATUS_ERROR = "Error"

    def __init__(self, error_callback=None):
        self._error_callback = error_callback

        # Contains every task, including completed tasks.
        self._tasks = {}

        # Maps task IDs to JTable row indexes.
        self._task_rows = {}

        self._date_formatter = SimpleDateFormat(
            "yyyy-MM-dd HH:mm:ss"
        )

        self._panel = None
        self._table = None
        self._table_model = None

    def build_ui(self):
        self._panel = JPanel()
        self._panel.setLayout(None)

        columns = [
            "Task ID",
            "URL",
            "Status",
            "Created",
            "Completed"
        ]

        self._table_model = ReadOnlyTableModel(columns, 0)
        self._table = JTable(self._table_model)

        self._table.setAutoCreateRowSorter(True)
        self._table.setFillsViewportHeight(True)

        scroll = JScrollPane(self._table)
        scroll.setBounds(10, 10, 1000, 500)

        self._panel.add(scroll)

        return self._panel

    def get_panel(self):
        return self._panel

    def create_task(self, url, task_id=None):
        """
        Add a task to the manager and return its ID.
        """
        if task_id is None:
            task_id = str(UUID.randomUUID())

        task = {
            "task_id": task_id,
            "url": url,
            "status": self.STATUS_PENDING,
            "created": self._current_time(),
            "completed": None,
            "error": None
        }

        self._tasks[task_id] = task
        self._add_task_row(task)

        return task_id

    def set_processing(self, task_id):
        self._set_task_status(
            task_id,
            self.STATUS_PROCESSING
        )

    def complete_task(self, task_id):
        self._set_task_status(
            task_id,
            self.STATUS_COMPLETE,
            completed_time=self._current_time()
        )

    def fail_task(self, task_id, error_message):
        task = self._tasks.get(task_id)

        if task is None:
            self._print_error(
                "Could not find task {}".format(task_id)
            )
            return

        task["error"] = str(error_message)

        self._set_task_status(
            task_id,
            self.STATUS_ERROR,
            completed_time=self._current_time()
        )

    def get_task(self, task_id):
        return self._tasks.get(task_id)

    def get_tasks(self):
        return dict(self._tasks)

    def get_active_task_count(self):
        count = 0

        for task in self._tasks.values():
            if task["status"] in (
                self.STATUS_PENDING,
                self.STATUS_PROCESSING
            ):
                count += 1

        return count

    def _add_task_row(self, task):
        def update():
            row_index = self._table_model.getRowCount()

            row = [
                task["task_id"],
                task["url"],
                task["status"],
                task["created"],
                ""
            ]

            self._table_model.addRow(row)
            self._task_rows[task["task_id"]] = row_index

        self._run_on_edt(update)

    def _set_task_status(
        self,
        task_id,
        status,
        completed_time=None
    ):
        task = self._tasks.get(task_id)

        if task is None:
            self._print_error(
                "Could not find task {}".format(task_id)
            )
            return

        task["status"] = status

        if completed_time is not None:
            task["completed"] = completed_time

        self._update_task_row(
            task_id,
            status,
            completed_time
        )

    def _update_task_row(
        self,
        task_id,
        status,
        completed_time=None
    ):
        def update():
            row_index = self._task_rows.get(task_id)

            if row_index is None:
                self._print_error(
                    "Could not find table row for task {}".format(
                        task_id
                    )
                )
                return

            # Status column.
            self._table_model.setValueAt(
                status,
                row_index,
                2
            )

            # Completed column.
            if completed_time is not None:
                self._table_model.setValueAt(
                    completed_time,
                    row_index,
                    4
                )

        self._run_on_edt(update)

    def _current_time(self):
        return self._date_formatter.format(Date())

    def _print_error(self, message):
        if self._error_callback is not None:
            self._error_callback(message)
        else:
            print("[TaskManager] {}".format(message))

    def _run_on_edt(self, function):
        if SwingUtilities.isEventDispatchThread():
            function()
        else:
            SwingUtilities.invokeLater(
                SwingCallback(function)
            )


class IssueSelectionListener(ListSelectionListener):

    def __init__(self, issue_manager):
        self.issue_manager = issue_manager

    def valueChanged(self, event):
        if event.getValueIsAdjusting():
            return

        self.issue_manager.show_selected_issue()


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
            "Title",
            "Severity",
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
        title,
        url,
        details,
        severity="Information",
        task_id=None,
        issue_id=None
    ):
        if issue_id is None:
            issue_id = str(UUID.randomUUID())

        issue = {
            "issue_id": issue_id,
            "title": title,
            "severity": severity,
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
            "Title: {title}\n"
            "Severity: {severity}\n"
            "URL: {url}\n"
            "Task ID: {task_id}\n"
            "Created: {created}\n\n"
            "Details:\n"
            "{details}"
        ).format(
            title=issue["title"],
            severity=issue["severity"],
            url=issue["url"],
            task_id=issue["task_id"],
            created=issue["created"],
            details=issue["details"]
        )

        self._details_area.setText(details_text)
        self._details_area.setCaretPosition(0)

    def _add_issue_row(self, issue):
        def update():
            row_index = self._table_model.getRowCount()

            row = [
                issue["issue_id"],
                issue["title"],
                issue["severity"],
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


class ResultsTabManager(object):
    """
    Owns the Tasks and Issues tabs.
    """

    def __init__(self, error_callback=None):
        self._error_callback = error_callback

        self.task_manager = TaskManager(
            error_callback=error_callback
        )

        self.issue_manager = IssueManager(
            error_callback=error_callback
        )

        self._tabs = None
        self._task_tab_index = 0
        self._issue_tab_index = 1

    def build_ui(self):
        self._tabs = JTabbedPane()

        task_panel = self.task_manager.build_ui()
        issue_panel = self.issue_manager.build_ui()

        self._tabs.addTab("Tasks (0)", task_panel)
        self._tabs.addTab("Issues (0)", issue_panel)

        return self._tabs

    def get_panel(self):
        return self._tabs

    def create_task(self, url, task_id=None):
        task_id = self.task_manager.create_task(
            url=url,
            task_id=task_id
        )

        self.refresh_tab_titles()
        return task_id

    def set_task_processing(self, task_id):
        self.task_manager.set_processing(task_id)
        self.refresh_tab_titles()

    def complete_task(self, task_id):
        self.task_manager.complete_task(task_id)
        self.refresh_tab_titles()

    def fail_task(self, task_id, error_message):
        self.task_manager.fail_task(
            task_id,
            error_message
        )
        self.refresh_tab_titles()

    def add_issue(
        self,
        title,
        url,
        details,
        severity="Information",
        task_id=None
    ):
        issue_id = self.issue_manager.add_issue(
            title=title,
            url=url,
            details=details,
            severity=severity,
            task_id=task_id
        )

        self.refresh_tab_titles()
        return issue_id

    def refresh_tab_titles(self):
        def update():
            active_tasks = (
                self.task_manager.get_active_task_count()
            )

            issue_count = (
                self.issue_manager.get_issue_count()
            )

            self._tabs.setTitleAt(
                self._task_tab_index,
                "Tasks ({})".format(active_tasks)
            )

            self._tabs.setTitleAt(
                self._issue_tab_index,
                "Issues ({})".format(issue_count)
            )

        self._run_on_edt(update)

    def select_issues_tab(self):
        def update():
            self._tabs.setSelectedIndex(
                self._issue_tab_index
            )

        self._run_on_edt(update)

    def _run_on_edt(self, function):
        if SwingUtilities.isEventDispatchThread():
            function()
        else:
            SwingUtilities.invokeLater(
                SwingCallback(function)
            )
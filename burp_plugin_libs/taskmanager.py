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

from burp_plugin_libs.swingcallback import SwingCallback
from burp_plugin_libs.readonlytablemodel import ReadOnlyTableModel








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


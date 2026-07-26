from javax.swing import (
    JPanel,
    JScrollPane,
    JTable,
    JTabbedPane,
    SwingUtilities
)
from java.text import SimpleDateFormat

class TaskManager():
    def __init__(self):
        # Active tasks only. Used for the tab count.
        self._tasks = {}

        # Maps task IDs to their row in the JTable.
        self._task_rows = {}

        self._date_formatter = SimpleDateFormat(
            "yyyy-MM-dd HH:mm:ss"
        )

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

        self._table_model = DefaultTableModel(columns, 0)
        self._table = JTable(self._table_model)

        scroll = JScrollPane(self._table)
        scroll.setBounds(10, 10, 900, 400)

        self._panel.add(scroll)

    def getPanel(self):
        return self._panel


    def _add_task_row(self, task_id, url):
        def update():
            row_index = self._table_model.getRowCount()

            row = [
                task_id,
                url,
                "Processing",
                self._current_time(),
                ""
            ]

            self._table_model.addRow(row)
            self._task_rows[task_id] = row_index

        self._run_on_edt(update)

    def _update_task_row(
        self,
        task_id,
        status,
        completed_time=None
    ):
        def update():
            row_index = self._task_rows.get(task_id)

            if row_index is None:
                self._print_err(
                    "Could not find table row for task {}".format(
                        task_id
                    )
                )
                return

            # Status column
            self._table_model.setValueAt(
                status,
                row_index,
                2
            )

            if completed_time is not None:
                # Completed column
                self._table_model.setValueAt(
                    completed_time,
                    row_index,
                    4
                )

        self._run_on_edt(update)

    def _current_time(self):
            return self._date_formatter.format(Date())
    
    def _run_on_edt(self, function):
        if SwingUtilities.isEventDispatchThread():
            function()
        else:
            SwingUtilities.invokeLater(function)

from javax.swing import (
    JPanel,
    JScrollPane,
    JTable,
    JTabbedPane,
    JSplitPane,
    JTextArea,
    SwingUtilities
)

from burp_plugin_libs.swingcallback import SwingCallback
from burp_plugin_libs.taskmanager import TaskManager
from burp_plugin_libs.issuemanager import IssueManager
from burp_plugin_libs.tabs.debugtab import DebugTab
from burp_plugin_libs.tabs.intrudertab import IntruderTab

class ResultsTabManager(object):
    """
    Owns the Tasks and Issues tabs.
    """

    def __init__(self, callbacks, helpers, error_callback=None):
        self.callbacks = callbacks
        self.helpers = helpers
        self._error_callback = error_callback
        self.task_manager = TaskManager(error_callback=error_callback)
        self.issue_manager = IssueManager(error_callback=error_callback)
        self.debug_tab = DebugTab(error_callback=error_callback)
        self.intruder_tab = IntruderTab(self.callbacks, self.helpers, error_callback=error_callback)

        self._tabs = None
        self._task_tab_index = 0
        self._issue_tab_index = 1
        self._debug_tab_index = 2
        self._intruder_tab_index = 3

    def build_ui(self):
        self._tabs = JTabbedPane()

        task_panel = self.task_manager.build_ui()
        issue_panel = self.issue_manager.build_ui()
        debug_panel = self.debug_tab.build_ui()
        intruder_panel = self.intruder_tab.build_ui()

        self._tabs.addTab("Tasks (0)", task_panel)
        self._tabs.addTab("Issues (0)", issue_panel)
        self._tabs.addTab("Debug", debug_panel)
        self._tabs.addTab("Intruder", intruder_panel)

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
        url,
        details,
        task_id=None
    ):
        issue_id = self.issue_manager.add_issue(
            url=url,
            details=details,
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
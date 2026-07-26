from burp import IBurpExtender
from burp import IContextMenuFactory
from burp import ITab

from java.util import ArrayList, UUID, Date


from javax.swing import (
    JPanel,
    JScrollPane,
    JTable,
    JMenuItem,
    JTabbedPane,
    SwingUtilities
)

from javax.swing.table import DefaultTableModel

from taskmanager import TaskManager
from techdetect import OllamaWorker


class BurpExtender(IBurpExtender, IContextMenuFactory, ITab):

    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        self._stdout = callbacks.getStdout()
        self._stderr = callbacks.getStderr()

        callbacks.setExtensionName("JSM Burp Assist")

        

        self.taskManager = TaskManager()

        self.taskManager.build_ui()

        callbacks.addSuiteTab(self)
        callbacks.registerContextMenuFactory(self)

        self._print("Extension loaded successfully.")

    

    def getTabCaption(self):
        return "JSM Assist"

    def getUiComponent(self):
        return self.taskManager.getPanel()

    def createMenuItems(self, invocation):
        menu = ArrayList()

        item = JMenuItem(
            "Technology Detect",
            actionPerformed=lambda event:
                self._handle_tech_detect(invocation)
        )

        menu.add(item)
        return menu

    def _handle_tech_detect(self, invocation):
        try:
            messages = invocation.getSelectedMessages()

            if not messages or len(messages) == 0:
                self._print("No message selected.")
                return

            message = messages[0]
            service = message.getHttpService()

            request = message.getRequest()
            analysed = self._helpers.analyzeRequest(
                service,
                request
            )

            url = str(analysed.getUrl())

            response = message.getResponse()

            if response is None:
                self._print_err(
                    "Selected item has no HTTP response."
                )
                return

            self._print(
                "Tech detection for {}".format(url)
            )

            task_id = str(UUID.randomUUID())

            self._tasks[task_id] = {
                "id": task_id,
                "url": url,
                "status": "Processing",
                "worker": None
            }

            self._add_task_row(
                task_id=task_id,
                url=url
            )

            self.update_tab_caption()

            worker = OllamaWorker(
                task_id=task_id,
                on_complete=self.ollama_complete,
                on_error=self.ollama_failed
            )

            self._tasks[task_id]["worker"] = worker

            worker.start()

        except Exception as ex:
            self._print_err(
                "JSM Error @ _handle_tech_detect: {}".format(
                    str(ex)
                )
            )



    def ollama_complete(self, task_id, result):
        task = self._tasks.get(task_id)

        if task is None:
            return

        self._print(
            "Task {} completed: {}".format(
                task_id,
                result
            )
        )

        self._update_task_row(
            task_id=task_id,
            status="Completed",
            completed_time=self._current_time()
        )

        self._remove_active_task(task_id)

        # Later:
        # self.add_scan_issue(...)

    def ollama_failed(self, task_id, exception):
        task = self._tasks.get(task_id)

        if task is None:
            return

        self._print_err(
            "Task {} failed: {}".format(
                task_id,
                str(exception)
            )
        )

        self._update_task_row(
            task_id=task_id,
            status="Error: {}".format(str(exception)),
            completed_time=self._current_time()
        )

        self._remove_active_task(task_id)

    def _remove_active_task(self, task_id):
        """
        Removes the task from the active-task collection.

        The JTable row remains so the user can see the completed
        or failed task.
        """
        self._tasks.pop(task_id, None)
        self.update_tab_caption()

    def _run_on_edt(self, function):
        if SwingUtilities.isEventDispatchThread():
            function()
        else:
            SwingUtilities.invokeLater(function)

    def _print(self, message):
        self._stdout.write(
            (message + "\n").encode("utf-8")
        )

    def _print_err(self, message):
        self._stderr.write(
            (message + "\n").encode("utf-8")
        )

    def find_parent_tabbed_pane(self, component):
        parent = component.getParent()

        while parent is not None:
            if isinstance(parent, JTabbedPane):
                return parent

            parent = parent.getParent()

        return None

    def update_tab_caption(self):
        task_count = len(self._tasks)

        if task_count > 0:
            caption = "JSM Assist ({})".format(
                task_count
            )
        else:
            caption = "JSM Assist"

        def update():
            tabbed_pane = self.find_parent_tabbed_pane(
                self._panel
            )

            if tabbed_pane is None:
                self._print_err(
                    "Could not locate the Burp tabbed pane"
                )
                return

            index = tabbed_pane.indexOfComponent(
                self._panel
            )

            if index >= 0:
                tabbed_pane.setTitleAt(
                    index,
                    caption
                )

        self._run_on_edt(update)
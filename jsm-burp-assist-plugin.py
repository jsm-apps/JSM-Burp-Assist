from burp import IBurpExtender
from burp import IContextMenuFactory
from burp import ITab
from burp import IScanIssue

from java.util import ArrayList, UUID, Date


from javax.swing import (
    JPanel,
    JScrollPane,
    JTable,
    JMenuItem,
    JTabbedPane,
    SwingUtilities
)



from burp_plugin_libs.taskmanager import *
from burp_plugin_libs.techdetect import OllamaWorker


API_BASE_URL = "http://127.0.0.1:5000/" 

class BurpExtender(IBurpExtender, IContextMenuFactory, ITab):

    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        self._stdout = callbacks.getStdout()
        self._stderr = callbacks.getStderr()

        callbacks.setExtensionName("JSM Burp Assist")

        self._results_manager = ResultsTabManager(
            error_callback=self._print_err
        )

        self._main_panel = self._results_manager.build_ui()

        callbacks.addSuiteTab(self)
        callbacks.registerContextMenuFactory(self)

        self._print("Extension loaded successfully.")

    

    def getTabCaption(self):
        return "JSM Assist"

    def getUiComponent(self):
        return self._main_panel

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

            raw_response = self._helpers.bytesToString(response)

            self._print(
                "Tech detection for {}".format(url)
            )
            #self._print(str(response))

            task_id = self._results_manager.create_task(url)

            self._results_manager.set_task_processing(task_id)

            #task_id = str(UUID.randomUUID())

            #self.taskManager._tasks[task_id] = {
            #    "id": task_id,
            #    "url": url,
            #    "status": "Processing",
            #    "worker": None
            #}

            #self.taskManager._add_task_row(
            #    task_id=task_id,
            #    url=url
            #)

            #self.update_tab_caption()

            worker = OllamaWorker(
                task_id=task_id,
                url=url,
                message=message,
                raw_response=raw_response,
                on_complete=self.ollama_complete,
                on_error=self.ollama_failed
            )

            #self.taskManager._tasks[task_id]["worker"] = worker

            worker.start()

        except Exception as ex:
            self._print_err(
                "JSM Error @ _handle_tech_detect: {}".format(
                    str(ex)
                )
            )



    def ollama_complete(self, task_id, message, result):
        #task = self.taskManager._tasks.get(task_id)

        #if task is None:
        #    return

        self._results_manager.complete_task(task_id)

        self._print(
            "Task {} completed: {}".format(
                task_id,
                result
            )
        )

        #self.taskManager._update_task_row(
        #    task_id=task_id,
        #    status="Completed",
        #    completed_time=self.taskManager._current_time()
        #)

        #self._remove_active_task(task_id)

        # Later:
        # self.add_scan_issue(...)
        title = result.get("title")
        details = result.get("details")

        if title and details:
            self._results_manager.add_issue(
                title=title,
                url=result.get("url", ""),
                details=details,
                severity=result.get(
                    "severity",
                    "Information"
                ),
                task_id=task_id
            )

        #issue = CustomScanIssue(
        #        httpService=message.getHttpService(),
        #        url=result["url"],
        #        httpMessages=[message],
        #        name="AI task complete",
        #        detail=result["details"],
        #        severity="Information",
        #        confidence="Certain"
        #    )

        #self._callbacks.addScanIssue(issue)

    def ollama_failed(self, task_id, exception):
        task = self.taskManager._tasks.get(task_id)

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
            completed_time=self.taskManager._current_time()
        )

        self._remove_active_task(task_id)

    def _remove_active_task(self, task_id):
        """
        Removes the task from the active-task collection.

        The JTable row remains so the user can see the completed
        or failed task.
        """
        self.taskManager._tasks.pop(task_id, None)
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
        task_count = len(self.taskManager._tasks)

        if task_count > 0:
            caption = "JSM Assist ({})".format(
                task_count
            )
        else:
            caption = "JSM Assist"

        def update():
            tabbed_pane = self.find_parent_tabbed_pane(
                self.taskManager._panel
            )

            if tabbed_pane is None:
                self._print_err(
                    "Could not locate the Burp tabbed pane"
                )
                return

            index = tabbed_pane.indexOfComponent(
                self.taskManager._panel
            )

            if index >= 0:
                tabbed_pane.setTitleAt(
                    index,
                    caption
                )

        self._run_on_edt(update)


class CustomScanIssue(IScanIssue):
    def __init__(self, httpService, url, httpMessages, name, detail, severity, confidence):
        self._httpService = httpService
        self._url = url
        self._httpMessages = httpMessages
        self._name = name
        self._detail = detail
        self._severity = severity
        self._confidence = confidence

    def getUrl(self):
        return self._url

    def getIssueName(self):
        return self._name

    def getIssueType(self):
        return 0

    def getSeverity(self):
        return self._severity

    def getConfidence(self):
        return self._confidence

    def getIssueBackground(self):
        return "This issue indicates that an AI-driven background task completed for the selected URL."

    def getRemediationBackground(self):
        return "No remediation required. This is an informational marker."

    def getIssueDetail(self):
        return self._detail

    def getRemediationDetail(self):
        return None

    def getHttpMessages(self):
        return self._httpMessages

    def getHttpService(self):
        return self._httpService
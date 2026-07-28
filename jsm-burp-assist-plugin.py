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

from burp_plugin_libs.taskmanager import *
from burp_plugin_libs.techdetect import OllamaWorker

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

            task_id = self._results_manager.create_task(url)
            self._results_manager.set_task_processing(task_id)

            worker = OllamaWorker(
                task_id=task_id,
                url=url,
                message=message,
                raw_response=raw_response,
                on_complete=self.ollama_complete,
                on_error=self.ollama_failed
            )
            worker.start()

        except Exception as ex:
            self._print_err(
                "JSM Error @ _handle_tech_detect: {}".format(
                    str(ex)
                )
            )



    def ollama_complete(self, task_id, message, result):
        self._results_manager.complete_task(task_id)

        self._print(
            "Task {} completed".format(
                task_id
            )
        )

        title = result.get("title")
        details = result.get("details")

        if title and details:
            self._results_manager.add_issue(
                url=result.get("url", ""),
                details=details,
                task_id=task_id
            )

    def ollama_failed(self, task_id, exception):
        self._results_manager.fail_task(task_id, exception)

        self._print_err(
            "Task {} failed: {}".format(
                task_id,
                str(exception)
            )
        )

    def _print(self, message):
        self._stdout.write(
            (message + "\n").encode("utf-8")
        )

    def _print_err(self, message):
        self._stderr.write(
            (message + "\n").encode("utf-8")
        )

    



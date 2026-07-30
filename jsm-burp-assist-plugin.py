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
from javax.swing import JOptionPane

from burp_plugin_libs.taskmanager import *
from burp_plugin_libs.techdetect import OllamaWorker
from burp_plugin_libs.menuitems import MenuItems
from burp_plugin_libs.utils import Utils

class BurpExtender(IBurpExtender, IContextMenuFactory, ITab):

    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        self._stdout = callbacks.getStdout()
        self._stderr = callbacks.getStderr()
        self.utils = Utils(self._print, self._print_err, self._helpers)

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
        mi = MenuItems(invocation)
        return mi.getMenuItems(self._handle_tech_detect, self._handle_xss_detection, self._handle_question)

    def _run_menuitem(self, invocation, path, question = None):
        try:
            url, raw_http_response, message = self.utils.get_selected_url_and_response(invocation)

            if url is None or raw_http_response is None:
                return

            task_id = self._results_manager.create_task(url)
            self._results_manager.set_task_processing(task_id)

            worker = OllamaWorker(
                path=path,
                task_id=task_id,
                url=url,
                message=message,
                question=question,
                raw_response=raw_http_response,
                on_complete=self.ollama_complete,
                on_error=self.ollama_failed
            )
            worker.start()

        except Exception as ex:
            self._print_err(
                "JSM Error @ _run_menuitem - {}: {}".format(
                    path,
                    str(ex)
                )
            )

    def _handle_tech_detect(self, invocation):
        self._run_menuitem(invocation, "/ai/techdetect")

    def _handle_xss_detection(self, invocation):
        self._run_menuitem(invocation, "/ai/xssdetect")

    def _handle_question(self, invocation):
        question = JOptionPane.showInputDialog(
            None,
            "Enter your question:",
            "Ask AI",
            JOptionPane.QUESTION_MESSAGE
        )

        # User pressed Cancel
        if question is None:
            return

        question = question.strip()

        # Empty question
        if len(question) == 0:
            JOptionPane.showMessageDialog(
                None,
                "Please enter a question.",
                "No Question Given",
                JOptionPane.WARNING_MESSAGE
            )
            return
        self._run_menuitem(invocation, "/ai/ask-question", question)
        

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

    



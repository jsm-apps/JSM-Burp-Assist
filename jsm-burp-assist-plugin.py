from burp import IBurpExtender
from burp import IContextMenuFactory
from burp import ITab

from java.util import ArrayList
from javax.swing import JMenuItem

class BurpExtender(IBurpExtender, IContextMenuFactory, ITab):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        self._stdout = callbacks.getStdout()
        self._stderr = callbacks.getStderr()
        
        callbacks.setExtensionName("JSM Burp Assist")
        
        callbacks.registerContextMenuFactory(self)
        
        
        self._print("Extension loaded successfully.")

    def createMenuItems(self, invocation):
        menu = ArrayList()
        item = JMenuItem("Technology Detect", actionPerformed=lambda e: self._handle_tech_detect(invocation))
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

            req = message.getRequest()
            analyzed = self._helpers.analyzeRequest(service, req)
            url = analyzed.getUrl()

            response = message.getResponse()
            if response is None:
                self._print_err("Selected item has no HTTP response.")
                return
                
            self._print("Tech detection for "+str(url))
        except Exception as ex:
            self._print_err("JSM Error @ _handle_tech_detect : %s" % str(ex))
            
    def _print(self, msg):
        self._stdout.write((msg + "\n").encode("utf-8"))

    def _print_err(self, msg):
        self._stderr.write((msg + "\n").encode("utf-8"))

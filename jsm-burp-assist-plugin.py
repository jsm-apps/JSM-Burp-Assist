from burp import IBurpExtender
from burp import IContextMenuFactory
from burp import ITab

from java.util import ArrayList
from javax.swing import JPanel, JScrollPane, JTable, JMenuItem
from javax.swing.table import DefaultTableModel
from javax.swing import JTabbedPane, SwingUtilities

from techdetect import OllamaWorker

class BurpExtender(IBurpExtender, IContextMenuFactory, ITab):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        self._stdout = callbacks.getStdout()
        self._stderr = callbacks.getStderr()
        
        callbacks.setExtensionName("JSM Burp Assist")
        
        self._tasks = []
        self._init_ui()
        
        callbacks.addSuiteTab(self)
        callbacks.registerContextMenuFactory(self)
        
        
        self._print("Extension loaded successfully.")
    
    def _init_ui(self):
        self._panel = JPanel()
        self._panel.setLayout(None)

        columns = ["Task ID", "URL", "Status", "Created", "Completed"]
        self._table_model = DefaultTableModel(columns, 0)
        self._table = JTable(self._table_model)

        scroll = JScrollPane(self._table)
        scroll.setBounds(10, 10, 900, 400)
        self._panel.add(scroll)
    
    def getTabCaption(self):
        return "JSM Assist"

    def getUiComponent(self):
        return self._panel
            
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
            self._tasks.append("bert")
            
            self.update_tab_caption()
        except Exception as ex:
            self._print_err("JSM Error @ _handle_tech_detect : %s" % str(ex))
            
    def _print(self, msg):
        self._stdout.write((msg + "\n").encode("utf-8"))

    def _print_err(self, msg):
        self._stderr.write((msg + "\n").encode("utf-8"))

    


    def find_parent_tabbed_pane(self, component):
        parent = component.getParent()

        while parent is not None:
            if isinstance(parent, JTabbedPane):
                return parent

            parent = parent.getParent()

        return None


    def update_tab_caption(self):
        caption = "JSM Assist"
        task_count = len(self._tasks)
        if task_count > 0:
            caption = "JSM Assist (" + str(task_count) + ")"
            
        
        def update():
            tabbed_pane = self.find_parent_tabbed_pane(self._panel)

            if tabbed_pane is None:
                self._print_err("Could not locate the Burp tabbed pane")
                return

            index = tabbed_pane.indexOfComponent(self._panel)

            if index >= 0:
                tabbed_pane.setTitleAt(index, caption)

        if SwingUtilities.isEventDispatchThread():
            update()
        else:
            SwingUtilities.invokeLater(update)

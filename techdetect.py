from java.lang import Runnable, Thread
from javax.swing import SwingUtilities
import time


class OllamaWorker(Runnable):

    def __init__(self, on_complete, on_error=None):
        """
        on_complete(result) - called on the EDT
        on_error(exception) - optional, called on the EDT
        """
        self._on_complete = on_complete
        self._on_error = on_error

    def start(self):
        Thread(self, "OllamaWorker").start()

    def run(self):
        try:
            # Simulate long running work
            time.sleep(10)

            result = "woop"

            SwingUtilities.invokeLater(
                lambda: self._on_complete(result)
            )

        except Exception as ex:
            if self._on_error:
                SwingUtilities.invokeLater(
                    lambda: self._on_error(ex)
                )
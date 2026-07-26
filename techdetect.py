from java.lang import Runnable, Thread
from java.util import UUID
from javax.swing import SwingUtilities
import time


class OllamaWorker(Runnable):

    def __init__(self, task_id, on_complete, on_error=None):
        self.task_id = task_id
        self._on_complete = on_complete
        self._on_error = on_error

    def start(self):
        thread = Thread(
            self,
            "OllamaWorker-{}".format(self.task_id)
        )
        thread.start()

    def run(self):
        try:
            # Simulate Ollama processing
            time.sleep(10)

            result = "woop"

            SwingUtilities.invokeLater(
                lambda: self._on_complete(
                    self.task_id,
                    result
                )
            )

        except Exception as ex:
            if self._on_error is not None:
                SwingUtilities.invokeLater(
                    lambda: self._on_error(
                        self.task_id,
                        ex
                    )
                )
from java.lang import Runnable, Thread
from java.util import UUID
from javax.swing import SwingUtilities
import time
from ollama import Client
from pathlib import Path

def load_from_file(filename):
    path = (Path("prompts") / filename)
    if not path.exists():
        raise FileNotFoundError(f"Payload file not found: {path}")
    
    filecontent = path.read_text(encoding="utf-8")
    return filecontent

class OllamaWorker(Runnable):

    def __init__(self, task_id, on_complete, on_error=None):
        self.task_id = task_id
        self._on_complete = on_complete
        self._on_error = on_error
        self.model  = "qwen3.5:latest"
        self.prompt = load_from_file("tectdetect.prompt.txt")

    def start(self):
        thread = Thread(
            self,
            "OllamaWorker-{}".format(self.task_id)
        )
        thread.start()

    def run(self):
        try:
            result = ollama.generate(model=self.model, prompt=self.prompt)
            print(result['response'])

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
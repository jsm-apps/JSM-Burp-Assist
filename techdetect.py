from java.lang import Runnable, Thread
from java.util import UUID
from javax.swing import SwingUtilities
import time

import os

from api_client import TaskApiClient, ApiClientError

def load_from_file(filename):
    base = "/home/g/Documents/JSM/code/JSM-Burp-Assist/prompts"
    path = os.path.join(base, filename)

    print("Looking for:", path)

    if not os.path.isfile(path):
        raise IOError("File not found: %s" % path)

    with open(path, "r") as f:
        return f.read()

class OllamaWorker(Runnable):

    def __init__(self, task_id, url, message, on_complete, on_error=None):
        self.task_id = task_id
        self.url = url
        self.message = message
        self._on_complete = on_complete
        self._on_error = on_error
        self.model  = "qwen3.5:latest"
        self.prompt = load_from_file("techdetect.prompt.txt")

    def start(self):
        thread = Thread(
            self,
            "OllamaWorker-{}".format(self.task_id)
        )
        thread.start()

    def run(self):
        try:
            #result = ollama.generate(model=self.model, prompt=self.prompt)

            client = TaskApiClient(
                base_url="http://127.0.0.1:5000",
                timeout=300,
            )

            task = client.create_task(self.url)

            print("Task ID: {0}".format(task['task_id']))

            result = client.wait_for_task(
                task_id=task['task_id'],
                poll_interval=10,
                timeout=300,
            )

            print("Title: {0}".format(result["title"]))
            print("URL: {0}".format(result["url"]))
            print("Details: {0}".format(result["details"]))




            #print(result['response'])

            SwingUtilities.invokeLater(
                lambda: self._on_complete(
                    self.task_id,
                    self.message,
                    result
                )
            )

        except Exception as ex:
            print("ERROR "+str(ex))
            if self._on_error is not None:
                SwingUtilities.invokeLater(
                    lambda: self._on_error(
                        self.task_id,
                        ex
                    )
                )
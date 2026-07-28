from java.lang import Runnable, Thread
from java.util import UUID
from javax.swing import SwingUtilities
import time

from burp_plugin_libs.api_client import TaskApiClient, ApiClientError


class OllamaWorker(Runnable):

    def __init__(self, path, task_id, url, message, raw_response, on_complete, on_error=None):
        self.path = path
        self.task_id = task_id
        self.url = url
        self.message = message
        self.raw_response = raw_response
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
            #result = ollama.generate(model=self.model, prompt=self.prompt)

            client = TaskApiClient(
                base_url="http://127.0.0.1:5000",
                timeout=300,
            )

            task = client.create_task(self.path, self.url, self.raw_response)

            print("Task ID: {0}".format(task['task_id']))

            result = client.wait_for_task(
                task_id=task['task_id'],
                poll_interval=10,
                timeout=300,
            )

            #print("Title: {0}".format(result["title"]))
            #print("URL: {0}".format(result["url"]))
            #print("Details: {0}".format(result["details"]))




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
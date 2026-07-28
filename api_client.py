# api_client.py

import json
import time
import urllib2


class ApiClientError(Exception):
    pass


class TaskApiClient(object):

    def __init__(self, base_url="http://127.0.0.1:5000", timeout=10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method, path, data=None):
        url = self.base_url + path

        headers = {
            "Accept": "application/json",
        }

        body = None

        if data is not None:
            body = json.dumps(data)
            headers["Content-Type"] = "application/json"

        request = urllib2.Request(
            url=url,
            data=body,
            headers=headers,
        )

        # Jython/Python 2 urllib2 does not support a method argument.
        request.get_method = lambda: method

        try:
            response = urllib2.urlopen(
                request,
                timeout=self.timeout,
            )

            response_body = response.read()
            status_code = response.getcode()

        except urllib2.HTTPError as exc:
            error_body = exc.read()

            try:
                error_data = json.loads(error_body)
                message = error_data.get("error", error_body)
            except Exception:
                message = error_body

            raise ApiClientError(
                "API returned HTTP {0}: {1}".format(
                    exc.code,
                    message,
                )
            )

        except urllib2.URLError as exc:
            raise ApiClientError(
                "Could not connect to API: {0}".format(exc.reason)
            )

        except Exception as exc:
            raise ApiClientError(
                "API request failed: {0}".format(str(exc))
            )

        if status_code < 200 or status_code >= 300:
            raise ApiClientError(
                "Unexpected HTTP status: {0}".format(status_code)
            )

        try:
            return json.loads(response_body)
        except ValueError:
            raise ApiClientError(
                "API returned invalid JSON: {0}".format(response_body)
            )

    def create_task(self, url):
        """
        Submit a URL for processing.

        Returns:
            {
                "task_id": "...",
                "status": "pending"
            }
        """
        if not url:
            raise ValueError("url is required")

        return self._request(
            method="POST",
            path="/task",
            data={
                "url": url,
            },
        )

    def get_task(self, task_id):
        """
        Retrieve the current task state.
        """
        if not task_id:
            raise ValueError("task_id is required")

        return self._request(
            method="GET",
            path="/task/{0}".format(task_id),
        )

    def wait_for_task(
        self,
        task_id,
        poll_interval=10,
        timeout=300,
        status_callback=None,
    ):
        """
        Poll until the task completes, errors, or times out.

        status_callback is optional and receives the current task dictionary.
        """
        started_at = time.time()

        while True:
            task = self.get_task(task_id)

            if status_callback is not None:
                status_callback(task)

            status = task.get("status")

            if status == "complete":
                return task

            if status == "error":
                raise ApiClientError(
                    task.get("error", "Task failed")
                )

            if time.time() - started_at >= timeout:
                raise ApiClientError(
                    "Timed out waiting for task {0}".format(task_id)
                )

            time.sleep(poll_interval)

    def submit_and_wait(
        self,
        url,
        poll_interval=10,
        timeout=300,
        status_callback=None,
    ):
        """
        Convenience method that creates and waits for a task.
        """
        created_task = self.create_task(url)
        task_id = created_task.get("task_id")

        if not task_id:
            raise ApiClientError(
                "API response did not contain a task_id"
            )

        return self.wait_for_task(
            task_id=task_id,
            poll_interval=poll_interval,
            timeout=timeout,
            status_callback=status_callback,
        )
# app.py (needs to be run using python 3.11 or higher)

import threading
import time
import uuid

from flask import Flask, jsonify, request
from ollama import Client
import requests
import os

model = "qwen3.5:latest"
ollama_host = "http://localhost:11434"
ollama_client = Client(host=ollama_host)

def load_from_file(filename):
    base = "/home/g/Documents/JSM/code/JSM-Burp-Assist/prompts"
    path = os.path.join(base, filename)

    print("Looking for:", path)

    if not os.path.isfile(path):
        raise IOError("File not found: %s" % path)

    with open(path, "r") as f:
        return f.read()

def create_summary(stringcontent):
    """
    Ask Ollama to summarise the supplied string.

    Args:
        stringcontent: Text to summarise.

    Returns:
        The generated summary as a string.

    Raises:
        ValueError: If no content was supplied.
        RuntimeError: If Ollama fails or returns no summary.
    """
    if stringcontent is None:
        raise ValueError("stringcontent is required")

    stringcontent = str(stringcontent).strip()

    if not stringcontent:
        raise ValueError("stringcontent cannot be empty")

    prompt = (
        "Create a clear and concise summary of the following content.\n\n"
        "Requirements:\n"
        "- Include the most important findings and facts.\n"
        "- Remove repetition and unnecessary detail.\n"
        "- Do not invent information.\n"
        "- Use plain English.\n"
        "- Return only the summary.\n\n"
        "Content:\n"
        "{}"
    ).format(stringcontent)

    try:
        response = ollama_client.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (load_from_file("techdetect.prompt.txt"))
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0.2
            }
        )

        # Support both object-style and dictionary-style responses.
        if hasattr(response, "message"):
            summary = response.message.content
        else:
            summary = response.get("message", {}).get("content")

        if not summary:
            raise RuntimeError(
                "Ollama returned an empty summary"
            )

        return summary.strip()

    except Exception as exc:
        raise RuntimeError(
            "Failed to create summary: {}".format(exc)
        )

def get_raw_http_response(url, timeout=30, verify=True):
    """
    Fetch a URL and return the raw HTTP response.

    Returns:
        String containing:
            HTTP/1.1 200 OK
            Header: Value
            ...

            <body>
    """

    response = requests.get(
        url,
        allow_redirects=False,
        timeout=timeout,
        verify=verify,
    )

    # Build status line
    status_line = "HTTP/1.1 {} {}".format(
        response.status_code,
        response.reason,
    )

    # Build headers
    headers = "\r\n".join(
        "{}: {}".format(k, v)
        for k, v in response.headers.items()
    )

    # Body
    body = response.text

    return "{}\r\n{}\r\n\r\n{}".format(
        status_line,
        headers,
        body,
    )

app = Flask(__name__)

# In-memory task storage.
# Replace this with Redis or a database for production use.
tasks = {}
tasks_lock = threading.Lock()


def process_task(task_id, url):
    """
    Simulate a task that takes 10 seconds.
    """
    try:
        #time.sleep(10)

        http_response = get_raw_http_response(url)
        summary = create_summary(http_response)

        result = {
            "task_id": task_id,
            "status": "complete",
            "title": "Example title",
            "url": url,
            "details": summary,
        }

        with tasks_lock:
            tasks[task_id] = result

    except Exception as exc:
        with tasks_lock:
            tasks[task_id] = {
                "task_id": task_id,
                "status": "error",
                "error": str(exc),
            }


@app.route("/task", methods=["POST"])
def create_task():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body must contain JSON."
        }), 400

    url = data.get("url")

    if not url or not isinstance(url, str):
        return jsonify({
            "error": "A valid URL string is required."
        }), 400

    if not url.startswith(("http://", "https://")):
        return jsonify({
            "error": "URL must start with http:// or https://."
        }), 400

    task_id = str(uuid.uuid4())

    with tasks_lock:
        tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "url": url,
        }

    worker = threading.Thread(
        target=process_task,
        args=(task_id, url),
        daemon=True,
    )
    worker.start()

    return jsonify({
        "task_id": task_id,
        "status": "pending",
    }), 202


@app.route("/task/<task_id>", methods=["GET"])
def get_task(task_id):
    with tasks_lock:
        task = tasks.get(task_id)

    if task is None:
        return jsonify({
            "error": "Task not found."
        }), 404

    return jsonify(task), 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        threaded=True,
    )
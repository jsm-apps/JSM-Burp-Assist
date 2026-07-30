# app.py (needs to be run using python 3.11 or higher)

import threading
import time
import uuid

from flask import Flask, jsonify, request
from ollama import Client
import requests
import os

model = "aratan/qwen3.5-uncensored:9b"
ollama_host = "http://localhost:11434"
ollama_client = Client(host=ollama_host)

def load_from_file(filename):
    base = "./prompts"
    path = os.path.join(base, filename)

    print("Looking for:", path)

    if not os.path.isfile(path):
        raise IOError("File not found: %s" % path)

    with open(path, "r") as f:
        return f.read()

def create_summary(system_prompt_file, url, stringcontent):
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

    system_prompt = load_from_file(system_prompt_file)

    prompt = (
        "URL: {}\n"
        "HTTP Response:\n"
        "{}"
    ).format(url, stringcontent)

    full_prompt = system_prompt+"\n"+prompt
    print(full_prompt)

    try:
        response = ollama_client.generate(
            model=model,
            prompt=full_prompt
        )

        # Support both object-style and dictionary-style responses.
        if hasattr(response, "response"):
            summary = response.response
        else:
            summary = response.get("response")

        if not summary:
            raise RuntimeError(
                "Ollama returned an empty summary"
            )

        return summary.strip()

    except Exception as exc:
        raise RuntimeError(
            "Failed to create summary: {}".format(exc)
        )


app = Flask(__name__)

# In-memory task storage.
# Replace this with Redis or a database for production use.
tasks = {}
tasks_lock = threading.Lock()


def process_ai_task(prompt_file, task_id, url, raw_response):
    """
    Simulate a task that takes 10 seconds.
    """
    try:
        #time.sleep(10)

        http_response = raw_response
        summary = create_summary(prompt_file, url, http_response)

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


@app.route("/ai/techdetect", methods=["POST"])
def create_task():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body must contain JSON."
        }), 400

    url = data.get("url")

    raw_response = data.get("raw_response")

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
        target=process_ai_task,
        args=("techdetect.prompt.txt", task_id, url, raw_response),
        daemon=True,
    )
    worker.start()

    return jsonify({
        "task_id": task_id,
        "status": "pending",
    }), 202


@app.route("/ai/xssdetect", methods=["POST"])
def create_xss_task():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body must contain JSON."
        }), 400

    url = data.get("url")

    raw_response = data.get("raw_response")

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
        target=process_ai_task,
        args=("xssdetect.prompt.txt", task_id, url, raw_response),
        daemon=True,
    )
    worker.start()

    return jsonify({
        "task_id": task_id,
        "status": "pending",
    }), 202



@app.route("/ai/ask-question", methods=["POST"])
def create_question_task():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body must contain JSON."
        }), 400

    url = data.get("url")

    raw_response = data.get("raw_response")
    question = data.get("question")

    if not url or not isinstance(url, str):
        return jsonify({
            "error": "A valid URL string is required."
        }), 400

    if not url.startswith(("http://", "https://")):
        return jsonify({
            "error": "URL must start with http:// or https://."
        }), 400

    # write question to prompts/question.prompt.txt
    with open("prompts/question.prompt.txt", "w", encoding="utf-8") as f:
        f.write(question)

    task_id = str(uuid.uuid4())

    with tasks_lock:
        tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "url": url,
        }

    worker = threading.Thread(
        target=process_ai_task,
        args=("question.prompt.txt", task_id, url, raw_response),
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
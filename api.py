# app.py (needs to be run using python 3.11 or higher)

import threading
import time
import uuid

from flask import Flask, jsonify, request


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
        time.sleep(10)

        result = {
            "task_id": task_id,
            "status": "complete",
            "title": "Example title",
            "url": url,
            "details": "Example task details generated after processing the URL.",
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